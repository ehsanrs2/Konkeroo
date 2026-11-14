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

## Batch-first cross-year direction — owner decision 2026-11-14

**Supersedes the former operational emphasis on 1396 passage-by-passage review.** The owner requested that subsequent years and the remaining work be handled by the assistant rather than requiring yearly suspicious-item checks or human acceptance calls. **Assistant-led assessment is the development standard for provisional content**; it is not independent factual proof that every glyph or keyed answer is correct.

- Work in **source-family batches**, not by issuing a new human acceptance process or a custom validation PR for each individual year. Share one extraction/checking strategy for representative key-layout families while preserving different booklet/range/edition semantics.
- Run `python -m english_exam.batch_inventory --source-dir source` to classify the complete **1391–1405** set in one read-only pass; it differentiates actual PDF/JPEG bytes from pointer-only Git LFS files, missing media, known hash mismatches, and the **recorded absence of an official 1405 key**. See [batch workflow](BATCH_FIRST_MULTYEAR.md) and [Issue #39](https://github.com/ehsanrs2/Konkeroo/issues/39).
- For supported representative families, produce **local-only, assistant-attributed provisional candidates** in batches. Use programmatic quality gates and isolate failed/ambiguous individual items as **exceptions**. Other independent cases may continue without waiting for annual owner signoff. Do not substitute stylistic grammar guesses for original source words.
- A successful source-present test, a source-independent test, a skipped test, a model visual reading, and an independent human audit are **five different evidence types**. A mechanical check proves only what it exercised; aggregate throughput is not a measured accuracy claim.
- Request owner action only for true external decisions, e.g. **rights/public redistribution (D-010)** or changing the authority for a learner-facing answer release. Do not repeatedly request that the owner inspect each year for ordinary provisional development.

The earlier [1396 Reading-1](review_batches/1396-reading-1.md), Reading-2 and Reading-3 slices are **historical completed/merged engineering examples**. The 1396 original-PDF integration for Reading-2 and Reading-3 and the INITIAL-key structural link passed locally as reported by the maintainer; those results do not automatically transfer to other years.

**Status of the first batch implementation:** the source inventory command only classifies *media readiness*. It does **not yet import, solve or source-validate the other fourteen English exam years**. Family-oriented extraction and per-item exception reports are separate implementations. The historical 19 human decisions, the 75 pending independent-review items, unreleased answers, unresolved final-key authority and `publication_status: BLOCKED` remain unchanged.
