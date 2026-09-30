#!/usr/bin/env python3
"""Screen cross-manufacturer pairs using versioned identity-profile rules."""

from __future__ import annotations

import argparse
import csv
import itertools
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ALGORITHM_VERSION = "cable-ladder-screen-0.1"
BLOCKING_PROPERTIES = (
    "PROP-FORM",
    "PROP-NOMINAL-WIDTH",
    "PROP-LENGTH",
    "PROP-MATERIAL",
    "PROP-SURFACE-PROTECTION",
    "PROP-RUNG-SPACING",
)
FIELDS = (
    "screening_id",
    "left_part_id",
    "right_part_id",
    "profile_id",
    "algorithm_version",
    "blocking_keys",
    "compared_properties",
    "matched_properties",
    "conflicting_properties",
    "missing_properties",
    "score",
    "result",
    "generated_at",
)


def normalized_value(row: sqlite3.Row) -> str:
    if row["normalized_text"] is not None:
        return str(row["normalized_text"]).strip().casefold()
    if row["normalized_number"] is not None:
        unit = row["unit_id"] or ""
        return f"{row['normalized_number']}|{unit}"
    return str(row["raw_value"]).strip().casefold()


def load_parts(connection: sqlite3.Connection) -> dict[str, dict[str, object]]:
    parts: dict[str, dict[str, object]] = {}
    for row in connection.execute(
        "SELECT manufacturer_part_id, manufacturer_id, profile_id, manufacturer_part_number "
        "FROM manufacturer_parts ORDER BY manufacturer_part_id"
    ):
        parts[row["manufacturer_part_id"]] = {
            "manufacturer_id": row["manufacturer_id"],
            "profile_id": row["profile_id"],
            "part_number": row["manufacturer_part_number"],
            "values": defaultdict(set),
        }
    for row in connection.execute(
        """
        SELECT o.manufacturer_part_id, sv.property_id, sv.raw_value,
               sv.normalized_text, sv.normalized_number, sv.unit_id
          FROM observations AS o
          JOIN specification_values AS sv ON sv.observation_id = o.observation_id
         WHERE o.review_state NOT IN ('rejected', 'superseded')
        """
    ):
        values = parts[row["manufacturer_part_id"]]["values"]
        assert isinstance(values, defaultdict)
        values[row["property_id"]].add(normalized_value(row))
    return parts


def required_properties(connection: sqlite3.Connection, profile_id: str) -> list[str]:
    return [
        row[0]
        for row in connection.execute(
            """
            SELECT property_id
              FROM identity_profile_properties
             WHERE profile_id = ? AND requirement = 'required'
             ORDER BY sequence_number
            """,
            (profile_id,),
        )
    ]


def join(values: list[str]) -> str:
    return ";".join(values)


def blocking_values(property_id: str, values: set[str]) -> set[str]:
    if property_id == "PROP-SURFACE-PROTECTION":
        return {
            "hot_dip_galvanized" if value.startswith("hot_dip_galvanized") else value
            for value in values
        }
    return values


def screen(connection: sqlite3.Connection, generated_at: str) -> list[dict[str, object]]:
    parts = load_parts(connection)
    output: list[dict[str, object]] = []
    sequence = 1
    for left_id, right_id in itertools.combinations(sorted(parts), 2):
        left = parts[left_id]
        right = parts[right_id]
        if left["manufacturer_id"] == right["manufacturer_id"]:
            continue
        if left["profile_id"] != right["profile_id"]:
            continue
        left_values = left["values"]
        right_values = right["values"]
        assert isinstance(left_values, defaultdict)
        assert isinstance(right_values, defaultdict)
        if any(
            not left_values[property_id]
            or not right_values[property_id]
            or blocking_values(property_id, left_values[property_id])
            != blocking_values(property_id, right_values[property_id])
            for property_id in BLOCKING_PROPERTIES
        ):
            continue

        required = required_properties(connection, str(left["profile_id"]))
        matched: list[str] = []
        conflicts: list[str] = []
        missing: list[str] = []
        for property_id in required:
            if not left_values[property_id] or not right_values[property_id]:
                missing.append(property_id)
            elif left_values[property_id] == right_values[property_id]:
                matched.append(property_id)
            else:
                conflicts.append(property_id)
        compared = len(matched) + len(conflicts)
        score = len(matched) / compared if compared else 0.0
        result = "hard_conflict" if conflicts else ("insufficient_evidence" if missing else "candidate")
        output.append(
            {
                "screening_id": f"SCREEN-{sequence:06d}",
                "left_part_id": left_id,
                "right_part_id": right_id,
                "profile_id": left["profile_id"],
                "algorithm_version": ALGORITHM_VERSION,
                "blocking_keys": join(list(BLOCKING_PROPERTIES)),
                "compared_properties": join(matched + conflicts),
                "matched_properties": join(matched),
                "conflicting_properties": join(conflicts),
                "missing_properties": join(missing),
                "score": f"{score:.6f}",
                "result": result,
                "generated_at": generated_at,
            }
        )
        sequence += 1
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=ROOT / "build" / "registry.sqlite")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check", type=Path, help="Fail if this saved screening CSV differs from generated output")
    parser.add_argument("--generated-at", default="2026-09-30")
    arguments = parser.parse_args()
    if not arguments.database.exists():
        print(f"Database not found: {arguments.database}. Run build_registry.py first.")
        return 2
    connection = sqlite3.connect(arguments.database)
    connection.row_factory = sqlite3.Row
    try:
        rows = screen(connection, arguments.generated_at)
    finally:
        connection.close()
    if arguments.output:
        arguments.output.parent.mkdir(parents=True, exist_ok=True)
        with arguments.output.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)
    if arguments.check:
        with arguments.check.open(encoding="utf-8-sig", newline="") as handle:
            expected = list(csv.DictReader(handle))
        comparable_rows = [{field: str(row[field]) for field in FIELDS} for row in rows]
        if expected != comparable_rows:
            print(f"Saved screening data is stale: {arguments.check}")
            return 1
        print(f"Saved screening data is reproducible: {arguments.check}")
    for row in rows:
        print(
            f"{row['left_part_id']} <> {row['right_part_id']}: {row['result']} "
            f"score={row['score']} conflicts={row['conflicting_properties']} "
            f"missing={row['missing_properties']}"
        )
    print(f"Screened candidates passing coarse blocking: {len(rows)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
