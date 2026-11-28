import hashlib
import sqlite3

import pytest

from english_exam.m4_events import LearnerEventStore
from english_exam.m4_scheduler import (
    DAY_SECONDS,
    MAX_EPOCH,
    MAX_INTERVAL,
    SCHEDULER_VERSION,
    build_queue,
    next_interval,
    replay_state,
)

A = "a" * 64
B = "b" * 64


def _content(path, prompt="Synthetic prompt"):
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
            (B, "one", "PRIVATE_PILOT_ONLY"),
            (A, "two", "PRIVATE_PILOT_ONLY"),
            (A, "blocked", "REVIEW_REQUIRED"),
            (A, "one", "PRIVATE_PILOT_ONLY"),
        ):
            con.execute(
                "INSERT INTO learning_unit_prompt VALUES (?, ?, 'shared', 'MEANING_RECALL', ?, ?)",
                (artifact, unit, prompt, gate),
            )
            con.execute(
                "INSERT INTO learning_unit_feedback VALUES (?, ?, 'answer', 'feedback', 'guide')",
                (artifact, unit),
            )
    con.close()
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


def _review(store, event_id, rating, at, artifact=A, unit="one", learner="local-1"):
    session = store.begin(learner, event_id, artifact, unit)
    session.record_attempt()
    session.reveal()
    return session.complete(rating, at)


@pytest.mark.parametrize(
    ("rating", "expected"),
    [("again", 600), ("hard", DAY_SECONDS), ("good", 2 * DAY_SECONDS), ("easy", 4 * DAY_SECONDS)],
)
def test_initial_intervals(rating, expected):
    assert next_interval(None, rating) == expected


@pytest.mark.parametrize(
    ("previous", "rating", "expected"),
    [
        (7 * DAY_SECONDS + 1, "hard", 725761),
        (7 * DAY_SECONDS, "good", 14 * DAY_SECONDS),
        (7 * DAY_SECONDS, "easy", 21 * DAY_SECONDS),
        (MAX_INTERVAL, "again", 600),
        (600, "hard", DAY_SECONDS),
        (600, "good", 2 * DAY_SECONDS),
        (600, "easy", 4 * DAY_SECONDS),
        (MAX_INTERVAL, "hard", MAX_INTERVAL),
        (MAX_INTERVAL, "good", MAX_INTERVAL),
        (MAX_INTERVAL, "easy", MAX_INTERVAL),
    ],
)
def test_subsequent_intervals(previous, rating, expected):
    assert next_interval(previous, rating) == expected


@pytest.mark.parametrize("previous", [True, 0, -1, 1.5, MAX_INTERVAL + 1])
def test_invalid_interval(previous):
    with pytest.raises(ValueError, match="Invalid previous interval"):
        next_interval(previous, "good")


def test_invalid_rating():
    with pytest.raises(ValueError, match="Invalid self-assessment"):
        next_interval(None, "invalid")


def test_new_queue_is_stable_and_gated(store):
    assert store.eligible_unit_revisions() == ((A, "one"), (A, "two"), (B, "one"))
    queue = build_queue(store, "local-1", 0, due_limit=10, new_limit=2)
    assert queue.scheduler_version == SCHEDULER_VERSION
    assert queue.due == ()
    assert queue.due_count == 0
    assert queue.new == ((A, "one"), (A, "two"))
    assert queue.new_count == 3
    assert store.history("local-1") == ()


def test_due_boundary_and_independent_duplicate_prompt(store):
    _review(store, "event-1", "again", 100)
    early = build_queue(store, "local-1", 699, due_limit=10, new_limit=10)
    assert early.due == ()
    assert early.new == ((A, "two"), (B, "one"))
    boundary = build_queue(store, "local-1", 700, due_limit=10, new_limit=10)
    assert len(boundary.due) == 1
    assert boundary.due[0].unit_id == "one"
    assert boundary.due[0].artifact_sha256 == A
    assert boundary.new == early.new
    assert len(replay_state(store, "local-1")) == 1


