#!/usr/bin/env python3
"""Report identity-property coverage and enforce the publication gate."""

from __future__ import annotations

import argparse
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

import numeric_rules


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
                   p.preferred_label,
                   CASE WHEN EXISTS (
                     SELECT 1
                       FROM observations AS o
                       JOIN specification_values AS sv
                         ON sv.observation_id = o.observation_id
                      WHERE o.manufacturer_part_id = mp.manufacturer_part_id
                        AND o.review_state NOT IN ('rejected', 'superseded')
                        AND sv.property_id = ipp.property_id
                   ) THEN 1 ELSE 0 END AS property_present,
                   COALESCE((
                     SELECT mpr.decision
                       FROM manufacturer_part_reviews AS mpr
                      WHERE mpr.manufacturer_part_id = mp.manufacturer_part_id
                      ORDER BY mpr.decided_at DESC, mpr.review_id DESC
                      LIMIT 1
                   ), 'unreviewed') AS review_decision,
                   (SELECT COUNT(*)
                      FROM observations AS o
                     WHERE o.manufacturer_part_id = mp.manufacturer_part_id
                       AND o.review_state = 'unreviewed') AS unreviewed_observations
              FROM manufacturer_parts AS mp
              JOIN identity_profile_properties AS ipp
                ON ipp.profile_id = mp.profile_id
               AND ipp.requirement = 'required'
              JOIN properties AS p
                ON p.property_id = ipp.property_id
          ORDER BY mp.manufacturer_part_number, ipp.sequence_number
            """
        ).fetchall()
        numeric_records = connection.execute(
            """
            SELECT mp.profile_id,
                   mp.manufacturer_part_number,
                   ipp.property_id,
                   p.preferred_label,
                   sv.normalized_number,
                   u.quantity_kind,
                   u.conversion_factor,
                   u.conversion_offset
              FROM manufacturer_parts AS mp
              JOIN identity_profile_properties AS ipp
                ON ipp.profile_id = mp.profile_id
               AND ipp.requirement = 'required'
              JOIN properties AS p
                ON p.property_id = ipp.property_id
              JOIN observations AS o
                ON o.manufacturer_part_id = mp.manufacturer_part_id
               AND o.review_state NOT IN ('rejected', 'superseded')
              JOIN specification_values AS sv
                ON sv.observation_id = o.observation_id
               AND sv.property_id = ipp.property_id
              JOIN units AS u ON u.unit_id = sv.unit_id
             WHERE sv.normalized_number IS NOT NULL
          ORDER BY mp.manufacturer_part_number, ipp.sequence_number, o.observation_id
            """
        ).fetchall()
        governed_numeric_rules = numeric_rules.load_rules(connection)
    finally:
        connection.close()

    numeric_values: dict[
        tuple[str, str, str, str], set[numeric_rules.NumericValue]
    ] = defaultdict(set)
    for record in numeric_records:
        value = numeric_rules.to_base_value(record)
        if value is not None:
            numeric_values[
                (
                    record["profile_id"],
                    record["manufacturer_part_number"],
                    record["property_id"],
                    record["preferred_label"],
                )
            ].add(value)

    conflicts: dict[str, list[str]] = defaultdict(list)
    for (profile_id, part_number, property_id, label), values in numeric_values.items():
        if len(values) < 2:
            continue
        rule = governed_numeric_rules.get((profile_id, property_id))
        if rule is None or not numeric_rules.sets_compatible(values, values, rule):
            conflicts[part_number].append(label)

    parts: dict[str, dict[str, object]] = {}
    for record in records:
        part = parts.setdefault(
            record["manufacturer_part_number"],
            {
                "required": 0,
                "present": 0,
                "missing": [],
                "review": record["review_decision"],
                "unreviewed_observations": record["unreviewed_observations"],
                "conflicts": conflicts.get(record["manufacturer_part_number"], []),
            },
        )
        part["required"] = int(part["required"]) + 1
        if record["property_present"]:
            part["present"] = int(part["present"]) + 1
        else:
            missing_list = part["missing"]
            assert isinstance(missing_list, list)
            missing_list.append(record["preferred_label"])

    publication_errors = 0
    for part_number, part in parts.items():
        missing_list = part["missing"]
        assert isinstance(missing_list, list)
        missing = "; ".join(missing_list) or "none"
        conflict_list = part["conflicts"]
        assert isinstance(conflict_list, list)
        source_conflicts = "; ".join(conflict_list) or "none"
        print(
            f"{part_number}: {part['present']}/{part['required']} required properties; "
            f"review={part['review']}; unreviewed_observations={part['unreviewed_observations']}; "
            f"missing={missing}; source_conflicts={source_conflicts}"
        )
        if part["review"] == "accepted" and (
            part["present"] != part["required"]
            or int(part["unreviewed_observations"]) > 0
            or bool(conflict_list)
        ):
            publication_errors += 1

    if publication_errors:
        print(f"Publication gate failed: {publication_errors} accepted observation(s) are incomplete.")
        return 1
    print("Publication gate passed: no incomplete or unreviewed evidence set has an accepted part review.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
