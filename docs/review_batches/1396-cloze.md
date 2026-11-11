# 1396 — Cloze independent human review (Q11–15)

**Status: 8 Cloze review decisions recorded (7 short edits ACCEPTED, 1 token-order anomaly RESOLVED by explicit owner report).** This file preserves the original handoff context; no corrected learner-facing dataset is published.

- Original exam: `source/96.pdf`, SHA-256 `69bc3434ae61c05c85bc9fabffd0b2ce13e5b39bc71b1dfd71c16709c9638ba2`, booklet C.
- Source-linked review JSON: `dataset/review/1396-cloze-text-review.json`, exact Git blob SHA-1 `5530e4484dbc274ee23fa37f5b24d34c25f8301c`.
- Printed PDF **page 2**: passage, heading, blanks. Printed PDF **page 3**: numbered answer choices Q11–15.
- Compare with the **rendered printed PDF**, not with what seems grammatically preferable.

## Printed-source context: locate each target

The following short excerpts were checked against the **rendered pages of the original, SHA-matched `96.pdf`** (not reconstructed from the damaged text layer). **Bold** marks the target as it appears in print. These are *navigation hints and candidate readings*, **not independently accepted corrections**. The user/reviewer must still verify the original page. Ellipses and `[blank]` below indicate omitted surrounding text and are editorial notation, **not verbatim printed punctuation**.

| Task ID suffix | PDF page | Position within page | Nearby text visible in the printed PDF |
| --- | ---: | --- | --- |
| `cloze-heading-passage` | 2 | Bottom of page, boxed **PART B** heading | PART B: Cloze **Passage** |
| `cloze-human` | 2 | Cloze paragraph 1, first sentence | an integral part of **human** existence. Without a good memory |
| `cloze-on` | 2 | Cloze paragraph 2, after blank (13) | blank at birth (13) [blank] **on the** impression of the events |
| `cloze-to-study` | 2 | Cloze paragraph 2, after “objective techniques” | techniques that have enabled us **to study** our recollections |
| `cloze-14-marker` | 2 | Cloze paragraph 2, after “though,” | in the past hundred years, though, **(14)** [blank] systematic |
| `cloze-13-choice4` | 3 | Very top of page, **Q13 option 4** | 4) that slowly **takes** |
| `cloze-15-marker` | 3 | Very top of page, immediately below Q14 options | **15-** 1) with 2) from 3) in 4) to |

### Context for the nonlocal ordering anomaly

On **PDF page 2, near the last lines of the Cloze passage**, the printed text contains:

> laboratory tests of our ability **to remember** verbal and visual materials

**Updated technical diagnosis:** the *plain pdfplumber text output* shows an isolated `10` near `approaches.`, but the glyph actually sits immediately before `remember` on the same visual PDF line. Konkeroo's baseline-aware stage extractor already groups these in order as `10 remember`. Thus the guarded candidate is a single **source-aligned glyph correction** (`10 remember` → `to remember`), **without moving or deleting a token**. See [source geometry and read-only preview](1396-cloze-token-order.md). Owner-reported original-source tests and complete-word comparison followed; the owner explicitly marked this **single anomaly** PASS, recorded as ledger disposition `RESOLVED`. This does not certify the exact printed blank leaders, unresolved other tasks, or publication.

## Seven short proposed edits

Choose `ACCEPTED`, `REJECTED` or `NEEDS_FOLLOWUP` for **each**. Record the exact observed word/marker/punctuation and page.

| Task ID | PDF page | Target field | Extracted raw fragment | Proposed printed fragment | Human result |
| --- | ---: | --- | --- | --- | --- |
| `edit:cloze:cloze-heading-passage` | 2 | `section_heading` | `Pnssnge` | `Passage` | ACCEPTED (owner-reported) |
| `edit:cloze:cloze-human` | 2 | `passage_body` | `Imm an` | `human` | ACCEPTED (owner-reported) |
| `edit:cloze:cloze-on` | 2 | `passage_body` | `en the` | `on the` | ACCEPTED (owner-reported) |
| `edit:cloze:cloze-to-study` | 2 | `passage_body` | `lo study` | `to study` | ACCEPTED (owner-reported) |
| `edit:cloze:cloze-14-marker` | 2 | `passage_body` | `{14)` | `(14)` | ACCEPTED (owner-reported) |
| `edit:cloze:cloze-13-choice4` | 3 | `choice_text:4` | `rakes` | `takes` | ACCEPTED (owner-reported) |
| `edit:cloze:cloze-15-marker` | 3 | `number_marker` | `t 5-` | `15-` | ACCEPTED (owner-reported) |

## One nonlocal ordering anomaly

- Task ID: `anomaly:cloze:cloze-ability-to-remember-displaced-token`
- Source PDF **page 2**: the owner confirmed the printed phrase `ability to remember verbal and visual materials` and no extra printed `10` near `approaches`. Only the **plain text extraction order** looks displaced; Konkeroo's stage groups `10 remember` correctly (see linked diagnostic).
- **Recorded `RESOLVED` per explicit human PASS disposition:** the reviewer verified the original printed words, ran the source-present integration checks (owner reported `2 passed`), inspected the entire candidate passage and confirmed its words; the precise glyph-only remedy is `10 remember` → `to remember` in the existing stage order. The source-proposal JSON remains unchanged and historically labels the original anomaly as unresolved; the **ledger** carries the later disposition. See [technical diagnostic](1396-cloze-token-order.md).

## How to report results

Review both original PDF pages and send eight lines to [Issue #20](https://github.com/ehsanrs2/Konkeroo/issues/20) or in the project chat. Format: `task-id: DISPOSITION — printed source evidence` (word/marker and page).

The assistant will then **transcribe the human reviewer's actual responses**, not generate approvals, into a **separate PR** updating only the ledger and matching tests. Each decision must include reviewer attribution `ehsanrs2`, `INDEPENDENT_HUMAN`, exact source SHA-256, 1-based source page and the pinned reviewed artifact revision `5530e4484dbc274ee23fa37f5b24d34c25f8301c`.

After the resolution ledger PR is merged: **19 reviewed, 75 pending** out of 94. The 7 Cloze text edits and this one anomaly are owner-attested; publication remains **`BLOCKED`** because Reading, initial-key and other tasks are still pending. The formatted `(N) ____` leaders are **presentation only**; no claim is made about exact PDF punctuation or a released corrected passage.

Do not alter original PDFs, raw staged text, the curated proposals or final/official answer authority during review. See [review protocol](../REVIEW_PROTOCOL.md).
