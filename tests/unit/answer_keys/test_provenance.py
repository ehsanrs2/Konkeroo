from english_exam.answer_keys.domain import (
    AnswerKeyEdition,
    AnswerKeyFamily,
    KeySourceDescriptor,
    MediaType,
    OfficialKeyAvailability,
    ProvenanceKind,
    RawSourceValue,
    SourcePage,
    SourceRegionProvenance,
)
from english_exam.answer_keys.validation import validate_raw_source_value
from english_exam.domain import BBox
from english_exam.pdf_layout import EXTRACTION_METHOD


def test_rejects_malformed_answer_key_bbox() -> None:
    source = KeySourceDescriptor(
        canonical_exam_id="synthetic",
        year=1,
        source_filename="synthetic.pdf",
        media_type=MediaType.PDF,
        sha256="a" * 64,
        pages=(SourcePage(1, 100.0, 100.0),),
        family=AnswerKeyFamily.NATIVE_REGULAR_PAIRED_GRID,
        edition=AnswerKeyEdition.INITIAL,
        availability=OfficialKeyAvailability.AVAILABLE,
    )
    value = RawSourceValue(
        raw_representation="1",
        provenance=(
            SourceRegionProvenance(
                source_filename="synthetic.pdf",
                page_number=1,
                bbox=BBox(10.0, 10.0, 10.0, 20.0),
                kind=ProvenanceKind.TEXT,
                extraction_method=EXTRACTION_METHOD,
                source_text="1",
            ),
        ),
    )

    errors = validate_raw_source_value(value, source=source, entity_id="synthetic")

    assert {error.code for error in errors} == {"KEY_PROVENANCE_BBOX"}
