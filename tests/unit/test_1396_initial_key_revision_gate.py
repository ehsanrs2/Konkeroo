"""Source-independent revision and authority guards for the 1396 INITIAL key.

All values are source-linked provisional claims, not confirmed key answers.
"""

import json
from copy import deepcopy
from pathlib import Path

import pytest

from english_exam.review_docket import (
    _git_blob_sha1,
    audit_review_directory,
    build_review_docket,
)

ROOT = Path(__file__).parents[2] / "dataset" / "review"
KEY_BLOB = "816ed02acebd38d8105424eccc07b91cc1c22736"


def _package():
    def load(name):
        return json.loads((ROOT / name).read_text(encoding="utf-8"))

    return {
        "vocabulary": load("1396-vocabulary-correction-proposals.json"),
        "cloze": load("1396-cloze-text-review.json"),
        "reading": load("1396-reading-text-review.json"),
        "key": load("1396-english-official-key.json"),
        "ledger": load("1396-review-ledger.json"),
    }


def test_curated_key_revision_is_pinned_and_every_claim_remains_pending():
    data = _package()
    before = deepcopy(data)
    key, ledger = data["key"], data["ledger"]
    assert ledger["artifact_git_blob_sha1"]["key"] == KEY_BLOB
    assert _git_blob_sha1(key) == KEY_BLOB
    assert key["key_source"]["edition"] == "INITIAL"
    assert key["key_source"]["booklet_code"] == "C"
    assert key["state"] == "PENDING_HUMAN_REVIEW"
    assert key["transcription_method"] == "AI_DIRECT_VISUAL_READING"
    assert key["verified_final_answer"] is False
    assert key["independent_blind_ai_solution"] is False

    result = audit_review_directory(ROOT)
    assert not result.errors, result.errors
    assert result.status == "BLOCKED_PENDING_REVIEW"
    assert result.reviewed_count == 19
    assert result.pending_count == 75
    key_tasks = [task for task in result.items if task.kind == "key"]
    assert len(key_tasks) == 30
    assert [task.task_id for task in key_tasks] == [f"key:q{number:02d}" for number in range(1, 31)]
    assert all(task.disposition == "PENDING" for task in key_tasks)
    assert all(task.source_pdf_page == 1 for task in key_tasks)
    assert all(task.artifact_git_blob_sha1 == KEY_BLOB for task in key_tasks)
    assert data == before


@pytest.mark.parametrize(
    "mode",
    [
        "valid_but_changed_answer_position",
        "stale_key_blob_pin",
        "unsupported_final_edition",
        "changed_booklet",
        "falsely_verified_key",
        "unblocked_publication",
    ],
)
def test_mutated_initial_key_or_premature_release_blocks_docket(mode):
    data = _package()
    key, ledger = data["key"], data["ledger"]
    if mode == "valid_but_changed_answer_position":
        old = key["entries"][0]["official_answer_position"]
        key["entries"][0]["official_answer_position"] = (old % 4) + 1
    elif mode == "stale_key_blob_pin":
        ledger["artifact_git_blob_sha1"]["key"] = "0" * 40
    elif mode == "unsupported_final_edition":
        key["key_source"]["edition"] = "FINAL"
    elif mode == "changed_booklet":
        key["key_source"]["booklet_code"] = "B"
    elif mode == "falsely_verified_key":
        key["verified_final_answer"] = True
    elif mode == "unblocked_publication":
        ledger["publication_status"] = "RELEASED"

    before = deepcopy(data)
    result = build_review_docket(
        data["vocabulary"],
        data["cloze"],
        data["reading"],
        data["key"],
        data["ledger"],
    )
    assert result.status == "BLOCKED_INVALID_INPUT"
    assert not result.items
    assert result.errors
    assert data == before
