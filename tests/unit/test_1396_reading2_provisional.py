"""Synthetic source-independent guards for provisional 1396 Reading Passage 2."""

import json
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import pytest

from english_exam.domain import BBox, ExtractedText, SourceProvenance
from english_exam.reading2_provisional import (
    EXPECTED_EDIT_IDS,
    PRINTED_ODDITY,
    preview_1396_reading2,
)

DIR = Path(__file__).parents[2] / "dataset" / "review"
BODY = (
    "present This applies. whenever a. disk / limes, has / "
    "TI1e concept of 11 worm, i.e. a self-contnine<l, self-propagating / "
    "In 1988, however. the Internet Worm / "
    "vulnerabilities ill operating systems."
)
Q22 = "According to lhe passage, in the beginning or lhe virus era -------."
Q23 = 'The work "self-contained" in Paragraph 2 could best be replaced by------.'


def _field(text, page=4):
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
    # Mirror the real 1396 importer: Q20 is in Reading 1, not Reading 2.
    questions = (
        SimpleNamespace(
            number=21,
            choices=(SimpleNamespace(position=4, text=_field("TI1e spread of viruses")),),
        ),
        SimpleNamespace(number=22, stem=_field(Q22)),
        SimpleNamespace(
            number=23,
            stem=_field(Q23),
            choices=tuple(SimpleNamespace(position=i) for i in range(1, 5)),
        ),
        SimpleNamespace(number=24),
        SimpleNamespace(number=25, stem=_field("The author mosl probably agrees.", page=5)),
    )
    reading = SimpleNamespace(
        id="reading",
        passages=(
            SimpleNamespace(
                id="reading-2",
                heading=_field("PASSAGB2:"),
                body=_field(BODY),
                questions=questions,
            ),
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
            sections=(reading,),
        ),
        validation=SimpleNamespace(status="PASSED", errors=()),
    )


def _package():
    reading = json.loads((DIR / "1396-reading-text-review.json").read_text(encoding="utf-8"))
    ledger = json.loads((DIR / "1396-review-ledger.json").read_text(encoding="utf-8"))
    return reading, ledger


def test_11_edits_two_technical_glyph_candidates_and_printed_oddity_preserved():
    stage = _stage()
    review, ledger = _package()
    snapshot = deepcopy((stage, review, ledger))
    result = preview_1396_reading2(stage, review, ledger)

    assert result.status == "ASSISTANT_PROVISIONAL"
    assert result.method == "ASSISTANT_PROVISIONAL"
    assert result.applied_edit_ids == EXPECTED_EDIT_IDS
    assert result.errors == ()
    assert tuple(q.number for q in stage.exam.sections[0].passages[0].questions) == (
        21, 22, 23, 24, 25
    )
    assert len(result.fields) == 6
    assert len(result.technical_candidates) == 2
    assert {candidate.anomaly_id for candidate in result.technical_candidates} == {
        "r1396-order-p2-stray",
        "r1396-order-q22",
    }
    assert all(
        candidate.status == "GEOMETRY_ALIGNED_ASSISTANT_PROVISIONAL"
        for candidate in result.technical_candidates
    )
    fields = {field.field_id: field for field in result.fields}
    assert fields["reading-2:passage_heading"].candidate_text == "PASSAGE 2:"
    body = fields["reading-2:passage_body"].candidate_text
    for text in (
        "present. This applies,",
        "whenever a disk",
        "times, has",
        "The concept of a worm",
        "self-contained",
        "1988, however,",
        "vulnerabilities in operating",
    ):
        assert text in body
    assert "concept of 11 worm" not in body
    assert fields["q-21:choice_text:4"].candidate_text == "The spread of viruses"
    assert fields["q-22:question_stem"].candidate_text == (
        "According to the passage, in the beginning of the virus era -------."
    )
    assert fields["q-23:question_stem"].candidate_text == Q23
    assert fields["q-25:question_stem"].candidate_text == "The author most probably agrees."
    assert fields["q-25:question_stem"].source_pdf_page == 5
    assert result.printed_oddity == PRINTED_ODDITY
    assert (stage, review, ledger) == snapshot
    assert ledger["publication_status"] == "BLOCKED"
    assert ledger["independently_verified"] is False
    assert len(ledger["decisions"]) == 19


@pytest.mark.parametrize(
    "mode",
    [
        "wrong_sha",
        "invalid_stage",
        "changed_revision_pin",
        "changed_review",
        "wrong_proposal_page",
        "wrong_proposal_target",
        "missing_short_anchor",
        "duplicate_short_anchor",
        "wrong_pdf_page_5",
        "reading2_includes_q20",
        "reading2_missing_q21",
        "precorrected",
        "missing_11_anchor",
        "wrong_q22_glyph_order",
        "changed_printed_work",
        "resolved_original_anomaly",
        "released_ledger",
    ],
)
def test_fail_closed_for_bad_source_provenance_and_unjustified_repairs(mode):
    stage = _stage()
    review, ledger = _package()
    passage = stage.exam.sections[0].passages[0]
    qs = {q.number: q for q in passage.questions}
    if mode == "wrong_sha":
        stage.exam.source_document.sha256 = "0" * 64
    elif mode == "invalid_stage":
        stage.validation.status = "FAILED"
    elif mode == "changed_revision_pin":
        ledger["artifact_git_blob_sha1"]["reading"] = "0" * 40
    elif mode == "changed_review":
        review["proposals"][12]["proposed_printed_fragment"] = "guess"
    elif mode == "wrong_proposal_page":
        review["proposals"][22]["source_pdf_page"] = 4
    elif mode == "wrong_proposal_target":
        review["proposals"][13]["field"] = "question_stem"
    elif mode == "missing_short_anchor":
        passage.body = _field(BODY.replace("limes, has", "unknown, has"))
    elif mode == "duplicate_short_anchor":
        passage.body = _field(BODY + " whenever a. disk")
    elif mode == "wrong_pdf_page_5":
        qs[25].stem = _field(qs[25].stem.raw_text, page=4)
    elif mode == "reading2_includes_q20":
        passage.questions = (SimpleNamespace(number=20), *passage.questions)
    elif mode == "reading2_missing_q21":
        passage.questions = tuple(q for q in passage.questions if q.number != 21)
    elif mode == "precorrected":
        passage.body = ExtractedText(
            raw_text=BODY, corrected_text="untrusted", provenance=passage.body.provenance
        )
    elif mode == "missing_11_anchor":
        passage.body = _field(BODY.replace("concept of 11 worm", "concept of a worm"))
    elif mode == "wrong_q22_glyph_order":
        qs[22].stem = _field(Q22.replace("beginning or lhe", "beginning the or"))
    elif mode == "changed_printed_work":
        qs[23].stem = _field(Q23.replace("The work", "The word"))
    elif mode == "resolved_original_anomaly":
        row = next(a for a in review["unresolved_anomalies"] if a["id"] == "r1396-order-q22")
        row["proposed_replacement"] = "wrong premature promotion"
    elif mode == "released_ledger":
        ledger["publication_status"] = "VERIFIED"

    snapshot = deepcopy((stage, review, ledger))
    result = preview_1396_reading2(stage, review, ledger)
    assert result.status == "BLOCKED"
    assert result.fields == ()
    assert result.applied_edit_ids == ()
    assert result.technical_candidates == ()
    assert result.errors
    assert (stage, review, ledger) == snapshot
