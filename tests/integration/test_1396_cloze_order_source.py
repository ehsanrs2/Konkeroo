"""Original 1396 PDF: prove the '10' glyph has correct staged line order.

The test is source-conditional and skips in GitHub CI without LFS media.
It does not approve or publish the suggested corrected text.
"""

from hashlib import sha256
from pathlib import Path

import pdfplumber
import pytest

from english_exam.cloze_order_review import (
    EXAM_SHA,
    RAW_ANCHOR,
    preview_1396_cloze_to_remember,
)
from english_exam.pipeline import extract_staged_1396

SOURCE = Path(__file__).parents[2] / "source/96.pdf"
pytestmark = pytest.mark.source_pdf


def test_original_pdf_baseline_order_and_read_only_candidate():
    if not SOURCE.is_file():
        pytest.skip("original source/96.pdf not present in source-independent CI")
    assert sha256(SOURCE.read_bytes()).hexdigest() == EXAM_SHA

    staged = extract_staged_1396(SOURCE)
    assert staged.validation.status == "PASSED"
    body = staged.exam.sections[1].passages[0].body
    assert body.raw_text.count(RAW_ANCHOR) == 1
    assert "10 remember verbal" in body.raw_text
    assert "\n10\napproaches." not in body.raw_text
    original = body.raw_text
    preview = preview_1396_cloze_to_remember(staged)
    assert preview.status == "PROPOSED_PENDING_TECHNICAL_REVIEW"
    assert preview.proposed_full_text is not None
    assert preview.proposed_full_text.count("to remember verbal") == 1
    assert preview.proposed_full_text.count("10 remember") == 0
    assert preview.proposed_full_text.endswith("approaches.")
    assert body.raw_text == original
    assert body.corrected_text is None

    with pdfplumber.open(SOURCE) as pdf:
        page = pdf.pages[1]
        words = page.extract_words(x_tolerance=2, y_tolerance=2, use_text_flow=False)
        glyph = next(
            w for w in words if w["text"] == "10" and 700 < w["top"] < 725 and w["x0"] < 95
        )
        remember = next(w for w in words if w["text"] == "remember")
        approaches = next(w for w in words if w["text"] == "approaches.")
        assert glyph["x1"] < remember["x0"]
        assert abs(glyph["bottom"] - remember["bottom"]) < 3
        assert abs(glyph["bottom"] - approaches["bottom"]) > 10
        assert "\n10\napproaches." in page.extract_text(x_tolerance=2, y_tolerance=2)
    assert sha256(SOURCE.read_bytes()).hexdigest() == EXAM_SHA
