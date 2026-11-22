"""Geometry-only cell lattice tests; no copyrighted answer contents."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace

import pytest
from PIL import Image, ImageDraw

from english_exam import visual_grid_cells as module
from english_exam.batch_inventory import SourceObservation
from english_exam.visual_grid_regions import RegionCandidate, detect_regions


def _source(year: int, status: str = "LOCAL_SOURCE_UNPINNED") -> SourceObservation:
    return SourceObservation(
        year=year,
        role="OFFICIAL_KEY",
        filename={1392: "92_key.pdf", 1393: "93_key.pdf", 1394: "94-key.jpg"}[year],
        media_kind="JPEG" if year == 1394 else "PDF",
        family="RENDERED_GRID",
        status=status,
        actual_sha256="f" * 64 if status.startswith("LOCAL_SOURCE_") else None,
        expected_sha256=None,
        lfs_oid_sha256=None,
        exception=None if status.startswith("LOCAL_SOURCE_") else status,
    )


def _draw_grid(
    image: Image.Image,
    left: int,
    top: int,
    right: int,
    bottom: int,
    *,
    missing_vertical: int | None = None,
) -> None:
    draw = ImageDraw.Draw(image)
    for col in range(7):
        if col == missing_vertical:
            continue
        x = left + col * (right - left) // 6
        draw.line((x, top, x, bottom), fill="black", width=2)
    for row in range(9):
        y = top + row * (bottom - top) // 8
        draw.line((left, y, right, y), fill="black", width=2)


def _image(*, missing_vertical: int | None = None) -> Image.Image:
    image = Image.new("RGB", (700, 340), "white")
    _draw_grid(image, 35, 35, 295, 275, missing_vertical=missing_vertical)
    _draw_grid(image, 405, 35, 665, 275)
    return image


def test_two_disjoint_cell_lattices_and_ordered_in_memory_cells() -> None:
    image = _image()
    candidates = detect_regions(image).regions
    assert len(candidates) == 2
    first = module.propose_cell_lattice(image, candidates[0])
    second = module.propose_cell_lattice(image, candidates[1])
    assert first is not None and second is not None
    assert len(first.row_boundaries_px) == 9
    assert len(first.column_boundaries_px) == 7
    assert len(first.cells) == len(second.cells) == 48
    assert [(c.row_index, c.column_index) for c in first.cells[:7]] == [
        (0, 0),
        (0, 1),
        (0, 2),
        (0, 3),
        (0, 4),
        (0, 5),
        (1, 0),
    ]
    assert first.cells[0].bbox_px[2] < first.cells[1].bbox_px[0]
    assert first.cells[0].bbox_px[3] < first.cells[6].bbox_px[1]
    summary = module.inspect_page_cells(image, page_number=3)
    assert summary.page_number == 3
    assert summary.region_status == "MULTIPLE_UNVERIFIED_REGIONS"
    assert summary.status == "UNVERIFIED_CELL_LATTICES_PER_REGION"
    assert [(item.row_count, item.column_count, item.cell_count) for item in summary.regions] == [
        (8, 6, 48),
        (8, 6, 48),
    ]
    public = json.dumps(asdict(summary), sort_keys=True)
    for forbidden in ("cells", "row_boundaries_px", "column_boundaries_px", "answer"):
        assert forbidden not in public


def test_missing_interior_separator_fails_closed() -> None:
    image = _image(missing_vertical=3)
    report = module.inspect_page_cells(image)
    assert report.status == "PARTIAL_CELL_LATTICES"
    assert [r.status for r in report.regions] == [
        "INCOMPLETE_CELL_LATTICE",
        "UNVERIFIED_CELL_LATTICE",
    ]
    assert report.regions[0].cell_count == 0


def test_blank_textlike_and_small_images_do_not_create_cells() -> None:
    image = Image.new("RGB", (300, 250), "white")
    assert module.inspect_page_cells(image).status == "NO_COMPLETE_CELL_LATTICE"
    draw = ImageDraw.Draw(image)
    for y in range(15, 240, 20):
        draw.line((10, y, 290, y), fill="black", width=2)
    assert module.inspect_page_cells(image).regions == ()
    assert module.inspect_page_cells(Image.new("RGB", (70, 70))).status == (
        "REGION_GEOMETRY_UNRESOLVED"
    )


def test_invalid_bbox_rejected_before_reconstruction() -> None:
    source = _image()
    bad_region = RegionCandidate((-1, 0, 15, 50), 8, 6)
    assert module.propose_cell_lattice(source, bad_region) is None


def test_real_compressed_jpeg_still_yields_metadata_only(tmp_path: Path) -> None:
    path = tmp_path / "94-key.jpg"
    _image().save(path, "JPEG", quality=95, subsampling=0)
    result = module._inspect_source(path, _source(1394))
    assert result.status == "UNVERIFIED_CELL_LATTICES_PER_PAGE"
    assert [region.cell_count for region in result.pages[0].regions] == [48, 48]
    assert "SOURCE_HASH_UNPINNED" in result.flags
    assert "NO_CELL_PIXELS_OR_ANSWER_VALUES" in result.flags
    assert "cell_crop" not in json.dumps(asdict(result))


def test_bad_jpeg_returns_failure_not_empty_verified_grid(tmp_path: Path) -> None:
    path = tmp_path / "94-key.jpg"
    path.write_bytes(bytes.fromhex("ffd8ffc000"))
    result = module._inspect_source(path, _source(1394))
    assert result.status == "SOURCE_PARSE_FAILED"
    assert result.pages == ()


def test_multipage_source_remains_separate(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    class Page:
        width = 700
        height = 340

        def __init__(self, picture: Image.Image) -> None:
            self.picture = picture

        def to_image(self, **_kwargs: object) -> SimpleNamespace:
            return SimpleNamespace(original=self.picture)

    class Pdf:
        def __init__(self) -> None:
            self.pages = [Page(_image()), Page(Image.new("RGB", (700, 340), "white"))]

        def __enter__(self):
            return self

        def __exit__(self, *_args: object) -> bool:
            return False

    monkeypatch.setattr(module.pdfplumber, "open", lambda _path: Pdf())
    path = tmp_path / "93_key.pdf"
    path.write_bytes(b"%PDF-1.7")
    result = module._inspect_source(path, _source(1393))
    assert result.status == "PARTIAL_UNVERIFIED_CELL_LATTICES"
    assert result.pages[0].status == "UNVERIFIED_CELL_LATTICES_PER_REGION"
    assert result.pages[1].status == "NO_COMPLETE_CELL_LATTICE"
    assert "MULTIPAGE_CONTINUATION_UNRESOLVED" in result.flags


def test_pdf_pixel_limit_blocks_unbounded_render(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    class HugePage:
        width = 60_000
        height = 60_000

        def to_image(self, **_kwargs: object) -> None:
            pytest.fail("unbounded rendering")

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
    assert "PDF_PIXEL_LIMIT" in result.flags


def test_pointer_and_hash_failure_are_not_opened(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    items = {
        1392: _source(1392, "LFS_POINTER_ONLY"),
        1393: _source(1393, "SOURCE_HASH_MISMATCH"),
        1394: _source(1394),
    }
    monkeypatch.setattr(
        module,
        "inventory_sources",
        lambda _root: SimpleNamespace(
            years=[SimpleNamespace(year=year, key=key) for year, key in items.items()]
        ),
    )
    inspected = []

    def fake_scan(_path: Path, key: SourceObservation) -> module.YearCellSummary:
        inspected.append(key.year)
        return module._source_error(
            key, "NO_COMPLETE_CELL_LATTICE", ("NO_CELL_PIXELS_OR_ANSWER_VALUES",)
        )

    monkeypatch.setattr(module, "_inspect_source", fake_scan)
    batch = module.process_cell_family(tmp_path)
    assert inspected == [1394]
    assert [item.status for item in batch.years] == [
        "SOURCE_NOT_READY",
        "SOURCE_NOT_READY",
        "NO_COMPLETE_CELL_LATTICE",
    ]
    assert batch.exceptions == 3
    assert batch.years[0].flags == ("LFS_POINTER_ONLY",)
    assert batch.years[1].flags == ("SOURCE_HASH_MISMATCH",)
