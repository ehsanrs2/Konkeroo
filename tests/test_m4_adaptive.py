import hashlib
import sqlite3

import pytest

from english_exam.m4_adaptive import ADAPTIVE_VERSION, build_adaptive_queue
from english_exam.m4_events import LearnerEventStore
from english_exam.m4_pilot import SessionConfig, main, run_session
from english_exam.m4_scheduler import DAY_SECONDS, replay_state

A = "a" * 64
K = "b" * 64
R = "c" * 64
C = "d" * 64


def _content(path):
    con = sqlite3.connect(path)
    with con:
        con.executescript(
            """
            CREATE TABLE learning_unit (
                artifact_sha256 TEXT, unit_id TEXT, knowledge_sha256 TEXT,
                concept_id TEXT, unit_type TEXT, prompt TEXT, review_eligibility TEXT,
                PRIMARY KEY (artifact_sha256, unit_id)
            );
            CREATE VIEW learning_unit_prompt AS SELECT * FROM learning_unit;
            CREATE TABLE learning_unit_feedback (
                artifact_sha256 TEXT, unit_id TEXT, expected_answer TEXT, feedback_fa TEXT,
                grading_guidance_fa TEXT, PRIMARY KEY (artifact_sha256, unit_id)
            );
            CREATE TABLE concept_cluster_member (
                audit_sha256 TEXT, cluster_id TEXT, knowledge_sha256 TEXT, concept_id TEXT
            );
            CREATE TABLE sense_review_mapping (
                review_sha256 TEXT, prior_audit_sha256 TEXT, prior_cluster_id TEXT, cluster_id TEXT
            );
            CREATE TABLE sense_review_cluster (
                review_sha256 TEXT, cluster_id TEXT, kind TEXT, source_anchored_question_count INT
            );
            """
        )
        for cluster, kind, count in (
            ("low", "vocabulary", 1),
            ("high", "vocabulary", 5),
            ("grammar", "grammar", 0),
        ):
            con.execute(
                "INSERT INTO sense_review_cluster VALUES (?, ?, ?, ?)", (R, cluster, kind, count)
            )
            con.execute(
                "INSERT INTO sense_review_mapping VALUES (?, ?, ?, ?)", (R, C, cluster, cluster)
            )
        for unit, cluster, prompt in (
            ("a", "low", "Low one"),
            ("b", "low", "Low two"),
            ("c", "high", "High one"),
            ("d", "high", "High two"),
            ("e", "grammar", "Grammar"),
            ("f", "grammar", "High one"),
            ("blocked", "high", "Blocked"),
        ):
            gate = "REVIEW_REQUIRED" if unit == "blocked" else "PRIVATE_PILOT_ONLY"
            con.execute(
                "INSERT INTO learning_unit VALUES (?, ?, ?, ?, 'MEANING_RECALL', ?, ?)",
                (A, unit, K, unit, prompt, gate),
            )
            con.execute(
                "INSERT INTO concept_cluster_member VALUES (?, ?, ?, ?)", (C, cluster, K, unit)
            )
            con.execute(
                "INSERT INTO learning_unit_feedback VALUES (?, ?, 'answer', 'feedback', 'guide')",
                (A, unit),
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


def _queue(store, now=100, due_limit=10, new_limit=10, learner="local-1"):
    return build_adaptive_queue(
        store,
        learner,
        now,
        review_sha256=R,
        audit_sha256=C,
        due_limit=due_limit,
        new_limit=new_limit,
    )


def _review(store, unit, rating, at, event_id, learner="local-1"):
    session = store.begin(learner, event_id, A, unit)
    session.record_attempt()
    session.reveal()
    return session.complete(rating, at)


def test_frequency_diversity_and_duplicate_deferral(store):
    queue = _queue(store)
    assert queue.adaptive_version == ADAPTIVE_VERSION
    assert queue.review_sha256 == R
    assert [item.unit_id for item in queue.new] == ["c", "a", "e", "d", "b"]
    assert queue.progress.eligible == queue.progress.new == 6
    assert queue.progress.events == queue.progress.reviewed == 0
    assert _queue(store, new_limit=2).new == queue.new[:2]
    assert store.history("local-1") == ()


def test_weak_signal_ranks_new_without_transferring_state(store):
    _review(store, "a", "again", 100, "event-1")
    queue = _queue(store)
    assert queue.new[0].unit_id == "b"
    assert queue.progress.latest_again == 1
    assert queue.progress.new == 5
    assert len(replay_state(store, "local-1")) == 1
    assert _queue(store, learner="local-2").new[0].unit_id == "c"
    _review(store, "a", "good", 101, "event-2")
    assert _queue(store, now=101).new[0].unit_id == "c"


def test_due_backlog_and_tie_order(store):
    _review(store, "c", "again", 100, "event-1")
    _review(store, "a", "again", 100, "event-2")
    queue = _queue(store, now=700, due_limit=1)
    assert [state.unit_id for state in queue.due] == ["a"]
    assert queue.new == ()
    assert queue.progress.due == 2
    queue = _queue(store, now=700, due_limit=2)
    assert [state.unit_id for state in queue.due] == ["a", "c"]
    assert "f" not in [item.unit_id for item in queue.new]
    assert queue.progress.new == 4
    assert _queue(store, now=700, due_limit=0).new == ()


def test_progress_latest_not_event_count(store):
    _review(store, "a", "again", 100, "event-1")
    _review(store, "a", "hard", 200, "event-2")
    _review(store, "e", "easy", 100, "event-3")
    queue = _queue(store, now=DAY_SECONDS + 200, new_limit=0)
    assert queue.new == ()
    assert queue.progress.events == 3
    assert queue.progress.reviewed == 2
    assert queue.progress.latest_again == 0
    assert queue.progress.latest_hard == queue.progress.latest_easy == 1
    assert queue.progress.due == 1
    groups = dict(queue.by_kind)
    assert groups["grammar"].events == groups["grammar"].latest_easy == 1
    assert groups["vocabulary"].events == 2
    assert sum(group.eligible for group in groups.values()) == 6


def test_reopen(files):
    store = LearnerEventStore(*files)
    try:
        _review(store, "a", "hard", 100, "event-1")
        before = _queue(store)
    finally:
        store.close()
    reopened = LearnerEventStore(*files)
    try:
        assert _queue(reopened) == before
    finally:
        reopened.close()
    assert hashlib.sha256(files[0].read_bytes()).hexdigest() == files[1]


@pytest.mark.parametrize("revision,audit", [("e" * 64, C), (R, "e" * 64), ("bad", C)])
def test_invalid_mapping_pin(store, revision, audit):
    with pytest.raises(ValueError):
        build_adaptive_queue(
            store,
            "local-1",
            100,
            review_sha256=revision,
            audit_sha256=audit,
            due_limit=1,
            new_limit=1,
        )


@pytest.mark.parametrize("operation", ["DELETE", "DUPLICATE"])
def test_incomplete_or_duplicate_mapping(files, operation):
    con = sqlite3.connect(files[0])
    with con:
        if operation == "DELETE":
            con.execute("DELETE FROM concept_cluster_member WHERE concept_id='a'")
        else:
            con.execute(
                "INSERT INTO concept_cluster_member SELECT * FROM concept_cluster_member "
                "WHERE concept_id='a'"
            )
    con.close()
    digest = hashlib.sha256(files[0].read_bytes()).hexdigest()
    store = LearnerEventStore(files[0], digest, files[2])
    try:
        with pytest.raises(ValueError, match="Incomplete or duplicate cluster mapping"):
            _queue(store)
    finally:
        store.close()


@pytest.mark.parametrize("now", [True, -1, 1.5])
def test_invalid_time(store, now):
    with pytest.raises(ValueError, match="UTC integer epoch"):
        _queue(store, now=now)


@pytest.mark.parametrize("limit", [True, -1, 1.5])
def test_invalid_limits(store, limit):
    with pytest.raises(ValueError, match="nonnegative integer limit"):
        _queue(store, due_limit=limit)
    with pytest.raises(ValueError, match="nonnegative integer limit"):
        _queue(store, new_limit=limit)


def test_future_or_gated_event_fails_closed(store):
    _review(store, "a", "good", 100, "event-1")
    with pytest.raises(ValueError, match="precedes recorded review"):
        _queue(store, now=99)
    with store._db:
        store._db.execute("UPDATE learner_event SET unit_id='blocked'")
    with pytest.raises(ValueError, match="outside eligible snapshot history"):
        _queue(store)


def _pilot(store, answers, *, now=100, due_limit=2, new_limit=2):
    outputs = []
    inputs = iter(answers)

    def read(_prompt):
        return next(inputs, "q")

    config = SessionConfig("local-1", R, C, due_limit, new_limit)
    completed = run_session(store, config, read=read, write=outputs.append, clock=lambda: now)
    return completed, outputs


def test_pilot_quit_before_reveal(store):
    completed, outputs = _pilot(store, ["wrong", "q"])
    assert completed == 0
    assert any("Invalid choice" in line for line in outputs)
    assert not any("Expected answer:" in line for line in outputs)
    assert store.history("local-1") == ()


def test_pilot_quit_after_reveal(store):
    completed, outputs = _pilot(store, ["r", "q"])
    assert completed == 0
    assert "Expected answer: answer" in outputs
    assert store.history("local-1") == ()


def test_pilot_rating_and_resume(files):
    store = LearnerEventStore(*files)
    try:
        completed, outputs = _pilot(store, ["r", "wrong", "again", "q"])
        assert completed == 1
        assert any("Saved. Next review (UTC):" in line for line in outputs)
        assert "Session completed ratings: 1/2" in outputs
        assert len(store.history("local-1")) == 1
    finally:
        store.close()
    reopened = LearnerEventStore(*files)
    try:
        completed, outputs = _pilot(reopened, ["r", "good"], now=700, new_limit=0)
        assert completed == 1
        assert any("[1/1] Due" in line for line in outputs)
        history = reopened.history("local-1")
        assert len(history) == 2
        assert history[0].unit_id == history[1].unit_id
        assert replay_state(reopened, "local-1")[0].interval_seconds == 2 * DAY_SECONDS
    finally:
        reopened.close()


@pytest.mark.parametrize("interrupt", [EOFError, KeyboardInterrupt])
def test_pilot_interrupted_after_attempt(store, interrupt):
    outputs = []
    answers = iter(["r"])

    def read(_prompt):
        choice = next(answers, None)
        if choice is None:
            raise interrupt
        return choice

    completed = run_session(
        store,
        SessionConfig("local-1", R, C),
        read=read,
        write=outputs.append,
        clock=lambda: 100,
    )
    assert completed == 0
    assert any("Session interrupted" in line for line in outputs)
    assert store.history("local-1") == ()


def test_pilot_zero_limits(store):
    completed, outputs = _pilot(store, [], due_limit=0, new_limit=0)
    assert completed == 0
    assert "Session completed ratings: 0/0" in outputs
    assert store.history("local-1") == ()


def _cli_args(files, digest):
    return [
        "--content",
        str(files[0]),
        "--content-sha256",
        digest,
        "--learner-db",
        str(files[2]),
        "--learner-id",
        "local-1",
        "--review-sha256",
        R,
        "--audit-sha256",
        C,
        "--due-limit",
        "0",
        "--new-limit",
        "0",
    ]


def test_pilot_cli_summary(files, capsys):
    assert main(_cli_args(files, files[1])) == 0
    assert "Reviewed: 0/6" in capsys.readouterr().out
    assert files[2].exists()


def test_pilot_cli_bad_digest(files, capsys):
    assert main(_cli_args(files, "f" * 64)) == 1
    assert "digest mismatch" in capsys.readouterr().err
    assert not files[2].exists()
