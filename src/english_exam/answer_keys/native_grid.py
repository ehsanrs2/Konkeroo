"""Small geometry-independent primitive for pairing native table cells."""

from __future__ import annotations

from dataclasses import dataclass

from english_exam.answer_keys.domain import RawSourceValue
from english_exam.domain import ExtractionIssue, IssueSeverity


@dataclass(frozen=True, slots=True)
class NativeGridSpec:
    group_starts: tuple[int, ...]
    group_lengths: tuple[int, ...]

    @property
    def row_count(self) -> int:
        return max(self.group_lengths, default=0)

    @property
    def column_count(self) -> int:
        return len(self.group_starts) * 2


@dataclass(frozen=True, slots=True)
class NativeGridPair:
    expected_question_number: int
    raw_question_number: RawSourceValue
    raw_answer: RawSourceValue


def pair_native_grid(
    rows: tuple[tuple[RawSourceValue | None, ...], ...],
    spec: NativeGridSpec,
) -> tuple[tuple[NativeGridPair, ...], tuple[ExtractionIssue, ...]]:
    """Pair configured question and answer cells while exposing all anomalies."""

    pairs: list[NativeGridPair] = []
    issues: list[ExtractionIssue] = []

    if len(spec.group_starts) != len(spec.group_lengths):
        raise ValueError("group starts and lengths must have equal sizes")
    if len(rows) != spec.row_count:
        issues.append(
            ExtractionIssue(
                code="KEY_GRID_ROW_COUNT",
                severity=IssueSeverity.ERROR,
                message=f"expected {spec.row_count} data rows, got {len(rows)}",
            )
        )

    for row_index, row in enumerate(rows):
        if len(row) != spec.column_count:
            issues.append(
                ExtractionIssue(
                    code="KEY_GRID_COLUMN_COUNT",
                    severity=IssueSeverity.ERROR,
                    message=(
                        f"row {row_index + 1} expected {spec.column_count} cells, got {len(row)}"
                    ),
                )
            )
            continue

        for group_index, (start, length) in enumerate(
            zip(spec.group_starts, spec.group_lengths, strict=True)
        ):
            question = row[group_index * 2]
            answer = row[group_index * 2 + 1]
            expected_number = start + row_index
            populated = row_index < length
            entity_id = f"key-question-{expected_number}"

            if populated:
                if question is None or answer is None:
                    issues.append(
                        ExtractionIssue(
                            code="KEY_GRID_MISSING_CELL",
                            severity=IssueSeverity.ERROR,
                            message=f"question {expected_number} has a missing paired cell",
                            entity_id=entity_id,
                        )
                    )
                    continue
                pairs.append(NativeGridPair(expected_number, question, answer))
            elif question is not None or answer is not None:
                issues.append(
                    ExtractionIssue(
                        code="KEY_GRID_UNEXPECTED_CELL",
                        severity=IssueSeverity.ERROR,
                        message=f"unexpected content after group ending at {start + length - 1}",
                        entity_id=entity_id,
                    )
                )

    return tuple(pairs), tuple(issues)
