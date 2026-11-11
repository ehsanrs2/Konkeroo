# Roadmap — dependency-driven, reviewable milestones

This is a *direction and execution order*, not a delivery-date commitment. Mark an item done only when its code, tests, review, and artifacts have been checked. For current code, GitHub `main` is the baseline; test-pass claims require test evidence.

| ID | Workstream | Status as of 2026-11-10 | Exit gate |
| --- | --- | --- | --- |
| M0 | Repo/bootstrap, safety rules, source preservation | **Implemented** | Versioned project and documented invariants |
| M1 | 1396 English paper import | **Implemented on main** | 30 validated questions; page provenance and non-text manifest |
| M2a | Answer-key foundation + 1395 native paired-grid import | **Implemented on main** | Separate staged key, 121 booklet-A entries, deterministic manifest |
| M2b | 1396 direct-visual English key curation | **Curated on main; independent review pending** | Source-linked Q1–30 official claims, explicit uncertainty, testable data file |
| M2c | Provisional 1396 key-to-exam alignment | **Merged on main; real-source integration pending** | Strict source, booklet, section, passage, choice and printed-question-page checks; no answer promotion |
| M2d | Other native paired grids (1401, 1402, 1404) | **Not started** | Fixture-safe import and regression checks |
| M2e | Broken-font paired grids (1397–1399) | **Not started** | Validated glyph map or cell OCR, no silent guessing |
| M2f | Rendered paired keys (1392–1394; includes JPG) | **Not started** | Reviewed structural/visual goldens and confidence thresholds |
| M2g | 1391 four-booklet legacy grid | **Not started** | Variant-safe cross-page join; multiple accepted positions |
| M2h | Personalized report keys (1403 native, 1400 raster) | **Not started** | Key vs candidate columns separated; deletion/positive-effect preserved |
| M2i | Corpus completeness + 1405 no-key status | **Not started** | Explicit coverage/unsupported/absent matrix |
| M3 | Exam-paper English-section import across remaining years | **Not started** | Verified year-specific section/range/passages; no global 25/30 assumption |
| M4 | Provisional assistant corrections, optional independent review and release gate | **In progress; owner opted out of routine per-item human checks (2026-11-11)** | Source-anchored provisional text, explicit uncertainty, separate release gate |
| M4a | 1396 Vocabulary Q1–10 source-backed editorial proposals | **11 human ACCEPTED decisions recorded (PR #19)** | Owner-reported findings; raw stage unmodified, no final dataset promotion |
| M4b | 1396 Cloze passage and Q11–15 source editorial review | **Merged on main; independent approval pending** | Seven short correction proposals and one unresolved text-order defect |
| M4c | 1396 Reading passages 1–3 and Q16–30 assistant-source provisional review | **Proposals merged; assistant-only source-aligned preview next** | 36 short proposals, 5 anomalies, 4 printed oddities; no fabricated human attestations |
| M4d | 1396 independent-review docket and educational release gate | **Merged; 19 reviewed, 75 pending; release blocked** | 94 source-linked tasks and evidence-bearing decisions |
| M4e | Bind human review evidence to exact artifact revisions | **Merged in PR #17** | Git blob revision pins, stale-approval rejection, Vocabulary handoff |
| M4f | Independent Cloze human review (1396 Q11–15) | **8/8 Cloze decisions recorded; PR #27 merged** | 7 edits + 1 token-order anomaly, original PDF pages 2–3 |
| M5 | Independent AI answering, explanations, and conflict review | **Not started** | Separate official/AI/final; provenance and error analysis |
| M6 | Vocabulary/skill enrichment, cloze/reading practice model | **Not started** | Context-aware word frequency/importance and reviewed skill tags |
| M7 | Android MVP with offline verified dataset | **Not started** | Functional retrieval practice, accessibility, safe local persistence |
| M8 | Adaptive scheduling, analytics and motivation | **Not started** | Retention, calibration, interleaving, meaningful streaks and goals |
| M9 | Learning-outcome evaluation and publication readiness | **Not started** | Held-out evaluation, privacy/copyright review and documented limitations |

Dependencies may be interleaved: additional exam parsers (M3) are needed before matching keys of those years to English sections. M2b does not require solving all other years first. M4–M9 are product targets, not claims about present functionality.

## Recommended immediate sequence

1. Review `main` status and the latest M2a implementation; verify tests in a reproducible environment, including clean CI without proprietary/local fixtures.
2. Close the open **source distribution / public Git LFS** decision before treating the repository as publication-ready.
3. Complete **M2b** by independent review of the 1396 English source-linked visual transcription and its exact 30 question/choice matches; no OCR or generic key parser required for one-time data acquisition.
4. Review M2b's curated data, independent cross-checks, source provenance, unit tests, and legal exposure. Merge only through a small PR.
5. M2c audit-only alignment is merged. Run its source-present integration test locally and retain its provisional status until independent answer/edition review.
6. Review the first **M4a** 1396 Vocabulary Q1–10 text correction proposals against page 2; accept/reject each through an explicit later review step, without changing raw staging.
7. Review **M4b Cloze** against printed pages 2–3: seven short proposed edits and the unresolved displaced `to` text-order issue. Do not apply automatic replacements or call this independent verification.
8. Review **M4c Reading passages 1–3** as a source-linked, read-only editorial proposal set; independently verify anomalous layout/order and preserve printed peculiarities verbatim.
9. M4d/M4e and Cloze decision PR #27 are merged: 94 tasks have pinned source revisions, 19 owner-reported decisions are recorded (11 Vocabulary + 8 Cloze) and 75 tasks remain pending; publication stays blocked.
10. Cloze [Issue #20](https://github.com/ehsanrs2/Konkeroo/issues/20) is complete. The owner opted out of per-item human reviews for *provisional development* on 2026-11-11. Implement the [assistant-only provisional policy](ASSISTANT_ONLY_PROVISIONAL.md) for [Reading Passage 1](review_batches/1396-reading-1.md), [Issue #28](https://github.com/ehsanrs2/Konkeroo/issues/28): 12 source-anchored edits, Q19 order diagnosis and preserving printed `fixture`. Proceed across the remaining Reading passages only with technical source evidence; keep the initial key explicitly unverified. Do not fill the human ledger with assistant-made decisions, promote final answers, or unblock publication.
11. Expand exam/key data to additional years through small data-first review batches.

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
