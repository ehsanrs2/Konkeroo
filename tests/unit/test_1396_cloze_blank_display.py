"""No-source and fail-closed tests for presentation-only 1396 Cloze blanks."""

from dataclasses import replace

import pytest

from english_exam.cloze_blank_display import format_1396_cloze_blanks_for_review
from english_exam.cloze_full_preview import FullClozePreview

CANDIDATE = (
    "children, (11) -·-··-··a book.\n"
    "humans since (12) ······---: Plato.\n"
    "wax tablet at birth ( 13) -·-·-· on the impression of events.\n"
    "hundred years, though, (14) ···-···-·systematic techniques.\n"
    "laboratory tests of our ability\n"
    "to remember verbal and visual materials ( 15) -····-·· more recent brain-imaging\n"
    "approaches."
)
EXPECTED = (
    "children, (11) ____ a book.\n"
    "humans since (12) ____: Plato.\n"
    "wax tablet at birth (13) ____ on the impression of events.\n"
    "hundred years, though, (14) ____ systematic techniques.\n"
    "laboratory tests of our ability\n"
    "to remember verbal and visual materials (15) ____ more recent brain-imaging\n"
    "approaches."
)


def _preview(text=CANDIDATE):
    return FullClozePreview(
        status="PENDING_FULL_FIELD_HUMAN_REVIEW",
        proposed_full_text=text,
        accepted_passage_edit_ids=(
            "edit:cloze:cloze-human",
            "edit:cloze:cloze-on",
            "edit:cloze:cloze-to-study",
            "edit:cloze:cloze-14-marker",
        ),
        technical_candidate_anomaly_id="cloze-ability-to-remember-displaced-token",
        unresolved_anomaly=True,
        errors=(),
    )


def test_renders_five_numbered_blanks_without_changing_source_preview():
    preview = _preview()
    result = format_1396_cloze_blanks_for_review(preview)
    assert result.status == "PENDING_BLANK_DISPLAY_REVIEW"
    assert result.errors == ()
    assert result.blank_numbers == (11, 12, 13, 14, 15)
    assert result.text == EXPECTED
    assert result.text.count("____") == 5
    assert "(12) ____: Plato" in result.text  # Keep existing colon.
    assert "(11) ____ a book" in result.text  # Insert missing display separator.
    assert "(14) ____ systematic" in result.text
    assert preview.proposed_full_text == CANDIDATE  # No semantic content mutation.


@pytest.mark.parametrize(
    "changed",
    [
        CANDIDATE.replace("(11) -·-··-··", "(11) "),
        CANDIDATE.replace("( 13) -·-·-·", "( 12) -·-·-·"),
        CANDIDATE.replace("(14) ···-···-·", "(14) ···-···-· (14) ···-···-·"),
        CANDIDATE.replace("children, ", "other context, "),
        CANDIDATE.replace(": Plato", "; Plato"),
        CANDIDATE.replace("( 15) -····-··", "( 15) _____"),
        CANDIDATE.replace("more recent", "different words"),
    ],
)
def test_fails_closed_for_missing_duplicated_or_changed_source_context(changed):
    preview = _preview(changed)
    result = format_1396_cloze_blanks_for_review(preview)
    assert result.status == "BLOCKED"
    assert result.errors
    assert result.text is None
    assert preview.proposed_full_text == changed


@pytest.mark.parametrize(
    "change",
    [
        {"status": "BLOCKED"},
        {"status": "PUBLISHED"},
        {"unresolved_anomaly": False},
        {"errors": ("bad source",)},
        {"proposed_full_text": None},
    ],
)
def test_blocks_invalid_preview_and_never_claims_review_or_release(change):
    preview = replace(_preview(), **change)
    result = format_1396_cloze_blanks_for_review(preview)
    assert result.status == "BLOCKED"
    assert result.text is None
    assert result.errors
