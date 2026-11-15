# Native paired-grid family batch — 1395, 1401, 1402, 1404

This **second implementation slice** of the [batch-first workflow](BATCH_FIRST_MULTYEAR.md) performs a real, read-only **PDF-table candidate scan** for four known native paired-grid key files in a single invocation. It does **not** ask the owner to review every year. It does **not** yet publish, finalize or assign a booklet/edition to other years.

## One command for the whole family

```bash
uv sync --locked --dev
uv run --dev python -m english_exam.native_key_batch --source-dir source
```

Outputs a reproducible JSON **metadata-only** summary: year, actual key source status/hash, processing status, strict candidate table/question counts and exception flags. Parsed answer positions remain **only inside the function while executing**; they are not printed, serialized, saved in Git or promoted to any `Question.answers` field.

| Year | Source | Implementation | Honest output status |
| --- | --- | --- | --- |
| 1395 | `95_Key.pdf` | Reuses the existing SHA-locked, tested `extract_staged_key` importer for booklet A | `SOURCE_STAGE_VALIDATED` **only** when original PDF matches the trusted source hash and the actual importer passes its validation |
| 1401 | `1401_Key.pdf` | Shared strict native table pair scanner | `ASSISTANT_PROVISIONAL_GRID` **only if** exactly one structurally valid numeric table is uniquely detected |
| 1402 | `1402_Key.pdf` | Same shared scanner | Same provisional rules |
| 1404 | `1404-key.pdf` | Same shared scanner | Same provisional rules |

### Strict pairing, not guessed answers

For the three new family members, the scanner queries each source PDF for native tables and checks:

- **Only even-column** question/answer pairs (2–12 columns); optional *nonnumeric* header; consistent row widths.
- Exact numeric question tokens and ordinary answer positions **1–4** after Persian/Arabic/Latin digit normalization. Any nonnumeric, ambiguous, special, deleted or marked answer blocks candidate recognition; do not guess a choice.
- Strictly increasing questions in each group, no unexpectedly populated cells after a trailing blank, no missing paired cell, no gaps or duplicates across groups. Right-to-left column-group order is allowed only if the question numbers form one continuous sequence after sorting.
- Minimum 20 pairs and a **unique** eligible table across the source. Multiple eligible tables may reflect separate booklets, but are reported as `MULTIPLE_GRID_CANDIDATES` rather than silently collapsed.
- Sources with absent/unmatched bytes or Git LFS pointers cannot enter the scanner. For other years without trusted SHA pins, emit `SOURCE_HASH_UNPINNED` and never claim verified source identity.

`ASSISTANT_PROVISIONAL_GRID` is **not an official answer set**: even where a strict table looks plausible, booklet identity, key edition and distinguishing an official answer column from candidate/scoring columns must be established separately. Its flags remain `BOOKLET_UNASSIGNED` and `KEY_EDITION_UNASSIGNED`; no automatic English question-range alignment is attempted. If the original PDF uses multiple valid grids or a different family layout, its status is `NO_UNIQUE_NATIVE_GRID` with a compact exception code. A failed source **does not block processing independent years**.

An output status `FAMILY_PROBE_COMPLETE` means the family scanner completed without source/parser exceptions, **not** that the four answer keys were independently verified. An exit code 0 means the report was generated, including if any source is still pending.

### Tests

Synthetic unit tests for the generic scanner cover Persian-digit normalization via the existing shared helper, reversed column groups, partial final groups, bad question/answer tokens, malformed shapes, duplicated questions, ambiguous tables, source absence and reuse of the existing 1395 importer. Public CI can run these without original PDFs or copyrighted fixtures.

For **one optional family-wide source-present check**, after merging:

```bash
uv run --dev python -m pytest -q -ra \
  tests/integration/test_native_family_batch_sources.py
```

A passing test checks the original SHA-bound 1395 importer and safely classifies any accessible 1401/02/04 sources in one run. If the real 1395 PDF is missing or represented by a pointer, the test **skips**: do not describe a skip as successful original-source validation. This integration alone does **not** guarantee the 1401/02/04 booklet mapping or correct official key values.

### Next batch-oriented expansion

Use the flagged layout/variant exceptions from this one family to determine whether a second group or multiple booklets exist; introduce an explicit variant identity only with actual source evidence. Then apply the same family-first approach to broken-font 1397–99 and rendered 1392–94, without annual human approval queues. Separate answer-key provenance (`INITIAL` versus `FINAL`), true English-section boundaries, and source redistribution rights still govern educational release.

Original exam/key PDFs, source-linked proposals, 1396's 19 human decisions/75 pending independent tasks, official answers and `publication_status: BLOCKED` are untouched. This PR is **technical provisional processing**, not a release.
