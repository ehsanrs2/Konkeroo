"""Source-independent mutation tests for curated editorial correction previews."""

import json
from copy import deepcopy
from dataclasses import replace
from pathlib import Path

import pytest

from english_exam.domain import (
    BBox,
    Choice,
    DatasetState,
    Exam,
    ExtractedText,
    GeneratorInfo,
    Question,
    QuestionKind,
    Section,
    SectionKind,
    SourceDocument,
    SourceProvenance,
    StagedDataset,
    ValidationReport,
)
from english_exam.review_corrections import preview_editorial_corrections

ROOT = Path(__file__).parents[2]
ARTIFACT = ROOT / "dataset" / "review" / "1396-vocabulary-correction-proposals.json"


def _text(raw: str) -> ExtractedText:
    return ExtractedText(
        raw_text=raw,
        provenance=(
            SourceProvenance(
                source_filename="fictional.pdf",
                page_number=2,
                bbox=BBox(10, 10, 50, 20),
                raw_text=raw,
                extraction_method="PDFPLUMBER_PDFMINER_TEXT_LAYER",
            ),
        ),
    )


def _exam() -> StagedDataset:
    questions = (
        Question(
            id="q-01",
            number=1,
            raw_number_marker=_text("I·"),
            kind=QuestionKind.SENTENCE_COMPLETION,
            stem=_text("You mighl read the book."),
            blank=None,
            choices=tuple(
                Choice(position=n, raw_marker=_text(f"{n})"), text=_text("fictional"))
                for n in range(1, 5)
            ),
        ),
        Question(
            id="q-02",
            number=2,
            raw_number_marker=_text("2-"),
            kind=QuestionKind.SENTENCE_COMPLETION,
            stem=_text("Another fictional question."),
            blank=None,
            choices=tuple(
                Choice(
                    position=n,
                    raw_marker=_text("!)" if n == 1 else f"{n})"),
                    text=_text("fictional"),
                )
                for n in range(1, 5)
            ),
        ),
    )
    return StagedDataset(
        schema_version="1.0",
        generator=GeneratorInfo("synthetic", "0.1", "fixture", "0", "0"),
        exam=Exam(
            id="fictional-exam-1499",
            year=1499,
            state=DatasetState.STAGED,
            source_document=SourceDocument(
                source_filename="fictional.pdf",
                sha256="a" * 64,
                page_count=4,
                page_width=612,
                page_height=792,
                english_pdf_pages=(2,),
            ),
            sections=(
                Section(
                    id="vocabulary",
                    kind=SectionKind.VOCABULARY,
                    heading=_text("Vocabulary"),
                    directions=_text("Choose"),
                    questions=questions,
                ),
            ),
        ),
        validation=ValidationReport("synthetic", "PASSED", (), ()),
    )


def _review():
    return {
        "schema_version": "1.0",
        "artifact_type": "EDITORIAL_CORRECTION_PROPOSALS",
        "exam_id": "fictional-exam-1499",
        "exam_source": {"filename": "fictional.pdf", "sha256": "a" * 64},
        "review_state": "AWAITING_INDEPENDENT_REVIEW",
        "review_method": "ASSISTANT_DIRECT_VISUAL_COMPARISON",
        "scope": {"section": "VOCABULARY", "question_numbers": [1, 2], "source_pdf_pages": [2]},
        "proposals": [
            {
                "id": "synthetic-q01-might",
                "question_id": "q-01",
                "field": "stem",
                "expected_raw_fragment": "mighl",
                "proposed_replacement": "might",
                "source_pdf_page": 2,
                "reason": "VISUALLY_OBSERVED",
            },
            {
                "id": "synthetic-q01-marker",
                "question_id": "q-01",
                "field": "number_marker",
                "expected_raw_fragment": "I·",
                "proposed_replacement": "1-",
                "source_pdf_page": 2,
                "reason": "VISUALLY_OBSERVED",
            },
            {
                "id": "synthetic-q02-choice",
                "question_id": "q-02",
                "field": "choice_marker:1",
                "expected_raw_fragment": "!)",
                "proposed_replacement": "1)",
                "source_pdf_page": 2,
                "reason": "VISUALLY_OBSERVED",
            },
        ],
    }


def test_immutable_preview_does_not_edit_staged_data():
    exam = _exam()
    review = _review()
    before_exam, before_review = deepcopy(exam), deepcopy(review)
    result = preview_editorial_corrections(exam, review)
    assert result.status == "AWAITING_INDEPENDENT_REVIEW"
    assert not result.errors
    assert len(result.previews) == 3
    assert {
        p.field: p.suggested_corrected_text
        for p in result.previews
        if p.question_id == "q-01"
    } == {
        "stem": "You might read the book.",
        "number_marker": "1-",
    }
    assert exam == before_exam and review == before_review
    assert exam.exam.sections[0].questions[0].stem.corrected_text is None


@pytest.mark.parametrize(
    "mutate",
    [
        lambda x: x["exam_source"].update(sha256="b" * 64),
        lambda x: x.update(review_state="VERIFIED"),
        lambda x: x["proposals"].append(deepcopy(x["proposals"][0])),
        lambda x: x["proposals"][0].update(expected_raw_fragment="migt"),
        lambda x: x["proposals"][0].update(question_id="q-99"),
        lambda x: x["proposals"][0].update(field="choice_marker:99"),
        lambda x: x["proposals"][0].update(source_pdf_page=3),
        lambda x: x["proposals"][0].update(proposed_replacement="mighl"),
        lambda x: x["proposals"][0].update(reason=""),
        lambda x: x["proposals"][0].update(extra_field=True),
        lambda x: x["proposals"].append(
            {**x["proposals"][0], "id": "overlapping", "expected_raw_fragment": "igh"}
        ),
    ],
)
def test_any_invalid_or_ambiguous_edit_blocks_entire_preview(mutate):
    proposal = _review()
    mutate(proposal)
    report = preview_editorial_corrections(_exam(), proposal)
    assert report.status == "BLOCKED"
    assert not report.previews
    assert report.errors


def test_previously_corrected_text_cannot_be_silently_recorrected():
    exam = _exam()
    section = exam.exam.sections[0]
    question = section.questions[0]
    modified = replace(question, stem=replace(question.stem, corrected_text="prior review"))
    changed_section = replace(section, questions=(modified, section.questions[1]))
    changed = replace(exam, exam=replace(exam.exam, sections=(changed_section,)))
    report = preview_editorial_corrections(changed, _review())
    assert report.status == "BLOCKED"
    assert report.previews == ()


def test_review_fixture_stays_compact_and_pending():
    data = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    assert data["exam_id"] == "iran-ce-msc-1396"
    assert data["exam_source"]["sha256"] == (
        "69bc3434ae61c05c85bc9fabffd0b2ce13e5b39bc71b1dfd71c16709c9638ba2"
    )
    assert data["review_state"] == "AWAITING_INDEPENDENT_REVIEW"
    assert data["scope"]["question_numbers"] == list(range(1, 11))
    assert len(data["proposals"]) == 11
    assert len({p["id"] for p in data["proposals"]}) == 11
    assert all(p["source_pdf_page"] == 2 for p in data["proposals"])
    assert all(len(p["expected_raw_fragment"]) < 30 for p in data["proposals"])
