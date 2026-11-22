"""Synthetic source-identity/geometry acceptance checks without source contents."""

from __future__ import annotations

import json
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path

import pytest
from PIL import Image, ImageDraw

from english_exam.batch_inventory import KEY_RENDERED_LFS_SHA
from english_exam.rendered_source_acceptance import (
    RENDERED_YEARS,
    audit_rendered_sources,
    main,
)


def _make_two_grids() -> Image.Image:
    image = Image.new("RGB", (700, 340), "white")
    draw = ImageDraw.Draw(image)
    for left, right in ((35, 295), (405, 665)):
        for column in range(7):
            x = left + (right - left) * column // 6
            draw.line((x, 35, x, 275), fill="black", width=2)
        for row in range(9):
            y = 35 + 240 * row // 8
            draw.line((left, y, right, y), fill="black", width=2)
    return image


def test_pointer_missing_and_mismatch_have_no_false_source_success(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "92_key.pdf").write_text(
        "version https://git-lfs.github.com/spec/v1\\n"
        f"oid sha256:{KEY_RENDERED_LFS_SHA[1392]}\\nsize 260186\\n"
    )
    (tmp_path / "93_key.pdf").write_bytes(b"%PDF-1.7\\nwrong original bytes\\n")
    report = audit_rendered_sources(tmp_path)
    rows = {item.year: item for item in report.years}
    assert rows[1392].source_status == "LFS_POINTER_ONLY"
    assert rows[1393].source_status == "SOURCE_HASH_MISMATCH"
    assert rows[1394].source_status == "SOURCE_MISSING"
    assert report.sources_pinned == 0
    assert report.provisional_geometry_years == 0
    assert report.exceptions == 3
    assert report.status == "DIAGNOSTICS_INCOMPLETE"
    assert all(item.status == "SOURCE_NOT_READY" for item in report.years)
    assert all(item.pages == () for item in report.years)
    assert main(["--source-dir", str(tmp_path), "--require-sources"]) == 2
    assert json.loads(capsys.readouterr().out)["sources_pinned"] == 0
    assert main(["--source-dir", str(tmp_path), "--require-provisional-geometry"]) == 3


def test_exact_sha_pinned_synthetic_jpeg_reports_geometry_not_answers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "94-key.jpg"
    _make_two_grids().save(path, "JPEG", quality=95, subsampling=0)
    fake_sha = sha256(path.read_bytes()).hexdigest()
    monkeypatch.setitem(KEY_RENDERED_LFS_SHA, 1394, fake_sha)

    report = audit_rendered_sources(tmp_path)
    assert report.sources_pinned == 1
    rows = {item.year: item for item in report.years}
    row = rows[1394]
    assert row.source_status == "LOCAL_SOURCE_PINNED"
    assert row.observed_sha256 == fake_sha
    assert row.identity_scope == "REPOSITORY_LFS_OBJECT_ONLY"
    assert row.status == "PROVISIONAL_GEOMETRY_OBSERVED"
    assert row.media_status == "MEDIA_TRIAGED_VISUAL_MAPPING_PENDING"
    assert len(row.pages) == 1
    assert row.pages[0].candidate_regions == 2
    assert row.pages[0].cell_lattices == 2
    assert row.pages[0].incomplete_lattices == 0
    assert row.flags == ("NO_OFFICIAL_ANSWER_VALIDATION",)

    metadata = json.dumps(asdict(report), sort_keys=True)
    for forbidden in (
        "answer_positions",
        "official_answer",
        "raw_text",
        "row_boundaries_px",
        "column_boundaries_px",
        "CellRectangle",
        "final_verified",
    ):
        assert forbidden not in metadata
    assert report.status == "DIAGNOSTICS_INCOMPLETE"


def test_cli_requires_all_originals_even_if_one_synthetic_jpeg_passes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "94-key.jpg"
    _make_two_grids().save(path, "JPEG", quality=95, subsampling=0)
    monkeypatch.setitem(KEY_RENDERED_LFS_SHA, 1394, sha256(path.read_bytes()).hexdigest())
    assert main(["--source-dir", str(tmp_path)]) == 0
    assert main(["--source-dir", str(tmp_path), "--require-sources"]) == 2
    assert main(["--source-dir", str(tmp_path), "--require-provisional-geometry"]) == 3
    assert "PROVISIONAL_GEOMETRY_OBSERVED" in capsys.readouterr().out


def test_expected_source_contract_is_three_distinct_lfs_objects() -> None:
    assert RENDERED_YEARS == (1392, 1393, 1394)
    assert len(set(KEY_RENDERED_LFS_SHA.values())) == len(RENDERED_YEARS)
    assert all(len(sha) == 64 for sha in KEY_RENDERED_LFS_SHA.values())
