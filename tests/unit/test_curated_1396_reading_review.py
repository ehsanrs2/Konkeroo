"""Source-independent guardrails for the curated 1396 Reading review."""

import json
from collections import Counter
from pathlib import Path

FILE = Path(__file__).parents[2] / "dataset/review/1396-reading-text-review.json"
EXPECTED_SHA = "69bc3434ae61c05c85bc9fabffd0b2ce13e5b39bc71b1dfd71c16709c9638ba2"


def _data():
    return json.loads(FILE.read_text(encoding="utf-8"))


def test_review_is_provisional_and_source_bound():
    data = _data()
    assert data["schema_version"] == "1.0"
    assert data["artifact_type"] == "SOURCE_LINKED_READING_TEXT_REVIEW"
    assert data["exam_id"] == "iran-ce-msc-1396"
    assert data["exam_source"] == {"filename": "96.pdf", "sha256": EXPECTED_SHA}
    assert data["booklet_code"] == "C"
    assert data["review_status"] == "PENDING_INDEPENDENT_REVIEW"
    assert data["review_method"] == "ASSISTANT_DIRECT_VISUAL_COMPARISON"
    assert data["independently_verified"] is False


def test_passage_and_cross_page_question_links_are_not_inferred_from_adjacency():
    mapping = _data()["passage_question_map"]
    assert [item["passage_id"] for item in mapping] == [
        "reading-1",
        "reading-2",
        "reading-3",
    ]
    assert [item["question_number_range"] for item in mapping] == [
        [16, 20],
        [21, 25],
        [26, 30],
    ]
    assert [item["passage_pdf_page"] for item in mapping] == [3, 4, 5]
    expected = {
        number: (3 if number <= 19 else 4 if number <= 24 else 5) for number in range(16, 31)
    }
    observed = {}
    for item in mapping:
        start, stop = item["question_number_range"]
        pages = item["question_pdf_pages"]
        assert set(pages) == {str(number) for number in range(start, stop + 1)}
        observed.update({int(number): page for number, page in pages.items()})
    assert observed == expected
    assert mapping[0]["question_pdf_pages"]["20"] == 4
    assert mapping[1]["question_pdf_pages"]["25"] == 5


def test_short_proposals_have_unique_ids_and_consistent_source_locators():
    data = _data()
    rows = data["proposals"]
    assert len(rows) == 36
    assert Counter(row["passage_id"] for row in rows) == {
        "reading-1": 12,
        "reading-2": 11,
        "reading-3": 13,
    }
    ids = [row["id"] for row in rows]
    assert len(ids) == len(set(ids))
    fields = {
        "passage_body",
        "passage_heading",
        "question_stem",
        "number_marker",
        "choice_text:1",
        "choice_text:4",
    }
    expected_keys = {
        "id",
        "passage_id",
        "target_entity_id",
        "field",
        "source_pdf_page",
        "expected_raw_fragment",
        "proposed_printed_fragment",
        "reason",
        "review_status",
    }
    for row in rows:
        assert set(row) == expected_keys
        assert row["field"] in fields
        assert row["source_pdf_page"] in (3, 4, 5)
        assert row["review_status"] == "PENDING_INDEPENDENT_REVIEW"
        original = row["expected_raw_fragment"]
        suggested = row["proposed_printed_fragment"]
        assert isinstance(original, str) and 0 < len(original) < 50
        assert isinstance(suggested, str) and 0 < len(suggested) < 50
        assert suggested != original
        if row["target_entity_id"].startswith("q-"):
            number = int(row["target_entity_id"][2:])
            assert 16 <= number <= 30
            actual_passage = 1 if number <= 20 else 2 if number <= 25 else 3
            assert row["passage_id"] == f"reading-{actual_passage}"
            assert row["source_pdf_page"] == (3 if number <= 19 else 4 if number <= 24 else 5)
        else:
            assert row["target_entity_id"] == row["passage_id"]
            assert row["source_pdf_page"] == int(row["passage_id"][-1]) + 2
    locations = [
        (row["passage_id"], row["target_entity_id"], row["field"], row["expected_raw_fragment"])
        for row in rows
    ]
    assert len(locations) == len(set(locations))


def test_known_readings_and_nonlocal_anomalies_remain_distinct():
    data = _data()
    pairs = {
        (row["expected_raw_fragment"], row["proposed_printed_fragment"])
        for row in data["proposals"]
    }
    assert ("IWO technical systems", "two technical systems") in pairs
    assert ("self-contnine<l", "self-contained") in pairs
    assert ("rest their performance", "test their performance") in pairs

    anomalies = data["unresolved_anomalies"]
    assert len(anomalies) == 5
    assert len({item["id"] for item in anomalies}) == 5
    assert {item["kind"] for item in anomalies} <= {
        "NONLOCAL_TEXT_ORDER",
        "STRAY_OR_MISORDERED_GLYPH",
    }
    for item in anomalies:
        assert item["status"] == "NEEDS_SOURCE_ALIGNED_REVIEW"
        assert item["proposed_replacement"] is None
        assert item["source_pdf_page"] in (3, 4, 5)
    assert len(data["printed_source_anomalies"]) == 4
    printed = {item["printed_fragment"] for item in data["printed_source_anomalies"]}
    assert "format of the fixture" in printed
    assert "walk thorough the rooms" in printed
    assert "fight training" in printed
    assert 'The work "self-contained"' in printed
    assert not any("final_verified" in row for row in data["proposals"])
