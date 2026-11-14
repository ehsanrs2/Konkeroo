"""Local source-present integration of curated 1396 key and staged exam data.

This asserts deterministic structural identity, NOT correctness of the visual
transcription or the existence of a later/final official answer key.
"""

import json
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

import pytest

from english_exam.pipeline import extract_staged_1396
from english_exam.review_docket import _git_blob_sha1, audit_review_directory
from english_exam.review_reconciliation import ExpectedKeyIdentity, align_curated_official_claims

ROOT = Path(__file__).parents[2]
SOURCE = ROOT / "source" / "96.pdf"
KEY_SOURCE = ROOT / "source" / "96_Key.pdf"
REVIEW_DIR = ROOT / "dataset" / "review"
CURATED = REVIEW_DIR / "1396-english-official-key.json"
LEDGER = REVIEW_DIR / "1396-review-ledger.json"

EXAM_SHA256 = "69bc3434ae61c05c85bc9fabffd0b2ce13e5b39bc71b1dfd71c16709c9638ba2"
KEY_BLOB_SHA1 = "816ed02acebd38d8105424eccc07b91cc1c22736"
KEY = ExpectedKeyIdentity(
    filename="96_Key.pdf",
    sha256="5d421dcddc780120b13a08753fd2559e7ec02a60200c7c88f4211d70429cba61",
    booklet_code="C",
    edition="INITIAL",
    page_number=1,
    table_group=1,
)
pytestmark = pytest.mark.source_pdf


def _questions(staged):
    for section in staged.exam.sections:
        yield from section.questions
        for passage in section.passages:
            yield from passage.questions


def test_source_present_alignment_matches_all_1396_english_questions():
    if not SOURCE.is_file() or not KEY_SOURCE.is_file():
        pytest.skip("immutable 1396 exam and official-key source files are unavailable")
    assert sha256(SOURCE.read_bytes()).hexdigest() == EXAM_SHA256
    assert sha256(KEY_SOURCE.read_bytes()).hexdigest() == KEY.sha256

    staged = extract_staged_1396(SOURCE)
    curated = json.loads(CURATED.read_text(encoding="utf-8"))
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    original_stage = deepcopy(staged)
    original_key = deepcopy(curated)
    original_ledger = deepcopy(ledger)

    # The proposal revision must be exactly the historical one recorded
    # in the immutable review ledger, not a replaced but plausible-looking key.
    assert ledger["artifact_git_blob_sha1"]["key"] == KEY_BLOB_SHA1
    assert _git_blob_sha1(curated) == KEY_BLOB_SHA1
    assert ledger["exam_source_sha256"] == EXAM_SHA256
    assert ledger["official_key_source_sha256"] == KEY.sha256
    assert ledger["publication_status"] == "BLOCKED"
    assert ledger["independently_verified"] is False
    docket = audit_review_directory(REVIEW_DIR)
    assert not docket.errors, docket.errors
    assert docket.status == "BLOCKED_PENDING_REVIEW"
    assert docket.reviewed_count == 19
    assert docket.pending_count == 75

    assert staged.validation.status == "PASSED"
    alignment = align_curated_official_claims(staged, curated, expected_key=KEY)

    assert not alignment.errors, alignment.errors
    assert alignment.status == "ALIGNED_PENDING_HUMAN_REVIEW"
    assert len(alignment.claims) == 30
    assert [claim.question_number for claim in alignment.claims] == list(range(1, 31))
    assert len(list(_questions(staged))) == 30
    by_number = {claim.question_number: claim for claim in alignment.claims}
    assert {n: by_number[n].passage_id for n in (11, 20, 25, 26, 30)} == {
        11: "cloze-1",
        20: "reading-1",
        25: "reading-2",
        26: "reading-3",
        30: "reading-3",
    }
    assert by_number[20].key_table_row == 20
    assert by_number[25].key_table_row == 25
    assert all(
        claim.review_state == "PENDING_HUMAN_REVIEW"
        and claim.key_filename == KEY.filename
        and claim.key_page_number == KEY.page_number
        and claim.key_booklet_code == KEY.booklet_code
        and claim.key_edition == KEY.edition
        and claim.key_table_group == KEY.table_group
        and claim.key_table_row == claim.question_number
        and 1 <= claim.official_answer_position <= 4
        for claim in alignment.claims
    )
    assert all(
        question.answers.official is None
        and question.answers.ai is None
        and question.answers.final_verified is None
        for question in _questions(staged)
    )
    assert staged == original_stage
    assert curated == original_key
    assert ledger == original_ledger
    assert sha256(SOURCE.read_bytes()).hexdigest() == EXAM_SHA256
    assert sha256(KEY_SOURCE.read_bytes()).hexdigest() == KEY.sha256
