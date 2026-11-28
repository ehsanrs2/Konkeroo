# M4 interactive local practice pilot

Tracking: #93; predecessor #91 / merged #92. Baseline main: 78ceccf8cb9db24f07c94857a7c99366aaedf0b1.

## Implemented scope

`english_exam.m4_pilot` is a dependency-free local terminal interface over the existing LearnerEventStore, adaptive-v1 queue, and pilot-v1 scheduler. No new database schema, content modification, dependencies, Android UI, authentication, synchronization, or release.

Each invocation captures one bounded due/new queue. Due units appear first; the existing adaptive backlog policy and eligibility gates are unchanged. The defaults are up to 20 due and 10 new units. Type r after making a retrieval attempt (including an abstention) to reveal the expected answer, Persian explanation and grading guidance. Rate again, hard, good or easy after viewing feedback. Only a completed rating is committed; its next review time is shown in UTC. Invalid commands are retried. Type q at either prompt to quit. EOF and keyboard interruption during the session exit with a summary of committed ratings.

The end-of-session summary shows committed event count change, reviewed/eligible, due and new counts, latest ratings and concept-kind coverage. It assumes one interactive process per learner and snapshot; concurrent sessions for the same learner are not supported. Start a new invocation using the same local learner database, learner ID and snapshot pins to reconstruct the next queue. The original queue is not persisted, and an unfinished prompt is not a recorded attempt or a reserved slot. Newly due exercises are considered on the next invocation, not dynamically inserted in a running session. An AGAIN rating schedules another review after ten minutes, not immediate presentation in the same fixed queue.

## Local setup

Use the repository's Python 3.12 environment. Extract the privately supplied sense-review archive outside the repository. Verify the archive and manifest digests, then supply the exact content snapshot SHA-256, sense-review revision and prior audit revision. The first run creates a separate learner database at the supplied path; its parent directory must already exist. Use a pseudonymous local learner ID, OS access controls and a stable private path. Do not commit the content database, learner database or session logs. The terminal must support Unicode/Persian text; right-to-left shaping depends on the terminal.

```bash
uv sync --locked --dev
uv run python -m english_exam.m4_pilot --help
uv run python -m english_exam.m4_pilot \
  --content /path/to/private/content.sqlite3 \
  --content-sha256 CONTENT_SHA256 \
  --learner-db /path/to/private/learner.sqlite3 \
  --learner-id local-pilot \
  --review-sha256 REVIEW_SHA256 \
  --audit-sha256 AUDIT_SHA256 \
  --due-limit 20 --new-limit 10
```

All placeholders must be replaced with actual local configuration. For the existing private sense-review snapshot, the input archive SHA-256 is `34e544134827a9d3283760069d44fbe19b7a4183d5ba938c87036b1521f56221`; the content digest is `5fc1d3b11135092bc82dec3a9ab0ee14ca048e1105ae6678d05ecad26421aa2a`; the review digest is `e130c0f33a10fb73ffc205621520ded991fb71095c9bace3d3f292cb27eeb68b`; the prior audit digest is `22dd735066d96c1843bd09102fde8342d463f08e032968f690d86b7ea370a158`. These pins were checked against the exact private artifact. No source or answer data is included in Git.

Use --due-limit 0 --new-limit 0 for a summary without presenting exercises. The existing due backlog rule may reduce the number of new exercises to zero. A completed rating is a self-assessment, not evidence of mastery or a verified exam score.

## Validation

61 isolated pytest cases passed (eight new pilot cases, 17 prior adaptive cases, 36 prior scheduler cases), Python 3.13.5, SQLite 3.46.1, pytest 9.0.2. The new tests cover quitting before and after feedback, invalid input, saving and reopening at the due boundary, EOF and keyboard interruption after attempt, zero limits, CLI summary and incorrect snapshot digest. Existing engine and prior test blobs matched main; both changed/new Python Git blobs matched locally tested files.

Private subprocess smoke: verified the prior archive SHA-256 and both manifest-listed files; ran the CLI in three independent processes on temporary extracted content and learner paths. Two completed synthetic ratings persisted across restarts. Two unfinished exercises (one after reveal, one before reveal) created no additional events. Progress showed 0, 1 and 2 reviewed as appropriate; learner SQLite integrity passed and content digest remained unchanged. Temporary learner data removed. This is a software smoke test, not a human learning outcome or full semantic review.

Ruff 0.16 is unavailable in the local environment and offline cache. Full repository checks on Python 3.12, lint and formatting remain unconfirmed. Verify PR checks before merge.

## Next

Conduct an owner-run private pilot and document actual usability and learning feedback before choosing the next interface. Continue content semantic review, the 105 gated units and unresolved source/answer exceptions; no gates cleared. D-010 remains BLOCKED. Android and publication remain downstream of appropriate data and release gates.
