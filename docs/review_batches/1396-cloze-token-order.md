# 1396 Cloze: source-aligned diagnosis of the apparent displaced token

**Status: technical candidate only — the eighth Issue #20 review task is still `PENDING`, not `RESOLVED`.** This is a **read-only** diagnostic, not a change to raw source, a verified correction or a final learner-facing passage.

## Source and human observation

- Source: `source/96.pdf` (SHA-256 `69bc3434ae61c05c85bc9fabffd0b2ce13e5b39bc71b1dfd71c16709c9638ba2`).
- Printed PDF page **2**, last lines of the Cloze passage.
- The owner independently reports that the printed phrase is `ability to remember verbal and visual materials` and no extra `10` appears beside `approaches`. This is the owner's submitted visual observation, not an assistant-generated independent review.
- Existing source-linked artifact `1396-cloze-text-review.json` remains unchanged/pinned (`5530e4484dbc274ee23fa37f5b24d34c25f8301c`). Its earlier “nonlocal” description refers to the *plain extracted text sequence*, not necessarily the project's staged geometry-aware word order.

## What actually happens

A plain `pdfplumber.Page.extract_text(x_tolerance=2, y_tolerance=2)` returns a line with `remember verbal ...`, followed by a **standalone** `10` before `approaches.`. However the actual glyph coordinates on **PDF page 2** place `10` **before `remember` on the same visual line**, not beside `approaches`:

| PDF text-layer word | x0 | x1 | top | bottom |
| --- | ---: | ---: | ---: | ---: |
| `10` (printed as `to`) | 84.000 | 91.740 | 714.042 | 722.042 |
| `remember` | 99.750 | 142.240 | 710.946 | 722.946 |
| `approaches.` | 84.000 | 135.948 | 725.196 | 737.196 |

The `10` bottom differs by only **0.904 PDF points** from `remember`, but by **15.154 points** from `approaches.`. Its different top position (3.096 points from the top of `remember`) likely explains why the simple text extractor groups it as a separate line.

Konkeroo's `group_words_into_lines` in `pdf_layout.py` groups words by **bottom/baseline proximity with a 3-point tolerance**, so its staged `cloze-1.body.raw_text` retains the *correct relative order*:

```text
... laboratory tests of our ability
10 remember verbal and visual materials ...
... approaches.
```

Thus **the source-specific staged repair requires one anchored glyph correction, not moving or deleting a separate token elsewhere**:

```text
before: ... ability
        10 remember verbal and visual materials ...
after:  ... ability
        to remember verbal and visual materials ...
```

The newline in this preview represents the **physical line break in the passage** and is deliberately retained. This is a preview only: `to` is the printed reading, while `10` is the damaged PDF character mapping.

## Guarded technical candidate

`preview_1396_cloze_to_remember(staged)` in `src/english_exam/cloze_order_review.py` verifies the immutable 1396 source identity and validated stage, the unique exact cross-line anchor, source page-2 provenance, unmodified raw/corrected field state, and the original passage ending. It returns `PROPOSED_PENDING_TECHNICAL_REVIEW` and an **in-memory** proposed full-field text. It never mutates `raw_text`, writes `corrected_text`, or changes review decisions.

Tests include source-independent negative cases (missing/duplicated/out-of-order tokens, wrong SHA, wrong provenance, already transformed text) and a source-conditional check of the real PDF, the **actual `extract_staged_1396` pipeline**, and glyph geometry. In CI, that integration check **skips** when LFS source media is absent; a human/maintainer must run it locally against the hashed original source before accepting the repair.

## Why the first full-field output still contains OCR-like artifacts

The owner ran the original single-token preview and returned `PROPOSED_PENDING_TECHNICAL_REVIEW` with the expected `to remember` in place. The **same output still includes** `Imm an`, `en the`, `lo study`, and `{14)`, because that preview deliberately fixes **only** the eighth to/10 problem. Those four short corrections were separately attested by the owner in merged PR #23; Q13 option 4, Q15 numbering and the section heading are **outside** this passage-body field.

A new read-only `preview_1396_reviewed_cloze_passage` composes the four **accepted passage-body** edits with the **still-pending** `to/10` technical candidate. It fails closed unless source SHA, the pinned curated review JSON, the actual owner-attested ledger decisions, unique raw fragments and the original staged passage are all consistent. It returns `PENDING_FULL_FIELD_HUMAN_REVIEW`; no raw text, `corrected_text`, reviewer ledger or answer key is changed.

From the repository root with original PDF present:

