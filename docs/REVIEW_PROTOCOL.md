# Independent review and release gate — 1396 English

**Status:** operational review protocol proposed in M4d. This is a human-review work queue, **not** an approval, a verified dataset, or a general PDF extraction pipeline.

## Inputs

| Source-linked file | Content and status |
| --- | --- |
| `dataset/review/1396-vocabulary-correction-proposals.json` | 11 proposals; owner-reported human review decisions recorded in merged PR #19 |
| `dataset/review/1396-cloze-text-review.json` | 7 proposals + 1 unresolved token-order anomaly |
| `dataset/review/1396-reading-text-review.json` | 36 proposals + 5 unresolved anomalies + 4 source-printed oddities to acknowledge |
| `dataset/review/1396-english-official-key.json` | 30 provisional official-key claims, booklet **C**, edition **INITIAL** |
| `dataset/review/1396-review-ledger.json` | **11 Vocabulary decisions recorded; 83 pending**; publication still blocked |

Exam `source/96.pdf` SHA-256: `69bc3434ae61c05c85bc9fabffd0b2ce13e5b39bc71b1dfd71c16709c9638ba2`.

Key `source/96_Key.pdf` SHA-256: `5d421dcddc780120b13a08753fd2559e7ec02a60200c7c88f4211d70429cba61`.

The review docket contains **94 distinct items**: 54 editorial edits, 6 unresolved source-order anomalies, 4 unusual *printed* phrases, and 30 official-key positions. Source-printed oddities are not automatically errors; an acknowledgment does not authorize their correction.

## Generate the audit

Run from the repository root, after installing the locked project dependencies:

```bash
uv run python -m english_exam.review_docket --review-dir dataset/review
```

The current expected result is `BLOCKED_PENDING_REVIEW`, **83 pending and 11 reviewed** (all 94 tasks remain in the docket). The command returns exit status 0 for a *validly structured but pending* dossier; it returns nonzero for invalid or unreadable inputs. Exit status 0 does **not** mean content is verified or publishable.

The docket derives IDs from the existing artifacts rather than copying question/answer sequences. Example task IDs:

- `edit:vocabulary:q01-might` — inspect a text-layer correction on original exam page 2
- `edit:cloze:cloze-human` — inspect the Cloze passage on page 2
- `edit:reading:r1396-02` — inspect the Reading passage on page 3
- `anomaly:cloze:cloze-ability-to-remember-displaced-token` — resolve a nonlocal text-order defect
- `key:q01` — independently compare the initial official key's Q1 claim with the actual **key page 1**, not the exam page
- `printed:reading:<digest>` — inspect an unusual source-printed phrase; the stable short digest is derived from PDF page and exact printed fragment

To see every ID, inspect the returned `ReviewDocket.items` programmatically; its IDs and page locators are deterministic.

## Review artifact revision integrity

The ledger pins the **exact Git blob SHA-1** for each of the four curated review JSON artifacts (Vocabulary, Cloze, Reading and initial key). This revision ID identifies the **proposed data**, while `evidence_source_sha256` identifies the **original PDF**. Both are required.

The validator reconstructs the checked-in JSON's UTF-8, two-space indentation, insertion-order serialization and final newline, and checks its Git blob identity. It rejects any unnoticed edit, including changes to plausible replacement text or valid key positions. Every human decision must also name the exact artifact revision inspected via `reviewed_artifact_blob_sha1`. If a source-artifact revision changes, old decisions referencing the old revision are invalid even when their task ID still exists. Require re-review of changed material, never copy approvals automatically.

The [1396 Vocabulary review batch](review_batches/1396-vocabulary.md) has 11 owner-reported decisions recorded in PR #19. The next review is [1396 Cloze on printed PDF pages 2–3](review_batches/1396-cloze.md) ([Issue #20](https://github.com/ehsanrs2/Konkeroo/issues/20)), with seven edits and one unresolved ordering anomaly.

## Required context in all future human-review handoffs

Every text correction or nonlocal anomaly presented for human review should include:

