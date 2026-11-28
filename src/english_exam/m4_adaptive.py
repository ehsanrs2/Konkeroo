"""Bounded private-pilot prioritization; ratings are not mastery evidence."""

from collections import Counter
from dataclasses import dataclass

from english_exam.m4_events import LearnerEventStore, UnitMetadata
from english_exam.m4_scheduler import MAX_EPOCH, SCHEDULER_VERSION, ReviewState, project_history

ADAPTIVE_VERSION = "adaptive-v1"


@dataclass(frozen=True)
class Progress:
    eligible: int
    reviewed: int
    due: int
    new: int
    events: int
    latest_again: int
    latest_hard: int
    latest_good: int
    latest_easy: int


@dataclass(frozen=True)
class AdaptiveQueue:
    scheduler_version: str
    adaptive_version: str
    review_sha256: str
    audit_sha256: str
    due: tuple[ReviewState, ...]
    new: tuple[UnitMetadata, ...]
    progress: Progress
    by_kind: tuple[tuple[str, Progress], ...]


def _progress(keys, latest, due_keys, event_counts):
    ratings = Counter(latest[key] for key in keys if key in latest)
    reviewed = sum(ratings.values())
    return Progress(
        len(keys),
        reviewed,
        len(keys & due_keys),
        len(keys) - reviewed,
        sum(event_counts[key] for key in keys),
        ratings["again"],
        ratings["hard"],
        ratings["good"],
        ratings["easy"],
    )


def build_adaptive_queue(
    store: LearnerEventStore,
    learner_id: str,
    now: int,
    *,
    review_sha256: str,
    audit_sha256: str,
    due_limit: int,
    new_limit: int,
) -> AdaptiveQueue:
    """Keep due ordering; rank unseen units by difficulty signals and source links."""
    if type(now) is not int or not 0 <= now <= MAX_EPOCH:
        raise ValueError("Expected UTC integer epoch seconds")
    for limit in (due_limit, new_limit):
        if type(limit) is not int or limit < 0:
            raise ValueError("Expected nonnegative integer limit")
    catalog = {item.key: item for item in store.adaptive_catalog(review_sha256, audit_sha256)}
    events = store.history(learner_id)
    states = project_history(events, set(catalog), learner_id, store.snapshot_sha256)
    if any(state.last_reviewed_at > now for state in states):
        raise ValueError("Queue time precedes recorded review")
    latest = {(event.artifact_sha256, event.unit_id): event.rating for event in events}
    event_counts = Counter((event.artifact_sha256, event.unit_id) for event in events)
    due = sorted(
        (state for state in states if state.due_at <= now),
        key=lambda state: (state.due_at, state.artifact_sha256, state.unit_id),
    )
    due_keys = {(state.artifact_sha256, state.unit_id) for state in due}
    selected_due = due[:due_limit]
    # Worst latest rating in each cluster is only a prioritization signal.
    difficulty: dict[str, int] = {}
    for key, rating in latest.items():
        cluster = catalog[key].cluster_id
        signal = {"again": 2, "hard": 1}.get(rating, 0)
        difficulty[cluster] = max(difficulty.get(cluster, 0), signal)
    candidates = sorted(
        (item for key, item in catalog.items() if key not in latest),
        key=lambda item: (-difficulty.get(item.cluster_id, 0), -item.source_count, item.key),
    )
    selected: list[UnitMetadata] = []
    used_clusters: set[str] = set()
    used_prompts: set[tuple[str, str]] = set()
    for state in selected_due:
        item = catalog[(state.artifact_sha256, state.unit_id)]
        used_clusters.add(item.cluster_id)
        used_prompts.add((item.unit_type, item.prompt_sha256))
    # Never displace a due review. Defer duplicate new prompts within this queue only.
    # First pass favors diverse clusters; second fills remaining slots.
    if len(due) <= due_limit:
        for diverse in (True, False):
            for item in candidates:
                if len(selected) >= new_limit:
                    break
                prompt = (item.unit_type, item.prompt_sha256)
                if prompt in used_prompts or (diverse and item.cluster_id in used_clusters):
                    continue
                selected.append(item)
                used_clusters.add(item.cluster_id)
                used_prompts.add(prompt)
    kinds = sorted({item.kind for item in catalog.values()})
    by_kind = tuple(
        (
            kind,
            _progress(
                {key for key, item in catalog.items() if item.kind == kind},
                latest,
                due_keys,
                event_counts,
            ),
        )
        for kind in kinds
    )
    return AdaptiveQueue(
        SCHEDULER_VERSION,
        ADAPTIVE_VERSION,
        review_sha256,
        audit_sha256,
        tuple(selected_due),
        tuple(selected),
        _progress(set(catalog), latest, due_keys, event_counts),
        by_kind,
    )
