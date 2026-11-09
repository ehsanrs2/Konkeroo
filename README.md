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

Install the locked Python 3.12 environment:

```bash
uv sync --locked --dev
```

## Milestone 1: 1396 English extraction

The first importer deterministically extracts the English section from local
`source/96.pdf` pages 2–5. It preserves the imperfect source text layer and
page-relative provenance; it does not read the answer key or correct OCR-like
errors.

Generate the local staged exam artifact:

```bash
uv run english-exam extract \
  --year 1396 \
  --source source/96.pdf \
  --output dataset/staged/1396.json
```

## 1395 native answer-key staging

The first answer-key importer independently stages the official initial key
from local `source/95_Key.pdf`. It extracts its native paired grid using PDF
geometry and does not infer which questions belong to English. It does not
modify or reconcile any staged exam artifact.

Generate the local staged key artifact:

```bash
uv run english-exam key extract \
  --exam-id iran-ce-msc-1395 \
  --source source/95_Key.pdf \
  --output dataset/staged/1395-key.json
```

Use `--force` to replace an existing generated artifact. Full staged JSON is
ignored by Git; tracked manifests record expected hashes and structural facts
without publishing the extracted content.

Run all tests, including real-PDF integration tests when local source material
is present:

```bash
uv run pytest
```
