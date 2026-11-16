# Rendered PDF/JPEG family — bounded media triage (1392–1394)

This first M2f slice is **media diagnostics only**, not an optical grid
transcriber or an independently authenticated answer-key importer.

Run:

```bash
uv run --dev python -m english_exam.rendered_key_batch --source-dir source
```

One run inventories `92_key.pdf`, `93_key.pdf`, and `94-key.jpg`.
Existing `batch_inventory` distinguishes missing files, LFS pointers,
signature mismatches, hash mismatches and genuine local media. Where a
valid media header exists, this probe reports bounded PDF page counts,
embedded image counts, pages with a nonempty native character layer, or
JPEG SOF frame dimensions. It does **not** parse answer rows, render PDF
pages, decode JPEG pixels, use OCR, infer variants, or publish original
media, glyphs, text, or key sequences.

`MEDIA_TRIAGED_VISUAL_MAPPING_PENDING` means only that technical metadata
was read. `JPEG_HEADER_ONLY` specifically does **not** prove that the
complete JPEG bitstream is decodable. `SOURCE_HASH_UNPINNED` persists
until an independently justified source-identity pin is recorded.
`VISUAL_GRID_UNLOCATED` and `BOOKLET_UNASSIGNED` remain explicit flags.
A normal CLI exit code 0 means report generation succeeded, even when
individual sources are `SOURCE_NOT_READY` or `MEDIA_PARSE_FAILED`.

Public checkout contains Git LFS pointers rather than underlying media;
synthetic tests cannot establish actual source-page geometry. Next M2f
slice should add bounded visual row/column localization with source-present
fixtures and explicit candidate confidence, leaving uncertain pages
unresolved. Do not turn a visual candidate into `final_verified`.

Related: [batch workflow](BATCH_FIRST_MULTYEAR.md), [Issue #45](https://github.com/ehsanrs2/Konkeroo/issues/45),
and umbrella [Issue #39](https://github.com/ehsanrs2/Konkeroo/issues/39).
Source rights D-010 and release status `BLOCKED` remain unchanged.
