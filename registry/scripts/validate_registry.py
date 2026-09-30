#!/usr/bin/env python3
"""Validate UPN registry seed data and ensure the SQLite schema loads."""

from __future__ import annotations

import csv
import sqlite3
import string
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import urlparse

import upn
import build_dataset_findings


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def read_csv(name: str) -> list[dict[str, str]]:
    path = DATA / name
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def require_unique(rows: list[dict[str, str]], field: str, errors: list[str]) -> None:
    values = [row.get(field, "").strip() for row in rows]
    missing = [index + 2 for index, value in enumerate(values) if not value]
    if missing:
        errors.append(f"{field}: missing on CSV lines {missing}")
    duplicates = sorted({value for value in values if value and values.count(value) > 1})
    if duplicates:
        errors.append(f"{field}: duplicate values {duplicates}")


def validate_sources(errors: list[str]) -> int:
    rows = read_csv("source-register.csv")
    require_unique(rows, "source_id", errors)
    require_unique(rows, "source_url", errors)
    valid_access = {"public", "registration", "subscription", "purchase", "unknown"}
    valid_types = {"standard", "dictionary", "classification", "catalog", "datasheet", "webpage", "database", "other"}
    valid_license = {"open", "attribution", "restricted", "review_required", "unknown"}
    valid_ingestion = {"metadata_only", "license_verified", "license_review", "reference_only", "blocked"}
    for line, row in enumerate(rows, start=2):
        if row["source_type"] not in valid_types:
            errors.append(f"source-register.csv:{line}: invalid source_type")
        parsed = urlparse(row["source_url"])
        if parsed.scheme != "https" or not parsed.netloc:
            errors.append(f"source-register.csv:{line}: source_url must be an absolute HTTPS URL")
        if row["license_url"]:
            license_url = urlparse(row["license_url"])
            if license_url.scheme != "https" or not license_url.netloc:
                errors.append(f"source-register.csv:{line}: license_url must be an absolute HTTPS URL")
        if row["access_state"] not in valid_access:
            errors.append(f"source-register.csv:{line}: invalid access_state")
        if row["license_state"] not in valid_license:
            errors.append(f"source-register.csv:{line}: invalid license_state")
        if row["ingestion_status"] not in valid_ingestion:
            errors.append(f"source-register.csv:{line}: invalid ingestion_status")
        if row["ingestion_status"] == "license_verified" and row["license_state"] not in {"open", "attribution"}:
            errors.append(f"source-register.csv:{line}: verified ingestion requires an open or attribution licence")
        try:
            tier = int(row["authority_tier"])
            if tier not in range(1, 5):
                raise ValueError
        except ValueError:
            errors.append(f"source-register.csv:{line}: authority_tier must be 1-4")
    return len(rows)


def validate_source_datasets(errors: list[str]) -> int:
    rows = read_csv("source-datasets.csv")
    require_unique(rows, "dataset_id", errors)
    require_unique(rows, "local_path", errors)
    valid_provenance = {"user_supplied", "external_export", "partner_feed"}
    valid_sensitivity = {"public", "business_contact", "commercial", "confidential", "unknown"}
    valid_state = {"unverified", "profiled", "validated", "rejected"}
    valid_use = {"structure_research", "identity_evidence", "ingestion_candidate", "blocked"}
    for line, row in enumerate(rows, start=2):
        if row["provenance_type"] not in valid_provenance:
            errors.append(f"source-datasets.csv:{line}: invalid provenance_type")
        if row["sensitivity"] not in valid_sensitivity:
            errors.append(f"source-datasets.csv:{line}: invalid sensitivity")
        if row["verification_state"] not in valid_state:
            errors.append(f"source-datasets.csv:{line}: invalid verification_state")
        if row["allowed_use"] not in valid_use:
            errors.append(f"source-datasets.csv:{line}: invalid allowed_use")
        if row["allowed_use"] == "identity_evidence" and row["verification_state"] != "validated":
            errors.append(f"source-datasets.csv:{line}: identity evidence must be validated")
        digest = row["sha256"].strip()
        if len(digest) != 64 or any(character not in string.hexdigits for character in digest):
            errors.append(f"source-datasets.csv:{line}: invalid SHA-256")
        try:
            if int(row["row_count"]) <= 0 or int(row["column_count"]) <= 0:
                raise ValueError
        except ValueError:
            errors.append(
                f"source-datasets.csv:{line}: row_count and column_count must be positive integers"
            )
        if not row["local_path"].startswith("registry/artifacts/"):
            errors.append(f"source-datasets.csv:{line}: local_path must remain under registry/artifacts")
    return len(rows)


