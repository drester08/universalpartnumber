"""UPN version-1 syntax and Luhn check-digit helpers."""

from __future__ import annotations

import re


UPN_PATTERN = re.compile(r"^UPN1-(\d{12})-(\d)$")


def luhn_check_digit(payload: str) -> str:
    if not payload.isdigit():
        raise ValueError("Luhn payload must contain only digits")
    total = 0
    parity = (len(payload) + 1) % 2
    for index, character in enumerate(payload):
        value = int(character)
        if index % 2 == parity:
            value *= 2
            if value > 9:
                value -= 9
        total += value
    return str((10 - total % 10) % 10)


def format_upn(sequence_number: int) -> str:
    if sequence_number < 1 or sequence_number > 999_999_999_999:
        raise ValueError("UPN sequence must be between 1 and 999999999999")
    body = f"{sequence_number:012d}"
    payload = f"1{body}"
    return f"UPN1-{body}-{luhn_check_digit(payload)}"


def valid_upn(value: str) -> bool:
    match = UPN_PATTERN.fullmatch(value)
    if match is None:
        return False
    body, check_digit = match.groups()
    if body == "000000000000":
        return False
    return check_digit == luhn_check_digit(f"1{body}")
