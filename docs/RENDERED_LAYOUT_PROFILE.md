# M2f: source-present page morphology profile — 1392–1394

## Why this exists

A local authorized test on **2026-11-25** against the three exact repository
LFS key objects confirmed `sources_pinned=3` and all four pages readable, but
the original strict ruled-region detector produced **zero candidate regions
and zero cell lattices** across 1392 page 1, 1393 pages 1–2 and 1394 page 1.
The M2f provisional-geometry command exited 3. The source-present integration
test passed, demonstrating correct source handling, not table coverage.

**The evidence does not yet tell us why**: pages may lack ruled lines, use
faint lines, place answers in vector text, or have otherwise incompatible
structure. Do not weaken arbitrary thresholds or add general-purpose OCR
before diagnosing the page layout.

## Safe run (metadata only)

In an authorized checkout with the real Git LFS media and the new PR merged:

```bash
uv sync --locked --dev
uv run --dev python -m english_exam.rendered_layout_profile \
  --source-dir source --require-sources \
  > /tmp/konkeroo-m2f-layout-profile.json
echo "LAYOUT_EXIT=$?"
```

Print the bounded report (no original source files or images required):

```bash
uv run --dev python - <<'PY'
import json
from pathlib import Path

report = json.loads(Path("/tmp/konkeroo-m2f-layout-profile.json").read_text())
print("pinned:", report["sources_pinned"], "pages:", report["profiled_pages"])
for year in report["years"]:
    print("\n", year["year"], year["source_status"], year["status"])
    for page in year["pages"]:
        print(" page", page["page_number"], page["width_px"], page["height_px"],
              "chars", page["pdf_text_layer_char_count"],
              "vectors", page["pdf_vector_line_count"],
              "images", page["pdf_embedded_image_count"],
              "status", page["status"])
        for t in page["thresholds"]:
            print("  threshold", t["dark_threshold"], "ink%", t["dark_percent"],
                  "H", t["horizontal_long_runs"], "V", t["vertical_long_runs"],
                  "maxH", t["longest_horizontal_run_px"],
                  "maxV", t["longest_vertical_run_px"])
PY
```

The report contains **only coarse per-page technical statistics**:
raster dimensions, counts of native PDF characters/vector-line/image
objects, ink fraction at grayscale thresholds 90/180/230, and counts
plus maximum lengths of relatively long horizontal/vertical dark runs.
It does not emit page text, character values, pixel maps, coordinates,
regions, per-cell images, content crops, answer positions or sequences.
The run definition inherits the strict detector's current minimum
span `max(24, image dimension/12)` and complexity cap; counts can be
`null` on overflow. A long run can also be a text underline, border,
or unrelated ornament; **not** a certified table rule.

`LAYOUT_EXIT=2` means one or more exact-LFS-matching originals are absent;
`LAYOUT_EXIT=0` only means the source-identity precondition was met and
a report was emitted. Per-page `RUN_COMPLEXITY_LIMIT` or
`SOURCE_PROFILE_FAILED` remain unresolved, not success.

## Decision gate

Compare source-present page-level numbers before choosing next code:
- native PDF char/line/image counts indicate which representation deserves
  investigation, but are not proof that the answer key is text-extractable
- changes in run counts/ink fractions between thresholds indicate contrast
  sensitivity, not a license to promote candidates
- a borderless, image-based or nonrectangular layout requires a separate,
  source-specific, validated approach, not extrapolation from synthetic grids

Preserve the unresolved 1393 multi-page continuation and multiple-correct
answer special case. No answer rows are inferred. Do not commit or send
source originals, screenshots or OCR output without a separate rights review.
The source redistribution rights decision D-010 and public release status
**BLOCKED** remain in force. Preserve local unrelated edits to
`pyproject.toml` and `uv.lock`.

Tracking: [#55](https://github.com/ehsanrs2/Konkeroo/issues/55),
[#53](https://github.com/ehsanrs2/Konkeroo/issues/53), and [#39](https://github.com/ehsanrs2/Konkeroo/issues/39).
