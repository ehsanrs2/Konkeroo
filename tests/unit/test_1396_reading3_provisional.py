"""Synthetic, real-importer-shaped tests for 1396 Reading Passage 3 previews."""

import json
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import pytest

from english_exam.domain import BBox, ExtractedText, SourceProvenance
from english_exam.reading3_provisional import (
    EXPECTED_EDIT_IDS,
    EXPECTED_QUESTIONS,
    PRINTED_ODDITIES,
    preview_1396_reading3,
)

REVIEW_DIR = Path(__file__).parents[2] / "dataset" / "review"
RAW_BODY = (
    "pictures. computer graphics / research. training / "
    "rest their performance / computer graphics. where / "
    "graphs. charts / financial, statistical. scientific data / "
    "computer science. 11 is used routinely / "
    "CAD techniques 10 design vehicles and / "
    'a simulated "walk" thorough the rooms'
)
Q30 = "The 11nragrn11h following this passag~ would mosl likely be about -------."


def _field(text, page=5):
    return ExtractedText(
        raw_text=text,
        provenance=(
            SourceProvenance(
                source_filename="96.pdf",
                page_number=page,
                bbox=BBox(80, 100, 150, 115),
                raw_text=text,
                extraction_method="PDFPLUMBER_PDFMINER_TEXT_LAYER",
            ),
        ),
    )


def _stage():
    q26 = SimpleNamespace(
        number=26,
        stem=_field("What docs the passage mainly discuss?"),
        choices=tuple(
            SimpleNamespace(
                position=i,
                text=_field("TI1e rapidly growing field" if i == 4 else "unmodified option"),
            )
            for i in range(1, 5)
        ),
    )
    q30 = SimpleNamespace(
        number=30,
        stem=_field(Q30),
        choices=tuple(
            SimpleNamespace(
                position=i,
                text=_field("fight training" if i == 2 else "unmodified option"),
            )
            for i in range(1, 5)
        ),
    )
    passage = SimpleNamespace(
        id="reading-3",
        body=_field(RAW_BODY),
        questions=(
            q26,
            SimpleNamespace(number=27),
            SimpleNamespace(
                number=28,
                stem=_field("According lo the passages, architects use CAD 10 --------."),
            ),
            SimpleNamespace(number=29),
            q30,
        ),
    )
    return SimpleNamespace(
        exam=SimpleNamespace(
            id="iran-ce-msc-1396",
            year=1396,
            source_document=SimpleNamespace(
                source_filename="96.pdf",
                sha256="69bc3434ae61c05c85bc9fabffd0b2ce13e5b39bc71b1dfd71c16709c9638ba2",
                english_pdf_pages=(2, 3, 4, 5),
            ),
            sections=(SimpleNamespace(id="reading", passages=(passage,)),),
        ),
        validation=SimpleNamespace(status="PASSED", errors=()),
    )


def _package():
    reading = json.loads(
        (REVIEW_DIR / "1396-reading-text-review.json").read_text(encoding="utf-8")
    )
    ledger = json.loads(
        (REVIEW_DIR / "1396-review-ledger.json").read_text(encoding="utf-8")
    )
    return reading, ledger


def test_13_edits_and_two_glyph_candidates_are_provisional_read_only():
    staged = _stage()
    reading, ledger = _package()
    snapshot = deepcopy((staged, reading, ledger))
    result = preview_1396_reading3(staged, reading, ledger)

    assert result.status == result.method == "ASSISTANT_PROVISIONAL", result.errors
    assert not result.errors
    assert result.applied_edit_ids == EXPECTED_EDIT_IDS
    assert len(result.fields) == 6
    assert sum(len(f.applied_edit_ids) for f in result.fields) == 13
    assert tuple(q.number for q in staged.exam.sections[0].passages[0].questions) == (
        26,
        27,
        28,
        29,
        30,
    )
    assert EXPECTED_QUESTIONS == (26, 27, 28, 29, 30)
    assert len(result.technical_candidates) == 2
    assert {c.anomaly_id for c in result.technical_candidates} == {
        "r1396-order-p3-it",
        "r1396-order-p3-to",
    }
    assert all(
        c.status == "GEOMETRY_ALIGNED_ASSISTANT_PROVISIONAL"
        for c in result.technical_candidates
    )
    fields = {f.field_id: f for f in result.fields}
    body = fields["reading-3:passage_body"].candidate_text
    for text in (
        "pictures, computer",
        "research, training",
        "test their performance",
        "computer graphics, where",
        "graphs, charts",
        "financial, statistical,",
        "computer science. It is used routinely",
        "CAD techniques to design vehicles",
        PRINTED_ODDITIES[0],
    ):
        assert text in body
    assert "computer science. 11 is used routinely" not in body
    assert "CAD techniques 10 design" not in body
    assert fields["q-26:question_stem"].candidate_text == (
        "What does the passage mainly discuss?"
    )
    assert fields["q-26:choice_text:4"].candidate_text == "The rapidly growing field"
    assert fields["q-28:question_stem"].candidate_text == (
        "According to the passages, architects use CAD to --------."
    )
    assert fields["q-30:question_stem"].candidate_text == (
        "The paragraph following this passage would most likely be about -------."
    )
    assert fields["q-30:choice_text:2"].candidate_text == "fight training"
    assert fields["q-30:choice_text:2"].applied_edit_ids == ()
    assert result.printed_oddities == PRINTED_ODDITIES
    assert all(f.source_pdf_page == 5 for f in result.fields)
    assert (staged, reading, ledger) == snapshot
    assert ledger["publication_status"] == "BLOCKED"
    assert ledger["independently_verified"] is False
    assert len(ledger["decisions"]) == 19


