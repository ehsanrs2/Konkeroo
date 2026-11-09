# Konkeroo project handbook

This directory is the canonical home for product intent, architecture, decisions, and execution state. Implementation code is authoritative for *current behavior*; these documents record *intent, boundaries, and open choices*. Update them in the same PR whenever a milestone changes a documented contract.

| Document | Purpose |
| --- | --- |
| [Product vision](PRODUCT.md) | The problem, audience, learning principles, success criteria, and non-goals |
| [Architecture](ARCHITECTURE.md) | System boundaries, data flow, domain contracts, and planned Android components |
| [Roadmap](ROADMAP.md) | Dependencies, completed baselines, next work, and acceptance gates |
| [Answer-key corpus audit](ANSWER_KEY_CORPUS.md) | Source-format families, exceptions, and safe importer sequencing |
| [Decision log](DECISIONS.md) | Accepted decisions, alternatives, and unresolved choices |
| [Data governance](DATA_GOVERNANCE.md) | Provenance, publishing policy, Git LFS exposure, and release safety |
| [Review protocol](REVIEW_PROTOCOL.md) | Independent textual/key review workflow, evidence and release blocker |
| [Development workflow](WORKFLOW.md) | Branch/PR process, quality gates, roles, and handoffs |

## Snapshot — 2026-11-09

- GitHub `main` at documentation baseline: `e81f20d9bb59bd6344f10c77756f0411bdaa17a5`.
- Implemented in `main`: deterministic 1396 English-question staging; independent native 1395 answer-key staging.
- **Not implemented**: 1396 answer-key recognition/reconciliation, other-year importers, verified dataset, AI solving, learning engine, or Android app.
- A public-repository source-material decision remains **open**: the current `main` tracks source-file Git LFS pointers (see [Data governance](DATA_GOVERNANCE.md)). Do not assume publishing permission.
- This snapshot is based on GitHub code and manifests, **not** a fresh local test run. Test status must be checked in CI/local execution.

For developer commands and current CLI usage, see the repository's top-level [README](../README.md) and [AGENTS.md](../AGENTS.md).