1. **Source locator:** exam and booklet, exact original-file SHA-256, 1-based **PDF page**, section, and question/choice number or passage paragraph.
2. **Raw fragment and proposed printed reading:** always separated, so the reviewer is not misled by text-layer damage.
3. **Short printed context:** preferably **5–12 surrounding words** or the smallest meaningful sentence fragment, with the proposed target emphasized. Include both preceding and following words when they exist; a heading or isolated answer choice can use the complete short line.
4. **Local position hint:** top/middle/bottom of PDF page, paragraph or question/option, and optionally “after/before [distinctive phrase].” For long or visually ambiguous documents, an exact source crop or page-coordinate reference may be added.
5. **Distinct uncertainty:** label any ellipsis, inserted `[blank]` marker, inferred punctuation or nonlocal text-order issue explicitly; **do not silently fabricate a complete corrected sentence**.
6. **Review authority:** context is only a navigation aid and does not itself constitute an independent human decision. Preserve existing source-linked JSON and revision pins unless opening a separate reviewed data-revision change.

The [1396 Cloze review batch](review_batches/1396-cloze.md) implements this pattern for seven proposed edits and one displaced-token anomaly. Future Reading and answer-key handoffs should follow the same principle (for answer grids, specify booklet, key page, table group/row rather than surrounding words).

## Independent review procedure

1. A **different human reviewer** obtains the original hash-matched PDF(s) and inspects the *printed source* at the referenced page, independently of the assistant's suggested correction.
2. For `edit` tasks: choose **ACCEPTED**, **REJECTED**, or **NEEDS_FOLLOWUP**. Rejecting a proposal does not guarantee the uncorrected raw text is usable; record an alternative correction as a separate reviewed change if needed.
3. For `anomaly` tasks: choose **RESOLVED** only with source-aligned evidence of the correct text/order; otherwise **NEEDS_FOLLOWUP**. A naive local substitution of misplaced `10`/`11`/glyph tokens is not sufficient.
4. For `printed` tasks: choose **ACKNOWLEDGED** when the unusual word or spelling is genuinely printed, or **DISPUTED** when the observation cannot be confirmed. Do not silently rewrite an oddity as good English.
5. For `key` tasks: choose **TRANSCRIPTION_CONFIRMED** or **DISPUTED** by **re-reading the original official booklet-C key** and identifying the claimed position. This is a check of faithful transcription, **not** an independent key-blind AI solve or proof that an initial key is final/correct.
6. For each recorded decision, add one object to `decisions` in `1396-review-ledger.json`, with `task_id`, `disposition`, `reviewer_role: INDEPENDENT_HUMAN`, a nonempty `reviewer_id`, an evidence note, the exact original `evidence_source_sha256`, 1-based `evidence_pdf_page`, and `reviewed_artifact_blob_sha1` matching the reviewed source artifact revision.
7. Use a focused PR containing the ledger update and any newly justified evidence. A reviewer identity/role field is **self-attested metadata** and cannot itself prove independence; require human oversight of the PR.
8. Re-run all tests and the docket audit. Keep original PDFs, raw staged text, AI answers, and proposed replacements unchanged until an explicit later versioned verified-content step.

**Illustrative schema only — NOT a real review decision:**

```json
{
  "task_id": "edit:vocabulary:q01-might",
  "disposition": "ACCEPTED",
  "reviewer_role": "INDEPENDENT_HUMAN",
  "reviewer_id": "example-independent-reviewer",
  "evidence_note": "EXAMPLE ONLY: checked the printed word on source PDF page 2.",
  "evidence_source_sha256": "69bc3434ae61c05c85bc9fabffd0b2ce13e5b39bc71b1dfd71c16709c9638ba2",
  "evidence_pdf_page": 2,
  "reviewed_artifact_blob_sha1": "d86e605924af939d03e4605896f6c42f5ec019ab"
}
```

Do not commit this example as an actual decision.

## Release boundary

`BLOCKED_INVALID_INPUT`: one or more identities, counts, formats, review attestations, or source references are invalid; no valid docket is returned.

`BLOCKED_PENDING_REVIEW`: at least one item has no recorded decision, or a rejected/disputed/follow-up decision remains unresolved. **Current expected state.**

`REVIEWED_NOT_PUBLISHED`: all item decisions were structurally recorded without blockers. **This still does not authorize release.** It does not attest that the reviewer really was independent; it does not settle the INITIAL-vs-final key question; and it does not populate `Question.answers.final_verified`.

A future *separate* release gate must verify the original exams and source-rights decision, review the complete corrected question/choice/passage rendering, resolve all text-order anomalies, check whether a later final key supersedes the initial key, and version a new reviewed dataset. No inference or automatic authority promotion is allowed.

Vocabulary, Cloze, Reading and answer-key proposals remain **source claims**, not final learner-facing correctness assertions.
