"""Independent-review docket for 1396 English source-linked data.

Structural alignment is not independent source review. This module does not
apply corrections, rewrite raw source text, or publish verified answers.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any

EXAM_ID = "iran-ce-msc-1396"
EXAM_SHA = "69bc3434ae61c05c85bc9fabffd0b2ce13e5b39bc71b1dfd71c16709c9638ba2"
KEY_SHA = "5d421dcddc780120b13a08753fd2559e7ec02a60200c7c88f4211d70429cba61"
FILES = {
    "vocabulary": "1396-vocabulary-correction-proposals.json",
    "cloze": "1396-cloze-text-review.json",
    "reading": "1396-reading-text-review.json",
    "key": "1396-english-official-key.json",
    "ledger": "1396-review-ledger.json",
}
DISPOSITIONS = {
    "edit": frozenset({"ACCEPTED", "REJECTED", "NEEDS_FOLLOWUP"}),
    "anomaly": frozenset({"RESOLVED", "NEEDS_FOLLOWUP"}),
    "printed": frozenset({"ACKNOWLEDGED", "DISPUTED"}),
    "key": frozenset({"TRANSCRIPTION_CONFIRMED", "DISPUTED"}),
}
UNRESOLVED = frozenset({"REJECTED", "NEEDS_FOLLOWUP", "DISPUTED"})


@dataclass(frozen=True, slots=True)
class ReviewItem:
    task_id: str
    kind: str
    source_sha256: str
    source_pdf_page: int
    disposition: str = "PENDING"


@dataclass(frozen=True, slots=True)
class ReviewDocket:
    status: str
    items: tuple[ReviewItem, ...]
    reviewed_count: int
    pending_count: int
    disputed_or_followup_count: int
    errors: tuple[str, ...]


def _dict(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _rows(data: Mapping[str, Any], field: str, errors: list[str]) -> list[Mapping[str, Any]]:
    rows = data.get(field)
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        errors.append(f"invalid {field} list")
        return []
    return rows


def build_review_docket(
    vocabulary: Mapping[str, Any],
    cloze: Mapping[str, Any],
    reading: Mapping[str, Any],
    key: Mapping[str, Any],
    ledger: Mapping[str, Any],
) -> ReviewDocket:
    """Derive item IDs from source artifacts; fail closed on any mismatch."""
    errors: list[str] = []
    items: list[ReviewItem] = []

    configs = (
        ("vocabulary", vocabulary, "EDITORIAL_CORRECTION_PROPOSALS", "AWAITING_INDEPENDENT_REVIEW"),
        ("cloze", cloze, "SOURCE_LINKED_CLOZE_TEXT_REVIEW", "PENDING_INDEPENDENT_REVIEW"),
        ("reading", reading, "SOURCE_LINKED_READING_TEXT_REVIEW", "PENDING_INDEPENDENT_REVIEW"),
        ("key", key, "SOURCE_LINKED_VISUAL_KEY_TRANSCRIPTION", "PENDING_HUMAN_REVIEW"),
    )
    for group, data, artifact_type, state in configs:
        exam_id = data.get("canonical_exam_id", data.get("exam_id"))
        if data.get("artifact_type") != artifact_type or exam_id != EXAM_ID:
            errors.append(f"{group}: unexpected artifact type or exam ID")
        status = data.get("review_state", data.get("review_status", data.get("state")))
        if status != state:
            errors.append(f"{group}: unsupported source review status")
        source = _dict(data.get("source", data.get("exam_source")))
        if source.get("filename") != "96.pdf" or source.get("sha256") != EXAM_SHA:
            errors.append(f"{group}: original exam source identity mismatch")

    if vocabulary.get("review_method") != "ASSISTANT_DIRECT_VISUAL_COMPARISON":
        errors.append("vocabulary: visual review method missing")
    if cloze.get("method") != "ASSISTANT_DIRECT_VISUAL_COMPARISON":
        errors.append("cloze: visual review method missing")
    if reading.get("review_method") != "ASSISTANT_DIRECT_VISUAL_COMPARISON":
        errors.append("reading: visual review method missing")
    if key.get("transcription_method") != "AI_DIRECT_VISUAL_READING":
        errors.append("key: original visual method missing")
    if key.get("verified_final_answer") is not False:
        errors.append("key: must not claim final verification")
    source_key = _dict(key.get("key_source"))
    for field, expected in (
        ("filename", "96_Key.pdf"),
        ("sha256", KEY_SHA),
        ("booklet_code", "C"),
        ("edition", "INITIAL"),
        ("page_number", 1),
    ):
        if source_key.get(field) != expected:
            errors.append(f"key: mismatched {field}")

    def append(task_id: str, kind: str, page: Any, source_sha: str = EXAM_SHA) -> None:
        if type(page) is not int or page <= 0 or page > (1 if kind == "key" else 5):
            errors.append(f"{task_id}: invalid source PDF page")
            return
        items.append(ReviewItem(task_id, kind, source_sha, page))

    for group, data, count in (
        ("vocabulary", vocabulary, 11),
        ("cloze", cloze, 7),
        ("reading", reading, 36),
    ):
        rows = _rows(data, "proposals", errors)
        if len(rows) != count:
            errors.append(f"{group}: unexpected proposal count")
        for row in rows:
            row_id = row.get("id")
            if not isinstance(row_id, str) or not row_id:
                errors.append(f"{group}: malformed proposal ID")
                continue
            raw = row.get("expected_raw_fragment")
            if not isinstance(raw, str) or not raw.strip() or len(raw) >= 50:
                errors.append(f"{group}/{row_id}: invalid short raw snippet")
            if group == "vocabulary":
                page = row.get("source_pdf_page")
                if page != 2 or not str(row.get("question_id", "")).startswith("q-"):
                    errors.append(f"{group}/{row_id}: invalid question/page")
            elif group == "cloze":
                page = row.get("pdf_page")
                if row.get("proposal_status") != "PENDING_INDEPENDENT_REVIEW":
                    errors.append(f"{group}/{row_id}: unexpected proposal status")
                if page != (3 if str(row.get("entity_id", "")).startswith("q-") else 2):
                    errors.append(f"{group}/{row_id}: unexpected printed page")
            else:
                page = row.get("source_pdf_page")
                if row.get("review_status") != "PENDING_INDEPENDENT_REVIEW":
                    errors.append(f"{group}/{row_id}: unexpected proposal status")
                passage = row.get("passage_id")
                if passage not in ("reading-1", "reading-2", "reading-3"):
                    errors.append(f"{group}/{row_id}: invalid passage ID")
            append(f"edit:{group}:{row_id}", "edit", page)

    for group, data, count in (("cloze", cloze, 1), ("reading", reading, 5)):
        rows = _rows(data, "unresolved_anomalies", errors)
        if len(rows) != count:
            errors.append(f"{group}: unexpected anomaly count")
        for row in rows:
            row_id = row.get("id")
            if not isinstance(row_id, str) or not row_id:
                errors.append(f"{group}: invalid anomaly ID")
                continue
            if row.get("status") != "NEEDS_SOURCE_ALIGNED_REVIEW":
                errors.append(f"{group}/{row_id}: unresolved state changed")
            if row.get("proposed_replacement") is not None:
                errors.append(f"{group}/{row_id}: guessed nonlocal replacement")
            page = row.get("pdf_page", row.get("source_pdf_page"))
            append(f"anomaly:{group}:{row_id}", "anomaly", page)

    printed = _rows(reading, "printed_source_anomalies", errors)
    if len(printed) != 4:
        errors.append("reading: unexpected printed oddity count")
    for note in printed:
        fragment = note.get("printed_fragment")
        page = note.get("source_pdf_page")
        if not isinstance(fragment, str) or not fragment.strip() or len(fragment) >= 60:
            errors.append("reading: invalid printed oddity")
            continue
        fingerprint = sha256(f"{page}\0{fragment}".encode()).hexdigest()[:16]
        append(f"printed:reading:{fingerprint}", "printed", page)

    key_entries = _rows(key, "entries", errors)
    numbers = [row.get("question_number") for row in key_entries]
    if numbers != list(range(1, 31)):
        errors.append("key: missing, reordered or duplicated Q1–30")
    if key.get("independent_blind_ai_solution") is not False:
        errors.append("key: must not falsely claim blind AI solution")
    for row in key_entries:
        number = row.get("question_number")
        option = row.get("official_answer_position")
        if type(number) is not int or not (1 <= number <= 30):
            errors.append("key: invalid question number")
            continue
        if type(option) is not int or not (1 <= option <= 4):
            errors.append(f"key: invalid option for Q{number}")
        if row.get("key_table_group") != 1 or row.get("key_table_row") != number:
            errors.append(f"key: invalid source table locator Q{number}")
        expected_page = 2 if number <= 10 else 3 if number <= 19 else 4 if number <= 24 else 5
        if row.get("question_pdf_page") != expected_page:
            errors.append(f"key: unexpected exam question page Q{number}")
        append(f"key:q{number:02d}", "key", 1, KEY_SHA)

    seen = Counter(item.task_id for item in items)
    if any(count != 1 for count in seen.values()):
        errors.append("duplicate review task IDs")
    if len(items) != 94:
        errors.append("expected 94 review tasks (54 edits, 6 anomalies, 4 printed, 30 key)")
    if ledger.get("schema_version") != "1.0" or (
        ledger.get("artifact_type") != "INDEPENDENT_REVIEW_LEDGER"
    ):
        errors.append("unsupported decision ledger schema")
    if ledger.get("exam_id") != EXAM_ID or (
        ledger.get("exam_source_sha256") != EXAM_SHA
        or ledger.get("official_key_source_sha256") != KEY_SHA
    ):
        errors.append("decision ledger source identity mismatch")
    if ledger.get("publication_status") != "BLOCKED" or (
        ledger.get("independently_verified") is not False
    ):
        errors.append("ledger cannot grant verified publication")
    decisions = _rows(ledger, "decisions", errors)
    by_id = {item.task_id: item for item in items}
    reviewed: dict[str, str] = {}
    for decision in decisions:
        task_id = decision.get("task_id")
        if not isinstance(task_id, str) or task_id not in by_id:
            errors.append("unknown review task")
            continue
        if task_id in reviewed:
            errors.append(f"{task_id}: duplicate reviewer decision")
            continue
        item = by_id[task_id]
        disposition = decision.get("disposition")
        if disposition not in DISPOSITIONS[item.kind]:
            errors.append(f"{task_id}: unsupported disposition")
            continue
        if decision.get("reviewer_role") != "INDEPENDENT_HUMAN":
            errors.append(f"{task_id}: independent human attestation required")
        reviewer_id = decision.get("reviewer_id")
        if not isinstance(reviewer_id, str) or len(reviewer_id.strip()) < 3:
            errors.append(f"{task_id}: reviewer identification required")
        note = decision.get("evidence_note")
        if not isinstance(note, str) or len(note.strip()) < 12:
            errors.append(f"{task_id}: substantive evidence note required")
        if decision.get("evidence_source_sha256") != item.source_sha256 or (
            decision.get("evidence_pdf_page") != item.source_pdf_page
        ):
            errors.append(f"{task_id}: evidence source/page mismatch")
        if set(decision) != {
            "task_id",
            "disposition",
            "reviewer_role",
            "reviewer_id",
            "evidence_note",
            "evidence_source_sha256",
            "evidence_pdf_page",
        }:
            errors.append(f"{task_id}: unexpected or missing decision fields")
        reviewed[task_id] = disposition

    if errors:
        return ReviewDocket("BLOCKED_INVALID_INPUT", (), 0, 0, 0, tuple(errors))
    final_items = tuple(
        ReviewItem(
            task_id=item.task_id,
            kind=item.kind,
            source_sha256=item.source_sha256,
            source_pdf_page=item.source_pdf_page,
            disposition=reviewed.get(item.task_id, "PENDING"),
        )
        for item in items
    )
    pending = sum(item.disposition == "PENDING" for item in final_items)
    followup = sum(item.disposition in UNRESOLVED for item in final_items)
    status = "BLOCKED_PENDING_REVIEW" if pending or followup else "REVIEWED_NOT_PUBLISHED"
    return ReviewDocket(status, final_items, len(reviewed), pending, followup, ())


def audit_review_directory(directory: Path) -> ReviewDocket:
    """Read the five explicitly named files, without reading any source PDF."""
    data = {
        group: json.loads((directory / filename).read_text(encoding="utf-8"))
        for group, filename in FILES.items()
    }
    return build_review_docket(
        data["vocabulary"], data["cloze"], data["reading"], data["key"], data["ledger"]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit 1396 independent-review readiness")
    parser.add_argument("--review-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = audit_review_directory(args.review_dir)
    except (OSError, ValueError, TypeError) as error:
        print(json.dumps({"status": "BLOCKED_INVALID_INPUT", "error": str(error)}))
        return 2
    counts = Counter(item.kind for item in result.items)
    print(
        json.dumps(
            {
                "status": result.status,
                "review_tasks": len(result.items),
                "by_kind": dict(sorted(counts.items())),
                "reviewed": result.reviewed_count,
                "pending": result.pending_count,
                "followup_or_disputed": result.disputed_or_followup_count,
                "errors": result.errors,
            },
            sort_keys=True,
        )
    )
    return 2 if result.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