@pytest.mark.parametrize(
    "mode",
    [
        "wrong_source_hash",
        "invalid_stage",
        "stale_reading_pin",
        "mutated_proposal",
        "wrong_proposal_page",
        "wrong_proposal_field",
        "missing_editorial_anchor",
        "duplicated_editorial_anchor",
        "wrong_pdf_page",
        "already_corrected",
        "reading3_extra_q25",
        "reading3_missing_q26",
        "missing_q30_choice2",
        "technical_it_bad_order",
        "technical_to_bad_order",
        "printed_thorough_changed",
        "printed_fight_changed",
        "premature_anomaly_resolution",
        "release_unblocked",
        "claims_human_verified",
    ],
)
def test_fail_closed_for_bad_source_field_question_or_editorial_evidence(mode):
    staged = _stage()
    reading, ledger = _package()
    passage = staged.exam.sections[0].passages[0]
    qs = {q.number: q for q in passage.questions}

    if mode == "wrong_source_hash":
        staged.exam.source_document.sha256 = "0" * 64
    elif mode == "invalid_stage":
        staged.validation.status = "FAILED"
    elif mode == "stale_reading_pin":
        ledger["artifact_git_blob_sha1"]["reading"] = "0" * 40
    elif mode == "mutated_proposal":
        reading["proposals"][23]["proposed_printed_fragment"] = "guess"
    elif mode == "wrong_proposal_page":
        reading["proposals"][35]["source_pdf_page"] = 4
    elif mode == "wrong_proposal_field":
        reading["proposals"][30]["field"] = "question_stem"
    elif mode == "missing_editorial_anchor":
        passage.body = _field(RAW_BODY.replace("pictures. computer", "missing"))
    elif mode == "duplicated_editorial_anchor":
        passage.body = _field(RAW_BODY + " / pictures. computer")
    elif mode == "wrong_pdf_page":
        qs[28].stem = _field(qs[28].stem.raw_text, page=4)
    elif mode == "already_corrected":
        passage.body = ExtractedText(
            raw_text=RAW_BODY, corrected_text="untrusted", provenance=passage.body.provenance
        )
    elif mode == "reading3_extra_q25":
        passage.questions = (SimpleNamespace(number=25), *passage.questions)
    elif mode == "reading3_missing_q26":
        passage.questions = tuple(q for q in passage.questions if q.number != 26)
    elif mode == "missing_q30_choice2":
        qs[30].choices = tuple(c for c in qs[30].choices if c.position != 2)
    elif mode == "technical_it_bad_order":
        passage.body = _field(RAW_BODY.replace("science. 11 is", "science. is 11"))
    elif mode == "technical_to_bad_order":
        passage.body = _field(RAW_BODY.replace("techniques 10 design", "techniques design 10"))
    elif mode == "printed_thorough_changed":
        passage.body = _field(RAW_BODY.replace("thorough the rooms", "through the rooms"))
    elif mode == "printed_fight_changed":
        qs[30].choices[1].text = _field("flight training")
    elif mode == "premature_anomaly_resolution":
        item = next(a for a in reading["unresolved_anomalies"] if a["id"] == "r1396-order-p3-to")
        item["proposed_replacement"] = "unattested"
    elif mode == "release_unblocked":
        ledger["publication_status"] = "VERIFIED"
    elif mode == "claims_human_verified":
        reading["independently_verified"] = True

    snapshot = deepcopy((staged, reading, ledger))
    report = preview_1396_reading3(staged, reading, ledger)
    assert report.status == "BLOCKED"
    assert report.fields == ()
    assert report.applied_edit_ids == ()
    assert report.technical_candidates == ()
    assert report.errors
    assert (staged, reading, ledger) == snapshot
