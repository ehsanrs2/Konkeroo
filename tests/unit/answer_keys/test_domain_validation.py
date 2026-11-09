from dataclasses import replace

from english_exam.answer_keys.catalog import AnswerKeySourceSpec
from english_exam.answer_keys.domain import (
    AnswerDisposition,
    AnswerKeyDataset,
    AnswerKeyEdition,
    AnswerKeyEntry,
    AnswerKeyFamily,
    AnswerKeyGeneratorInfo,
    AnswerKeyVariant,
    KeySourceDescriptor,
    MediaType,
    OfficialKeyAvailability,
    ProvenanceKind,
    RawSourceValue,
    RecognitionStatus,
    SourcePage,
    SourceRegionProvenance,
)
from english_exam.answer_keys.validation import validate_answer_key
from english_exam.domain import BBox, DatasetState, ValidationReport
from english_exam.pdf_layout import EXTRACTION_METHOD


def _source_value(raw: str, *, x0: float = 10.0) -> RawSourceValue:
    return RawSourceValue(
        raw_representation=raw,
        provenance=(
            SourceRegionProvenance(
                source_filename="synthetic-key.pdf",
                page_number=1,
                bbox=BBox(x0, 10.0, x0 + 5.0, 20.0),
                kind=ProvenanceKind.TEXT,
                extraction_method=EXTRACTION_METHOD,
                source_text=raw,
            ),
        ),
        recognition_status=RecognitionStatus.NOT_REQUIRED,
    )


SPEC = AnswerKeySourceSpec(
    canonical_exam_id="synthetic-exam",
    year=1,
    source_filename="synthetic-key.pdf",
    media_type=MediaType.PDF,
    expected_sha256="a" * 64,
    expected_page_count=1,
    family=AnswerKeyFamily.NATIVE_REGULAR_PAIRED_GRID,
    edition=AnswerKeyEdition.INITIAL,
    availability=OfficialKeyAvailability.AVAILABLE,
)


def _dataset() -> AnswerKeyDataset:
    entry = AnswerKeyEntry(
        question_number=1,
        raw_question_number=_source_value("1"),
        raw_answer=_source_value("2", x0=20.0),
        accepted_choice_positions=(2,),
        disposition=AnswerDisposition.ANSWERED,
    )
    return AnswerKeyDataset(
        schema_version="1.0",
        state=DatasetState.STAGED,
        generator=AnswerKeyGeneratorInfo(
            name="test",
            version="0",
            extraction_method=EXTRACTION_METHOD,
            pdfplumber_version="0",
            pdfminer_version="0",
        ),
        source=KeySourceDescriptor(
            canonical_exam_id=SPEC.canonical_exam_id,
            year=SPEC.year,
            source_filename=SPEC.source_filename,
            media_type=SPEC.media_type,
            sha256=SPEC.expected_sha256,
            pages=(SourcePage(1, 100.0, 100.0),),
            family=SPEC.family,
            edition=SPEC.edition,
            availability=SPEC.availability,
        ),
        variants=(AnswerKeyVariant("booklet-A", "A", _source_value("A"), (entry,)),),
        validation=ValidationReport("synthetic", "PENDING", (), ()),
    )


def _codes(dataset: AnswerKeyDataset) -> set[str]:
    return {issue.code for issue in validate_answer_key(dataset, source_spec=SPEC).errors}


def test_generic_answer_key_is_valid() -> None:
    assert not _codes(_dataset())


def test_rejects_duplicate_question_numbers() -> None:
    dataset = _dataset()
    variant = dataset.variants[0]
    changed = replace(variant, entries=(variant.entries[0], variant.entries[0]))

    assert "KEY_DUPLICATE_QUESTIONS" in _codes(replace(dataset, variants=(changed,)))


def test_rejects_invalid_accepted_positions() -> None:
    dataset = _dataset()
    variant = dataset.variants[0]
    entry = replace(variant.entries[0], accepted_choice_positions=(2, 2))

    assert "KEY_ACCEPTED_POSITIONS" in _codes(
        replace(dataset, variants=(replace(variant, entries=(entry,)),))
    )


def test_rejects_nonanswer_with_ordinary_position() -> None:
    dataset = _dataset()
    variant = dataset.variants[0]
    entry = replace(variant.entries[0], disposition=AnswerDisposition.DELETED)

    assert "KEY_NONANSWER_WITH_POSITION" in _codes(
        replace(dataset, variants=(replace(variant, entries=(entry,)),))
    )


def test_rejects_empty_and_inconsistent_raw_provenance() -> None:
    dataset = _dataset()
    variant = dataset.variants[0]
    entry = variant.entries[0]
    provenance = replace(entry.raw_answer.provenance[0], source_text="different")
    raw_answer = replace(entry.raw_answer, raw_representation="", provenance=(provenance,))
    changed = replace(variant, entries=(replace(entry, raw_answer=raw_answer),))

    codes = _codes(replace(dataset, variants=(changed,)))
    assert {"KEY_RAW_VALUE", "KEY_PROVENANCE_FRAGMENT"} <= codes


def test_rejects_bad_source_page_method_and_bbox() -> None:
    dataset = _dataset()
    variant = dataset.variants[0]
    entry = variant.entries[0]
    provenance = replace(
        entry.raw_answer.provenance[0],
        page_number=0,
        extraction_method="",
        bbox=BBox(20.0, 10.0, 20.0, 20.0),
    )
    changed = replace(
        variant,
        entries=(replace(entry, raw_answer=replace(entry.raw_answer, provenance=(provenance,))),),
    )

    codes = _codes(replace(dataset, variants=(changed,)))
    assert {"KEY_PROVENANCE_PAGE", "KEY_PROVENANCE_METHOD"} <= codes
