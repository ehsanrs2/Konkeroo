# 1396 Reading Passage 1 — assistant-only source-aligned preview

**Status: assistant provisional implementation; no new independent human decisions.**

The owner opted out of routine per-item human source review for *provisional development* in [PR #30](https://github.com/ehsanrs2/Konkeroo/pull/30). This preview implements that workflow only for Reading Passage 1 on original PDF page 3, **not** for all Reading passages or the official key.

- Original exam: `source/96.pdf`, booklet C, SHA-256 `69bc3434ae61c05c85bc9fabffd0b2ce13e5b39bc71b1dfd71c16709c9638ba2`.
- Proposal source: `dataset/review/1396-reading-text-review.json`, pinned Git blob `2f8f9b3c323b2b7173fcf7d8cf237e44804621f1`. It remains historically marked `PENDING_INDEPENDENT_REVIEW`.
- Existing historical human ledger: **19 recorded decisions, 75 pending**, `publication_status: BLOCKED`, `independently_verified: false`.
- Tracking: [Issue #28](https://github.com/ehsanrs2/Konkeroo/issues/28).

## What the code does

`src/english_exam/reading1_provisional.py` provides `preview_1396_reading1(staged, reading_review, ledger)`. Its only successful output status is **`ASSISTANT_PROVISIONAL`**. It constructs in-memory candidate fields; it **does not** write `corrected_text`, overwrite the original `raw_text`, add ledger human decisions, set answer authority or publish question passages.

Exactly 12 preexisting candidate edits (`r1396-01` through `r1396-12`) are mapped to the original page-3 fields: seven edits inside the passage body, two inside Q16 stem, one in Q17 choice 1, and one each in Q18 number marker and stem. Each field checks page-3 provenance and one unique exact raw source anchor. All replacements are applied from fixed nonoverlapping offsets rather than unguarded string rewrites. An unexpected, missing, duplicated, or overlapping anchor **blocks the entire preview**. It also pins the original exam hash, Reading artifact Git blob SHA-1, validated source stage and unchanged release-blocked ledger.

### Separate Q19 geometry diagnostic, not an automatic review decision

Plain `pdfplumber.Page.extract_text(x_tolerance=2, y_tolerance=2)` emits `as------.` *above* the Q19 number in text sequence. The actual original PDF page 3 word coordinates show the `as------.` glyph **to the right of** `described` on the **same visual line**:

| Word | x0 (pt) | x1 (pt) | bottom (pt) |
| --- | ---: | ---: | ---: |
| `described` | 261.750 | 303.854 | 707.730 |
| `as------.` | 309.750 | 378.398 | 709.458 |

Their bottom difference is ~**1.728 pt**, within Konkeroo's 3-point baseline tolerance. The project's staged Q19 `stem.raw_text` already reads `The tone of the passage could best be described as------.` with exact source provenance. Therefore **do not** move or insert `as` again. The successful preview reports `STAGED_ORDER_ALIGNED_NOT_INDEPENDENTLY_REVIEWED` and leaves Q19 completely unchanged. A changed/ambiguous Q19 stem causes `BLOCKED`, not a guessed repair or `RESOLVED` decision.

### Unusual actually printed phrase

The phrase **`format of the fixture`** is present in the printed Passage 1. The preview requires it **exactly once** in original and proposed body and forbids automatic transformation to **`format of the future`** even though the latter may seem more natural. No `ACKNOWLEDGED` human evidence is invented.

## Test locally with original PDF

From the repository root (after merging this PR):

```bash
git pull --ff-only
uv sync --locked --dev
uv run --dev python -m pytest -q tests/integration/test_1396_reading1_source.py
```

Expected: **1 passed** with original `source/96.pdf` present and SHA-matched; **1 skipped** if source LFS media is absent. A skipped source-conditional test is not evidence that original-source extraction passed. Source-independent tests run in public CI.

For a **local in-memory-only** preview:

```bash
uv run --dev python - <<'PY'
import json
from pathlib import Path
from english_exam.pipeline import extract_staged_1396
from english_exam.reading1_provisional import preview_1396_reading1

folder = Path("dataset/review")
review = json.loads((folder / "1396-reading-text-review.json").read_text(encoding="utf-8"))
ledger = json.loads((folder / "1396-review-ledger.json").read_text(encoding="utf-8"))
staged = extract_staged_1396(Path("source/96.pdf"))
result = preview_1396_reading1(staged, review, ledger)
print("Status:", result.status)
print("Applied IDs:", result.applied_edit_ids)
print("Q19:", result.q19_order_status)
print("Errors:", result.errors)
assert result.status == "ASSISTANT_PROVISIONAL", result.errors
for field in result.fields:
    print(field.field_id, "edits:", field.applied_edit_ids)
    print(field.candidate_text)
PY
```

**Do not paste the entire copyrighted passage into a public issue or commit generated preview text to public Git.** Preserve the 19 genuine owner-attested decisions and 75 outstanding *independent-review* tasks. Next engineering stage: Passage 2 and its ordering anomalies, with similarly narrow source-bound previews; the initial official answer key remains unverified. The current preview is neither a human signoff nor a certified dataset release.
