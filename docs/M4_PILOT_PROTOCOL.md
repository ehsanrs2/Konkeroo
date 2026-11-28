# M4 pilot protocol

Tracking: #59; prior acquisition: #57. Baseline: main commit 75245014639024ae81db6df0ba82053347e22b12. D-003, D-005, D-008, D-010 and D-014 remain applicable.

## Private workflow

- Keep the owner-confirmed M3 database immutable. Verify the pinned digest, SQLite integrity and foreign keys before use. Work on a separate local copy.
- Export a key-excluded packet from the confirmed M3 database using the explicit field allowlist:
  `uv run python -m english_exam.m4_packet /private/confirmed.sqlite3 1391 510A /private/packet.json`.
  Use a new destination outside Git. The exporter is a staging adapter, not a production importer or proof of experimental blinding. It never queries answer tables, excludes metadata hints and checks coverage and passage relations. Content itself is trusted confirmed transcription; arbitrary embedded answer hints in content text are not detected.
- Solve from the packet and record question ID, option or abstention, evidence, rationale, confidence and uncertainty. Pin the exact packet and solution bytes before exposing candidate key values. Prior exposure may have occurred; do not claim a blinded trial.
- Compare only structurally aligned source key candidates. Preserve all accepted positions where present. Missing or blocked key alignments are not disagreements and must not be joined by guesswork. Source edition/authority remain explicit.
- Store comparison records separately, bound to the frozen AI run and source-key identity; no automatic mutation of source keys, AI solutions or final answers. Agreement is not semantic verification. Record caveats and disagreements for adjudication.

## Local pilot checkpoint

The 1391/510A pilot completed 30 proposed solutions, 30 guarded comparisons, all agreement and two retained wording caveats. Source key edition is unspecified. The packet and solution digests were rechecked; the packet matches the explicit database content projection. The new local reconciliation table has 30 rows, zero final-verified entries, and all prior table/view contents and definitions were checked unchanged. SQLite integrity passed and foreign-key check returned zero violations. This is assistant provisional evidence, not independent human answer approval or statistical accuracy estimation.

The remaining 400 questions have not been solved in this pilot. The 170 blocked key alignments remain unchanged. No source media was re-read in this stage. No new OCR, source content, answer values, private database or explanation artifacts are published.

## Tests and next milestone

Public tests use synthetic fixtures only. Run `uv lock --check`, `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .` and `git diff --check`. The assistant's local private checks are distinct from repository CI. Review and CI are required before merge. M4.3 will add separate Persian educational explanations with distractor analysis, preserve caveats and maintain blocked publication status.
