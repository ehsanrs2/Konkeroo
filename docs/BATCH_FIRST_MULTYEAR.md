# Batch-first 1391–1405 English source processing

**Owner development direction: 2026-11-14.** Prioritize scaling Konkeroo beyond 1396. The assistant is authorized to perform **provisional source interpretation and technical validation** without requesting separate human acceptance of each suspicious word, each question, or each year. This does **not** equate AI assertions with independently verified answers.

This milestone adds the **first operational step**: a read-only multi-year inventory/triage utility with **one command**. It is intentionally **not** an all-year text parser, answer solver, copyright permission, or production dataset.

## Use one command for 15 years

```bash
uv sync --locked --dev
uv run --dev python -m english_exam.batch_inventory --source-dir source
```

The command prints deterministic JSON containing a `schema_version`, 15 per-year records, per-file media-readiness status, file hashes when accessible, one row for the intentionally absent 1405 official key, total source availability and exception counts. It does **not** extract or reproduce full question text, key sequences or original media.

- `LOCAL_SOURCE_PINNED`: real PDF/JPEG header and SHA-256 equal an **already recorded** expected hash (only particular 1395/1396 sources have those pins). This indicates source identity **only**, not a correct interpretation.
- `LOCAL_SOURCE_UNPINNED`: real PDF/JPEG header, observed SHA, but **no trusted expected hash yet**; suitable for exploratory provisional work, not identity attestation.
- `LFS_POINTER_ONLY`: the local file is an LFS metadata pointer, **not a usable PDF**. `SOURCE_IDENTITY_CONFLICT` additionally flags pointer OIDs inconsistent with an existing pin.
- `SOURCE_MISSING`, `MALFORMED_LFS_POINTER`, `MEDIA_SIGNATURE_MISMATCH`, `SOURCE_HASH_MISMATCH`: independent per-source exceptions; never silently convert a pointer/invalid file to validated media.
- `NO_OFFICIAL_KEY_RECORDED` (1405): a **known missing official key** is not an algorithmic failure and is never filled by AI guesses.

The command exits successfully when it has completed the inventory, **even if `status=SOURCES_INCOMPLETE`**. Do not confuse an exit code 0 with successful source parsing or complete source availability.

## Group by technical family, not by acceptance year

| Family | Years | Reusable next technical step |
| --- | --- | --- |
| Legacy multi-booklet | 1391 | Model each booklet/variant and cross-page joins; never collapse to one answer column |
| Rendered PDF/JPEG grids | 1392–1394 | Shared visual row/column locator and provisional confidence; retain JPEG/PDF identity |
| Native paired-grid | 1395, 1401, 1402, 1404 | Reuse the existing 1395 paired-grid primitive; detect fixture-specific dimensions and digit normalization without assuming identical key layout |
| 1396 visual initial | 1396 | Reuse existing 30-row curated source and structural alignment; key edition remains INITIAL |
| Broken-font paired-grid | 1397–1399 | Source-aligned glyph mapping with ambiguity tracking; no unsupported universal OCR assumption |
| Personalized reports | 1400, 1403 | Preserve **candidate response** versus **official response**, deletion, and scoring annotations; 1400 raster, 1403 native |
| No official key | 1405 | Exam-only provisional data; explicit absent official authority |

These families are **routing hints**, not claims that the relevant source was successfully parsed. The exact filenames and 1391–1405 coverage are from the observed repository tree; they are intentionally **explicit** in `english_exam.batch_inventory.YEAR_SOURCES`, not invented by a naming rule. A file being observed does not establish a copyright license or a final official key.

## Follow-on batch processing (not yet implemented)

1. Register one **representative and source-dependent fixture** per family; derive the actual English question range and booklet for that fixture, not from a universal 30-question assumption.
2. For every real source that is locally available, record immutable hash/media provenance. Extract field/choice structure and only the required source-aligned assistant provisional readings. Preserve `raw_text` independently.
3. Validate **family-wide** row/column completeness, order, choice-count, duplicate IDs, stable source hashes and answer authority. Use assistant-led visual/geometry checks for ambiguous source; flag only the exceptional row/field when doubt remains.
4. Write a **private/local** provisional artifact with per-record `ASSISTANT_PROVISIONAL`, source/edition/variant and evidence metadata, and a small non-copyright-bearing public manifest of counts/statuses only. Never write full source-derived contents or answer sequences into the Git repository.
5. Summarize progress as **batch coverage and exception categories**, not 15 separate requests for owner test execution. Mechanical test skip ≠ source-present pass; uncertain items remain uncertain, but other years need not wait for them.

The existing 1396 vocabulary/Cloze/Reading sample correction modules and 1395 source-key importer are valuable reference fixtures, not a mandate to recreate their long human-review docket annually. The source-linked 1396 owner-review ledger remains **19 historical decisions / 75 independent checks pending**. Those statuses **must not be forged or copied** to later years.

## Clear boundary

This plan **removes routine owner involvement for provisional development**, not scientific uncertainty. AI-only validation can be the project's provisional quality criterion and still have an explicit error rate that is unknown until measured. No unverified official answer can be labeled `final_verified`; an INITIAL key is not automatically FINAL; 1405 stays no-key; public dataset release stays **BLOCKED** until a separate authority and source redistribution-rights decision (D-010). No history rewrite, LFS deletion or rights decision is implied here.

Implementation tracker: [Issue #39](https://github.com/ehsanrs2/Konkeroo/issues/39).
