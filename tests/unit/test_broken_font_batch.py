"""Synthetic broken-font family probes; no copied exam/answer-key cells."""

import json
from dataclasses import asdict, replace
from types import SimpleNamespace

import pytest

from english_exam.batch_inventory import (
    KEY_BROKEN_FONT_SHA,
    SourceObservation,
    inventory_sources,
)
from english_exam.broken_font_batch import (
    BROKEN_FONT_YEARS,
    _probe_pdf,
    process_broken_font_family,
    recover_glyph_grid,
)

ENCODE = {str(digit): chr(0xE000 + digit) for digit in range(10)}


def _glyphs(value):
    return "".join(ENCODE[character] for character in str(value))


def _rows(starts=(1, 21), count=20, header=True):
    data = [
        tuple(
            raw
            for start in starts
            for raw in (_glyphs(start + row), _glyphs((row + start) % 4 + 1))
        )
        for row in range(count)
    ]
    if header:
        data.insert(0, tuple(x for _ in starts for x in ("QUESTION", "ANSWER")))
    return tuple(data)


def _observed(year=1397):
    return SourceObservation(
        year=year,
        role="OFFICIAL_KEY",
        filename=f"{year - 1300}_Key.pdf",
        media_kind="PDF",
        family="BROKEN_FONT_PAIRED_GRID",
        status="LOCAL_SOURCE_PINNED",
        actual_sha256=KEY_BROKEN_FONT_SHA[year],
        expected_sha256=KEY_BROKEN_FONT_SHA[year],
        lfs_oid_sha256=None,
        exception=None,
    )


def test_private_glyph_substitution_recovers_one_question_answer_table():
    candidates = recover_glyph_grid(_rows())
    assert len(candidates) == 1
    result = candidates[0]
    assert result.question_numbers == tuple(range(1, 41))
    assert len(result.answer_positions) == 40
    assert all(position in (1, 2, 3, 4) for position in result.answer_positions)
    assert len(result.glyph_pairs) == 10
    assert len({digit for _glyph, digit in result.glyph_pairs}) == 10
    assert result.group_count == 2
    assert all(glyph not in "0123456789" for glyph, _digit in result.glyph_pairs)


def test_right_to_left_group_and_no_header_still_source_anchored():
    matches = recover_glyph_grid(_rows(starts=(21, 1), header=False), page_number=2)
    assert len(matches) == 1
    assert matches[0].page_number == 2
    assert matches[0].question_numbers == tuple(range(1, 41))


@pytest.mark.parametrize(
    "mode",
    [
        "missing_first_question",
        "wrong_first_question",
        "wrong_digit_length",
        "collided_digit",
        "missing_question_cell",
        "bad_answer",
        "unknown_answer_glyph",
        "duplicated_question",
        "overlapping_second_group",
        "number_gap",
        "malformed_row",
        "short_anchor",
    ],
)
def test_bad_or_ambiguous_glyphs_fail_closed(mode):
    rows = [list(row) for row in _rows()]
    if mode == "missing_first_question":
        rows[1][0] = None
    elif mode == "wrong_first_question":
        rows[1][0] = _glyphs(2)
    elif mode == "wrong_digit_length":
        rows[9][0] = _glyphs(100)
    elif mode == "collided_digit":
        # Encoding a 1 as the same glyph as 2 breaks invertibility.
        rows[1][0] = _glyphs(2)
    elif mode == "missing_question_cell":
        rows[4][2] = None
    elif mode == "bad_answer":
        rows[4][1] = _glyphs(5)
    elif mode == "unknown_answer_glyph":
        rows[4][1] = "🔍"
    elif mode == "duplicated_question":
        rows[4][0] = rows[3][0]
    elif mode == "overlapping_second_group":
        for offset, row in enumerate(rows[1:]):
            row[2] = _glyphs(offset + 1)
    elif mode == "number_gap":
        rows[7][2] = _glyphs(30)
    elif mode == "malformed_row":
        rows[6].append("extra")
    elif mode == "short_anchor":
        rows = rows[:15]
    assert recover_glyph_grid(tuple(tuple(row) for row in rows)) == ()


class _Table:
    def __init__(self, rows):
        self._rows = rows

    def extract(self):
        return self._rows


class _PDF:
    def __init__(self, pages):
        self.pages = pages

    def __enter__(self):
        return self

    def __exit__(self, _kind, _error, _trace):
        return False


def _fake_pdf(monkeypatch, tables_by_page):
    pages = [
        SimpleNamespace(find_tables=lambda tables=tables: [_Table(rows) for rows in tables])
        for tables in tables_by_page
    ]
    monkeypatch.setattr(
        "english_exam.broken_font_batch.pdfplumber.open",
        lambda _path: _PDF(pages),
    )


def test_two_page_source_never_claims_complete_key(monkeypatch, tmp_path):
    _fake_pdf(monkeypatch, [[_rows()], []])
    result = _probe_pdf(tmp_path / "97_Key.pdf", _observed())
    assert result.status == "ASSISTANT_PROVISIONAL_PARTIAL_GRID"
    assert result.page_count == 2
    assert result.geometric_tables == 1
    assert result.candidate_tables == 1
    assert result.candidate_questions == 40
    assert result.flags == (
        "UNVERIFIED_Q1_ANCHOR",
        "BOOKLET_UNASSIGNED",
        "KEY_EDITION_UNASSIGNED",
        "MULTIPAGE_CONTINUATION_UNRESOLVED",
    )
    metadata = json.dumps(asdict(result))
    assert "glyph_pairs" not in metadata
    assert "answer_positions" not in metadata
    assert "question_numbers" not in metadata


