# 1396 — Cloze independent human review (Q11–15)

**Status: 8 tasks pending; no Cloze decisions yet.** This file is a handoff, **not** a set of approved corrections.

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

The text layer does **not** preserve that word order: `to` is absent at the expected place and a token resembling `10` occurs farther down, near `approaches.`. This printed context locates the anomaly; it **does not** establish how the displaced token must be removed or repositioned in a corrected structured field. If you cannot identify the complete correction, report `NEEDS_FOLLOWUP`.

## Seven short proposed edits

Choose `ACCEPTED`, `REJECTED` or `NEEDS_FOLLOWUP` for **each**. Record the exact observed word/marker/punctuation and page.

| Task ID | PDF page | Target field | Extracted raw fragment | Proposed printed fragment | Human result |
| --- | ---: | --- | --- | --- | --- |
| `edit:cloze:cloze-heading-passage` | 2 | `section_heading` | `Pnssnge` | `Passage` | pending |
| `edit:cloze:cloze-human` | 2 | `passage_body` | `Imm an` | `human` | pending |
| `edit:cloze:cloze-on` | 2 | `passage_body` | `en the` | `on the` | pending |
| `edit:cloze:cloze-to-study` | 2 | `passage_body` | `lo study` | `to study` | pending |
| `edit:cloze:cloze-14-marker` | 2 | `passage_body` | `{14)` | `(14)` | pending |
| `edit:cloze:cloze-13-choice4` | 3 | `choice_text:4` | `rakes` | `takes` | pending |
| `edit:cloze:cloze-15-marker` | 3 | `number_marker` | `t 5-` | `15-` | pending |

## One nonlocal ordering anomaly

- Task ID: `anomaly:cloze:cloze-ability-to-remember-displaced-token`
- Source PDF **page 2**: printed phrase was visually read as `ability to remember`; native text layer has a `10`-like token displaced near the end of the passage.
- Choose **`RESOLVED` only if** you can document the entire correct source-aligned ordering and what should happen to the misplaced token. Otherwise choose **`NEEDS_FOLLOWUP`**, report the printed phrase you observed and why the full repair is still uncertain. Do **not** blindly insert `to` and leave a duplicate elsewhere.

## How to report results

Review both original PDF pages and send eight lines to [Issue #20](https://github.com/ehsanrs2/Konkeroo/issues/20) or in the project chat. Format: `task-id: DISPOSITION — printed source evidence` (word/marker and page).

The assistant will then **transcribe the human reviewer's actual responses**, not generate approvals, into a **separate PR** updating only the ledger and matching tests. Each decision must include reviewer attribution `ehsanrs2`, `INDEPENDENT_HUMAN`, exact source SHA-256, 1-based source page and the pinned reviewed artifact revision `5530e4484dbc274ee23fa37f5b24d34c25f8301c`.

Current overall docket after merged [PR #19](https://github.com/ehsanrs2/Konkeroo/pull/19): **11 reviewed, 83 pending**. The release remains `BLOCKED`. Even after all eight Cloze decisions have been recorded, the other 75 tasks will still have no decisions. A `NEEDS_FOLLOWUP` anomaly remains an unresolved release blocker.

Do not alter original PDFs, raw staged text, the curated proposals or final/official answer authority during review. See [review protocol](../REVIEW_PROTOCOL.md).
