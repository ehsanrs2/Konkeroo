"""Read-only broken-font answer-key probes for 1397, 1398 and 1399.

A unique single-character glyph substitution is inferred only from a complete,
consecutive 1–20+ question-number column. This is an ASSUMED Q1 anchor,
not a validated font map, official key or complete multi-page transcription.
No decoded answers or glyph mapping appear in CLI output.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import pdfplumber
from pdfminer.pdfexceptions import PDFException

from english_exam.batch_inventory import SourceObservation, inventory_sources
from english_exam.native_key_batch import parse_native_paired_rows

BROKEN_FONT_YEARS = (1397, 1398, 1399)
EXPECTED_PAGE_COUNTS = {1397: 2, 1398: 2, 1399: 1}
MIN_ANCHOR_ROWS = 20
MAX_PDF_PAGES = 6


@dataclass(frozen=True, slots=True)
class RecoveredGlyphGrid:
    """Internal candidate only; NEVER pass to metadata serialization."""

    page_number: int
    table_index: int
    question_numbers: tuple[int, ...]
    answer_positions: tuple[int, ...]
    glyph_pairs: tuple[tuple[str, str], ...]
    group_count: int


@dataclass(frozen=True, slots=True)
class BrokenFontYearResult:
    year: int
    source_filename: str | None
    source_status: str
    source_sha256: str | None
    page_count: int | None
    status: str
    geometric_tables: int
    candidate_tables: int
    candidate_questions: int
    flags: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class BrokenFontBatch:
    schema_version: str
    family: str
    status: str
    years: tuple[BrokenFontYearResult, ...]
    source_ready: int
    provisional_candidates: int
    exceptions: int


def _learn_bijective_digit_map(q_cells: tuple[str | None, ...]) -> dict[str, str] | None:
    """Q1 through at least Q20 determines all ten digits, if glyphs are unique.

    A different starting question number must NOT be assumed equivalent to Q1.
    The source may contain non-single-character ligatures; fail closed there.
    """
    if len(q_cells) < MIN_ANCHOR_ROWS:
        return None
    forward: dict[str, str] = {}
    backward: dict[str, str] = {}
    for number, raw in enumerate(q_cells, start=1):
        expected = str(number)
        if not isinstance(raw, str) or not raw or raw != raw.strip() or len(raw) != len(expected):
            return None
        for glyph, digit in zip(raw, expected, strict=True):
            if (glyph in forward and forward[glyph] != digit) or (
                digit in backward and backward[digit] != glyph
            ):
                return None
            forward[glyph] = digit
            backward[digit] = glyph
    if len(backward) != 10 or len(forward) != 10:
        return None
    return forward


def _translate_token(token: str | None, glyphs: dict[str, str]) -> str | None:
    if token is None or not token.strip():
        return None
    if token != token.strip():
        return None
    try:
        return "".join(glyphs[char] for char in token)
    except KeyError:
        return None


def recover_glyph_grid(
    rows: tuple[tuple[str | None, ...], ...],
    *,
    page_number: int = 1,
    table_index: int = 0,
) -> tuple[RecoveredGlyphGrid, ...]:
    """Return only *unique possible* Q1-anchored full-table interpretations.

    No answer token independently proves its displayed numerical meaning.
    All answers must be 1–4 after one consistent map learned exclusively
    from printed-position question-number sequences.
    """
    if len(rows) < MIN_ANCHOR_ROWS or len({len(row) for row in rows}) != 1:
        return ()
    width = len(rows[0])
    if not 2 <= width <= 12 or width % 2:
        return ()

    recovered: set[RecoveredGlyphGrid] = set()
    for header_rows in (0, 1):
        data = rows[header_rows:]
        if len(data) < MIN_ANCHOR_ROWS:
            continue
        for group_column in range(0, width, 2):
            q_cells = tuple(row[group_column] for row in data)
            mapping = _learn_bijective_digit_map(q_cells)
            if mapping is None:
                continue
            decoded: list[tuple[str | None, ...]] = []
            undecodable = False
            for row in data:
                normalized = tuple(_translate_token(cell, mapping) for cell in row)
                for original, mapped in zip(row, normalized, strict=True):
                    if original is not None and original.strip() and mapped is None:
                        undecodable = True
                        break
                if undecodable:
                    break
                decoded.append(normalized)
            if undecodable:
                continue

            paired = parse_native_paired_rows(
                tuple(decoded), page_number=page_number, table_index=table_index
            )
            if paired is None or paired.question_numbers[0] != 1:
                continue
            recovered.add(
                RecoveredGlyphGrid(
                    page_number=page_number,
                    table_index=table_index,
                    question_numbers=paired.question_numbers,
                    answer_positions=paired.answer_positions,
                    glyph_pairs=tuple(sorted(mapping.items())),
                    group_count=paired.group_count,
                )
            )
    return tuple(sorted(recovered, key=lambda c: (c.page_number, c.table_index, c.glyph_pairs)))


def _unavailable(observed: SourceObservation) -> BrokenFontYearResult:
    return BrokenFontYearResult(
        year=observed.year,
        source_filename=observed.filename,
        source_status=observed.status,
        source_sha256=observed.actual_sha256,
        page_count=None,
        status="SOURCE_NOT_READY",
        geometric_tables=0,
        candidate_tables=0,
        candidate_questions=0,
        flags=(observed.exception or observed.status,),
    )


def _probe_pdf(path: Path, observed: SourceObservation) -> BrokenFontYearResult:
    page_count: int | None = None
    total_tables = 0
    candidates: list[RecoveredGlyphGrid] = []
    try:
        with pdfplumber.open(path) as pdf:
            page_count = len(pdf.pages)
            if page_count != EXPECTED_PAGE_COUNTS[observed.year] or page_count > MAX_PDF_PAGES:
                return BrokenFontYearResult(
                    observed.year,
                    observed.filename,
                    observed.status,
                    observed.actual_sha256,
                    page_count,
                    "PAGE_LAYOUT_MISMATCH",
                    0,
                    0,
                    0,
                    ("EXPECTED_PAGE_COUNT_MISMATCH",),
                )
            for page_number, page in enumerate(pdf.pages, start=1):
                tables = page.find_tables()
                total_tables += len(tables)
                for table_index, table in enumerate(tables):
                    rows = tuple(tuple(row) if row is not None else () for row in table.extract())
                    candidates.extend(
                        recover_glyph_grid(rows, page_number=page_number, table_index=table_index)
                    )
    except (OSError, PDFException, RuntimeError, ValueError, TypeError, IndexError, KeyError):
        return BrokenFontYearResult(
            observed.year,
            observed.filename,
            observed.status,
            observed.actual_sha256,
            page_count,
            "SOURCE_PARSE_FAILED",
            total_tables,
            0,
            0,
            ("PDF_GLYPH_TABLE_EXTRACTION_FAILED",),
        )

    if len(candidates) != 1:
        return BrokenFontYearResult(
            observed.year,
            observed.filename,
            observed.status,
            observed.actual_sha256,
            page_count,
            "NEEDS_GLYPH_GEOMETRY_FOLLOWUP",
            total_tables,
            len(candidates),
            0,
            ("NO_UNIQUE_Q1_GLYPH_MAP" if not candidates else "MULTIPLE_Q1_GLYPH_MAPS",),
        )

    one = candidates[0]
    flags = ["UNVERIFIED_Q1_ANCHOR", "BOOKLET_UNASSIGNED", "KEY_EDITION_UNASSIGNED"]
    if all(glyph == digit for glyph, digit in one.glyph_pairs):
        flags.append("IDENTITY_TEXT_LAYER_MAP")
    if page_count != 1:
        flags.append("MULTIPAGE_CONTINUATION_UNRESOLVED")
    return BrokenFontYearResult(
        year=observed.year,
        source_filename=observed.filename,
        source_status=observed.status,
        source_sha256=observed.actual_sha256,
        page_count=page_count,
        status=(
            "ASSISTANT_PROVISIONAL_PARTIAL_GRID"
            if page_count != 1
            else "ASSISTANT_PROVISIONAL_GLYPH_GRID"
        ),
        geometric_tables=total_tables,
        candidate_tables=1,
        candidate_questions=len(one.question_numbers),
        flags=tuple(flags),
    )


def process_broken_font_family(source_dir: Path) -> BrokenFontBatch:
    """Batch source-bound extraction attempts; isolate each file's exceptions."""
    inventory = inventory_sources(source_dir)
    observations = {row.year: row.key for row in inventory.years}
    years: list[BrokenFontYearResult] = []
    for year in BROKEN_FONT_YEARS:
        observed = observations[year]
        if observed.status != "LOCAL_SOURCE_PINNED" or not observed.filename:
            years.append(_unavailable(observed))
        else:
            years.append(_probe_pdf(source_dir / observed.filename, observed))

    provisional = sum(row.status.startswith("ASSISTANT_PROVISIONAL") for row in years)
    exceptions = len(years) - provisional
    return BrokenFontBatch(
        schema_version="1.0",
        family="BROKEN_FONT_PAIRED_GRID",
        status=(
            "FAMILY_PROBE_COMPLETE_WITH_EXCEPTIONS"
            if exceptions
            else "FAMILY_PROBE_COMPLETE_PROVISIONAL_ONLY"
        ),
        years=tuple(years),
        source_ready=sum(row.source_status == "LOCAL_SOURCE_PINNED" for row in years),
        provisional_candidates=provisional,
        exceptions=exceptions,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Read-only 1397–1399 broken-font glyph-grid batch (metadata only)"
    )
    parser.add_argument("--source-dir", type=Path, default=Path("source"))
    args = parser.parse_args()
    result = process_broken_font_family(args.source_dir)
    print(json.dumps(asdict(result), ensure_ascii=False, sort_keys=True, indent=2))
    return 0  # Successful report generation is not source/answer verification.


if __name__ == "__main__":
    raise SystemExit(main())
