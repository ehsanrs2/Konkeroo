# Answer-key corpus audit (planning evidence)

**Status:** audit completed from local source inspection prior to implementation; conclusions below are *layout observations*, not proof of parser support. Most sources do **not** have an importer yet. Source bytes were not copied into this documentation.

## Inventory and format families

| Year / source | Observed format | Family | Main risk / special behavior |
| --- | --- | --- | --- |
| 1391 `91_Key.pdf` | 6-page native numeric text, 4 booklet variants A–D | Legacy multi-booklet | Cross-page and variant boundaries; Q103 accepts 1 and 4 |
| 1392 `92_key.pdf` | 1-page raster PDF, 5 paired groups | Paired grid: rendered | OCR per cell; website boilerplate |
| 1393 `93_key.pdf` | 2-page vector-outlined key, continuation | Paired grid: rendered | Q100 accepts 2 and 3; unused `سفید` cells |
| 1394 `94-key.jpg` | Small, low-resolution JPEG paired grid | Paired grid: image | Low-res digit OCR; reviewed golden required |
| 1395 `95_Key.pdf` | 1-page native text, 5 pairs per row | Paired grid: native | **Implemented**; booklet A, 121 entries; initial edition |
| 1396 `96_Key.pdf` | 1-page vector-only table | Paired grid: rendered | Q70 option 1 with positive-effect annotation |
| 1397 `97_Key.pdf` | 2 pages, unusable font map | Paired grid: broken font | Glyph-code map or regional OCR |
| 1398 `98_Key.pdf` | 2 pages, unusable font map | Paired grid: broken font | Same risks as 1397 |
| 1399 `99_Key.pdf` | 1 page, unusable font map | Paired grid: broken font | Same risks as 1397 |
| 1400 `1400_Key.pdf` | 2-page raster, candidate/key triplets | Personalized | **Never mix candidate responses with official key**; multiple, deletions and positive-effect text |
| 1401 `1401_Key.pdf` | 2-page native paired grid | Paired grid: native | Unused scaffold cells |
| 1402 `1402_Key.pdf` | 2-page native paired grid | Paired grid: native | Flattened extraction truncates/reorders a group |
| 1403 `1403_Key.pdf` | 2-page native candidate/key triplets | Personalized | Official deletions Q46 and Q114; distinct candidate column |
| 1404 `1404-key.pdf` | 1-page compact native paired grid | Paired grid: native | Header/QR outside answer table |
| 1405 | **No official key file** | Unavailable | Record explicit `NO_OFFICIAL_KEY` |

Different spellings `_Key`, `_key`, and `-key` are *source filenames*, not parsing rules.

## Verified audit examples requiring special representation

- Multiple accepted answers: 1391/Q103 (1,4), 1393/Q100 (2,3), 1400/Q92 (1,2).
- Positive-effect notes: 1396/Q70; 1400/Q59, Q61, Q65, Q70, Q95, Q113. **Preserve raw annotation**; do not infer scoring semantics.
- Deleted/canceled entries: 1400/Q39, Q74, Q80, Q87, Q98; 1403/Q46, Q114.
- `سفید` or empty scaffolding can mean unused range, blank candidate response, or unavailable official value. It does **not** automatically mean a deleted question.
- Some published sources label themselves **initial**, not final; carry edition with provenance.
- English ranges for all unimported exam years remain **unknown**. No universal 25/30-question assumption.

## Importer design guidance

Use one shared source catalog, page region/bbox abstraction, digit normalization (Latin/Persian/Arabic-Indic), raw and normalized values, disposition/annotation support, validation, serialization, and deterministic manifests. Provide family-specific table geometry and reading strategy.

Preferred order: reliable native text -> explicit glyph map if validated -> render individual geometric cells and targeted local OCR -> human-reviewed declaration when uncertain. Avoid full-page OCR as the parser. For personalized keys, the table's **official key column** must be specified, never inferred from nearby candidate-response values. Import the *entire key* into independent staging, then attach only verified English question IDs in reconciliation.

Current implementation uses only 1395 native paired-grid; `RecognitionStatus` and visual provenance in the model do not imply rendered OCR is implemented.

This is an audit, not a machine-executable catalog. Each supported importer must add an exact source checksum, fixture validation, and regression tests.
