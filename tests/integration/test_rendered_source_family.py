"""Optional exact-source rendered-key family diagnostic.

A public Git checkout normally contains LFS pointers, not the original bytes.
SKIP is not source acceptance; classified geometry is not answer correctness.
"""

import json
from dataclasses import asdict
from pathlib import Path

import pytest

from english_exam.batch_inventory import KEY_RENDERED_LFS_SHA, inventory_sources
from english_exam.rendered_source_acceptance import audit_rendered_sources

SOURCE = Path(__file__).parents[2] / "source"
pytestmark = pytest.mark.source_pdf


def test_original_rendered_key_family_source_diagnostic():
    sources = {item.year: item.key for item in inventory_sources(SOURCE).years}
    available = [
        year for year in (1392, 1393, 1394)
        if sources[year].status == "LOCAL_SOURCE_PINNED"
    ]
    if not available:
        pytest.skip("No actual SHA-matched rendered key media; pointers are not PDFs/JPEGs")

    report = audit_rendered_sources(SOURCE)
    rows = {item.year: item for item in report.years}
    assert report.sources_pinned == len(available)
    assert tuple(rows) == (1392, 1393, 1394)

    for year, row in rows.items():
        assert row.expected_repo_lfs_sha256 == KEY_RENDERED_LFS_SHA[year]
        assert row.source_status == sources[year].status
        assert row.observed_sha256 == sources[year].actual_sha256
        assert row.status != "STAGE_EVIDENCE_CONFLICT"
        if year not in available:
            assert row.status == "SOURCE_NOT_READY"
            assert row.pages == ()
            continue
        assert row.identity_scope == "REPOSITORY_LFS_OBJECT_ONLY"
        assert row.observed_sha256 == KEY_RENDERED_LFS_SHA[year]
        assert row.status in (
            "PROVISIONAL_GEOMETRY_OBSERVED",
            "SOURCE_PRESENT_GEOMETRY_UNRESOLVED",
        )
        if year == 1393 and len(row.pages) > 1:
            assert "MULTIPAGE_CONTINUATION_UNRESOLVED" in row.flags

    serialized = json.dumps(asdict(report))
    for forbidden in (
        "answer_positions", "official_answer", "raw_text",
        "row_boundaries_px", "column_boundaries_px", "final_verified",
    ):
        assert forbidden not in serialized