def test_due_order_and_limits(store):
    _review(store, "event-1", "again", 100, artifact=B)
    _review(store, "event-2", "again", 100)
    _review(store, "event-3", "again", 50, unit="two")
    queue = build_queue(store, "local-1", 700, due_limit=2, new_limit=0)
    assert [(state.artifact_sha256, state.unit_id) for state in queue.due] == [
        (A, "two"),
        (A, "one"),
    ]
    assert queue.due_count == 3
    assert queue.new_count == 0
    empty = build_queue(store, "local-1", 700, due_limit=0, new_limit=0)
    assert empty.due == empty.new == ()
    assert empty.due_count == 3


def test_replay_actual_time_reset_and_retry(store):
    first = _review(store, "event-1", "good", 100)
    assert _review(store, "event-1", "good", 100) == first
    _review(store, "event-2", "good", 10 * DAY_SECONDS)
    state = replay_state(store, "local-1")[0]
    assert state.review_count == 2
    assert state.interval_seconds == 4 * DAY_SECONDS
    assert state.due_at == 14 * DAY_SECONDS
    _review(store, "event-3", "again", 11 * DAY_SECONDS)
    state = replay_state(store, "local-1")[0]
    assert state.review_count == 3
    assert state.due_at == 11 * DAY_SECONDS + 600
    assert state.interval_seconds == 600


def test_restart_and_learner_snapshot_isolation(files, tmp_path):
    store = LearnerEventStore(*files)
    try:
        _review(store, "event-1", "hard", 100)
        _review(store, "event-2", "easy", 100, learner="local-2")
        before = replay_state(store, "local-1")
        queue = build_queue(store, "local-1", DAY_SECONDS + 100, due_limit=10, new_limit=10)
    finally:
        store.close()
    reopened = LearnerEventStore(*files)
    changed = tmp_path / "changed.db"
    updated = LearnerEventStore(changed, _content(changed, "New prompt"), files[2])
    try:
        assert replay_state(reopened, "local-1") == before
        after = build_queue(reopened, "local-1", DAY_SECONDS + 100, due_limit=10, new_limit=10)
        assert after == queue
        assert replay_state(reopened, "local-2")[0].interval_seconds == 4 * DAY_SECONDS
        assert replay_state(updated, "local-1") == ()
        assert build_queue(updated, "local-1", 100, due_limit=10, new_limit=10).new_count == 3
    finally:
        updated.close()
        reopened.close()
    assert hashlib.sha256(files[0].read_bytes()).hexdigest() == files[1]


def test_transaction_failure_does_not_change_projection(store):
    _review(store, "event-1", "hard", 100)
    before = replay_state(store, "local-1")
    with store._db:
        store._db.execute(
            "CREATE TRIGGER reject_event AFTER INSERT ON learner_event "
            "BEGIN SELECT RAISE(ABORT, 'synthetic failure'); END"
        )
    with pytest.raises(sqlite3.IntegrityError, match="synthetic failure"):
        _review(store, "event-2", "easy", 101)
    assert replay_state(store, "local-1") == before


def test_maximum_epoch(store):
    _review(store, "event-1", "easy", MAX_EPOCH - 1)
    state = replay_state(store, "local-1")[0]
    assert state.interval_seconds == 4 * DAY_SECONDS
    assert state.due_at == MAX_EPOCH


@pytest.mark.parametrize("now", [True, -1, 1.5, MAX_EPOCH + 1])
def test_invalid_queue_time(store, now):
    with pytest.raises(ValueError, match="UTC integer epoch"):
        build_queue(store, "local-1", now, due_limit=10, new_limit=10)


@pytest.mark.parametrize("limit", [True, -1, 1.5])
def test_invalid_queue_limits(store, limit):
    with pytest.raises(ValueError, match="nonnegative integer limit"):
        build_queue(store, "local-1", 100, due_limit=limit, new_limit=10)
    with pytest.raises(ValueError, match="nonnegative integer limit"):
        build_queue(store, "local-1", 100, due_limit=10, new_limit=limit)


def test_queue_rejects_time_before_event(store):
    _review(store, "event-1", "good", 100)
    with pytest.raises(ValueError, match="precedes recorded review"):
        build_queue(store, "local-1", 99, due_limit=10, new_limit=10)


def test_replay_rejects_corrupted_gate_history(store):
    _review(store, "event-1", "good", 100)
    with store._db:
        store._db.execute("UPDATE learner_event SET unit_id='blocked'")
    with pytest.raises(ValueError, match="outside eligible snapshot history"):
        replay_state(store, "local-1")
