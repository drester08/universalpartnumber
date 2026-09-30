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
            insert_rows(connection, "domains", DOMAIN_FIELDS, rows("domain-seed.csv"))
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
    finally:
        connection.close()
    print(f"Built {output} with {source_count} sources and {domain_count} domains.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
