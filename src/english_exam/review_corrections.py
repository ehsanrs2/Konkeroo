"""Fail-closed previews of visually reviewed exam text correction proposals.

This module never writes to or mutates raw staged exam data. The proposals
are editorial data, not OCR output or automatically verified corrections.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping
from dataclasses import dataclass
from itertools import pairwise
from typing import Any

from english_exam.domain import ExtractedText, StagedDataset
from english_exam.validation import all_questions


@dataclass(frozen=True, slots=True)
class FieldCorrectionPreview:
    question_id: str
    field: str
    proposal_ids: tuple[str, ...]
    source_raw_text: str
    suggested_corrected_text: str


@dataclass(frozen=True, slots=True)
class CorrectionPreviewReport:
    status: str
    previews: tuple[FieldCorrectionPreview, ...]
    errors: tuple[str, ...]


def _field_text(question: Any, field: str) -> ExtractedText | None:
    if field == "stem":
        return question.stem
    if field == "number_marker":
        return question.raw_number_marker
    if field.startswith("choice_marker:"):
        marker = field.removeprefix("choice_marker:")
        if not marker.isascii() or not marker.isdecimal():
            return None
        position = int(marker)
        return next(
            (choice.raw_marker for choice in question.choices if choice.position == position),
            None,
        )
    return None


def preview_editorial_corrections(
    staged: StagedDataset, review: Mapping[str, Any]
) -> CorrectionPreviewReport:
    """Check exact source substrings, then preview edits without mutating input.

    Every requested edit must pass; any failure returns no previews.
    A successful preview remains AWAITING_INDEPENDENT_REVIEW.
    """
    errors: list[str] = []

    def fail(message: str) -> None:
        errors.append(message)

    source = staged.exam.source_document
    if staged.validation.status != "PASSED" or staged.validation.errors:
        fail("unvalidated staged exam")
    if review.get("schema_version") != "1.0" or (
        review.get("artifact_type") != "EDITORIAL_CORRECTION_PROPOSALS"
    ):
        fail("unsupported correction proposal schema")
    if review.get("exam_id") != staged.exam.id:
        fail("exam identity mismatch")
    src = review.get("exam_source")
    if not isinstance(src, dict) or (
        src.get("filename") != source.source_filename
        or src.get("sha256") != source.sha256
    ):
        fail("source filename or SHA-256 mismatch")
    if review.get("review_state") != "AWAITING_INDEPENDENT_REVIEW" or (
        review.get("review_method") != "ASSISTANT_DIRECT_VISUAL_COMPARISON"
    ):
        fail("review state or method mismatch")

    questions = all_questions(staged.exam)
    by_id = {question.id: question for question in questions}
    if len(questions) != len(by_id):
        fail("duplicate staged question IDs")

    scope = review.get("scope")
    if not isinstance(scope, dict):
        fail("missing correction review scope")
        scope = {}
    allowed = scope.get("question_numbers")
    if not isinstance(allowed, list) or any(
        type(number) is not int or number <= 0 for number in allowed
    ):
        fail("invalid scope question numbers")
        allowed = []
    if len(set(allowed)) != len(allowed):
        fail("duplicate scope question numbers")
    scope_pages = scope.get("source_pdf_pages")
    if not isinstance(scope_pages, list) or any(
        type(page) is not int or page not in source.english_pdf_pages
        for page in scope_pages
    ):
        fail("invalid scope pages")
        scope_pages = []
    if not scope_pages:
        fail("missing scope pages")

    proposals = review.get("proposals")
    if not isinstance(proposals, list) or not proposals:
        fail("missing correction proposals")
        proposals = []

    required = {
        "id",
        "question_id",
        "field",
        "expected_raw_fragment",
        "proposed_replacement",
        "source_pdf_page",
        "reason",
    }
    ids = [row.get("id") for row in proposals if isinstance(row, dict)]
    if any(not isinstance(item, str) or not item for item in ids):
        fail("empty or invalid proposal ID")
    if len(ids) != len(proposals) or any(count > 1 for count in Counter(ids).values()):
        fail("duplicate or malformed proposal IDs")

    edits: dict[tuple[str, str], list[tuple[int, int, str, str]]] = defaultdict(list)
    field_values: dict[tuple[str, str], ExtractedText] = {}
    for index, row in enumerate(proposals):
        if not isinstance(row, dict) or set(row) != required:
            fail(f"proposal {index} has missing or unexpected fields")
            continue
        proposal_id = row["id"]
        qid = row["question_id"]
        field = row["field"]
        before = row["expected_raw_fragment"]
        after = row["proposed_replacement"]
        if not all(
            isinstance(s, str) and s.strip()
            for s in (proposal_id, qid, field, before, after, row["reason"])
        ):
            fail(f"{proposal_id!r}: malformed proposal text")
            continue
        if before == after:
            fail(f"{proposal_id}: no-op replacement")
            continue
        question = by_id.get(qid)
        if question is None or question.number not in allowed:
            fail(f"{proposal_id}: unknown or out-of-scope question")
            continue
        value = _field_text(question, field)
        if value is None:
            fail(f"{proposal_id}: unsupported or absent target field")
            continue
        page = row["source_pdf_page"]
        if (
            type(page) is not int
            or page not in scope_pages
            or not any(item.page_number == page for item in value.provenance)
        ):
            fail(f"{proposal_id}: printed page / field provenance mismatch")
            continue
        if value.corrected_text is not None or value.normalized_text is not None:
            fail(f"{proposal_id}: field already transformed; raw review required")
            continue
        if value.raw_text.count(before) != 1:
            fail(f"{proposal_id}: expected raw substring is absent or ambiguous")
            continue
        start = value.raw_text.index(before)
        key = (qid, field)
        field_values[key] = value
        edits[key].append((start, start + len(before), after, proposal_id))

    previews: list[FieldCorrectionPreview] = []
    for key, changes in sorted(edits.items()):
        ordered = sorted(changes)
        for previous, following in pairwise(ordered):
            if previous[1] > following[0]:
                fail(f"{key}: overlapping editorial corrections")
        original = field_values[key].raw_text
        suggested = original
        for start, stop, replacement, _ in reversed(ordered):
            suggested = suggested[:start] + replacement + suggested[stop:]
        previews.append(
            FieldCorrectionPreview(
                question_id=key[0],
                field=key[1],
                proposal_ids=tuple(edit[3] for edit in ordered),
                source_raw_text=original,
                suggested_corrected_text=suggested,
            )
        )

    if errors:
        return CorrectionPreviewReport("BLOCKED", (), tuple(errors))
    return CorrectionPreviewReport(
        "AWAITING_INDEPENDENT_REVIEW", tuple(previews), ()
    )
