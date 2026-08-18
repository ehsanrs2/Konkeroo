from english_exam.domain import BBox
from english_exam.pdf_layout import (
    LayoutChar,
    LayoutWord,
    extracted_substring_from_words,
    group_words_into_lines,
)


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


def test_groups_by_baseline_and_restores_geometric_order() -> None:
    words = (
        word("second", 20, 30, 50, 40),
        word("tail", 70, 10, 90, 20),
        word("first", 10, 10, 40, 20),
        word("raised", 45, 7, 65, 19),
    )

    lines = group_words_into_lines(words, page_number=2)

    assert [line.raw_text for line in lines] == ["first raised tail", "second"]


def test_displaced_glyph_joins_line_by_bottom_edge() -> None:
    words = (
        word("try", 84, 338, 98, 349),
        word("10", 101, 341, 109, 349),
        word("control", 113, 338, 145, 349),
    )

    lines = group_words_into_lines(words, page_number=2)

    assert len(lines) == 1
    assert lines[0].raw_text == "try 10 control"


def test_substrings_use_their_own_character_geometry() -> None:
    combined = character_word("!)justify", 10, 20)

    marker = extracted_substring_from_words(
        (combined,),
        start=0,
        end=2,
        source_filename="synthetic.pdf",
        page_number=1,
    )
    choice_text = extracted_substring_from_words(
        (combined,),
        start=2,
        end=len(combined.text),
        source_filename="synthetic.pdf",
        page_number=1,
    )

    assert marker.raw_text == "!)"
    assert marker.provenance[0].raw_text == "!)"
    assert marker.provenance[0].bbox == BBox(10, 20, 14, 30)
    assert choice_text.raw_text == "justify"
    assert choice_text.provenance[0].raw_text == "justify"
    assert choice_text.provenance[0].bbox == BBox(14, 20, 28, 30)
