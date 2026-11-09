# Roadmap — dependency-driven, reviewable milestones

This is a *direction and execution order*, not a delivery-date commitment. Mark an item done only when its code, tests, review, and artifacts have been checked. For current code, GitHub `main` is the baseline; test-pass claims require test evidence.

| ID | Workstream | Status as of 2026-11-09 | Exit gate |
| --- | --- | --- | --- |
| M0 | Repo/bootstrap, safety rules, source preservation | **Implemented** | Versioned project and documented invariants |
| M1 | 1396 English paper import | **Implemented on main** | 30 validated questions; page provenance and non-text manifest |
| M2a | Answer-key foundation + 1395 native paired-grid import | **Implemented on main** | Separate staged key, 121 booklet-A entries, deterministic manifest |
| M2b | 1396 visual/vector key import | **Next candidate** | Region-level recognition, uncertainty gating, special annotation preserved |
| M2c | First exam/key reconciliation for verified 1396 English section | **Not started** | Attach official entries only to 1396 English Q1–30; detect mismatch |
| M2d | Other native paired grids (1401, 1402, 1404) | **Not started** | Fixture-safe import and regression checks |
| M2e | Broken-font paired grids (1397–1399) | **Not started** | Validated glyph map or cell OCR, no silent guessing |
| M2f | Rendered paired keys (1392–1394; includes JPG) | **Not started** | Reviewed structural/visual goldens and confidence thresholds |
| M2g | 1391 four-booklet legacy grid | **Not started** | Variant-safe cross-page join; multiple accepted positions |
| M2h | Personalized report keys (1403 native, 1400 raster) | **Not started** | Key vs candidate columns separated; deletion/positive-effect preserved |
| M2i | Corpus completeness + 1405 no-key status | **Not started** | Explicit coverage/unsupported/absent matrix |
| M3 | Exam-paper English-section import across remaining years | **Not started** | Verified year-specific section/range/passages; no global 25/30 assumption |
| M4 | Human review, corrections, verified dataset and release gate | **Not started** | Auditable corrections, uncertainty resolution, schema/version governance |
| M5 | Independent AI answering, explanations, and conflict review | **Not started** | Separate official/AI/final; provenance and error analysis |
| M6 | Vocabulary/skill enrichment, cloze/reading practice model | **Not started** | Context-aware word frequency/importance and reviewed skill tags |
| M7 | Android MVP with offline verified dataset | **Not started** | Functional retrieval practice, accessibility, safe local persistence |
| M8 | Adaptive scheduling, analytics and motivation | **Not started** | Retention, calibration, interleaving, meaningful streaks and goals |
| M9 | Learning-outcome evaluation and publication readiness | **Not started** | Held-out evaluation, privacy/copyright review and documented limitations |

Dependencies may be interleaved: additional exam parsers (M3) are needed before matching keys of those years to English sections. M2b does not require solving all other years first. M4–M9 are product targets, not claims about present functionality.

## Recommended immediate sequence

1. Review `main` status and the latest M2a implementation; verify tests in a reproducible environment, including clean CI without proprietary/local fixtures.
2. Close the open **source distribution / public Git LFS** decision before treating the repository as publication-ready.
3. Implement **M2b only** in a feature branch: the SHA-verified 1396 vector-key layout, region-level extraction/recognition, uncertainty and special annotation handling; no AI or other years.
4. Review M2b content, manifests, regression tests, raw/visual provenance, and legal exposure. Merge only through a small PR.
5. Implement M2c reconciliation as a **separate PR** after importer validation.
6. Expand across audited families and remaining exam papers in narrow representative increments.

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
