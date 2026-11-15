"""Optional real-media check for the native key *family* in one source run.

GitHub CI normally contains LFS pointers or missing originals; that is a skip,
not evidence of native family extraction against actual PDF content.
"""

import json
from dataclasses import asdict
from pathlib import Path

import pytest

from english_exam.batch_inventory import inventory_sources
from english_exam.native_key_batch import NATIVE_YEARS, process_native_family

ROOT = Path(__file__).parents[2]
SOURCE = ROOT / "source"
pytestmark = pytest.mark.source_pdf


def test_native_family_source_run_preserves_1395_gold_and_routes_other_sources():
    inventory = inventory_sources(SOURCE)
    by_year = {year.year: year for year in inventory.years}
    if by_year[1395].key.status != "LOCAL_SOURCE_PINNED":
        pytest.skip("real SHA-bound 1395 key source absent; LFS pointer is not PDF media")

    report = process_native_family(SOURCE)
    results = {row.year: row for row in report.years}
    assert tuple(results) == NATIVE_YEARS
    assert results[1395].status == "SOURCE_STAGE_VALIDATED"
    assert results[1395].candidate_questions == 121
    assert results[1395].flags == ()
    assert results[1395].source_sha256 == by_year[1395].key.actual_sha256

    for year in (1401, 1402, 1404):
        row = results[year]
        observed = by_year[year].key
        assert row.source_status == observed.status
        assert row.source_sha256 == observed.actual_sha256
        if observed.can_attempt_key:
            assert row.status in (
                "ASSISTANT_PROVISIONAL_GRID",
                "NO_UNIQUE_NATIVE_GRID",
                "SOURCE_PARSE_FAILED",
                "SOURCE_LAYOUT_UNSUPPORTED",
            )
        else:
            assert row.status == "SOURCE_NOT_READY"
        if row.status == "ASSISTANT_PROVISIONAL_GRID":
            assert "BOOKLET_UNASSIGNED" in row.flags
            assert "KEY_EDITION_UNASSIGNED" in row.flags

    metadata = json.dumps(asdict(report))
    assert "answer_positions" not in metadata
    assert "question_numbers" not in metadata
    assert "final_verified" not in metadata
