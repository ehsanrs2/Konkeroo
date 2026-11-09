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
