# M2f: disconnected ruled-region geometry — 1392–1394

This read-only family probe is **a geometry experiment**, building on [media triage](RENDERED_KEY_FAMILY.md) and [whole-page ruled-line projections](VISUAL_GRID_GEOMETRY.md). It does **not** extract cells, recognize digits, assign booklets, reconcile pages or verify an answer.

```bash
uv run --dev python -m english_exam.visual_grid_regions --source-dir source
```

The batch handles `92_key.pdf` (1392), `93_key.pdf` (1393) and `94-key.jpg` (1394). It first uses the same immutable source inventory and rejects missing media, Git LFS pointers, hash/signature mismatches or malformed source. A readable JPEG is pixel-decoded; a real PDF is rasterized page by page at 100 DPI, with file, page and pixel limits applied before any expensive step. **CI does not have the actual LFS images**, so source-specific real-layout success remains unverified.

## Why this differs from the preceding scanner

The previous stage globally projected ink across complete rows and columns. This can fuse two adjacent tables or miss shorter table rules. The new method scans **long contiguous dark horizontal/vertical runs**, joins only runs crossing geometrically, and groups their connected components. Components require at least four thin rules on each axis, a minimum local extent, and at least 80% intersection occupancy. Every surviving candidate yields only **page-local pixel bounding box** plus counts of horizontal/vertical rules. Candidate order is deterministic (top, left).

Notably, the returned bbox is **not** a trusted cell grid, crop, row transcription or key range. Long text strokes, low resolution, broken lines, outlines and unruled tables can still cause false positives/negatives. A detector can report `NO_STRICT_RULED_REGION` for a visually present grid. Overlap between candidates, more than eight plausible regions or excessive line-run counts fail closed. It produces **no answer sequences, text, images, OCR values or reconstructed source material**.

Multi-page keys (especially 1393) stay independent per page and carry `MULTIPAGE_CONTINUATION_UNRESOLVED`. Statuses `SINGLE_UNVERIFIED_REGION`, `MULTIPLE_UNVERIFIED_REGIONS`, `PARTIAL_UNVERIFIED_REGIONS` and `REGION_AMBIGUITY_UNRESOLVED` never imply validation. Source SHA observations are kept, and `SOURCE_HASH_UNPINNED`, `BOOKLET_UNASSIGNED`, `NO_CELL_OR_ANSWER_DECODING` remain explicit.

Synthetic tests include **two adjacent disconnected grids**, one grid, blank/unruled images, malformed JPEG, real pixel-decoded JPEG, raster bounds, mocked two-page PDF, and per-source pointer/hash isolation. An original-media source-present acceptance must follow before claiming useful coverage on Iranian exam keys. Subsequent work can inspect **exceptional regions locally** and add reviewed cell-level visual evidence; it must not fill in official answers from geometry alone.

Tracking: [Issue #49](https://github.com/ehsanrs2/Konkeroo/issues/49), [Issue #47](https://github.com/ehsanrs2/Konkeroo/issues/47), umbrella [Issue #39](https://github.com/ehsanrs2/Konkeroo/issues/39). Dataset release remains `BLOCKED`; publisher/redistribution rights decision D-010 is unchanged.
