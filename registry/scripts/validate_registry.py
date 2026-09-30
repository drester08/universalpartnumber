#!/usr/bin/env python3
"""Validate UPN registry seed data and ensure the SQLite schema loads."""

from __future__ import annotations

import csv
import sqlite3
import sys
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
