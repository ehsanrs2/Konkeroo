"""Review docket contract tests, independent of any source PDF."""

import json
from collections import Counter
from copy import deepcopy
from pathlib import Path

import pytest

from english_exam.review_docket import (
    DISPOSITIONS,
    KEY_SHA,
    _git_blob_sha1,
    audit_review_directory,
    build_review_docket,
)

REVIEW_DIR = Path(__file__).parents[2] / "dataset" / "review"


def _package():
    names = (
        "1396-vocabulary-correction-proposals.json",
        "1396-cloze-text-review.json",
        "1396-reading-text-review.json",
        "1396-english-official-key.json",
        "1396-review-ledger.json",
    )
    return tuple(json.loads((REVIEW_DIR / name).read_text(encoding="utf-8")) for name in names)


def _audit(package):
    return build_review_docket(*package)


def _decision(item, disposition=None):
    if disposition is None:
        disposition = {
            "edit": "ACCEPTED",
            "anomaly": "RESOLVED",
            "printed": "ACKNOWLEDGED",
            "key": "TRANSCRIPTION_CONFIRMED",
        }[item.kind]
    return {
        "task_id": item.task_id,
        "disposition": disposition,
        "reviewer_role": "INDEPENDENT_HUMAN",
        "reviewer_id": "synthetic-reviewer",
        "evidence_note": "Synthetic evidence for testing the decision validator only.",
        "evidence_source_sha256": item.source_sha256,
        "evidence_pdf_page": item.source_pdf_page,
        "reviewed_artifact_blob_sha1": item.artifact_git_blob_sha1,
    }


def test_merged_review_package_derives_18_reviewed_and_76_pending_tasks():
    result = audit_review_directory(REVIEW_DIR)
    assert result.status == "BLOCKED_PENDING_REVIEW"
    assert not result.errors
    assert result.reviewed_count == 18
    assert result.pending_count == 76
    assert result.disputed_or_followup_count == 0
    assert len(result.items) == 94
    assert Counter(item.kind for item in result.items) == {
        "edit": 54,
        "anomaly": 6,
        "printed": 4,
        "key": 30,
    }
    assert len({item.task_id for item in result.items}) == 94
    assert sum(item.disposition == "ACCEPTED" for item in result.items) == 18
    assert all(
        item.disposition == "PENDING"
        for item in result.items
        if not item.task_id.startswith(("edit:vocabulary:", "edit:cloze:"))
    )
    assert all(len(item.artifact_git_blob_sha1) == 40 for item in result.items)
    assert all(item.source_sha256 == KEY_SHA for item in result.items if item.kind == "key")


@pytest.mark.parametrize(
    ("index", "change"),
    [
        (0, lambda d: d["exam_source"].update(sha256="a" * 64)),
        (1, lambda d: d.update(review_status="VERIFIED")),
        (2, lambda d: d["proposals"].append(deepcopy(d["proposals"][0]))),
        (2, lambda d: d["unresolved_anomalies"][0].update(proposed_replacement="guess")),
        (3, lambda d: d["key_source"].update(edition="FINAL")),
        (3, lambda d: d["entries"][19].update(question_pdf_page=3)),
        (3, lambda d: d["entries"][0].update(official_answer_position=5)),
        (3, lambda d: d["entries"].pop()),
        (4, lambda d: d.update(publication_status="VERIFIED")),
        (4, lambda d: d.update(independently_verified=True)),
        (4, lambda d: d.update(official_key_source_sha256="bad")),
        (4, lambda d: d["artifact_git_blob_sha1"].update(key="0" * 40)),
        (4, lambda d: d.pop("artifact_git_blob_sha1")),
    ],
)
def test_structural_or_source_mismatch_blocks_all_review_tasks(index, change):
    package = list(_package())
    change(package[index])
    result = _audit(package)
    assert result.status == "BLOCKED_INVALID_INPUT"
    assert result.errors
    assert result.items == ()


