# M2f — conservative cell-lattice geometry (1392–1394)

This is a third **geometry-only** step after [region segmentation](RENDERED_GRID_REGIONS.md). It is **not** an OCR solution, answer-key transcription, page join, or final dataset. Public CI does not have the real LFS images.

```bash
uv sync --locked --dev
uv run --dev python -m english_exam.visual_grid_cells --source-dir source
```

The batch tries 1392/1393 PDF and 1394 JPEG originals **only** when the existing source catalog says actual media are locally available. Files recognized as LFS pointers, missing, malformed, signature-invalid or hash-mismatched are blocked. Bounded JPEG decoding and PDF page rendering use the established size, page and pixel caps. Original PDFs/JPEGs are never modified.

For each *disconnected ruled region* returned by the [previous detector](RENDERED_GRID_REGIONS.md), the new function `propose_cell_lattice` independently checks that horizontal and vertical separator runs span their region, boundary coordinates match the region extents, each separator is thin and distinct, every grid intersection is dark, and each proposed cell has nonzero interior. It cautiously rejects widths/heights that differ by more than 1.8× because the larger gap may indicate a missing separator. **This assumption is intentionally conservative** and may reject perfectly valid asymmetric answer-key tables; it is not evidence that real historical grids are evenly spaced. Source-specific geometry or independent visual review is required to relax it.

For a candidate region, an **in-memory** typed `CellLattice` holds ordered 0-based row/column-indexed pixel rectangles strictly inside separator lines. The batch JSON does **not** serialize those rectangles or any line coordinates. It publishes only year/source SHA, page number, region index and bounding box, provisional row/column/cell **counts**, failures and uncertainty flags. This is sufficient for diagnosis without exporting full images, cell pixels, question IDs, answer choices, raw text or copyrighted sequences.

`UNVERIFIED_CELL_LATTICE` represents technical geometry, **not a validated official answer**. An ambiguous/missing separator yields `INCOMPLETE_CELL_LATTICE`; some regions/pages may still be independently usable. No question range, booklet, edition or English-section mapping is inferred, and multi-page 1393 stays explicitly `MULTIPAGE_CONTINUATION_UNRESOLVED`. Actual-source checks for 1392–94 remain pending; synthetic and JPEG tests cannot establish real-page acceptance. A successful command exit only means a report was emitted.

Next substantial gate: obtain real media in a private/authorized environment, collect page-level detector statuses and source-identity evidence, then evaluate limited visually anchored cell readings and special entries (1393/Q100 has multiple accepted answers). Keep uncertain rows unresolved. No complete answer key can be promoted to `final_verified` from this module.

Tracking: [Issue #51](https://github.com/ehsanrs2/Konkeroo/issues/51), [Issue #49](https://github.com/ehsanrs2/Konkeroo/issues/49), and umbrella [Issue #39](https://github.com/ehsanrs2/Konkeroo/issues/39). Source redistribution decision D-010 and public release status `BLOCKED` remain unchanged.


The next source-bound check is [rendered original-media acceptance](RENDERED_SOURCE_ACCEPTANCE.md),
which pins the repository LFS object identities, compares stage counts and
separates source-present evidence from synthetic CI. It does not decode answers.