def test_one_page_source_only_has_unverified_provisional_glyph_grid(monkeypatch, tmp_path):
    _fake_pdf(monkeypatch, [[_rows()]])
    result = _probe_pdf(tmp_path / "99_Key.pdf", _observed(year=1399))
    assert result.status == "ASSISTANT_PROVISIONAL_GLYPH_GRID"
    assert result.page_count == 1
    assert result.candidate_questions == 40
    assert "UNVERIFIED_Q1_ANCHOR" in result.flags
    assert "MULTIPAGE_CONTINUATION_UNRESOLVED" not in result.flags


def test_ambiguous_two_tables_do_not_pass_source_gate(monkeypatch, tmp_path):
    _fake_pdf(monkeypatch, [[_rows(), _rows()], []])
    result = _probe_pdf(tmp_path / "97_Key.pdf", _observed())
    assert result.status == "NEEDS_GLYPH_GEOMETRY_FOLLOWUP"
    assert result.candidate_tables == 2
    assert result.candidate_questions == 0
    assert result.flags == ("MULTIPLE_Q1_GLYPH_MAPS",)


def test_missing_table_is_not_treated_as_a_numeric_answer_source(monkeypatch, tmp_path):
    _fake_pdf(monkeypatch, [[], []])
    result = _probe_pdf(tmp_path / "97_Key.pdf", _observed())
    assert result.status == "NEEDS_GLYPH_GEOMETRY_FOLLOWUP"
    assert result.flags == ("NO_UNIQUE_Q1_GLYPH_MAP",)
    assert result.candidate_questions == 0


def test_unexpected_source_page_count_is_fail_closed(monkeypatch, tmp_path):
    _fake_pdf(monkeypatch, [[_rows()]])
    result = _probe_pdf(tmp_path / "97_Key.pdf", _observed())
    assert result.status == "PAGE_LAYOUT_MISMATCH"
    assert result.flags == ("EXPECTED_PAGE_COUNT_MISMATCH",)
    assert result.candidate_questions == 0


def test_all_three_years_missing_are_isolated_without_implicit_source_acceptance(tmp_path):
    report = process_broken_font_family(tmp_path)
    assert BROKEN_FONT_YEARS == (1397, 1398, 1399)
    assert len(report.years) == 3
    assert report.source_ready == 0
    assert report.provisional_candidates == 0
    assert report.exceptions == 3
    assert report.status == "FAMILY_PROBE_COMPLETE_WITH_EXCEPTIONS"
    assert all(year.status == "SOURCE_NOT_READY" for year in report.years)


def test_repo_lfs_object_ids_are_pinned_and_pointer_is_not_pdf(tmp_path):
    assert len(set(KEY_BROKEN_FONT_SHA.values())) == 3
    for year in BROKEN_FONT_YEARS:
        token = f"{year - 1300}_Key.pdf"
        (tmp_path / token).write_text(
            "version https://git-lfs.github.com/spec/v1\n"
            f"oid sha256:{KEY_BROKEN_FONT_SHA[year]}\nsize 200000\n",
            encoding="ascii",
        )
    inventory = inventory_sources(tmp_path)
    for row in inventory.years:
        if row.year in BROKEN_FONT_YEARS:
            assert row.key.expected_sha256 == KEY_BROKEN_FONT_SHA[row.year]
            assert row.key.status == "LFS_POINTER_ONLY"
            assert not row.can_attempt_key
    report = process_broken_font_family(tmp_path)
    assert report.source_ready == 0
    assert report.provisional_candidates == 0
    assert report.exceptions == 3


def test_one_failed_year_does_not_prevent_other_ready_year(monkeypatch, tmp_path):
    from english_exam import broken_font_batch as batch

    observed = {
        year: (
            _observed(year)
            if year != 1398
            else replace(
                _observed(year),
                status="SOURCE_HASH_MISMATCH",
                actual_sha256="f" * 64,
                exception="SOURCE_HASH_MISMATCH",
            )
        )
        for year in BROKEN_FONT_YEARS
    }
    inventory = SimpleNamespace(
        years=tuple(SimpleNamespace(year=y, key=obs) for y, obs in observed.items())
    )
    monkeypatch.setattr(batch, "inventory_sources", lambda _root: inventory)

    def fake_probe(_path, obs):
        return batch.BrokenFontYearResult(
            obs.year,
            obs.filename,
            obs.status,
            obs.actual_sha256,
            2 if obs.year == 1397 else 1,
            "ASSISTANT_PROVISIONAL_PARTIAL_GRID"
            if obs.year == 1397
            else "ASSISTANT_PROVISIONAL_GLYPH_GRID",
            1,
            1,
            40,
            ("UNVERIFIED_Q1_ANCHOR",),
        )

    monkeypatch.setattr(batch, "_probe_pdf", fake_probe)
    result = process_broken_font_family(tmp_path)
    assert result.source_ready == 2
    assert result.provisional_candidates == 2
    assert result.exceptions == 1
    assert [x.status for x in result.years] == [
        "ASSISTANT_PROVISIONAL_PARTIAL_GRID",
        "SOURCE_NOT_READY",
        "ASSISTANT_PROVISIONAL_GLYPH_GRID",
    ]


def test_font_collision_or_multi_character_ligature_is_not_guessed():
    original = _rows(header=False)
    # Two distinct source digits decode to one glyph: not bijective.
    collision = tuple(
        tuple(cell.replace(ENCODE["2"], ENCODE["1"]) if cell is not None else None for cell in row)
        for row in original
    )
    assert recover_glyph_grid(collision) == ()

    # A rendered glyph may expand to two text-layer characters; never guess.
    expanded = [list(row) for row in original]
    expanded[0][0] = ENCODE["1"] * 2
    assert recover_glyph_grid(tuple(tuple(row) for row in expanded)) == ()