def validate_domains(errors: list[str]) -> int:
    rows = read_csv("domain-seed.csv")
    require_unique(rows, "domain_id", errors)
    require_unique(rows, "label", errors)
    for line, row in enumerate(rows, start=2):
        if row["status"] not in {"seed", "reviewed", "retired"}:
            errors.append(f"domain-seed.csv:{line}: invalid status")
        if not row["scope_note"].strip():
            errors.append(f"domain-seed.csv:{line}: scope_note is required")
    return len(rows)


def gs1_mod10_valid(identifier: str) -> bool:
    if len(identifier) < 2 or not identifier.isdigit():
        return False
    body = identifier[:-1]
    total = sum(
        int(digit) * (3 if index % 2 == 0 else 1)
        for index, digit in enumerate(reversed(body))
    )
    expected_check_digit = (10 - total % 10) % 10
    return expected_check_digit == int(identifier[-1])


def validate_trade_identifiers(errors: list[str]) -> None:
    valid_lengths = {
        "ean": {8, 13},
        "upc": {12},
        "gtin": {8, 12, 13, 14},
    }
    for name in ("supplier-offer-identifiers.csv", "manufacturer-part-identifiers.csv"):
        for line, row in enumerate(read_csv(name), start=2):
            scheme = row["scheme"].strip().lower()
            if scheme not in valid_lengths:
                continue
            identifier = row["identifier_value"].strip()
            if len(identifier) not in valid_lengths[scheme]:
                allowed = ", ".join(str(length) for length in sorted(valid_lengths[scheme]))
                errors.append(f"{name}:{line}: {scheme} length must be one of {allowed}")
            elif not gs1_mod10_valid(identifier):
                errors.append(f"{name}:{line}: {scheme} has an invalid GS1 Mod-10 check digit")


def validate_numeric_rules(errors: list[str]) -> None:
    rules = read_csv("numeric-comparison-rules.csv")
    require_unique(rules, "rule_id", errors)
    rule_keys = [(row["profile_id"], row["property_id"]) for row in rules]
    duplicate_keys = sorted({key for key in rule_keys if rule_keys.count(key) > 1})
    if duplicate_keys:
        errors.append(f"numeric-comparison-rules.csv: duplicate profile/property rules {duplicate_keys}")

    properties = {row["property_id"]: row for row in read_csv("properties.csv")}
    profiles = {row["profile_id"] for row in read_csv("identity-profiles.csv")}
    quantity_kinds = {row["quantity_kind"] for row in read_csv("units.csv") if row["quantity_kind"]}
    required_numeric = {
        (row["profile_id"], row["property_id"])
        for row in read_csv("identity-profile-properties.csv")
        if row["requirement"] == "required" and row["comparison_rule"] == "numeric_exact"
    }

    for line, row in enumerate(rules, start=2):
        if row["profile_id"] not in profiles:
            errors.append(f"numeric-comparison-rules.csv:{line}: unknown profile_id")
        property_row = properties.get(row["property_id"])
        if property_row is None:
            errors.append(f"numeric-comparison-rules.csv:{line}: unknown property_id")
        elif property_row["value_kind"] != "number":
            errors.append(f"numeric-comparison-rules.csv:{line}: property must have number value_kind")
        if row["comparison_method"] != "absolute_or_relative":
            errors.append(f"numeric-comparison-rules.csv:{line}: unsupported comparison_method")
        if row["quantity_kind"] not in quantity_kinds:
            errors.append(f"numeric-comparison-rules.csv:{line}: unknown quantity_kind")
        try:
            absolute = Decimal(row["absolute_tolerance_base"])
            relative = Decimal(row["relative_tolerance"])
            if absolute < 0 or relative < 0 or relative > Decimal("0.02"):
                raise InvalidOperation
        except (InvalidOperation, ValueError):
            errors.append(
                f"numeric-comparison-rules.csv:{line}: tolerances must be non-negative decimals and relative_tolerance cannot exceed 0.02"
            )

    missing = sorted(required_numeric - set(rule_keys))
    extra = sorted(set(rule_keys) - required_numeric)
    if missing:
        errors.append(f"numeric-comparison-rules.csv: missing required numeric rules {missing}")
    if extra:
        errors.append(f"numeric-comparison-rules.csv: rules may only govern required numeric_exact properties {extra}")


