"""Explicit catalog of immutable official answer-key sources."""

from __future__ import annotations

from dataclasses import dataclass

from english_exam.answer_keys.domain import (
    AnswerKeyEdition,
    AnswerKeyFamily,
    MediaType,
    OfficialKeyAvailability,
)


@dataclass(frozen=True, slots=True)
class AnswerKeySourceSpec:
    canonical_exam_id: str
    year: int
    source_filename: str | None
    media_type: MediaType | None
    expected_sha256: str | None
    expected_page_count: int | None
    family: AnswerKeyFamily | None
    edition: AnswerKeyEdition
    availability: OfficialKeyAvailability


KEY_1395 = AnswerKeySourceSpec(
    canonical_exam_id="iran-ce-msc-1395",
    year=1395,
    source_filename="95_Key.pdf",
    media_type=MediaType.PDF,
    expected_sha256="298efdeb70dc84b3bf92872f96bf2f15394f617e8c9e8d6cb9364e50789b3d9b",
    expected_page_count=1,
    family=AnswerKeyFamily.NATIVE_REGULAR_PAIRED_GRID,
    edition=AnswerKeyEdition.INITIAL,
    availability=OfficialKeyAvailability.AVAILABLE,
)

ANSWER_KEY_SOURCES = {KEY_1395.canonical_exam_id: KEY_1395}


def get_answer_key_source(canonical_exam_id: str) -> AnswerKeySourceSpec:
    """Look up a source by canonical identity, never by filename convention."""

    try:
        return ANSWER_KEY_SOURCES[canonical_exam_id]
    except KeyError as error:
        raise ValueError(f"unsupported answer-key source: {canonical_exam_id}") from error
