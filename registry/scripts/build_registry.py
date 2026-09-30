#!/usr/bin/env python3
"""Build a reproducible SQLite registry from reviewed seed files."""

from __future__ import annotations

import argparse
import csv
import sqlite3
import sys
from pathlib import Path

import validate_registry


ROOT = Path(__file__).resolve().parents[1]
SOURCE_FIELDS = (
    "source_id",
    "publisher_name",
    "title",
    "source_url",
    "source_type",
    "authority_tier",
    "access_state",
    "license_state",
    "license_url",
    "ingestion_status",
    "version_label",
    "publication_date",
    "retrieved_at",
    "notes",
)
DOMAIN_FIELDS = ("domain_id", "label", "scope_note", "status")
ORGANIZATION_FIELDS = ("organization_id", "legal_name", "organization_type", "website_url")
ARTIFACT_FIELDS = ("artifact_id", "source_id", "artifact_url", "media_type", "local_path", "sha256", "retrieved_at", "retrieval_state", "notes")
UNIT_FIELDS = ("unit_id", "unece_code", "symbol", "name", "quantity_kind", "conversion_factor", "conversion_offset")
PROPERTY_FIELDS = ("property_id", "source_id", "external_code", "preferred_label", "definition", "value_kind", "identity_role")
PROFILE_FIELDS = ("profile_id", "domain_id", "class_label", "version_label", "status", "scope_note")
PROFILE_PROPERTY_FIELDS = ("profile_id", "property_id", "requirement", "comparison_rule", "sequence_number", "rationale")
NUMERIC_RULE_FIELDS = ("rule_id", "profile_id", "property_id", "comparison_method", "quantity_kind", "absolute_tolerance_base", "relative_tolerance", "version_label", "rationale")
ITEM_FIELDS = ("item_id", "upn", "profile_id", "preferred_name", "lifecycle_state", "fingerprint_version", "identity_fingerprint", "created_at", "reviewed_at")
UPN_ALLOCATION_FIELDS = ("allocation_id", "sequence_number", "upn", "item_id", "allocated_by", "allocated_at", "allocation_state")
MANUFACTURER_PART_FIELDS = ("manufacturer_part_id", "manufacturer_id", "profile_id", "manufacturer_part_number", "normalized_part_number", "manufacturer_name", "lifecycle_state")
SUPPLIER_OFFER_FIELDS = ("supplier_offer_id", "supplier_id", "manufacturer_part_id", "source_id", "seller_sku", "normalized_sku", "offered_name", "brand_name", "order_quantity", "order_unit", "package_level", "lifecycle_state")
SUPPLIER_OFFER_IDENTIFIER_FIELDS = ("supplier_offer_id", "scheme", "identifier_value", "identifier_authority", "identifier_scope", "source_id", "is_primary")
PART_IDENTIFIER_FIELDS = ("manufacturer_part_id", "scheme", "identifier_value", "identifier_authority", "source_id", "is_primary")
EXTERNAL_IDENTIFIER_FIELDS = ("external_identifier_id", "namespace", "identifier_value", "issuing_authority", "identifier_scope", "verification_state", "verified_source_id", "verified_at", "notes")
PART_EXTERNAL_REFERENCE_FIELDS = ("reference_id", "manufacturer_part_id", "external_identifier_id", "relationship", "assertion_source_id", "review_state", "observed_at", "notes")
EXTERNAL_IDENTIFIER_EVIDENCE_FIELDS = ("evidence_id", "external_identifier_id", "source_id", "evidence_role", "source_locator", "observed_at", "notes")
PART_REVIEW_FIELDS = ("review_id", "manufacturer_part_id", "decision", "rationale", "reviewer", "decided_at", "policy_version")
MATCH_CANDIDATE_FIELDS = ("match_candidate_id", "left_part_id", "right_part_id", "algorithm_version", "score", "blocking_keys", "generated_at")
EQUIVALENCE_DECISION_FIELDS = ("decision_id", "match_candidate_id", "decision", "rationale", "reviewer", "decided_at", "policy_version")
ITEM_REVIEW_FIELDS = ("item_review_id", "item_id", "decision", "rationale", "reviewer", "decided_at", "policy_version", "independence_attested")
ITEM_MEMBERSHIP_FIELDS = ("item_id", "manufacturer_part_id", "equivalence_decision_id", "part_review_id", "valid_from", "valid_to")
OBSERVATION_FIELDS = ("observation_id", "manufacturer_part_id", "item_id", "source_id", "source_locator", "observed_name", "observed_part_number", "observed_at", "raw_payload_sha256", "review_state")
SPECIFICATION_FIELDS = ("specification_id", "observation_id", "property_id", "raw_value", "normalized_text", "normalized_number", "unit_id", "qualifier")
PAIR_SCREENING_FIELDS = ("screening_id", "left_part_id", "right_part_id", "profile_id", "algorithm_version", "blocking_keys", "compared_properties", "matched_properties", "conflicting_properties", "missing_properties", "score", "result", "generated_at")


def rows(name: str) -> list[dict[str, str | None]]:
    with (ROOT / "data" / name).open(encoding="utf-8-sig", newline="") as handle:
        return [
            {key: (value if value != "" else None) for key, value in row.items()}
            for row in csv.DictReader(handle)
        ]


