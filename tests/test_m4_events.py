import hashlib
import sqlite3
from datetime import datetime
from pathlib import Path

import pytest

from english_exam.m4_events import LearnerEventStore

A = "a" * 64
B = "b" * 64


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _content(path, text="Synthetic prompt"):
    con = sqlite3.connect(path)
    with con:
        con.executescript(
            """
            CREATE TABLE learning_unit_prompt (
                artifact_sha256 TEXT, unit_id TEXT, concept_id TEXT, unit_type TEXT,
                prompt TEXT, review_eligibility TEXT,
                PRIMARY KEY (artifact_sha256, unit_id)
            );
            CREATE TABLE learning_unit_feedback (
                artifact_sha256 TEXT, unit_id TEXT, expected_answer TEXT, feedback_fa TEXT,
                grading_guidance_fa TEXT, PRIMARY KEY (artifact_sha256, unit_id)
            );
            """
        )
        for artifact, unit, gate in (
            (A, "one", "PRIVATE_PILOT_ONLY"),
            (A, "two", "PRIVATE_PILOT_ONLY"),
            (A, "blocked", "REVIEW_REQUIRED"),
            (B, "one", "PRIVATE_PILOT_ONLY"),
        ):
            con.execute(
                "INSERT INTO learning_unit_prompt VALUES (?, ?, 'shared', 'MEANING_RECALL', ?, ?)",
                (artifact, unit, text, gate),
            )
            con.execute(
                "INSERT INTO learning_unit_feedback VALUES (?, ?, 'answer', 'feedback', 'guide')",
                (artifact, unit),
            )
    con.close()
    return _sha(path)


@pytest.fixture
def files(tmp_path):
    content = tmp_path / "content.db"
    return content, _content(content), tmp_path / "learner.db"


@pytest.fixture
def store(files):
    instance = LearnerEventStore(*files)
    try:
        yield instance
    finally:
        instance.close()


def _ready(store, event_id, learner="local-1", artifact=A, unit="one"):
    session = store.begin(learner, event_id, artifact, unit)
    session.record_attempt()
    session.reveal()
    return session


def test_lifecycle_and_retry(store):
    session = store.begin("local-1", "event-1", A, "one")
    assert session.prompt.text == "Synthetic prompt"
    with pytest.raises(ValueError, match="requires an attempt"):
        session.reveal()
    with pytest.raises(ValueError, match="requires revealed feedback"):
        session.complete("good", 100)
    session.record_attempt()
    with pytest.raises(ValueError, match="requires revealed feedback"):
        session.complete("good", 100)
    assert session.reveal().expected_answer == "answer"
    with pytest.raises(ValueError, match="Invalid self-assessment"):
        session.complete("invalid", 100)
    assert store.history("local-1") == ()
    event = session.complete("good", 100)
    assert event.snapshot_sha256 == store.snapshot_sha256
    assert event.artifact_sha256 == A
    assert event.rating == "good"
    assert session.complete("good", 100) == event
    with pytest.raises(ValueError, match="Completion already fixed"):
        session.complete("hard", 100)
    assert store.history("local-1") == (event,)


@pytest.mark.parametrize("value", [True, -1, 1.5, "100", datetime(2026, 1, 1), 253402300800])
def test_invalid_timestamp(store, value):
    session = _ready(store, "event-1")
    with pytest.raises(ValueError, match="UTC integer epoch"):
        session.complete("good", value)
    assert store.history("local-1") == ()
    assert session.complete("good", 100).occurred_at == 100


def test_gates_and_identity(store):
    with pytest.raises(ValueError, match="not eligible"):
        store.begin("local-1", "event-1", A, "blocked")
    with pytest.raises(ValueError, match="Unknown unit revision"):
        store.begin("local-1", "event-1", "c" * 64, "one")
    with pytest.raises(ValueError, match="Invalid identifier"):
        store.begin("", "event-1", A, "one")
    with pytest.raises(ValueError, match="Invalid identifier"):
        store.begin("local-1", " event-1", A, "one")
    with pytest.raises(ValueError, match="Invalid SHA-256"):
        store.begin("local-1", "event-1", "invalid", "one")
    assert store.history("local-1") == ()


