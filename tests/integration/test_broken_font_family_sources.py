"""Single optional source-present broken-font family check for 1397–1399.

Public CI normally contains only source/ Git LFS pointers, not real PDFs.
A skipped test is not original-media proof or official key confirmation.
"""

import json
from dataclasses import asdict
from pathlib import Path

import pytest

from english_exam.batch_inventory import KEY_BROKEN_FONT_SHA, inventory_sources
from english_exam.broken_font_batch import BROKEN_FONT_YEARS, process_broken_font_family

ROOT = Path(__file__).parents[2]
SOURCE = ROOT / "source"
pytestmark = pytest.mark.source_pdf


def test_real_broken_font_family_source_coverage_and_no_answer_leakage():
    inventory = inventory_sources(SOURCE)
    observed = {row.year: row.key for row in inventory.years}
    available = tuple(
        year for year in BROKEN_FONT_YEARS if observed[year].status == "LOCAL_SOURCE_PINNED"
    )
    if not available:
        pytest.skip("no original SHA-bound 1397–1399 PDFs; LFS pointers are not media")

    report = process_broken_font_family(SOURCE)
    results = {row.year: row for row in report.years}
    assert tuple(results) == BROKEN_FONT_YEARS
    assert report.source_ready == len(available)
    for year in BROKEN_FONT_YEARS:
        row = results[year]
        key = observed[year]
        assert key.expected_sha256 == KEY_BROKEN_FONT_SHA[year]
        assert row.source_status == key.status
        assert row.source_sha256 == key.actual_sha256
        if year not in available:
            assert row.status == "SOURCE_NOT_READY"
            assert row.candidate_questions == 0
            continue

        # Classification with an actual source is not necessarily successful
        # glyph decoding, which depends on recoverable native table geometry.
        assert row.status in (
            "PAGE_LAYOUT_MISMATCH",
            "SOURCE_PARSE_FAILED",
            "NEEDS_GLYPH_GEOMETRY_FOLLOWUP",
            "ASSISTANT_PROVISIONAL_PARTIAL_GRID",
            "ASSISTANT_PROVISIONAL_GLYPH_GRID",
        )
        if row.status.startswith("ASSISTANT_PROVISIONAL"):
            assert row.candidate_tables == 1
            assert row.candidate_questions >= 20
            assert "UNVERIFIED_Q1_ANCHOR" in row.flags
            assert "BOOKLET_UNASSIGNED" in row.flags
            assert "KEY_EDITION_UNASSIGNED" in row.flags
            if year in (1397, 1398):
                assert row.status == "ASSISTANT_PROVISIONAL_PARTIAL_GRID"
                assert "MULTIPAGE_CONTINUATION_UNRESOLVED" in row.flags

    safe = json.dumps(asdict(report), sort_keys=True)
    assert "question_numbers" not in safe
    assert "answer_positions" not in safe
    assert "glyph_pairs" not in safe
    assert "final_verified" not in safe
