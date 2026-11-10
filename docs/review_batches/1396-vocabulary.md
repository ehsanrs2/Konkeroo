# 1396 — independent Vocabulary review batch (Q1–10)

**Not yet reviewed.** This is a reviewer handoff, not a set of approved edits. It covers the **11 existing text-correction proposals** from M4a, affecting Q1, Q3, Q4, Q5, Q9 and Q10. No proposals were recorded for Q2, Q6, Q7 or Q8; this does **not** certify them error-free.

Review the **printed PDF page 2** from the original booklet C, independently of the assistant's proposed replacement. If the printed word or marker differs from both columns, choose `REJECTED` and describe the actual observed wording.

- Exam: `source/96.pdf`, SHA-256 `69bc3434ae61c05c85bc9fabffd0b2ce13e5b39bc71b1dfd71c16709c9638ba2`
- Source-linked artifact: `dataset/review/1396-vocabulary-correction-proposals.json`
- Exact artifact revision (Git blob SHA-1): `d86e605924af939d03e4605896f6c42f5ec019ab`
- Review status: **11 pending; zero human approvals**
- Allowed dispositions: `ACCEPTED`, `REJECTED`, `NEEDS_FOLLOWUP`

| Task ID | Question | Field | Raw text-layer fragment | Suggested printed reading | PDF page | Human decision |
| --- | --- | --- | --- | --- | ---: | --- |
| `edit:vocabulary:q01-number` | q-01 | `number_marker` | `I·` | `1-` | 2 | — |
| `edit:vocabulary:q01-might` | q-01 | `stem` | `mighl` | `might` | 2 | — |
| `edit:vocabulary:q01-about` | q-01 | `stem` | `Rbour` | `about` | 2 | — |
| `edit:vocabulary:q01-punctuation` | q-01 | `stem` | `disease. so` | `disease, so` | 2 | — |
| `edit:vocabulary:q01-out` | q-01 | `stem` | `find our` | `find out` | 2 | — |
| `edit:vocabulary:q03-to` | q-03 | `stem` | `ro settle` | `to settle` | 2 | — |
| `edit:vocabulary:q04-continues` | q-04 | `stem` | `contiuues` | `continues` | 2 | — |
| `edit:vocabulary:q05-not` | q-05 | `stem` | `did nol` | `did not` | 2 | — |
| `edit:vocabulary:q05-to` | q-05 | `stem` | `try 10 control` | `try to control` | 2 | — |
| `edit:vocabulary:q09-choice-one` | q-09 | `choice_marker:1` | `!)` | `1)` | 2 | — |
| `edit:vocabulary:q10-number` | q-10 | `number_marker` | `10..` | `10-` | 2 | — |

## How the reviewer submits findings

1. Independently view the original PDF at the page above and confirm its SHA-256.
2. For every listed task, choose a disposition and write a **specific evidence note** (what was printed and why the edit is or is not faithful). Avoid a generic note such as “looks right.”
3. Add decisions only to `dataset/review/1396-review-ledger.json` in a separate PR. **Do not** change the curated source artifact or mark `publication_status` verified.
4. Each decision requires `reviewer_role: INDEPENDENT_HUMAN`, `reviewer_id`, `evidence_note`, `evidence_source_sha256`, `evidence_pdf_page: 2`, and `reviewed_artifact_blob_sha1: "d86e605924af939d03e4605896f6c42f5ec019ab"`, along with the exact `task_id` and `disposition`.
5. Run `uv run python -m english_exam.review_docket --review-dir dataset/review` and project tests. The review remains **blocked for publication** while the other 83 tasks are pending.
6. If the actual proposal content must change, start a new content revision and re-review the affected decisions; do not carry forward an old approval by task ID alone.

The assistant who made the original visual proposals must **not** self-attest as the independent human reviewer. This review does not certify the official answer key or create the learner-facing corrected exam.

[Full review protocol](../REVIEW_PROTOCOL.md)
