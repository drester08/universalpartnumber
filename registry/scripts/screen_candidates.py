#!/usr/bin/env python3
"""Screen cross-manufacturer pairs using versioned identity-profile rules."""

from __future__ import annotations

import argparse
import csv
import itertools
import re
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

import numeric_rules


ROOT = Path(__file__).resolve().parents[1]
PROFILE_RULES = {
    "PROFILE-ANGLE-EQUAL-HOT-ROLLED-STEEL-0.1": {
        "algorithm_version": "equal-angle-screen-0.1",
        "blocking_properties": ("PROP-ANGLE-LEG-A", "PROP-ANGLE-LEG-B", "PROP-ANGLE-THICKNESS"),
    },
    "PROFILE-CABLE-LADDER-STRAIGHT-STEEL-0.1": {
        "algorithm_version": "cable-ladder-screen-0.3",
        "blocking_properties": (
            "PROP-FORM",
            "PROP-NOMINAL-WIDTH",
            "PROP-LENGTH",
            "PROP-MATERIAL",
            "PROP-SURFACE-PROTECTION",
            "PROP-RUNG-SPACING",
        ),
    },
    "PROFILE-FASTENER-HEX-FULL-ISO4017-0.1": {
        "algorithm_version": "iso4017-hex-screen-0.2",
        "blocking_properties": (
            "PROP-FASTENER-STANDARD",
            "PROP-THREAD-DIAMETER",
            "PROP-FASTENER-LENGTH",
            "PROP-THREAD-EXTENT",
            "PROP-HEAD-FORM",
            "PROP-DRIVE-FORM",
            "PROP-FASTENER-MATERIAL",
            "PROP-PROPERTY-CLASS",
            "PROP-FASTENER-SURFACE",
        ),
    },
    "PROFILE-WIRE-MESH-BASKET-STRAIGHT-STEEL-0.1": {
        "algorithm_version": "wire-mesh-screen-0.2",
        "blocking_properties": (
            "PROP-FORM",
            "PROP-MATERIAL",
        ),
    },
    "PROFILE-BEARING-DGBB-1R-DOUBLE-METAL-SHIELD-0.1": {
        "algorithm_version": "bearing-dgbb-screen-0.1",
        "blocking_properties": (
            "PROP-BEARING-GEOMETRY",
            "PROP-BORE-DIAMETER",
            "PROP-OUTSIDE-DIAMETER",
            "PROP-BEARING-WIDTH",
            "PROP-BEARING-CLOSURE",
        ),
    },
}
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


