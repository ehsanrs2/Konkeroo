"""One-pass, source-family native answer-grid candidate scanner.

Existing locked 1395 importer remains authoritative *for staging only*.
Other native-family sources get strict, unassigned, assistant-provisional
table candidates. No answer positions or copyrighted rows go to stdout.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import pdfplumber

from english_exam.answer_keys.digits import parse_unsigned_integer
from english_exam.answer_keys.pipeline import extract_staged_key
from english_exam.batch_inventory import SourceObservation, inventory_sources

NATIVE_YEARS = (1395, 1401, 1402, 1404)
MIN_CANDIDATE_QUESTIONS = 20
MAX_PDF_PAGES = 20


@dataclass(frozen=True, slots=True)
class NativeGridCandidate:
    """Internal-only parsed positions; never serialize this object in CLI output."""

    page_number: int
    table_index: int
    question_numbers: tuple[int, ...]
    answer_positions: tuple[int, ...]
    group_count: int


@dataclass(frozen=True, slots=True)
class NativeFamilyYearResult:
    year: int
    source_filename: str | None
    source_status: str
    source_sha256: str | None
    status: str
    candidate_tables: int
    candidate_questions: int
    flags: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class NativeFamilyBatch:
    schema_version: str
    status: str
    family: str
    years: tuple[NativeFamilyYearResult, ...]
    source_ready: int
    provisional_tables: int
    exceptions: int


def _number(token: object) -> int | None:
    if not isinstance(token, str):
        return None
    try:
        return parse_unsigned_integer(token.strip())
    except ValueError:
        return None


def parse_native_paired_rows(
    rows: tuple[tuple[str | None, ...], ...],
    *,
    page_number: int = 1,
    table_index: int = 0,
) -> NativeGridCandidate | None:
    """Accept only unambiguous paired question/answer numerical grids.

    The first row may be a non-numeric header, groups may have trailing
    empty cells, and question groups may be arranged right-to-left.
    A single bad number/option or overlapping range rejects the *whole* table.
    """

    if len(rows) < 3:
        return None
    widths = {len(row) for row in rows}
    if len(widths) != 1:
        return None
    width = widths.pop()
    if width < 2 or width > 12 or width % 2:
        return None

    first = rows[0]
    header = any(_number(first[col]) is None for col in range(0, width, 2))
    data = rows[1:] if header else rows
    if not data:
        return None

    groups: list[tuple[tuple[int, int], ...]] = []
    for col in range(0, width, 2):
        pairs: list[tuple[int, int]] = []
        ended = False
        for row in data:
            q_raw, a_raw = row[col], row[col + 1]
            question = _number(q_raw)
            answer = _number(a_raw)
            empty = (q_raw is None or not str(q_raw).strip()) and (
                a_raw is None or not str(a_raw).strip()
            )
            if empty:
                ended = True
                continue
            if ended or question is None or answer not in (1, 2, 3, 4):
                return None
            if question < 1 or (pairs and question != pairs[-1][0] + 1):
                return None
            pairs.append((question, answer))
        if not pairs:
            return None
        groups.append(tuple(pairs))

    # Order may be mirrored in a right-to-left table; compare by question
    # number, not by the visual left-to-right column index.
    groups.sort(key=lambda group: group[0][0])
    flat = tuple(item for group in groups for item in group)
    if len(flat) < MIN_CANDIDATE_QUESTIONS:
        return None
    numbers = tuple(question for question, _answer in flat)
    if len(set(numbers)) != len(numbers):
        return None
    if numbers != tuple(range(numbers[0], numbers[0] + len(numbers))):
        return None
    return NativeGridCandidate(
        page_number=page_number,
        table_index=table_index,
        question_numbers=numbers,
        answer_positions=tuple(answer for _question, answer in flat),
        group_count=len(groups),
    )


def _source_unavailable(observation: SourceObservation) -> NativeFamilyYearResult:
    return NativeFamilyYearResult(
        observation.year,
        observation.filename,
        observation.status,
        observation.actual_sha256,
        "SOURCE_NOT_READY",
        0,
        0,
        (observation.exception or observation.status,),
    )


def _locked_1395(path: Path, observed: SourceObservation) -> NativeFamilyYearResult:
    try:
        staged = extract_staged_key("iran-ce-msc-1395", path)
    except (OSError, RuntimeError, ValueError, TypeError):
        return NativeFamilyYearResult(
            observed.year,
            observed.filename,
            observed.status,
            observed.actual_sha256,
            "LOCKED_IMPORTER_FAILED",
            0,
            0,
            ("LOCKED_1395_IMPORTER_FAILED",),
        )
    if staged.validation.status != "PASSED" or staged.validation.errors:
        return NativeFamilyYearResult(
            observed.year,
            observed.filename,
            observed.status,
            observed.actual_sha256,
            "LOCKED_IMPORTER_FAILED",
            0,
            0,
            ("LOCKED_1395_VALIDATION_FAILED",),
        )
    return NativeFamilyYearResult(
        observed.year,
        observed.filename,
        observed.status,
        observed.actual_sha256,
        "SOURCE_STAGE_VALIDATED",
        1,
        sum(len(variant.entries) for variant in staged.variants),
        (),
    )


def _probe_pdf(path: Path, observed: SourceObservation) -> NativeFamilyYearResult:
    candidates: list[NativeGridCandidate] = []
    try:
        with pdfplumber.open(path) as pdf:
            if len(pdf.pages) > MAX_PDF_PAGES:
                return NativeFamilyYearResult(
                    observed.year,
                    observed.filename,
                    observed.status,
                    observed.actual_sha256,
                    "SOURCE_LAYOUT_UNSUPPORTED",
                    0,
                    0,
                    ("PAGE_LIMIT_EXCEEDED",),
                )
            for page_number, page in enumerate(pdf.pages, start=1):
                for table_index, table in enumerate(page.find_tables()):
                    raw_rows: list[tuple[str | None, ...]] = []
                    for row in table.extract():
                        if row is None:
                            raw_rows.append(())
                        else:
                            raw_rows.append(tuple(row))
                    candidate = parse_native_paired_rows(
                        tuple(raw_rows),
                        page_number=page_number,
                        table_index=table_index,
                    )
                    if candidate is not None:
                        candidates.append(candidate)
    except (OSError, ValueError, TypeError, KeyError, IndexError):
        return NativeFamilyYearResult(
            observed.year,
            observed.filename,
            observed.status,
            observed.actual_sha256,
            "SOURCE_PARSE_FAILED",
            0,
            0,
            ("PDF_TABLE_EXTRACTION_FAILED",),
        )

    count = len(candidates)
    if count != 1:
        return NativeFamilyYearResult(
            observed.year,
            observed.filename,
            observed.status,
            observed.actual_sha256,
            "NO_UNIQUE_NATIVE_GRID",
            count,
            0,
            ("NO_STRICT_PAIR_GRID" if not count else "MULTIPLE_GRID_CANDIDATES",),
        )

    candidate = candidates[0]
    flags = ["BOOKLET_UNASSIGNED", "KEY_EDITION_UNASSIGNED"]
    if observed.expected_sha256 is None:
        flags.append("SOURCE_HASH_UNPINNED")
    return NativeFamilyYearResult(
        observed.year,
        observed.filename,
        observed.status,
        observed.actual_sha256,
        "ASSISTANT_PROVISIONAL_GRID",
        1,
        len(candidate.question_numbers),
        tuple(flags),
    )


def process_native_family(source_dir: Path) -> NativeFamilyBatch:
    """Attempt four native-family sources in one pass, isolating failures."""

    inventory = inventory_sources(source_dir)
    by_year = {row.year: row.key for row in inventory.years}
    results: list[NativeFamilyYearResult] = []
    for year in NATIVE_YEARS:
        observed = by_year[year]
        if observed.status not in ("LOCAL_SOURCE_PINNED", "LOCAL_SOURCE_UNPINNED"):
            results.append(_source_unavailable(observed))
            continue
        if observed.filename is None or observed.actual_sha256 is None:
            results.append(_source_unavailable(observed))
            continue
        path = source_dir / observed.filename
        if year == 1395:
            results.append(_locked_1395(path, observed))
        else:
            results.append(_probe_pdf(path, observed))

    source_ready = sum(
        result.source_status in ("LOCAL_SOURCE_PINNED", "LOCAL_SOURCE_UNPINNED")
        for result in results
    )
    provisional = sum(result.status == "ASSISTANT_PROVISIONAL_GRID" for result in results)
    exceptions = sum(
        result.status not in ("SOURCE_STAGE_VALIDATED", "ASSISTANT_PROVISIONAL_GRID")
        for result in results
    )
    return NativeFamilyBatch(
        schema_version="1.0",
        status="FAMILY_PROBE_COMPLETE_WITH_EXCEPTIONS" if exceptions else "FAMILY_PROBE_COMPLETE",
        family="NATIVE_PAIRED_GRID",
        years=tuple(results),
        source_ready=source_ready,
        provisional_tables=provisional,
        exceptions=exceptions,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Batch native paired-key source probe; no answer data in output"
    )
    parser.add_argument("--source-dir", type=Path, default=Path("source"))
    args = parser.parse_args()
    result = process_native_family(args.source_dir)
    print(json.dumps(asdict(result), sort_keys=True, indent=2))
    return 0  # Command ran, not evidence that all four sources parsed successfully.


if __name__ == "__main__":
    raise SystemExit(main())
