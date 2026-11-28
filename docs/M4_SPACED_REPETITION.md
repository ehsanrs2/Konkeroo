# M4 spaced repetition and review queue

Tracking: #89; predecessor #87 / merged #88. Baseline main: 50b36c1425e4afec978afc5cfc1d293aaaeb4681.

## Implemented scope

`english_exam.m4_scheduler` exposes `next_interval`, `replay_state`, and `build_queue`. The scheduler version is `pilot-v1`; it implements the provisional interval rules in M4_SENSE_REVIEW_AND_LEARNER_EVENTS.md, not FSRS or a validated memory model.

| Rating | Initial interval | Later interval |
| --- | --- | --- |
| again | 600 seconds | Reset to 600 seconds |
| hard | 1 day | Prior interval times 6/5, rounded down, minimum 1 day |
| good | 2 days | Prior interval times 2, minimum 2 days |
| easy | 4 days | Prior interval times 3, minimum 4 days |

All intervals are capped at 365 days. The due timestamp is measured from the actual committed event timestamp, not the previous due date; it saturates at the largest supported UTC epoch timestamp (9999-12-31T23:59:59Z). No automatic clock reads, random jitter, or time-zone conversion occur.

## Projection and queue

The learner event store exposes only sorted, eligible unit revision identities via `eligible_unit_revisions()`. Invalid or duplicate identities fail closed. No gated prompts or feedback fields enter the queue.

Replay uses the committed event sequence for one learner and the pinned snapshot, and validates scope, eligibility, order, timestamps and ratings. It produces independent per-unit state: exact artifact digest, unit ID, last review time, interval, due time, and review count. There is deliberately no persisted derived-state table in this pilot: an event commit is the only persistence operation, and projection is rebuilt from committed history. This avoids a stale dual-write cache. The existing learner database schema and event lifecycle are unchanged. Replay is deterministic under the named version; future scheduling changes must retain/version the previous rules rather than silently reinterpret history.

`build_queue(store, learner_id, now, due_limit=..., new_limit=...)` returns a versioned result with separate due and new tuples and their uncapped counts. Due means due_at <= now; ties use exact artifact and unit identity. New units are unseen eligible revisions sorted by identity. Reviewed units not yet due are excluded. Both limits are caller-supplied nonnegative integers. A queue time earlier than an already recorded review fails rather than silently reconstructing an earlier state. The caller should present due entries before new entries. Selection is a read-only point-in-time result, not a reservation or authorization to skip the existing practice lifecycle; begin/complete still validate eligibility.

No mastery propagates between units, including duplicate prompts or shared concepts. A review count records self-assessment events, not independent evidence of mastery. No cross-snapshot history migration, adaptive ranking, cluster diversity, user-interface, or publication is implemented.

## Validation

36 isolated synthetic pytest cases passed on Python 3.13.5, SQLite 3.46.1 and pytest 9.0.2. Cases cover initial and repeated intervals, integer rounding, floors/cap/reset, invalid inputs, due boundary, tie ordering and queue limits, duplicate prompt/unit independence, duplicate event retry, actual review time, transaction failure, replay and restart, learner/snapshot isolation, gated and corrupt history, timestamp bounds, and immutable source digest. All three modified/new Python Git blobs match the locally tested files; the unchanged PracticeSession blob matches main.

Private smoke: verified the prior sense-review archive digest and both manifest-listed file digests. All 797 eligible revisions appeared as new, and all 105 review-required revisions were excluded. A synthetic local learner completed an again event for each eligible unit and retried it. Exactly 797 committed events and projected states remained. At one second before the due boundary none were due; at the boundary all 797 were due, with zero new. A separate learner remained unseen. Reopening reproduced the same state and queue; learner SQLite integrity and unchanged content SHA-256 passed. Temporary learner data removed. No private content or learner events committed. These are software checks, not observed human learning outcomes.

Ruff is unavailable in the local environment and its offline cache. The full repository test suite, Python 3.12 CI, lint and formatting remain unconfirmed. Run the repository checks before merging.

## Next

Add conservative adaptive queue prioritization and progress summaries using versioned concept mappings without transferring mastery or counting duplicate prompts as independent evidence. Keep due reviews prioritized and maintain all eligibility gates. Continue semantic content review, including the 105 gated units and unresolved source/answer exceptions. D-010 remains BLOCKED; Android and publication remain downstream.
