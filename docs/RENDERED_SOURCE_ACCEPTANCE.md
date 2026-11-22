# M2f original-media acceptance diagnostics (1392–1394)

**Evidence status:** Repository Git LFS pointers are observed. No original PDF/JPEG
bytes were available to this development session or ordinary public CI.
**No claim of actual-source geometry acceptance or official-key validation.**

This step shifts from synthetic heuristic development toward repeatable
source-present diagnostics. It pins the **repository LFS object SHA-256** for
three original key files:

| Year | Key | Repo LFS SHA-256 | LFS recorded size |
| --- | --- | --- | ---: |
| 1392 | `92_key.pdf` | `d48c332dfa189adde10b2dfbd0ef03ccad6586e4222da9c3159077200edb51c6` | 260186 |
| 1393 | `93_key.pdf` | `264e1ba0f4b970977b9da13a2125606d44502563308db9e5fbe972786e5f7e46` | 602063 |
| 1394 | `94-key.jpg` | `6bb88afff457a2c9fad1d34af8c77871b0670432f1218902307c46eef3bedaa6` | 129773 |

**These are not independent publisher attestations.** A matching local file
proves the bytes match the object referenced by this repository, **not**
which booklet/edition the publisher intended, official scoring semantics,
answer correctness, or redistribution rights.

## Single-command batch audit

In an authorized local checkout with Git LFS and the original media:

```bash
uv sync --locked --dev
git lfs pull --include="source/92_key.pdf,source/93_key.pdf,source/94-key.jpg" --exclude=""
uv run --dev python -m english_exam.rendered_source_acceptance --source-dir source
```

The command compares per-year outputs from **existing**, independently
maintained stages: `batch_inventory`, `rendered_key_batch`,
`visual_grid_regions`, and `visual_grid_cells`. It checks source
identity and per-page consistency between reported region counts,
dimensions and cell-lattice statuses, and emits only JSON **metadata**:
source OID and observed hash, source status, page numbers, provisional
region/lattice counts, exceptions and flags. It never prints PDF text,
answer positions, cell coordinates, images, decoded content, or answer
sequences. No originals or generated images should be committed or
uploaded to CI artifacts.

For a stricter source-presence gate:

```bash
uv run --dev python -m english_exam.rendered_source_acceptance \
  --source-dir source --require-sources
```

Exit codes: `0` means the report was produced, or that all three **matching
repository-object media files** were available with `--require-sources`.
`2` means at least one actual SHA-matched source is missing. It says
nothing about geometric coverage.

For provisional **geometry** evidence (still no answer verification):

```bash
uv run --dev python -m english_exam.rendered_source_acceptance \
  --source-dir source --require-provisional-geometry
```

Exit `3` means at least one original was absent or one source's full
per-page region/cell-lattice diagnostics was incomplete. This test
conservatively treats ambiguous/borderless layouts as exceptions instead
of guessing. An exit `0` here indicates only **provisional geometry**
over all three sources — not official answer accuracy, complete key
decoding, page joins or public release.

## Interpretation

- `LFS_POINTER_ONLY` is not source media, even when its OID matches.
- `SOURCE_IDENTITY_CONFLICT` and `SOURCE_HASH_MISMATCH` block processing.
- `PROVISIONAL_GEOMETRY_OBSERVED` is only geometry; answer authority is
  always unverified. `SOURCE_PRESENT_GEOMETRY_UNRESOLVED` requires a
  targeted local inspection, not an automatic parser promotion.
- Multi-page 1393 remains `MULTIPAGE_CONTINUATION_UNRESOLVED`.
- Real-source CI integration skips if none of these 3 original media are
  available. If some are present, it checks each matching file independently
  and explicitly records the others as unavailable. A skip is **never** a pass.

Run only in an environment authorized to access the originals. Keep any
visual crops or extracted content private and local, with rights decision
D-010 unresolved. The public dataset remains **`BLOCKED`**.

Tracking [Issue #53](https://github.com/ehsanrs2/Konkeroo/issues/53)
under [#39](https://github.com/ehsanrs2/Konkeroo/issues/39). Subsequent
work should use the **actual** per-page exception report to choose narrow
visual verification/OCR or handle 1393's special multiple-answer entry;
no universal OCR or guessed answer rows.
