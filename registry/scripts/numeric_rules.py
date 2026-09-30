"""Governed cross-unit comparison for identity-defining numeric properties."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class NumericRule:
    quantity_kind: str
    absolute_tolerance: Decimal
    relative_tolerance: Decimal


@dataclass(frozen=True)
class NumericValue:
    quantity_kind: str
    base_value: Decimal


def load_rules(connection: sqlite3.Connection) -> dict[tuple[str, str], NumericRule]:
    return {
        (row["profile_id"], row["property_id"]): NumericRule(
            quantity_kind=row["quantity_kind"],
            absolute_tolerance=Decimal(row["absolute_tolerance_base"]),
            relative_tolerance=Decimal(row["relative_tolerance"]),
        )
        for row in connection.execute(
            """
            SELECT profile_id, property_id, quantity_kind,
                   absolute_tolerance_base, relative_tolerance
              FROM numeric_comparison_rules
            """
        )
    }


def to_base_value(row: sqlite3.Row) -> NumericValue | None:
    if row["normalized_number"] is None or row["quantity_kind"] is None:
        return None
    factor = Decimal(row["conversion_factor"] or "1")
    offset = Decimal(row["conversion_offset"] or "0")
    return NumericValue(
        quantity_kind=row["quantity_kind"],
        base_value=Decimal(row["normalized_number"]) * factor + offset,
    )


def compatible(left: NumericValue, right: NumericValue, rule: NumericRule) -> bool:
    if left.quantity_kind != rule.quantity_kind or right.quantity_kind != rule.quantity_kind:
        return False
    scale = max(abs(left.base_value), abs(right.base_value))
    tolerance = max(rule.absolute_tolerance, scale * rule.relative_tolerance)
    return abs(left.base_value - right.base_value) <= tolerance


def sets_compatible(
    left: set[NumericValue], right: set[NumericValue], rule: NumericRule
) -> bool:
    combined = tuple(left | right)
    return bool(left and right) and all(
        compatible(value, other, rule)
        for index, value in enumerate(combined)
        for other in combined[index + 1 :]
    )
