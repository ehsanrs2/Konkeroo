# Reading Passage 2 — source-aligned assistant-only provisional preview (1396)

**Authority: ASSISTANT_PROVISIONAL.** No per-item human approval is required to develop this preview, under the owner's [merged policy PR #30](https://github.com/ehsanrs2/Konkeroo/pull/30). It is *not* independently verified, learner-releasable data or a declaration that the official key is correct.

- Original source: `source/96.pdf`, SHA-256 `69bc3434ae61c05c85bc9fabffd0b2ce13e5b39bc71b1dfd71c16709c9638ba2`, booklet C.
- Source pages: **PDF page 4** (Passage 2, Q21–24) and **PDF page 5** (Q25, which belongs to Passage 2). Q20 is also associated with Passage 1 and is **not** edited here.
- Fixed proposal revision: `dataset/review/1396-reading-text-review.json`, Git blob SHA-1 `2f8f9b3c323b2b7173fcf7d8cf237e44804621f1`.
- Tracking: [Issue #32](https://github.com/ehsanrs2/Konkeroo/issues/32).

## Eleven existing short proposals

All are uniquely anchored to an exact `raw_text` source field with the original PDF page provenance and the pinned proposal revision; the renderer refuses duplicated, missing or overlapping edits. The eleven IDs are `r1396-13` through `r1396-23`:

| Location | IDs | Original text-layer examples | In-memory printed-reading candidates |
| --- | --- | --- | --- |
| Page 4, Passage 2 heading | 13 | `PASSAGB2:` | `PASSAGE 2:` |
| Page 4, Passage 2 body | 14–20 | `present This applies.`, `whenever a. disk`, `limes, has`, `TI1e concept`, `self-contnine<l`, `1988, however.`, `vulnerabilities ill operating` | `present. This applies,`, `whenever a disk`, `times, has`, `The concept`, `self-contained`, `1988, however,`, `vulnerabilities in operating` |
| Page 4, Q21 choice 4 | 21 | `TI1e spread` | `The spread` |
| Page 4, Q22 question | 22 | `According to lhe passage` | `According to the passage` |
| Page 5, Q25 question | 23 | `mosl probably` | `most probably` |

The source-independent tests use invented surrounding sentences. The complete original passage, answer key and question-option sequences are **not committed**.

## Two technical glyph corrections, separate from those eleven edits

The original review JSON historically labels these as unresolved anomalies. Direct inspection of the rendered SHA-matched PDF page 4, its PDF word geometry and the baseline-based importer establishes that the affected glyphs are already in **the correct visual reading order** in the staged text. Consequently, **do not move, drop or duplicate a token**; consider narrowly anchored *in-memory* glyph readings:

1. `r1396-order-p2-stray`: the text layer's `11` occurs immediately to the left of `worm,` on the same baseline and corresponds to the printed `a`. After the seven normal passage-body edits, the exact anchor `concept of 11 worm` can be previewed as `concept of a worm`.
2. `r1396-order-q22`: the text-layer `or` occurs immediately after `beginning` and immediately before `lhe` on the printed Q22 stem's baseline. The source print reads **“in the beginning of the virus era”**. After the short Q22 proposal, the unique anchor `beginning or lhe virus era` can be previewed as `beginning of the virus era`.

Both appear in `technical_candidates` with method `GEOMETRY_ALIGNED_ASSISTANT_PROVISIONAL`. Their original review-anomaly records and the independent-human ledger remain **unchanged**: no `RESOLVED` or `INDEPENDENT_HUMAN` assertion is fabricated. If geometry, source text or the unique anchor fails, the entire preview returns **BLOCKED** rather than applying a guessed edit. A technical correction candidate is not itself an independent human confirmation of the printed text.

## Printed-source peculiarity

Original Q23 reads **`The work "self-contained"`** in the question stem. This may look like a printing mistake for `word`, but it is really printed **work**. The preview requires this exact phrase **once** in the original and candidate; it must not silently become `The word`.

## Reproducible local checks

After merging the implementation PR and fetching the original PDF into `source/96.pdf`, run:

```bash
git pull --ff-only
uv sync --locked --dev
uv run --dev python -m pytest -q tests/integration/test_1396_reading2_source.py
```

Expected **1 passed** if the genuine original `source/96.pdf` matches SHA-256 and the real importer produces the observed fields/geometry. **1 skipped** in CI without the LFS media means that original-PDF test **has not run**, even if source-independent tests pass.

To view the **local, read-only provisional** field candidates without writing full copyrighted passage text into the Git repository:

```bash
uv run --dev python - <<'PY'
import json
from pathlib import Path
from english_exam.pipeline import extract_staged_1396
from english_exam.reading2_provisional import preview_1396_reading2

directory = Path("dataset/review")
review = json.loads((directory / "1396-reading-text-review.json").read_text(encoding="utf-8"))
ledger = json.loads((directory / "1396-review-ledger.json").read_text(encoding="utf-8"))
staged = extract_staged_1396(Path("source/96.pdf"))
result = preview_1396_reading2(staged, review, ledger)
print("Status:", result.status, "Errors:", result.errors)
print("Short edits:", result.applied_edit_ids)
for candidate in result.technical_candidates:
    print(candidate.anomaly_id, candidate.status, candidate.suggested_printed_anchor)
assert result.status == "ASSISTANT_PROVISIONAL", result.errors
for field in result.fields:
    print(field.field_id, "page", field.source_pdf_page, "edits", field.applied_edit_ids)
    print(field.candidate_text)
PY
```

**Do not paste the full copyrighted text into a public issue or commit a generated full dataset.** After this narrow slice, Reading Passage 3 (original PDF page 5) should receive its own source-bound engineering PR; the official 1396 initial key, source-rights decision, and future educational release remain separate blockers. Human-review docket remains **19 historical decisions / 75 pending**, with `publication_status: BLOCKED`.
