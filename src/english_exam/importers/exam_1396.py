"""Deterministic importer for the 1396 (source/96.pdf) English fixture."""

from __future__ import annotations

import re
from collections.abc import Iterable, Sequence
from hashlib import sha256
from pathlib import Path

from english_exam.domain import (
    Blank,
    Choice,
    DatasetState,
    Exam,
    ExtractedText,
    ExtractionIssue,
    IssueSeverity,
    Passage,
    PassageKind,
    Question,
    QuestionKind,
    Section,
    SectionKind,
    SourceDocument,
)
from english_exam.pdf_layout import (
    LayoutWord,
    PageLayout,
    TextLine,
    extract_pdf_layout,
    extracted_substring_from_words,
    extracted_text_from_lines,
    extracted_text_from_word_groups,
    slice_layout_word,
)

EXPECTED_FILENAME = "96.pdf"
EXPECTED_SHA256 = "69bc3434ae61c05c85bc9fabffd0b2ce13e5b39bc71b1dfd71c16709c9638ba2"
ENGLISH_PAGES = (2, 3, 4, 5)
CROP_TOP = 80.0
READING_QUESTION_RANGES = {
    "reading-1": tuple(range(16, 21)),
    "reading-2": tuple(range(21, 26)),
    "reading-3": tuple(range(26, 31)),
}

_OBSERVED_MARKER_VALUES = {
    "I·": 1,
    "t 5-": 15,
    "IS.-": 18,
}
_CHOICE_MARKER = re.compile(r"^([1-4I!])\)(.*)$")
_BLANK_MARKER = re.compile(r"[-·~_]{3,}")
_CLOZE_BLANK = re.compile(r"[({]\s*(1[1-5])\)\s*[·-]+")


class FixtureParseError(RuntimeError):
    """Raised when the inspected 1396 layout no longer matches expectations."""


def _sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _marker_words(line: TextLine) -> tuple[LayoutWord, ...]:
    if line.bbox.x0 > 78:
        return ()
    return tuple(word for word in line.words if word.bbox.x0 < 80)


def _marker_value(raw_marker: str) -> int | None:
    if raw_marker in _OBSERVED_MARKER_VALUES:
        return _OBSERVED_MARKER_VALUES[raw_marker]
    match = re.fullmatch(r"(\d{1,2})[.·-]+", raw_marker)
    return int(match.group(1)) if match else None


def _question_starts(
    lines: Sequence[TextLine],
    expected_numbers: Sequence[int],
) -> tuple[tuple[int, int, tuple[LayoutWord, ...]], ...]:
    expected = set(expected_numbers)
    starts: list[tuple[int, int, tuple[LayoutWord, ...]]] = []
    for index, line in enumerate(lines):
        words = _marker_words(line)
        value = _marker_value(" ".join(word.text for word in words)) if words else None
        if value in expected:
            starts.append((index, value, words))
    actual = tuple(value for _, value, _ in starts)
    if actual != tuple(expected_numbers):
        raise FixtureParseError(
            f"question markers differ from fixture: expected {tuple(expected_numbers)}, got {actual}"
        )
    return tuple(starts)


def _find_question_index(lines: Sequence[TextLine], number: int) -> int:
    return _question_starts(lines, (number,))[0][0]


def _find_line(lines: Sequence[TextLine], predicate, description: str) -> int:
    for index, line in enumerate(lines):
        if predicate(line.raw_text):
            return index
    raise FixtureParseError(f"could not locate {description}")


def _marker_text(
    words: Sequence[LayoutWord],
    *,
    source_filename: str,
    page_number: int,
) -> ExtractedText:
    return extracted_text_from_word_groups(
        ((page_number, words),),
        source_filename=source_filename,
    )


def _choice_marker_value(text: str) -> tuple[int, str, str] | None:
    match = _CHOICE_MARKER.fullmatch(text)
    if not match:
        return None
    raw_position, suffix = match.groups()
    position = 1 if raw_position in {"I", "!"} else int(raw_position)
    return position, f"{raw_position})", suffix


def _blank_from_word_groups(
    groups: Sequence[tuple[int, Sequence[LayoutWord]]],
    *,
    source_filename: str,
) -> Blank:
    for page_number, words in groups:
        raw_text = " ".join(word.text for word in words)
        match = _BLANK_MARKER.search(raw_text)
        if match:
            return Blank(
                marker=extracted_substring_from_words(
                    words,
                    start=match.start(),
                    end=match.end(),
                    source_filename=source_filename,
                    page_number=page_number,
                )
            )
    stem_text = "\n".join(" ".join(word.text for word in words) for _, words in groups)
    raise FixtureParseError(f"no blank marker found in vocabulary stem: {stem_text!r}")


