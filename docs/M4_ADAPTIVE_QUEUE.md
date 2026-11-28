# M4 adaptive queue and progress projection

Tracking: #91; predecessor #89 / merged #90. Baseline main: 6fb3e5e71b03e5b0d06de9bf47054644d74657cb.

## Implemented scope

The learner event store exposes eligible unit metadata from an explicitly selected sense-review revision and prior audit revision in the SHA-256-pinned, read-only snapshot. Each eligible exact unit revision must resolve to one cluster. Missing or duplicate mappings fail closed; an unknown mapping revision is rejected. Metadata includes concept kind, source-anchored distinct question count, unit type and exact prompt SHA-256, not feedback or answer values. The supplied snapshot is a trusted local artifact, not an untrusted database security boundary. Existing schema, gates and event lifecycle remain unchanged.

The scheduler now exposes the pure history projection used by its existing replay function. The adaptive module captures history once for both state and summaries, avoiding inconsistent multiple reads of a concurrently appended event history. It preserves the pilot-v1 interval rules.

## Adaptive-v1 policy

Call `build_adaptive_queue(store, learner_id, now, review_sha256=..., audit_sha256=..., due_limit=..., new_limit=...)` from `english_exam.m4_adaptive`. The two mapping digests must identify the selected revisions in the pinned local corpus. All times are integer UTC epoch seconds, limits nonnegative integers. The result is a read-only point-in-time selection, not a reservation. The caller must still complete the existing attempt/reveal/assess lifecycle.

Due reviews retain oldest-due-first order, breaking ties by exact artifact and unit identity. If the due backlog exceeds due_limit, no new units are selected. No due unit is postponed by cluster or prompt duplication. Unseen eligible units rank by the worst latest rating of previously reviewed units in their cluster (again=2, hard=1, good/easy=0, no history=0), then descending source-anchored distinct question count, then stable unit identity. The first selection pass favors clusters not already represented by selected due/new units; the second fills remaining slots. Exact unit-type/prompt-digest duplicates among selected due/new entries are deferred for the current queue only. This does not equate different feedback or imply mastery transfer. The number of selected new units can be less than the requested limit. No persisted adaptive state or schema migration is necessary.

The ranking signals, tie order, and backlog policy are provisional engineering choices, not validated indicators of exam importance or learning efficacy. Source counts are curated question associations, not exhaustive word frequencies. No cross-unit interval updates, mastered status, inferred probability of recall, or learning outcome claim.

## Progress

The result contains uncapped eligible, reviewed, due, new and event counts and counts of each latest self-rating, overall and by concept kind. Reviewed counts distinct unit revisions with events; latest ratings are not event totals or independent mastery evidence. A deferred new unit remains new. This is not a section-level reading/vocabulary/grammar achievement score. No free-text responses or private learner data are exposed to Git.

## Validation

Local isolated test run: 53 passed (17 new adaptive cases, 36 unchanged scheduler cases), Python 3.13.5. Tests cover frequency and difficulty ordering, diversity, duplicate deferral, due backlog and ties, limits, latest ratings versus event counts, isolation and reopening, invalid mapping pins, missing/duplicate mapping, invalid time and limit, and corrupt gated history. The four modified/new Python blobs match the locally tested files.

Private smoke: verified the prior sense-review archive and its two manifest-listed file digests. All 797 eligible revisions mapped to 765 provisional clusters; 105 gated units were excluded. Initial unlimited queue selected 776 distinct unit-type/prompt combinations, deferring 21 duplicates without changing eligibility. A synthetic local learner completed an again event for each of the 797 eligible revisions. All were reviewed; none were due one second before the boundary and all 797 were due at the boundary. With a due limit of 20, no new units were selected. Independent learner and restart projections matched expectations; learner SQLite integrity passed and content digest remained unchanged. Temporary learner data removed. No private content committed. These are software checks, not observed learning outcomes.

Ruff is unavailable locally and absent from the offline cache. Full repository Python 3.12 CI, lint and formatting remain unconfirmed; verify the PR checks before merge.

## Next

Build an end-to-end private interactive local practice pilot with bounded sessions, explicit learner rating, resumption and progress presentation. Keep semantic review, unresolved source/answer exceptions, 105 gated units and D-010 release block intact. Section-level analytics, duplicate-evidence mastery controls, scheduler efficacy evaluation, and Android remain separate later work.
