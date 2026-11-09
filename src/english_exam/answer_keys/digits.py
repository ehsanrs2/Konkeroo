"""Lossless normalization helpers for digit tokens."""

from __future__ import annotations

import re

_DIGIT_TRANSLATION = str.maketrans(
    "٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹",
    "01234567890123456789",
)
_ASCII_UNSIGNED_INTEGER = re.compile(r"[0-9]+", flags=re.ASCII)


def normalize_digits(value: str) -> str:
    """Map Arabic-Indic and Persian digits to Latin without changing other text."""

    return value.translate(_DIGIT_TRANSLATION)


def parse_unsigned_integer(value: str) -> int:
    """Parse a token containing digits only after script normalization."""

    normalized = normalize_digits(value)
    if not _ASCII_UNSIGNED_INTEGER.fullmatch(normalized):
        raise ValueError(f"not an unsigned digit token: {value!r}")
    return int(normalized)
