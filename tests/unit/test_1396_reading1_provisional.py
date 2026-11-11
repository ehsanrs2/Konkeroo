"""Source-independent tests for assistant-only 1396 Reading-1 previews."""

import json
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import pytest

from english_exam.domain import BBox, ExtractedText, SourceProvenance
from english_exam.reading1_provisional import (
    EXAM_SHA,
    EXPECTED_EDIT_IDS,
    PRINTED_ODDITY,
    Q19_STEM,
    preview_1396_reading1,
)

DIR = Path(__file__).parents[2] / "dataset" / "review"
RAW_BODY = (
    "lo 1983 / IWO technical systems / rhere was / "
    "bit of slippage. which / Tims the fidelity / die disc / "
    "indefinitely.T his / format of the fixture."
)


def _field(text, page=3):
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


def _staged():
    q16 = SimpleNamespace(number=16, stem=_field("WhAt is 11assage?"))
    q17 = SimpleNamespace(
        number=17,
        choices=(SimpleNamespace(position=1, text=_field("nostalgia i11 rhe l990s")),),
    )
    q18 = SimpleNamespace(
        number=18,
        raw_number_marker=_field("IS.-"),
        stem=_field("Which is ~OT mentioned?"),
    )
    q19 = SimpleNamespace(
        number=19,
        stem=_field(Q19_STEM),
        choices=tuple(SimpleNamespace(position=i) for i in range(1, 5)),
    )
    passage = SimpleNamespace(
        id="reading-1",
        body=_field(RAW_BODY),
        questions=(q16, q17, q18, q19),
    )
    section = SimpleNamespace(id="reading", passages=(passage,))
    return SimpleNamespace(
        exam=SimpleNamespace(
            id="iran-ce-msc-1396",
            year=1396,
            source_document=SimpleNamespace(
                source_filename="96.pdf",
                sha256=EXAM_SHA,
                english_pdf_pages=(2, 3, 4, 5),
            ),
            sections=(section,),
        ),
        validation=SimpleNamespace(status="PASSED", errors=()),
    )


def _review_package():
    proposals = json.loads((DIR / "1396-reading-text-review.json").read_text(encoding="utf-8"))
    ledger = json.loads((DIR / "1396-review-ledger.json").read_text(encoding="utf-8"))
    return proposals, ledger


def test_exact_twelve_source_aligned_edits_produce_unpublished_read_only_preview():
    staged = _staged()
    review, ledger = _review_package()
    before = deepcopy((staged, review, ledger))
    report = preview_1396_reading1(staged, review, ledger)

    assert report.status == "ASSISTANT_PROVISIONAL"
    assert report.method == "ASSISTANT_PROVISIONAL"
    assert report.applied_edit_ids == EXPECTED_EDIT_IDS
    assert report.errors == ()
    assert len(report.fields) == 6
    assert sum(len(field.applied_edit_ids) for field in report.fields) == 12
    assert report.q19_order_status == "STAGED_ORDER_ALIGNED_NOT_INDEPENDENTLY_REVIEWED"
    assert report.printed_oddity == PRINTED_ODDITY

    fields = {f.field_id: f for f in report.fields}
    candidate = fields["reading-1:passage_body"].candidate_text
    assert "In 1983" in candidate
    assert "two technical systems" in candidate
    assert "there was" in candidate
    assert "bit of slippage, which" in candidate
    assert "Thus the fidelity" in candidate
    assert "the disc" in candidate
    assert "indefinitely. This" in candidate
    assert PRINTED_ODDITY in candidate
    assert "format of the future" not in candidate
    assert fields["q-16:question_stem"].candidate_text == "What is passage?"
    assert fields["q-17:choice_text:1"].candidate_text == "nostalgia in the 1990s"
    assert fields["q-18:number_marker"].candidate_text == "18-"
    assert fields["q-18:question_stem"].candidate_text == "Which is NOT mentioned?"
    assert fields["q-19:question_stem"].candidate_text == Q19_STEM
    assert fields["q-19:question_stem"].applied_edit_ids == ()
    assert (staged, review, ledger) == before
    assert ledger["publication_status"] == "BLOCKED"
    assert len(ledger["decisions"]) == 19


@pytest.mark.parametrize(
    "mode",
    [
        "wrong_source",
        "unvalidated_stage",
        "stale_review_blob",
        "changed_proposal",
        "wrong_proposal_page",
        "wrong_target_field",
        "missing_anchor",
        "duplicate_anchor",
        "wrong_provenance",
        "already_corrected",
        "q19_misordered",
        "printed_fixture_removed",
        "premature_publication",
        "claimed_independent_review",
    ],
)
def test_fail_closed_no_misapplied_edits_or_invented_human_decisions(mode):
    staged = _staged()
    review, ledger = _review_package()
    body = staged.exam.sections[0].passages[0].body
    fields = staged.exam.sections[0].passages[0].questions
    if mode == "wrong_source":
        staged.exam.source_document.sha256 = "0" * 64
    elif mode == "unvalidated_stage":
        staged.validation.status = "FAILED"
    elif mode == "stale_review_blob":
        ledger["artifact_git_blob_sha1"]["reading"] = "0" * 40
    elif mode == "changed_proposal":
        review["proposals"][0]["proposed_printed_fragment"] = "untrusted"
    elif mode == "wrong_proposal_page":
        review["proposals"][0]["source_pdf_page"] = 5
    elif mode == "wrong_target_field":
        review["proposals"][0]["field"] = "choice_text:4"
    elif mode == "missing_anchor":
        staged.exam.sections[0].passages[0].body = _field(
            body.raw_text.replace("lo 1983", "unknown")
        )
    elif mode == "duplicate_anchor":
        staged.exam.sections[0].passages[0].body = _field(body.raw_text + " / lo 1983")
    elif mode == "wrong_provenance":
        staged.exam.sections[0].passages[0].body = _field(body.raw_text, page=4)
    elif mode == "already_corrected":
        staged.exam.sections[0].passages[0].body = ExtractedText(
            raw_text=body.raw_text, corrected_text="incorrect", provenance=body.provenance
        )
    elif mode == "q19_misordered":
        fields[3].stem = _field("as------. The tone of the passage could best be described")
    elif mode == "printed_fixture_removed":
        staged.exam.sections[0].passages[0].body = _field(
            body.raw_text.replace(PRINTED_ODDITY, "format of the future")
        )
    elif mode == "premature_publication":
        ledger["publication_status"] = "VERIFIED"
    elif mode == "claimed_independent_review":
        review["independently_verified"] = True

    original = deepcopy((staged, review, ledger))
    report = preview_1396_reading1(staged, review, ledger)
    assert report.status == "BLOCKED"
    assert report.fields == ()
    assert report.applied_edit_ids == ()
    assert report.errors
    assert (staged, review, ledger) == original
