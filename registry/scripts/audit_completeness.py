#!/usr/bin/env python3
"""Report identity-property coverage and enforce the publication gate."""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--database",
        type=Path,
        default=ROOT / "build" / "registry.sqlite",
        help="SQLite registry path",
    )
    arguments = parser.parse_args()
    if not arguments.database.exists():
        print(f"Database not found: {arguments.database}. Run build_registry.py first.")
        return 2

    connection = sqlite3.connect(arguments.database)
    connection.row_factory = sqlite3.Row
    try:
        records = connection.execute(
            """
            SELECT mp.manufacturer_part_number,
                   o.observation_id,
                   o.review_state,
                   COUNT(DISTINCT ipp.property_id) AS required_count,
                   COUNT(DISTINCT sv.property_id) AS present_count,
                   GROUP_CONCAT(
                     CASE WHEN sv.property_id IS NULL THEN p.preferred_label END,
                     '; '
                   ) AS missing_properties
              FROM manufacturer_parts AS mp
              JOIN observations AS o
                ON o.manufacturer_part_id = mp.manufacturer_part_id
              JOIN identity_profile_properties AS ipp
                ON ipp.profile_id = mp.profile_id
               AND ipp.requirement = 'required'
              JOIN properties AS p
                ON p.property_id = ipp.property_id
         LEFT JOIN specification_values AS sv
                ON sv.observation_id = o.observation_id
               AND sv.property_id = ipp.property_id
          GROUP BY mp.manufacturer_part_number, o.observation_id, o.review_state
          ORDER BY mp.manufacturer_part_number, o.observation_id
            """
        ).fetchall()
    finally:
        connection.close()

    publication_errors = 0
    for record in records:
        missing = record["missing_properties"] or "none"
        print(
            f"{record['manufacturer_part_number']}: "
            f"{record['present_count']}/{record['required_count']} required properties; "
            f"review={record['review_state']}; missing={missing}"
        )
        if record["review_state"] == "accepted" and record["present_count"] != record["required_count"]:
            publication_errors += 1

    if publication_errors:
        print(f"Publication gate failed: {publication_errors} accepted observation(s) are incomplete.")
        return 1
    print("Publication gate passed: no incomplete observation is marked accepted.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
