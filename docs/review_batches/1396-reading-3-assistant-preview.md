# 1396 Reading Passage 3 — assistant-only provisional preview

**Scope:** only Passage 3, original PDF **page 5**, Q26–Q30. This is a source-bound, in-memory **`ASSISTANT_PROVISIONAL`** output, not independently reviewed final exam data or a new answer key. The owner explicitly opted out of routine per-word human review **for provisional development** in merged PR #30.

- Original `source/96.pdf` SHA-256: `69bc3434ae61c05c85bc9fabffd0b2ce13e5b39bc71b1dfd71c16709c9638ba2`.
- Immutable Reading review: `dataset/review/1396-reading-text-review.json`, Git blob SHA-1 `2f8f9b3c323b2b7173fcf7d8cf237e44804621f1`.
- Issue: [#35](https://github.com/ehsanrs2/Konkeroo/issues/35).
- Existing review ledger remains **19 human-recorded decisions / 75 pending independent-review tasks**, `publication_status: BLOCKED` and `independently_verified: false`.

## Source-linked corrections — 13 short editorial proposals

The original revision-pinned `r1396-24` through `r1396-36` proposals belong to five fields:

| Original PDF page 5 field | Proposal IDs | Representative source-layer glyph/punctuation → suggested printed reading |
| --- | --- | --- |
| Passage-3 body | `r1396-24..29` | `pictures. computer` → `pictures, computer`; `rest their performance` → `test their performance` |
| Q26 stem | `r1396-30` | `What docs` → `What does` |
| Q26 choice 4 | `r1396-31` | `TI1e rapidly` → `The rapidly` |
| Q28 stem | `r1396-32..33` | `According lo` → `According to`; `CAD 10` → `CAD to` |
| Q30 stem | `r1396-34..36` | `11nragrn11h` → `paragraph`; `mosl likely` → `most likely` |

The actual original importer maps **exactly Q26–Q30 to Reading-3**; Q25 is in Reading-2. This distinction is asserted in synthetic and source-present tests to avoid repeating the real-PDF issue corrected in PR #34.

For every edit, the preview checks the original PDF filename/hash, original proposal blob and ledger release guard, unique exact raw-field anchor, page-5 provenance, correct task identity/order, and non-overlap between **all editorial and technical spans**. Candidate text is derived by right-to-left replacement in memory only. If any guard fails, it returns `BLOCKED` with diagnostic `errors` and **zero** partial candidate fields.

## Two separate geometry-supported glyph candidates

The original source-linked review records two `NONLOCAL_TEXT_ORDER` anomalies, but direct inspection of the rendered page 5 and text-layer coordinates shows these are glyph mappings in an **already correct visual order**. The baseline-aware importer groups both correctly. We therefore **do not move, insert or delete any tokens**.

| Anomaly ID | Exact unique source-stage anchor | Suggested printed-reading anchor | Same-line geometry |
| --- | --- | --- | --- |
| `r1396-order-p3-it` | `computer science. 11 is used routinely` | `computer science. It is used routinely` | `11` x0=175.5, x1=182.85 pt, bottom=239.844 pt, immediately after `science.` and before `is` |
| `r1396-order-p3-to` | `CAD techniques 10 design vehicles` | `CAD techniques to design vehicles` | `10` x0=396.75, x1=404.606 pt, bottom=336.003 pt, between `techniques` and `design` |

Both are **`GEOMETRY_ALIGNED_ASSISTANT_PROVISIONAL`**, not independent human `RESOLVED` entries. The original curated review JSON's unresolved anomaly records remain unchanged. **Do not confuse the passage-body `10` with the separate Q28 `CAD 10` editorial proposal**; both occur on page 5 but belong to different fields.

## Two unusual phrases really printed in the exam

- Passage-body string: `"walk" thorough the rooms` — **thorough** is printed, not **through**. Preserve it exactly.
- Q30 choice 2: `fight training` — **fight**, not **flight**. Keep the option unchanged, even if a different English phrase looks more plausible.

The second phrase is an unmodified field included only to enforce preservation. Neither oddity is an assistant-generated human acknowledgment.

## Local original-source test (after PR merge)

```bash
git pull --ff-only
uv sync --locked --dev
uv run --dev python -m pytest -q -ra \
  tests/integration/test_1396_reading3_source.py
```

**Expected only after actual execution:** `1 passed` when `source/96.pdf` is present, has its expected hash and the real importer and preview agree. `1 skipped` without the source LFS media in public CI **does not** confirm source-present success. The test checks the original staged fields, exact Q26–30 membership, all 13 edits, both unique glyph anchors, same-line PDF word geometry and immutable ledger/source.

For local, **in-memory-only** inspection without writing the original passage or options into the public repository:

```bash
uv run --dev python - <<'PY'
import json
from pathlib import Path
from english_exam.pipeline import extract_staged_1396
from english_exam.reading3_provisional import preview_1396_reading3

directory = Path("dataset/review")
reading = json.loads((directory / "1396-reading-text-review.json").read_text(encoding="utf-8"))
ledger = json.loads((directory / "1396-review-ledger.json").read_text(encoding="utf-8"))
stage = extract_staged_1396(Path("source/96.pdf"))
preview = preview_1396_reading3(stage, reading, ledger)
print("Status:", preview.status)
print("Errors:", preview.errors)
print("Edits:", preview.applied_edit_ids)
print("Technical glyphs:", [(c.anomaly_id, c.status) for c in preview.technical_candidates])
assert preview.status == "ASSISTANT_PROVISIONAL", preview.errors
for field in preview.fields:
    print(field.field_id, "page:", field.source_pdf_page, "edits:", field.applied_edit_ids)
    print(field.candidate_text)
PY
```

**Do not commit generated full copyrighted passage/option text or publish the official initial answer key.** The 13 original proposals and two historical anomalies remain pinned and non-human; 19 authentic human decisions and 75 pending independent tasks stay unchanged. Source-rights checks and final-answer verification are separate release requirements.
