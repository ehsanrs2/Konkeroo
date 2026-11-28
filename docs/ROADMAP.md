# Roadmap — dependency-driven, reviewable milestones

This is a *direction and execution order*, not a delivery-date commitment. Mark an item done only when its code, tests, review, and artifacts have been checked. For current code, GitHub `main` is the baseline; test-pass claims require test evidence.

| ID | Workstream | Status as of 2026-11-25 | Exit gate |
| --- | --- | --- | --- |
| M0 | Repo/bootstrap, safety rules, source preservation | **Implemented** | Versioned project and documented invariants |
| M1 | 1396 English paper import | **Implemented on main** | 30 validated questions; page provenance and non-text manifest |
| M2a | Answer-key foundation + 1395 native paired-grid import | **Importer on main; direct Q1–30 reading owner-confirmed (2026-11-25)** | Keep full staged key and match exam booklet/English section |
| M2b | 1396 direct-visual English key curation | **Existing curated key matches all 30 new owner-confirmed positions (2026-11-25); historical ledger unchanged** | Retain exact review evidence and initial-key authority |
| M2c | Provisional 1396 key-to-exam alignment | **Source-present original exam+key integration owner-reported PASS; PR #38 merged** | 30 initial-key structural joins with pinned revision, no answer promotion |
| M2d | Other native paired grids (1401, 1402, 1404) | **Generic family-wide strict table probe in PR #42; variant/edition attribution and real-media acceptance pending** | Reuse 1395 validated importer, safely inspect three other native grids together, retain exceptions |
| M2e | Broken-font paired grids (1397–1399) | **Family-wide Q1-anchored glyph candidate probe in PR #44; source-page reconciliation pending** | Repo-LFS pinned sources, collision/ambiguity rejection, no unverified final key |
| M2f | Rendered paired keys (1392–1394; includes JPG) | **3/3 original LFS objects confirmed locally (2026-11-25), but 0/4 pages yielded ruled-region/cell candidates; source-bound morphology profiling in progress** | Real-page layout diagnosis, visual cell mapping, edition attribution and evidence flags; no official-key pass |
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

## Active learning-knowledge sequence — M3/M4 checkpoint (2026-11-28)

The latest [M3/M4 handoff](M3_M4_HANDOFF.md) supersedes the older acquisition status and milestone numbering below. The historical M4a–M4f editorial tasks and M5–M9 product targets are retained for traceability, not treated as prerequisites to this pilot.

| ID | Status | Exit gate |
| --- | --- | --- |
| M3 | Content owner-confirmed locally: 430 questions, 1720 options, 62 passages, 15 attestations | Key alignment exceptions remain separate (260 candidates, 170 blocked); public release blocked |
| M4.1 | All 430 questions have local frozen first-pass hypotheses across 1391–1405 (409 selected, 21 abstentions) | Reproducible key-excluded packets, frozen independent-pass hypotheses |
| M4.2 | 430 local reconciliation records: 251 agreements, 2 disagreements, 7 aligned abstentions, 170 alignment-blocked; two separate provisional conflict reviews | Retain uncertainty, key provenance and conflicts; no automatic final answer |
| M4.3 | Private 1391–1405: all 430 questions have provisional Persian explanations; all four options analyzed for every 1393–1405 question, including abstentions and the two 1400 conflicts | Preserve evidence and caveats; no verified release |
| M4.4 | Private 1391–1405: 902 revision-scoped provisional concept records, 914 question links, all 430 questions covered | Source-linked, deduplicated educational concepts |
| M4.5 | Private 1391–1405: 902 learning units and feedback records; 797 private-practice eligible, 105 review-required; no learner release | Separate prompts and feedback, revision gates and self-assessment; no release or mastery claim |

