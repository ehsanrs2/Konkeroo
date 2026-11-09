"""Real-PDF editorial review fixture: never edit the original 1396 source."""

import json
from hashlib import sha256
from pathlib import Path

import pytest

from english_exam.pipeline import extract_staged_1396
from english_exam.review_corrections import preview_editorial_corrections

ROOT = Path(__file__).parents[2]
SOURCE = ROOT / "source" / "96.pdf"
CORRECTIONS = ROOT / "dataset" / "review" / "1396-vocabulary-correction-proposals.json"
EXPECTED_SHA256 = "69bc3434ae61c05c85bc9fabffd0b2ce13e5b39bc71b1dfd71c16709c9638ba2"

pytestmark = pytest.mark.source_pdf


def test_1396_vocabulary_visual_edits_match_exact_raw_source():
    if not SOURCE.is_file():
        pytest.skip("original immutable 1396 exam PDF is unavailable")
    assert sha256(SOURCE.read_bytes()).hexdigest() == EXPECTED_SHA256

    staged = extract_staged_1396(SOURCE)
    review = json.loads(CORRECTIONS.read_text(encoding="utf-8"))
    result = preview_editorial_corrections(staged, review)

    assert result.status == "AWAITING_INDEPENDENT_REVIEW", result.errors
    assert not result.errors
    assert len(result.previews) == 7
    by_target = {(item.question_id, item.field): item for item in result.previews}
    assert "You might" in by_target["q-01", "stem"].suggested_corrected_text
    assert "thinking about" in by_target["q-01", "stem"].suggested_corrected_text
    assert "disease, so" in by_target["q-01", "stem"].suggested_corrected_text
    assert "find out" in by_target["q-01", "stem"].suggested_corrected_text
    assert "to settle" in by_target["q-03", "stem"].suggested_corrected_text
    assert "continues" in by_target["q-04", "stem"].suggested_corrected_text
    assert "did not" in by_target["q-05", "stem"].suggested_corrected_text
    assert "try to control" in by_target["q-05", "stem"].suggested_corrected_text
    assert by_target["q-09", "choice_marker:1"].suggested_corrected_text == "1)"
    assert by_target["q-10", "number_marker"].suggested_corrected_text == "10-"

    first_question = staged.exam.sections[0].questions[0]
    assert "mighl" in first_question.stem.raw_text
    assert first_question.stem.corrected_text is None
    assert sha256(SOURCE.read_bytes()).hexdigest() == EXPECTED_SHA256
