"""Local source-present integration of curated 1396 key and staged exam data."""

import json
from hashlib import sha256
from pathlib import Path

import pytest

from english_exam.pipeline import extract_staged_1396
from english_exam.review_reconciliation import ExpectedKeyIdentity, align_curated_official_claims

ROOT = Path(__file__).parents[2]
SOURCE = ROOT / "source" / "96.pdf"
KEY_SOURCE = ROOT / "source" / "96_Key.pdf"
CURATED = ROOT / "dataset" / "review" / "1396-english-official-key.json"
EXAM_SHA256 = "69bc3434ae61c05c85bc9fabffd0b2ce13e5b39bc71b1dfd71c16709c9638ba2"
KEY = ExpectedKeyIdentity(
    filename="96_Key.pdf",
    sha256="5d421dcddc780120b13a08753fd2559e7ec02a60200c7c88f4211d70429cba61",
    booklet_code="C",
    edition="INITIAL",
    page_number=1,
    table_group=1,
)

pytestmark = pytest.mark.source_pdf


def test_source_present_alignment_matches_all_1396_english_questions():
    if not SOURCE.is_file() or not KEY_SOURCE.is_file():
        pytest.skip("immutable 1396 exam and official-key source files are unavailable")
    assert sha256(SOURCE.read_bytes()).hexdigest() == EXAM_SHA256
    assert sha256(KEY_SOURCE.read_bytes()).hexdigest() == KEY.sha256

    staged = extract_staged_1396(SOURCE)
    curated = json.loads(CURATED.read_text(encoding="utf-8"))
    initial_answer = staged.exam.sections[0].questions[0].answers.official
    alignment = align_curated_official_claims(staged, curated, expected_key=KEY)

    assert not alignment.errors
    assert alignment.status == "ALIGNED_PENDING_HUMAN_REVIEW"
    assert len(alignment.claims) == 30
    assert [claim.question_number for claim in alignment.claims] == list(range(1, 31))
    by_number = {claim.question_number: claim for claim in alignment.claims}
    assert by_number[11].passage_id == "cloze-1"
    assert by_number[20].passage_id == "reading-1"
    assert by_number[25].passage_id == "reading-2"
    assert by_number[30].passage_id == "reading-3"
    assert all(claim.review_state == "PENDING_HUMAN_REVIEW" for claim in alignment.claims)
    assert staged.exam.sections[0].questions[0].answers.official == initial_answer
    assert curated["state"] == "PENDING_HUMAN_REVIEW"
