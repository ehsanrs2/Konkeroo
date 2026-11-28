import hashlib
import json
import sqlite3
from contextlib import closing

import pytest

from english_exam.m4_batch import prepare_batch


@pytest.fixture
def database(tmp_path):
    path = tmp_path / "synthetic.sqlite3"
    with closing(sqlite3.connect(path)) as con:
        con.executescript("""
            CREATE TABLE exam_alignment (year, exam_booklet_code, first_question, last_question);
            CREATE TABLE content_review (year, status);
            CREATE TABLE exam_section (year, section, printed_title, directions);
            CREATE TABLE exam_passage (year, passage_id, kind, printed_label, body, pdf_pages_json);
            CREATE TABLE exam_passage_emphasis (year, passage_id, term);
            CREATE TABLE exam_question (
                year, question_number, question_id, section, stem, cloze_blank_number,
                passage_id, pdf_page, content_review_status, answer_hint
            );
            CREATE TABLE exam_option (year, question_number, position, body);
            CREATE TABLE key_transcription (year, answer);
            INSERT INTO key_transcription VALUES (9001, 'SECRET_MARKER');
        """)
        confirmed = "OWNER_CONFIRMED_TRANSCRIPTION"
        for year, count in [(9001, 2), (9002, 1)]:
            con.execute("INSERT INTO exam_alignment VALUES (?, 'TESTA', 1, ?)", (year, count))
            con.execute("INSERT INTO content_review VALUES (?, ?)", (year, confirmed))
            con.execute(
                "INSERT INTO exam_section VALUES (?, 'vocabulary', 'Test', 'Choose')", (year,)
            )
            for n in range(1, count + 1):
                con.execute(
                    "INSERT INTO exam_question VALUES (?, ?, ?, 'vocabulary', 'Blank', "
                    "NULL, NULL, 2, ?, 'SECRET_MARKER')",
                    (year, n, f"{year}-{n}", confirmed),
                )
                con.executemany(
                    "INSERT INTO exam_option VALUES (?, ?, ?, 'Synthetic choice')",
                    [(year, n, position) for position in range(1, 5)],
                )
        con.commit()
    return path


def digest(database):
    return hashlib.sha256(database.read_bytes()).hexdigest()


def test_prepare_batch(database):
    before = digest(database)
    files = prepare_batch(database, before, [9002, 9001])
    assert files == prepare_batch(database, before, [9001, 9002])
    assert set(files) == {"manifest.json", "packet_9001.json", "packet_9002.json"}
    manifest = json.loads(files["manifest.json"])
    assert manifest["questions"] == 3
    assert manifest["status"] == "PACKETS_PREPARED_NOT_SOLVED"
    assert manifest["publication_status"] == "BLOCKED"
    assert [entry["questions"] for entry in manifest["packets"]] == [2, 1]
    for entry in manifest["packets"]:
        data = files[entry["file"]]
        assert hashlib.sha256(data).hexdigest() == entry["sha256"]
        assert b"SECRET_MARKER" not in data
    assert digest(database) == before


@pytest.mark.parametrize("years", [[], [9001, 9001], [9001, 9003]])
def test_reject_invalid_years(database, years):
    with pytest.raises(ValueError):
        prepare_batch(database, digest(database), years)


def test_reject_digest_mismatch(database):
    with pytest.raises(ValueError, match="digest mismatch"):
        prepare_batch(database, "wrong", [9001])


def test_reject_incomplete_second_packet(database):
    with closing(sqlite3.connect(database)) as con:
        con.execute("DELETE FROM exam_option WHERE year=9002 AND position=4")
        con.commit()
    with pytest.raises(ValueError, match="option coverage"):
        prepare_batch(database, digest(database), [9001, 9002])


def test_reject_duplicate_cross_year_identity(database):
    with closing(sqlite3.connect(database)) as con:
        con.execute("UPDATE exam_question SET question_id='9001-1' WHERE year=9002")
        con.commit()
    with pytest.raises(ValueError, match="Duplicate question identity"):
        prepare_batch(database, digest(database), [9001, 9002])
