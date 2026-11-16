# Rendered key line-grid geometry candidates (M2f)

This is a **second, still provisional** step beyond [PDF/JPEG media triage](RENDERED_KEY_FAMILY.md), not an OCR pipeline or answer importer.

```bash
uv run --dev python -m english_exam.visual_grid_batch --source-dir source
```

The command inspects 1392 `92_key.pdf`, 1393 `93_key.pdf` and 1394 `94-key.jpg` in one run. It reuses the central 1391–1405 source inventory: missing originals, LFS pointer text, signature mismatches and hash conflicts are **not** passed to the raster stage. Original source files are immutable; no image, digits, key positions, text, or cell crops are written to disk or printed.

## Deliberately narrow geometric method

- Real JPEG pixel decode via Pillow (not merely the JPEG header check). PDF pages rendered at 100 DPI with pdfplumber, after page-count, file-size and **predicted** rendered-pixel bounds are checked.
- Threshold dark pixels and project ink over image rows and columns. Thin, repeated long horizontal/vertical rules are grouped into candidate line centers. Only a grid with at least four of each, substantial bounding area and at least 80% of expected line intersections qualifies.
- Output per page: raster dimensions, candidate counts, an **approximate pixel bounding box**, and `UNVERIFIED_LINE_GRID_CANDIDATE` status. These are geometry observations, **not cells**, correct readings, calibrated confidence, OCR output or complete keys.
- PDFs with multiple pages are kept as independent page results. `MULTIPAGE_CONTINUATION_UNRESOLVED` is always set for multi-page sources (notably 1393). A candidate on only some pages yields `PARTIAL_GEOMETRY_CANDIDATES`.
- A blank, borderless, irregular or thin/low-resolution grid may produce `NO_STRICT_INTERSECTING_RULE_GRID` even if a human can see a key. This is intentional **fail-closed** behavior, not evidence that a source contains no table.
- A global projection cannot safely distinguish overlapping/multiple tables. `GLOBAL_PROJECTION_UNSEGMENTED` remains set even when a candidate exists, and geometry is **never** promoted to an answer.
- `SOURCE_HASH_UNPINNED`, `BOOKLET_UNASSIGNED`, `KEY_EDITION_UNASSIGNED`, `NO_ANSWER_DECODING` remain until independent evidence changes those facts.

Synthetic tests construct small artificial ruled images, borderless/no-grid images, actual JPEG compressed images, corrupt JPEG, bounded fake PDF raster pages, continuation cases and LFS pointer isolation. **Public CI without original Git LFS media cannot establish actual layout coverage.** On real source media, use this report to decide the next *region-specific* visual/OCR analysis, retaining every unsupported page as an exception rather than guessing.

The related tracking issues are [#47](https://github.com/ehsanrs2/Konkeroo/issues/47), [#45](https://github.com/ehsanrs2/Konkeroo/issues/45), and umbrella [#39](https://github.com/ehsanrs2/Konkeroo/issues/39). Rights decision D-010 remains open; public dataset release is `BLOCKED`.
