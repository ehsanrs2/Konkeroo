"""Original-PDF-conditional Reading 2 assistant provisional source geometry tests.

GitHub CI without source/ Git LFS media skips this test honestly.
"""

import json
from hashlib import sha256
from pathlib import Path

import pdfplumber
import pytest

from english_exam.pipeline import extract_staged_1396
from english_exam.reading2_provisional import (
    EXPECTED_EDIT_IDS,
    PRINTED_ODDITY,
    preview_1396_reading2,
)

ROOT = Path(__file__).parents[2]
SOURCE = ROOT / "source" / "96.pdf"
EXPECTED_SHA = "69bc3434ae61c05c85bc9fabffd0b2ce13e5b39bc71b1dfd71c16709c9638ba2"
pytestmark = pytest.mark.source_pdf


def test_reading2_original_pages_4_5_edits_and_nonlocal_glyph_geometry():
    if not SOURCE.is_file():
        pytest.skip("original source/96.pdf unavailable; source-dependent check not executed")
    assert sha256(SOURCE.read_bytes()).hexdigest() == EXPECTED_SHA

    reading = json.loads(
        (ROOT / "dataset/review/1396-reading-text-review.json").read_text(encoding="utf-8")
    )
    ledger = json.loads(
        (ROOT / "dataset/review/1396-review-ledger.json").read_text(encoding="utf-8")
    )
    original_ledger = json.dumps(ledger, sort_keys=True)
    staged = extract_staged_1396(SOURCE)
    assert staged.validation.status == "PASSED"
    passage = staged.exam.sections[2].passages[1]
    assert passage.id == "reading-2"
    original_heading = passage.heading.raw_text
    original_body = passage.body.raw_text

    preview = preview_1396_reading2(staged, reading, ledger)
    assert preview.status == "ASSISTANT_PROVISIONAL"
    assert preview.errors == ()
    assert preview.applied_edit_ids == EXPECTED_EDIT_IDS
    assert len(preview.technical_candidates) == 2
    assert len(preview.fields) == 6
    fields = {field.field_id: field for field in preview.fields}
    assert fields["reading-2:passage_heading"].candidate_text == "PASSAGE 2:"
    assert "The concept of a worm" in fields["reading-2:passage_body"].candidate_text
    assert "in the beginning of the virus era" in fields["q-22:question_stem"].candidate_text
    assert fields["q-23:question_stem"].candidate_text.count(PRINTED_ODDITY) == 1
    assert fields["q-25:question_stem"].source_pdf_page == 5
    assert "most probably" in fields["q-25:question_stem"].candidate_text

    for proposal in reading["proposals"][12:23]:
        field_id = f"{proposal['target_entity_id']}:{proposal['field']}"
        field = fields[field_id]
        assert field.original_text.count(proposal["expected_raw_fragment"]) == 1
        assert proposal["proposed_printed_fragment"] in field.candidate_text
        assert proposal["source_pdf_page"] == field.source_pdf_page

    with pdfplumber.open(SOURCE) as pdf:
        page = pdf.pages[3]
        words = page.extract_words(x_tolerance=2, y_tolerance=2, use_text_flow=False)

        # 11 is printed 'a' immediately before worm, not a token to delete.
        eleven = next(w for w in words if w["text"] == "11" and 330 < w["top"] < 350)
        worm = next(w for w in words if w["text"] == "worm," and 330 < w["top"] < 350)
        assert eleven["x1"] < worm["x0"]
        assert abs(eleven["bottom"] - worm["bottom"]) < 3

        # Plain text moves 'or' before Q22, but geometrically it is printed
        # immediately after 'beginning' and before the damaged 'lhe'.
        displaced = next(w for w in words if w["text"] == "or" and 535 < w["top"] < 555)
        beginning = next(w for w in words if w["text"] == "beginning" and 535 < w["top"] < 555)
        article = next(
            w for w in words if w["text"] == "lhe" and 535 < w["top"] < 555 and w["x0"] > 295
        )
        assert beginning["x1"] < displaced["x0"] < displaced["x1"] < article["x0"]
        assert abs(displaced["bottom"] - beginning["bottom"]) < 3
        assert abs(displaced["bottom"] - article["bottom"]) < 3
        plain_text = page.extract_text(x_tolerance=2, y_tolerance=2)
        assert "11\nnot require" in plain_text
        assert "or\n22-" in plain_text

    assert passage.heading.raw_text == original_heading
    assert passage.body.raw_text == original_body
    assert passage.body.corrected_text is None
    assert json.dumps(ledger, sort_keys=True) == original_ledger
    assert len(ledger["decisions"]) == 19
    assert ledger["publication_status"] == "BLOCKED"
    assert ledger["independently_verified"] is False
    assert not any(d["task_id"].startswith("edit:reading:") for d in ledger["decisions"])
    assert sha256(SOURCE.read_bytes()).hexdigest() == EXPECTED_SHA
