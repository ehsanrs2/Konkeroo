"""Native paired-grid importer for the 1395 official initial key."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path

import pdfplumber
from pdfplumber.page import Page
from pdfplumber.table import Table

from english_exam.answer_keys.catalog import AnswerKeySourceSpec
from english_exam.answer_keys.digits import parse_unsigned_integer
from english_exam.answer_keys.domain import (
    AnswerDisposition,
    AnswerKeyEntry,
    AnswerKeyVariant,
    KeySourceDescriptor,
    OfficialKeyAvailability,
    ProvenanceKind,
    RawSourceValue,
    RecognitionStatus,
    SourcePage,
    SourceRegionProvenance,
)
from english_exam.answer_keys.native_grid import NativeGridSpec, pair_native_grid
from english_exam.domain import BBox, ExtractionIssue, IssueSeverity
from english_exam.pdf_layout import EXTRACTION_METHOD, union_bbox

ANSWER_TABLE_BBOX = (63.233, 268.615, 449.192, 651.115)
METADATA_TABLE_BBOX = (63.233, 221.885, 559.192, 245.538)
BBOX_TOLERANCE = 1.0
EXPECTED_PAGE_SIZE = (612.0, 792.0)
GRID_SPEC = NativeGridSpec(
    group_starts=(1, 31, 61, 91, 121),
    group_lengths=(30, 30, 30, 30, 1),
)


def _bbox_matches(actual: tuple[float, float, float, float], expected: tuple[float, ...]) -> bool:
    return all(abs(float(left) - right) <= BBOX_TOLERANCE for left, right in zip(actual, expected))


def _select_table(tables: list[Table], expected_bbox: tuple[float, ...], label: str) -> Table:
    matches = [table for table in tables if _bbox_matches(table.bbox, expected_bbox)]
    if len(matches) != 1:
        raise ValueError(f"expected one {label} at {expected_bbox}, found {len(matches)}")
    return matches[0]


def _source_value_from_cell(
    page: Page,
    cell_bbox: tuple[float, float, float, float] | None,
    *,
    source_filename: str,
    entity_id: str,
) -> tuple[RawSourceValue | None, tuple[ExtractionIssue, ...]]:
    if cell_bbox is None:
        return None, ()

    words = page.crop(cell_bbox).extract_words(
        x_tolerance=2,
        y_tolerance=2,
        keep_blank_chars=False,
        use_text_flow=False,
        return_chars=True,
    )
    if not words:
        return None, ()

    issues: list[ExtractionIssue] = []
    if len(words) != 1:
        issues.append(
            ExtractionIssue(
                code="KEY_CELL_TOKEN_COUNT",
                severity=IssueSeverity.ERROR,
                message=f"expected one native token, got {len(words)}",
                entity_id=entity_id,
            )
        )

    raw_text = " ".join(str(word["text"]) for word in words)
    character_boxes = [
        BBox(
            x0=round(float(char["x0"]), 3),
            y0=round(float(char["top"]), 3),
            x1=round(float(char["x1"]), 3),
            y1=round(float(char["bottom"]), 3),
        )
        for word in words
        for char in word.get("chars", ())
    ]
    if not character_boxes:
        issues.append(
            ExtractionIssue(
                code="KEY_CELL_CHARACTER_GEOMETRY",
                severity=IssueSeverity.ERROR,
                message="native token has no character-level geometry",
                entity_id=entity_id,
            )
        )
        return None, tuple(issues)

    return (
        RawSourceValue(
            raw_representation=raw_text,
            provenance=(
                SourceRegionProvenance(
                    source_filename=source_filename,
                    page_number=page.page_number,
                    bbox=union_bbox(character_boxes),
                    kind=ProvenanceKind.TEXT,
                    extraction_method=EXTRACTION_METHOD,
                    source_text=raw_text,
                ),
            ),
            recognition_status=RecognitionStatus.NOT_REQUIRED,
        ),
        tuple(issues),
    )


def _extract_grid(
    page: Page,
    table: Table,
    *,
    source_filename: str,
) -> tuple[tuple[AnswerKeyEntry, ...], tuple[ExtractionIssue, ...]]:
    issues: list[ExtractionIssue] = []
    if len(table.rows) != GRID_SPEC.row_count + 1:
        issues.append(
            ExtractionIssue(
                code="KEY_TABLE_ROW_COUNT",
                severity=IssueSeverity.ERROR,
                message=f"expected 31 table rows including header, got {len(table.rows)}",
            )
        )

    data_rows: list[tuple[RawSourceValue | None, ...]] = []
    for row_number, row in enumerate(table.rows[1:], start=1):
        values: list[RawSourceValue | None] = []
        for column_number, bbox in enumerate(row.cells, start=1):
            value, cell_issues = _source_value_from_cell(
                page,
                bbox,
                source_filename=source_filename,
                entity_id=f"key-grid-r{row_number}-c{column_number}",
            )
            values.append(value)
            issues.extend(cell_issues)
        data_rows.append(tuple(values))

    pairs, grid_issues = pair_native_grid(tuple(data_rows), GRID_SPEC)
    issues.extend(grid_issues)
    entries: list[AnswerKeyEntry] = []
    for pair in pairs:
        try:
            question_number = parse_unsigned_integer(pair.raw_question_number.raw_representation)
        except ValueError as error:
            issues.append(
                ExtractionIssue(
                    code="KEY_QUESTION_TOKEN",
                    severity=IssueSeverity.ERROR,
                    message=str(error),
                    entity_id=f"key-question-{pair.expected_question_number}",
                )
            )
            continue

        try:
            answer_position = parse_unsigned_integer(pair.raw_answer.raw_representation)
        except ValueError as error:
            issues.append(
                ExtractionIssue(
                    code="KEY_ANSWER_TOKEN",
                    severity=IssueSeverity.ERROR,
                    message=str(error),
                    entity_id=f"key-question-{pair.expected_question_number}",
                )
            )
            continue

        if question_number != pair.expected_question_number:
            issues.append(
                ExtractionIssue(
                    code="KEY_GRID_QUESTION_SEQUENCE",
                    severity=IssueSeverity.ERROR,
                    message=(
                        f"expected question {pair.expected_question_number}, got {question_number}"
                    ),
                    entity_id=f"key-question-{pair.expected_question_number}",
                )
            )

        entries.append(
            AnswerKeyEntry(
                question_number=question_number,
                raw_question_number=pair.raw_question_number,
                raw_answer=pair.raw_answer,
                accepted_choice_positions=(answer_position,),
                disposition=AnswerDisposition.ANSWERED,
            )
        )

    return tuple(sorted(entries, key=lambda entry: entry.question_number)), tuple(issues)


def import_key_1395(
    source_path: Path,
    source_spec: AnswerKeySourceSpec,
) -> tuple[KeySourceDescriptor, tuple[AnswerKeyVariant, ...], tuple[ExtractionIssue, ...]]:
    """Import the SHA-bound 1395 native key without consulting an exam dataset."""

    source_path = Path(source_path)
    if source_spec.availability is not OfficialKeyAvailability.AVAILABLE:
        raise ValueError(f"official key is unavailable for {source_spec.canonical_exam_id}")
    if source_spec.source_filename is None or source_path.name != source_spec.source_filename:
        raise ValueError(
            f"expected source filename {source_spec.source_filename!r}, got {source_path.name!r}"
        )

    source_hash = sha256(source_path.read_bytes()).hexdigest()
    if source_hash != source_spec.expected_sha256:
        raise ValueError(
            f"source SHA-256 does not match catalog for {source_spec.canonical_exam_id}"
        )

    issues: list[ExtractionIssue] = []
    with pdfplumber.open(source_path) as pdf:
        if len(pdf.pages) != source_spec.expected_page_count:
            raise ValueError(
                f"expected {source_spec.expected_page_count} page, got {len(pdf.pages)}"
            )
        page = pdf.pages[0]
        tables = page.find_tables()
        answer_table = _select_table(tables, ANSWER_TABLE_BBOX, "1395 answer table")
        metadata_table = _select_table(tables, METADATA_TABLE_BBOX, "1395 metadata table")

        if len(answer_table.rows) != 31 or any(len(row.cells) != 10 for row in answer_table.rows):
            issues.append(
                ExtractionIssue(
                    code="KEY_TABLE_SHAPE",
                    severity=IssueSeverity.ERROR,
                    message="1395 answer table must contain 31 rows and 10 columns",
                )
            )

        booklet_bbox = metadata_table.rows[1].cells[0]
        booklet, booklet_issues = _source_value_from_cell(
            page,
            booklet_bbox,
            source_filename=source_path.name,
            entity_id="booklet-A",
        )
        issues.extend(booklet_issues)
        if booklet is None:
            raise ValueError("1395 metadata table has no booklet code")

        entries, grid_issues = _extract_grid(
            page,
            answer_table,
            source_filename=source_path.name,
        )
        issues.extend(grid_issues)
        source = KeySourceDescriptor(
            canonical_exam_id=source_spec.canonical_exam_id,
            year=source_spec.year,
            source_filename=source_path.name,
            media_type=source_spec.media_type,
            sha256=source_hash,
            pages=(
                SourcePage(
                    page_number=1,
                    width=round(float(page.width), 3),
                    height=round(float(page.height), 3),
                ),
            ),
            family=source_spec.family,
            edition=source_spec.edition,
            availability=source_spec.availability,
        )

    variant = AnswerKeyVariant(
        id="booklet-A",
        booklet_code=booklet.raw_representation,
        raw_booklet_code=booklet,
        entries=entries,
    )
    return source, (variant,), tuple(issues)
