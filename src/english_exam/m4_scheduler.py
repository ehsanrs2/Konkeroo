"""Deterministic private-pilot scheduling, not a mastery model or FSRS."""

from dataclasses import dataclass

from english_exam.m4_events import LearnerEventStore
from english_exam.m4_practice import Rating

SCHEDULER_VERSION = "pilot-v1"
DAY_SECONDS = 86400
MAX_INTERVAL = 365 * DAY_SECONDS
MAX_EPOCH = 253402300799


@dataclass(frozen=True)
class ReviewState:
    artifact_sha256: str
    unit_id: str
    last_reviewed_at: int
    interval_seconds: int
    due_at: int
    review_count: int


@dataclass(frozen=True)
class ReviewQueue:
    scheduler_version: str
    due: tuple[ReviewState, ...]
    new: tuple[tuple[str, str], ...]
    due_count: int
    new_count: int


def next_interval(previous: int | None, rating: Rating) -> int:
    """Use integer arithmetic and the version-one pilot interval rules."""
    if previous is not None and (type(previous) is not int or not 1 <= previous <= MAX_INTERVAL):
        raise ValueError("Invalid previous interval")
    if rating == "again":
        return 600
    if rating == "hard":
        return min(MAX_INTERVAL, max(DAY_SECONDS, (previous or 0) * 6 // 5))
    if rating == "good":
        return min(MAX_INTERVAL, max(2 * DAY_SECONDS, (previous or 0) * 2))
    if rating == "easy":
        return min(MAX_INTERVAL, max(4 * DAY_SECONDS, (previous or 0) * 3))
    raise ValueError("Invalid self-assessment")


def replay_state(store: LearnerEventStore, learner_id: str) -> tuple[ReviewState, ...]:
    """Project committed events for one learner and the pinned snapshot."""
    eligible = set(store.eligible_unit_revisions())
    states: dict[tuple[str, str], ReviewState] = {}
    last_sequence = 0
    for event in store.history(learner_id):
        key = (event.artifact_sha256, event.unit_id)
        if (
            event.learner_id != learner_id
            or event.snapshot_sha256 != store.snapshot_sha256
            or key not in eligible
        ):
            raise ValueError("Event outside eligible snapshot history")
        if event.sequence <= last_sequence:
            raise ValueError("Invalid event sequence")
        last_sequence = event.sequence
        if type(event.occurred_at) is not int or not 0 <= event.occurred_at <= MAX_EPOCH:
            raise ValueError("Invalid event timestamp")
        previous = states.get(key)
        if previous is not None and event.occurred_at < previous.last_reviewed_at:
            raise ValueError("Backdated event")
        interval = next_interval(previous.interval_seconds if previous else None, event.rating)
        states[key] = ReviewState(
            *key,
            event.occurred_at,
            interval,
            min(MAX_EPOCH, event.occurred_at + interval),
            previous.review_count + 1 if previous else 1,
        )
    return tuple(states[key] for key in sorted(states))


def build_queue(
    store: LearnerEventStore,
    learner_id: str,
    now: int,
    *,
    due_limit: int,
    new_limit: int,
) -> ReviewQueue:
    """Return due reviews first, then unseen eligible units; no writes."""
    if type(now) is not int or not 0 <= now <= MAX_EPOCH:
        raise ValueError("Expected UTC integer epoch seconds")
    for limit in (due_limit, new_limit):
        if type(limit) is not int or limit < 0:
            raise ValueError("Expected nonnegative integer limit")
    states = replay_state(store, learner_id)
    if any(state.last_reviewed_at > now for state in states):
        raise ValueError("Queue time precedes recorded review")
    seen = {(state.artifact_sha256, state.unit_id) for state in states}
    due = sorted(
        (state for state in states if state.due_at <= now),
        key=lambda state: (state.due_at, state.artifact_sha256, state.unit_id),
    )
    new = [key for key in store.eligible_unit_revisions() if key not in seen]
    return ReviewQueue(
        SCHEDULER_VERSION, tuple(due[:due_limit]), tuple(new[:new_limit]), len(due), len(new)
    )
