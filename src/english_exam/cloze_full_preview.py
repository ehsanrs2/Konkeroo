"""Read-only unified Cloze passage preview for 1396 owner-reviewed edits.

Joins four independently attested *passage-body* edits to the still-pending
source-aligned '10' -> 'to' technical candidate. Does not promote answers,
change raw text, or record the anomaly as resolved.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from english_exam.cloze_order_review import (
    ANOMALY_ID,
    EXAM_SHA,
    preview_1396_cloze_to_remember,
)
from english_exam.domain import StagedDataset
from english_exam.review_docket import _git_blob_sha1

CLOZE_BLOB_SHA1 = "5530e4484dbc274ee23fa37f5b24d34c25f8301c"
PASSAGE_EDIT_IDS = frozenset(
    {
        "cloze-human",
        "cloze-on",
        "cloze-to-study",
        "cloze-14-marker",
    }
)


@dataclass(frozen=True, slots=True)
class FullClozePreview:
    status: str
    proposed_full_text: str | None
    accepted_passage_edit_ids: tuple[str, ...]
    technical_candidate_anomaly_id: str
    unresolved_anomaly: bool
    errors: tuple[str, ...]


def preview_1396_reviewed_cloze_passage(
    staged: StagedDataset,
    curated_review: Mapping[str, Any],
    ledger: Mapping[str, Any],
) -> FullClozePreview:
    """Produce one full-field preview without editing stage/review/ledger inputs.

    A source-linked, human-attested short edit is not equivalent to independent
    inspection of the *whole* corrected Cloze passage. The to/10 candidate is
    also deliberately NOT an accepted ledger decision.
    """
    errors: list[str] = []
    candidate = preview_1396_cloze_to_remember(staged)
    if candidate.status != "PROPOSED_PENDING_TECHNICAL_REVIEW":
        errors.extend(candidate.errors or ("source-specific token preview unavailable",))
    if (
        curated_review.get("artifact_type") != "SOURCE_LINKED_CLOZE_TEXT_REVIEW"
        or curated_review.get("exam_id") != "iran-ce-msc-1396"
        or curated_review.get("review_status") != "PENDING_INDEPENDENT_REVIEW"
        or curated_review.get("independently_verified") is not False
    ):
        errors.append("unexpected Cloze review artifact or state")
    source = curated_review.get("source")
    if not isinstance(source, Mapping) or (
        source.get("filename") != "96.pdf" or source.get("sha256") != EXAM_SHA
    ):
        errors.append("curated Cloze original source identity mismatch")

    if (
        ledger.get("publication_status") != "BLOCKED"
        or ledger.get("independently_verified") is not False
        or ledger.get("exam_source_sha256") != EXAM_SHA
    ):
        errors.append("decision ledger is not source-bound and release-blocked")
    pins = ledger.get("artifact_git_blob_sha1")
    if not isinstance(pins, Mapping) or pins.get("cloze") != CLOZE_BLOB_SHA1:
        errors.append("decision ledger Cloze revision pin mismatch")
    if _git_blob_sha1(curated_review) != CLOZE_BLOB_SHA1:
        errors.append("curated review data no longer matches reviewed revision")

    all_rows = curated_review.get("proposals")
    rows: list[Mapping[str, Any]] = []
    if not isinstance(all_rows, list) or len(all_rows) != 7 or any(
        not isinstance(row, Mapping) for row in all_rows
    ):
        errors.append("expected seven source-linked Cloze edit proposals")
    else:
        rows = [
            row
            for row in all_rows
            if row.get("entity_id") == "cloze-1" and row.get("field") == "passage_body"
        ]
        if len(rows) != 4 or {row.get("id") for row in rows} != PASSAGE_EDIT_IDS:
            errors.append("unexpected Cloze passage edit identities")

    decisions = ledger.get("decisions")
    if not isinstance(decisions, list) or any(not isinstance(d, Mapping) for d in decisions):
        errors.append("decision ledger has no valid decisions list")
        decisions = []
    all_ids = [d.get("task_id") for d in decisions]
    if any(count > 1 for count in Counter(all_ids).values()):
        errors.append("duplicate ledger task decisions")
    decisions_by_id = {d.get("task_id"): d for d in decisions}
    if f"anomaly:cloze:{ANOMALY_ID}" in decisions_by_id:
        errors.append("displaced-token anomaly is not allowed to be pre-resolved")

    for row in rows:
        task_id = f"edit:cloze:{row['id']}"
        decision = decisions_by_id.get(task_id)
        if not isinstance(decision, Mapping) or (
            decision.get("disposition") != "ACCEPTED"
            or decision.get("reviewer_role") != "INDEPENDENT_HUMAN"
            or decision.get("reviewed_artifact_blob_sha1") != CLOZE_BLOB_SHA1
            or decision.get("evidence_source_sha256") != EXAM_SHA
            or decision.get("evidence_pdf_page") != 2
        ):
            errors.append(f"{task_id}: missing valid attested source-linked decision")
        if (
            row.get("pdf_page") != 2
            or row.get("proposal_status") != "PENDING_INDEPENDENT_REVIEW"
        ):
            errors.append(f"{task_id}: unsupported printed page or proposal status")

    if errors or candidate.proposed_full_text is None:
        return FullClozePreview("BLOCKED", None, (), ANOMALY_ID, True, tuple(errors))

    result = candidate.proposed_full_text
    for row in rows:
        before = row["expected_raw_fragment"]
        after = row["proposed_replacement"]
        if not isinstance(before, str) or not before or not isinstance(after, str) or not after:
            errors.append(f"{row['id']}: missing candidate fragment")
            continue
        if result.count(before) != 1:
            errors.append(f"{row['id']}: fragment absent or repeated in full field")
            continue
        result = result.replace(before, after, 1)

    if errors:
        return FullClozePreview("BLOCKED", None, (), ANOMALY_ID, True, tuple(errors))
    if "10 remember" in result or result.count("to remember") != 1:
        return FullClozePreview(
            "BLOCKED", None, (), ANOMALY_ID, True, ("displaced glyph still present",)
        )
    return FullClozePreview(
        status="PENDING_FULL_FIELD_HUMAN_REVIEW",
        proposed_full_text=result,
        accepted_passage_edit_ids=tuple(f"edit:cloze:{row['id']}" for row in rows),
        technical_candidate_anomaly_id=ANOMALY_ID,
        unresolved_anomaly=True,
        errors=(),
    )
