# 1396 — Cloze independent human review (Q11–15)

**Status: 8 tasks pending; no Cloze decisions yet.** This file is a handoff, **not** a set of approved corrections.

- Original exam: `source/96.pdf`, SHA-256 `69bc3434ae61c05c85bc9fabffd0b2ce13e5b39bc71b1dfd71c16709c9638ba2`, booklet C.
- Source-linked review JSON: `dataset/review/1396-cloze-text-review.json`, exact Git blob SHA-1 `5530e4484dbc274ee23fa37f5b24d34c25f8301c`.
- Printed PDF **page 2**: passage, heading, blanks. Printed PDF **page 3**: numbered answer choices Q11–15.
- Compare with the **rendered printed PDF**, not with what seems grammatically preferable.

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
