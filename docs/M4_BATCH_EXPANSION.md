# M4 batch expansion

Tracking: #67; predecessor #65 / merged #66. Baseline main: ee8a28b72c56be0239232c793ad0283e4526fcd0.

## Local workflow

Use an immutable private SQLite snapshot with no concurrent writer or uncheckpointed WAL. Verify its SHA-256 against the previous manifest. The batch wrapper reuses the explicit-field M4 packet exporter, verifies SQLite integrity and foreign keys, checks an explicit list of distinct years and uses the content booklet identity rather than key alignment status. It validates every selected packet before returning the output mapping, checks cross-year question ID uniqueness and emits deterministic JSON plus a digest/count manifest. The CLI writes to a new directory outside the public repository; a disk I/O failure during file writing can leave an incomplete directory, which must not be used without validating the manifest.

Example (paths and digest must be supplied locally):

```bash
uv run python -m english_exam.m4_batch /private/input.sqlite3 EXPECTED_SHA256 \
  /private/new-packets 1392 1393 1394
```

Packet readiness does not mean solved, aligned, reviewed or published. Solve from these packets, preserve abstentions and uncertainty, pin solution revisions before accessing source-key values, and compare only against guarded candidate joins. Blocked alignments remain blocked. Earlier exposure is possible, so this is not a blinded trial. Additive private staging must not overwrite previously frozen hypotheses or source text. For source wording conflicts, inspect the original image, retain the original reading and document any proposed correction separately.

## Checkpoint

All 12 input files in the M4.5 manifest matched their digests. Fourteen private key-excluded packets cover 400 remaining English questions, 1600 options and the corresponding passages. The 1392/510B local pass recorded 30 hypotheses, including one abstention for a source-wording conflict; comparison against the aligned initial key yielded 29 agreements, one abstention and zero disagreements. This is provisional evidence only; no source wording was changed. The 1392 source-image review remains pending. Two additional inference caveats were retained.

The private working database now has 60 AI solution rows and 60 reconciliation rows. All 20 previous table/view definitions and previous rows were preserved; only 30 new rows were appended to each of the two answer-analysis tables. SQLite integrity passed, foreign-key violations were zero, guarded candidate coverage remained 260 and the input database digest was unchanged. No final verified answer or learner release was promoted.

Seven synthetic batch tests passed in an isolated local harness with an equivalent copy of the M4 packet exporter; the real private corpus export also succeeded. Full repository CI and Ruff are unconfirmed. The public module prepares packets only; semantic solving, reconciliation, explanation and knowledge generation remain private assistant-led workflows rather than an automated public pipeline.

M4.3–M4.5 are complete only for the 1391 pilot (30 questions, 119 units); 1392 explanations and units are pending, and 370 questions still require a first solution pass. D-010 / publication BLOCKED. No question text, source answers, private JSON or database are committed. D-014 remains in force.
