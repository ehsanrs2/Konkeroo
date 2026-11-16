"""Read-only PDF/JPEG media triage for rendered answer-key sources (1392–1394).

This is NOT a visual answer-grid importer. No key positions, images, or text
leave the local source directory; only bounded technical metadata is reported.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import pdfplumber
from pdfminer.pdfexceptions import PDFException

from english_exam.batch_inventory import SourceObservation, inventory_sources

RENDERED_YEARS = (1392, 1393, 1394)
MAX_PDF_PAGES = 20
MAX_JPEG_HEADER_BYTES = 1024 * 1024
SOF_MARKERS = frozenset(
    (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF)
)


@dataclass(frozen=True, slots=True)
class RenderedYearResult:
    year: int
    filename: str | None
    media_kind: str | None
    source_status: str
    source_sha256: str | None
    status: str
    page_count: int | None
    embedded_image_count: int | None
    text_layer_pages: int | None
    image_width: int | None
    image_height: int | None
    flags: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RenderedFamilyBatch:
    schema_version: str
    family: str
    status: str
    years: tuple[RenderedYearResult, ...]
    media_inspected: int
    exceptions: int


def jpeg_frame_dimensions(path: Path) -> tuple[int, int]:
    """Read a JPEG SOF frame header, not a decoded or semantically verified image.

    Never scan unbounded input; a valid JPEG with distant SOF is classified
    as unsupported by this deliberately bounded probe.
    """
    with path.open("rb") as handle:
        data = handle.read(MAX_JPEG_HEADER_BYTES)
    if not data.startswith(b"\xff\xd8"):
        raise ValueError("invalid JPEG SOI")
    offset = 2
    while offset < len(data):
        if data[offset] != 0xFF:
            raise ValueError("invalid JPEG marker boundary")
        while offset < len(data) and data[offset] == 0xFF:
            offset += 1
        if offset >= len(data):
            break
        marker = data[offset]
        offset += 1
        if marker == 0xD9 or marker == 0xDA:
            break
        if marker in (0x01, *range(0xD0, 0xD8)):
            continue
        if offset + 2 > len(data):
            break
        length = int.from_bytes(data[offset : offset + 2], "big")
        if length < 2 or offset + length > len(data):
            break
        if marker in SOF_MARKERS:
            if length < 8:
                break
            height = int.from_bytes(data[offset + 3 : offset + 5], "big")
            width = int.from_bytes(data[offset + 5 : offset + 7], "big")
            if width == 0 or height == 0:
                break
            return width, height
        offset += length
    raise ValueError("no bounded valid JPEG frame header")


def _result(
    observed: SourceObservation,
    status: str,
    *,
    page_count: int | None = None,
    embedded_image_count: int | None = None,
    text_layer_pages: int | None = None,
    image_width: int | None = None,
    image_height: int | None = None,
    flags: tuple[str, ...] = (),
) -> RenderedYearResult:
    return RenderedYearResult(
        year=observed.year,
        filename=observed.filename,
        media_kind=observed.media_kind,
        source_status=observed.status,
        source_sha256=observed.actual_sha256,
        status=status,
        page_count=page_count,
        embedded_image_count=embedded_image_count,
        text_layer_pages=text_layer_pages,
        image_width=image_width,
        image_height=image_height,
        flags=flags,
    )


def _inspect(path: Path, observed: SourceObservation) -> RenderedYearResult:
    identity_flags = ("SOURCE_HASH_UNPINNED",) if observed.expected_sha256 is None else ()
    if observed.media_kind == "JPEG":
        try:
            width, height = jpeg_frame_dimensions(path)
        except (OSError, ValueError):
            return _result(observed, "MEDIA_PARSE_FAILED", flags=("JPEG_FRAME_HEADER_INVALID",))
        return _result(
            observed,
            "MEDIA_TRIAGED_VISUAL_MAPPING_PENDING",
            page_count=1,
            image_width=width,
            image_height=height,
            flags=identity_flags + ("JPEG_HEADER_ONLY", "VISUAL_GRID_UNLOCATED", "BOOKLET_UNASSIGNED"),
        )
    if observed.media_kind != "PDF":
        return _result(observed, "MEDIA_UNSUPPORTED", flags=("UNEXPECTED_MEDIA_KIND",))
    try:
        with pdfplumber.open(path) as pdf:
            count = len(pdf.pages)
            if count < 1 or count > MAX_PDF_PAGES:
                return _result(
                    observed, "MEDIA_UNSUPPORTED", page_count=count, flags=("PAGE_LIMIT",)
                )
            image_count = 0
            text_pages = 0
            for page in pdf.pages:
                image_count += len(page.images)
                text_pages += bool(page.chars)
    except (OSError, PDFException, ValueError, TypeError, RuntimeError, KeyError, IndexError):
        return _result(observed, "MEDIA_PARSE_FAILED", flags=("PDF_MEDIA_INSPECTION_FAILED",))
    return _result(
        observed,
        "MEDIA_TRIAGED_VISUAL_MAPPING_PENDING",
        page_count=count,
        embedded_image_count=image_count,
        text_layer_pages=text_pages,
        flags=identity_flags + ("VISUAL_GRID_UNLOCATED", "BOOKLET_UNASSIGNED"),
    )


def process_rendered_family(source_dir: Path) -> RenderedFamilyBatch:
    inventory = inventory_sources(source_dir)
    keys = {row.year: row.key for row in inventory.years}
    results = []
    for year in RENDERED_YEARS:
        observed = keys[year]
        if not observed.status.startswith("LOCAL_SOURCE_") or not observed.filename:
            results.append(
                _result(observed, "SOURCE_NOT_READY", flags=(observed.exception or observed.status,))
            )
        else:
            results.append(_inspect(source_dir / observed.filename, observed))
    inspected = sum(row.status == "MEDIA_TRIAGED_VISUAL_MAPPING_PENDING" for row in results)
    return RenderedFamilyBatch(
        schema_version="1.0",
        family="RENDERED_GRID",
        status="FAMILY_MEDIA_TRIAGE_COMPLETE_WITH_EXCEPTIONS"
        if inspected != len(RENDERED_YEARS)
        else "FAMILY_MEDIA_TRIAGE_COMPLETE",
        years=tuple(results),
        media_inspected=inspected,
        exceptions=len(RENDERED_YEARS) - inspected,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only rendered-key media metadata triage")
    parser.add_argument("--source-dir", type=Path, default=Path("source"))
    args = parser.parse_args()
    print(json.dumps(asdict(process_rendered_family(args.source_dir)), indent=2, sort_keys=True))
    return 0  # Report generation does not mean any answer is verified.


if __name__ == "__main__":
    raise SystemExit(main())
