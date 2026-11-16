"""Synthetic and source-independent tests for unverified line-grid geometry."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace

import pytest
from PIL import Image, ImageDraw

from english_exam import visual_grid_batch as module
from english_exam.batch_inventory import SourceObservation


def _source(year: int, status: str = "LOCAL_SOURCE_UNPINNED") -> SourceObservation:
    return SourceObservation(
        year=year,
        role="OFFICIAL_KEY",
        filename={1392: "92_key.pdf", 1393: "93_key.pdf", 1394: "94-key.jpg"}[year],
        media_kind="JPEG" if year == 1394 else "PDF",
        family="RENDERED_GRID",
        status=status,
        actual_sha256="a" * 64 if status.startswith("LOCAL_SOURCE_") else None,
        expected_sha256=None,
        lfs_oid_sha256=None,
        exception=None if status.startswith("LOCAL_SOURCE_") else status,
    )


def _grid() -> Image.Image:
    image = Image.new("RGB", (320, 240), "white")
    draw = ImageDraw.Draw(image)
    for x in range(40, 281, 40):
        draw.line((x, 30, x, 210), fill="black", width=2)
    for y in range(30, 211, 20):
        draw.line((40, y, 280, y), fill="black", width=2)
    return image


def test_strict_grid_is_geometry_only() -> None:
    result = module.detect_line_grid(_grid(), page_number=2)
    assert result.status == "UNVERIFIED_LINE_GRID_CANDIDATE"
    assert result.page_number == 2
    assert result.row_rules == 10
    assert result.column_rules == 7
    assert result.grid_bbox_px is not None
    assert 35 <= result.grid_bbox_px[0] <= 45
    assert 275 <= result.grid_bbox_px[2] <= 285
    assert not hasattr(result, "answers")


def test_blank_and_unintersecting_rules_fail_closed() -> None:
    blank = Image.new("RGB", (320, 240), "white")
    assert module.detect_line_grid(blank).status == "NO_STRICT_INTERSECTING_RULE_GRID"
    draw = ImageDraw.Draw(blank)
    for y in range(20, 220, 20):
        draw.line((20, y, 300, y), fill="black", width=2)
    assert module.detect_line_grid(blank).grid_bbox_px is None


def test_pixel_bound_is_checked_before_decoding() -> None:
    tiny = Image.new("RGB", (80, 80))
    assert module.detect_line_grid(tiny).status == "RASTER_BOUNDS_UNSUPPORTED"


def test_jpeg_actual_pixels_and_provisional_metadata(tmp_path: Path) -> None:
    path = tmp_path / "94-key.jpg"
    _grid().save(path, "JPEG", quality=95, subsampling=0)
    result = module._inspect_source(path, _source(1394))
    assert result.status == "UNVERIFIED_GEOMETRY_CANDIDATES"
    assert result.pages[0].grid_bbox_px is not None
    assert "SOURCE_HASH_UNPINNED" in result.flags
    assert "NO_ANSWER_DECODING" in result.flags
    report = json.dumps(asdict(result))
    assert "answer_positions" not in report
    assert "official_answer" not in report


def test_corrupted_jpeg_is_not_a_candidate(tmp_path: Path) -> None:
    path = tmp_path / "94-key.jpg"
    path.write_bytes(b"\xff\xd8\xff\xc0\x00")
    result = module._inspect_source(path, _source(1394))
    assert result.status == "RENDER_OR_DECODE_FAILED"
    assert result.pages == ()


def test_pdf_pages_remain_independent_and_unjoined(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    class Page:
        width = 320
        height = 240

        def __init__(self, image: Image.Image):
            self.image = image

        def to_image(self, **_kwargs: object) -> SimpleNamespace:
            return SimpleNamespace(original=self.image)

    class Pdf:
        def __init__(self) -> None:
            self.pages = [Page(_grid()), Page(Image.new("RGB", (320, 240), "white"))]

        def __enter__(self):
            return self

        def __exit__(self, *_args: object) -> bool:
            return False

    monkeypatch.setattr(module.pdfplumber, "open", lambda _path: Pdf())
    path = tmp_path / "93_key.pdf"
    path.write_bytes(b"%PDF-1.7")
    result = module._inspect_source(path, _source(1393))
    assert result.status == "PARTIAL_GEOMETRY_CANDIDATES"
    assert len(result.pages) == 2
    assert "MULTIPAGE_CONTINUATION_UNRESOLVED" in result.flags
    assert result.pages[1].grid_bbox_px is None


def test_pdf_render_limit_skips_rendering(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    class HugePage:
        width = 100_000
        height = 100_000

        def to_image(self, **_kwargs: object) -> None:
            pytest.fail("must not rasterize over limit")

    class Pdf:
        def __init__(self) -> None:
            self.pages = [HugePage()]

        def __enter__(self):
            return self

        def __exit__(self, *_args: object) -> bool:
            return False

    monkeypatch.setattr(module.pdfplumber, "open", lambda _path: Pdf())
    path = tmp_path / "92_key.pdf"
    path.write_bytes(b"%PDF-1.7")
    result = module._inspect_source(path, _source(1392))
    assert result.status == "SOURCE_BOUNDS_UNSUPPORTED"
    assert "PDF_RENDER_PIXEL_LIMIT" in result.flags


def test_pointer_and_per_year_isolation(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    sources = {
        1392: _source(1392, "LFS_POINTER_ONLY"),
        1393: _source(1393),
        1394: _source(1394),
    }
    monkeypatch.setattr(
        module,
        "inventory_sources",
        lambda _root: SimpleNamespace(
            years=[SimpleNamespace(year=year, key=source) for year, source in sources.items()]
        ),
    )
    monkeypatch.setattr(
        module,
        "_inspect_source",
        lambda _path, source: module.YearGeometry(
            source.year, source.filename, source.status, source.actual_sha256,
            "NO_STRICT_LINE_GRID", (), ("NO_ANSWER_DECODING",),
        ),
    )
    result = module.process_visual_grid_family(tmp_path)
    assert [row.status for row in result.years] == [
        "SOURCE_NOT_READY", "NO_STRICT_LINE_GRID", "NO_STRICT_LINE_GRID"
    ]
    assert result.years[0].flags == ("LFS_POINTER_ONLY",)
    assert result.candidate_years == 0
