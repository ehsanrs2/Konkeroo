"""Structural checks for visually curated 1396 Cloze editorial proposals.

These checks protect scope and review status. They cannot independently confirm
the visual correctness of proposed text changes.
"""

import json
from collections import Counter
from pathlib import Path

FILE = Path(__file__).parents[2] / "dataset" / "review" / "1396-cloze-text-review.json"
SOURCE_SHA256 = "69bc3434ae61c05c85bc9fabffd0b2ce13e5b39bc71b1dfd71c16709c9638ba2"


def _review():
    return json.loads(FILE.read_text(encoding="utf-8"))


def test_identity_scope_and_no_implicit_promotion():
    data = _review()
    assert data["schema_version"] == "1.0"
    assert data["artifact_type"] == "SOURCE_LINKED_CLOZE_TEXT_REVIEW"
    assert data["exam_id"] == "iran-ce-msc-1396"
    assert data["source"] == {"filename": "96.pdf", "sha256": SOURCE_SHA256}
    assert data["review_status"] == "PENDING_INDEPENDENT_REVIEW"
    assert data["method"] == "ASSISTANT_DIRECT_VISUAL_COMPARISON"
    assert data["independently_verified"] is False
    assert data["scope"] == {
        "section": "CLOZE",
        "question_numbers": [11, 12, 13, 14, 15],
        "passage_id": "cloze-1",
        "printed_passage_pdf_page": 2,
        "question_choices_pdf_page": 3,
    }


def test_each_short_edit_has_a_unique_field_and_page_locator():
    edits = _review()["proposals"]
    assert len(edits) == 7
    ids = [row["id"] for row in edits]
    assert len(ids) == len(set(ids))
    assert all(
        set(row)
        == {
            "id",
            "entity_id",
            "field",
            "pdf_page",
            "expected_raw_fragment",
            "proposed_replacement",
            "reason",
            "proposal_status",
        }
        for row in edits
    )
    assert all(row["proposal_status"] == "PENDING_INDEPENDENT_REVIEW" for row in edits)
    assert all(
        isinstance(row["expected_raw_fragment"], str)
        and 0 < len(row["expected_raw_fragment"]) < 40
        and isinstance(row["proposed_replacement"], str)
        and 0 < len(row["proposed_replacement"]) < 40
        and row["expected_raw_fragment"] != row["proposed_replacement"]
        for row in edits
    )
    assert all(row["pdf_page"] == (3 if row["entity_id"].startswith("q-") else 2) for row in edits)
    assert {row["entity_id"] for row in edits} == {"cloze", "cloze-1", "q-13", "q-15"}
    assert len(
        {(row["entity_id"], row["field"], row["expected_raw_fragment"]) for row in edits}
    ) == len(edits)
    assert not any("corrected_text" in row or "final_verified" in row for row in edits)


def test_visual_proposals_only_record_the_relevant_source_fragments():
    by_id = {row["id"]: row for row in _review()["proposals"]}
    assert (
        by_id["cloze-human"]["expected_raw_fragment"],
        by_id["cloze-human"]["proposed_replacement"],
    ) == ("Imm an", "human")
    assert (
        by_id["cloze-13-choice4"]["expected_raw_fragment"],
        by_id["cloze-13-choice4"]["proposed_replacement"],
    ) == ("rakes", "takes")
    assert (
        by_id["cloze-15-marker"]["expected_raw_fragment"],
        by_id["cloze-15-marker"]["proposed_replacement"],
    ) == ("t 5-", "15-")


def test_displaced_word_is_marked_unresolved_not_autocorrected():
    data = _review()
    anomalies = data["unresolved_anomalies"]
    assert len(anomalies) == 1
    anomaly = anomalies[0]
    assert anomaly["kind"] == "NONLOCAL_TEXT_ORDER"
    assert anomaly["status"] == "NEEDS_SOURCE_ALIGNED_REVIEW"
    assert anomaly["proposed_replacement"] is None
    assert anomaly["printed_phrase"] == "ability to remember"
    assert "10" in anomaly["observed_raw_fragments"]
    assert not any(row["id"] == anomaly["id"] for row in data["proposals"])


def test_no_duplicate_raw_snippets_within_same_target():
    rows = _review()["proposals"]
    key_counts = Counter(
        (row["entity_id"], row["field"], row["expected_raw_fragment"]) for row in rows
    )
    assert max(key_counts.values(), default=0) == 1
