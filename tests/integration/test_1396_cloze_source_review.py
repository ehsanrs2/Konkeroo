"""Local original-PDF check for source fragments used by Cloze review.

This verifies source-layer substring identity, NOT the accuracy of the visual
correction. An independent reviewer still needs to inspect the printed page.
"""

import json
from hashlib import sha256
from pathlib import Path

import pdfplumber
import pytest

ROOT = Path(__file__).parents[2]
PDF = ROOT / "source" / "96.pdf"
REVIEW = ROOT / "dataset" / "review" / "1396-cloze-text-review.json"

pytestmark = pytest.mark.source_pdf


def test_source_present_cloze_review_fragments_and_sha():
    if not PDF.is_file():
        pytest.skip("original 1396 exam source is absent")
    data = json.loads(REVIEW.read_text(encoding="utf-8"))
    before = sha256(PDF.read_bytes()).hexdigest()
    assert before == data["source"]["sha256"]
    with pdfplumber.open(PDF) as document:
        assert len(document.pages) == 40
        page_text = {
            page_number: document.pages[page_number - 1].extract_text(
                x_tolerance=2, y_tolerance=2
            )
            for page_number in (2, 3)
        }

    for proposal in data["proposals"]:
        raw = proposal["expected_raw_fragment"]
        page_number = proposal["pdf_page"]
        assert page_text[page_number].count(raw) == 1, proposal["id"]

    anomaly = data["unresolved_anomalies"][0]
    assert "10\napproaches." in page_text[anomaly["pdf_page"]]
    assert sha256(PDF.read_bytes()).hexdigest() == before
