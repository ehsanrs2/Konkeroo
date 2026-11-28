"""Local provisional practice cycle; not a release or mastery engine."""

import sqlite3
from dataclasses import dataclass
from typing import Literal

Rating = Literal["again", "hard", "good", "easy"]


@dataclass(frozen=True)
class Prompt:
    unit_id: str
    concept_id: str
    unit_type: str
    text: str


@dataclass(frozen=True)
class Feedback:
    expected_answer: str
    explanation: str
    grading_guidance: str


@dataclass(frozen=True)
class Assessment:
    artifact_sha256: str
    unit_id: str
    rating: Rating


class PracticeSession:
    """One in-memory attempt against a pinned private unit revision."""

    def __init__(self, con: sqlite3.Connection, artifact_sha256: str, unit_id: str):
        row = con.execute(
            "SELECT unit_id, concept_id, unit_type, prompt, review_eligibility "
            "FROM learning_unit_prompt WHERE artifact_sha256=? AND unit_id=?",
            (artifact_sha256, unit_id),
        ).fetchone()
        if row is None:
            raise ValueError("Unknown unit revision")
        if row[4] != "PRIVATE_PILOT_ONLY":
            raise ValueError("Unit is not eligible for private practice")
        self.prompt = Prompt(*row[:4])
        self._con = con
        self._artifact = artifact_sha256
        self._state = "presented"

    def record_attempt(self) -> None:
        """Explicitly acknowledge a retrieval attempt, including an abstention."""
        if self._state != "presented":
            raise ValueError("Attempt already recorded")
        self._state = "attempted"

    def reveal(self) -> Feedback:
        if self._state != "attempted":
            raise ValueError("Feedback requires an attempt")
        row = self._con.execute(
            "SELECT expected_answer, feedback_fa, grading_guidance_fa "
            "FROM learning_unit_feedback WHERE artifact_sha256=? AND unit_id=?",
            (self._artifact, self.prompt.unit_id),
        ).fetchone()
        if row is None or any(not isinstance(value, str) or not value.strip() for value in row):
            raise ValueError("Missing or invalid feedback")
        self._state = "revealed"
        return Feedback(*row)

    def assess(self, rating: Rating) -> Assessment:
        if self._state != "revealed":
            raise ValueError("Assessment requires revealed feedback")
        if rating not in ("again", "hard", "good", "easy"):
            raise ValueError("Invalid self-assessment")
        self._state = "assessed"
        return Assessment(self._artifact, self.prompt.unit_id, rating)
