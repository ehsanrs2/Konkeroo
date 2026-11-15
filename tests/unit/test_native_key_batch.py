"""Synthetic family-level source probes: no copyrighted cells or answer keys."""

import json
from dataclasses import asdict
from types import SimpleNamespace

import pytest

from english_exam.batch_inventory import SourceObservation
from english_exam.native_key_batch import (
    NATIVE_YEARS,
    _probe_pdf,
    parse_native_paired_rows,
    process_native_family,
)


def _rows(group_starts=(1, 21), count=20, header=True):
    data = [
        tuple(
            token
            for start in group_starts
            for token in (str(start + index), str(((index + start) % 4) + 1))
        )
        for index in range(count)
    ]
    if header:
        data.insert(0, tuple(token for _ in group_starts for token in ("Question", "Answer")))
    return tuple(data)


def _observed(year=1401, status="LOCAL_SOURCE_UNPINNED"):
    return SourceObservation(
        year=year,
        role="OFFICIAL_KEY",
        filename=f"{year}_Key.pdf",
        media_kind="PDF",
        family="NATIVE_PAIRED_GRID",
        status=status,
        actual_sha256="a" * 64,
        expected_sha256=None,
        lfs_oid_sha256=None,
        exception=None,
    )


def test_two_groups_20_rows_and_header_are_read_in_source_order():
    result = parse_native_paired_rows(_rows())
    assert result is not None
    assert result.page_number == 1
    assert result.table_index == 0
    assert result.group_count == 2
    assert result.question_numbers == tuple(range(1, 41))
    assert len(result.answer_positions) == 40
    assert all(1 <= a <= 4 for a in result.answer_positions)


def test_right_to_left_group_order_and_optional_header():
    rows = _rows(group_starts=(21, 1), header=False)
    result = parse_native_paired_rows(rows, page_number=2, table_index=3)
    assert result is not None
    assert result.page_number == 2
    assert result.table_index == 3
    assert result.question_numbers == tuple(range(1, 41))
    assert result.group_count == 2


def test_short_trailing_last_group_without_guessing_missing_cells():
    full = _rows(group_starts=(1, 21), header=False)
    rows = tuple(
        (row[0], row[1], row[2], row[3])
        if index < 4
        else (row[0], row[1], None, None)
        for index, row in enumerate(full)
    )
    result = parse_native_paired_rows(rows)
    assert result is not None
    assert result.group_count == 2
    assert result.question_numbers == tuple(range(1, 25))


@pytest.mark.parametrize(
    "mode",
    [
        "bad_answer",
        "missing_question",
        "duplicate_question",
        "gap_question",
        "overlap_groups",
        "incomplete_pair",
        "unexpected_tail_value",
        "odd_columns",
        "different_row_widths",
        "too_short",
        "unknown_row",
    ],
)
def test_invalid_or_ambiguous_table_cannot_be_promoted(mode):
    rows = [list(row) for row in _rows()]
    if mode == "bad_answer":
        rows[1][1] = "5"
    elif mode == "missing_question":
        rows[1][0] = None
    elif mode == "duplicate_question":
        rows[3][0] = rows[2][0]
    elif mode == "gap_question":
        rows[4][0] = "100"
    elif mode == "overlap_groups":
        for index, row in enumerate(rows[1:], start=1):
            row[2] = str(index)
    elif mode == "incomplete_pair":
        rows[3][0] = None
    elif mode == "unexpected_tail_value":
        rows[3][2:4] = [None, None]
        rows[4][2:4] = ["23", "2"]
    elif mode == "odd_columns":
        rows = [row[:-1] for row in rows]
    elif mode == "different_row_widths":
        rows[-1].append("1")
    elif mode == "too_short":
        rows = rows[:4]
    elif mode == "unknown_row":
        rows[5][1] = "?"
    assert parse_native_paired_rows(tuple(tuple(row) for row in rows)) is None


class _Table:
    def __init__(self, rows):
        self.rows = rows

    def extract(self):
        return self.rows


class _PDF:
    def __init__(self, pages):
        self.pages = pages

    def __enter__(self):
        return self

    def __exit__(self, _kind, _error, _trace):
        return False


