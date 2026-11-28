# M4 learner event store

Tracking: #87; predecessor #85 / merged #86. Baseline main: 536540ddb127c8ba5b8d06dae370df9a5f49903e.

## Implemented scope

`english_exam.m4_events.LearnerEventStore` wraps the existing PracticeSession without modifying that module. It reads a checkpointed local content file, compares the SHA-256 of the actual bytes with the expected digest, deserializes those bytes into an in-memory SQLite connection, and enables query-only mode. The snapshot must be immutable and have no concurrent writer, WAL or rollback-journal sidecars. SQLite must support deserialize (available in the tested build). The separate learner database uses application ID and schema version 1; an unrelated database is rejected. One calling thread per connection; SQLite BEGIN IMMEDIATE serializes appends.

The supported application API requires a retrieval-attempt acknowledgement and revealed feedback before completing a self-assessment. Exact unit eligibility is checked again before persistence. Events store only sequence, unique event ID, pseudonymous learner ID, content snapshot digest, artifact digest, unit ID, integer UTC epoch seconds, and rating. No free-text answers, credentials or identity fields. Caller supplies a stable event ID and timestamp, and should retain both for retries; identical replay returns the prior event, conflicting replay fails. Same-unit backdating is rejected within a learner/snapshot/revision; equal timestamps are ordered by sequence. An interrupted or rejected transaction does not leave a partial event. A session can retry the identical completion following a transient write failure.

The store is append-only through the supported application API; it is not a tamper-proof database or authentication boundary. History is scoped to the current snapshot and learner, and no state is transferred across revisions. Use private paths with OS access controls; the database is not encrypted by this module. Do not commit the learner database or a private content database.

## Example

```python
from pathlib import Path
from uuid import uuid4

from english_exam.m4_events import LearnerEventStore

# All three values and the exact unit revision come from local configuration.
store = LearnerEventStore(
    Path(content_path),
    expected_snapshot_sha256,
    Path(learner_path),
)
try:
    event_id = str(uuid4())
    session = store.begin("local-pilot", event_id, artifact_sha256, unit_id)
    # Present session.prompt; wait for an actual retrieval attempt.
    session.record_attempt()
    feedback = session.reveal()
    # Present feedback; collect the learner's rating and UTC integer timestamp.
    event = session.complete(rating, occurred_at)
    history = store.history("local-pilot")
finally:
    store.close()
```

The example is an API sketch with locally supplied variables, not an interactive CLI or automatic practice completion.

## Validation

15 isolated synthetic pytest cases passed (Python 3.13.5, SQLite 3.46.1, pytest 9.0.2; repository target is Python 3.12). Coverage includes attempt/reveal/assessment order, invalid ratings and timestamps, blocked/unknown revisions, conflicting and identical replay, reopening, learner/unit/artifact/snapshot isolation, backdating, injected transaction failure and retry, wrong digest, same-file/hardlink aliases, sidecar rejection, and rejecting an unrelated learner database. The unchanged local PracticeSession blob matched the exact GitHub blob; both new source and test blobs also matched the tested local files.

Private smoke: verified the prior sense-review archive digest and its two manifest-listed file digests. Used temporary paths and a synthetic local learner to exercise every one of the 797 eligible units, each with a duplicate retry; all 105 gated units were rejected. Reopening returned exactly 797 events in order, learner isolation passed, learner SQLite integrity returned ok, content SHA-256 unchanged. Temporary learner data removed. No private content or learner events committed or attached. This is a software smoke test, not a human learning outcome or semantic review.

Ruff 0.16 is unavailable in the local environment and not cached; network installation failed DNS resolution. Full repository Python 3.12 CI, lint and Ruff formatting remain unconfirmed; run the repository checks on the PR before merging.

## Deferred

This PR does not implement derived due state, scheduling, cluster metadata in event rows, cluster-aware queues, mastery transfer, synchronization, UI, or authentication. The scheduler version will govern the later replay projection; event history is the input, not a due-state record. No cluster ID is recorded until a validated mapping is integrated. The 105 review gates, provisional content, 170 blocked alignments and two unresolved conflict reviews remain unchanged; D-010 remains BLOCKED.

Next: implement the versioned deterministic interval function from the contract, replay-derived per-unit due state and stable eligible due/new queue, with synthetic interval/replay/tie/limit tests. Continue content semantic review separately.
