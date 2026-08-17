# Repository Guidelines

## Project Purpose

This repository contains the source material and data-processing pipeline for
an adaptive English-learning system based on Iranian Computer Engineering
master's entrance exams.

The project will eventually include:

- source exam papers and official answer keys
- deterministic PDF/image extraction
- OCR-quality detection and correction workflows
- answer-key normalization
- structured exam datasets
- validation tools
- AI-assisted analysis
- learning-domain logic
- an Android application

Work incrementally. The current priority is building a trustworthy exam dataset
before implementing the Android application.

## Current Phase and Architecture

The project is currently in the dataset-pipeline phase. Build and validate the
exam dataset before starting Android implementation.

Keep these responsibilities separated as the codebase grows:

* source ingestion and parsing
* normalization and correction
* validation
* domain modeling
* AI-assisted analysis

Data should flow from immutable local source material through reproducible
staging and validation steps into verified datasets. Application code should
consume verified data rather than depend directly on source-document parsing.

---

## Repository Structure

Expected top-level layout:

```text
English/
├── AGENTS.md
├── README.md
├── pyproject.toml
├── source/
├── src/
│   └── english_exam/
├── dataset/
│   ├── staged/
│   ├── verified/
│   └── releases/
├── tests/
└── docs/
```

Do not create additional top-level directories without a clear architectural
reason.

---

## Source Material Is Immutable

Everything under `source/` is original source material.

Never:

* modify a source file
* overwrite a source file
* rename a source file
* recompress or crop a source PDF/image
* replace a source file with a corrected version
* silently normalize filenames inside `source/`

Read source files as-is.

Any normalized naming or metadata must be represented outside `source/`.

The existing source filenames are intentionally treated as external input and
may be inconsistent, for example:

* `96_Key.pdf`
* `92_key.pdf`
* `94-key.jpg`
* `1404-key.pdf`

Importer code must tolerate such variation.

---

## Preserve Provenance

Every extracted piece of content must retain enough provenance to trace it back
to the original document.

Where feasible preserve:

* source filename
* PDF page number
* page-relative bounding box
* extraction method
* raw extracted text

Never replace raw extracted text with corrected text.

Store corrected or normalized forms separately.

---

## Raw Data vs Corrected Data

Source-derived text and corrected text are different concepts.

Prefer models such as:

* `raw_text`
* `normalized_text`
* `corrected_text`

Do not silently fix OCR errors.

Every correction must be attributable to a processing stage.

Generated records should move through explicit states such as:

```text
RAW
STAGED
AI_CORRECTED
VERIFIED
```

Only validated content may enter `dataset/verified/`.

---

## Exam Structure Must Be Data-Driven

Do not assume that every exam has the same number of English questions.

Do not globally hard-code assumptions such as:

* English always has 25 questions
* English always has 30 questions
* Vocabulary always contains 10 questions
* Reading always contains exactly 3 passages

Year-specific expectations may be used in fixtures and validation rules, but
the domain model must support variation between exams.

Sections should be modeled explicitly, for example:

* VOCABULARY
* CLOZE
* READING

---

## Domain Modeling

Keep domain models independent from PDF parsing implementation.

Important concepts must remain distinct.

Examples:

* Exam
* Section
* Passage
* Question
* Choice
* AnswerRecord
* SourceProvenance

Do not collapse official, AI-generated, and verified answers into one field.

At minimum distinguish:

* official answer
* AI answer
* final verified answer
* accepted answers
* answer status
* confidence where applicable

The model must support multiple accepted answers.

---

## PDF and Image Extraction

Prefer layout-aware extraction over flattened page text.

The PDFs may contain:

* usable text layers
* incorrect OCR text
* incorrect reading order
* image-only pages
* mixed Persian and English content
* tables
* answer keys represented only visually

Do not assume that successful text extraction means the extracted text is
correct.

Use text coordinates and page layout when they materially improve extraction.

Avoid running OCR over an entire document unnecessarily when a usable text
layer already exists.

Visual/image-based extraction may be used where text extraction is unavailable
or structurally unreliable.

---

## Answer Keys

Answer-key formats vary across years.

Importers must eventually support:

* text PDFs
* scanned/image PDFs
* JPG files
* Persian digits
* Arabic-Indic digits
* Latin digits
* multiple table layouts
* special scoring annotations
* multiple accepted answers

Normalize these representations into one internal domain model.

Never treat a parsed answer key as trustworthy merely because parsing
succeeded.

---

## AI Usage

Do not call an external AI API unless the task explicitly requests it.

Deterministic parsing, normalization, and validation should be preferred where
possible.

When AI analysis is introduced:

* AI should solve questions independently before seeing the official key when
  answer verification is the goal.
* AI output must not overwrite official source data.
* disagreements between AI and official keys must be preserved and flagged.
* structured output is preferred over free-form prose.
* AI-only answers must be distinguishable from official answers.

---

## Validation

Dataset correctness is more important than extraction coverage.

Implement validation for assumptions such as:

* missing question numbers
* duplicate question numbers
* missing choices
* unexpected choice counts
* missing passages
* broken passage/question relationships
* suspicious OCR
* answer-key mismatches
* source provenance gaps

Validation failures must be visible. Do not silently discard malformed data.

---

## Tests

Every parser or normalization behavior should have automated tests.

Prefer tests based on small fixtures derived from real exam structures.

For known exam fixtures, explicit year-specific expectations are acceptable.

Run the relevant test suite before declaring a task complete.

Do not weaken tests merely to make a failing implementation pass.

---

## Generated Data

Do not commit generated files into `source/`.

Use:

* `dataset/staged/` for machine-generated intermediate results
* `dataset/verified/` for validated records
* `dataset/releases/` for explicitly prepared dataset releases

Generated files must be reproducible whenever practical.

---

## Development Workflow

Prefer small, reviewable changes.

For substantial work:

1. inspect the relevant source files
2. understand the existing code
3. state or confirm the intended approach
4. implement the smallest coherent change
5. add or update tests
6. run validation/tests
7. summarize what changed and any unresolved issues

Do not implement unrelated future features in the same task.

In particular, do not start Android UI work while the current task concerns
dataset extraction unless explicitly requested.

---

## Coding Style

Use clear domain-oriented names.

Prefer explicit models and typed interfaces over loosely structured dictionaries
when the structure is stable.

Keep parsing, normalization, validation, and domain modeling separate where
practical.

Avoid premature abstractions for hypothetical future formats, but do not encode
known year-specific quirks as global assumptions.

---

## Git

Keep commits focused and reviewable.

Use concise imperative commit messages, for example:

* `Bootstrap exam extraction pipeline`
* `Add 1396 English section parser`
* `Add answer-key normalization model`
* `Validate question choice counts`

Never commit sensitive data, credentials, API keys, local environment files, or
unreviewed generated artifacts.
