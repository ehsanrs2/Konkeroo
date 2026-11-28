"""Append-only private practice events; no scheduler or mastery inference."""

import hashlib
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from english_exam.m4_practice import Assessment, Feedback, PracticeSession, Prompt, Rating

_APPLICATION_ID = 0x4B455654
_SCHEMA_VERSION = 1
_MAX_EPOCH = 253402300799  # 9999-12-31T23:59:59Z
_COLUMNS = (
    "sequence, event_id, learner_id, snapshot_sha256, artifact_sha256, unit_id, occurred_at, rating"
)


@dataclass(frozen=True)
class LearnerEvent:
    sequence: int
    event_id: str
    learner_id: str
    snapshot_sha256: str
    artifact_sha256: str
    unit_id: str
    occurred_at: int
    rating: Rating


def _identifier(value: str) -> None:
    if not isinstance(value, str) or not value or len(value) > 128 or value.strip() != value:
        raise ValueError("Invalid identifier")
    if any(char.isspace() or not char.isprintable() for char in value):
        raise ValueError("Invalid identifier")


def _digest(value: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError("Invalid SHA-256")
    if any(char not in "0123456789abcdef" for char in value):
        raise ValueError("Invalid SHA-256")


def _timestamp(value: int) -> None:
    if type(value) is not int or not 0 <= value <= _MAX_EPOCH:
        raise ValueError("Expected UTC integer epoch seconds")


class LearnerEventStore:
    """A separate local database and a pinned, in-memory content snapshot.

    Input must be an immutable, checkpointed SQLite file. The store is intended
    for one calling thread per connection; SQLite serializes concurrent writers.
    """

    def __init__(self, content_path: Path, expected_sha256: str, learner_path: Path):
        _digest(expected_sha256)
        content_path = Path(content_path).resolve(strict=True)
        learner_path = Path(learner_path).resolve()
        if learner_path == content_path or (
            learner_path.exists() and learner_path.samefile(content_path)
        ):
            raise ValueError("Learner and content databases must be separate")
        for suffix in ("-wal", "-shm", "-journal"):
            if Path(str(content_path) + suffix).exists():
                raise ValueError("Content snapshot must be checkpointed")
        blob = content_path.read_bytes()
        if hashlib.sha256(blob).hexdigest() != expected_sha256:
            raise ValueError("Content snapshot digest mismatch")
        self._snapshot_sha256 = expected_sha256
        self._content = sqlite3.connect(":memory:")
        try:
            self._content.deserialize(blob)
            self._content.execute("PRAGMA query_only=ON")
            if self._content.execute("PRAGMA quick_check").fetchall() != [("ok",)]:
                raise ValueError("Invalid content snapshot")
            self._content.execute(
                "SELECT artifact_sha256, unit_id, concept_id, unit_type, prompt, "
                "review_eligibility FROM learning_unit_prompt LIMIT 0"
            )
            self._content.execute(
                "SELECT artifact_sha256, unit_id, expected_answer, feedback_fa, "
                "grading_guidance_fa FROM learning_unit_feedback LIMIT 0"
            )
            self._db = sqlite3.connect(learner_path)
            try:
                self._initialize()
            except BaseException:
                self._db.close()
                raise
        except BaseException:
            self._content.close()
            raise

    def _initialize(self) -> None:
        with self._db:
            self._db.execute("BEGIN IMMEDIATE")
            app_id = self._db.execute("PRAGMA application_id").fetchone()[0]
            version = self._db.execute("PRAGMA user_version").fetchone()[0]
            if (app_id, version) == (_APPLICATION_ID, _SCHEMA_VERSION):
                self._db.execute(f"SELECT {_COLUMNS} FROM learner_event LIMIT 0")
                return
            has_objects = self._db.execute("SELECT 1 FROM sqlite_schema LIMIT 1").fetchone()
            if (app_id, version) != (0, 0) or has_objects:
                raise ValueError("Unrecognized learner database")
            self._db.execute(
                """
                CREATE TABLE learner_event (
                    sequence INTEGER PRIMARY KEY,
                    event_id TEXT NOT NULL UNIQUE,
                    learner_id TEXT NOT NULL,
                    snapshot_sha256 TEXT NOT NULL,
                    artifact_sha256 TEXT NOT NULL,
                    unit_id TEXT NOT NULL,
                    occurred_at INTEGER NOT NULL CHECK(occurred_at >= 0),
                    rating TEXT NOT NULL CHECK(rating IN ('again', 'hard', 'good', 'easy'))
                )
                """
            )
            self._db.execute(
                "CREATE INDEX learner_event_history ON learner_event "
                "(learner_id, snapshot_sha256, artifact_sha256, unit_id, occurred_at)"
            )
            self._db.execute(f"PRAGMA application_id={_APPLICATION_ID}")
            self._db.execute(f"PRAGMA user_version={_SCHEMA_VERSION}")

    @property
    def snapshot_sha256(self) -> str:
        return self._snapshot_sha256

    def close(self) -> None:
        self._db.close()
        self._content.close()

    def begin(
        self, learner_id: str, event_id: str, artifact_sha256: str, unit_id: str
    ) -> "_RecordedPracticeSession":
        _identifier(learner_id)
        _identifier(event_id)
        _identifier(unit_id)
        _digest(artifact_sha256)
        practice = PracticeSession(self._content, artifact_sha256, unit_id)
        return _RecordedPracticeSession(self, practice, learner_id, event_id)

    def history(self, learner_id: str) -> tuple[LearnerEvent, ...]:
        """Replay order for this learner and exact content snapshot only."""
        _identifier(learner_id)
        rows = self._db.execute(
            f"SELECT {_COLUMNS} FROM learner_event "
            "WHERE learner_id=? AND snapshot_sha256=? ORDER BY sequence",
            (learner_id, self.snapshot_sha256),
        )
        return tuple(LearnerEvent(*row) for row in rows)

    def _append(
        self, learner_id: str, event_id: str, assessment: Assessment, occurred_at: int
    ) -> LearnerEvent:
        _identifier(learner_id)
        _identifier(event_id)
        _identifier(assessment.unit_id)
        _digest(assessment.artifact_sha256)
        _timestamp(occurred_at)
        # Revalidate the exact unit, including its eligibility, before any write.
        PracticeSession(self._content, assessment.artifact_sha256, assessment.unit_id)
        payload = (
            event_id,
            learner_id,
            self.snapshot_sha256,
            assessment.artifact_sha256,
            assessment.unit_id,
            occurred_at,
            assessment.rating,
        )
        with self._db:
            self._db.execute("BEGIN IMMEDIATE")
            existing = self._db.execute(
                f"SELECT {_COLUMNS} FROM learner_event WHERE event_id=?", (event_id,)
            ).fetchone()
            if existing is not None:
                if existing[1:] != payload:
                    raise ValueError("Conflicting event ID")
                return LearnerEvent(*existing)
            latest = self._db.execute(
                "SELECT MAX(occurred_at) FROM learner_event WHERE learner_id=? "
                "AND snapshot_sha256=? AND artifact_sha256=? AND unit_id=?",
                payload[1:5],
            ).fetchone()[0]
            if latest is not None and occurred_at < latest:
                raise ValueError("Backdated event")
            cur = self._db.execute(
                "INSERT INTO learner_event (event_id, learner_id, snapshot_sha256, "
                "artifact_sha256, unit_id, occurred_at, rating) VALUES (?, ?, ?, ?, ?, ?, ?)",
                payload,
            )
            return LearnerEvent(cur.lastrowid, *payload)


class _RecordedPracticeSession:
    """Complete the existing practice lifecycle before appending an event."""

    def __init__(
        self, store: LearnerEventStore, practice: PracticeSession, learner_id: str, event_id: str
    ):
        self._store = store
        self._practice = practice
        self._learner_id = learner_id
        self._event_id = event_id
        self._completion: tuple[Assessment, int] | None = None

    @property
    def prompt(self) -> Prompt:
        return self._practice.prompt

    def record_attempt(self) -> None:
        self._practice.record_attempt()

    def reveal(self) -> Feedback:
        return self._practice.reveal()

    def complete(self, rating: Rating, occurred_at: int) -> LearnerEvent:
        _timestamp(occurred_at)
        if self._completion is None:
            self._completion = (self._practice.assess(rating), occurred_at)
        assessment, timestamp = self._completion
        if (rating, occurred_at) != (assessment.rating, timestamp):
            raise ValueError("Completion already fixed")
        # A failed transaction can be retried with the identical completion.
        return self._store._append(self._learner_id, self._event_id, assessment, timestamp)
