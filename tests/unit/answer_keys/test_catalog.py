import pytest

from english_exam.answer_keys.catalog import KEY_1395, get_answer_key_source
from english_exam.answer_keys.domain import (
    AnswerKeyEdition,
    AnswerKeyFamily,
    MediaType,
    OfficialKeyAvailability,
)


def test_1395_catalog_entry_uses_explicit_identity() -> None:
    source = get_answer_key_source("iran-ce-msc-1395")

    assert source is KEY_1395
    assert source.year == 1395
    assert source.source_filename == "95_Key.pdf"
    assert source.media_type is MediaType.PDF
    assert source.expected_sha256 == (
        "298efdeb70dc84b3bf92872f96bf2f15394f617e8c9e8d6cb9364e50789b3d9b"
    )
    assert source.expected_page_count == 1
    assert source.family is AnswerKeyFamily.NATIVE_REGULAR_PAIRED_GRID
    assert source.edition is AnswerKeyEdition.INITIAL
    assert source.availability is OfficialKeyAvailability.AVAILABLE


def test_catalog_does_not_discover_sources_from_filename() -> None:
    with pytest.raises(ValueError, match="unsupported answer-key source"):
        get_answer_key_source("95_Key.pdf")
