#!/usr/bin/env python3
"""Report identity-property coverage and enforce the publication gate."""

from __future__ import annotations

import argparse
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

import numeric_rules
import conditional_requirements


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
            SELECT mp.manufacturer_part_id, mp.manufacturer_part_number,
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
                       AND o.review_state = 'unreviewed') AS unreviewed_observations,
                   (SELECT COUNT(DISTINCT sv.specification_id)
                       FROM observations AS o
                       JOIN specification_values AS sv
                         ON sv.observation_id = o.observation_id
                       JOIN identity_profile_properties AS required_ipp
                         ON required_ipp.profile_id = mp.profile_id
                        AND required_ipp.property_id = sv.property_id
                        AND required_ipp.requirement = 'required'
                       JOIN properties AS mapped_property
                         ON mapped_property.property_id = sv.property_id
                      WHERE o.manufacturer_part_id = mp.manufacturer_part_id
                        AND o.review_state NOT IN ('rejected', 'superseded')
                        AND mapped_property.value_kind = 'code'
                        AND (
                            (SELECT COUNT(*)
                               FROM specification_value_mappings AS approved_mapping
                              WHERE approved_mapping.specification_id = sv.specification_id
                                AND approved_mapping.mapping_state = 'approved') != 1
                            OR
                            (SELECT COUNT(*)
                               FROM specification_value_mappings AS active_mapping
                              WHERE active_mapping.specification_id = sv.specification_id
                                AND active_mapping.mapping_state != 'rejected') != 1
                        )) AS unapproved_code_mappings
              FROM manufacturer_parts AS mp
              JOIN identity_profile_properties AS ipp
                ON ipp.profile_id = mp.profile_id
               AND ipp.requirement = 'required'
              JOIN properties AS p
                ON p.property_id = ipp.property_id
          ORDER BY mp.manufacturer_part_id, ipp.sequence_number
            """
        ).fetchall()
        numeric_records = connection.execute(
            """
            SELECT mp.profile_id, mp.manufacturer_part_id,
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
        conditional_parts = conditional_requirements.unresolved_parts(connection)
        conditional_reviews = connection.execute(
            "SELECT mp.manufacturer_part_id, mp.manufacturer_part_number, "
            "COALESCE((SELECT decision FROM manufacturer_part_reviews r "
            "WHERE r.manufacturer_part_id=mp.manufacturer_part_id "
            "ORDER BY decided_at DESC, review_id DESC LIMIT 1), 'unreviewed') "
            "FROM manufacturer_parts mp ORDER BY mp.manufacturer_part_id"
        ).fetchall()
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
                    record["manufacturer_part_id"],
                    record["property_id"],
                    record["preferred_label"],
                )
            ].add(value)

    conflicts: dict[str, list[str]] = defaultdict(list)
    for (profile_id, part_id, property_id, label), values in numeric_values.items():
        if len(values) < 2:
            continue
        rule = governed_numeric_rules.get((profile_id, property_id))
        if rule is None or not numeric_rules.sets_compatible(values, values, rule):
            conflicts[part_id].append(label)

    parts: dict[str, dict[str, object]] = {}
    for record in records:
        part = parts.setdefault(
            record["manufacturer_part_id"],
            {
                "required": 0,
                "part_number": record["manufacturer_part_number"],
                "present": 0,
                "missing": [],
                "review": record["review_decision"],
                "unreviewed_observations": record["unreviewed_observations"],
                "unapproved_code_mappings": record["unapproved_code_mappings"],
                "conflicts": conflicts.get(record["manufacturer_part_id"], []),
            },
        )
        part["required"] = int(part["required"]) + 1
        if record["property_present"]:
            part["present"] = int(part["present"]) + 1
        else:
            missing_list = part["missing"]
            assert isinstance(missing_list, list)
            missing_list.append(record["preferred_label"])

    conditional_errors = set()
    for row in conditional_reviews:
        if row[0] not in conditional_parts:
            continue
        labels = '; '.join(label for _, label in conditional_parts[row[0]])
        print(f'{row[1]}: unresolved_conditional_applicability={labels}; manufacturer_part_id={row[0]}')
        if row[2] == 'accepted':
            conditional_errors.add(row[0])
    publication_errors = 0
    for part_id, part in parts.items():
        missing_list = part["missing"]
        assert isinstance(missing_list, list)
        missing = "; ".join(missing_list) or "none"
        conflict_list = part["conflicts"]
        assert isinstance(conflict_list, list)
        source_conflicts = "; ".join(conflict_list) or "none"
        print(
            f"{part['part_number']}: {part['present']}/{part['required']} required properties; "
            f"review={part['review']}; unreviewed_observations={part['unreviewed_observations']}; "
            f"unapproved_code_mappings={part['unapproved_code_mappings']}; "
            f"missing={missing}; source_conflicts={source_conflicts}; manufacturer_part_id={part_id}"
        )
        if part["review"] == "accepted" and (
            part["present"] != part["required"]
            or int(part["unreviewed_observations"]) > 0
            or int(part["unapproved_code_mappings"]) > 0
            or bool(conflict_list)
            or part_id in conditional_errors
        ):
            publication_errors += 1

    # A profile containing only conditional fields has no rows in the required-
    # property query above. It must still fail for an accepted part.
    publication_errors += len(conditional_errors - parts.keys())

    if publication_errors:
        print(f"Publication gate failed: {publication_errors} accepted part record(s) fail evidence or normalization governance.")
        return 1
    print("Publication gate passed: no accepted part has incomplete, unreviewed, conflicting, unnormalized evidence or unresolved conditional applicability.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
