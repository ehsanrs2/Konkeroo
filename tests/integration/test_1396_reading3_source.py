"""Original-PDF-conditional 1396 Reading Passage 3 preview and geometry test.

Public GitHub CI lacks original source/96.pdf LFS media and must skip honestly.
"""

import json
from hashlib import sha256
from pathlib import Path

import pdfplumber
import pytest

from english_exam.pipeline import extract_staged_1396
from english_exam.reading3_provisional import (
    EXPECTED_EDIT_IDS,
    EXPECTED_QUESTIONS,
    PRINTED_ODDITIES,
    TECHNICAL_ANCHORS,
    preview_1396_reading3,
)

ROOT = Path(__file__).parents[2]
SOURCE = ROOT / "source" / "96.pdf"
EXPECTED_SHA = "69bc3434ae61c05c85bc9fabffd0b2ce13e5b39bc71b1dfd71c16709c9638ba2"
pytestmark = pytest.mark.source_pdf


def test_real_source_1396_reading3_edits_and_glyph_baselines():
    if not SOURCE.is_file():
        pytest.skip("source/96.pdf original LFS source unavailable; PDF test NOT executed")
    assert sha256(SOURCE.read_bytes()).hexdigest() == EXPECTED_SHA

    reading = json.loads(
        (ROOT / "dataset/review/1396-reading-text-review.json").read_text(encoding="utf-8")
    )
    ledger = json.loads(
        (ROOT / "dataset/review/1396-review-ledger.json").read_text(encoding="utf-8")
    )
    original_ledger = json.dumps(ledger, sort_keys=True)
    stage = extract_staged_1396(SOURCE)
    assert stage.validation.status == "PASSED"
    section = next(s for s in stage.exam.sections if s.id == "reading")
    passage = next(p for p in section.passages if p.id == "reading-3")
    assert tuple(q.number for q in passage.questions) == EXPECTED_QUESTIONS
    assert 25 in tuple(
        q.number for p in section.passages if p.id == "reading-2" for q in p.questions
    )
    raw_body = passage.body.raw_text
    original_stems = {
        q.number: q.stem.raw_text for q in passage.questions if q.number in (26, 28, 30)
    }

    result = preview_1396_reading3(stage, reading, ledger)
    assert result.status == "ASSISTANT_PROVISIONAL", result.errors
    assert result.errors == ()
    assert result.method == "ASSISTANT_PROVISIONAL"
    assert result.applied_edit_ids == EXPECTED_EDIT_IDS
    assert len(result.fields) == 6
    assert len(result.technical_candidates) == 2
    fields = {f.field_id: f for f in result.fields}

    for proposal in reading["proposals"][23:36]:
        field_id = f"{proposal['target_entity_id']}:{proposal['field']}"
        field = fields[field_id]
        assert field.source_pdf_page == proposal["source_pdf_page"] == 5
        assert field.original_text.count(proposal["expected_raw_fragment"]) == 1
        assert proposal["proposed_printed_fragment"] in field.candidate_text
    for anomaly_id, field_id, before, after in TECHNICAL_ANCHORS:
        assert fields[field_id].original_text.count(before) == 1, anomaly_id
        assert fields[field_id].candidate_text.count(after) == 1, anomaly_id

    body = fields["reading-3:passage_body"]
    assert body.candidate_text.count(PRINTED_ODDITIES[0]) == 1
    assert fields["q-30:choice_text:2"].candidate_text == (
        fields["q-30:choice_text:2"].original_text
    )
    assert fields["q-30:choice_text:2"].candidate_text.count(PRINTED_ODDITIES[1]) == 1

    with pdfplumber.open(SOURCE) as pdf:
        words = pdf.pages[4].extract_words(
            x_tolerance=2, y_tolerance=2, use_text_flow=False
        )
        # The text-layer '11' corresponds to the printed 'It' and is already
        # horizontally between 'science.' and 'is' on the same baseline.
        eleven = next(w for w in words if w["text"] == "11" and 220 < w["top"] < 243)
        science = next(w for w in words if w["text"] == "science." and 225 < w["top"] < 242)
        following_is = next(w for w in words if w["text"] == "is" and 225 < w["top"] < 242)
        assert science["x1"] < eleven["x0"] < eleven["x1"] < following_is["x0"]
        assert abs(eleven["bottom"] - science["bottom"]) < 3
        assert abs(eleven["bottom"] - following_is["bottom"]) < 3

        # The passage '10' is the printed 'to' between 'techniques' and
        # 'design'. Q28 has a different '10' and is a separate editorial edit.
        ten = next(w for w in words if w["text"] == "10" and 320 < w["top"] < 340)
        techniques = next(
            w for w in words if w["text"] == "techniques" and 320 < w["top"] < 340
        )
        design = next(w for w in words if w["text"] == "design" and 320 < w["top"] < 340)
        assert techniques["x1"] < ten["x0"] < ten["x1"] < design["x0"]
        assert abs(ten["bottom"] - techniques["bottom"]) < 3
        assert abs(ten["bottom"] - design["bottom"]) < 3

    assert passage.body.raw_text == raw_body
    assert passage.body.corrected_text is None
    assert {
        q.number: q.stem.raw_text for q in passage.questions if q.number in (26, 28, 30)
    } == original_stems
    assert json.dumps(ledger, sort_keys=True) == original_ledger
    assert len(ledger["decisions"]) == 19
    assert ledger["publication_status"] == "BLOCKED"
    assert ledger["independently_verified"] is False
    assert not any(d["task_id"].startswith("edit:reading:") for d in ledger["decisions"])
    assert sha256(SOURCE.read_bytes()).hexdigest() == EXPECTED_SHA
