"""No-answer, source-independent tests for page morphology profiling."""

from __future__ import annotations

import json
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace

import pytest
from PIL import Image, ImageDraw

from english_exam import rendered_layout_profile as module
from english_exam.batch_inventory import KEY_RENDERED_LFS_SHA, SourceObservation


def _source(year: int, media_kind: str = "JPEG") -> SourceObservation:
    return SourceObservation(
        year=year,
        role="OFFICIAL_KEY",
        filename="94-key.jpg" if media_kind == "JPEG" else "92_key.pdf",
        media_kind=media_kind,
        family="RENDERED_GRID",
        status="LOCAL_SOURCE_PINNED",
        actual_sha256="e" * 64,
        expected_sha256="e" * 64,
        lfs_oid_sha256=None,
        exception=None,
    )


def _lines(shade: int = 30) -> Image.Image:
    image = Image.new("RGB", (340, 260), "white")
    draw = ImageDraw.Draw(image)
    for y in range(30, 231, 25):
        draw.line((30, y, 310, y), fill=(shade, shade, shade), width=2)
    for x in range(30, 311, 40):
        draw.line((x, 30, x, 230), fill=(shade, shade, shade), width=2)
    return image


def test_blank_page_is_not_mistaken_for_a_readable_grid() -> None:
    page = module.profile_page(Image.new("RGB", (340, 260), "white"), page_number=2)
    assert page.page_number == 2
    assert page.status == "PAGE_STATISTICS_OBSERVED"
    assert all(level.dark_percent == 0 for level in page.thresholds)
    assert all(level.horizontal_long_runs == 0 for level in page.thresholds)
    assert all(level.vertical_long_runs == 0 for level in page.thresholds)
    assert not hasattr(page, "answers")


def test_threshold_profile_separates_dark_and_faint_rules() -> None:
    dark = module.profile_page(_lines(30))
    faint = module.profile_page(_lines(150))
    assert dark.thresholds[0].dark_percent > 0
    assert dark.thresholds[0].horizontal_long_runs > 0
    assert dark.thresholds[0].vertical_long_runs > 0
    assert faint.thresholds[0].dark_percent == 0
    assert faint.thresholds[1].dark_percent > 0
    assert faint.thresholds[1].horizontal_long_runs > 0
    assert faint.thresholds[1].vertical_long_runs > 0
    assert faint.thresholds[1].longest_horizontal_run_px >= 200


def test_small_raster_fails_closed() -> None:
    page = module.profile_page(Image.new("RGB", (70, 70)))
    assert page.status == "RASTER_BOUNDS_UNSUPPORTED"
    assert page.thresholds == ()


def test_jpeg_is_read_and_serializes_only_statistics(tmp_path: Path) -> None:
    path = tmp_path / "94-key.jpg"
    _lines().save(path, "JPEG", quality=95, subsampling=0)
    row = module._profile_source(path, _source(1394))
    assert row.status == "PAGE_STATISTICS_OBSERVED"
    assert len(row.pages) == 1
    assert row.pages[0].width_px == 340
    assert row.pages[0].pdf_text_layer_char_count is None
    assert row.pages[0].thresholds[0].horizontal_long_runs > 0
    payload = json.dumps(asdict(row))
    for forbidden in (
        "ocr", "answers", "answer_positions", "raw_text", "row_boundaries_px",
        "column_boundaries_px", "cell_crop", "final_verified",
    ):
        assert forbidden not in payload


def test_malformed_jpeg_does_not_create_page_observations(tmp_path: Path) -> None:
    path = tmp_path / "94-key.jpg"
    path.write_bytes(bytes.fromhex("ffd8ffc000"))
    result = module._profile_source(path, _source(1394))
    assert result.status == "SOURCE_PROFILE_FAILED"
    assert result.pages == ()