def test_reopen_and_conflicting_replay(files):
    store = LearnerEventStore(*files)
    event = _ready(store, "event-1").complete("good", 100)
    store.close()
    store = LearnerEventStore(*files)
    try:
        assert store.history("local-1") == (event,)
        assert _ready(store, "event-1").complete("good", 100) == event
        with pytest.raises(ValueError, match="Conflicting event ID"):
            _ready(store, "event-1").complete("easy", 100)
        with pytest.raises(ValueError, match="Conflicting event ID"):
            _ready(store, "event-1", learner="local-2").complete("good", 100)
        assert store.history("local-1") == (event,)
    finally:
        store.close()


def test_history_isolation_and_backdating(store):
    first = _ready(store, "event-1").complete("good", 100)
    with pytest.raises(ValueError, match="Backdated event"):
        _ready(store, "event-2").complete("again", 99)
    other = _ready(store, "event-3", unit="two").complete("hard", 50)
    revision = _ready(store, "event-4", artifact=B).complete("easy", 50)
    separate = _ready(store, "event-5", learner="local-2").complete("again", 50)
    tie = _ready(store, "event-6").complete("hard", 100)
    assert store.history("local-1") == (first, other, revision, tie)
    assert store.history("local-2") == (separate,)
    assert _ready(store, "event-1").complete("good", 100) == first


def test_snapshot_isolation(files, tmp_path):
    content, digest, learner = files
    original = LearnerEventStore(content, digest, learner)
    changed = tmp_path / "changed.db"
    updated = LearnerEventStore(changed, _content(changed, "New prompt"), learner)
    try:
        first = _ready(original, "event-1").complete("good", 100)
        assert updated.history("local-1") == ()
        with pytest.raises(ValueError, match="Conflicting event ID"):
            _ready(updated, "event-1").complete("good", 100)
        second = _ready(updated, "event-2").complete("good", 50)
        assert updated.history("local-1") == (second,)
        assert original.history("local-1") == (first,)
    finally:
        updated.close()
        original.close()
    assert _sha(content) == digest


def test_transaction_failure_and_retry(store):
    session = _ready(store, "event-1")
    with store._db:
        store._db.execute(
            "CREATE TRIGGER reject_event AFTER INSERT ON learner_event "
            "BEGIN SELECT RAISE(ABORT, 'synthetic failure'); END"
        )
    with pytest.raises(sqlite3.IntegrityError, match="synthetic failure"):
        session.complete("good", 100)
    assert store.history("local-1") == ()
    with store._db:
        store._db.execute("DROP TRIGGER reject_event")
    assert store.history("local-1") == ()
    event = session.complete("good", 100)
    assert store.history("local-1") == (event,)


def test_bad_digest_and_path_alias(files, tmp_path):
    content, digest, learner = files
    with pytest.raises(ValueError, match="digest mismatch"):
        LearnerEventStore(content, "f" * 64, learner)
    assert not learner.exists()
    with pytest.raises(ValueError, match="must be separate"):
        LearnerEventStore(content, digest, content)
    alias = tmp_path / "alias.db"
    alias.hardlink_to(content)
    with pytest.raises(ValueError, match="must be separate"):
        LearnerEventStore(content, digest, alias)
    assert _sha(content) == digest


def test_uncheckpointed_snapshot(files):
    content, digest, learner = files
    sidecar = Path(str(content) + "-wal")
    sidecar.touch()
    with pytest.raises(ValueError, match="must be checkpointed"):
        LearnerEventStore(content, digest, learner)
    assert not learner.exists()


def test_foreign_database_is_not_modified(files):
    content, digest, learner = files
    con = sqlite3.connect(learner)
    with con:
        con.execute("CREATE TABLE unrelated (value TEXT)")
    con.close()
    before = _sha(learner)
    with pytest.raises(ValueError, match="Unrecognized learner database"):
        LearnerEventStore(content, digest, learner)
    assert _sha(learner) == before
