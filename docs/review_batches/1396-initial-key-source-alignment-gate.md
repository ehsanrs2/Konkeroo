# 1396 English INITIAL key — real-source alignment gate

**Scope: audit only, not a new key importer and not verified final answers.**

The 1396 English key already has a visual, source-linked **30-row transcription** and an existing `align_curated_official_claims` structural reconciliation. The purpose of this small hardening PR is to preserve immutable key revision identity and to obtain a **source-present integration result** against the two actual PDFs. Do not use this work to promote any answer authority or publish content.

## Exact original sources and status

| Source or record | SHA / authority |
| --- | --- |
| Exam `source/96.pdf` | SHA-256 `69bc3434ae61c05c85bc9fabffd0b2ce13e5b39bc71b1dfd71c16709c9638ba2` |
| Key `source/96_Key.pdf` | SHA-256 `5d421dcddc780120b13a08753fd2559e7ec02a60200c7c88f4211d70429cba61` |
| Pinned `dataset/review/1396-english-official-key.json` | Git blob SHA-1 `816ed02acebd38d8105424eccc07b91cc1c22736` |
| Printed key identity (original source-linked claim) | **Booklet C, edition INITIAL, page 1, first visual group, rows 1–30** |
| Review authority | `AI_DIRECT_VISUAL_READING`, `PENDING_HUMAN_REVIEW`; 30 independent-human key checks still pending |
| Release | `publication_status: BLOCKED`, `independently_verified:false` |

The JSON records **positions attributed to the initial official key**; it does not verify that transcription against the actual key page independently, prove that the initial key was never superseded, or solve questions key-blind. The key PDF does not expose native answer text; its table source is a **visual** locator, not native PDF text geometry.

The existing `src/english_exam/review_reconciliation.py` already checks all 30 question/choice links against a validated staged exam. Do **not** duplicate this function or claim a universal key parser was added.

## What the strengthened tests prove

- Both original source PDFs actually exist and match the **expected SHA-256** before the source-conditional test proceeds.
- The visual-key JSON itself matches its **exact immutable revision pin in the independent-review ledger**, and that ledger's existing 94-task review docket is structurally sound but still **BLOCKED_PENDING_REVIEW** (19 recorded human decisions, 75 pending).
- All 30 staged question/choice rows exist once, and the curator-supplied booklet/edition/key-table group and row are structurally consistent with the original exam and the preexisting `ExpectedKeyIdentity`.
- **Q20 belongs to Reading-1, Q25 to Reading-2, Q26–30 to Reading-3** despite crossing printed PDF pages. Cloze 11–15 belongs to `cloze-1`.
- Original stage, source-linked JSON, ledger and the three separate answer authorities (`official`, `ai`, `final_verified`) are **not modified**.
- Source-independent negative tests reject even a valid-looking but changed answer position if its curated revision pin is stale, and reject fabricated FINAL edition, wrong booklet and premature release state.

**What these tests do not prove:** the actual visual grid positions have been independently re-read; an **INITIAL** key is the definitive/final answer set; all question texts are free of OCR-like ambiguities; source media or answers are licensed for redistributable public use. Such claims are outside this audit and require separate evidence.

## Run against real sources after merging

The test already existed before this hardening; this PR strengthens it and adds revision guards. With **both** SHA-matched originals present locally:

```bash
git pull --ff-only
uv sync --locked --dev
uv run --dev python -m pytest -q -ra \
  tests/integration/test_1396_curated_key_alignment.py
```

**Expected only after actual execution:** `1 passed`. In public CI, with missing `source/` LFS media, this test **skips**; such a skip is **not** equivalent to a real source-present success. Any missing/changed key source hash or original revision pin must **fail**, not be bypassed.

The source-independent tests are included in regular CI:

```bash
uv run --dev python -m pytest -q \
  tests/unit/test_1396_initial_key_revision_gate.py
```

Do not paste a full key position sequence into public GitHub comments, and do not create a public full exam/key dataset from the audit. Record the **test outcome and source identity only**, then close [Issue #37](https://github.com/ehsanrs2/Konkeroo/issues/37) as *structural alignment complete* when the actual source-present test passes. Full key-version authority, source-distribution rights and later local/privately generated provisional text export remain separate work.