def test_single_evidenced_decision_preserves_remaining_pending_items():
    package = list(_package())
    first = _audit(package).items[0]
    package[4]["decisions"] = [_decision(first)]
    result = _audit(package)
    assert result.status == "BLOCKED_PENDING_REVIEW"
    assert result.reviewed_count == 1
    assert result.pending_count == 93
    assert result.disputed_or_followup_count == 0
    assert result.items[0].disposition == "ACCEPTED"


def test_unknown_duplicate_or_invalid_decision_blocks_all():
    for change in (
        lambda d: d.update(task_id="unknown"),
        lambda d: d.update(reviewer_role="AI_ASSISTANT"),
        lambda d: d.update(reviewer_id=""),
        lambda d: d.update(evidence_note=""),
        lambda d: d.update(evidence_source_sha256="wrong"),
        lambda d: d.update(evidence_pdf_page=90),
        lambda d: d.update(reviewed_artifact_blob_sha1="0" * 40),
        lambda d: d.pop("reviewed_artifact_blob_sha1"),
        lambda d: d.update(disposition="VERIFIED"),
        lambda d: d.update(extra="not in schema"),
    ):
        package = list(_package())
        original = _audit(package).items[0]
        decision = _decision(original)
        change(decision)
        package[4]["decisions"] = [decision]
        result = _audit(package)
        assert result.status == "BLOCKED_INVALID_INPUT"
        assert result.items == ()
        assert result.errors

    package = list(_package())
    item = _audit(package).items[0]
    package[4]["decisions"] = [_decision(item), _decision(item)]
    assert _audit(package).status == "BLOCKED_INVALID_INPUT"


def test_wrong_disposition_for_task_kind_is_rejected():
    items = _audit(_package()).items
    for kind, dispositions in DISPOSITIONS.items():
        item = next(row for row in items if row.kind == kind)
        forbidden = next(
            value
            for value in ("ACCEPTED", "RESOLVED", "ACKNOWLEDGED", "DISPUTED")
            if value not in dispositions
        )
        package = list(_package())
        package[4]["decisions"] = [_decision(item, forbidden)]
        assert _audit(package).status == "BLOCKED_INVALID_INPUT"


def test_all_synthetic_decisions_still_do_not_create_a_verified_release():
    package = list(_package())
    items = _audit(package).items
    package[4]["decisions"] = [_decision(item) for item in items]
    result = _audit(package)
    assert not result.errors
    assert result.reviewed_count == 94
    assert result.pending_count == 0
    assert result.status == "REVIEWED_NOT_PUBLISHED"
    assert all(item.disposition != "PENDING" for item in result.items)
    assert package[4]["independently_verified"] is False
    assert package[4]["publication_status"] == "BLOCKED"


def test_disputed_or_followup_decisions_continue_to_block_publication():
    package = list(_package())
    items = _audit(package).items
    decisions = [_decision(item) for item in items]
    decisions[0]["disposition"] = "REJECTED"
    package[4]["decisions"] = decisions
    result = _audit(package)
    assert result.status == "BLOCKED_PENDING_REVIEW"
    assert result.disputed_or_followup_count == 1
    assert result.pending_count == 0


@pytest.mark.parametrize(
    ("index", "mutate"),
    [
        (0, lambda d: d["proposals"][1].update(proposed_replacement="wrong")),
        (1, lambda d: d["proposals"][0].update(proposed_replacement="Not passage")),
        (2, lambda d: d["proposals"][1].update(proposed_printed_fragment="three systems")),
        (3, lambda d: d["entries"][0].update(official_answer_position=2)),
    ],
)
def test_valid_looking_proposal_or_official_key_change_invalidates_revision_pin(index, mutate):
    package = list(_package())
    mutate(package[index])
    result = _audit(package)
    assert result.status == "BLOCKED_INVALID_INPUT"
    assert not result.items
    assert any("artifact revision changed" in error for error in result.errors)


