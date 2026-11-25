"""Metadata-only page morphology profiler for actual rendered keys (1392–1394).

This deliberately produces NO page content, glyphs, pixel positions, crops,
answer values, OCR, or confidence scores. Source SHA matching means only
repository LFS object identity, never publisher authenticity.
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
from english_exam.visual_grid_regions import YEARS, _runs

THRESHOLDS = (90, 180, 230)


@dataclass(frozen=True, slots=True)
class ThresholdProfile:
    dark_threshold: int
    dark_percent: float
    horizontal_long_runs: int | None
    vertical_long_runs: int | None
    longest_horizontal_run_px: int | None
    longest_vertical_run_px: int | None


@dataclass(frozen=True, slots=True)
class PageMorphology:
    page_number: int
    width_px: int
    height_px: int
    pdf_text_layer_char_count: int | None
    pdf_vector_line_count: int | None
    pdf_embedded_image_count: int | None
    status: str
    thresholds: tuple[ThresholdProfile, ...]


@dataclass(frozen=True, slots=True)
class YearMorphology:
    year: int
    filename: str | None
    source_status: str
    observed_sha256: str | None
    status: str
    pages: tuple[PageMorphology, ...]
    flags: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class MorphologyBatch:
    schema_version: str
    scope: str
    status: str
    sources_pinned: int
    profiled_pages: int
    years: tuple[YearMorphology, ...]


def profile_page(
    image: Image.Image,
    *,
    page_number: int = 1,
    pdf_text_layer_char_count: int | None = None,
    pdf_vector_line_count: int | None = None,
    pdf_embedded_image_count: int | None = None,
) -> PageMorphology:
    """Count only coarse ink/rule statistics; never serialize pixel locations."""
    width, height = image.size
    if width < 96 or height < 96 or width * height > MAX_PIXELS:
        return PageMorphology(
            page_number, width, height, pdf_text_layer_char_count,
            pdf_vector_line_count, pdf_embedded_image_count,
            "RASTER_BOUNDS_UNSUPPORTED", (),
        )
    grayscale = image.convert("L")
    hist = grayscale.histogram()
    total = width * height
    metrics: list[ThresholdProfile] = []
    saturated = False
    for threshold in THRESHOLDS:
        mask = grayscale.point(lambda pixel: 1 if pixel <= threshold else 0)
        pixels = mask.tobytes()
        horizontal = _runs(pixels, width, height, rows=True)
        vertical = _runs(pixels, width, height, rows=False)
        saturated |= horizontal is None or vertical is None
        metrics.append(
            ThresholdProfile(
                dark_threshold=threshold,
                dark_percent=round(100 * sum(hist[: threshold + 1]) / total, 2),
                horizontal_long_runs=len(horizontal) if horizontal is not None else None,
                vertical_long_runs=len(vertical) if vertical is not None else None,
                longest_horizontal_run_px=(
                    max((end - start + 1 for _, start, end in horizontal), default=0)
                    if horizontal is not None
                    else None
                ),
                longest_vertical_run_px=(
                    max((end - start + 1 for _, start, end in vertical), default=0)
                    if vertical is not None
                    else None
                ),
            )
        )
    return PageMorphology(
        page_number, width, height, pdf_text_layer_char_count,
        pdf_vector_line_count, pdf_embedded_image_count,
        "RUN_COMPLEXITY_LIMIT" if saturated else "PAGE_STATISTICS_OBSERVED",
        tuple(metrics),
    )


def _error(
    observed: SourceObservation, status: str, flags: tuple[str, ...]
) -> YearMorphology:
    return YearMorphology(
        observed.year, observed.filename, observed.status,
        observed.actual_sha256, status, (), flags,
    )


def _profile_source(path: Path, observed: SourceObservation) -> YearMorphology:
    flags = ["REPOSITORY_LFS_IDENTITY_ONLY", "NO_ANSWER_OR_GRID_VALIDATION"]
    pages: list[PageMorphology] = []
    try:
        if path.stat().st_size > MAX_FILE_BYTES:
            return _error(observed, "MEDIA_BOUNDS_UNSUPPORTED", tuple(flags + ["FILE_LIMIT"]))
        if observed.media_kind == "JPEG":
            with Image.open(path) as image:
                if image.format != "JPEG" or image.width * image.height > MAX_PIXELS:
                    return _error(
                        observed, "MEDIA_BOUNDS_UNSUPPORTED", tuple(flags + ["JPEG_PIXEL_LIMIT"])
                    )
                image.load()
                pages.append(profile_page(image))
        elif observed.media_kind == "PDF":
            with pdfplumber.open(path) as pdf:
                if not 1 <= len(pdf.pages) <= MAX_PDF_PAGES:
                    return _error(
                        observed, "MEDIA_BOUNDS_UNSUPPORTED", tuple(flags + ["PDF_PAGE_LIMIT"])
                    )
                for page_number, page in enumerate(pdf.pages, start=1):
                    pixel_count = round(page.width * RENDER_DPI / 72) * round(
                        page.height * RENDER_DPI / 72
                    )
                    if pixel_count < 1 or pixel_count > MAX_PIXELS:
                        return _error(
                            observed, "MEDIA_BOUNDS_UNSUPPORTED",
                            tuple(flags + ["PDF_PIXEL_LIMIT"]),
                        )
                    image = page.to_image(resolution=RENDER_DPI, antialias=False).original
                    pages.append(
                        profile_page(
                            image, page_number=page_number,
                            pdf_text_layer_char_count=len(page.chars),
                            pdf_vector_line_count=len(page.lines),
                            pdf_embedded_image_count=len(page.images),
                        )
                    )
        else:
            return _error(observed, "MEDIA_UNSUPPORTED", tuple(flags + ["MEDIA_KIND"]))
    except (
        OSError, ValueError, RuntimeError, TypeError, PDFException,
        Image.DecompressionBombError,
    ):
        return _error(
            observed, "SOURCE_PROFILE_FAILED", tuple(flags + ["MEDIA_READ_FAILED"])
        )

    if len(pages) > 1:
        flags.append("MULTIPAGE_CONTINUATION_UNRESOLVED")
    return YearMorphology(
        observed.year, observed.filename, observed.status, observed.actual_sha256,
        "PAGE_STATISTICS_OBSERVED"
        if all(page.status == "PAGE_STATISTICS_OBSERVED" for page in pages)
        else "PAGE_STATISTICS_PARTIAL",
        tuple(pages), tuple(flags),
    )


def profile_rendered_family(source_dir: Path) -> MorphologyBatch:
    by_year = {row.year: row.key for row in inventory_sources(source_dir).years}
    rows = []
    for year in YEARS:
        observed = by_year[year]
        if observed.status != "LOCAL_SOURCE_PINNED" or not observed.filename:
            rows.append(
                _error(observed, "SOURCE_NOT_READY", (observed.exception or observed.status,))
            )
        else:
            rows.append(_profile_source(source_dir / observed.filename, observed))
    return MorphologyBatch(
        schema_version="1.0",
        scope="SOURCE_BOUND_PAGE_MORPHOLOGY_METADATA_ONLY",
        status="OBSERVATIONS_ONLY_NOT_VERIFIED",
        sources_pinned=sum(row.source_status == "LOCAL_SOURCE_PINNED" for row in rows),
        profiled_pages=sum(len(row.pages) for row in rows),
        years=tuple(rows),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Source-bound, metadata-only image morphology")
    parser.add_argument("--source-dir", type=Path, default=Path("source"))
    parser.add_argument(
        "--require-sources", action="store_true",
        help="Exit 2 if any of the three repository-SHA-matched originals is missing",
    )
    args = parser.parse_args(argv)
    report = profile_rendered_family(args.source_dir)
    print(json.dumps(asdict(report), sort_keys=True, indent=2))
    return 2 if args.require_sources and report.sources_pinned != len(YEARS) else 0


if __name__ == "__main__":
    raise SystemExit(main())