```bash
uv run --dev python - <<'PY'
import json
from pathlib import Path

from english_exam.cloze_full_preview import preview_1396_reviewed_cloze_passage
from english_exam.pipeline import extract_staged_1396

directory = Path("dataset/review")
review = json.loads((directory / "1396-cloze-text-review.json").read_text(encoding="utf-8"))
ledger = json.loads((directory / "1396-review-ledger.json").read_text(encoding="utf-8"))
staged = extract_staged_1396(Path("source/96.pdf"))
result = preview_1396_reviewed_cloze_passage(staged, review, ledger)
print("Status:", result.status)
print("Errors:", result.errors)
assert result.proposed_full_text is not None, result.errors
print(result.proposed_full_text)
PY
```

Compare this entire *candidate* passage against page 2 of the original. Placeholder-like blank markings (e.g. `-·-··`) are **not** silently normalized by this procedure; blanks and layout should be separately checked in a later full-exam release review. The `cloze-heading-passage`, `cloze-13-choice4`, and `cloze-15-marker` approvals remain in the ledger but are **not** part of this passage-body-only output.

Run the source-present check:

```bash
uv run --dev python -m pytest -q tests/integration/test_1396_cloze_order_source.py
```

The integration test verifies both the one-token candidate and the combined read-only preview against actual source. A passing test establishes *mechanical consistency*, **not** independent approval of the whole corrected passage or a right to publish the source.

## Consistent question blanks — reviewer-facing rendering only

After running the merged PR #25 unified preview on the original PDF, the owner reported that **the words looked correct** and identified a remaining readability issue: gaps Q11–15 used inconsistent artifacts such as `(11) -·-··-··` and `( 13) -·-·-·`. This is a **presentation concern**, not a new independent approval of the blank glyphs/punctuation or a request to overwrite the source.

The follow-up `format_1396_cloze_blanks_for_review` function produces a **separate display-only field** for human inspection, with the consistent visual marker `(N) ____`. It requires a successfully source- and ledger-gated unified preview; verifies exactly five gaps in increasing Q11–15 order, with unique known preceding/following context; and refuses to display a guessed result if the raw gap leader, sequence or context differs. The function does **not** change the `FullClozePreview.proposed_full_text`, the original PDF, `raw_text`, the curated JSON, human decisions or `corrected_text`.

Illustrative local formatting, **not a full transcription of the source**:

| Gap | Source-layer appearance | Reviewer display |
| --- | --- | --- |
| Q11 | `(11) -·-··-··a book` | `(11) ____ a book` |
| Q12 | `(12) ······---: Plato` | `(12) ____: Plato` |
| Q13 | `( 13) -·-·-· on the` | `(13) ____ on the` |
| Q14 | `(14) ···-···-·systematic` | `(14) ____ systematic` |
| Q15 | `( 15) -····-·· more recent` | `(15) ____ more recent` |

**Punctuation and whitespace:** The colon immediately following Q12's raw leader is *preserved as-is*, not silently removed or asserted to be correct in print. A single display space is inserted where the damaged gap leader runs directly into the next word. The literal underscores are **UI placeholders**, not a claim that the PDF contains underscores. For release, a separate review must address any genuine ambiguity in the printed punctuation and blanks.

After merging this PR, run from the repository root:

```bash
uv run --dev python - <<'PY'
import json
from pathlib import Path

from english_exam.cloze_blank_display import format_1396_cloze_blanks_for_review
from english_exam.cloze_full_preview import preview_1396_reviewed_cloze_passage
from english_exam.pipeline import extract_staged_1396

directory = Path("dataset/review")
review = json.loads((directory / "1396-cloze-text-review.json").read_text(encoding="utf-8"))
ledger = json.loads((directory / "1396-review-ledger.json").read_text(encoding="utf-8"))
staged = extract_staged_1396(Path("source/96.pdf"))
preview = preview_1396_reviewed_cloze_passage(staged, review, ledger)
display = format_1396_cloze_blanks_for_review(preview)

print("Preview:", preview.status)
print("Display:", display.status)
print("Errors:", display.errors)
assert display.text is not None, display.errors
print(display.text)
PY
```

**Expected status:** `PENDING_BLANK_DISPLAY_REVIEW` and `Errors: ()`. The original candidate `proposed_full_text` remains unchanged. The anomaly `to/10` remains pending a separate task-specific decision, even if the display looks consistent.

## Still required before closing Issue #20

1. Run the actual source-present integration check and preserve its logs, including the unchanged original PDF SHA.
2. Review the entire in-memory suggested passage field with its source-aligned line provenance, not only the short word.
3. Obtain an explicit human disposition for the **eighth** anomaly task. A printed-text confirmation by itself does **not** authorize an automatic `RESOLVED` entry; `NEEDS_FOLLOWUP` or no decision remain valid until the engineering review is complete.
4. If accepted, design a **separate, versioned corrected-text artifact** and re-review the proposed field. Keep the original raw data, all key answers and final-verified status unchanged.

Until then **Issue #20 stays open** and the 1396 review ledger remains release-blocked.
