"""1396 original-PDF gated Reading Passage-1 assistant-only preview checks.

Skipped in public CI without the copyright-sensitive source/ LFS payload.
No source, human ledger, or verified answers are written.
"""

import json
from hashlib import sha256
from pathlib import Path

import pdfplumber
import pytest

from english_exam.pipeline import extract_staged_1396
from english_exam.reading1_provisional import (
    EXAM_SHA,
    EXPECTED_EDIT_IDS,
    PRINTED_ODDITY,
    Q19_STEM,
    preview_1396_reading1,
)

ROOT = Path(__file__).parents[2]
SOURCE = ROOT / "source" / "96.pdf"
pytestmark = pytest.mark.source_pdf


def test_original_1396_pdf_passage_1_provisional_edit_and_q19_geometry():
    if not SOURCE.is_file():
        pytest.skip("original source/96.pdf missing from source-independent CI")
    assert sha256(SOURCE.read_bytes()).hexdigest() == EXAM_SHA

    reading = json.loads(
        (ROOT / "dataset/review/1396-reading-text-review.json").read_text(encoding="utf-8")
    )
    ledger = json.loads(
        (ROOT / "dataset/review/1396-review-ledger.json").read_text(encoding="utf-8")
    )
    staged = extract_staged_1396(SOURCE)
    assert staged.validation.status == "PASSED"
    original_ledger = json.dumps(ledger, sort_keys=True)
    passage = staged.exam.sections[2].passages[0]
    original_body = passage.body.raw_text

    report = preview_1396_reading1(staged, reading, ledger)
    assert report.status == "ASSISTANT_PROVISIONAL"
    assert report.errors == ()
    assert report.applied_edit_ids == EXPECTED_EDIT_IDS
    assert report.q19_order_status == "STAGED_ORDER_ALIGNED_NOT_INDEPENDENTLY_REVIEWED"
    fields = {field.field_id: field for field in report.fields}
    assert len(fields) == 6

    for p in reading["proposals"][:12]:
        key = f"{p['target_entity_id']}:{p['field']}"
        field = fields[key]
        assert p["expected_raw_fragment"] in field.original_text
        assert p["proposed_printed_fragment"] in field.candidate_text
        assert field.source_pdf_page == 3
    body = fields["reading-1:passage_body"]
    assert body.candidate_text.count(PRINTED_ODDITY) == 1
    assert body.candidate_text.count("format of the future") == 0
    assert passage.body.raw_text == original_body
    assert passage.body.corrected_text is None
    q19 = fields["q-19:question_stem"]
    assert q19.original_text == Q19_STEM == q19.candidate_text
    assert not q19.applied_edit_ids

    with pdfplumber.open(SOURCE) as pdf:
        page = pdf.pages[2]
        words = page.extract_words(x_tolerance=2, y_tolerance=2, use_text_flow=False)
        phrase = next(w for w in words if w["text"] == "described")
        ending = next(w for w in words if w["text"] == "as------.")
        assert phrase["x1"] < ending["x0"]
        assert abs(phrase["bottom"] - ending["bottom"]) < 3
        # Plain reading-order extraction can still move the ending fragment.
        plain = page.extract_text(x_tolerance=2, y_tolerance=2)
        assert "as------.\n19-" in plain

    assert json.dumps(ledger, sort_keys=True) == original_ledger
    assert len(ledger["decisions"]) == 19
    assert ledger["publication_status"] == "BLOCKED"
    assert ledger["independently_verified"] is False
    assert not any(d["task_id"].startswith("edit:reading:") for d in ledger["decisions"])
    assert sha256(SOURCE.read_bytes()).hexdigest() == EXAM_SHA
