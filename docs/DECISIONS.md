# Architecture and product decision log

Decisions are recorded with **status**. `Accepted` means a project constraint; `Observed` means true of the inspected repository/source; `Proposed` is not yet binding; `Open` requires a decision before relying on an assumption.

## D-001 — Source fidelity and corrections
**Status: Accepted.** Original PDFs/JPGs are immutable inputs. Keep raw text, normalized text, and corrected text distinct. Never silently fix bad OCR or reuse misleading geometry; corrections must be reviewed and attributable.

**Why:** Auditable, reproducible datasets and later disagreement analysis. Applies to raw question markers as well as text.

## D-002 — Geometry-first exam extraction
**Status: Accepted; implemented for 1396.** Use `pdfplumber` and PDF character/word bounding boxes. Avoid flattened reading order when layout reorders cross-page content. Prefer its permissive license to a PyMuPDF AGPL/commercial dependency.

**Why:** 1396 has distorted text-layer glyphs and Reading questions on pages before their next passage heading. Fixture mapping 16–20, 21–25, and 26–30 is 1396-only.

## D-003 — Preserve distinct answer authorities
**Status: Accepted.** Model official, AI-produced, and final verified answers independently. Support multiple accepted positions, deletion, special scoring notes, and confidence/status; do not treat an official *initial* key as inherently final.

**Why:** Supports disputed, missing, or exceptional keys and a real review workflow.

## D-004 — Answer-key imports are independent of exam staging
**Status: Accepted; partially implemented.** Use explicit catalog IDs/checksums and a separate key pipeline. Import full keys with booklet/edition provenance. Reconcile English entries **only** after verified exam section metadata identifies the target questions.

**Why:** Prevents false English-range assumptions and mixing candidate responses in personalized reports with official values. Implemented source catalog currently contains only 1395.

## D-005 — Validation before publishing content
**Status: Accepted.** Deterministic staged JSON is local/ignored; compact structure/hash manifests are tracked. Use synthetic public fixtures and skip-cleanly real-source integration tests; ambiguity/structural mismatch blocks verified release.

**Why:** Reproducibility and copyright-conscious development. A successful parser is not itself a correctness guarantee.

## D-006 — Corpus diversity, not a universal key parser
**Status: Accepted.** The audited key corpus has paired grids, multi-booklet legacy layouts, and personalized candidate/key triplets, with native, broken-font, rendered, and JPEG media. Implement by representative fixture in reviewable increments; only generic invariants belong in shared modules.

**Why:** Avoid accidental overfitting to 1396 or one table format.

## D-007 — No fabricated official key for 1405
**Status: Accepted.** No official key file was present in the audited corpus for 1405. Represent absent official source explicitly; a possible future AI-only learning mode must not be labeled official.

## D-008 — Dataset before application
**Status: Accepted.** Prioritize trustworthy extraction, corrections, validation and verified releases before Android or adaptive-engine deployment. AI must solve independently before seeing the key for verification experiments.

**Target stack (Proposed):** Kotlin, Jetpack Compose and Room on Android; offline-first verified-content consumption. No app layer is implemented yet.

## D-009 — Git collaboration and review
**Status: Accepted for future work.** Use dedicated feature/docs branches, small commits, tests and Pull Requests into `main`. Update the roadmap/decisions with architectural changes. No force-push as normal workflow.

**Why:** Maintains traceability and protects concurrent local work.

## D-010 — Public Git LFS source publication
**Status: Open — requires explicit owner and rights review.**

**Previous intent:** Original source PDFs/JPGs should remain local, immutable, and untracked; full staged JSON should not be published.

**Current observed repository:** The public GitHub `main` includes `.gitattributes` with `source/*.pdf` and `source/*.jpg` using Git LFS, and 29 tracked `source/` LFS pointer files introduced in `e81f20d` (`Add answer-key extraction pipeline and exam sources`). A pointer for `96.pdf` names SHA-256 `69bc…8ba2` and original size 4,494,678 bytes. These are not the PDF bytes in the Git tree, but may enable public retrieval of uploaded LFS objects.

**Decision required:** Are those original exam and key files licensed/authorized for publication and redistribution from a public repository? Retain public LFS artifacts, move material to private access, or keep only source metadata and require local acquisition? Obtain an explicit rights/distribution decision.

**Safety:** Merely deleting pointers in a later commit would not erase public Git/LFS history. Avoid expanding source publication or issuing dataset releases until this is resolved. Do not rewrite history or delete remote files without explicit authorization and a migration plan.

## D-011 — Human/AI source review over building generic OCR pipelines
**Status: Accepted direction for exam/key data acquisition; partial 1396 example pending review.** The value is a reliable English exam/answer dataset and a learning application, **not** a general-purpose PDF/OCR product. Direct visual reading of the actual exam paper and official key by the assistant, with explicit source hashes, page/table locations, booklet, edition, and review status, is an accepted method of acquiring data. Do not require a new reusable importer or OCR pipeline before curating a year's material.

**Safeguards:** Separate source claim from the transcription/reviewer confidence; never treat an AI visual read as independently verified or a key-blind solution. Mark uncertain digits or mismatch cases for review. Keep original source PDFs immutable; record curated data separately, with year-specific structure and CI checks. Preserve earlier deterministic 1396 exam / 1395 key importers as existing tooling, but avoid spending new milestones solely on extraction engine generalization. AI-generated explanations and final verified answers remain separate stages.

**Scope:** The current direct-visual 1396 task records **English Q1–30 only**, and uses the first pair of columns of the full initial key. Other years require individually confirmed English ranges and booklet matching. This decision revises the earlier M2b implementation strategy, not the provenance/validation obligations of D-001 through D-007.

## D-012 — Bind reviewer evidence to the actual curated artifact revision
**Status: Proposed in M4e PR; not yet merged.** A reviewer decision must identify both immutable original source (PDF SHA-256 and page) and the **exact curated proposal or key artifact revision** examined (Git blob SHA-1). Source identity alone is insufficient because a suggested replacement or answer position may change without changing the original PDF or the task ID.

**Why:** Prevent stale approvals being replayed against altered edits/answers. Changing a source-linked artifact requires repinning the ledger and explicit re-review of affected decisions. A Git blob digest identifies the JSON revision, not a human reviewer or legal permission. Source-independent CI validates the pins; genuine independent human approval remains a separate task.

## How to change a decision

Propose a PR that updates this file, explains new evidence and alternatives, cites affected modules/tests, and links a targeted issue. Do not silently relabel `Open` decisions as `Accepted`.
