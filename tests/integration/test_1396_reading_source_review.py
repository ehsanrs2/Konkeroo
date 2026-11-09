"""Source-present checks for curated Reading editorial evidence.

Only verifies source identity and raw text-layer fragments; the replacement
readings still require an independent reviewer of the printed PDF pages.
"""

import json
from hashlib import sha256
from pathlib import Path

import pdfplumber
import pytest

ROOT = Path(__file__).parents[2]
PDF = ROOT / "source" / "96.pdf"
REVIEW = ROOT / "dataset/review/1396-reading-text-review.json"

pytestmark = pytest.mark.source_pdf


def test_reading_review_uses_the_original_pdf_and_exact_source_fragments():
    if not PDF.is_file():
        pytest.skip("the original immutable 1396 exam source is unavailable")
    review = json.loads(REVIEW.read_text(encoding="utf-8"))
    expected_sha = review["exam_source"]["sha256"]
    assert sha256(PDF.read_bytes()).hexdigest() == expected_sha

    with pdfplumber.open(PDF) as document:
        assert len(document.pages) == 40
        page_text = {
            page_number: document.pages[page_number - 1].extract_text(x_tolerance=2, y_tolerance=2)
            for page_number in (3, 4, 5)
        }

    for row in review["proposals"]:
        text = page_text[row["source_pdf_page"]]
        assert text.count(row["expected_raw_fragment"]) == 1, row["id"]

    for anomaly in review["unresolved_anomalies"]:
        text = page_text[anomaly["source_pdf_page"]]
        assert all(token in text for token in anomaly["observed_raw_fragments"])

    assert "16-" in page_text[3] and "19-" in page_text[3]
    assert "20-" in page_text[4] and "21-" in page_text[4]
    assert "24-" in page_text[4] and "25-" in page_text[5]
    assert "26-" in page_text[5] and "30-" in page_text[5]
    assert sha256(PDF.read_bytes()).hexdigest() == expected_sha
