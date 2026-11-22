"""Fail-closed geometric cell-lattice proposals for 1392–1394 answer-key media.

This module never recognizes digits, choices or official answers. Individual
cell rectangles exist only in memory; batch JSON exposes counts/region bounds.
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
from english_exam.visual_grid_batch import MAX_FILE_BYTES, MAX_PDF_PAGES, MAX_PIXELS, RENDER_DPI
from english_exam.visual_grid_regions import (
    YEARS,
    RegionCandidate,
    _centers,
    _intersects,
    _runs,
    detect_regions,
)

MAX_BOUNDARIES = 100
MAX_CELLS = 5000
MIN_CELL_SIDE = 6
BOUNDARY_TOLERANCE = 3


@dataclass(frozen=True, slots=True)
class CellRectangle:
    """In-memory pixel rectangle only; never include this in batch metadata."""

    row_index: int
    column_index: int
    bbox_px: tuple[int, int, int, int]


@dataclass(frozen=True, slots=True)
class CellLattice:
    """In-memory candidate. Neither question numbers nor answers are implied."""

    region_bbox_px: tuple[int, int, int, int]
    row_boundaries_px: tuple[int, ...]
    column_boundaries_px: tuple[int, ...]
    cells: tuple[CellRectangle, ...]


@dataclass(frozen=True, slots=True)
class RegionCellSummary:
    region_index: int
    bbox_px: tuple[int, int, int, int]
    status: str
    row_count: int
    column_count: int
    cell_count: int


@dataclass(frozen=True, slots=True)
class PageCellSummary:
    page_number: int
    width_px: int
    height_px: int
    status: str
    region_status: str
    regions: tuple[RegionCellSummary, ...]


@dataclass(frozen=True, slots=True)
class YearCellSummary:
    year: int
    source_filename: str | None
    source_status: str
    source_sha256: str | None
    status: str
    pages: tuple[PageCellSummary, ...]
    flags: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CellBatch:
    schema_version: str
    family: str
    status: str
    years: tuple[YearCellSummary, ...]
    candidate_years: int
    exceptions: int


def _matches_outer_edges(
    bounds: tuple[int, ...], first: int, last: int
) -> bool:
    return bool(bounds) and abs(bounds[0] - first) <= BOUNDARY_TOLERANCE and abs(
        bounds[-1] - last
    ) <= BOUNDARY_TOLERANCE


def _valid_spacing(bounds: tuple[int, ...]) -> bool:
    return 4 <= len(bounds) <= MAX_BOUNDARIES and all(
        right - left >= MIN_CELL_SIDE + 2 for left, right in zip(bounds, bounds[1:])
    )


def propose_cell_lattice(image: Image.Image, region: RegionCandidate) -> CellLattice | None:
    """Require complete, distinct horizontal/vertical rules within one region.

    Existing region geometry is only a hint. This independent strict check
    requires fully spanning lines, all crossings and positive-size cells.
    """
    width, height = image.size
    if width < 96 or height < 96 or width * height > MAX_PIXELS:
        return None
    left, top, right, bottom = region.bbox_px
    if not (0 <= left < right < width and 0 <= top < bottom < height):
        return None
    ink = image.convert("L").point(lambda value: 1 if value <= 90 else 0).tobytes()
    horizontal = _runs(ink, width, height, rows=True)
    vertical = _runs(ink, width, height, rows=False)
    if horizontal is None or vertical is None:
        return None
    ys = _centers(
        {
            y
            for y, begin, end in horizontal
            if top - BOUNDARY_TOLERANCE <= y <= bottom + BOUNDARY_TOLERANCE
            and begin <= left + BOUNDARY_TOLERANCE
            and end >= right - BOUNDARY_TOLERANCE
        }
    )
    xs = _centers(
        {
            x
            for x, begin, end in vertical
            if left - BOUNDARY_TOLERANCE <= x <= right + BOUNDARY_TOLERANCE
            and begin <= top + BOUNDARY_TOLERANCE
            and end >= bottom - BOUNDARY_TOLERANCE
        }
    )
    if ys is None or xs is None or not _valid_spacing(ys) or not _valid_spacing(xs):
        return None
    if not _matches_outer_edges(xs, left, right) or not _matches_outer_edges(
        ys, top, bottom
    ):
        return None
    if len(ys) != region.horizontal_rules or len(xs) != region.vertical_rules:
        return None
    if (len(ys) - 1) * (len(xs) - 1) > MAX_CELLS:
        return None
    if not all(_intersects(ink, width, height, x, y) for x in xs for y in ys):
        return None

    cells = tuple(
        CellRectangle(
            row,
            col,
            (x0 + 1, y0 + 1, x1 - 1, y1 - 1),
        )
        for row, (y0, y1) in enumerate(zip(ys, ys[1:]))
        for col, (x0, x1) in enumerate(zip(xs, xs[1:]))
    )
    return CellLattice(region.bbox_px, ys, xs, cells)


def inspect_page_cells(image: Image.Image, *, page_number: int = 1) -> PageCellSummary:
    """Publish only region bounds and counts; no in-memory cells or pixels."""
    regions = detect_regions(image, page_number=page_number)
    if regions.status in (
        "RASTER_BOUNDS_UNSUPPORTED",
        "RULE_COMPLEXITY_LIMIT",
        "REGION_COUNT_AMBIGUOUS",
        "REGION_OVERLAP_AMBIGUOUS",
    ):
        return PageCellSummary(
            page_number, regions.width_px, regions.height_px,
            "REGION_GEOMETRY_UNRESOLVED", regions.status, (),
        )
    summaries = []
    for index, region in enumerate(regions.regions):
        lattice = propose_cell_lattice(image, region)
        summaries.append(
            RegionCellSummary(
                index,
                region.bbox_px,
                "UNVERIFIED_CELL_LATTICE" if lattice else "INCOMPLETE_CELL_LATTICE",
                len(lattice.row_boundaries_px) - 1 if lattice else 0,
                len(lattice.column_boundaries_px) - 1 if lattice else 0,
                len(lattice.cells) if lattice else 0,
            )
        )
    accepted = sum(item.status == "UNVERIFIED_CELL_LATTICE" for item in summaries)
    if accepted and accepted == len(summaries):
        status = "UNVERIFIED_CELL_LATTICES_PER_REGION"
    elif accepted:
        status = "PARTIAL_CELL_LATTICES"
    else:
        status = "NO_COMPLETE_CELL_LATTICE"
    return PageCellSummary(
        page_number, regions.width_px, regions.height_px, status,
        regions.status, tuple(summaries),
    )


def _source_error(
    source: SourceObservation, status: str, flags: tuple[str, ...]
) -> YearCellSummary:
    return YearCellSummary(
        source.year, source.filename, source.status, source.actual_sha256,
        status, (), flags,
    )


def _inspect_source(path: Path, source: SourceObservation) -> YearCellSummary:
    flags = [
        "ASSISTANT_PROVISIONAL_GEOMETRY",
        "NO_CELL_PIXELS_OR_ANSWER_VALUES",
        "BOOKLET_UNASSIGNED",
        "KEY_EDITION_UNASSIGNED",
    ]
    if source.expected_sha256 is None:
        flags.append("SOURCE_HASH_UNPINNED")
    pages = []
    try:
        if path.stat().st_size > MAX_FILE_BYTES:
            return _source_error(source, "SOURCE_BOUNDS_UNSUPPORTED", tuple(flags + ["FILE_LIMIT"]))
        if source.media_kind == "JPEG":
            with Image.open(path) as raster:
                if raster.format != "JPEG" or raster.width * raster.height > MAX_PIXELS:
                    return _source_error(
                        source, "SOURCE_BOUNDS_UNSUPPORTED", tuple(flags + ["JPEG_PIXEL_LIMIT"])
                    )
                raster.load()
                pages.append(inspect_page_cells(raster))
        elif source.media_kind == "PDF":
            with pdfplumber.open(path) as pdf:
                if not 1 <= len(pdf.pages) <= MAX_PDF_PAGES:
                    return _source_error(
                        source, "SOURCE_BOUNDS_UNSUPPORTED", tuple(flags + ["PDF_PAGE_LIMIT"])
                    )
                for page_number, page in enumerate(pdf.pages, start=1):
                    predicted = round(page.width * RENDER_DPI / 72) * round(
                        page.height * RENDER_DPI / 72
                    )
                    if predicted < 1 or predicted > MAX_PIXELS:
                        return _source_error(
                            source, "SOURCE_BOUNDS_UNSUPPORTED", tuple(flags + ["PDF_PIXEL_LIMIT"])
                        )
                    raster = page.to_image(resolution=RENDER_DPI, antialias=False).original
                    pages.append(inspect_page_cells(raster, page_number=page_number))
        else:
            return _source_error(source, "MEDIA_UNSUPPORTED", tuple(flags + ["MEDIA_KIND"]))
    except (
        OSError,
        ValueError,
        TypeError,
        RuntimeError,
        PDFException,
        Image.DecompressionBombError,
    ):
        return _source_error(
            source, "SOURCE_PARSE_FAILED", tuple(flags + ["SOURCE_RASTERIZATION_FAILED"])
        )

    if len(pages) > 1:
        flags.append("MULTIPAGE_CONTINUATION_UNRESOLVED")
    if any(page.status == "REGION_GEOMETRY_UNRESOLVED" for page in pages):
        status = "CELL_GEOMETRY_UNRESOLVED"
    else:
        valid = sum(page.status == "UNVERIFIED_CELL_LATTICES_PER_REGION" for page in pages)
        if valid == len(pages):
            status = "UNVERIFIED_CELL_LATTICES_PER_PAGE"
        elif valid:
            status = "PARTIAL_UNVERIFIED_CELL_LATTICES"
        else:
            status = "NO_COMPLETE_CELL_LATTICE"
    return YearCellSummary(
        source.year, source.filename, source.status, source.actual_sha256,
        status, tuple(pages), tuple(flags),
    )


def process_cell_family(source_dir: Path) -> CellBatch:
    keys = {item.year: item.key for item in inventory_sources(source_dir).years}
    years = []
    for year in YEARS:
        source = keys[year]
        if (
            source.status not in ("LOCAL_SOURCE_PINNED", "LOCAL_SOURCE_UNPINNED")
            or not source.filename
        ):
            years.append(
                _source_error(source, "SOURCE_NOT_READY", (source.exception or source.status,))
            )
        else:
            years.append(_inspect_source(source_dir / source.filename, source))
    accepted = sum(
        row.status in ("UNVERIFIED_CELL_LATTICES_PER_PAGE", "PARTIAL_UNVERIFIED_CELL_LATTICES")
        for row in years
    )
    return CellBatch(
        "1.0", "RENDERED_KEY_CELL_LATTICE", "BATCH_DIAGNOSTICS_ONLY",
        tuple(years), accepted, len(years) - accepted,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Metadata-only unverified cell lattice probe")
    parser.add_argument("--source-dir", type=Path, default=Path("source"))
    args = parser.parse_args()
    print(json.dumps(asdict(process_cell_family(args.source_dir)), sort_keys=True, indent=2))
    return 0  # Status of a report is not source verification or answer correctness.


if __name__ == "__main__":
    raise SystemExit(main())