def insert_rows(
    connection: sqlite3.Connection,
    table: str,
    fields: tuple[str, ...],
    records: list[dict[str, str | None]],
) -> None:
    columns = ", ".join(fields)
    placeholders = ", ".join("?" for _ in fields)
    connection.executemany(
        f"INSERT INTO {table} ({columns}) VALUES ({placeholders})",
        ([record[field] for field in fields] for record in records),
    )


def build(output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(".tmp")
    temporary.unlink(missing_ok=True)
    try:
        connection = sqlite3.connect(temporary)
        try:
            connection.executescript((ROOT / "schema.sql").read_text(encoding="utf-8"))
            insert_rows(connection, "sources", SOURCE_FIELDS, rows("source-register.csv"))
            insert_rows(connection, "source_artifacts", ARTIFACT_FIELDS, rows("source-artifacts.csv"))
            insert_rows(connection, "organizations", ORGANIZATION_FIELDS, rows("organizations.csv"))
            insert_rows(connection, "domains", DOMAIN_FIELDS, rows("domain-seed.csv"))
            insert_rows(connection, "units", UNIT_FIELDS, rows("units.csv"))
            insert_rows(connection, "properties", PROPERTY_FIELDS, rows("properties.csv"))
            insert_rows(connection, "identity_profiles", PROFILE_FIELDS, rows("identity-profiles.csv"))
            insert_rows(connection, "identity_profile_properties", PROFILE_PROPERTY_FIELDS, rows("identity-profile-properties.csv"))
            insert_rows(connection, "numeric_comparison_rules", NUMERIC_RULE_FIELDS, rows("numeric-comparison-rules.csv"))
            insert_rows(connection, "items_of_supply", ITEM_FIELDS, rows("items-of-supply.csv"))
            insert_rows(connection, "upn_allocations", UPN_ALLOCATION_FIELDS, rows("upn-allocations.csv"))
            insert_rows(connection, "manufacturer_parts", MANUFACTURER_PART_FIELDS, rows("manufacturer-parts.csv"))
            insert_rows(connection, "supplier_offers", SUPPLIER_OFFER_FIELDS, rows("supplier-offers.csv"))
            insert_rows(connection, "supplier_offer_identifiers", SUPPLIER_OFFER_IDENTIFIER_FIELDS, rows("supplier-offer-identifiers.csv"))
            insert_rows(connection, "manufacturer_part_identifiers", PART_IDENTIFIER_FIELDS, rows("manufacturer-part-identifiers.csv"))
            insert_rows(connection, "external_identifiers", EXTERNAL_IDENTIFIER_FIELDS, rows("external-identifiers.csv"))
            insert_rows(connection, "manufacturer_part_external_references", PART_EXTERNAL_REFERENCE_FIELDS, rows("manufacturer-part-external-references.csv"))
            insert_rows(connection, "external_identifier_evidence", EXTERNAL_IDENTIFIER_EVIDENCE_FIELDS, rows("external-identifier-evidence.csv"))
            insert_rows(connection, "manufacturer_part_reviews", PART_REVIEW_FIELDS, rows("manufacturer-part-reviews.csv"))
            insert_rows(connection, "observations", OBSERVATION_FIELDS, rows("observations.csv"))
            insert_rows(connection, "specification_values", SPECIFICATION_FIELDS, rows("specification-values.csv"))
            insert_rows(connection, "match_candidates", MATCH_CANDIDATE_FIELDS, rows("match-candidates.csv"))
            insert_rows(connection, "equivalence_decisions", EQUIVALENCE_DECISION_FIELDS, rows("equivalence-decisions.csv"))
            insert_rows(connection, "item_reviews", ITEM_REVIEW_FIELDS, rows("item-reviews.csv"))
            insert_rows(connection, "item_memberships", ITEM_MEMBERSHIP_FIELDS, rows("item-memberships.csv"))
            insert_rows(connection, "pair_screenings", PAIR_SCREENING_FIELDS, rows("pair-screenings.csv"))
            foreign_key_errors = connection.execute("PRAGMA foreign_key_check").fetchall()
            if foreign_key_errors:
                raise RuntimeError(f"Foreign-key errors: {foreign_key_errors}")
            integrity = connection.execute("PRAGMA integrity_check").fetchone()
            if not integrity or integrity[0] != "ok":
                raise RuntimeError(f"Integrity check failed: {integrity}")
            connection.commit()
        finally:
            connection.close()
        output.unlink(missing_ok=True)
        temporary.replace(output)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "build" / "registry.sqlite",
        help="SQLite output path (default: registry/build/registry.sqlite)",
    )
    arguments = parser.parse_args()
    if validate_registry.main() != 0:
        return 1
    output = arguments.output.resolve()
    build(output)
    connection = sqlite3.connect(output)
    try:
        source_count = connection.execute("SELECT count(*) FROM sources").fetchone()[0]
        domain_count = connection.execute("SELECT count(*) FROM domains").fetchone()[0]
        part_count = connection.execute("SELECT count(*) FROM manufacturer_parts").fetchone()[0]
        observation_count = connection.execute("SELECT count(*) FROM observations").fetchone()[0]
    finally:
        connection.close()
    print(
        f"Built {output} with {source_count} sources, {domain_count} domains, "
        f"{part_count} manufacturer parts and {observation_count} observations."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
