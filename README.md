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
