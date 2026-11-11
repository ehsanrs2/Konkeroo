"""Read-only 1396 Reading Passage 2 assistant-source provisional corrections.

Applies 11 pinned editorial proposals plus two *separate*, tightly anchored
technical glyph candidates. Nothing here is a human reviewer decision or a
verified learner dataset.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from itertools import pairwise
from typing import Any

from english_exam.domain import ExtractedText, StagedDataset
from english_exam.reading1_provisional import (
    EXAM_SHA,
    READING_BLOB_SHA,
    ProvisionalField,
)
from english_exam.review_docket import _git_blob_sha1

EXPECTED_EDIT_IDS = tuple(f"r1396-{index:02d}" for index in range(13, 24))
PRINTED_ODDITY = 'The work "self-contained"'
EXPECTED_PAGES = {
    "reading-2:passage_heading": 4,
    "reading-2:passage_body": 4,
    "q-21:choice_text:4": 4,
    "q-22:question_stem": 4,
    "q-23:question_stem": 4,
    "q-25:question_stem": 5,
}

# Exact anchored, printed-source/geometry-based technical suggestions, not
# replacements authorized by the historical independent-human review docket.
_TECHNICAL_ANCHORS = (
    (
        "r1396-order-p2-stray",
        "reading-2:passage_body",
        "concept of 11 worm",
        "concept of a worm",
    ),
    (
        "r1396-order-q22",
        "q-22:question_stem",
        "beginning or lhe virus era",
        "beginning of the virus era",
    ),
)


@dataclass(frozen=True, slots=True)
class TechnicalGlyphCandidate:
    anomaly_id: str
    field_id: str
    expected_stage_anchor: str
    suggested_printed_anchor: str
    source_pdf_page: int
    status: str = "GEOMETRY_ALIGNED_ASSISTANT_PROVISIONAL"


@dataclass(frozen=True, slots=True)
class Reading2Preview:
    status: str
    method: str
    fields: tuple[ProvisionalField, ...]
    applied_edit_ids: tuple[str, ...]
    technical_candidates: tuple[TechnicalGlyphCandidate, ...]
    printed_oddity: str
    errors: tuple[str, ...]


def _blocked(errors: list[str]) -> Reading2Preview:
    return Reading2Preview(
        "BLOCKED",
        "ASSISTANT_PROVISIONAL",
        (),
        (),
        (),
        PRINTED_ODDITY,
        tuple(errors),
    )


def _get_fields(staged: StagedDataset) -> dict[str, ExtractedText]:
    section = next(s for s in staged.exam.sections if s.id == "reading")
    passage = next(p for p in section.passages if p.id == "reading-2")
    questions = {q.number: q for q in passage.questions}
    if any(number not in questions for number in range(20, 26)):
        raise ValueError("Reading-2 questions Q20–25 missing")
    choice4 = next(c for c in questions[21].choices if c.position == 4)
    if len(questions[23].choices) != 4:
        raise ValueError("Q23 must preserve its original four choices")
    return {
        "reading-2:passage_heading": passage.heading,
        "reading-2:passage_body": passage.body,
        "q-21:choice_text:4": choice4.text,
        "q-22:question_stem": questions[22].stem,
        "q-23:question_stem": questions[23].stem,
        "q-25:question_stem": questions[25].stem,
    }


def preview_1396_reading2(
    staged: StagedDataset,
    reading_review: Mapping[str, Any],
    ledger: Mapping[str, Any],
) -> Reading2Preview:
    """Fail closed for any stale anchor, source mismatch, or ambiguous field.

    The two technical suggestions are derived from rendered PDF and same-line
    glyph geometry. They are in-memory only, remain *provisional*, and do not
    set independent-review anomaly decisions to RESOLVED.
    """
    errors: list[str] = []
    exam = staged.exam
    source = exam.source_document
    if (
        exam.id != "iran-ce-msc-1396"
        or exam.year != 1396
        or source.source_filename != "96.pdf"
        or source.sha256 != EXAM_SHA
        or not {4, 5}.issubset(source.english_pdf_pages)
        or staged.validation.status != "PASSED"
        or staged.validation.errors
    ):
        errors.append("original 1396 source identity or stage validation mismatch")

    if (
        reading_review.get("artifact_type") != "SOURCE_LINKED_READING_TEXT_REVIEW"
        or reading_review.get("exam_id") != "iran-ce-msc-1396"
        or reading_review.get("booklet_code") != "C"
        or reading_review.get("review_status") != "PENDING_INDEPENDENT_REVIEW"
        or reading_review.get("independently_verified") is not False
    ):
        errors.append("Reading proposal identity, booklet or review state changed")
    source_info = reading_review.get("exam_source")
    if not isinstance(source_info, Mapping) or (
        source_info.get("filename") != "96.pdf" or source_info.get("sha256") != EXAM_SHA
    ):
        errors.append("Reading source PDF provenance differs")

    pins = ledger.get("artifact_git_blob_sha1")
    if (
        ledger.get("publication_status") != "BLOCKED"
        or ledger.get("independently_verified") is not False
        or ledger.get("exam_source_sha256") != EXAM_SHA
        or not isinstance(pins, Mapping)
        or pins.get("reading") != READING_BLOB_SHA
        or _git_blob_sha1(reading_review) != READING_BLOB_SHA
    ):
        errors.append("Reading review revision pin or release-blocked ledger mismatch")

    proposals = reading_review.get("proposals")
    if (
        not isinstance(proposals, list)
        or len(proposals) != 36
        or any(not isinstance(item, Mapping) for item in proposals)
    ):
        rows: list[Mapping[str, Any]] = []
        errors.append("original Reading proposal list is missing or altered")
    else:
        rows = [item for item in proposals if item.get("passage_id") == "reading-2"]
        if tuple(item.get("id") for item in rows) != EXPECTED_EDIT_IDS:
            errors.append("Reading-2 source-linked edit IDs or order changed")

    anomalies = reading_review.get("unresolved_anomalies")
    if not isinstance(anomalies, list) or len(anomalies) != 5:
        errors.append("Reading anomaly source list changed")
    else:
        for anomaly_id, field_id, before, after in _TECHNICAL_ANCHORS:
            expected_page = EXPECTED_PAGES[field_id]
            items = [
                anomaly
                for anomaly in anomalies
                if isinstance(anomaly, Mapping) and anomaly.get("id") == anomaly_id
            ]
            if len(items) != 1 or (
                items[0].get("source_pdf_page") != expected_page
                or items[0].get("status") != "NEEDS_SOURCE_ALIGNED_REVIEW"
                or items[0].get("proposed_replacement") is not None
                or items[0].get("passage_id") != "reading-2"
            ):
                errors.append(f"{anomaly_id}: source anomaly record mismatch")

    oddities = reading_review.get("printed_source_anomalies")
    if not isinstance(oddities, list) or not any(
        isinstance(row, Mapping)
        and row.get("passage_id") == "reading-2"
        and row.get("source_pdf_page") == 4
        and row.get("printed_fragment") == PRINTED_ODDITY
        for row in oddities
    ):
        errors.append("Q23 printed oddity source record missing")

    try:
        fields = _get_fields(staged)
    except (AttributeError, KeyError, StopIteration, TypeError, ValueError) as exc:
        errors.append(f"Reading-2 staged fields missing: {exc}")
        return _blocked(errors)
    for field_id, expected_page in EXPECTED_PAGES.items():
        field = fields.get(field_id)
        if not isinstance(field, ExtractedText):
            errors.append(f"{field_id}: source field missing")
            continue
        if field.normalized_text is not None or field.corrected_text is not None:
            errors.append(f"{field_id}: source already transformed")
        if not field.provenance or any(
            p.source_filename != "96.pdf" or p.page_number != expected_page
            for p in field.provenance
        ):
            errors.append(f"{field_id}: incorrect PDF page or source provenance")

    groups: dict[str, list[Mapping[str, Any]]] = {}
    for row in rows:
        field_id = f"{row.get('target_entity_id')}:{row.get('field')}"
        if (
            field_id not in EXPECTED_PAGES
            or row.get("source_pdf_page") != EXPECTED_PAGES.get(field_id)
            or row.get("review_status") != "PENDING_INDEPENDENT_REVIEW"
            or row.get("reason") not in ("TEXT_LAYER_GLYPH_ERROR", "PUNCTUATION_LAYER_ERROR")
        ):
            errors.append(f"{row.get('id')}: unsupported field/page/reason")
        groups.setdefault(field_id, []).append(row)

    if errors:
        return _blocked(errors)

    output: list[ProvisionalField] = []
    applied: list[str] = []
    for field_id, source_field in fields.items():
        raw = source_field.raw_text
        spans: list[tuple[int, int, str, str]] = []
        for proposal in groups.get(field_id, []):
            before = proposal.get("expected_raw_fragment")
            after = proposal.get("proposed_printed_fragment")
            if (
                not isinstance(before, str)
                or not before
                or not isinstance(after, str)
                or not after
                or raw.count(before) != 1
            ):
                errors.append(f"{proposal['id']}: absent or repeated raw edit anchor")
                continue
            start = raw.index(before)
            spans.append((start, start + len(before), after, str(proposal["id"])))
        spans.sort()
        if any(left[1] > right[0] for left, right in pairwise(spans)):
            errors.append(f"{field_id}: overlapping short editorial edits")
            continue

        candidate = raw
        for start, end, replacement, _task_id in reversed(spans):
            candidate = candidate[:start] + replacement + candidate[end:]

        for anomaly_id, target_field, before, after in _TECHNICAL_ANCHORS:
            if field_id != target_field:
                continue
            if raw.count(before) != 1 or candidate.count(before) != 1:
                errors.append(f"{anomaly_id}: missing/duplicated technical glyph anchor")
                continue
            candidate = candidate.replace(before, after, 1)

        edits_for_field = tuple(str(item["id"]) for item in groups.get(field_id, ()))
        applied.extend(edits_for_field)
        output.append(
            ProvisionalField(
                field_id=field_id,
                original_text=raw,
                candidate_text=candidate,
                applied_edit_ids=edits_for_field,
                source_pdf_page=EXPECTED_PAGES[field_id],
            )
        )

    if errors or tuple(applied) != EXPECTED_EDIT_IDS:
        if not errors:
            errors.append("not all eleven short edit IDs were applied")
        return _blocked(errors)

    q23 = next(field for field in output if field.field_id == "q-23:question_stem")
    if (
        q23.original_text.count(PRINTED_ODDITY) != 1
        or q23.candidate_text.count(PRINTED_ODDITY) != 1
        or 'The word "self-contained"' in q23.candidate_text
    ):
        return _blocked(["Q23 printed 'work' must remain intact"])

    technical = tuple(
        TechnicalGlyphCandidate(
            anomaly_id=anomaly_id,
            field_id=field_id,
            expected_stage_anchor=before,
            suggested_printed_anchor=after,
            source_pdf_page=EXPECTED_PAGES[field_id],
        )
        for anomaly_id, field_id, before, after in _TECHNICAL_ANCHORS
    )
    return Reading2Preview(
        status="ASSISTANT_PROVISIONAL",
        method="ASSISTANT_PROVISIONAL",
        fields=tuple(output),
        applied_edit_ids=tuple(applied),
        technical_candidates=technical,
        printed_oddity=PRINTED_ODDITY,
        errors=(),
    )
