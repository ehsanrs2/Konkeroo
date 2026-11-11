"""Read-only, assistant-attributed, source-anchored 1396 Reading-1 preview.

This is NOT a human review, a rewritten raw stage or a verified answer set.
The reviewed JSON and its immutable Git blob identity are used as proposals.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from itertools import pairwise
from typing import Any

from english_exam.domain import ExtractedText, StagedDataset
from english_exam.review_docket import _git_blob_sha1

EXAM_SHA = "69bc3434ae61c05c85bc9fabffd0b2ce13e5b39bc71b1dfd71c16709c9638ba2"
READING_BLOB_SHA = "2f8f9b3c323b2b7173fcf7d8cf237e44804621f1"
EXPECTED_EDIT_IDS = tuple(f"r1396-{i:02d}" for i in range(1, 13))
Q19_STEM = "The tone of the passage could best be described as------."
PRINTED_ODDITY = "format of the fixture"


@dataclass(frozen=True, slots=True)
class ProvisionalField:
    field_id: str
    original_text: str
    candidate_text: str
    applied_edit_ids: tuple[str, ...]
    source_pdf_page: int


@dataclass(frozen=True, slots=True)
class Reading1Preview:
    status: str
    method: str
    fields: tuple[ProvisionalField, ...]
    applied_edit_ids: tuple[str, ...]
    q19_order_status: str
    printed_oddity: str
    errors: tuple[str, ...]


def _blocked(errors: list[str]) -> Reading1Preview:
    return Reading1Preview(
        "BLOCKED",
        "ASSISTANT_PROVISIONAL",
        (),
        (),
        "NEEDS_TECHNICAL_FOLLOWUP",
        PRINTED_ODDITY,
        tuple(errors),
    )


def _get_fields(staged: StagedDataset) -> dict[str, ExtractedText]:
    reading = next(section for section in staged.exam.sections if section.id == "reading")
    passage = next(p for p in reading.passages if p.id == "reading-1")
    questions = {q.number: q for q in passage.questions}
    if not all(number in questions for number in (16, 17, 18, 19)):
        raise ValueError("Reading-1 questions Q16–19 missing")
    choice1 = next(c for c in questions[17].choices if c.position == 1)
    if len(questions[19].choices) != 4:
        raise ValueError("Q19 must have four unmodified options")
    return {
        "reading-1:passage_body": passage.body,
        "q-16:question_stem": questions[16].stem,
        "q-17:choice_text:1": choice1.text,
        "q-18:number_marker": questions[18].raw_number_marker,
        "q-18:question_stem": questions[18].stem,
        "q-19:question_stem": questions[19].stem,
    }


def preview_1396_reading1(
    staged: StagedDataset,
    reading_review: Mapping[str, Any],
    ledger: Mapping[str, Any],
) -> Reading1Preview:
    """Prepare exactly twelve short source-aligned edits, but no human approvals.

    The original staged field and review ledger are never mutated. A failed
    source pin, overlapping edit, duplicated/missing anchor, wrong field/page,
    or already-transformed field blocks the entire preview.
    """
    errors: list[str] = []
    exam = staged.exam
    source = exam.source_document
    if (
        exam.id != "iran-ce-msc-1396"
        or exam.year != 1396
        or source.source_filename != "96.pdf"
        or source.sha256 != EXAM_SHA
        or 3 not in source.english_pdf_pages
        or staged.validation.status != "PASSED"
        or staged.validation.errors
    ):
        errors.append("source identity or validated staged exam mismatch")
    if (
        reading_review.get("artifact_type") != "SOURCE_LINKED_READING_TEXT_REVIEW"
        or reading_review.get("exam_id") != "iran-ce-msc-1396"
        or reading_review.get("booklet_code") != "C"
        or reading_review.get("review_status") != "PENDING_INDEPENDENT_REVIEW"
        or reading_review.get("independently_verified") is not False
    ):
        errors.append("unsupported original Reading proposal identity or review state")
    review_source = reading_review.get("exam_source")
    if not isinstance(review_source, Mapping) or (
        review_source.get("filename") != "96.pdf" or review_source.get("sha256") != EXAM_SHA
    ):
        errors.append("Reading proposed source SHA mismatch")
    pins = ledger.get("artifact_git_blob_sha1")
    if (
        ledger.get("publication_status") != "BLOCKED"
        or ledger.get("independently_verified") is not False
        or ledger.get("exam_source_sha256") != EXAM_SHA
        or not isinstance(pins, Mapping)
        or pins.get("reading") != READING_BLOB_SHA
        or _git_blob_sha1(reading_review) != READING_BLOB_SHA
    ):
        errors.append("stale Reading artifact pin or unblocked/verified ledger")

    proposals = reading_review.get("proposals")
    if not isinstance(proposals, list) or len(proposals) != 36 or any(
        not isinstance(p, Mapping) for p in proposals
    ):
        errors.append("original Reading proposals missing or changed")
        rows: list[Mapping[str, Any]] = []
    else:
        rows = [p for p in proposals if p.get("passage_id") == "reading-1"]
        if tuple(p.get("id") for p in rows) != EXPECTED_EDIT_IDS:
            errors.append("Reading-1 edit identities/count/order changed")
    anomalies = reading_review.get("unresolved_anomalies")
    if not isinstance(anomalies, list) or len(anomalies) != 5 or not any(
        a.get("id") == "r1396-order-q19"
        and a.get("status") == "NEEDS_SOURCE_ALIGNED_REVIEW"
        and a.get("proposed_replacement") is None
        for a in anomalies
        if isinstance(a, Mapping)
    ):
        errors.append("Q19 original ordering anomaly record has changed")

    try:
        fields = _get_fields(staged)
    except (AttributeError, KeyError, StopIteration, ValueError, TypeError) as exc:
        errors.append(f"Reading-1 stage field unavailable: {exc}")
        return _blocked(errors)
    for field_id, text in fields.items():
        if not isinstance(text, ExtractedText):
            errors.append(f"{field_id}: expected extracted source text")
            continue
        if text.normalized_text is not None or text.corrected_text is not None:
            errors.append(f"{field_id}: already normalized or corrected")
        if not text.provenance or any(
            p.source_filename != "96.pdf" or p.page_number != 3 for p in text.provenance
        ):
            errors.append(f"{field_id}: wrong original PDF-page provenance")

    groups: dict[str, list[Mapping[str, Any]]] = {}
    for p in rows:
        entity = p.get("target_entity_id")
        field = p.get("field")
        field_id = f"{entity}:{field}"
        if (
            field_id not in fields
            or p.get("source_pdf_page") != 3
            or p.get("review_status") != "PENDING_INDEPENDENT_REVIEW"
            or p.get("reason") not in (
                "TEXT_LAYER_GLYPH_ERROR",
                "PUNCTUATION_LAYER_ERROR",
                "WORD_BREAK_LAYER_ERROR",
            )
        ):
            errors.append(f"{p.get('id')}: unexpected field, page, or proposed reason")
        groups.setdefault(field_id, []).append(p)
    if errors:
        return _blocked(errors)

    fields_out: list[ProvisionalField] = []
    edits: list[str] = []
    for field_id, source_text in fields.items():
        raw = source_text.raw_text
        applied: list[str] = []
        spans: list[tuple[int, int, str, str]] = []
        for p in groups.get(field_id, []):
            before, after = p.get("expected_raw_fragment"), p.get("proposed_printed_fragment")
            if (
                not isinstance(before, str)
                or not before
                or not isinstance(after, str)
                or not after
                or raw.count(before) != 1
            ):
                errors.append(f"{p['id']}: missing/duplicated source-anchored edit")
                continue
            offset = raw.index(before)
            spans.append((offset, offset + len(before), after, str(p["id"])))
        spans.sort()
        if any(previous[1] > following[0] for previous, following in pairwise(spans)):
            errors.append(f"{field_id}: overlapping source edit spans")
            continue
        candidate = raw
        for start, end, after, task_id in reversed(spans):
            candidate = candidate[:start] + after + candidate[end:]
        applied = [p["id"] for p in groups.get(field_id, [])]
        edits.extend(applied)
        fields_out.append(ProvisionalField(field_id, raw, candidate, tuple(applied), 3))

    if errors or tuple(edits) != EXPECTED_EDIT_IDS:
        if not errors:
            errors.append("twelve provisional edits were not applied exactly once")
        return _blocked(errors)

    body = next(p for p in fields_out if p.field_id == "reading-1:passage_body")
    if (
        body.original_text.count(PRINTED_ODDITY) != 1
        or body.candidate_text.count(PRINTED_ODDITY) != 1
        or "format of the future" in body.candidate_text
    ):
        return _blocked(["printed fixture oddity was changed or was not unique"])

    # The plain PDF text extraction misorders this fragment, whereas the
    # baseline-aware importer already reconstructs the complete Q19 stem.
    # This is a technical observation, NOT a human RESOLVED decision.
    q19 = fields["q-19:question_stem"]
    if (
        q19.raw_text != Q19_STEM
        or len(q19.provenance) != 1
        or q19.provenance[0].raw_text != Q19_STEM
    ):
        return _blocked(["Q19 staged word order needs technical follow-up"])

    return Reading1Preview(
        "ASSISTANT_PROVISIONAL",
        "ASSISTANT_PROVISIONAL",
        tuple(fields_out),
        tuple(edits),
        "STAGED_ORDER_ALIGNED_NOT_INDEPENDENTLY_REVIEWED",
        PRINTED_ODDITY,
        (),
    )
