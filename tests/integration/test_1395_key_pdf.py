import json
from hashlib import sha256
from pathlib import Path

import pytest

from english_exam.answer_keys.domain import (
    AnswerDisposition,
    ProvenanceKind,
    RecognitionStatus,
)
from english_exam.answer_keys.pipeline import extract_staged_key
from english_exam.cli import main
from english_exam.pdf_layout import EXTRACTION_METHOD
from english_exam.serialization import sha256_text, to_json

ROOT = Path(__file__).parents[2]
SOURCE = ROOT / "source" / "95_Key.pdf"
MANIFEST = ROOT / "dataset" / "staged" / "1395-key.manifest.json"
EXPECTED_SOURCE_SHA256 = "298efdeb70dc84b3bf92872f96bf2f15394f617e8c9e8d6cb9364e50789b3d9b"

pytestmark = pytest.mark.source_pdf


@pytest.fixture(scope="module")
def staged():
    if not SOURCE.exists():
        pytest.skip("local immutable source/95_Key.pdf is unavailable")
    assert sha256(SOURCE.read_bytes()).hexdigest() == EXPECTED_SOURCE_SHA256
    return extract_staged_key("iran-ce-msc-1395", SOURCE)


def test_real_key_structure(staged) -> None:
    assert staged.validation.status == "PASSED"
    assert not staged.validation.errors
    assert staged.source.canonical_exam_id == "iran-ce-msc-1395"
    assert [(page.width, page.height) for page in staged.source.pages] == [(612.0, 792.0)]
    assert len(staged.variants) == 1
    variant = staged.variants[0]
    assert (variant.id, variant.booklet_code) == ("booklet-A", "A")
    assert [entry.question_number for entry in variant.entries] == list(range(1, 122))
    assert all(entry.disposition is AnswerDisposition.ANSWERED for entry in variant.entries)
    assert all(
        len(entry.accepted_choice_positions) == 1 and 1 <= entry.accepted_choice_positions[0] <= 4
        for entry in variant.entries
    )
    assert all(not entry.annotations for entry in variant.entries)


def test_real_key_representative_group_boundaries(staged) -> None:
    entries = {entry.question_number: entry for entry in staged.variants[0].entries}

    assert {
        number: entries[number].accepted_choice_positions
        for number in (1, 30, 31, 60, 61, 90, 91, 120, 121)
    } == {
        1: (1,),
        30: (3,),
        31: (2,),
        60: (3,),
        61: (4,),
        90: (1,),
        91: (2,),
        120: (1,),
        121: (3,),
    }


def test_real_key_has_tight_native_provenance(staged) -> None:
    values = [staged.variants[0].raw_booklet_code]
    for entry in staged.variants[0].entries:
        values.extend((entry.raw_question_number, entry.raw_answer))

    assert all(value is not None for value in values)
    for value in values:
        assert value.recognition_status is RecognitionStatus.NOT_REQUIRED
        assert value.confidence is None
        assert len(value.provenance) == 1
        provenance = value.provenance[0]
        assert provenance.source_filename == "95_Key.pdf"
        assert provenance.page_number == 1
        assert provenance.kind is ProvenanceKind.TEXT
        assert provenance.extraction_method == EXTRACTION_METHOD
        assert provenance.source_text == value.raw_representation
        assert 0 <= provenance.bbox.x0 < provenance.bbox.x1 <= 612
        assert 0 <= provenance.bbox.y0 < provenance.bbox.y1 <= 792
        assert provenance.bbox.x1 - provenance.bbox.x0 < 20
        assert provenance.bbox.y1 - provenance.bbox.y0 < 10


def test_generation_matches_compact_manifest(staged) -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    text = to_json(staged)

    assert manifest["source_sha256"] == EXPECTED_SOURCE_SHA256
    assert manifest["artifact_sha256"] == sha256_text(text)
    assert manifest["variant_ids"] == ["booklet-A"]
    assert manifest["entry_count"] == 121
    assert manifest["question_range"] == [1, 121]
    assert manifest["group_starts"] == [1, 31, 61, 91, 121]
    assert manifest["group_lengths"] == [30, 30, 30, 30, 1]
    assert "answers" not in manifest


def test_generation_is_byte_identical(staged) -> None:
    regenerated = extract_staged_key("iran-ce-msc-1395", SOURCE)

    assert to_json(regenerated) == to_json(staged)


def test_key_import_does_not_modify_source() -> None:
    if not SOURCE.exists():
        pytest.skip("local immutable source/95_Key.pdf is unavailable")
    before_hash = sha256(SOURCE.read_bytes()).hexdigest()
    before_stat = SOURCE.stat()

    extract_staged_key("iran-ce-msc-1395", SOURCE)

    after_stat = SOURCE.stat()
    assert sha256(SOURCE.read_bytes()).hexdigest() == before_hash
    assert after_stat.st_size == before_stat.st_size
    assert after_stat.st_mtime_ns == before_stat.st_mtime_ns


def test_key_cli_writes_independent_artifact(staged, tmp_path: Path) -> None:
    output = tmp_path / "1395-key.json"

    result = main(
        [
            "key",
            "extract",
            "--exam-id",
            "iran-ce-msc-1395",
            "--source",
            str(SOURCE),
            "--output",
            str(output),
        ]
    )

    assert result == 0
    assert output.read_text(encoding="utf-8") == to_json(staged)
