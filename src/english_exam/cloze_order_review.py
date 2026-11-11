"""Fail-closed, read-only preview for the 1396 Cloze 'to remember' token.

This is a source-specific diagnostic, not a general PDF/OCR repair engine.
No mutation or independent-review decision is performed by this module.
"""

from __future__ import annotations

from dataclasses import dataclass

from english_exam.domain import StagedDataset

EXAM_SHA = "69bc3434ae61c05c85bc9fabffd0b2ce13e5b39bc71b1dfd71c16709c9638ba2"
RAW_ANCHOR = "laboratory tests of our ability\n10 remember verbal and visual materials"
SUGGESTED_ANCHOR = "laboratory tests of our ability\nto remember verbal and visual materials"
ANOMALY_ID = "cloze-ability-to-remember-displaced-token"


@dataclass(frozen=True, slots=True)
class ClozeTokenPreview:
    status: str
    anomaly_id: str
    source_pdf_page: int
    original_fragment: str | None
    proposed_fragment: str | None
    proposed_full_text: str | None
    errors: tuple[str, ...]


def preview_1396_cloze_to_remember(staged: StagedDataset) -> ClozeTokenPreview:
    """Propose one anchored token edit; never edit the staged passage or ledger.

    The project's baseline-grouping importer already places the glyph token
    '10' immediately before 'remember'. The plain pdfplumber text extractor
    can show it as an isolated line because the token's top differs by 3.096
    PDF points. The source glyph is printed 'to' (owner visually attested).
    """
    errors: list[str] = []
    source = staged.exam.source_document
    if staged.exam.id != "iran-ce-msc-1396" or source.source_filename != "96.pdf":
        errors.append("wrong exam identity or filename")
    if source.sha256 != EXAM_SHA or 2 not in source.english_pdf_pages:
        errors.append("wrong source SHA or English page coverage")
    if staged.validation.status != "PASSED" or staged.validation.errors:
        errors.append("staged exam has not passed validation")
    cloze = next((section for section in staged.exam.sections if section.id == "cloze"), None)
    if cloze is None or len(cloze.passages) != 1 or cloze.passages[0].id != "cloze-1":
        errors.append("expected single source-bound Cloze passage is missing")
        body = None
    else:
        body = cloze.passages[0].body

    if body is not None:
        if body.corrected_text is not None or body.normalized_text is not None:
            errors.append("passage already transformed")
        if not any(
            item.page_number == 2 and item.source_filename == "96.pdf" for item in body.provenance
        ):
            errors.append("missing page-2 source provenance")
        raw = body.raw_text
        if raw.count(RAW_ANCHOR) != 1:
            errors.append("anchored source string absent or duplicated")
        if raw.count("10 remember") != 1 or "\n10\n" in raw:
            errors.append("token order not uniquely aligned in staged text")
        if raw.count("approaches.") != 1:
            errors.append("ending context absent or ambiguous")

    if errors or body is None:
        return ClozeTokenPreview("BLOCKED", ANOMALY_ID, 2, None, None, None, tuple(errors))
    return ClozeTokenPreview(
        status="PROPOSED_PENDING_TECHNICAL_REVIEW",
        anomaly_id=ANOMALY_ID,
        source_pdf_page=2,
        original_fragment=RAW_ANCHOR,
        proposed_fragment=SUGGESTED_ANCHOR,
        proposed_full_text=body.raw_text.replace(RAW_ANCHOR, SUGGESTED_ANCHOR, 1),
        errors=(),
    )