def test_one_strict_table_is_only_assistant_provisional_and_no_answers_are_reported(
    monkeypatch, tmp_path
):
    page = SimpleNamespace(find_tables=lambda: [_Table(_rows())])
    monkeypatch.setattr(
        "english_exam.native_key_batch.pdfplumber.open",
        lambda _path: _PDF([page]),
    )
    result = _probe_pdf(tmp_path / "1401_Key.pdf", _observed())
    assert result.status == "ASSISTANT_PROVISIONAL_GRID"
    assert result.candidate_tables == 1
    assert result.candidate_questions == 40
    assert result.flags == (
        "BOOKLET_UNASSIGNED",
        "KEY_EDITION_UNASSIGNED",
        "SOURCE_HASH_UNPINNED",
    )
    output = json.dumps(asdict(result))
    assert "answer_positions" not in output
    assert "question_numbers" not in output
    assert "official_answer" not in output


def test_ambiguous_multiple_tables_do_not_publish_any_candidate_count(monkeypatch, tmp_path):
    page = SimpleNamespace(find_tables=lambda: [_Table(_rows()), _Table(_rows())])
    monkeypatch.setattr(
        "english_exam.native_key_batch.pdfplumber.open",
        lambda _path: _PDF([page]),
    )
    result = _probe_pdf(tmp_path / "1402_Key.pdf", _observed(year=1402))
    assert result.status == "NO_UNIQUE_NATIVE_GRID"
    assert result.candidate_tables == 2
    assert result.candidate_questions == 0
    assert result.flags == ("MULTIPLE_GRID_CANDIDATES",)


def test_no_candidate_is_localized_exception(monkeypatch, tmp_path):
    page = SimpleNamespace(find_tables=lambda: [_Table([["header", "cell"]])])
    monkeypatch.setattr(
        "english_exam.native_key_batch.pdfplumber.open",
        lambda _path: _PDF([page]),
    )
    result = _probe_pdf(tmp_path / "1404-key.pdf", _observed(year=1404))
    assert result.status == "NO_UNIQUE_NATIVE_GRID"
    assert result.flags == ("NO_STRICT_PAIR_GRID",)
    assert result.candidate_questions == 0


def test_no_source_or_lfs_pointer_stays_exception_not_a_validated_key(tmp_path):
    report = process_native_family(tmp_path)
    assert NATIVE_YEARS == (1395, 1401, 1402, 1404)
    assert report.family == "NATIVE_PAIRED_GRID"
    assert report.source_ready == 0
    assert report.provisional_tables == 0
    assert report.exceptions == 4
    assert report.status == "FAMILY_PROBE_COMPLETE_WITH_EXCEPTIONS"
    assert all(row.status == "SOURCE_NOT_READY" for row in report.years)
    assert [row.year for row in report.years] == list(NATIVE_YEARS)


def test_locked_1395_dispatch_reuses_existing_importer_without_new_1395_parser(
    tmp_path, monkeypatch
):
    from english_exam import native_key_batch as batch
    from english_exam.batch_inventory import BatchInventory, YearInventory

    key = SourceObservation(
        year=1395,
        role="OFFICIAL_KEY",
        filename="95_Key.pdf",
        media_kind="PDF",
        family="NATIVE_PAIRED_GRID",
        status="LOCAL_SOURCE_PINNED",
        actual_sha256="a" * 64,
        expected_sha256="a" * 64,
        lfs_oid_sha256=None,
        exception=None,
    )
    unavailable = _observed(year=1401, status="SOURCE_MISSING")
    fake = SimpleNamespace(
        validation=SimpleNamespace(status="PASSED", errors=()),
        variants=(SimpleNamespace(entries=tuple(range(121))),),
    )
    observed_calls = []
    monkeypatch.setattr(
        batch,
        "extract_staged_key",
        lambda exam, path: observed_calls.append((exam, path)) or fake,
    )
    dummy_exam = SourceObservation(
        year=1395,
        role="EXAM",
        filename="95.pdf",
        media_kind="PDF",
        family="EXAM_PAPER",
        status="SOURCE_MISSING",
        actual_sha256=None,
        expected_sha256=None,
        lfs_oid_sha256=None,
        exception="SOURCE_MISSING",
    )
    rows = [
        YearInventory(1395, dummy_exam, key, False, True),
        *(
            YearInventory(y, dummy_exam, unavailable, False, False)
            for y in (1401, 1402, 1404)
        ),
    ]
    monkeypatch.setattr(
        batch,
        "inventory_sources",
        lambda _dir: BatchInventory("1.0", "SOURCES_INCOMPLETE", tuple(rows), 0, 1, 3),
    )
    result = process_native_family(tmp_path)
    assert result.years[0].status == "SOURCE_STAGE_VALIDATED"
    assert result.years[0].candidate_questions == 121
    assert result.years[0].flags == ()
    assert observed_calls == [("iran-ce-msc-1395", tmp_path / "95_Key.pdf")]
    assert result.exceptions == 3
