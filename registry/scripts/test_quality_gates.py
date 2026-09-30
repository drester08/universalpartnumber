#!/usr/bin/env python3
"""Exercise fail-closed registry constraints and publication gates."""

from __future__ import annotations

import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

import build_registry
import screen_candidates


ROOT = Path(__file__).resolve().parents[1]


def expect_integrity_error(connection: sqlite3.Connection, sql: str, values: tuple[object, ...]) -> None:
    try:
        connection.execute(sql, values)
    except sqlite3.IntegrityError:
        connection.rollback()
        return
    raise AssertionError("Expected SQLite integrity constraint to reject the record")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="upn-quality-") as directory:
        database = Path(directory) / "registry.sqlite"
        build_registry.build(database)

        screening_connection = sqlite3.connect(database)
        screening_connection.row_factory = sqlite3.Row
        try:
            fastener_part_eans = screening_connection.execute(
                """
                SELECT count(*)
                  FROM manufacturer_part_identifiers
                 WHERE manufacturer_part_id IN (
                   'MP-BOSSARD-1049860', 'MP-WUERTH-00578-30', 'MP-FABORY-01210080030'
                 ) AND scheme = 'ean'
                """
            ).fetchone()[0]
            if fastener_part_eans:
                raise AssertionError("Commercial EAN was attached directly to a physical fastener record")
            fabory_offer = screening_connection.execute(
                """
                SELECT so.pack_quantity, so.package_level, soi.identifier_scope
                  FROM supplier_offers AS so
                  JOIN supplier_offer_identifiers AS soi
                    ON soi.supplier_offer_id = so.supplier_offer_id
                 WHERE so.supplier_offer_id = 'OFFER-FABORY-01210080030'
                   AND soi.identifier_value = '8715492030054'
                """
            ).fetchone()
            if not fabory_offer or tuple(fabory_offer) != (200, "box", "box"):
                raise AssertionError("Fabory box quantity and EAN scope were not preserved as an offer")
            direct_nsn = screening_connection.execute(
                """
                SELECT count(*)
                  FROM manufacturer_part_identifiers
                 WHERE manufacturer_part_id = 'MP-FABORY-01210080030'
                   AND identifier_value = '5305-12-337-0503'
                """
            ).fetchone()[0]
            if direct_nsn:
                raise AssertionError("NSN was incorrectly modeled as a manufacturer part identifier")
            nsn = screening_connection.execute(
                """
                SELECT ei.verification_state, mper.review_state
                  FROM external_identifiers AS ei
                  JOIN manufacturer_part_external_references AS mper
                    ON mper.external_identifier_id = ei.external_identifier_id
                 WHERE ei.namespace = 'NSN'
                   AND ei.identifier_value = '5305-12-337-0503'
                   AND mper.manufacturer_part_id = 'MP-FABORY-01210080030'
                """
            ).fetchone()
            if not nsn or tuple(nsn) != ("unverified", "unreviewed"):
                raise AssertionError("Unverified Fabory NSN assertion was not kept fail-closed")
            screenings = screen_candidates.screen(screening_connection, "2026-09-30")
        finally:
            screening_connection.close()
        by_pair = {
            (row["left_part_id"], row["right_part_id"]): row
            for row in screenings
        }
        material_specificity = by_pair[("MP-ATKORE-LEK103RHG", "MP-NIEDAX-KL100303F")]
        if "PROP-MATERIAL" in str(material_specificity["conflicting_properties"]).split(";"):
            raise AssertionError("Generic steel versus mild steel was incorrectly treated as a contradiction")
        if "PROP-MATERIAL" not in str(material_specificity["missing_properties"]).split(";"):
            raise AssertionError("Material specificity gap was not preserved as unresolved evidence")
        finish_specificity = by_pair[("MP-OBO-LCIS630", "MP-OGLAEND-1371512")]
        if "PROP-SURFACE-PROTECTION" in str(finish_specificity["conflicting_properties"]).split(";"):
            raise AssertionError("Generic versus specific hot-dip galvanizing was treated as a contradiction")
        if "PROP-SURFACE-PROTECTION" not in str(finish_specificity["missing_properties"]).split(";"):
            raise AssertionError("Finish specificity gap was not preserved as unresolved evidence")
        fastener_pairs = (
            ("MP-BOSSARD-1049860", "MP-FABORY-01210080030"),
            ("MP-BOSSARD-1049860", "MP-WUERTH-00578-30"),
            ("MP-FABORY-01210080030", "MP-WUERTH-00578-30"),
        )
        for pair in fastener_pairs:
            if by_pair[pair]["result"] != "insufficient_evidence":
                raise AssertionError(f"Unproven ISO 4017 equivalence was not held for evidence: {pair}")
        bossard_wuerth_missing = str(
            by_pair[("MP-BOSSARD-1049860", "MP-WUERTH-00578-30")]["missing_properties"]
        ).split(";")
        for property_id in (
            "PROP-THREAD-PITCH",
            "PROP-THREAD-DIRECTION",
            "PROP-COATING-SPEC",
            "PROP-PRODUCT-CLASS",
        ):
            if property_id not in bossard_wuerth_missing:
                raise AssertionError(f"Fastener evidence gap was not retained: {property_id}")
        fabory_wuerth_missing = str(
            by_pair[("MP-FABORY-01210080030", "MP-WUERTH-00578-30")]["missing_properties"]
        ).split(";")
        if "PROP-FASTENER-SURFACE" not in fabory_wuerth_missing:
            raise AssertionError("Generic electrolytic zinc versus blue zinc was treated as exact")

        connection = sqlite3.connect(database)
        try:
            connection.execute(
                """
                INSERT INTO manufacturer_part_reviews
                  (review_id, manufacturer_part_id, decision, rationale, reviewer, decided_at, policy_version)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "TEST-REVIEW",
                    "MP-LEGRAND-ZL600G",
                    "accepted",
                    "Deliberately invalid test review",
                    "quality-gate-test",
                    "2026-09-30",
                    "0.1",
                ),
            )
            connection.commit()
        finally:
            connection.close()

        audit = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "audit_completeness.py"), "--database", str(database)],
            capture_output=True,
            text=True,
            check=False,
        )
        if audit.returncode != 1 or "Publication gate failed" not in audit.stdout:
            raise AssertionError(f"Incomplete accepted part was not rejected:\n{audit.stdout}\n{audit.stderr}")

        connection = sqlite3.connect(database)
        try:
            expect_integrity_error(
                connection,
                """
                INSERT INTO source_artifacts
                  (artifact_id, source_id, artifact_url, retrieved_at, retrieval_state)
                VALUES (?, ?, ?, ?, ?)
                """,
                ("TEST-ARTIFACT", "SRC-OGLAEND-LOE-SYSTEM", "https://example.invalid/evidence.pdf", "2026-09-30", "retrieved"),
            )
            expect_integrity_error(
                connection,
                """
                INSERT INTO items_of_supply
                  (item_id, profile_id, preferred_name, lifecycle_state)
                VALUES (?, ?, ?, ?)
                """,
                ("TEST-ITEM", "PROFILE-CABLE-LADDER-STRAIGHT-STEEL-0.1", "Invalid issued item", "issued"),
            )
            expect_integrity_error(
                connection,
                """
                INSERT INTO external_identifiers
                  (external_identifier_id, namespace, identifier_value, issuing_authority,
                   identifier_scope, verification_state, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "TEST-EXT-ID",
                    "NSN",
                    "0000-00-000-0000",
                    "Test authority",
                    "item_of_supply",
                    "authority_verified",
                    "Invalid verified identifier without an authority source",
                ),
            )
        finally:
            connection.close()

    print(
        "Quality-gate tests passed: specificity gaps stayed unresolved; incomplete review, "
        "unverified artifact, and unnumbered issued item were rejected."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
