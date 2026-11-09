# System architecture

**Status:** dataset infrastructure implemented for two fixtures; remaining layers are planned. Distinguish `Implemented`, `Planned`, and `Decision pending` below.

## Logical data flow

```text
Immutable source media (PDF/JPG) + explicit catalog / source hash
                |
       page/media adapters and layout-aware readers
                |
      +---------+----------+
      |                    |
Exam/English importer   Official-key importer (separate pipeline)
      |                    |
Raw staged exam         Raw staged answer-key dataset, variants, editions
      |                    |
Schema, source, geometry, completeness and anomaly validation
      |                    |
Corrections/review      Normalize dispositions and accepted positions
      |                    |
      +--- verified exam identity / booklet / English sections ---+
                          |
               reconciliation (NOT IMPLEMENTED)
                          |
     Official claim  |  independent AI claim (future)  |  verified decision
                          |
              reviewable versioned dataset (future)
                          |
       content/skill index and Android learning runtime (future)
                          |
         spaced repetition, analytics, motivation (future)
```

Source extraction and official-key extraction are deliberately independent. In particular, an answer-key importer must not guess which rows are English until exam-section metadata is verified.

## Implemented Python layout

- `src/english_exam/domain.py`: frozen exam/question/section/passage/choice models, raw/normalized/corrected text, source provenance, and distinct `AnswerSet.official`, `.ai`, `.final_verified`.
- `src/english_exam/pdf_layout.py`: layout-aware pdfplumber geometry and character-aligned extraction.
- `src/english_exam/importers/exam_1396.py`: fixture-specific English-section parser.
- `src/english_exam/pipeline.py`, `validation.py`, `serialization.py`: exam staging, guards, deterministic writing.
- `src/english_exam/answer_keys/`: source catalog, digit normalization, answer-key staging/domain, native paired-grid reader, 1395 importer, validation, and pipeline.
- `src/english_exam/cli.py`: separate `extract` and `key extract` commands.
- `tests/`: sanitized unit tests and source-conditional integration tests; manifests under `dataset/staged/` contain non-text regressions.

Current known fixtures:

- **1396 exam:** `source/96.pdf`, English PDF pages 2–5, 30 questions; Vocabulary 1–10, Cloze 11–15, Reading 16–30. Reading passage mapping: 16–20, 21–25, 26–30, including cross-page boundary cases. These are **fixture-level**, never global rules.
- **1395 key:** `source/95_Key.pdf`, one native-text page, booklet A, 121 official-key entries, ordinary answers, no English range inferred. Initial key edition preserved.
- **No 1396 key parser or reconciliation is currently implemented.**

## Data contracts and boundaries

**Exam staging:** sections and questions are source-derived. Preserve `raw_text` exactly; `normalized_text` and `corrected_text` are separate, opt-in transformations. Choices have positions and raw markers. Passages contain linked questions. Layout provenance uses source filename, 1-based page, tight bounding box, source fragment, and method. Never infer universal question counts.

**Answer-key staging:** `AnswerKeyDataset` has an explicit source descriptor and variants/booklets. Each `AnswerKeyEntry` retains raw number/answer values and provenance independently from canonical accepted-choice positions, disposition, and annotations. Source-native and visual-derived provenance must not be confused. `INITIAL` does not mean `FINAL`. No candidate response in personalized reports may be mistaken for an official answer.

**Reconciliation (planned):** join only after verified exam metadata identifies the English question IDs, year, and booklet variant; validate completeness and valid choice ranges. Keep all source-key rows in separate staging, including non-English material. Never write an official key directly into raw exam extraction.

**AI-assisted analysis (planned):** generate independent answer hypotheses without exposing the official key first; store model/version, evidence, uncertainty, and disagreements separately. Verified resolutions require an explicit review path; do not overwrite official records.

**Dataset publication (planned):** represent release schema, provenance, source hashes, correction history, review status, and license decision. `STAGED`, `VERIFIED`, and release status must not be silently conflated. Full generated exam/key JSON currently remains local and ignored.

## Future service/app boundaries (not implemented)

- **Content/review tools:** human-assisted correction of OCR and ambiguous answer-key cells; maintain raw evidence, alternatives, reviewer notes, and audit trail.
- **Language enrichment:** stem/choice/passage vocabulary occurrences, lemma/word family, context, skill tags, graded explanations, difficulty/priority scores, and provenance to source occurrences. Never count words from stem alone.
- **Learning engine:** active recall, interval scheduling, interleaving, adaptive item selection, misconception patterns; prevent repetition leakage in held-out evaluation.
- **Analytics:** retention, delayed recall, accuracy, time, confidence calibration, mastery by skill, error taxonomy, unseen-question transfer.
- **Motivation:** effort/quality-aware streaks, daily quests, achievements; avoid gaming through low-value actions.
- **Android:** Kotlin + Jetpack Compose + Room is the preferred *target stack*, not a current implementation commitment. Prefer offline-first verified content with migration/versioning and privacy controls. Define APIs and storage once the dataset contract stabilizes.

## Engineering constraints

- Python 3.12, `uv.lock`, `pdfplumber` with permissive licensing; avoid PyMuPDF AGPL/commercial requirements without explicit license review.
- No native text flattening as the source of truth for table/reading order.
- Prefer geometric cell extraction, then narrow OCR only where native text is absent/unusable; surface low-confidence or exceptional cells.
- SHA-bound fixtures; deterministic serialization; non-text manifests; validation before output; no writes into `source/`.
- Failure must be explicit: unexpected cells, duplicate numbers, misleading provenance, unsupported sources, incomplete question-key mapping, or uncertainty.
- Keep generic invariants shared; layout/range/quirk assumptions in fixture adapters and fixture validators.

See [Corpus audit](ANSWER_KEY_CORPUS.md), [Decision log](DECISIONS.md), and [Roadmap](ROADMAP.md).
