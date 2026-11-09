"""Fail-closed alignment of curated official-key claims with staged exam questions.

No PDF parsing, staged-exam mutation, independent solving, or answer promotion.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from english_exam.domain import ExtractionIssue, IssueSeverity, StagedDataset


@dataclass(frozen=True, slots=True)
class ExpectedKeyIdentity:
    """Independently inspected source identity supplied by the caller."""

    filename: str
    sha256: str
    booklet_code: str
    edition: str
    page_number: int
    table_group: int
    first_group_question_number: int = 1


@dataclass(frozen=True, slots=True)
class LinkedOfficialClaim:
    """An unverified official-key claim, not a final or AI-generated answer."""

    question_id: str
    question_number: int
    section: str
    passage_id: str | None
    official_answer_position: int
    key_filename: str
    key_page_number: int
    key_table_group: int
    key_table_row: int
    key_booklet_code: str
    key_edition: str
    review_state: str = "PENDING_HUMAN_REVIEW"


@dataclass(frozen=True, slots=True)
class ClaimAlignment:
    status: str
    exam_id: str
    claims: tuple[LinkedOfficialClaim, ...]
    errors: tuple[ExtractionIssue, ...]


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _int(value: Any) -> bool:
    return type(value) is int


def align_curated_official_claims(
    staged: StagedDataset,
    curated: Mapping[str, Any],
    *,
    expected_key: ExpectedKeyIdentity,
) -> ClaimAlignment:
    """Validate exact question/choice joins without promoting review-stage answers.

    Passing establishes structural alignment, not source accuracy or final-key
    verification. The key identity comes from independently inspected evidence.
    """
    errors: list[ExtractionIssue] = []
    exam = staged.exam

    def fail(code: str, message: str, entity_id: str | None = None) -> None:
        errors.append(
            ExtractionIssue(
                code=code,
                severity=IssueSeverity.ERROR,
                message=message,
                entity_id=entity_id,
            )
        )

    if staged.validation.status != "PASSED" or staged.validation.errors:
        fail("CLAIM_EXAM_NOT_VALIDATED", "exam staging must pass validation before alignment")
    if exam.state != "STAGED":
        fail("CLAIM_EXAM_STATE", "alignment requires unmodified staged exam data")

    if curated.get("schema_version") != "1.0" or (
        curated.get("artifact_type") != "SOURCE_LINKED_VISUAL_KEY_TRANSCRIPTION"
    ):
        fail("CLAIM_SCHEMA", "unsupported curated-key artifact schema or type")
    if curated.get("canonical_exam_id") != exam.id:
        fail("CLAIM_EXAM_ID", "curated exam ID does not match the staged exam")
    if curated.get("state") != "PENDING_HUMAN_REVIEW":
        fail("CLAIM_REVIEW_STATE", "only pending human-review claims can be aligned here")
    if curated.get("verified_final_answer") is not False or (
        curated.get("independent_blind_ai_solution") is not False
    ):
        fail("CLAIM_AUTHORITY", "curated claims must not assert final or blind AI review")

    exam_source = _mapping(curated.get("exam_source"))
    if exam_source.get("filename") != exam.source_document.source_filename or (
        exam_source.get("sha256") != exam.source_document.sha256
    ):
        fail("CLAIM_EXAM_SOURCE", "curated and staged exam source identities differ")
    if exam_source.get("english_pdf_pages") != list(exam.source_document.english_pdf_pages):
        fail("CLAIM_EXAM_PAGES", "curated English PDF-page coverage differs")

    key_source = _mapping(curated.get("key_source"))
    for field_name, expected in (
        ("filename", expected_key.filename),
        ("sha256", expected_key.sha256),
        ("booklet_code", expected_key.booklet_code),
        ("edition", expected_key.edition),
        ("page_number", expected_key.page_number),
    ):
        if key_source.get(field_name) != expected:
            fail("CLAIM_KEY_IDENTITY", f"unexpected key source {field_name}")
    if key_source.get("provenance_kind") != "VISUAL" or (
        key_source.get("native_pdf_text") is not False
    ):
        fail("CLAIM_KEY_PROVENANCE", "visual key cannot claim native PDF text")
    region_descriptor = key_source.get("source_region_descriptor")
    if not isinstance(region_descriptor, str) or not region_descriptor.strip():
        fail("CLAIM_KEY_REGION", "source key visual region must be named")

    questions: dict[int, tuple[Any, str, str | None]] = {}
    exam_numbers: list[int] = []
    for section in exam.sections:
        for question in section.questions:
            exam_numbers.append(question.number)
            questions[question.number] = (question, section.kind.value, None)
        for passage in section.passages:
            for question in passage.questions:
                exam_numbers.append(question.number)
                questions[question.number] = (question, section.kind.value, passage.id)
    if len(exam_numbers) != len(set(exam_numbers)):
        fail("CLAIM_EXAM_DUPLICATE", "staged exam has duplicate question numbers")
    for question, _, _ in questions.values():
        if any((question.answers.official, question.answers.ai, question.answers.final_verified)):
            fail("CLAIM_EXAM_HAS_ANSWERS", "raw staged questions must remain answer-free", question.id)

    raw_entries = curated.get("entries")
    if not isinstance(raw_entries, list):
        fail("CLAIM_ENTRIES", "curated entries must be an ordered list")
        raw_entries = []
    expected_fields = {
        "question_number",
        "section",
        "question_pdf_page",
        "passage_id",
        "official_answer_position",
        "key_table_group",
        "key_table_row",
    }
    entries = [_mapping(row) for row in raw_entries]
    numbers = [row.get("question_number") for row in entries]
    if any(not _int(number) or number <= 0 for number in numbers):
        fail("CLAIM_QUESTION_NUMBER", "question numbers must be positive integers")
    duplicates = [n for n, count in Counter(n for n in numbers if _int(n)).items() if count > 1]
    if duplicates:
        fail("CLAIM_DUPLICATE", f"duplicate curated question numbers: {sorted(duplicates)}")
    if len(entries) != len(questions) or set(n for n in numbers if _int(n)) != set(questions):
        fail("CLAIM_COVERAGE", "curated and staged question-number sets differ")

    linked: list[LinkedOfficialClaim] = []
    seen_regions: set[tuple[int, int]] = set()
    for row in entries:
        number = row.get("question_number")
        if set(row) != expected_fields:
            fail("CLAIM_ROW_SCHEMA", "curated row has unexpected or missing fields")
        if not _int(number) or number not in questions:
            fail("CLAIM_UNKNOWN_QUESTION", "curated question is absent from staged exam")
            continue
        question, section, passage_id = questions[number]
        entity_id = question.id
        if row.get("section") != section or row.get("passage_id") != passage_id:
            fail("CLAIM_SECTION_PASSAGE", "section or passage identity differs", entity_id)
        page = row.get("question_pdf_page")
        numbered_pages = {p.page_number for p in question.raw_number_marker.provenance}
        if not _int(page) or page not in numbered_pages:
            fail(
                "CLAIM_PRINTED_QUESTION_PAGE",
                "page must identify numbered question/choice row, not passage context",
                entity_id,
            )
        option = row.get("official_answer_position")
        valid_positions = {choice.position for choice in question.choices}
        if not _int(option) or option not in valid_positions:
            fail("CLAIM_INVALID_CHOICE", "official position is not a choice of the question", entity_id)
            continue
        group = row.get("key_table_group")
        table_row = row.get("key_table_row")
        if not _int(group) or group != expected_key.table_group or (
            not _int(table_row) or table_row <= 0
        ):
            fail("CLAIM_KEY_CELL", "invalid key table group or row", entity_id)
            continue
        expected_row = number - expected_key.first_group_question_number + 1
        if table_row != expected_row:
            fail("CLAIM_KEY_ROW_MAPPING", "key table row does not match question mapping", entity_id)
        region = (group, table_row)
        if region in seen_regions:
            fail("CLAIM_KEY_CELL_DUPLICATE", "same key cell assigned to two questions", entity_id)
        seen_regions.add(region)
        linked.append(
            LinkedOfficialClaim(
                question_id=question.id,
                question_number=number,
                section=section,
                passage_id=passage_id,
                official_answer_position=option,
                key_filename=expected_key.filename,
                key_page_number=expected_key.page_number,
                key_table_group=group,
                key_table_row=table_row,
                key_booklet_code=expected_key.booklet_code,
                key_edition=expected_key.edition,
            )
        )

    return ClaimAlignment(
        status="BLOCKED" if errors else "ALIGNED_PENDING_HUMAN_REVIEW",
        exam_id=exam.id,
        claims=() if errors else tuple(sorted(linked, key=lambda claim: claim.question_number)),
        errors=tuple(errors),
    )
