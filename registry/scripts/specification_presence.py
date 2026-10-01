"""Reject empty/invalid normalization without guessing source values."""
from decimal import Decimal, InvalidOperation


def has_value(raw_value, normalized_text=None, normalized_number=None):
    if not isinstance(raw_value, str) or not raw_value.strip():
        return False
    # An explicitly blank normalization is not permission to fall back to raw
    # text. Both coverage and screening must report the unresolved value.
    if normalized_text is not None and (
        not isinstance(normalized_text, str) or not normalized_text.strip()
    ):
        return False
    if normalized_number is not None:
        if not isinstance(normalized_number, str) or not normalized_number.strip():
            return False
        try:
            if not Decimal(normalized_number).is_finite():
                return False
        except InvalidOperation:
            return False
    return True
