#!/usr/bin/env python3
"""Validate UPN registry seed data and ensure the SQLite schema loads."""

from __future__ import annotations

import csv
import sqlite3
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import urlparse


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
    valid_license = {"open", "attribution", "restricted", "review_required", "unknown"}
    valid_ingestion = {"metadata_only", "license_verified", "license_review", "reference_only", "blocked"}
    for line, row in enumerate(rows, start=2):
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
    domain_count = validate_domains(errors)
    validate_trade_identifiers(errors)
    validate_numeric_rules(errors)
    table_count = validate_schema(errors)
    if errors:
        print("Registry validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Registry validation passed: {source_count} sources, {domain_count} domains, {table_count} tables.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
