"""Source-independent tests for provisional source-claim alignment."""

from copy import deepcopy
from dataclasses import replace

import pytest

from english_exam.domain import (
    AnswerRecord,
    AnswerStatus,
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
from english_exam.review_reconciliation import ExpectedKeyIdentity, align_curated_official_claims


KEY = ExpectedKeyIdentity(
    filename="synthetic-key.pdf",
    sha256="b" * 64,
    booklet_code="C",
    edition="INITIAL",
    page_number=1,
    table_group=1,
)


def _text(value: str, page: int = 2) -> ExtractedText:
    return ExtractedText(
        raw_text=value,
        provenance=(
            SourceProvenance(
                source_filename="synthetic-exam.pdf",
                page_number=page,
                bbox=BBox(10.0, 20.0, 30.0, 40.0),
                raw_text=value,
                extraction_method="PDFPLUMBER_PDFMINER_TEXT_LAYER",
            ),
        ),
    )


def _question(number: int) -> Question:
    return Question(
        id=f"q-{number:02d}",
        number=number,
        raw_number_marker=_text(str(number)),
        kind=QuestionKind.SENTENCE_COMPLETION,
        stem=_text("Fictional question"),
        blank=None,
        choices=tuple(
            Choice(position=position, raw_marker=_text(f"{position})"), text=_text("fictional"))
            for position in (1, 2, 3, 4)
        ),
    )


def _staged() -> StagedDataset:
    exam = Exam(
        id="iran-ce-msc-1499",
        year=1499,
        state=DatasetState.STAGED,
        source_document=SourceDocument(
            source_filename="synthetic-exam.pdf",
            sha256="a" * 64,
            page_count=10,
            page_width=612,
            page_height=792,
            english_pdf_pages=(2,),
        ),
        sections=(
            Section(
                id="vocabulary",
                kind=SectionKind.VOCABULARY,
                heading=_text("Vocabulary"),
                directions=_text("Fictional directions"),
                questions=(_question(1), _question(2)),
            ),
        ),
    )
    return StagedDataset(
        schema_version="1.0",
        generator=GeneratorInfo("test", "1.0", "native", "none", "none"),
        exam=exam,
        validation=ValidationReport("synthetic", "PASSED", (), ()),
    )


def _curated():
    return {
        "schema_version": "1.0",
        "artifact_type": "SOURCE_LINKED_VISUAL_KEY_TRANSCRIPTION",
        "canonical_exam_id": "iran-ce-msc-1499",
        "state": "PENDING_HUMAN_REVIEW",
        "verified_final_answer": False,
        "independent_blind_ai_solution": False,
        "exam_source": {
            "filename": "synthetic-exam.pdf",
            "sha256": "a" * 64,
            "english_pdf_pages": [2],
        },
        "key_source": {
            "filename": "synthetic-key.pdf",
            "sha256": "b" * 64,
            "page_number": 1,
            "edition": "INITIAL",
            "booklet_code": "C",
            "provenance_kind": "VISUAL",
            "native_pdf_text": False,
            "source_region_descriptor": "fictional first table group rows 1-2",
        },
        "entries": [
            {
                "question_number": number,
                "section": "VOCABULARY",
                "question_pdf_page": 2,
                "passage_id": None,
                "official_answer_position": number,
                "key_table_group": 1,
                "key_table_row": number,
            }
            for number in (1, 2)
        ],
    }


def _codes(result) -> set[str]:
    assert result.status == "BLOCKED"
    assert not result.claims
    return {error.code for error in result.errors}


def test_aligns_source_claims_without_mutating_or_promoting_verified_answers():
    staged = _staged()
    source_before = deepcopy(staged)
    curated = _curated()
    curated_before = deepcopy(curated)
    result = align_curated_official_claims(staged, curated, expected_key=KEY)

    assert not result.errors
    assert result.status == "ALIGNED_PENDING_HUMAN_REVIEW"
    assert [claim.question_id for claim in result.claims] == ["q-01", "q-02"]
    assert [claim.official_answer_position for claim in result.claims] == [1, 2]
    assert {claim.review_state for claim in result.claims} == {"PENDING_HUMAN_REVIEW"}
    assert {claim.key_booklet_code for claim in result.claims} == {"C"}
    assert staged == source_before
    assert curated == curated_before
    assert all(q.answers.official is None for q in staged.exam.sections[0].questions)


@pytest.mark.parametrize(
    ("change", "code"),
    [
        (lambda x: x["key_source"].update(sha256="c" * 64), "CLAIM_KEY_IDENTITY"),
        (lambda x: x["key_source"].update(booklet_code="A"), "CLAIM_KEY_IDENTITY"),
        (lambda x: x["key_source"].update(native_pdf_text=True), "CLAIM_KEY_PROVENANCE"),
        (lambda x: x["exam_source"].update(sha256="d" * 64), "CLAIM_EXAM_SOURCE"),
        (lambda x: x["entries"].pop(), "CLAIM_COVERAGE"),
        (lambda x: x["entries"].append(deepcopy(x["entries"][0])), "CLAIM_DUPLICATE"),
        (lambda x: x["entries"][1].update(official_answer_position=5), "CLAIM_INVALID_CHOICE"),
        (lambda x: x["entries"][1].update(section="READING"), "CLAIM_SECTION_PASSAGE"),
        (lambda x: x["entries"][1].update(question_pdf_page=3), "CLAIM_PRINTED_QUESTION_PAGE"),
        (lambda x: x["entries"][1].update(key_table_row=1), "CLAIM_KEY_ROW_MAPPING"),
        (lambda x: x.update(state="VERIFIED"), "CLAIM_REVIEW_STATE"),
        (lambda x: x.update(verified_final_answer=True), "CLAIM_AUTHORITY"),
    ],
)
def test_fails_closed_on_bad_identity_coverage_mapping_or_review_state(change, code):
    data = _curated()
    change(data)
    assert code in _codes(align_curated_official_claims(_staged(), data, expected_key=KEY))


def test_refuses_unvalidated_exam_staging():
    staged = _staged()
    staged = replace(staged, validation=replace(staged.validation, status="FAILED"))
    assert "CLAIM_EXAM_NOT_VALIDATED" in _codes(
        align_curated_official_claims(staged, _curated(), expected_key=KEY)
    )


def test_refuses_prepopulated_answer_even_if_staging_claimed_to_have_passed():
    staged = _staged()
    section = staged.exam.sections[0]
    question = section.questions[0]
    record = AnswerRecord((1,), AnswerStatus.ACCEPTED)
    modified = replace(question, answers=replace(question.answers, official=record))
    changed_section = replace(section, questions=(modified, *section.questions[1:]))
    changed = replace(staged, exam=replace(staged.exam, sections=(changed_section,)))
    assert "CLAIM_EXAM_HAS_ANSWERS" in _codes(
        align_curated_official_claims(changed, _curated(), expected_key=KEY)
    )
