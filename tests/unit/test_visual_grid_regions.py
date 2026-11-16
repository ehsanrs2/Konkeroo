"""Source-independent geometry-only tests for disconnected ruled regions."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace

import pytest
from PIL import Image, ImageDraw

from english_exam import visual_grid_regions as module
from english_exam.batch_inventory import SourceObservation


def source(year: int, status: str = "LOCAL_SOURCE_UNPINNED") -> SourceObservation:
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


def draw_grid(image: Image.Image, left: int, top: int, right: int, bottom: int) -> None:
    draw = ImageDraw.Draw(image)
    cols = [left + i * (right - left) // 6 for i in range(7)]
    rows = [top + i * (bottom - top) // 8 for i in range(9)]
    for x in cols:
        draw.line((x, top, x, bottom), fill="black", width=2)
    for y in rows:
        draw.line((left, y, right, y), fill="black", width=2)


def two_grids() -> Image.Image:
    image = Image.new("RGB", (700, 340), "white")
    draw_grid(image, 35, 35, 295, 275)
    draw_grid(image, 405, 35, 665, 275)
    return image


def test_disconnected_grids_get_two_sorted_regions() -> None:
    report = module.detect_regions(two_grids(), page_number=3)
    assert report.status == "MULTIPLE_UNVERIFIED_REGIONS"
    assert report.page_number == 3
    assert len(report.regions) == 2
    assert all(r.horizontal_rules == 9 and r.vertical_rules == 7 for r in report.regions)
    assert 25 < report.regions[0].bbox_px[0] < 45
    assert 395 < report.regions[1].bbox_px[0] < 415
    assert report.regions[0].bbox_px[2] < report.regions[1].bbox_px[0]
    assert not hasattr(report, "answer_positions")


def test_single_region_and_blank_and_horizontal_only() -> None:
    single = Image.new("RGB", (340, 300), "white")
    draw_grid(single, 40, 35, 300, 275)
    assert module.detect_regions(single).status == "SINGLE_UNVERIFIED_REGION"
    blank = Image.new("RGB", (340, 300), "white")
    assert module.detect_regions(blank).status == "NO_STRICT_RULED_REGION"
    draw = ImageDraw.Draw(blank)
    for y in range(30, 280, 30):
        draw.line((20, y, 320, y), fill="black", width=2)
    assert module.detect_regions(blank).regions == ()


def test_small_images_and_rule_budget_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    assert module.detect_regions(Image.new("RGB", (50, 50))).status == ("RASTER_BOUNDS_UNSUPPORTED")
    monkeypatch.setattr(module, "MAX_RULE_SEGMENTS", 5)
    report = module.detect_regions(two_grids())
    assert report.status == "RULE_COMPLEXITY_LIMIT"
    assert report.regions == ()


def test_actual_compressed_jpeg_is_decoded_without_text(tmp_path: Path) -> None:
    path = tmp_path / "94-key.jpg"
    two_grids().save(path, "JPEG", quality=95, subsampling=0)
    result = module._inspect_source(path, source(1394))
    assert result.status == "UNVERIFIED_REGIONS_PER_PAGE"
    assert len(result.pages[0].regions) == 2
    assert "SOURCE_HASH_UNPINNED" in result.flags
    as_json = json.dumps(asdict(result))
    for secret in ("answer_positions", "official_answer", "raw_text", "cell_crop"):
        assert secret not in as_json


def test_corrupt_media_rejected(tmp_path: Path) -> None:
    path = tmp_path / "94-key.jpg"
    path.write_bytes(bytes.fromhex("ffd8ffc000"))
    report = module._inspect_source(path, source(1394))
    assert report.status == "RENDER_OR_DECODE_FAILED"
    assert report.pages == ()


def test_multipage_not_joined(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    class FakePage:
        width = 340
        height = 300

        def __init__(self, img: Image.Image):
            self.img = img

        def to_image(self, **_kwargs: object) -> SimpleNamespace:
            return SimpleNamespace(original=self.img)

    class FakePdf:
        def __init__(self):
            self.pages = [FakePage(two_grids()), FakePage(Image.new("RGB", (340, 300)))]

        def __enter__(self):
            return self

        def __exit__(self, *_args: object):
            return False

    monkeypatch.setattr(module.pdfplumber, "open", lambda _path: FakePdf())
    path = tmp_path / "93_key.pdf"
    path.write_bytes(b"%PDF-1.7")
    report = module._inspect_source(path, source(1393))
    assert report.status == "PARTIAL_UNVERIFIED_REGIONS"
    assert report.pages[0].status == "MULTIPLE_UNVERIFIED_REGIONS"
    assert report.pages[1].status == "NO_STRICT_RULED_REGION"
    assert "MULTIPAGE_CONTINUATION_UNRESOLVED" in report.flags


def test_pdf_pixel_limit_prior_to_render(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    class HugePage:
        width = 50_000
        height = 50_000

        def to_image(self, **_kwargs: object) -> None:
            pytest.fail("unbounded render attempted")

    class FakePdf:
        def __init__(self):
            self.pages = [HugePage()]

        def __enter__(self):
            return self

        def __exit__(self, *_args: object):
            return False

    monkeypatch.setattr(module.pdfplumber, "open", lambda _path: FakePdf())
    path = tmp_path / "92_key.pdf"
    path.write_bytes(b"%PDF-1.7")
    report = module._inspect_source(path, source(1392))
    assert report.status == "SOURCE_BOUNDS_UNSUPPORTED"
    assert "PDF_PIXEL_LIMIT" in report.flags


def test_unavailable_source_isolation(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    entries = {
        1392: source(1392, "LFS_POINTER_ONLY"),
        1393: source(1393, "SOURCE_HASH_MISMATCH"),
        1394: source(1394),
    }
    monkeypatch.setattr(
        module,
        "inventory_sources",
        lambda _root: SimpleNamespace(
            years=[SimpleNamespace(year=y, key=src) for y, src in entries.items()]
        ),
    )
    monkeypatch.setattr(
        module,
        "_inspect_source",
        lambda _path, src: module.YearRegions(
            src.year,
            src.filename,
            src.status,
            src.actual_sha256,
            "UNVERIFIED_REGIONS_PER_PAGE",
            (),
            ("NO_CELL_OR_ANSWER_DECODING",),
        ),
    )
    report = module.process_region_family(tmp_path)
    assert [row.status for row in report.years] == [
        "SOURCE_NOT_READY",
        "SOURCE_NOT_READY",
        "UNVERIFIED_REGIONS_PER_PAGE",
    ]
    assert report.candidate_years == 1
    assert report.years[0].flags == ("LFS_POINTER_ONLY",)
    assert report.years[1].flags == ("SOURCE_HASH_MISMATCH",)
