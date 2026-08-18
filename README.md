# English Exam Dataset

This project is building an adaptive English-learning system from Iranian
Computer Engineering master's entrance exams.

## Current phase

The immediate goal is a trustworthy, reproducible dataset pipeline. Extraction,
normalization, correction, provenance tracking, and validation come before the
Android application.

## High-level architecture

The planned architecture keeps source ingestion and parsing, normalization,
validation, domain modeling, AI-assisted analysis, verified dataset releases,
and application logic as distinct concerns. Exam structure is data-driven, and
official, AI-generated, and final verified answers remain separate.

Original exam papers and answer keys live under `source/` as immutable local
input. These binary files are not currently committed to Git; a future
`source/README.md` may document their local organization without tracking the
materials themselves.

## Milestone 1: 1396 English extraction

The first importer deterministically extracts the English section from local
`source/96.pdf` pages 2–5. It preserves the imperfect source text layer and
page-relative provenance; it does not read the answer key or correct OCR-like
errors.

Install the locked Python 3.12 environment:

```bash
uv sync --locked --dev
```

Generate the local staged artifact:

```bash
uv run english-exam extract \
  --year 1396 \
  --source source/96.pdf \
  --output dataset/staged/1396.json
```

Use `--force` to replace an existing generated artifact. Full staged JSON is
ignored by Git; the tracked manifest records its expected hash and structure.

Run all tests, including the real-PDF integration test when local source
material is present:

```bash
uv run pytest
```
