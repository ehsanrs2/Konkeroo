import pytest

from english_exam.answer_keys.digits import normalize_digits, parse_unsigned_integer


def test_normalizes_supported_digit_systems_without_changing_other_text() -> None:
    assert normalize_digits("Latin 120 / Persian ۴۵۶ / Arabic ٧٨٩") == (
        "Latin 120 / Persian 456 / Arabic 789"
    )


@pytest.mark.parametrize("value", ["123", "۱۲۳", "١٢٣", "1۲٣"])
def test_parses_normalized_unsigned_integer(value: str) -> None:
    assert parse_unsigned_integer(value) == 123


@pytest.mark.parametrize("value", ["", " 1", "1 ", "-1", "+1", "1.0", "one", "۱،۲"])
def test_rejects_non_digit_tokens(value: str) -> None:
    with pytest.raises(ValueError, match="not an unsigned digit token"):
        parse_unsigned_integer(value)
