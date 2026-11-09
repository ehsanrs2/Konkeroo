# Engineering and GitHub workflow

## Collaboration model

GitHub `main` is the reviewed baseline. Work in small branches named by goal, e.g. `docs/project-charter-architecture-roadmap` or `feature/key-1396-rendered`. Open focused PRs; avoid direct commits to `main`, force-pushes, and unrelated refactors.

**Assistant/GitHub connector:** can inspect committed repository history, create branches/files/PRs and review diffs. It **cannot see a developer's local uncommitted files** unless they are published or explicitly supplied. Never assume GitHub's `main` reflects an unpushed local working tree.

**Local development/Codex:** executes environment-dependent work such as reading local full source media, tests, geometry verification, and generating ignored staged outputs. Reports must include commit SHA, test results, ignored-file safety and relevant manifest hashes. Keep local work safe when fetching remote changes; use a separate worktree if necessary.

## Task sequence

1. Confirm goal, relevant decision(s), source/fixture constraints, expected input and output, and whether the task is planning or implementation.
2. Inspect current `main` and linked documentation, including source publication policy; verify branch and local working-tree status before changing files.
3. Open a narrowly scoped issue or branch; keep implementation small enough for human review.
4. Implement without altering `source/`, conflating answer authority, or adding unapproved external AI/network calls.
5. Add source-independent unit tests and source-conditional integration coverage, plus deterministic manifest expectations where appropriate.
6. Run: `uv lock --check`, `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `git diff --check`.
7. Inspect the diff for accidental source media, full datasets, secrets, debug outputs, and changed assertions that weaken validation.
8. Create PR with scope, tests, known limitations, and doc/decision updates. Require explicit review before merging.
9. Verify resulting `main` and update [Roadmap](ROADMAP.md) state, relevant decision records, and artifacts only when evidence supports it.

## PR review checklist

- Does the implementation respect [Architecture](ARCHITECTURE.md) and recorded decisions?
- Is fixture-specific behavior outside shared domain invariants?
- Is raw provenance truthful and can every derived field be traced back to source?
- Are source hashes and page bounding boxes valid and applicable?
- Does no parser silently guess when a cell, answer, or scoring annotation is ambiguous?
- Do tests assert actual content/relationships rather than only record counts or hashes?
- Is the full staged source-derived data excluded from Git?
- Are policy/legal considerations addressed for any public media or dataset changes?
- Can a separate reviewer reproduce the results from permitted local sources?

## Completion and continuity

Every completed milestone should leave: implementation code, a focused PR/commit, tests and their results, a non-text manifest when applicable, remaining limitations, and an updated roadmap/decision log. When uncertain, mark work `not verified` instead of `done`.