def test_pdf_page_counts_without_text_value_leakage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    class FakePage:
        width = 340
        height = 260

        def __init__(self, picture: Image.Image, chars: list[dict]) -> None:
            self.picture = picture
            self.chars = chars
            self.lines = [{"line": 1}, {"line": 2}]
            self.images = [{"image": 1}]

        def to_image(self, **_kwargs: object) -> SimpleNamespace:
            return SimpleNamespace(original=self.picture)

    class FakePdf:
        def __init__(self) -> None:
            self.pages = [
                FakePage(_lines(), [{"text": "DO_NOT_LEAK"}, {"text": "secret"}]),
                FakePage(Image.new("RGB", (340, 260), "white"), []),
            ]

        def __enter__(self):
            return self

        def __exit__(self, *_args: object) -> bool:
            return False

    monkeypatch.setattr(module.pdfplumber, "open", lambda _path: FakePdf())
    path = tmp_path / "92_key.pdf"
    path.write_bytes(b"%PDF-1.7")
    year = module._profile_source(path, _source(1392, "PDF"))
    assert year.status == "PAGE_STATISTICS_OBSERVED"
    assert len(year.pages) == 2
    assert [page.pdf_text_layer_char_count for page in year.pages] == [2, 0]
    assert [page.pdf_vector_line_count for page in year.pages] == [2, 2]
    assert [page.pdf_embedded_image_count for page in year.pages] == [1, 1]
    assert "MULTIPAGE_CONTINUATION_UNRESOLVED" in year.flags
    assert "DO_NOT_LEAK" not in json.dumps(asdict(year))
    assert "secret" not in json.dumps(asdict(year))


def test_pdf_bounds_block_rasterization(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    class TooLargePage:
        width = 120_000
        height = 120_000

        def to_image(self, **_kwargs: object) -> None:
            pytest.fail("must not rasterize out-of-bounds PDF")

    class FakePdf:
        def __init__(self) -> None:
            self.pages = [TooLargePage()]

        def __enter__(self):
            return self

        def __exit__(self, *_args: object) -> bool:
            return False

    monkeypatch.setattr(module.pdfplumber, "open", lambda _path: FakePdf())
    path = tmp_path / "92_key.pdf"
    path.write_bytes(b"%PDF-1.7")
    year = module._profile_source(path, _source(1392, "PDF"))
    assert year.status == "MEDIA_BOUNDS_UNSUPPORTED"
    assert year.pages == ()


def test_only_exact_lfs_matched_source_is_profiled(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "94-key.jpg"
    _lines().save(path, "JPEG", quality=95, subsampling=0)
    expected_sha = sha256(path.read_bytes()).hexdigest()
    monkeypatch.setitem(KEY_RENDERED_LFS_SHA, 1394, expected_sha)
    (tmp_path / "92_key.pdf").write_text(
        "version https://git-lfs.github.com/spec/v1\n"
        f"oid sha256:{KEY_RENDERED_LFS_SHA[1392]}\nsize 260186\n"
    )
    (tmp_path / "93_key.pdf").write_bytes(b"%PDF-1.7\nincorrect bytes\n")
    result = module.profile_rendered_family(tmp_path)
    assert result.sources_pinned == 1
    assert result.profiled_pages == 1
    assert [item.status for item in result.years] == [
        "SOURCE_NOT_READY", "SOURCE_NOT_READY", "PAGE_STATISTICS_OBSERVED"
    ]
    assert [item.source_status for item in result.years] == [
        "LFS_POINTER_ONLY", "SOURCE_HASH_MISMATCH", "LOCAL_SOURCE_PINNED"
    ]


def test_cli_failure_for_missing_originals(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert module.main(["--source-dir", str(tmp_path), "--require-sources"]) == 2
    report = json.loads(capsys.readouterr().out)
    assert report["sources_pinned"] == 0
    assert report["profiled_pages"] == 0
    assert report["status"] == "OBSERVATIONS_ONLY_NOT_VERIFIED"
