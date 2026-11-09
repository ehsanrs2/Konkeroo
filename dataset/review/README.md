# Direct visual review — 1396 English official key (pending independent human review)

This is a **source-linked, AI visually transcribed** mapping, not an OCR result, a reusable answer-key parser, or a verified dataset release. The existing 1396 exam parser and 1395 key importer remain as historical implementations.

- Exam: `source/96.pdf` (SHA-256 `69bc3434ae61c05c85bc9fabffd0b2ce13e5b39bc71b1dfd71c16709c9638ba2`), English questions on PDF pages 2–5.
- Official key: `source/96_Key.pdf` (SHA-256 `5d421dcddc780120b13a08753fd2559e7ec02a60200c7c88f4211d70429cba61`), page 1, **initial key**, booklet **C**, first question/answer group, rows 1–30.
- The PDF visual source was reviewed directly. The key file does not expose native answer text. For this review we did **not** run OCR/Tesseract or build an importer.
- Each answer position was compared against the corresponding visible question/choice context. This is **not** an independent, key-blind AI solution: the key was read before contextual comparison.
- Reading mapping follows question numbers, **not** source page adjacency: passage 1 Q16–20 (Q20 on next page); passage 2 Q21–25 (Q25 on next page); passage 3 Q26–30.
- The compact JSON stores answer **positions** and source locators, not a full copyrighted passage/option transcription. It does not populate `AnswerSet.final_verified` or imply a learner-facing verification decision.
- No tight cell bounding boxes are asserted; the locator is explicitly a visual table group+row, to avoid invented geometry. A future human reviewer can open the original key page and inspect any row.

## Source-to-answer summary

| Section | Question range | Choices, in question-number order | Exam question PDF pages |
| --- | --- | --- | --- |
| Vocabulary | 1–10 | 1, 3, 4, 3, 1, 3, 2, 4, 2, 3 | 2 |
| Cloze | 11–15 | 4, 1, 3, 2, 4 | 3 (passage begins on 2) |
| Reading 1 | 16–20 | 3, 2, 4, 1, 2 | 3–4 |
| Reading 2 | 21–25 | 3, 2, 4, 3, 1 | 4–5 |
| Reading 3 | 26–30 | 1, 4, 4, 2, 3 | 5 |

## Review / publication gate

1. Independently re-read the **source images** against all 30 positions (ideally with a second reviewer or separate key-blind solving pass).
2. Verify the selected booklet is truly **C** for these exam pages and check whether a later/final key supersedes this **initial** key.
3. Record every disagreement and its source evidence; never rewrite the official source claim to agree with a model's guess.
4. Only after explicit review, create a separate versioned **verified** artifact; keep this raw curated transcription unchanged and traceable.
5. Reconciliation with structured questions (M2c) is a separate step and must not mutate the existing staged exam extraction.

## Next years

Repeat the **direct source reading + review + structured recording** process with each available exam and key. Do not impose a universal 25/30-question range. If a source file is inaccessible or an answer is illegible, mark it unresolved instead of guessing. Recorded absence of a key (1405) is not an AI-generated official key.

## Alignment semantics (M2c)

The `question_pdf_page` value denotes the page containing the **numbered question and its answer choices**, as printed in the exam. In the Cloze section, the passage and blanks 11–15 appear on PDF page **2**, while their numbered choice rows appear on PDF page **3**. The correspondence is source-specific, not a rule for other years. Reading Q20 is printed on page 4 but belongs to passage 1; Q25 is printed on page 5 but belongs to passage 2.

`english_exam.review_reconciliation.align_curated_official_claims` cross-checks the reviewed JSON against a separately validated staged exam. Callers must provide independently inspected expected key identity (filename, SHA-256, booklet, edition, key page and group). This function only returns **provisional, in-memory claim links** when every source and question relation agrees; it never changes `Question.answers`, generates final answers, or turns one AI transcription into an independent review. In a source-present environment the integration test additionally hashes `96.pdf` and `96_Key.pdf`.

## 1396 Vocabulary source-text correction proposals (M4a)

A separate data artifact, [`1396-vocabulary-correction-proposals.json`](1396-vocabulary-correction-proposals.json), proposes **11 small, visually supported edits** across Q1, Q3, Q4, Q5, Q9, and Q10. Q2, Q6, Q7, and Q8 have no proposed edits in this initial pass; **absence of a proposal does not certify an entire question is error-free**.

- Source: `source/96.pdf`, SHA-256 `69bc3434ae61c05c85bc9fabffd0b2ce13e5b39bc71b1dfd71c16709c9638ba2`, original PDF page 2, booklet C.
- Review: the assistant directly inspected the rendered source page and compared it with the native text layer. No OCR tool or general parser was newly developed for this editorial task.
- Examples: misrecognized letters (`mighl` -> `might`), a misplaced/ambiguous PDF text-layer token (`try 10 control` -> `try to control`), and printed number/choice markers. Both raw and proposed fragments are recorded, not a wholesale reconstruction of the source text.
- The artifact is **AWAITING_INDEPENDENT_REVIEW**, not a verified correction set. A successful code-level preview shows only exact substring alignment with the staged model; it does not independently establish that a visually read replacement is correct.
- `preview_editorial_corrections` is read-only, source-SHA-bound and fail-closed. It returns proposed full-field previews in memory, with no modification of `raw_text`, `normalized_text`, `corrected_text`, or question answers.
- The source-present integration test checks actual field-level fragments; the public CI source-independent test cannot perform that check because it intentionally excludes `source/` files.

**Review gate:** independently compare every proposal against printed page 2; record accept/reject/uncertainty with review evidence in a separate PR. Only accepted changes may later populate `corrected_text` in a versioned verified dataset. Check question-level option text and stem, not only listed OCR-like defects. Do not confuse this text editorial review with independent official-key verification.


## 1396 Cloze source-text review (M4b)

The compact [`1396-cloze-text-review.json`](1396-cloze-text-review.json) records **seven** directly visually supported editorial proposals for the printed Cloze section, plus **one unresolved nonlocal text-order anomaly**. The passage is on PDF page 2; its numbered choices (Q11–15) are on page 3.

- Same immutable `source/96.pdf` checksum as M4a. Proposals refer only to the relevant short source fragments: a Part B heading defect, passage words and blank marker, Q13 option-four spelling, and Q15 question-number marker.
- Actual printed pages were viewed directly. Source text-layer fragments were also inspected using the original PDF, **only to check evidence**, not to build a general-purpose extraction/OCR system. The extracted fragments occurred exactly once in their expected pages in this local inspection.
- The printed phrase `ability to remember` has a **displaced `to`** token in the PDF text layer (appearing as `10` near the end of the passage). This cannot be safely represented as an isolated simple replacement without checking the full staged field; it is explicitly **NEEDS_SOURCE_ALIGNED_REVIEW**, not an auto-correctable proposal.
- Status remains `PENDING_INDEPENDENT_REVIEW`: this assistant's visual reading is **not a separate human review**, and native text matches alone do not prove that a proposed reading is correct. Do not populate `corrected_text` or final verified answers on this evidence alone.
- Source-independent tests check the compact artifact's source ID, page/field references, review status, unique proposal IDs and unresolved classification. A source-conditional test checks actual raw fragments and source SHA when the original PDF is available; it skips on CI without PDF media.

M4a Vocabulary corrections have already been merged as **proposals**, not independently approved final corrections. Editorial approval and any verified dataset promotion remain separate future steps.
