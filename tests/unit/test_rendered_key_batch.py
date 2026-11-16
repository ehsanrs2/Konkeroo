"""Source-independent rendered-family media triage tests."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from english_exam import rendered_key_batch as module
from english_exam.batch_inventory import SourceObservation


def observation(year: int, status: str = "LOCAL_SOURCE_UNPINNED") -> SourceObservation:
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


def test_jpeg_frame_metadata_only(tmp_path: Path) -> None:
    path = tmp_path / "sample.jpg"
    # Minimal segment structure for SOF header testing; not a decodable JPEG.
    path.write_bytes(
        b"\xff\xd8\xff\xe0\x00\x04ab\xff\xc0\x00\x0b\x08\x00\x30\x00\x40\x01\x01\x11\x00\xff\xd9"
    )
    assert module.jpeg_frame_dimensions(path) == (64, 48)
    result = module._inspect(path, observation(1394))
    assert result.status == "MEDIA_TRIAGED_VISUAL_MAPPING_PENDING"
    assert (result.image_width, result.image_height) == (64, 48)
    assert "VISUAL_GRID_UNLOCATED" in result.flags
    assert not hasattr(result, "answer_positions")


@pytest.mark.parametrize(
    "payload",
    [b"not a jpeg", b"\xff\xd8\xff\xc0\x00", b"\xff\xd8\xff\xd9"],
)
def test_bad_jpeg_is_not_promoted(tmp_path: Path, payload: bytes) -> None:
    path = tmp_path / "bad.jpg"
    path.write_bytes(payload)
    result = module._inspect(path, observation(1394))
    assert result.status == "MEDIA_PARSE_FAILED"
    assert result.image_width is None


def test_pdf_page_image_and_text_counts(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    class FakePdf:
        def __init__(self) -> None:
            self.pages = [
                SimpleNamespace(images=[object(), object()], chars=[]),
                SimpleNamespace(images=[], chars=[object()]),
            ]

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(module.pdfplumber, "open", lambda _path: FakePdf())
    result = module._inspect(tmp_path / "dummy.pdf", observation(1392))
    assert result.page_count == 2
    assert result.embedded_image_count == 2
    assert result.text_layer_pages == 1
    assert result.status == "MEDIA_TRIAGED_VISUAL_MAPPING_PENDING"
    assert result.source_sha256 == "f" * 64


def test_lfs_pointer_and_per_year_exception_isolation(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    observations = {
        1392: observation(1392, "LFS_POINTER_ONLY"),
        1393: observation(1393),
        1394: observation(1394),
    }
    monkeypatch.setattr(
        module,
        "inventory_sources",
        lambda _root: SimpleNamespace(
            years=[SimpleNamespace(year=year, key=obs) for year, obs in observations.items()]
        ),
    )
    monkeypatch.setattr(
        module,
        "_inspect",
        lambda _path, observed: module._result(
            observed, "MEDIA_TRIAGED_VISUAL_MAPPING_PENDING", flags=("VISUAL_GRID_UNLOCATED",)
        ),
    )
    report = module.process_rendered_family(tmp_path)
    assert report.media_inspected == 2
    assert report.exceptions == 1
    assert [row.status for row in report.years] == [
        "SOURCE_NOT_READY",
        "MEDIA_TRIAGED_VISUAL_MAPPING_PENDING",
        "MEDIA_TRIAGED_VISUAL_MAPPING_PENDING",
    ]
    assert report.years[0].flags == ("LFS_POINTER_ONLY",)


def test_hash_mismatch_is_not_inspected(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    observations = {
        year: replace(observation(year), status="SOURCE_HASH_MISMATCH", exception="SOURCE_HASH_MISMATCH")
        for year in module.RENDERED_YEARS
    }
    monkeypatch.setattr(
        module,
        "inventory_sources",
        lambda _root: SimpleNamespace(
            years=[SimpleNamespace(year=year, key=obs) for year, obs in observations.items()]
        ),
    )
    monkeypatch.setattr(module, "_inspect", lambda *_args: pytest.fail("must not inspect"))
    report = module.process_rendered_family(tmp_path)
    assert report.media_inspected == 0
    assert report.exceptions == 3
    assert all(row.status == "SOURCE_NOT_READY" for row in report.years)
