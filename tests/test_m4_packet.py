"""Synthetic-only tests for the M4 content boundary."""

import json
import sqlite3

import pytest

from english_exam.m4_packet import export_packet


@pytest.fixture
def database(tmp_path):
    path = tmp_path / "synthetic.sqlite3"
    con = sqlite3.connect(path)
    con.executescript("""
        CREATE TABLE exam_alignment (
            year, exam_booklet_code, first_question, last_question
        );
        CREATE TABLE content_review (year, status);
        CREATE TABLE exam_section (year, section, printed_title, directions);
        CREATE TABLE exam_passage (year, passage_id, kind, printed_label, body, pdf_pages_json);
        CREATE TABLE exam_passage_emphasis (year, passage_id, term);
        CREATE TABLE exam_question (
            year, question_number, question_id, section, stem, cloze_blank_number,
            passage_id, pdf_page, content_review_status, answer_hint
        );
        CREATE TABLE exam_option (year, question_number, position, body, is_correct);
        CREATE TABLE key_transcription (year, answer);
        CREATE TABLE ai_solution (year, answer);
        INSERT INTO exam_alignment VALUES (9999, 'TESTA', 1, 2);
        INSERT INTO content_review VALUES (9999, 'OWNER_CONFIRMED_TRANSCRIPTION');
        INSERT INTO exam_section VALUES (9999, 'vocabulary', 'Synthetic', 'Choose one');
        INSERT INTO exam_section VALUES (9999, 'reading', 'Synthetic', 'Read');
        INSERT INTO exam_passage VALUES (9999, 'p1', 'reading', 'Example', 'Made up', '[2]');
        INSERT INTO exam_passage_emphasis VALUES (9999, 'p1', 'up');
        INSERT INTO exam_question VALUES
          (9999, 1, 'a', 'vocabulary', 'Synthetic blank', NULL, NULL, 2,
           'OWNER_CONFIRMED_TRANSCRIPTION', 'SECRET_MARKER'),
          (9999, 2, 'b', 'reading', 'Synthetic question', NULL, 'p1', 2,
           'OWNER_CONFIRMED_TRANSCRIPTION', 'SECRET_MARKER');
        INSERT INTO key_transcription VALUES (9999, 'SECRET_MARKER');
        INSERT INTO ai_solution VALUES (9999, 'SECRET_MARKER');
    """)
    con.executemany(
        "INSERT INTO exam_option VALUES (9999, ?, ?, ?, 'SECRET_MARKER')",
        [(n, p, f"Choice {p}") for n in (1, 2) for p in range(1, 5)],
    )
    con.commit()
    con.close()
    return path


def test_key_free_deterministic_export(database):
    before = database.read_bytes()
    packet = export_packet(database, 9999, "TESTA")
    assert packet == export_packet(database, 9999, "TESTA")
    assert database.read_bytes() == before
    assert len(packet["exam_question"]) == 2
    assert len(packet["exam_option"]) == 8
    assert len(packet["exam_passage_emphasis"]) == 1
    assert set(packet) == {
        "year",
        "booklet",
        "source_db_sha256",
        "exam_section",
        "exam_passage",
        "exam_passage_emphasis",
        "exam_question",
        "exam_option",
    }
    assert "SECRET_MARKER" not in json.dumps(packet)
    assert "answer_hint" not in packet["exam_question"][0]
    assert "is_correct" not in packet["exam_option"][0]


def test_wrong_booklet(database):
    with pytest.raises(ValueError, match="identity"):
        export_packet(database, 9999, "TESTB")


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("UPDATE content_review SET status='PENDING'", "not confirmed"),
        ("UPDATE exam_question SET content_review_status='PENDING'", "Unconfirmed"),
        ("DELETE FROM exam_question WHERE question_number=2", "question coverage"),
        ("DELETE FROM exam_option WHERE position=4", "option coverage"),
        ("UPDATE exam_question SET passage_id='unknown' WHERE question_number=2", "association"),
        ("UPDATE exam_question SET question_id='a' WHERE question_number=2", "Duplicate"),
        ("UPDATE exam_passage_emphasis SET passage_id='unknown'", "emphasized"),
    ],
)
def test_reject_invalid_content(database, mutation, message):
    con = sqlite3.connect(database)
    con.execute(mutation)
    con.commit()
    con.close()
    with pytest.raises(ValueError, match=message):
        export_packet(database, 9999, "TESTA")
