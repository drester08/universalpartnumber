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
        fastener_pair = by_pair[("MP-BOSSARD-1049860", "MP-WUERTH-00578-30")]
        if fastener_pair["result"] != "insufficient_evidence":
            raise AssertionError("Unproven ISO 4017 fastener equivalence was not held for evidence")
        fastener_missing = str(fastener_pair["missing_properties"]).split(";")
        for property_id in ("PROP-THREAD-PITCH", "PROP-COATING-SPEC", "PROP-PRODUCT-CLASS"):
            if property_id not in fastener_missing:
                raise AssertionError(f"Fastener evidence gap was not retained: {property_id}")

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
        finally:
            connection.close()

    print(
        "Quality-gate tests passed: specificity gaps stayed unresolved; incomplete review, "
        "unverified artifact, and unnumbered issued item were rejected."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
