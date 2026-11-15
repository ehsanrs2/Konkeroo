# Roadmap — dependency-driven, reviewable milestones

This is a *direction and execution order*, not a delivery-date commitment. Mark an item done only when its code, tests, review, and artifacts have been checked. For current code, GitHub `main` is the baseline; test-pass claims require test evidence.

| ID | Workstream | Status as of 2026-11-14 | Exit gate |
| --- | --- | --- | --- |
| M0 | Repo/bootstrap, safety rules, source preservation | **Implemented** | Versioned project and documented invariants |
| M1 | 1396 English paper import | **Implemented on main** | 30 validated questions; page provenance and non-text manifest |
| M2a | Answer-key foundation + 1395 native paired-grid import | **Implemented on main** | Separate staged key, 121 booklet-A entries, deterministic manifest |
| M2b | 1396 direct-visual English key curation | **Curated on main; independent review pending** | Source-linked Q1–30 official claims, explicit uncertainty, testable data file |
| M2c | Provisional 1396 key-to-exam alignment | **Source-present original exam+key integration owner-reported PASS; PR #38 merged** | 30 initial-key structural joins with pinned revision, no answer promotion |
| M2d | Other native paired grids (1401, 1402, 1404) | **Family-batch processing pending** | Reuse native grid representation, fixture-specific dimensions, exception-only review |
| M2e | Broken-font paired grids (1397–1399) | **Family-batch processing pending** | Source-aligned glyph evidence and isolated ambiguous-row exceptions |
| M2f | Rendered paired keys (1392–1394; includes JPG) | **Family-batch processing pending** | Visual table/row mapping, source-specific media identity and confidence flags |
| M2g | 1391 four-booklet legacy grid | **Not started** | Variant-safe cross-page join; multiple accepted positions |
| M2h | Personalized report keys (1403 native, 1400 raster) | **Not started** | Key vs candidate columns separated; deletion/positive-effect preserved |
| M2i | Corpus completeness + 1405 no-key status | **Not started** | Explicit coverage/unsupported/absent matrix |
| M3 | Exam-paper English-section import across remaining years | **Batch triage started; full multi-year import not implemented** | Shared processing per source family with per-item exception log, not annual human signoff |
| M4 | Provisional assistant corrections, optional independent review and release gate | **In progress; owner opted out of routine per-item human checks (2026-11-11)** | Source-anchored provisional text, explicit uncertainty, separate release gate |
| M4a | 1396 Vocabulary Q1–10 source-backed editorial proposals | **11 human ACCEPTED decisions recorded (PR #19)** | Owner-reported findings; raw stage unmodified, no final dataset promotion |
| M4b | 1396 Cloze passage and Q11–15 source editorial review | **Merged on main; independent approval pending** | Seven short correction proposals and one unresolved text-order defect |
| M4c | 1396 Reading passages 1–3 and Q16–30 assistant-source provisional review | **Three in-memory previews merged (PR #31/#33/#36); owner-reported real-PDF Passage 2/3 tests passed** | 36 short proposals, 5 anomaly diagnostics, 4 printed oddities; no independent-human attestations or release |
| M4d | 1396 independent-review docket and educational release gate | **Merged; 19 reviewed, 75 pending; release blocked** | 94 source-linked tasks and evidence-bearing decisions |
| M4e | Bind human review evidence to exact artifact revisions | **Merged in PR #17** | Git blob revision pins, stale-approval rejection, Vocabulary handoff |
| M4f | Independent Cloze human review (1396 Q11–15) | **8/8 Cloze decisions recorded; PR #27 merged** | 7 edits + 1 token-order anomaly, original PDF pages 2–3 |
| M5 | Independent AI answering, explanations, and conflict review | **Not started** | Separate official/AI/final; provenance and error analysis |
| M6 | Vocabulary/skill enrichment, cloze/reading practice model | **Not started** | Context-aware word frequency/importance and reviewed skill tags |
| M7 | Android MVP with offline verified dataset | **Not started** | Functional retrieval practice, accessibility, safe local persistence |
| M8 | Adaptive scheduling, analytics and motivation | **Not started** | Retention, calibration, interleaving, meaningful streaks and goals |
| M9 | Learning-outcome evaluation and publication readiness | **Not started** | Held-out evaluation, privacy/copyright review and documented limitations |

Dependencies may be interleaved: additional exam parsers (M3) are needed before matching keys of those years to English sections. M2b does not require solving all other years first. M4–M9 are product targets, not claims about present functionality.

## Recommended immediate sequence — batch-first (owner decision 2026-11-14)

1. **Start with a single corpus-wide inventory.** Use `uv run --dev python -m english_exam.batch_inventory --source-dir source` and keep its `SOURCES_INCOMPLETE` / pointer / missing / mismatch statuses explicit. This operation is read-only; it is **not** full-year import or semantic answer checking.
2. **Implement representative technical source families in batches**, reusing 1395 native paired grids and 1396 provisional exam/key examples where suitable. Group 1391 legacy, 1392–94 rendered, 1397–99 broken-font, 1400/1403 personalized, 1401/02/04 native. Source-specific question ranges, booklets and editions remain required; do not build an unsafe one-size-fits-all key importer.
3. **Let assistant-led provisional quality checks carry development forward** without annual owner signoff queues. Record source hashes, structure checks, method attribution and localized exception classifications. Keep question text and answers private/local; publish at most non-content manifests until rights and answer authority are settled.
4. **Advance app-learning architecture and independent AI solving after source-family coverage**, while maintaining separate `INITIAL` source claims, optional audit and `final_verified` authority. The 1396 initial-key test passed locally after PR #38. Source redistribution decision D-010 and final release remain explicitly open, and cannot be cleared by model confidence alone.

Batch workflow details: [BATCH_FIRST_MULTYEAR.md](BATCH_FIRST_MULTYEAR.md), tracking [Issue #39](https://github.com/ehsanrs2/Konkeroo/issues/39). No further requirement to request the owner's approval for each year merely to proceed with *provisional* extraction or corrections.

## Definition of Done for every parser milestone

- Source identified by explicit catalog/year fixture and expected checksum; no modification of original material.
- Correct counts, choice positions, sections/variants, passage associations, and source/page geometry for the **actual** fixture.
- Unexpected/ambiguous source tokens or cells surfaced as warnings/errors rather than corrected invisibly.
- Synthetic/source-independent tests plus source-conditional real integration tests; missing local source skips only source-specific tests.
- Deterministic output (byte identity), verified manifest, and no full generated dataset committed.
- `uv lock --check`, `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, and `git diff --check` pass.
- Scope-limited PR reviewed; design/decision/status docs updated when a contract changes.
- No source media or data-publication policy changes made implicitly.

## Parking lot / explicitly open

- LFS/public redistribution rights and whether to keep binary exam media in this public repository.
- Verified-vs-initial key precedence, special scoring semantics, and official source hierarchy.
- 1397–1399 glyph mapping reliability vs cell OCR.
- English ranges/booklet variants for unparsed exam years.
- Human review UI and a validated feedback rubric.
- Android persistence, privacy policy, telemetry opt-in, and scientifically credible learning evaluation.

Use GitHub Issues for scoped work and PRs for evidence; this file preserves the cross-cutting sequence.
