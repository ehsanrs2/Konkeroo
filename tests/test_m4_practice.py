import sqlite3

import pytest

from english_exam.m4_practice import PracticeSession


@pytest.fixture
def database():
    with sqlite3.connect(":memory:") as con:
        con.executescript("""
            CREATE TABLE learning_unit_prompt (
                artifact_sha256, unit_id, concept_id, unit_type, prompt, review_eligibility
            );
            CREATE TABLE learning_unit_feedback (
                artifact_sha256, unit_id, expected_answer, feedback_fa, grading_guidance_fa
            );
            INSERT INTO learning_unit_prompt VALUES
                ('revision', 'u1', 'c1', 'MEANING_RECALL', 'Synthetic prompt',
                 'PRIVATE_PILOT_ONLY'),
                ('revision', 'u2', 'c2', 'MEANING_RECALL', 'Blocked prompt', 'REVIEW_REQUIRED');
            INSERT INTO learning_unit_feedback VALUES
                ('revision', 'u1', 'SECRET', 'Explanation', 'Self-assess');
        """)
        yield con


def test_practice_cycle(database):
    session = PracticeSession(database, "revision", "u1")
    assert session.prompt.text == "Synthetic prompt"
    assert "SECRET" not in repr(session.prompt)
    with pytest.raises(ValueError, match="requires an attempt"):
        session.reveal()
    with pytest.raises(ValueError, match="requires revealed"):
        session.assess("good")
    session.record_attempt()
    with pytest.raises(ValueError, match="already recorded"):
        session.record_attempt()
    assert session.reveal().expected_answer == "SECRET"
    with pytest.raises(ValueError, match="Invalid self-assessment"):
        session.assess("invalid")
    event = session.assess("good")
    assert (event.artifact_sha256, event.unit_id, event.rating) == ("revision", "u1", "good")
    with pytest.raises(ValueError, match="requires revealed"):
        session.assess("easy")


def test_revision_and_review_gate(database):
    with pytest.raises(ValueError, match="Unknown unit revision"):
        PracticeSession(database, "wrong", "u1")
    with pytest.raises(ValueError, match="not eligible"):
        PracticeSession(database, "revision", "u2")


def test_missing_feedback(database):
    database.execute("DELETE FROM learning_unit_feedback")
    session = PracticeSession(database, "revision", "u1")
    session.record_attempt()
    with pytest.raises(ValueError, match="Missing or invalid"):
        session.reveal()
