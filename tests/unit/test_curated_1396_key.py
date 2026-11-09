"""Contract tests for source-linked, manually curated 1396 key observations.

Does not require or parse actual exam PDFs.
"""

import json
from pathlib import Path

DATA = Path(__file__).parents[2] / "dataset" / "review" / "1396-english-official-key.json"


def _data():
    return json.loads(DATA.read_text(encoding="utf-8"))


def test_transcription_is_source_linked_and_not_final():
    data = _data()
    assert data["canonical_exam_id"] == "iran-ce-msc-1396"
    assert data["state"] == "PENDING_HUMAN_REVIEW"
    assert data["transcription_method"] == "AI_DIRECT_VISUAL_READING"
    assert data["independent_blind_ai_solution"] is False
    assert data["verified_final_answer"] is False
    assert data["exam_source"]["sha256"] == (
        "69bc3434ae61c05c85bc9fabffd0b2ce13e5b39bc71b1dfd71c16709c9638ba2"
    )
    assert data["key_source"]["sha256"] == (
        "5d421dcddc780120b13a08753fd2559e7ec02a60200c7c88f4211d70429cba61"
    )
    assert data["key_source"]["edition"] == "INITIAL"
    assert data["key_source"]["booklet_code"] == "C"
    assert data["key_source"]["provenance_kind"] == "VISUAL"
    assert data["key_source"]["native_pdf_text"] is False


def test_all_30_english_answers_have_valid_geometry_free_locators():
    entries = _data()["entries"]
    assert [row["question_number"] for row in entries] == list(range(1, 31))
    assert all(1 <= row["official_answer_position"] <= 4 for row in entries)
    assert all(row["key_table_group"] == 1 for row in entries)
    assert [row["key_table_row"] for row in entries] == list(range(1, 31))
    assert all(row["question_pdf_page"] in (2, 3, 4, 5) for row in entries)
    assert set(entries[0]) == {
        "question_number",
        "section",
        "question_pdf_page",
        "passage_id",
        "official_answer_position",
        "key_table_group",
        "key_table_row",
    }


def test_section_and_passage_relationships_remain_fixture_specific():
    entries = _data()["entries"]
    for entry in entries:
        number = entry["question_number"]
        section = ("VOCABULARY" if number <= 10 else "CLOZE" if number <= 15 else "READING")
        passage = (
            None if number <= 10 else
            "cloze-1" if number <= 15 else
            "reading-1" if number <= 20 else
            "reading-2" if number <= 25 else "reading-3"
        )
        expected_page = 2 if number <= 10 else 3 if number <= 19 else 4 if number <= 24 else 5
        assert entry["section"] == section
        assert entry["passage_id"] == passage
        assert entry["question_pdf_page"] == expected_page


def test_selected_boundary_values_match_visual_review():
    by_number = {row["question_number"]: row for row in _data()["entries"]}
    for number, position in {1: 1, 10: 3, 11: 4, 15: 4, 16: 3, 20: 2,
                             21: 3, 25: 1, 26: 1, 30: 3}.items():
        assert by_number[number]["official_answer_position"] == position
