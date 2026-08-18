from english_exam.domain import BBox, QuestionKind
from english_exam.importers.exam_1396 import (
    READING_QUESTION_RANGES,
    _marker_value,
    _parse_questions,
)
from english_exam.pdf_layout import LayoutChar, LayoutWord, TextLine


def word(text: str, x0: float, y0: float, x1: float, y1: float) -> LayoutWord:
    return LayoutWord(text, BBox(x0, y0, x1, y1), "SyntheticFont", 11.0)


def character_word(text: str, x0: float, y0: float, width: float = 2.0) -> LayoutWord:
    chars = tuple(
        LayoutChar(
            char,
            BBox(x0 + index * width, y0, x0 + (index + 1) * width, y0 + 10),
        )
        for index, char in enumerate(text)
    )
    return LayoutWord(
        text,
        BBox(x0, y0, x0 + len(text) * width, y0 + 10),
        "SyntheticFont",
        11.0,
        chars,
    )


def test_observed_question_markers_are_fixture_specific() -> None:
    assert _marker_value("I·") == 1
    assert _marker_value("10..") == 10
    assert _marker_value("t 5-") == 15
    assert _marker_value("IS.-") == 18
    assert _marker_value("PASSAGE") is None


def test_parses_four_column_vocabulary_question_and_preserves_markers() -> None:
    lines = (
        TextLine(
            2,
            (
                word("I·", 58, 100, 68, 111),
                word("Invented", 84, 100, 130, 111),
                word("----", 135, 100, 160, 111),
                word("stem.", 165, 100, 195, 111),
            ),
        ),
        TextLine(
            2,
            (
                word("I)", 85, 115, 95, 126),
                word("alpha", 100, 115, 130, 126),
                word("2)", 190, 115, 200, 126),
                word("beta", 205, 115, 230, 126),
                word("3)", 294, 115, 304, 126),
                word("gamma", 309, 115, 345, 126),
                word("4)", 398, 115, 408, 126),
                word("delta", 413, 115, 445, 126),
            ),
        ),
    )

    questions, warnings = _parse_questions(
        lines,
        expected_numbers=(1,),
        kind=QuestionKind.SENTENCE_COMPLETION,
        source_filename="96.pdf",
    )

    question = questions[0]
    assert question.number == 1
    assert question.raw_number_marker.raw_text == "I·"
    assert question.blank is not None
    assert question.blank.marker.raw_text == "----"
    assert [choice.text.raw_text for choice in question.choices] == [
        "alpha",
        "beta",
        "gamma",
        "delta",
    ]
    assert [warning.code for warning in warnings] == ["OCR_LIKE_QUESTION_MARKER"]


def test_reading_ranges_are_explicit_1396_data() -> None:
    assert READING_QUESTION_RANGES == {
        "reading-1": (16, 17, 18, 19, 20),
        "reading-2": (21, 22, 23, 24, 25),
        "reading-3": (26, 27, 28, 29, 30),
    }


def test_parser_splits_combined_choice_tokens_with_exact_geometry() -> None:
    lines = (
        TextLine(
            2,
            (
                word("9-", 58, 100, 68, 111),
                word("Invented", 84, 100, 130, 111),
                character_word("----", 135, 100),
                word("stem.", 165, 100, 195, 111),
            ),
        ),
        TextLine(
            2,
            (
                character_word("!)justify", 85, 115),
                character_word("2)clarify", 190, 115),
                character_word("3)emerge", 294, 115),
                character_word("4)improvise", 398, 115),
            ),
        ),
    )

    questions, _ = _parse_questions(
        lines,
        expected_numbers=(9,),
        kind=QuestionKind.SENTENCE_COMPLETION,
        source_filename="96.pdf",
    )

    question = questions[0]
    marker_box = question.choices[0].raw_marker.provenance[0].bbox
    text_box = question.choices[0].text.provenance[0].bbox
    blank_box = question.blank.marker.provenance[0].bbox

    assert question.choices[0].raw_marker.raw_text == "!)"
    assert question.choices[0].text.raw_text == "justify"
    assert marker_box.x1 == text_box.x0
    assert blank_box == BBox(135, 100, 143, 110)