def test_old_review_decision_cannot_be_replayed_after_repinning_changed_artifact():
    package = list(_package())
    item = _audit(package).items[0]
    package[4]["decisions"] = [_decision(item)]
    package[0]["proposals"][1]["proposed_replacement"] = "wrong"
    package[4]["artifact_git_blob_sha1"]["vocabulary"] = _git_blob_sha1(package[0])
    result = _audit(package)
    assert result.status == "BLOCKED_INVALID_INPUT"
    assert not result.items
    assert any("stale artifact revision" in error for error in result.errors)


def test_git_revision_pin_matches_repository_json_representation():
    package = _package()
    for group, artifact in zip(("vocabulary", "cloze", "reading", "key"), package[:4], strict=True):
        assert _git_blob_sha1(artifact) == package[4]["artifact_git_blob_sha1"][group]


def test_recorded_human_review_only_covers_11_original_vocabulary_proposals():
    package = _package()
    vocabulary, _, _, _, ledger = package
    decisions = [
        decision
        for decision in ledger["decisions"]
        if decision["task_id"].startswith("edit:vocabulary:")
    ]
    expected_task_ids = [f"edit:vocabulary:{p['id']}" for p in vocabulary["proposals"]]
    assert [decision["task_id"] for decision in decisions] == expected_task_ids
    assert len(decisions) == 11
    for decision in decisions:
        assert decision["disposition"] == "ACCEPTED"
        assert decision["reviewer_role"] == "INDEPENDENT_HUMAN"
        assert decision["reviewer_id"] == "ehsanrs2"
        assert decision["evidence_pdf_page"] == 2
        assert decision["evidence_source_sha256"] == ledger["exam_source_sha256"]
        assert (
            decision["reviewed_artifact_blob_sha1"]
            == ledger["artifact_git_blob_sha1"]["vocabulary"]
        )
        assert "Human reviewer report" in decision["evidence_note"]
    assert ledger["publication_status"] == "BLOCKED"
    assert ledger["independently_verified"] is False


def test_seven_owner_confirmed_cloze_edits_preserve_pending_nonlocal_anomaly():
    package = _package()
    _, cloze, _, _, ledger = package
    decisions = [
        decision
        for decision in ledger["decisions"]
        if decision["task_id"].startswith("edit:cloze:")
    ]
    assert len(decisions) == 7
    assert [d["task_id"] for d in decisions] == [
        f"edit:cloze:{proposal['id']}" for proposal in cloze["proposals"]
    ]
    for proposal, decision in zip(cloze["proposals"], decisions, strict=True):
        assert decision["disposition"] == "ACCEPTED"
        assert decision["reviewer_role"] == "INDEPENDENT_HUMAN"
        assert decision["reviewer_id"] == "ehsanrs2"
        assert decision["evidence_pdf_page"] == proposal["pdf_page"]
        assert decision["evidence_source_sha256"] == ledger["exam_source_sha256"]
        assert decision["reviewed_artifact_blob_sha1"] == ledger["artifact_git_blob_sha1"]["cloze"]
        assert "group-level human attestation" in decision["evidence_note"]
        assert "No separate per-item quote" in decision["evidence_note"]

    anomaly = "anomaly:cloze:cloze-ability-to-remember-displaced-token"
    assert not any(d["task_id"] == anomaly for d in ledger["decisions"])
    docket = _audit(package)
    assert not docket.errors
    assert next(item for item in docket.items if item.task_id == anomaly).disposition == "PENDING"
    assert docket.reviewed_count == 18
    assert docket.pending_count == 76
    assert ledger["publication_status"] == "BLOCKED"
    assert ledger["independently_verified"] is False


def test_revised_cloze_evidence_cannot_validate_against_wrong_artifact_revision():
    package = list(_package())
    decision = next(
        item for item in package[4]["decisions"] if item["task_id"].startswith("edit:cloze:")
    )
    decision["reviewed_artifact_blob_sha1"] = "0" * 40
    docket = _audit(package)
    assert docket.status == "BLOCKED_INVALID_INPUT"
    assert docket.items == ()
    assert any("stale artifact revision" in error for error in docket.errors)
