"""Bounded line-grid *geometry* candidates for 1392–1394 rendered keys.

No OCR, cell decoding, answer positions, or candidate/official attribution.
An apparent ruled grid is not evidence of a correct or complete answer key.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import pdfplumber
from pdfminer.pdfexceptions import PDFException
from PIL import Image

from english_exam.batch_inventory import SourceObservation, inventory_sources

YEARS = (1392, 1393, 1394)
RENDER_DPI = 100
MAX_PDF_PAGES = 6
MAX_PIXELS = 6_000_000
MAX_FILE_BYTES = 30_000_000
MAX_LINE_CANDIDATES = 250


@dataclass(frozen=True, slots=True)
class PageGeometry:
    page_number: int
    width_px: int
    height_px: int
    row_rules: int
    column_rules: int
    grid_bbox_px: tuple[int, int, int, int] | None
    status: str


@dataclass(frozen=True, slots=True)
class YearGeometry:
    year: int
    filename: str | None
    source_status: str
    source_sha256: str | None
    status: str
    pages: tuple[PageGeometry, ...]
    flags: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class GeometryBatch:
    schema_version: str
    family: str
    status: str
    years: tuple[YearGeometry, ...]
    candidate_years: int
    exceptions: int


def _line_centers(counts: list[int], threshold: int) -> tuple[int, ...]:
    """Coalesce adjacent high-ink projection rows into single thin rules."""
    selected = [i for i, count in enumerate(counts) if count >= threshold]
    groups: list[list[int]] = []
    for position in selected:
        if not groups or position != groups[-1][-1] + 1:
            groups.append([position])
        else:
            groups[-1].append(position)
    return tuple(group[len(group) // 2] for group in groups if len(group) <= 12)


def _ink_projection(mask: Image.Image) -> list[int]:
    raw = mask.tobytes()
    width, height = mask.size
    return [raw[y * width : (y + 1) * width].count(1) for y in range(height)]


def detect_line_grid(image: Image.Image, *, page_number: int = 1) -> PageGeometry:
    """Inspect strict, intersecting full-row/full-column dark rules only.

    Global projections intentionally do not segment multiple tables or infer
    actual cell ownership. Every match remains explicitly unverified.
    """
    width, height = image.size
    if width < 96 or height < 96 or width * height > MAX_PIXELS:
        return PageGeometry(page_number, width, height, 0, 0, None, "RASTER_BOUNDS_UNSUPPORTED")
    grayscale = image.convert("L")
    ink = grayscale.point(lambda value: 1 if value <= 90 else 0)
    row_rules = _line_centers(_ink_projection(ink), max(2, int(width * 0.38)))
    col_rules = _line_centers(
        _ink_projection(ink.transpose(Image.Transpose.TRANSPOSE)),
        max(2, int(height * 0.25)),
    )
    if (
        not 4 <= len(row_rules) <= MAX_LINE_CANDIDATES
        or not 4 <= len(col_rules) <= MAX_LINE_CANDIDATES
    ):
        return PageGeometry(
            page_number,
            width,
            height,
            len(row_rules),
            len(col_rules),
            None,
            "NO_STRICT_INTERSECTING_RULE_GRID",
        )
    left, right = col_rules[0], col_rules[-1]
    top, bottom = row_rules[0], row_rules[-1]
    if right - left < width * 0.15 or bottom - top < height * 0.10:
        return PageGeometry(
            page_number,
            width,
            height,
            len(row_rules),
            len(col_rules),
            None,
            "NO_STRICT_INTERSECTING_RULE_GRID",
        )
    # Require most candidate ruled intersections to be present, tolerating
    # one-pixel registration offset but never making a semantic cell claim.
    hits = sum(
        any(
            ink.getpixel((x + dx, y + dy)) == 1
            for dx in (-1, 0, 1)
            for dy in (-1, 0, 1)
            if 0 <= x + dx < width and 0 <= y + dy < height
        )
        for x in col_rules
        for y in row_rules
    )
    if hits * 5 < len(row_rules) * len(col_rules) * 4:
        return PageGeometry(
            page_number,
            width,
            height,
            len(row_rules),
            len(col_rules),
            None,
            "NO_STRICT_INTERSECTING_RULE_GRID",
        )
    return PageGeometry(
        page_number,
        width,
        height,
        len(row_rules),
        len(col_rules),
        (left, top, right, bottom),
        "UNVERIFIED_LINE_GRID_CANDIDATE",
    )


def _inspect_source(path: Path, observed: SourceObservation) -> YearGeometry:
    flags = ["BOOKLET_UNASSIGNED", "KEY_EDITION_UNASSIGNED", "NO_ANSWER_DECODING"]
    if observed.expected_sha256 is None:
        flags.append("SOURCE_HASH_UNPINNED")
    pages: list[PageGeometry] = []
    try:
        if path.stat().st_size > MAX_FILE_BYTES:
            return YearGeometry(
                observed.year,
                observed.filename,
                observed.status,
                observed.actual_sha256,
                "SOURCE_BOUNDS_UNSUPPORTED",
                (),
                tuple(flags + ["FILE_SIZE_LIMIT"]),
            )
        if observed.media_kind == "JPEG":
            with Image.open(path) as raster:
                if raster.format != "JPEG" or raster.width * raster.height > MAX_PIXELS:
                    raise ValueError("JPEG format or pixel bound")
                raster.load()  # Unlike SOF header triage, require decodable pixels.
                pages.append(detect_line_grid(raster, page_number=1))
        elif observed.media_kind == "PDF":
            with pdfplumber.open(path) as pdf:
                if not 1 <= len(pdf.pages) <= MAX_PDF_PAGES:
                    return YearGeometry(
                        observed.year,
                        observed.filename,
                        observed.status,
                        observed.actual_sha256,
                        "SOURCE_BOUNDS_UNSUPPORTED",
                        (),
                        tuple(flags + ["PAGE_COUNT_LIMIT"]),
                    )
                for page_number, page in enumerate(pdf.pages, start=1):
                    predicted = round(page.width * RENDER_DPI / 72) * round(
                        page.height * RENDER_DPI / 72
                    )
                    if predicted > MAX_PIXELS or predicted < 1:
                        return YearGeometry(
                            observed.year,
                            observed.filename,
                            observed.status,
                            observed.actual_sha256,
                            "SOURCE_BOUNDS_UNSUPPORTED",
                            (),
                            tuple(flags + ["PDF_RENDER_PIXEL_LIMIT"]),
                        )
                    raster = page.to_image(resolution=RENDER_DPI, antialias=False).original
                    pages.append(detect_line_grid(raster, page_number=page_number))
        else:
            return YearGeometry(
                observed.year,
                observed.filename,
                observed.status,
                observed.actual_sha256,
                "MEDIA_UNSUPPORTED",
                (),
                tuple(flags + ["UNEXPECTED_MEDIA_KIND"]),
            )
    except (
        OSError,
        ValueError,
        PDFException,
        TypeError,
        RuntimeError,
        Image.DecompressionBombError,
    ):
        return YearGeometry(
            observed.year,
            observed.filename,
            observed.status,
            observed.actual_sha256,
            "RENDER_OR_DECODE_FAILED",
            (),
            tuple(flags + ["SOURCE_RASTERIZATION_FAILED"]),
        )

    if len(pages) > 1:
        flags.append("MULTIPAGE_CONTINUATION_UNRESOLVED")
    flags.append("GLOBAL_PROJECTION_UNSEGMENTED")
    candidates = sum(page.status == "UNVERIFIED_LINE_GRID_CANDIDATE" for page in pages)
    if candidates and candidates == len(pages):
        status = "UNVERIFIED_GEOMETRY_CANDIDATES"
    elif candidates:
        status = "PARTIAL_GEOMETRY_CANDIDATES"
    else:
        status = "NO_STRICT_LINE_GRID"
    return YearGeometry(
        observed.year,
        observed.filename,
        observed.status,
        observed.actual_sha256,
        status,
        tuple(pages),
        tuple(flags),
    )


def process_visual_grid_family(source_dir: Path) -> GeometryBatch:
    by_year = {row.year: row.key for row in inventory_sources(source_dir).years}
    results = []
    for year in YEARS:
        source = by_year[year]
        if not source.status.startswith("LOCAL_SOURCE_") or not source.filename:
            results.append(
                YearGeometry(
                    year,
                    source.filename,
                    source.status,
                    source.actual_sha256,
                    "SOURCE_NOT_READY",
                    (),
                    (source.exception or source.status,),
                )
            )
        else:
            results.append(_inspect_source(source_dir / source.filename, source))
    candidates = sum(
        row.status in ("UNVERIFIED_GEOMETRY_CANDIDATES", "PARTIAL_GEOMETRY_CANDIDATES")
        for row in results
    )
    return GeometryBatch(
        "1.0",
        "RENDERED_GRID_LINE_GEOMETRY",
        "BATCH_DIAGNOSTICS_ONLY",
        tuple(results),
        candidates,
        len(results) - candidates,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only rendered-key line geometry probe")
    parser.add_argument("--source-dir", type=Path, default=Path("source"))
    args = parser.parse_args()
    print(json.dumps(asdict(process_visual_grid_family(args.source_dir)), sort_keys=True, indent=2))
    return 0  # Diagnostic report success is NOT an original-source or answer validation.


if __name__ == "__main__":
    raise SystemExit(main())
