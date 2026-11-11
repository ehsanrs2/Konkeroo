# Data governance, reproducibility, and release policy

## What is in the repository today

- **Source catalog/input:** `source/` has the known 15 exam paper years 1391–1405 and 14 corresponding key files (1405 has none). On current public `main`, 29 source paths are **Git LFS pointer files**, tracked under `.gitattributes`.
- **Raw derived data:** full staged `dataset/staged/*.json` is ignored; checked-in `*.manifest.json` contains hashes/counts/structural expectations, not answer sequences or substantial question text.
- **Implementation/tests:** Python importers, source-independent sanitized fixtures, and source-conditional integration tests.
- **Verified or releasable content:** no verified dataset or release has been established by the current code.

The Git LFS state is different from the original local-only intention. Track it as the open publication decision [D-010](DECISIONS.md), not as an implicitly approved license.

## Integrity and provenance contract

1. Keep the original source immutable; use SHA-256 hashes to bind import results to the correct bytes.
2. Preserve file name, actual media type, page/image dimension, 1-based page, source region, extraction method, and raw representation as appropriate to the source.
3. Native PDF text provenance may include exact characters and tight source bounding boxes. Image/vector-derived readings must cite a **visual region** and recognition/review status, not claim the OCR result is native PDF text.
4. Keep `raw_text`, `normalized_text`, and `corrected_text` separate, with explicit review and audit trail for modifications.
5. Preserve booklet variants, editions, multiple answers, deleted entries, `سفید`, and scoring annotations; do not invent scoring semantics.
6. Do not attach official answers to a target English question until the year/booklet/section mapping is independently verified.
7. Fail visibly on duplicate rows, missing cells, unsupported source hashes, bad geometry, low-confidence recognition or unresolved ambiguity.

## Public distribution guardrails

- Never commit full staged exam/key JSON, OCR dumps, generated full passages, extracted answer sequences, or user learning records by default.
- Sanitized test fixtures should use invented text and should not reproduce a substantial source-derived extract.
- Tracked manifests may include source/artifact hashes, counts, schema versions, supported ranges and validation outcomes.
- Do not assume that a public exam page or “official” key is public-domain or has a redistribution license. Evaluate rights separately for source LFS media, verified text, answer keys, and app-bundled content.
- **Open action:** assess whether publicly tracked Git LFS exam PDFs/JPGs should remain accessible. If not, removing them from working tree alone is insufficient: Git history, cached copies, LFS storage and external forks need a coordinated response.
- Do not disclose private learner progress, raw telemetry or credentials; Android analytics/consent/retention policy is to be decided before any collection.

## Assistant-only provisional development lane (owner opted out of routine human review)

From 2026-11-11, the owner opted out of mandatory **per-item independent human checks for provisional correction development**. See [assistant-only provisional workflow](ASSISTANT_ONLY_PROVISIONAL.md) for exactly how source-bound assistant proposals, deterministic validation and unresolved anomalies are handled.

This changes **who must check each editing task before development can continue**; it does **not** silently grant source correctness, independent verification, the right to distribute copyrighted source material or the authority to publish a verified dataset. The 19 genuine prior human decisions remain in the review ledger; its 75 unreviewed tasks are not retroactively marked as approved. The public/source-rights and final-answer-key release gates below remain intact.

## Regeneration and release checklist

For a candidate dataset release (future):
- Record source identities/hashes and exact parser/schema/dependency versions.
- Reproduce staged outputs from source and compare deterministic hashes with manifests.
- Resolve parser warnings and ambiguous answer-key recognition through an auditable review process.
- Confirm question and choice coverage, page-region provenance, and correct answer authority/edition.
- Verify exam/key alignment by year and booklet; mark missing or unverified answers explicitly.
- Execute source-independent and source-present integration tests.
- Confirm redistribution rights and release license for the proposed content, including source media and app bundles.
- Version the verified schema/artifact and maintain correction/withdrawal procedures.

No present manifest checksum, by itself, proves semantic correctness.