def validate_upn_seeds(errors: list[str]) -> None:
    items = read_csv("items-of-supply.csv")
    allocations = read_csv("upn-allocations.csv")
    require_unique(items, "item_id", errors)
    require_unique(allocations, "allocation_id", errors)
    seen_upns: set[str] = set()
    seen_sequences: set[int] = set()
    for line, row in enumerate(items, start=2):
        identifier = row["upn"].strip()
        if identifier and not upn.valid_upn(identifier):
            errors.append(f"items-of-supply.csv:{line}: invalid UPN syntax or check digit")
        if identifier and identifier in seen_upns:
            errors.append(f"items-of-supply.csv:{line}: duplicate UPN")
        if identifier:
            seen_upns.add(identifier)
    for line, row in enumerate(allocations, start=2):
        try:
            sequence = int(row["sequence_number"])
            expected = upn.format_upn(sequence)
        except ValueError:
            errors.append(f"upn-allocations.csv:{line}: invalid sequence_number")
            continue
        if sequence in seen_sequences:
            errors.append(f"upn-allocations.csv:{line}: duplicate sequence_number")
        seen_sequences.add(sequence)
        if row["upn"] != expected:
            errors.append(f"upn-allocations.csv:{line}: UPN does not match its sequence/check digit")


def validate_controlled_values(errors: list[str]) -> None:
    values = read_csv("controlled-values.csv")
    mappings = read_csv("specification-value-mappings.csv")
    specifications = {
        row["specification_id"]: row
        for row in read_csv("specification-values.csv")
    }
    properties = {
        row["property_id"]: row
        for row in read_csv("properties.csv")
    }
    require_unique(values, "controlled_value_id", errors)
    require_unique(mappings, "mapping_id", errors)
    value_keys = [(row["property_id"], row["canonical_code"]) for row in values]
    duplicate_value_keys = sorted({key for key in value_keys if value_keys.count(key) > 1})
    if duplicate_value_keys:
        errors.append(f"controlled-values.csv: duplicate property/code values {duplicate_value_keys}")
    values_by_id = {row["controlled_value_id"]: row for row in values}
    for line, row in enumerate(values, start=2):
        if row["property_id"] not in properties:
            errors.append(f"controlled-values.csv:{line}: unknown property_id")
        elif properties[row["property_id"]]["value_kind"] != "code":
            errors.append(f"controlled-values.csv:{line}: controlled values require a code property")
        if row["lifecycle_state"] not in {"active", "deprecated"}:
            errors.append(f"controlled-values.csv:{line}: invalid lifecycle_state")
        if not row["canonical_code"].strip() or not row["preferred_label"].strip() or not row["definition"].strip():
            errors.append(f"controlled-values.csv:{line}: code, label, and definition are required")

    valid_bases = {"source_exact", "manufacturer_definition", "standard_crosswalk", "expert_interpretation"}
    valid_states = {"proposed", "approved", "rejected"}
    mapping_keys: list[tuple[str, str]] = []
    for line, row in enumerate(mappings, start=2):
        mapping_keys.append((row["specification_id"], row["controlled_value_id"]))
        specification = specifications.get(row["specification_id"])
        value = values_by_id.get(row["controlled_value_id"])
        if specification is None:
            errors.append(f"specification-value-mappings.csv:{line}: unknown specification_id")
        if value is None:
            errors.append(f"specification-value-mappings.csv:{line}: unknown controlled_value_id")
        if row["property_id"] not in properties:
            errors.append(f"specification-value-mappings.csv:{line}: unknown property_id")
        if specification is not None and specification["property_id"] != row["property_id"]:
            errors.append(f"specification-value-mappings.csv:{line}: specification property mismatch")
        if value is not None and value["property_id"] != row["property_id"]:
            errors.append(f"specification-value-mappings.csv:{line}: controlled-value property mismatch")
        if row["mapping_basis"] not in valid_bases:
            errors.append(f"specification-value-mappings.csv:{line}: invalid mapping_basis")
        if row["mapping_state"] not in valid_states:
            errors.append(f"specification-value-mappings.csv:{line}: invalid mapping_state")
        if row["mapping_state"] == "approved" and (
            not row["reviewer"].strip()
            or not row["reviewed_at"].strip()
            or row["reviewer"] == row["proposed_by"]
        ):
            errors.append(f"specification-value-mappings.csv:{line}: approval requires an independent reviewer and date")
    duplicate_mapping_keys = sorted({key for key in mapping_keys if mapping_keys.count(key) > 1})
    if duplicate_mapping_keys:
        errors.append(f"specification-value-mappings.csv: duplicate specification/value mappings {duplicate_mapping_keys}")


