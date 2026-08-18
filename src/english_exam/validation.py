"""Generic and 1396 fixture-specific validation."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from math import isfinite

from english_exam.domain import (
    Exam,
    ExtractedText,
    ExtractionIssue,
    IssueSeverity,
    Question,
    SectionKind,
    SourceDocument,
    ValidationReport,
)
from english_exam.importers.exam_1396 import (
    ENGLISH_PAGES,
    EXPECTED_FILENAME,
    EXPECTED_SHA256,
    READING_QUESTION_RANGES,
)
from english_exam.pdf_layout import SUPPORTED_EXTRACTION_METHODS


def all_questions(exam: Exam) -> tuple[Question, ...]:
    questions: list[Question] = []
    for section in exam.sections:
        questions.extend(section.questions)
        for passage in section.passages:
            questions.extend(passage.questions)
    return tuple(questions)


def _all_text(exam: Exam) -> Iterable[tuple[str, ExtractedText]]:
    for section in exam.sections:
        yield f"section:{section.id}:heading", section.heading
        yield f"section:{section.id}:directions", section.directions
        for passage in section.passages:
            if passage.heading is not None:
                yield f"passage:{passage.id}:heading", passage.heading
            yield f"passage:{passage.id}:body", passage.body
            yield from _question_text(passage.questions)
        yield from _question_text(section.questions)


def _question_text(
    questions: Iterable[Question],
) -> Iterable[tuple[str, ExtractedText]]:
    for question in questions:
        yield f"{question.id}:number", question.raw_number_marker
        if question.stem is not None:
            yield f"{question.id}:stem", question.stem
        if question.blank is not None:
            yield f"{question.id}:blank", question.blank.marker
        for choice in question.choices:
            yield f"{question.id}:choice:{choice.position}:marker", choice.raw_marker
            yield f"{question.id}:choice:{choice.position}:text", choice.text


def _valid_bbox(text: ExtractedText, source: SourceDocument) -> bool:
    for item in text.provenance:
        box = item.bbox
        try:
            finite = all(isfinite(value) for value in (box.x0, box.y0, box.x1, box.y1))
        except TypeError:
            return False
        if not (
            finite
            and box.units == "pt"
            and box.origin == "top-left"
            and 0 <= box.x0 < box.x1 <= source.page_width + 0.01
            and 0 <= box.y0 < box.y1 <= source.page_height + 0.01
        ):
            return False
    return True


def validate_text_provenance(
    text: ExtractedText,
    *,
    source: SourceDocument,
    entity_id: str,
) -> tuple[ExtractionIssue, ...]:
    """Validate source-independent provenance invariants for extracted text."""

    errors: list[ExtractionIssue] = []

    def fail(code: str, message: str) -> None:
        errors.append(
            ExtractionIssue(
                code=code,
                severity=IssueSeverity.ERROR,
                message=message,
                entity_id=entity_id,
            )
        )

    if not text.provenance:
        fail("MISSING_PROVENANCE", "extracted text has no provenance")
        return tuple(errors)

    for item in text.provenance:
        if not item.raw_text:
            fail("PROVENANCE_RAW_TEXT", "provenance raw_text is empty")
        if item.source_filename != source.source_filename:
            fail(
                "PROVENANCE_SOURCE",
                f"provenance source {item.source_filename!r} does not match "
                f"{source.source_filename!r}",
            )
        if item.extraction_method not in SUPPORTED_EXTRACTION_METHODS:
            fail(
                "PROVENANCE_METHOD",
                f"unsupported extraction method {item.extraction_method!r}",
            )
        if (
            not isinstance(item.page_number, int)
            or isinstance(item.page_number, bool)
            or not 1 <= item.page_number <= source.page_count
        ):
            fail(
                "PROVENANCE_PAGE_NUMBER",
                f"invalid 1-based page number {item.page_number!r}",
            )

    if not _valid_bbox(text, source):
        fail("PROVENANCE_BBOX", "provenance contains an invalid bounding box")

    provenance_text = "\n".join(item.raw_text for item in text.provenance)
    if provenance_text != text.raw_text:
        fail(
            "PROVENANCE_FRAGMENT",
            "provenance raw fragments do not reconstruct extracted raw_text",
        )

    return tuple(errors)


def validate_exam_1396(
    exam: Exam,
    *,
    parser_warnings: tuple[ExtractionIssue, ...] = (),
) -> ValidationReport:
    errors: list[ExtractionIssue] = []

    def fail(code: str, message: str, entity_id: str | None = None) -> None:
        errors.append(
            ExtractionIssue(
                code=code,
                severity=IssueSeverity.ERROR,
                message=message,
                entity_id=entity_id,
            )
        )

    source = exam.source_document
    if source.source_filename != EXPECTED_FILENAME:
        fail("SOURCE_FILENAME", f"expected {EXPECTED_FILENAME}, got {source.source_filename}")
    if source.sha256 != EXPECTED_SHA256:
        fail("SOURCE_HASH", "source/96.pdf SHA-256 does not match the fixture")
    if source.page_count != 40:
        fail("PAGE_COUNT", f"expected 40 PDF pages, got {source.page_count}")
    if source.english_pdf_pages != ENGLISH_PAGES:
        fail(
            "ENGLISH_PAGE_RANGE",
            f"expected English pages {ENGLISH_PAGES}, got {source.english_pdf_pages}",
        )

    section_kinds = tuple(section.kind for section in exam.sections)
    expected_sections = (
        SectionKind.VOCABULARY,
        SectionKind.CLOZE,
        SectionKind.READING,
    )
    if section_kinds != expected_sections:
        fail("SECTION_ORDER", f"expected {expected_sections}, got {section_kinds}")

    questions = all_questions(exam)
    numbers = tuple(question.number for question in questions)
    counts = Counter(numbers)
    duplicates = tuple(sorted(number for number, count in counts.items() if count > 1))
    if duplicates:
        fail("DUPLICATE_QUESTIONS", f"duplicate question numbers: {duplicates}")
    if tuple(sorted(numbers)) != tuple(range(1, 31)):
        fail("QUESTION_RANGE", f"expected questions 1-30, got {tuple(sorted(numbers))}")

    for question in questions:
        positions = tuple(choice.position for choice in question.choices)
        if positions != (1, 2, 3, 4):
            fail(
                "CHOICE_COUNT",
                f"question {question.number} choices are {positions}, expected (1, 2, 3, 4)",
                question.id,
            )
        answers = question.answers
        if any((answers.official, answers.ai, answers.final_verified)):
            fail("UNEXPECTED_ANSWER", "staged extraction must not contain answers", question.id)

    if len(exam.sections) == 3:
        vocabulary, cloze, reading = exam.sections
        if tuple(question.number for question in vocabulary.questions) != tuple(range(1, 11)):
            fail("VOCABULARY_RANGE", "Vocabulary must contain questions 1-10")
        if any(question.blank is None for question in vocabulary.questions):
            fail("VOCABULARY_BLANK", "every Vocabulary question must have a blank")
        if len(cloze.passages) != 1:
            fail("CLOZE_PASSAGE_COUNT", "Cloze must contain exactly one passage")
        elif tuple(question.number for question in cloze.passages[0].questions) != tuple(
            range(11, 16)
        ):
            fail("CLOZE_RANGE", "Cloze passage must contain questions 11-15")
        elif any(question.blank is None for question in cloze.passages[0].questions):
            fail("CLOZE_BLANK", "every Cloze question must link to a passage blank")

        if len(reading.passages) != 3:
            fail("READING_PASSAGE_COUNT", "Reading must contain exactly three passages")
        else:
            for passage in reading.passages:
                expected = READING_QUESTION_RANGES.get(passage.id)
                actual = tuple(question.number for question in passage.questions)
                if expected != actual:
                    fail(
                        "READING_RELATIONSHIP",
                        f"{passage.id} expected {expected}, got {actual}",
                        passage.id,
                    )

    for entity_id, text in _all_text(exam):
        if not text.raw_text:
            fail("EMPTY_RAW_TEXT", "extracted text is empty", entity_id)
        if text.normalized_text is not None or text.corrected_text is not None:
            fail("SILENT_CORRECTION", "Milestone 1 may populate raw_text only", entity_id)
        errors.extend(validate_text_provenance(text, source=source, entity_id=entity_id))
        for item in text.provenance:
            valid_document_page = (
                isinstance(item.page_number, int)
                and not isinstance(item.page_number, bool)
                and 1 <= item.page_number <= source.page_count
            )
            if valid_document_page and item.page_number not in ENGLISH_PAGES:
                fail(
                    "PROVENANCE_PAGE",
                    f"unexpected provenance page {item.page_number}",
                    entity_id,
                )

    return ValidationReport(
        fixture="1396",
        status="PASSED" if not errors else "FAILED",
        errors=tuple(errors),
        warnings=parser_warnings,
    )
