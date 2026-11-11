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

## Still required before closing Issue #20

1. Run the actual source-present integration check and preserve its logs, including the unchanged original PDF SHA.
2. Review the entire in-memory suggested passage field with its source-aligned line provenance, not only the short word.
3. Obtain an explicit human disposition for the **eighth** anomaly task. A printed-text confirmation by itself does **not** authorize an automatic `RESOLVED` entry; `NEEDS_FOLLOWUP` or no decision remain valid until the engineering review is complete.
4. If accepted, design a **separate, versioned corrected-text artifact** and re-review the proposed field. Keep the original raw data, all key answers and final-verified status unchanged.

Until then **Issue #20 stays open** and the 1396 review ledger remains release-blocked.
