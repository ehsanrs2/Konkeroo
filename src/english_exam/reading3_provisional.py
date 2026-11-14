"""Read-only, source-pinned assistant provisional Reading Passage 3 preview.

Q26–30 belong to Passage 3 on printed exam PDF page 5; Q25 belongs to
Passage 2. Candidate corrections are not human review or released answers.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from itertools import pairwise
from typing import Any

from english_exam.domain import ExtractedText, StagedDataset
from english_exam.reading1_provisional import EXAM_SHA, READING_BLOB_SHA, ProvisionalField
from english_exam.reading2_provisional import TechnicalGlyphCandidate
from english_exam.review_docket import _git_blob_sha1

EXPECTED_EDIT_IDS = tuple(f"r1396-{number:02d}" for number in range(24, 37))
EXPECTED_QUESTIONS = tuple(range(26, 31))
EXPECTED_PAGE = 5
EXPECTED_FIELDS = (
    "reading-3:passage_body",
    "q-26:question_stem",
    "q-26:choice_text:4",
    "q-28:question_stem",
    "q-30:question_stem",
    "q-30:choice_text:2",
)
PRINTED_ODDITIES = ('"walk" thorough the rooms', "fight training")
TECHNICAL_ANCHORS = (
    (
        "r1396-order-p3-it",
        "reading-3:passage_body",
        "computer science. 11 is used routinely",
        "computer science. It is used routinely",
    ),
    (
        "r1396-order-p3-to",
        "reading-3:passage_body",
        "CAD techniques 10 design vehicles",
        "CAD techniques to design vehicles",
    ),
)


@dataclass(frozen=True, slots=True)
class Reading3Preview:
    status: str
    method: str
    fields: tuple[ProvisionalField, ...]
    applied_edit_ids: tuple[str, ...]
    technical_candidates: tuple[TechnicalGlyphCandidate, ...]
    printed_oddities: tuple[str, ...]
    errors: tuple[str, ...]


def _blocked(errors: list[str]) -> Reading3Preview:
    return Reading3Preview(
        "BLOCKED",
        "ASSISTANT_PROVISIONAL",
        (),
        (),
        (),
        PRINTED_ODDITIES,
        tuple(errors),
    )


def _get_fields(staged: StagedDataset) -> dict[str, ExtractedText]:
    section = next(s for s in staged.exam.sections if s.id == "reading")
    passage = next(p for p in section.passages if p.id == "reading-3")
    questions = {q.number: q for q in passage.questions}
    # Importer attaches Q25 to Passage 2, and Q26–30 to Passage 3.
    if (
        len(passage.questions) != len(EXPECTED_QUESTIONS)
        or tuple(sorted(questions)) != EXPECTED_QUESTIONS
    ):
        raise ValueError("Reading-3 must contain exactly Q26–30 (not Q25)")
    if tuple(c.position for c in questions[26].choices) != (1, 2, 3, 4):
        raise ValueError("Q26 choices must preserve all four original positions")
    if tuple(c.position for c in questions[30].choices) != (1, 2, 3, 4):
        raise ValueError("Q30 choices must preserve all four original positions")
    return {
        "reading-3:passage_body": passage.body,
        "q-26:question_stem": questions[26].stem,
        "q-26:choice_text:4": questions[26].choices[3].text,
        "q-28:question_stem": questions[28].stem,
        "q-30:question_stem": questions[30].stem,
        "q-30:choice_text:2": questions[30].choices[1].text,
    }


def preview_1396_reading3(
    staged: StagedDataset,
    reading_review: Mapping[str, Any],
    ledger: Mapping[str, Any],
) -> Reading3Preview:
    """Apply exactly 13 pinned proposals plus two separate glyph previews.

    Each exact raw anchor must occur once in a source-page-bound field. All
    spans (including technical candidates) must be disjoint, so partial
    application or quiet word displacement is never accepted.
    """
    errors: list[str] = []
    exam = staged.exam
    source = exam.source_document
    if (
        exam.id != "iran-ce-msc-1396"
        or exam.year != 1396
        or source.source_filename != "96.pdf"
        or source.sha256 != EXAM_SHA
        or EXPECTED_PAGE not in source.english_pdf_pages
        or staged.validation.status != "PASSED"
        or staged.validation.errors
    ):
        errors.append("original 1396 source identity or validated stage mismatch")

    if (
        reading_review.get("artifact_type") != "SOURCE_LINKED_READING_TEXT_REVIEW"
        or reading_review.get("exam_id") != "iran-ce-msc-1396"
        or reading_review.get("booklet_code") != "C"
        or reading_review.get("review_status") != "PENDING_INDEPENDENT_REVIEW"
        or reading_review.get("independently_verified") is not False
    ):
        errors.append("Reading source review identity or state differs")
    review_source = reading_review.get("exam_source")
    if not isinstance(review_source, Mapping) or (
        review_source.get("filename") != "96.pdf" or review_source.get("sha256") != EXAM_SHA
    ):
        errors.append("original PDF identity differs in curated Reading proposals")

    pins = ledger.get("artifact_git_blob_sha1")
    if (
        ledger.get("publication_status") != "BLOCKED"
        or ledger.get("independently_verified") is not False
        or ledger.get("exam_source_sha256") != EXAM_SHA
        or not isinstance(pins, Mapping)
        or pins.get("reading") != READING_BLOB_SHA
        or _git_blob_sha1(reading_review) != READING_BLOB_SHA
    ):
        errors.append("stale Reading revision pin or invalid release-blocked ledger")

    proposals = reading_review.get("proposals")
    if (
        not isinstance(proposals, list)
        or len(proposals) != 36
        or any(not isinstance(p, Mapping) for p in proposals)
    ):
        rows: list[Mapping[str, Any]] = []
        errors.append("original 36 Reading proposals missing or changed")
    else:
        rows = [p for p in proposals if p.get("passage_id") == "reading-3"]
        if tuple(p.get("id") for p in rows) != EXPECTED_EDIT_IDS:
            errors.append("Reading-3 edit IDs, count or order differ")

    anomalies = reading_review.get("unresolved_anomalies")
    if not isinstance(anomalies, list) or len(anomalies) != 5:
        errors.append("source-linked Reading anomaly set changed")
    else:
        for anomaly_id, field_id, _before, _after in TECHNICAL_ANCHORS:
            matches = [a for a in anomalies if isinstance(a, Mapping) and a.get("id") == anomaly_id]
            if len(matches) != 1 or (
                matches[0].get("passage_id") != "reading-3"
                or matches[0].get("target_entity_id") != "reading-3"
                or matches[0].get("source_pdf_page") != EXPECTED_PAGE
                or matches[0].get("kind") != "NONLOCAL_TEXT_ORDER"
                or matches[0].get("status") != "NEEDS_SOURCE_ALIGNED_REVIEW"
                or matches[0].get("proposed_replacement") is not None
                or field_id != "reading-3:passage_body"
            ):
                errors.append(f"{anomaly_id}: source anomaly metadata mismatch")

    printed = reading_review.get("printed_source_anomalies")
    if not isinstance(printed, list) or len(printed) != 4:
        errors.append("printed-source oddities set differs from pinned proposal")
    else:
        for fragment in ("walk thorough the rooms", "fight training"):
            if (
                sum(
                    isinstance(p, Mapping)
                    and p.get("passage_id") == "reading-3"
                    and p.get("source_pdf_page") == EXPECTED_PAGE
                    and p.get("printed_fragment") == fragment
                    for p in printed
                )
                != 1
            ):
                errors.append(f"printed oddity {fragment!r} missing or duplicated")

    try:
        fields = _get_fields(staged)
    except (AttributeError, KeyError, StopIteration, TypeError, ValueError) as exc:
        errors.append(f"Reading-3 stage field or question membership mismatch: {exc}")
        return _blocked(errors)

    if tuple(fields) != EXPECTED_FIELDS:
        errors.append("unexpected field mapping in Reading-3")
    for field_id, source_field in fields.items():
        if not isinstance(source_field, ExtractedText):
            errors.append(f"{field_id}: missing extracted field")
            continue
        if source_field.corrected_text is not None or source_field.normalized_text is not None:
            errors.append(f"{field_id}: stage field was already transformed")
        if not source_field.provenance or any(
            p.source_filename != "96.pdf" or p.page_number != EXPECTED_PAGE
            for p in source_field.provenance
        ):
            errors.append(f"{field_id}: source provenance is not original PDF page 5")

    groups: dict[str, list[Mapping[str, Any]]] = {}
    for p in rows:
        field_id = f"{p.get('target_entity_id')}:{p.get('field')}"
        if (
            field_id not in EXPECTED_FIELDS
            or p.get("source_pdf_page") != EXPECTED_PAGE
            or p.get("review_status") != "PENDING_INDEPENDENT_REVIEW"
            or p.get("reason") not in ("TEXT_LAYER_GLYPH_ERROR", "PUNCTUATION_LAYER_ERROR")
        ):
            errors.append(f"{p.get('id')}: unsupported field, page, status or reason")
        groups.setdefault(field_id, []).append(p)
    if errors:
        return _blocked(errors)

    output: list[ProvisionalField] = []
    applied: list[str] = []
    for field_id, source_field in fields.items():
        raw = source_field.raw_text
        spans: list[tuple[int, int, str, str]] = []
        for proposal in groups.get(field_id, ()):
            before = proposal.get("expected_raw_fragment")
            after = proposal.get("proposed_printed_fragment")
            if (
                not isinstance(before, str)
                or not before
                or not isinstance(after, str)
                or not after
                or raw.count(before) != 1
            ):
                errors.append(f"{proposal['id']}: missing/duplicated editorial anchor")
                continue
            start = raw.index(before)
            spans.append((start, start + len(before), after, str(proposal["id"])))

        for anomaly_id, target, before, after in TECHNICAL_ANCHORS:
            if field_id != target:
                continue
            if raw.count(before) != 1:
                errors.append(f"{anomaly_id}: missing/duplicated technical glyph anchor")
                continue
            start = raw.index(before)
            spans.append((start, start + len(before), after, anomaly_id))

        spans.sort()
        if any(left[1] > right[0] for left, right in pairwise(spans)):
            errors.append(f"{field_id}: overlapping source edits or glyph candidates")
            continue

        candidate = raw
        for start, end, after, _task_id in reversed(spans):
            candidate = candidate[:start] + after + candidate[end:]

        ids_for_field = tuple(str(p["id"]) for p in groups.get(field_id, ()))
        applied.extend(ids_for_field)
        output.append(
            ProvisionalField(
                field_id=field_id,
                original_text=raw,
                candidate_text=candidate,
                applied_edit_ids=ids_for_field,
                source_pdf_page=EXPECTED_PAGE,
            )
        )

    if errors or tuple(applied) != EXPECTED_EDIT_IDS:
        if not errors:
            errors.append("not all thirteen source-linked Reading-3 edits were applied")
        return _blocked(errors)

    by_id = {field.field_id: field for field in output}
    body = by_id["reading-3:passage_body"]
    choice2 = by_id["q-30:choice_text:2"]
    if (
        body.original_text.count(PRINTED_ODDITIES[0]) != 1
        or body.candidate_text.count(PRINTED_ODDITIES[0]) != 1
        or '"walk" through the rooms' in body.candidate_text
        or choice2.original_text.count(PRINTED_ODDITIES[1]) != 1
        or choice2.candidate_text != choice2.original_text
        or choice2.candidate_text.count(PRINTED_ODDITIES[1]) != 1
        or "flight training" in choice2.candidate_text
    ):
        return _blocked(["printed 'thorough' or 'fight training' oddity was changed"])

    candidates = tuple(
        TechnicalGlyphCandidate(
            anomaly_id=anomaly_id,
            field_id=field_id,
            expected_stage_anchor=before,
            suggested_printed_anchor=after,
            source_pdf_page=EXPECTED_PAGE,
        )
        for anomaly_id, field_id, before, after in TECHNICAL_ANCHORS
    )
    return Reading3Preview(
        status="ASSISTANT_PROVISIONAL",
        method="ASSISTANT_PROVISIONAL",
        fields=tuple(output),
        applied_edit_ids=tuple(applied),
        technical_candidates=candidates,
        printed_oddities=PRINTED_ODDITIES,
        errors=(),
    )
