"""Governed cross-unit comparison for identity-defining numeric properties."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from decimal import Decimal, DecimalException


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


def to_base_value(row: sqlite3.Row | dict[str, object]) -> NumericValue | None:
    if not isinstance(row['quantity_kind'], str) or not row['quantity_kind'].strip():
        return None
    values = [row[key] for key in ('normalized_number', 'conversion_factor', 'conversion_offset')]
    if any(not isinstance(value, str) or not value.strip() for value in values):
        return None
    try:
        number, factor, offset = map(Decimal, values)
        if not all(value.is_finite() for value in (number, factor, offset)) or factor <= 0:
            return None
        base = number * factor + offset
        if not base.is_finite():
            return None
    except DecimalException:
        return None
    return NumericValue(quantity_kind=row['quantity_kind'], base_value=base)


def conversion_ready(number, quantity_kind, factor, offset):
    return to_base_value(dict(normalized_number=number, quantity_kind=quantity_kind,
                              conversion_factor=factor, conversion_offset=offset)) is not None


def compatible(left: NumericValue, right: NumericValue, rule: NumericRule) -> bool:
    if not all(isinstance(value, Decimal) and value.is_finite() for value in
               (left.base_value, right.base_value, rule.absolute_tolerance, rule.relative_tolerance)):
        return False
    if rule.absolute_tolerance < 0 or not Decimal('0') <= rule.relative_tolerance <= Decimal('0.02'):
        return False
    if left.quantity_kind != rule.quantity_kind or right.quantity_kind != rule.quantity_kind:
        return False
    try:
        scale = max(abs(left.base_value), abs(right.base_value))
        tolerance = max(rule.absolute_tolerance, scale * rule.relative_tolerance)
        return abs(left.base_value - right.base_value) <= tolerance
    except DecimalException:
        return False


def sets_compatible(
    left: set[NumericValue], right: set[NumericValue], rule: NumericRule
) -> bool:
    combined = tuple(left | right)
    return bool(left and right) and all(compatible(value, value, rule) for value in combined) and all(
        compatible(value, other, rule)
        for index, value in enumerate(combined)
        for other in combined[index + 1 :]
    )
