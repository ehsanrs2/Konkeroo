"""Source-independent tests for the 1396 Cloze word-order preview."""

from copy import deepcopy
from types import SimpleNamespace

import pytest

from english_exam.cloze_order_review import (
    EXAM_SHA,
    RAW_ANCHOR,
    SUGGESTED_ANCHOR,
    preview_1396_cloze_to_remember,
)

RAW_PASSAGE = "These range from " + RAW_ANCHOR + " ( 15) more recent brain-imaging\napproaches."


def _staged(text=RAW_PASSAGE):
    body = SimpleNamespace(
        raw_text=text,
        corrected_text=None,
        normalized_text=None,
        provenance=(SimpleNamespace(page_number=2, source_filename="96.pdf"),),
    )
    passage = SimpleNamespace(id="cloze-1", body=body)
    section = SimpleNamespace(id="cloze", passages=(passage,))
    exam = SimpleNamespace(
        id="iran-ce-msc-1396",
        source_document=SimpleNamespace(
            source_filename="96.pdf", sha256=EXAM_SHA, english_pdf_pages=(2, 3, 4, 5)
        ),
        sections=(section,),
    )
    staged = SimpleNamespace(
        exam=exam,
        validation=SimpleNamespace(status="PASSED", errors=()),
    )
    return staged


def test_preview_only_changes_one_source_anchored_token_without_mutation():
    staged = _staged()
    unchanged = deepcopy(staged)
    report = preview_1396_cloze_to_remember(staged)
    assert report.status == "PROPOSED_PENDING_TECHNICAL_REVIEW"
    assert report.anomaly_id == "cloze-ability-to-remember-displaced-token"
    assert report.source_pdf_page == 2
    assert report.original_fragment == RAW_ANCHOR
    assert report.proposed_fragment == SUGGESTED_ANCHOR
    assert report.proposed_full_text == RAW_PASSAGE.replace(RAW_ANCHOR, SUGGESTED_ANCHOR)
    assert report.proposed_full_text.count("to remember") == 1
    assert "10 remember" not in report.proposed_full_text
    assert report.proposed_full_text.count("approaches.") == 1
    assert report.errors == ()
    assert staged == unchanged
    assert staged.exam.sections[0].passages[0].body.corrected_text is None


@pytest.mark.parametrize(
    ("text", "changed_attribute", "value"),
    [
        (RAW_PASSAGE.replace("10 remember", "to remember"), None, None),
        (RAW_PASSAGE.replace("10 remember", "remember"), None, None),
        (RAW_PASSAGE.replace("10 remember", "10\nremember"), None, None),
        (RAW_PASSAGE + "\n" + RAW_ANCHOR, None, None),
        (RAW_PASSAGE.replace("approaches.", "ending."), None, None),
        (RAW_PASSAGE, "source_sha", "0" * 64),
        (RAW_PASSAGE, "source_name", "different.pdf"),
        (RAW_PASSAGE, "validation", "FAILED"),
        (RAW_PASSAGE, "transformed", "already corrected"),
        (RAW_PASSAGE, "provenance_page", 3),
    ],
)
def test_preview_blocks_ambiguous_or_untrusted_inputs(text, changed_attribute, value):
    staged = _staged(text)
    if changed_attribute == "source_sha":
        staged.exam.source_document.sha256 = value
    elif changed_attribute == "source_name":
        staged.exam.source_document.source_filename = value
    elif changed_attribute == "validation":
        staged.validation.status = value
    elif changed_attribute == "transformed":
        staged.exam.sections[0].passages[0].body.corrected_text = value
    elif changed_attribute == "provenance_page":
        staged.exam.sections[0].passages[0].body.provenance = (
            SimpleNamespace(page_number=value, source_filename="96.pdf"),
        )
    before = deepcopy(staged)
    report = preview_1396_cloze_to_remember(staged)
    assert report.status == "BLOCKED"
    assert report.errors
    assert report.proposed_full_text is None
    assert staged == before