def normalized_value(row: sqlite3.Row) -> str | numeric_rules.NumericValue:
    numeric = numeric_rules.to_base_value(row)
    if numeric is not None:
        return numeric
    if row["canonical_code"] is not None:
        return str(row["canonical_code"]).strip().casefold()
    if row["normalized_text"] is not None:
        return str(row["normalized_text"]).strip().casefold()
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
               sv.normalized_text, sv.normalized_number, sv.unit_id,
               u.quantity_kind, u.conversion_factor, u.conversion_offset,
               cv.canonical_code, p.value_kind
          FROM observations AS o
          JOIN specification_values AS sv ON sv.observation_id = o.observation_id
          JOIN properties AS p ON p.property_id = sv.property_id
          LEFT JOIN units AS u ON u.unit_id = sv.unit_id
          LEFT JOIN specification_value_mappings AS svm
            ON svm.specification_id = sv.specification_id
           AND svm.mapping_state != 'rejected'
          LEFT JOIN controlled_values AS cv
            ON cv.controlled_value_id = svm.controlled_value_id
         WHERE o.review_state NOT IN ('rejected', 'superseded')
        """
    ):
        # A raw manufacturer designation is not a semantic comparison value.
        # Typed normalization may support research screening; approval still
        # requires the explicit terminology-mapping governance gates.
        if row["value_kind"] == "code" and row["canonical_code"] is None and row["normalized_text"] is None:
            continue
        values = parts[row["manufacturer_part_id"]]["values"]
        assert isinstance(values, defaultdict)
        values[row["property_id"]].add(normalized_value(row))
    return parts


def required_properties(connection: sqlite3.Connection, profile_id: str) -> list[tuple[str, str]]:
    return [
        (row[0], row[1])
        for row in connection.execute(
            """
            SELECT property_id, comparison_rule
              FROM identity_profile_properties
             WHERE profile_id = ? AND requirement = 'required'
             ORDER BY sequence_number
            """,
            (profile_id,),
        )
    ]


def join(values: list[str]) -> str:
    # CSV ingestion intentionally converts empty fields to SQL NULL, while the
    # screening audit columns are NOT NULL. Preserve an explicit machine value.
    return ";".join(values) if values else "none"


def blocking_values(property_id: str, values: set[object]) -> set[object]:
    if property_id == "PROP-MATERIAL":
        return {
            "steel" if value in {"mild_steel", "carbon_steel"} else value
            for value in values
        }
    if property_id == "PROP-SURFACE-PROTECTION":
        return {
            "hot_dip_galvanized"
            if isinstance(value, str) and value.startswith("hot_dip_galvanized")
            else value
            for value in values
        }
    if property_id == "PROP-COATING-SPEC":
        return {
            "blue_passivated"
            if isinstance(value, str) and value.startswith("blue_passivated")
            else value
            for value in values
        }
    if property_id == "PROP-FASTENER-SURFACE":
        return {
            "electrolytic_zinc"
            if isinstance(value, str) and value.startswith("electrolytic_zinc")
            else value
            for value in values
        }
    if property_id == "PROP-CAGE-CONSTRUCTION":
        return {
            "sheet_metal_cage"
            if value in {"sheet_metal_unspecified", "pressed_steel"}
            else value
            for value in values
        }
    return values


def compatible_but_less_specific(property_id: str, left: set[object], right: set[object]) -> bool:
    """Return true when values share a coarse family but do not prove exact equality."""
    return property_id in {
        "PROP-MATERIAL",
        "PROP-SURFACE-PROTECTION",
        "PROP-COATING-SPEC",
        "PROP-FASTENER-SURFACE",
        "PROP-CAGE-CONSTRUCTION",
    } and (
        blocking_values(property_id, left) == blocking_values(property_id, right)
    )


def compare_property(
    profile_id: str,
    property_id: str,
    comparison_rule: str,
    left: set[object],
    right: set[object],
    governed_numeric_rules: dict[tuple[str, str], numeric_rules.NumericRule],
) -> str:
    if not left or not right:
        return "missing"
    if profile_id == "PROFILE-ANGLE-EQUAL-HOT-ROLLED-STEEL-0.1":
        generic = {"unknown", "unspecified", "not_stated", "not_applicable", "cq", "commercial_quality"}
        if any(isinstance(v, str) and v in generic for v in left | right):
            return "missing"
        scope_codes = {"PROP-ANGLE-GEOMETRY": "equal_leg_angle_90_degree",
                       "PROP-SECTION-PRODUCTION-ROUTE": "hot_rolled"}
        if property_id in scope_codes and left | right != {scope_codes[property_id]}:
            return "missing"
    if profile_id == "PROFILE-ANGLE-EQUAL-HOT-ROLLED-STEEL-0.1" and property_id == "PROP-MATERIAL-GRADE":
        # This draft scope requires impact-quality grades. A broad grade family
        # or commercial-quality assertion never proves the full designation.
        if any(not isinstance(v, str) or not re.fullmatch(r"s\d{3}(?:jr|j0|j2|k2)", v) for v in left | right):
            return "missing"
    if comparison_rule == "numeric_exact":
        rule = governed_numeric_rules.get((profile_id, property_id))
        if rule is None:
            return "missing"
        if not all(isinstance(value, numeric_rules.NumericValue) for value in left | right):
            return "missing"
        numeric_left = {value for value in left if isinstance(value, numeric_rules.NumericValue)}
        numeric_right = {value for value in right if isinstance(value, numeric_rules.NumericValue)}
        return "match" if numeric_rules.sets_compatible(numeric_left, numeric_right, rule) else "conflict"
    if left == right:
        return "match"
    if compatible_but_less_specific(property_id, left, right):
        return "missing"
    return "conflict"


def screen(connection: sqlite3.Connection, generated_at: str) -> list[dict[str, object]]:
    parts = load_parts(connection)
    governed_numeric_rules = numeric_rules.load_rules(connection)
    output: list[dict[str, object]] = []
    sequence = 1
    for left_id, right_id in itertools.combinations(sorted(parts), 2):
        left = parts[left_id]
        right = parts[right_id]
        if left["manufacturer_id"] == right["manufacturer_id"]:
            continue
        if left["profile_id"] != right["profile_id"]:
            continue
        profile_id = str(left["profile_id"])
        rule = PROFILE_RULES.get(profile_id)
        if rule is None:
            continue
        blocking_properties = tuple(rule["blocking_properties"])
        left_values = left["values"]
        right_values = right["values"]
        assert isinstance(left_values, defaultdict)
        assert isinstance(right_values, defaultdict)
        profile_properties = dict(required_properties(connection, profile_id))
        if any(
            (
                compare_property(
                    profile_id,
                    property_id,
                    profile_properties[property_id],
                    left_values[property_id],
                    right_values[property_id],
                    governed_numeric_rules,
                )
                != "match"
                if profile_properties[property_id] == "numeric_exact"
                else blocking_values(property_id, left_values[property_id])
                != blocking_values(property_id, right_values[property_id])
            )
            for property_id in blocking_properties
        ):
            continue

        required = list(profile_properties.items())
        matched: list[str] = []
        conflicts: list[str] = []
        missing: list[str] = []
        for property_id, comparison_rule in required:
            outcome = compare_property(
                profile_id,
                property_id,
                comparison_rule,
                left_values[property_id],
                right_values[property_id],
                governed_numeric_rules,
            )
            if outcome == "missing":
                missing.append(property_id)
            elif outcome == "match":
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
                "algorithm_version": rule["algorithm_version"],
                "blocking_keys": join(list(blocking_properties)),
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
    parser.add_argument("--generated-at", default="2026-10-01")
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