Batch expansion (#67, #69, #71, #73, #75, #77, #79, #81): all 430 questions now have frozen first-pass records and provisional educational coverage (1391–1405). This is coverage completion, not final semantic approval. 170 key alignments remain blocked and two 1400 conflicts have separate unresolved provisional reviews. Quality records total one owner-confirmed printed defect, 59 suspected observations, and one packet limitation. See [all-question first-pass checkpoint](M4_ALL_SOLVED_1394_LEARNING.md), [1400–1401 learning checkpoint](M4_LEARNING_1400_1401.md) and [full educational coverage checkpoint](M4_LEARNING_COMPLETE.md). The initial [corpus audit and exact grouping checkpoint](M4_CORPUS_AUDIT.md) (#83) structurally checks all 430 explanations, 902 units and 914 anchors; 19 exact label/gloss groups map 902 original concept records to 878 provisional clusters, with 22 same-label groups requiring sense review. All 105 review-required units remain gated. Next: semantic review and sense-aware resolution, and synthetic-tested persistent learner events and spaced-repetition scheduling. Android and publication remain downstream of the data and release gates.

See [M4.5 learning units](M4_5_LEARNING_UNITS.md). See [M4 pilot protocol](M4_PILOT_PROTOCOL.md) and [Issue #59](https://github.com/ehsanrs2/Konkeroo/issues/59). Public release remains blocked by D-010. No final verified answers or production database integration are claimed. Acquisition details below are historical.

## Historical direct-curation sequence (owner decision 2026-11-25)

1. Obtain remaining original keys and exam papers by upload, directly read their source claims and preserve unknown/ambiguous entries. Do not expand OCR or geometry tooling merely to acquire this finite corpus.
2. Review answer positions in compact batches, record explicit owner confirmation bound to the exact artifact digest, and preserve local JSON/SQLite staging. Only metadata manifests enter public GitHub pending D-010.
3. Match source booklet/edition and printed question numbers against actual exam questions before attaching answers; do not infer English ranges. Keep independent AI solutions and final answer authority distinct.
4. Proceed toward the core learning application as the curated corpus becomes usable. Existing family probes are optional diagnostics, not the critical path. See D-014 and [Issue #57](https://github.com/ehsanrs2/Konkeroo/issues/57).

The 1392–1394 batch records confirmed readings, not aligned or final verified keys. Original PDFs for 1392 and 1393 match repository LFS pins; the 1394 upload is a WebP derivative with unknown booklet/edition and unverified repository identity. The old ruled-grid detector found zero candidates on four actual pages, so the optional profiler PR #56 is not a dependency.

The second owner-confirmed batch (1395–1399) adds 150 printed positions with zero corrections. All five PDFs match repository SHA pins; 1399 exam code is unprinted and the single uploaded page has a 1/2 footer, but Q1–30 are present. Cumulative local staging: 240 positions, eight years, two review batches. See [second manifest](../dataset/staged/1395-1399-direct-key-review.manifest.json). The third batch adds 210 selected positions from 1391 A and 1400–1405. B/C/D (90 positions) are excluded by owner. All 15 years now have confirmed readings (450 active positions; three review batches). 1405 is a third-party MasterTest image, not an official repository key. The 1391 exam 510A (code 1277) matches booklet A and English Q1–30 (PDF pp. 2–7); other new alignments remain pending. See [third manifest](../dataset/staged/1391-1400-1405-direct-key-review.manifest.json). Next: direct exam content curation, beginning with 1391 A. New exam alignment and final verification remain separate.

## Historical sequence — batch-first (owner decision 2026-11-14; superseded for acquisition priority)

1. **Start with a single corpus-wide inventory.** Use `uv run --dev python -m english_exam.batch_inventory --source-dir source` and keep its `SOURCES_INCOMPLETE` / pointer / missing / mismatch statuses explicit. This operation is read-only; it is **not** full-year import or semantic answer checking.
2. **Implement representative technical source families in batches.** First, [native paired family probe](NATIVE_PAIRED_FAMILY.md) (PR #42) reuses the 1395 validated importer and scans 1401/02/04 in a single run, without inventing variant/edition attribution. Then use the [broken-font glyph family probe](BROKEN_FONT_FAMILY.md) (PR #44) for 1397–99 (unique source glyphs only, multi-page still partial), followed by 1392–94 rendered-media triage (not visual key decoding), 1391 legacy, and 1400/1403 personalized families. Source-specific question ranges, booklets, editions and candidate/official columns remain required; do not build an unsafe one-size-fits-all key importer.
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
