# Broken-font paired-grid batch: 1397–1399

**Status:** source-bounded, assistant-attributed *candidate probe*, not a verified key importer.

The original key PDFs for years **1397, 1398 and 1399** have unusable native font-to-Unicode mappings (see [corpus format audit](ANSWER_KEY_CORPUS.md)). A normal text parser may return symbols unrelated to the actual digits. Under the owner's batch-first policy, one command analyzes all three as a **technical family**, without requesting an annual human correction queue.

```bash
uv sync --locked --dev
uv run --dev python -m english_exam.broken_font_batch --source-dir source
```

The output is deterministic JSON **metadata only**: year, observed source SHA, source readiness, number of PDF pages, geometric table count, provisional candidate and question counts, and explicit flags. It **does not print or save decoded answer positions, codepoint maps, the original PDF contents, or full question text**.

## Source identity

| Year | File | Page count expected | SHA-256 from repository LFS object |
| --- | --- | --- | --- |
| 1397 | `source/97_Key.pdf` | 2 | `c00ddaeba1bb640ec095d7823f31e80d2e548ee26a16eeab9f8e95f11784263f` |
| 1398 | `source/98_Key.pdf` | 2 | `baa697ee3592b1a5d89896938e5d96e93ba445d86c2cb85c41876cd44fb0326c` |
| 1399 | `source/99_Key.pdf` | 1 | `2cd70e03fb11bad443ea365dae082478fd893e42d598ef2e4b09d4abbda960c7` |

These are **Git LFS object IDs already committed in the repository**, not checksums independently supplied by the exam publisher. The inventory now uses these repository pins to require an exact match when genuine local PDF bytes are present. A local Git LFS **pointer file is not PDF media**, even if its OID matches; it stays `SOURCE_NOT_READY`. A PDF with different bytes or wrong page count cannot silently pass.

## Deterministic glyph candidate method

1. Use `pdfplumber` to find geometric tables in the genuine PDF; inspect *cell-bound native text only*, never unrestricted full-page OCR.
2. For every even-numbered question/answer column pair, try **zero or one header row**, then a strict **Q1, Q2, …, Q20+ starting-number hypothesis**. Pair each source glyph one-to-one with the corresponding Latin digit. At least 20 consecutive question labels are needed so the hypothesis covers all ten decimal digits.
3. Reject a candidate if any distinct digits collide onto one text-layer glyph, glyphs map inconsistently, question tokens are mixed/ambiguous, a raw glyph has no inferred mapping, or the recovered values fail the **existing strict native paired-table validator**. That validator also blocks duplicate/gapped questions, illegal option numbers, unexpected populated trailing cells or inconsistent column groups.
4. If one uniquely constrained table remains, preserve the inferred mapping **only in memory** and return its count and an `UNVERIFIED_Q1_ANCHOR` flag. This Q1 anchor is an explicit structural **hypothesis**, not a second reading of the printed PDF; no score/calibrated accuracy is claimed.
5. If multiple candidates remain, or no table/mapping is uniquely decodable, return `NEEDS_GLYPH_GEOMETRY_FOLLOWUP` and **zero candidate questions**. An unrelated year's result continues independently.
6. **Two-page 1397/1398 keys remain partial**, even if a page-1 grid is decoded. The scanner does not yet reconcile all continuation rows/pages. It labels such a result `ASSISTANT_PROVISIONAL_PARTIAL_GRID` plus `MULTIPAGE_CONTINUATION_UNRESOLVED`. A one-page 1399 candidate may be `ASSISTANT_PROVISIONAL_GLYPH_GRID` but is still **not** a checked official answer set.

Even an apparently complete decoded table is marked `BOOKLET_UNASSIGNED` and `KEY_EDITION_UNASSIGNED`; no assumption equates an original candidate-response column to an official key or an initial key to a final key. No automatic English-section range is inferred.

## Evidence and next family pass

Unit tests (no copyrighted cells) use synthetic one-character font substitutions, reversed group order, collided glyphs, invalid answers, duplicate/gapped numbering, ambiguous tables, unexpected pages, pinned LFS pointers, and isolation when one year fails. Public GitHub CI runs the synthetic tests; the full source-dependent family check is honestly **skipped** without local LFS media.

To run **one optional combined source-present diagnostic** with available originals:

```bash
uv run --dev python -m pytest -q -ra \
  tests/integration/test_broken_font_family_sources.py
```

A pass here means the three files were source-identity-checked and **safely classified**; it does **not** mean every year yielded a table, all pages were reconciled or any official answer was independently confirmed. The routine batch command can be run without a manual review of each year.

Future implementation should examine only flagged geometry failures and add a *bounded region-based glyph/visual fallback*, while separately reconciling 1397/1398 page continuations and booklet/edition evidence. **Do not silently substitute an unvalidated glyph map or whole-page OCR**. This focused step is tracked in [Issue #43](https://github.com/ehsanrs2/Konkeroo/issues/43), as part of [Issue #39](https://github.com/ehsanrs2/Konkeroo/issues/39).

Original files, 1396's 19 authentic human decisions/75 pending independent tasks, curated key claims, official/AI/final answer fields, redistribution rights decision D-010 and publication `BLOCKED` remain unchanged.
