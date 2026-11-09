import json
from dataclasses import replace
from pathlib import Path

from english_exam.answer_keys.domain import (
    ProvenanceKind,
    RawSourceValue,
    RecognitionStatus,
    SourceRegionProvenance,
)
from english_exam.answer_keys.native_grid import NativeGridSpec, pair_native_grid
from english_exam.domain import BBox
from english_exam.pdf_layout import EXTRACTION_METHOD

FIXTURE = Path(__file__).parents[2] / "fixtures" / "sanitized_native_key_grid.json"


def _value(raw: str, index: int) -> RawSourceValue:
    box = BBox(float(index), 10.0, float(index + max(len(raw), 1)), 18.0)
    return RawSourceValue(
        raw_representation=raw,
        provenance=(
            SourceRegionProvenance(
                source_filename="synthetic-key.pdf",
                page_number=1,
                bbox=box,
                kind=ProvenanceKind.TEXT,
                extraction_method=EXTRACTION_METHOD,
                source_text=raw,
            ),
        ),
        recognition_status=RecognitionStatus.NOT_REQUIRED,
    )


def _fixture_grid():
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    rows = tuple(
        tuple(None if raw is None else _value(raw, index * 10) for index, raw in enumerate(row))
        for row in data["rows"]
    )
    spec = NativeGridSpec(
        group_starts=tuple(data["group_starts"]),
        group_lengths=tuple(data["group_lengths"]),
    )
    return rows, spec


def test_pairs_sanitized_partial_final_group() -> None:
    rows, spec = _fixture_grid()

    pairs, issues = pair_native_grid(rows, spec)

    assert not issues
    assert [pair.expected_question_number for pair in pairs] == [1, 4, 2, 3]
    assert [
        (pair.raw_question_number.raw_representation, pair.raw_answer.raw_representation)
        for pair in pairs
    ] == [
        ("1", "2"),
        ("4", "3"),
        ("2", "1"),
        ("3", "4"),
    ]


def test_surfaces_missing_required_cell_without_hiding_other_pairs() -> None:
    rows, spec = _fixture_grid()
    changed_row = (rows[0][0], None, *rows[0][2:])

    pairs, issues = pair_native_grid((changed_row, *rows[1:]), spec)

    assert "KEY_GRID_MISSING_CELL" in {issue.code for issue in issues}
    assert {pair.expected_question_number for pair in pairs} == {2, 3, 4}


def test_surfaces_unexpected_content_in_unpopulated_cell() -> None:
    rows, spec = _fixture_grid()
    changed = list(rows[1])
    changed[2] = replace(rows[0][2], raw_representation="5")

    _, issues = pair_native_grid((rows[0], tuple(changed), rows[2]), spec)

    assert {issue.code for issue in issues} == {"KEY_GRID_UNEXPECTED_CELL"}
