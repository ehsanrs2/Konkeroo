from pathlib import Path

from english_exam.domain import BBox, ExtractedText, SourceProvenance
from english_exam.serialization import to_json

FIXTURE = Path(__file__).parents[1] / "fixtures" / "sanitized_text_expected.json"


def test_sanitized_golden_serialization() -> None:
    value = ExtractedText(
        raw_text="Invented ---- text",
        provenance=(
            SourceProvenance(
                source_filename="synthetic.pdf",
                page_number=1,
                bbox=BBox(10.0, 20.0, 110.0, 32.0),
                raw_text="Invented ---- text",
                extraction_method="SYNTHETIC_TEST_LAYOUT",
            ),
        ),
    )

    assert to_json(value) == FIXTURE.read_text(encoding="utf-8")
