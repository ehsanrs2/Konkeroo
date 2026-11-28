"""Local interactive private practice; no content or learner-data publication."""

import argparse
import sqlite3
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import cast
from uuid import uuid4

from english_exam.m4_adaptive import Progress, build_adaptive_queue
from english_exam.m4_events import LearnerEventStore
from english_exam.m4_practice import Rating
from english_exam.m4_scheduler import replay_state


@dataclass(frozen=True)
class SessionConfig:
    learner_id: str
    review_sha256: str
    audit_sha256: str
    due_limit: int = 20
    new_limit: int = 10


def _choose(
    read: Callable[[str], str], write: Callable[[str], None], prompt: str, choices: tuple[str, ...]
) -> str:
    while True:
        choice = read(prompt).strip().lower()
        if choice in choices or choice == "q":
            return choice
        write("Invalid choice; try again or enter q to quit.")


def _show_progress(write: Callable[[str], None], progress: Progress) -> None:
    write(
        f"Reviewed: {progress.reviewed}/{progress.eligible} | "
        f"Due: {progress.due} | New: {progress.new} | Events: {progress.events}"
    )
    write(
        f"Latest self-ratings: again={progress.latest_again}, hard={progress.latest_hard}, "
        f"good={progress.latest_good}, easy={progress.latest_easy}"
    )


def run_session(
    store: LearnerEventStore,
    config: SessionConfig,
    *,
    read: Callable[[str], str],
    write: Callable[[str], None],
    clock: Callable[[], int],
) -> int:
    """Present a bounded queue once; only completed ratings persist."""
    queue = build_adaptive_queue(
        store,
        config.learner_id,
        clock(),
        review_sha256=config.review_sha256,
        audit_sha256=config.audit_sha256,
        due_limit=config.due_limit,
        new_limit=config.new_limit,
    )
    write("Konkeroo | Private pilot | Self-assessment, not mastery verification")
    _show_progress(write, queue.progress)
    planned = [(item.artifact_sha256, item.unit_id, "Due") for item in queue.due] + [
        (item.artifact_sha256, item.unit_id, "New") for item in queue.new
    ]
    write(f"Session: {len(queue.due)} due, {len(queue.new)} new. Enter q to quit.")
    try:
        for index, (artifact, unit, category) in enumerate(planned, 1):
            session = store.begin(config.learner_id, str(uuid4()), artifact, unit)
            write(f"[{index}/{len(planned)}] {category} | {session.prompt.unit_type}")
            write(session.prompt.text)
            if _choose(read, write, "After attempting recall, enter r (or q): ", ("r",)) == "q":
                break
            session.record_attempt()
            feedback = session.reveal()
            write(f"Expected answer: {feedback.expected_answer}")
            write(feedback.explanation)
            write(feedback.grading_guidance)
            rating = _choose(
                read,
                write,
                "Rate recall (again/hard/good/easy, or q): ",
                ("again", "hard", "good", "easy"),
            )
            if rating == "q":
                break
            session.complete(cast("Rating", rating), clock())
            state = next(
                item
                for item in replay_state(store, config.learner_id)
                if (item.artifact_sha256, item.unit_id) == (artifact, unit)
            )
            due = datetime.fromtimestamp(state.due_at, tz=UTC).isoformat()
            write(f"Saved. Next review (UTC): {due}")
    except (EOFError, KeyboardInterrupt):
        write("Session interrupted. Only committed ratings are saved.")
    final = build_adaptive_queue(
        store,
        config.learner_id,
        clock(),
        review_sha256=config.review_sha256,
        audit_sha256=config.audit_sha256,
        due_limit=0,
        new_limit=0,
    )
    completed = final.progress.events - queue.progress.events
    write(f"Session completed ratings: {completed}/{len(planned)}")
    _show_progress(write, final.progress)
    for kind, progress in final.by_kind:
        write(f"{kind}: reviewed {progress.reviewed}/{progress.eligible}, due {progress.due}")
    return completed


def _write(message: str) -> None:
    sys.stdout.write(message + "\n")


def _now() -> int:
    return int(time.time())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--content", type=Path, required=True)
    parser.add_argument("--content-sha256", required=True)
    parser.add_argument("--learner-db", type=Path, required=True)
    parser.add_argument("--learner-id", required=True)
    parser.add_argument("--review-sha256", required=True)
    parser.add_argument("--audit-sha256", required=True)
    parser.add_argument("--due-limit", type=int, default=20)
    parser.add_argument("--new-limit", type=int, default=10)
    args = parser.parse_args(argv)
    config = SessionConfig(
        args.learner_id, args.review_sha256, args.audit_sha256, args.due_limit, args.new_limit
    )
    try:
        store = LearnerEventStore(args.content, args.content_sha256, args.learner_db)
        try:
            run_session(store, config, read=input, write=_write, clock=_now)
        finally:
            store.close()
    except (ValueError, OSError, sqlite3.Error) as exc:
        sys.stderr.write(f"Konkeroo pilot error: {exc}\n")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