def validate_dataset_findings(errors: list[str]) -> None:
    """Findings are reproducible research snapshots, never mutable approvals."""
    try:
        findings, refs = build_dataset_findings.derive(ROOT)
        for name, fields, records in (
            ('dataset-findings.csv', build_dataset_findings.FINDING_FIELDS, findings),
            ('dataset-finding-rows.csv', build_dataset_findings.ROW_FIELDS, refs),
        ):
            expected = [{f: str(r[f]) for f in fields} for r in records]
            if read_csv(name) != expected:
                errors.append(f'{name}: stale or modified derived findings snapshot')
        affected = {r['dataset_id'] for r in findings}
        for dataset in read_csv('source-datasets.csv'):
            if dataset['dataset_id'] in affected and (
                dataset['verification_state'] == 'validated' or dataset['allowed_use'] == 'identity_evidence'
            ):
                errors.append(f"{dataset['dataset_id']}: unresolved findings prevent identity promotion")
    except (OSError, ValueError, KeyError, TypeError, StopIteration) as exc:
        errors.append(f'Dataset finding evidence invalid: {exc}')


def validate_schema(errors: list[str]) -> int:
    schema = (ROOT / "schema.sql").read_text(encoding="utf-8")
    try:
        connection = sqlite3.connect(":memory:")
        connection.executescript(schema)
        result = connection.execute(
            "SELECT count(*) FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
        ).fetchone()
        return int(result[0]) if result else 0
    except sqlite3.Error as exc:
        errors.append(f"schema.sql: {exc}")
        return 0


def main() -> int:
    errors: list[str] = []
    source_count = validate_sources(errors)
    dataset_count = validate_source_datasets(errors)
    domain_count = validate_domains(errors)
    validate_trade_identifiers(errors)
    validate_numeric_rules(errors)
    validate_upn_seeds(errors)
    validate_controlled_values(errors)
    validate_dataset_findings(errors)
    table_count = validate_schema(errors)
    if errors:
        print("Registry validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(
        f"Registry validation passed: {source_count} sources, {dataset_count} reference datasets, "
        f"{domain_count} domains, {table_count} tables."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