def _parse_question(
    lines: Sequence[TextLine],
    *,
    number: int,
    kind: QuestionKind,
    source_filename: str,
    cloze_blank: Blank | None = None,
) -> tuple[Question, tuple[ExtractionIssue, ...]]:
    if not lines:
        raise FixtureParseError(f"question {number} has an empty region")

    number_words = _marker_words(lines[0])
    raw_number_marker = _marker_text(
        number_words,
        source_filename=source_filename,
        page_number=lines[0].page_number,
    )
    expected_choice = 1
    active_choice: int | None = None
    choice_markers: dict[int, ExtractedText] = {}
    choice_groups: dict[int, list[tuple[int, tuple[LayoutWord, ...]]]] = {}
    stem_groups: list[tuple[int, tuple[LayoutWord, ...]]] = []

    for line_index, line in enumerate(lines):
        words = line.words[len(number_words) :] if line_index == 0 else line.words
        stem_words: list[LayoutWord] = []
        choice_words: list[LayoutWord] = []

        for word in words:
            marker = _choice_marker_value(word.text)
            if marker and marker[0] == expected_choice:
                if active_choice is not None and choice_words:
                    choice_groups.setdefault(active_choice, []).append(
                        (line.page_number, tuple(choice_words))
                    )
                    choice_words = []
                position, raw_marker, suffix = marker
                marker_word = slice_layout_word(word, 0, len(raw_marker))
                choice_markers[position] = _marker_text(
                    (marker_word,),
                    source_filename=source_filename,
                    page_number=line.page_number,
                )
                active_choice = position
                expected_choice += 1
                if suffix:
                    choice_words.append(slice_layout_word(word, len(raw_marker), len(word.text)))
                continue

            if active_choice is None:
                stem_words.append(word)
            else:
                choice_words.append(word)

        if stem_words:
            stem_groups.append((line.page_number, tuple(stem_words)))
        if active_choice is not None and choice_words:
            choice_groups.setdefault(active_choice, []).append(
                (line.page_number, tuple(choice_words))
            )

    if tuple(sorted(choice_markers)) != (1, 2, 3, 4):
        raise FixtureParseError(
            f"question {number} choices differ from fixture: {tuple(sorted(choice_markers))}"
        )

    choices = tuple(
        Choice(
            position=position,
            raw_marker=choice_markers[position],
            text=extracted_text_from_word_groups(
                choice_groups[position],
                source_filename=source_filename,
            ),
        )
        for position in range(1, 5)
    )

    if kind is QuestionKind.CLOZE_BLANK:
        stem = None
        blank = cloze_blank
    else:
        stem = extracted_text_from_word_groups(
            stem_groups,
            source_filename=source_filename,
        )
        blank = (
            _blank_from_word_groups(stem_groups, source_filename=source_filename)
            if kind is QuestionKind.SENTENCE_COMPLETION
            else None
        )

    issues: list[ExtractionIssue] = []
    if raw_number_marker.raw_text != f"{number}-":
        issues.append(
            ExtractionIssue(
                code="OCR_LIKE_QUESTION_MARKER",
                severity=IssueSeverity.WARNING,
                message=(
                    f"Question {number} uses source marker "
                    f"{raw_number_marker.raw_text!r}; canonical number comes from the 1396 fixture."
                ),
                entity_id=f"q-{number:02d}",
                provenance=raw_number_marker.provenance,
            )
        )

    return (
        Question(
            id=f"q-{number:02d}",
            number=number,
            raw_number_marker=raw_number_marker,
            kind=kind,
            stem=stem,
            blank=blank,
            choices=choices,
        ),
        tuple(issues),
    )


def _parse_questions(
    lines: Sequence[TextLine],
    *,
    expected_numbers: Sequence[int],
    kind: QuestionKind,
    source_filename: str,
    cloze_blanks: dict[int, Blank] | None = None,
) -> tuple[tuple[Question, ...], tuple[ExtractionIssue, ...]]:
    starts = _question_starts(lines, expected_numbers)
    questions: list[Question] = []
    issues: list[ExtractionIssue] = []
    for position, (start, number, _) in enumerate(starts):
        end = starts[position + 1][0] if position + 1 < len(starts) else len(lines)
        question, question_issues = _parse_question(
            lines[start:end],
            number=number,
            kind=kind,
            source_filename=source_filename,
            cloze_blank=cloze_blanks[number] if cloze_blanks else None,
        )
        questions.append(question)
        issues.extend(question_issues)
    return tuple(questions), tuple(issues)


