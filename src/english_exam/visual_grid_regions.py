"""Bounded *region* candidates for 1392–1394 rendered keys.

Geometry only: no cells, OCR, answer positions or answer authority. A ruled
rectangle does not prove that the contents are an answer-key grid.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path

import pdfplumber
from pdfminer.pdfexceptions import PDFException
from PIL import Image

from english_exam.batch_inventory import SourceObservation, inventory_sources
from english_exam.visual_grid_batch import MAX_FILE_BYTES, MAX_PDF_PAGES, MAX_PIXELS, RENDER_DPI

YEARS = (1392, 1393, 1394)
MAX_RULE_SEGMENTS = 600
MAX_REGIONS = 8
MIN_RULES = 4


@dataclass(frozen=True, slots=True)
class RegionCandidate:
    """Pixel geometry, not extracted cells or decoded answers."""

    bbox_px: tuple[int, int, int, int]
    horizontal_rules: int
    vertical_rules: int


@dataclass(frozen=True, slots=True)
class PageRegions:
    page_number: int
    width_px: int
    height_px: int
    status: str
    regions: tuple[RegionCandidate, ...]
    rejected_components: int


@dataclass(frozen=True, slots=True)
class YearRegions:
    year: int
    source_filename: str | None
    source_status: str
    source_sha256: str | None
    status: str
    pages: tuple[PageRegions, ...]
    flags: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RegionBatch:
    schema_version: str
    family: str
    status: str
    years: tuple[YearRegions, ...]
    candidate_years: int
    exceptions: int


def _runs(data: bytes, width: int, height: int, *, rows: bool) -> list[tuple[int, int, int]] | None:
    """Long orthogonal dark runs or None on complexity overflow.

    Each triple is (fixed coordinate, first pixel, last pixel), inclusive.
    """
    threshold = max(24, (width if rows else height) // 12)
    lines: list[tuple[int, int, int]] = []
    major, minor = (height, width) if rows else (width, height)
    for fixed in range(major):
        start = -1
        for offset in range(minor + 1):
            dark = offset < minor and bool(
                data[fixed * width + offset] if rows else data[offset * width + fixed]
            )
            if dark and start == -1:
                start = offset
            elif not dark and start != -1:
                if offset - start >= threshold:
                    lines.append((fixed, start, offset - 1))
                    if len(lines) > MAX_RULE_SEGMENTS:
                        return None
                start = -1
    return lines


def _centers(values: set[int]) -> tuple[int, ...] | None:
    """Merge adjacent thin ink runs; reject thick blocks."""
    if not values:
        return ()
    ordered = sorted(values)
    groups: list[list[int]] = [[ordered[0]]]
    for value in ordered[1:]:
        if value == groups[-1][-1] + 1:
            groups[-1].append(value)
        else:
            groups.append([value])
    if any(len(group) > 12 for group in groups):
        return None
    return tuple(group[len(group) // 2] for group in groups)


def _intersects(ink: bytes, width: int, height: int, x: int, y: int) -> bool:
    return any(
        ink[(y + dy) * width + (x + dx)]
        for dy in (-1, 0, 1)
        for dx in (-1, 0, 1)
        if 0 <= x + dx < width and 0 <= y + dy < height
    )


def _overlap(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> bool:
    return max(a[0], b[0]) <= min(a[2], b[2]) and max(a[1], b[1]) <= min(a[3], b[3])


def detect_regions(image: Image.Image, *, page_number: int = 1) -> PageRegions:
    """Detect disconnected ruled-line components in one bounded raster.

    Only intersecting long horizontal and vertical runs participate. Too
    many or overlapping candidates fail closed; no semantic cell claims.
    """
    width, height = image.size
    if width < 96 or height < 96 or width * height > MAX_PIXELS:
        return PageRegions(page_number, width, height, "RASTER_BOUNDS_UNSUPPORTED", (), 0)
    ink = image.convert("L").point(lambda v: 1 if v <= 90 else 0).tobytes()
    horizontal = _runs(ink, width, height, rows=True)
    vertical = _runs(ink, width, height, rows=False)
    if horizontal is None or vertical is None:
        return PageRegions(page_number, width, height, "RULE_COMPLEXITY_LIMIT", (), 0)
    h_count = len(horizontal)
    parent = list(range(h_count + len(vertical)))

    def root(value: int) -> int:
        while parent[value] != value:
            parent[value] = parent[parent[value]]
            value = parent[value]
        return value

    def unite(a: int, b: int) -> None:
        ra, rb = root(a), root(b)
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)

    crossing: list[tuple[int, int]] = []
    for hi, (y, x_start, x_end) in enumerate(horizontal):
        for vi, (x, y_start, y_end) in enumerate(vertical):
            if x_start - 1 <= x <= x_end + 1 and y_start - 1 <= y <= y_end + 1:
                unite(hi, h_count + vi)
                crossing.append((hi, vi))

    components: dict[int, tuple[set[int], set[int]]] = defaultdict(lambda: (set(), set()))
    for hi, vi in crossing:
        hs, vs = components[root(hi)]
        hs.add(hi)
        vs.add(vi)

    candidates: list[RegionCandidate] = []
    rejected = 0
    for hs, vs in components.values():
        xs = _centers({vertical[index][0] for index in vs})
        ys = _centers({horizontal[index][0] for index in hs})
        if xs is None or ys is None or len(xs) < MIN_RULES or len(ys) < MIN_RULES:
            rejected += 1
            continue
        x0, x1, y0, y1 = xs[0], xs[-1], ys[0], ys[-1]
        if x1 - x0 < max(32, width // 14) or y1 - y0 < max(32, height // 14):
            rejected += 1
            continue
        hits = sum(_intersects(ink, width, height, x, y) for x in xs for y in ys)
        if hits * 5 < len(xs) * len(ys) * 4:
            rejected += 1
            continue
        candidates.append(RegionCandidate((x0, y0, x1, y1), len(ys), len(xs)))

    candidates.sort(key=lambda c: (c.bbox_px[1], c.bbox_px[0], c.bbox_px))
    if len(candidates) > MAX_REGIONS:
        return PageRegions(page_number, width, height, "REGION_COUNT_AMBIGUOUS", (), rejected)
    if any(
        _overlap(first.bbox_px, second.bbox_px)
        for i, first in enumerate(candidates)
        for second in candidates[i + 1 :]
    ):
        return PageRegions(page_number, width, height, "REGION_OVERLAP_AMBIGUOUS", (), rejected)
    status = (
        "MULTIPLE_UNVERIFIED_REGIONS"
        if len(candidates) > 1
        else "SINGLE_UNVERIFIED_REGION"
        if candidates
        else "NO_STRICT_RULED_REGION"
    )
    return PageRegions(page_number, width, height, status, tuple(candidates), rejected)


def _source_error(source: SourceObservation, status: str, flags: tuple[str, ...]) -> YearRegions:
    return YearRegions(
        source.year, source.filename, source.status, source.actual_sha256, status, (), flags
    )


def _inspect_source(path: Path, source: SourceObservation) -> YearRegions:
    flags = ["UNVERIFIED_GEOMETRY_ONLY", "NO_CELL_OR_ANSWER_DECODING", "BOOKLET_UNASSIGNED"]
    if source.expected_sha256 is None:
        flags.append("SOURCE_HASH_UNPINNED")
    pages: list[PageRegions] = []
    try:
        if path.stat().st_size > MAX_FILE_BYTES:
            return _source_error(source, "SOURCE_BOUNDS_UNSUPPORTED", tuple(flags + ["FILE_LIMIT"]))
        if source.media_kind == "JPEG":
            with Image.open(path) as raster:
                if raster.format != "JPEG" or raster.width * raster.height > MAX_PIXELS:
                    return _source_error(
                        source, "SOURCE_BOUNDS_UNSUPPORTED", tuple(flags + ["JPEG_BOUNDS"])
                    )
                raster.load()
                pages.append(detect_regions(raster))
        elif source.media_kind == "PDF":
            with pdfplumber.open(path) as pdf:
                if not 1 <= len(pdf.pages) <= MAX_PDF_PAGES:
                    return _source_error(
                        source, "SOURCE_BOUNDS_UNSUPPORTED", tuple(flags + ["PDF_PAGE_LIMIT"])
                    )
                for index, page in enumerate(pdf.pages, start=1):
                    predicted = round(page.width * RENDER_DPI / 72) * round(
                        page.height * RENDER_DPI / 72
                    )
                    if predicted < 1 or predicted > MAX_PIXELS:
                        return _source_error(
                            source, "SOURCE_BOUNDS_UNSUPPORTED", tuple(flags + ["PDF_PIXEL_LIMIT"])
                        )
                    raster = page.to_image(resolution=RENDER_DPI, antialias=False).original
                    pages.append(detect_regions(raster, page_number=index))
        else:
            return _source_error(source, "MEDIA_UNSUPPORTED", tuple(flags + ["MEDIA_KIND"]))
    except (
        OSError,
        ValueError,
        PDFException,
        TypeError,
        RuntimeError,
        Image.DecompressionBombError,
    ):
        return _source_error(
            source, "RENDER_OR_DECODE_FAILED", tuple(flags + ["SOURCE_RASTERIZATION_FAILED"])
        )
    if len(pages) > 1:
        flags.append("MULTIPAGE_CONTINUATION_UNRESOLVED")
    if any(
        page.status
        in (
            "RULE_COMPLEXITY_LIMIT",
            "REGION_COUNT_AMBIGUOUS",
            "REGION_OVERLAP_AMBIGUOUS",
        )
        for page in pages
    ):
        status = "REGION_AMBIGUITY_UNRESOLVED"
    else:
        hits = sum(bool(page.regions) for page in pages)
        if hits == len(pages):
            status = "UNVERIFIED_REGIONS_PER_PAGE"
        elif hits:
            status = "PARTIAL_UNVERIFIED_REGIONS"
        else:
            status = "NO_STRICT_RULED_REGION"
    return YearRegions(
        source.year,
        source.filename,
        source.status,
        source.actual_sha256,
        status,
        tuple(pages),
        tuple(flags),
    )


def process_region_family(source_dir: Path) -> RegionBatch:
    keys = {row.year: row.key for row in inventory_sources(source_dir).years}
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
    candidate_years = sum(
        row.status in ("UNVERIFIED_REGIONS_PER_PAGE", "PARTIAL_UNVERIFIED_REGIONS") for row in years
    )
    return RegionBatch(
        "1.0",
        "RENDERED_KEY_REGION_GEOMETRY",
        "BATCH_DIAGNOSTICS_ONLY",
        tuple(years),
        candidate_years,
        len(years) - candidate_years,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only per-region key geometry (no decoding)")
    parser.add_argument("--source-dir", type=Path, default=Path("source"))
    args = parser.parse_args()
    print(json.dumps(asdict(process_region_family(args.source_dir)), sort_keys=True, indent=2))
    return 0  # Report generation does not prove real-source coverage or answer validity.


if __name__ == "__main__":
    raise SystemExit(main())
