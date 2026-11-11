# Assistant-only provisional correction workflow

**Owner decision: 2026-11-11.** Routine **per-item independent human review is no longer required** for developing the *provisional* Konkeroo dataset. This policy records a workflow choice, **not evidence that the assistant's readings are always correct**.

The owner previously compared all seven Cloze corrections and the eighth to/10 anomaly against the printed source, ran source-present tests, and found the word corrections correct. The owner now prefers to rely on the assistant's corrections rather than repeatedly checking every new proposed edit. This experience justifies changing the *amount of review effort*, but it does **not** establish an error rate or prove that the 75 remaining tasks are correct.

## Scope and evidence classes

| Work product | Allowed authority / usage | Prohibited inference |
| --- | --- | --- |
| **Immutable original** | SHA-256-bound original PDF or official key plus native text/geometry | A raw glyph proves how a word is printed |
| **Assistant-sourced local correction** | `ASSISTANT_PROVISIONAL` candidate, exact source anchor, page/field provenance, deterministic preview | `INDEPENDENT_HUMAN`, `ACCEPTED` human decision or `final_verified` |
| **Nonlocal/order anomaly** | Technical reconstruction with full before/after field and unique token accounting; otherwise `NEEDS_TECHNICAL_FOLLOWUP` | Automatically “RESOLVED” because the sentence sounds grammatical |
| **Source-printed oddity** | Keep the literal printed phrase, with a separate note if linguistically unexpected | Correcting source wording merely to make it idiomatic |
| **Initial official answer key** | `INITIAL_SOURCE_TRANSCRIPTION_UNVERIFIED` with row/booklet/edition provenance | Final key, verified answer, independently solved answer |
| **Existing human decisions** | Preserve the previous 19 owner-reported, revision-pinned decisions verbatim | Copying their human attestation onto different items or artifacts |

The 1396 independent-review docket remains a **historical and optional independent-review gate**. It currently has **19 human-recorded decisions and 75 pending human decisions**. Those 75 do **not** become `ACCEPTED`, `RESOLVED` or `TRANSCRIPTION_CONFIRMED` merely because the owner opted out of further manual checking.

## Active assistant-only development sequence

1. **Source lock.** Require the original immutable source filename/hash, exact 1-based PDF page and source field identity. Check text layer and, if needed, rendered page/word geometry. Label any visual interpretation as assistant-made.
2. **Exact local edit.** For each proposed replacement, assert one unique raw anchor in the correct field, enforce nonoverlapping edits, and preserve surrounding text. A failed anchor goes to `NEEDS_TECHNICAL_FOLLOWUP`, **never guessed substitution**.
3. **Order-sensitive anomalies.** Trace all source tokens and their geometry across the *complete field*, as for the 1396 Cloze to/10 case. Preserve uncertain portions, list blockers and do not promote an unresolved passage as wholly corrected.
4. **Reviewer-friendly local preview.** Generate `corrected_text` **candidates in a distinct provisional, versioned local artifact or in memory**. Keep original `raw_text` unchanged. Display-only blank markers (such as `(11) ____`) must not masquerade as printed glyphs.
5. **Mechanical checks.** Run source-independent unit/negative tests, source-present tests where the hashed PDF exists, exact diff and punctuation checks, deterministic regeneration and immutable-source checks. A CI skip due to absent local source **is not a passing source verification**.
6. **Traceability.** Record proposed before/after text, source identities, exact curated proposal revision, assistant-method attribution, automated test evidence, outstanding order/answer-key risks and status `ASSISTANT_PROVISIONAL`. Preserve evidence for later audits.
7. **No human queue requirement for development.** Work may proceed through Reading passages 1–3 and other source-supported text corrections without presenting each proposed line to the owner for acceptance. If a genuinely ambiguous source reading cannot be reconstructed, leave the **particular** item pending technical follow-up rather than asking the owner by default.

This procedure is **work to implement**, not a claim that every one of these checks has been coded for every year. Each scope-specific implementation PR must demonstrate what actually runs, and may initially cover only one passage.

## Official key and public-use boundary

Per-item human review is optional for the **provisional development lane**, but existing strong release gates are **not automatically waived**:

- Do not convert AI-proposed corrections to `INDEPENDENT_HUMAN` decisions or mark `independently_verified: true`.
- Do not set `Question.answers.final_verified`, infer a later **FINAL** key from an **INITIAL** key or pretend source-to-question alignment is independently confirmed.
- `publication_status: BLOCKED` stays unchanged, and no full staged/provisional passage, key answer sequence or source PDF is newly published through this policy.
- For learner-facing/public release, separately resolve original-source redistribution rights, complete field and question/choice consistency, answer-key edition and provenance, and all critical ambiguous anomalies. A future explicit release policy may allow a transparently labeled **unverified experimental dataset**, but this document does not authorize one.
- Prior PRs and the 19 owner-attested decisions remain intact; the human-review procedure in `REVIEW_PROTOCOL.md` is retained as an **optional independent audit method**.

## Reading 1396 next step

[Reading Issue #28](https://github.com/ehsanrs2/Konkeroo/issues/28) is repurposed from “collect 14 human decisions” to “build and test a source-aligned **assistant-only provisional preview** of Reading Passage 1”. The existing [Reading page-3 context handoff](review_batches/1396-reading-1.md) remains a useful source locator, **not a mandatory owner review form**.

For Reading Passage 1: apply 12 short proposals only when their raw source anchors match the exact field; preserve `format of the fixture` as printed; reconstruct Q19's nonlocal `as` ordering separately. Do **not** generate 14 fictitious human decisions. Continue with Reading 2 and Reading 3 under the same rules.

**Success for this new lane** means a reproducible, provenance-rich and visibly provisional correction preview, **not** an independently verified dataset or a bypassed release gate.
