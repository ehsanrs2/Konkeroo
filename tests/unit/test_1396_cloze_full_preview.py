"""Source-independent tests for combined 1396 Cloze reviewer preview."""

import json
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import pytest

from english_exam.cloze_full_preview import preview_1396_reviewed_cloze_passage
from english_exam.cloze_order_review import EXAM_SHA, RAW_ANCHOR

REVIEW_DIR = Path(__file__).parents[2] / "dataset" / "review"
RAW = (
    "An integral part of Imm an existence.\n"
    "Since birth en the impression of events.\n"
    "Though, {14) systematic techniques enable us lo study memory.\n"
    + RAW_ANCHOR
    + " (15) more recent brain-imaging\napproaches."
)


def _package():
    review = json.loads((REVIEW_DIR / "1396-cloze-text-review.json").read_text(encoding="utf-8"))
    ledger = json.loads((REVIEW_DIR / "1396-review-ledger.json").read_text(encoding="utf-8"))
    return review, ledger


def _staged(raw=RAW):
    body = SimpleNamespace(
        raw_text=raw,
        normalized_text=None,
        corrected_text=None,
        provenance=(SimpleNamespace(page_number=2, source_filename="96.pdf"),),
    )
    exam = SimpleNamespace(
        id="iran-ce-msc-1396",
        source_document=SimpleNamespace(
            source_filename="96.pdf", sha256=EXAM_SHA, english_pdf_pages=(2, 3, 4, 5)
        ),
        sections=(
            SimpleNamespace(id="cloze", passages=(SimpleNamespace(id="cloze-1", body=body),)),
        ),
    )
    return SimpleNamespace(exam=exam, validation=SimpleNamespace(status="PASSED", errors=()))


def test_full_preview_applies_only_four_attested_body_edits_plus_one_candidate():
    staged = _staged()
    review, ledger = _package()
    originals = deepcopy((staged, review, ledger))
    report = preview_1396_reviewed_cloze_passage(staged, review, ledger)
    assert report.status == "PENDING_FULL_FIELD_HUMAN_REVIEW"
    assert not report.errors
    assert report.unresolved_anomaly is False
    assert report.technical_candidate_anomaly_id == "cloze-ability-to-remember-displaced-token"
    assert len(report.accepted_passage_edit_ids) == 4
    assert report.proposed_full_text == (
        RAW.replace("Imm an", "human")
        .replace("en the", "on the")
        .replace("{14)", "(14)")
        .replace("lo study", "to study")
        .replace("10 remember", "to remember")
    )
    assert "10 remember" not in report.proposed_full_text
    assert report.proposed_full_text.count("to remember") == 1
    assert staged.exam.sections[0].passages[0].body.corrected_text is None
    assert (staged, review, ledger) == originals


@pytest.mark.parametrize(
    "mode",
    [
        "remove_decision",
        "reverse_decision",
        "fake_human",
        "stale_decision_pin",
        "falsify_reviewed_blob",
        "change_accepted_proposal",
        "duplicate_text",
        "wrong_source",
        "already_corrected",
        "anomaly_resolved",
        "invalid_anomaly_role",
        "stale_anomaly_pin",
        "unsupported_anomaly_disposition",
        "publish_verified",
    ],
)
def test_full_preview_blocks_unsupported_release_or_review_claim(mode):
    staged = _staged()
    review, ledger = _package()
    if mode == "remove_decision":
        ledger["decisions"] = [
            d for d in ledger["decisions"] if d["task_id"] != "edit:cloze:cloze-human"
        ]
    elif mode == "reverse_decision":
        next(d for d in ledger["decisions"] if d["task_id"] == "edit:cloze:cloze-human")[
            "disposition"
        ] = "REJECTED"
    elif mode == "fake_human":
        next(d for d in ledger["decisions"] if d["task_id"] == "edit:cloze:cloze-human")[
            "reviewer_role"
        ] = "AI_ASSISTANT"
    elif mode == "stale_decision_pin":
        next(d for d in ledger["decisions"] if d["task_id"] == "edit:cloze:cloze-human")[
            "reviewed_artifact_blob_sha1"
        ] = "0" * 40
    elif mode == "falsify_reviewed_blob":
        ledger["artifact_git_blob_sha1"]["cloze"] = "0" * 40
    elif mode == "change_accepted_proposal":
        review["proposals"][1]["proposed_replacement"] = "guess"
    elif mode == "duplicate_text":
        staged.exam.sections[0].passages[0].body.raw_text += "\nImm an"
    elif mode == "wrong_source":
        staged.exam.source_document.sha256 = "0" * 64
    elif mode == "already_corrected":
        staged.exam.sections[0].passages[0].body.corrected_text = "edited"
    elif mode == "anomaly_resolved":
        ledger["decisions"].append(
            {"task_id": "anomaly:cloze:cloze-ability-to-remember-displaced-token"}
        )
    elif mode == "invalid_anomaly_role":
        next(d for d in ledger["decisions"] if d["task_id"].startswith("anomaly:cloze:"))[
            "reviewer_role"
        ] = "AI_ASSISTANT"
    elif mode == "stale_anomaly_pin":
        next(d for d in ledger["decisions"] if d["task_id"].startswith("anomaly:cloze:"))[
            "reviewed_artifact_blob_sha1"
        ] = "0" * 40
    elif mode == "unsupported_anomaly_disposition":
        next(d for d in ledger["decisions"] if d["task_id"].startswith("anomaly:cloze:"))[
            "disposition"
        ] = "ACCEPTED"
    elif mode == "publish_verified":
        ledger["publication_status"] = "VERIFIED"

    snapshot = deepcopy((staged, review, ledger))
    report = preview_1396_reviewed_cloze_passage(staged, review, ledger)
    assert report.status == "BLOCKED"
    assert report.proposed_full_text is None
    assert report.errors
    assert (staged, review, ledger) == snapshot