def _extract_cloze_blanks(
    lines: Sequence[TextLine],
    *,
    source_filename: str,
) -> dict[int, Blank]:
    blanks: dict[int, Blank] = {}
    for line in lines:
        for match in _CLOZE_BLANK.finditer(line.raw_text):
            number = int(match.group(1))
            blanks[number] = Blank(
                marker=extracted_substring_from_words(
                    line.words,
                    start=match.start(),
                    end=match.end(),
                    source_filename=source_filename,
                    page_number=line.page_number,
                )
            )
    if tuple(sorted(blanks)) != (11, 12, 13, 14, 15):
        raise FixtureParseError(f"cloze blank markers differ from fixture: {tuple(sorted(blanks))}")
    return blanks


def _questions_by_number(groups: Iterable[Sequence[Question]]) -> dict[int, Question]:
    return {question.number: question for group in groups for question in group}


def import_exam_1396(source_path: Path) -> tuple[Exam, tuple[ExtractionIssue, ...]]:
    source_path = Path(source_path)
    if source_path.name != EXPECTED_FILENAME:
        raise FixtureParseError(
            f"1396 fixture expects {EXPECTED_FILENAME!r}, got {source_path.name!r}"
        )
    source_hash = _sha256(source_path)
    if source_hash != EXPECTED_SHA256:
        raise FixtureParseError(
            f"source hash mismatch for {source_path}: expected {EXPECTED_SHA256}, got {source_hash}"
        )

    layout = extract_pdf_layout(
        source_path,
        page_numbers=ENGLISH_PAGES,
        crop_top=CROP_TOP,
    )
    pages: dict[int, PageLayout] = {page.page_number: page for page in layout.pages}
    p2, p3, p4, p5 = (pages[number].lines for number in ENGLISH_PAGES)
    issues: list[ExtractionIssue] = []

    part_a = _find_line(p2, lambda text: text.startswith("PART A:"), "Part A heading")
    part_b = _find_line(p2, lambda text: text.startswith("PART B:"), "Part B heading")
    q1 = _find_question_index(p2[part_a:part_b], 1) + part_a
    vocabulary_questions, found = _parse_questions(
        p2[q1:part_b],
        expected_numbers=range(1, 11),
        kind=QuestionKind.SENTENCE_COMPLETION,
        source_filename=layout.source_filename,
    )
    issues.extend(found)

    cloze_body_start = (
        _find_line(
            p2[part_b:],
            lambda text: text.startswith("Remembering the past"),
            "Cloze passage body",
        )
        + part_b
    )
    cloze_body_lines = p2[cloze_body_start:]
    cloze_blanks = _extract_cloze_blanks(
        cloze_body_lines,
        source_filename=layout.source_filename,
    )

    part_c = _find_line(p3, lambda text: text.startswith("PART C:"), "Part C heading")
    cloze_questions, found = _parse_questions(
        p3[:part_c],
        expected_numbers=range(11, 16),
        kind=QuestionKind.CLOZE_BLANK,
        source_filename=layout.source_filename,
        cloze_blanks=cloze_blanks,
    )
    issues.extend(found)

    passage_1_heading = _find_line(
        p3,
        lambda text: text.upper().startswith("PASSAGE.I"),
        "Reading Passage 1 heading",
    )
    q16 = _find_question_index(p3[passage_1_heading:], 16) + passage_1_heading
    reading_16_19, found = _parse_questions(
        p3[q16:],
        expected_numbers=range(16, 20),
        kind=QuestionKind.READING_COMPREHENSION,
        source_filename=layout.source_filename,
    )
    issues.extend(found)

    passage_2_heading = _find_line(
        p4,
        lambda text: text.upper().startswith("PASSAGB2"),
        "Reading Passage 2 heading",
    )
    q21 = _find_question_index(p4[passage_2_heading:], 21) + passage_2_heading
    reading_20, found = _parse_questions(
        p4[:passage_2_heading],
        expected_numbers=(20,),
        kind=QuestionKind.READING_COMPREHENSION,
        source_filename=layout.source_filename,
    )
    issues.extend(found)
    reading_21_24, found = _parse_questions(
        p4[q21:],
        expected_numbers=range(21, 25),
        kind=QuestionKind.READING_COMPREHENSION,
        source_filename=layout.source_filename,
    )
    issues.extend(found)

    passage_3_heading = _find_line(
        p5,
        lambda text: text.upper().startswith("PASSAGE 3"),
        "Reading Passage 3 heading",
    )
    q26 = _find_question_index(p5[passage_3_heading:], 26) + passage_3_heading
    reading_25, found = _parse_questions(
        p5[:passage_3_heading],
        expected_numbers=(25,),
        kind=QuestionKind.READING_COMPREHENSION,
        source_filename=layout.source_filename,
    )
    issues.extend(found)
    reading_26_30, found = _parse_questions(
        p5[q26:],
        expected_numbers=range(26, 31),
        kind=QuestionKind.READING_COMPREHENSION,
        source_filename=layout.source_filename,
    )
    issues.extend(found)

    reading_questions = _questions_by_number(
        (reading_16_19, reading_20, reading_21_24, reading_25, reading_26_30)
    )
    passage_1 = Passage(
        id="reading-1",
        kind=PassageKind.READING,
        heading=extracted_text_from_lines(
            (p3[passage_1_heading],),
            source_filename=layout.source_filename,
        ),
        body=extracted_text_from_lines(
            p3[passage_1_heading + 1 : q16],
            source_filename=layout.source_filename,
        ),
        questions=tuple(
            reading_questions[number] for number in READING_QUESTION_RANGES["reading-1"]
        ),
    )
    passage_2 = Passage(
        id="reading-2",
        kind=PassageKind.READING,
        heading=extracted_text_from_lines(
            (p4[passage_2_heading],),
            source_filename=layout.source_filename,
        ),
        body=extracted_text_from_lines(
            p4[passage_2_heading + 1 : q21],
            source_filename=layout.source_filename,
        ),
        questions=tuple(
            reading_questions[number] for number in READING_QUESTION_RANGES["reading-2"]
        ),
    )
    passage_3 = Passage(
        id="reading-3",
        kind=PassageKind.READING,
        heading=extracted_text_from_lines(
            (p5[passage_3_heading],),
            source_filename=layout.source_filename,
        ),
        body=extracted_text_from_lines(
            p5[passage_3_heading + 1 : q26],
            source_filename=layout.source_filename,
        ),
        questions=tuple(
            reading_questions[number] for number in READING_QUESTION_RANGES["reading-3"]
        ),
    )

    vocabulary = Section(
        id="vocabulary",
        kind=SectionKind.VOCABULARY,
        heading=extracted_text_from_lines(
            (p2[part_a],),
            source_filename=layout.source_filename,
        ),
        directions=extracted_text_from_lines(
            p2[part_a + 1 : q1],
            source_filename=layout.source_filename,
        ),
        questions=vocabulary_questions,
    )
    cloze = Section(
        id="cloze",
        kind=SectionKind.CLOZE,
        heading=extracted_text_from_lines(
            (p2[part_b],),
            source_filename=layout.source_filename,
        ),
        directions=extracted_text_from_lines(
            p2[part_b + 1 : cloze_body_start],
            source_filename=layout.source_filename,
        ),
        passages=(
            Passage(
                id="cloze-1",
                kind=PassageKind.CLOZE,
                heading=None,
                body=extracted_text_from_lines(
                    cloze_body_lines,
                    source_filename=layout.source_filename,
                ),
                questions=cloze_questions,
            ),
        ),
    )
    reading = Section(
        id="reading",
        kind=SectionKind.READING,
        heading=extracted_text_from_lines(
            (p3[part_c],),
            source_filename=layout.source_filename,
        ),
        directions=extracted_text_from_lines(
            p3[part_c + 1 : passage_1_heading],
            source_filename=layout.source_filename,
        ),
        passages=(passage_1, passage_2, passage_3),
    )

    return (
        Exam(
            id="iran-ce-msc-1396",
            year=1396,
            state=DatasetState.STAGED,
            source_document=SourceDocument(
                source_filename=layout.source_filename,
                sha256=source_hash,
                page_count=layout.page_count,
                page_width=pages[2].width,
                page_height=pages[2].height,
                english_pdf_pages=ENGLISH_PAGES,
            ),
            sections=(vocabulary, cloze, reading),
        ),
        tuple(issues),
    )
