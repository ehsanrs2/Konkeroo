import json
from dataclasses import replace
from hashlib import sha256
from pathlib import Path

import pytest

from english_exam.domain import AnswerRecord, AnswerStatus
from english_exam.pipeline import extract_staged_1396
from english_exam.serialization import sha256_text, to_json
from english_exam.validation import all_questions, validate_exam_1396

ROOT = Path(__file__).parents[2]
SOURCE = ROOT / "source" / "96.pdf"
MANIFEST = ROOT / "dataset" / "staged" / "1396.manifest.json"

pytestmark = pytest.mark.source_pdf


@pytest.fixture(scope="module")
def staged():
    if not SOURCE.exists():
        pytest.skip("local immutable source/96.pdf is unavailable")
    return extract_staged_1396(SOURCE)


def _replace_first_vocabulary_question(exam, question):
    vocabulary, cloze, reading = exam.sections
    changed = replace(vocabulary, questions=(question, *vocabulary.questions[1:]))
    return replace(exam, sections=(changed, cloze, reading))


def _replace_first_marker_provenance(exam, **changes):
    question = exam.sections[0].questions[0]
    provenance = replace(question.raw_number_marker.provenance[0], **changes)
    marker = replace(question.raw_number_marker, provenance=(provenance,))
    return _replace_first_vocabulary_question(
        exam,
        replace(question, raw_number_marker=marker),
    )


def _error_codes(exam) -> set[str]:
    return {issue.code for issue in validate_exam_1396(exam).errors}


def test_real_pdf_structure_and_relationships(staged) -> None:
    assert staged.validation.status == "PASSED"
    assert not staged.validation.errors
    assert [section.id for section in staged.exam.sections] == [
        "vocabulary",
        "cloze",
        "reading",
    ]

    questions = all_questions(staged.exam)
    assert sorted(question.number for question in questions) == list(range(1, 31))
    assert all(
        [choice.position for choice in question.choices] == [1, 2, 3, 4] for question in questions
    )

    reading = staged.exam.sections[2]
    assert {
        passage.id: [question.number for question in passage.questions]
        for passage in reading.passages
    } == {
        "reading-1": [16, 17, 18, 19, 20],
        "reading-2": [21, 22, 23, 24, 25],
        "reading-3": [26, 27, 28, 29, 30],
    }


def test_real_pdf_preserves_raw_errors_and_provenance(staged) -> None:
    questions = {question.number: question for question in all_questions(staged.exam)}
    assert questions[1].raw_number_marker.raw_text == "I·"
    assert "mighl" in questions[1].stem.raw_text
    assert "try 10 control" in questions[5].stem.raw_text
    assert questions[15].raw_number_marker.raw_text == "t 5-"
    assert questions[18].raw_number_marker.raw_text == "IS.-"
    assert "11nragrn11h" in questions[30].stem.raw_text

    for question in questions.values():
        assert question.raw_number_marker.provenance
        assert all(
            item.source_filename == "96.pdf" for item in question.raw_number_marker.provenance
        )
        assert all(2 <= item.page_number <= 5 for item in question.raw_number_marker.provenance)


def test_fixture_validator_detects_bad_choice_count(staged) -> None:
    vocabulary, cloze, reading = staged.exam.sections
    bad_question = replace(vocabulary.questions[0], choices=vocabulary.questions[0].choices[:3])
    bad_vocabulary = replace(
        vocabulary,
        questions=(bad_question, *vocabulary.questions[1:]),
    )
    bad_exam = replace(staged.exam, sections=(bad_vocabulary, cloze, reading))

    report = validate_exam_1396(bad_exam)

    assert report.status == "FAILED"
    assert any(issue.code == "CHOICE_COUNT" for issue in report.errors)


def test_generation_matches_compact_manifest(staged) -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    text = to_json(staged)

    assert staged.exam.source_document.sha256 == manifest["source_sha256"]
    assert sha256_text(text) == manifest["artifact_sha256"]
    assert manifest["question_count"] == 30
    assert manifest["reading_question_ranges"] == {
        "reading-1": [16, 17, 18, 19, 20],
        "reading-2": [21, 22, 23, 24, 25],
        "reading-3": [26, 27, 28, 29, 30],
    }


def test_import_does_not_modify_source() -> None:
    if not SOURCE.exists():
        pytest.skip("local immutable source/96.pdf is unavailable")
    before_hash = sha256(SOURCE.read_bytes()).hexdigest()
    before_stat = SOURCE.stat()

    extract_staged_1396(SOURCE)

    after_stat = SOURCE.stat()
    assert sha256(SOURCE.read_bytes()).hexdigest() == before_hash
    assert after_stat.st_size == before_stat.st_size
    assert after_stat.st_mtime_ns == before_stat.st_mtime_ns


def test_real_pdf_substring_provenance_is_precise(staged) -> None:
    questions = {question.number: question for question in all_questions(staged.exam)}

    vocabulary_blank = questions[1].blank.marker
    vocabulary_line = next(
        item for item in questions[1].stem.provenance if vocabulary_blank.raw_text in item.raw_text
    )
    vocabulary_box = vocabulary_blank.provenance[0].bbox
    assert vocabulary_blank.provenance[0].raw_text == vocabulary_blank.raw_text
    assert (
        vocabulary_line.bbox.x0 <= vocabulary_box.x0 < vocabulary_box.x1 <= vocabulary_line.bbox.x1
    )
    assert vocabulary_box.x1 - vocabulary_box.x0 < vocabulary_line.bbox.x1 - vocabulary_line.bbox.x0

    question_9 = questions[9]
    q9_marker = question_9.choices[0].raw_marker.provenance[0]
    q9_text = question_9.choices[0].text.provenance[0]
    assert (q9_marker.raw_text, q9_text.raw_text) == ("!)", "justify")
    assert q9_marker.bbox.x1 == q9_text.bbox.x0
    assert q9_marker.bbox != q9_text.bbox

    question_15 = questions[15]
    for position, expected in ((3, ("3)", "in")), (4, ("4)", "to"))):
        choice = question_15.choices[position - 1]
        marker = choice.raw_marker.provenance[0]
        choice_text = choice.text.provenance[0]
        assert (marker.raw_text, choice_text.raw_text) == expected
        assert marker.bbox.x1 == choice_text.bbox.x0
        assert marker.bbox != choice_text.bbox

    cloze_passage = staged.exam.sections[1].passages[0]
    cloze_blank = questions[11].blank.marker
    cloze_line = next(
        item for item in cloze_passage.body.provenance if cloze_blank.raw_text in item.raw_text
    )
    cloze_box = cloze_blank.provenance[0].bbox
    assert cloze_blank.provenance[0].raw_text == cloze_blank.raw_text
    assert cloze_line.bbox.x0 <= cloze_box.x0 < cloze_box.x1 <= cloze_line.bbox.x1
    assert cloze_box.x1 - cloze_box.x0 < cloze_line.bbox.x1 - cloze_line.bbox.x0


def test_fixture_validator_detects_duplicate_question_number(staged) -> None:
    vocabulary, cloze, reading = staged.exam.sections
    duplicate = replace(vocabulary.questions[1], number=1)
    changed = replace(
        vocabulary,
        questions=(vocabulary.questions[0], duplicate, *vocabulary.questions[2:]),
    )

    codes = _error_codes(replace(staged.exam, sections=(changed, cloze, reading)))

    assert "DUPLICATE_QUESTIONS" in codes


def test_fixture_validator_detects_missing_question_number(staged) -> None:
    vocabulary, cloze, reading = staged.exam.sections
    changed = replace(vocabulary, questions=vocabulary.questions[:-1])

    codes = _error_codes(replace(staged.exam, sections=(changed, cloze, reading)))

    assert "QUESTION_RANGE" in codes


def test_fixture_validator_detects_broken_reading_relationship(staged) -> None:
    vocabulary, cloze, reading = staged.exam.sections
    first, second, third = reading.passages
    reordered = replace(
        first,
        questions=(*first.questions[:3], first.questions[4], first.questions[3]),
    )
    changed = replace(reading, passages=(reordered, second, third))

    codes = _error_codes(replace(staged.exam, sections=(vocabulary, cloze, changed)))

    assert "READING_RELATIONSHIP" in codes
    assert "DUPLICATE_QUESTIONS" not in codes
    assert "QUESTION_RANGE" not in codes


@pytest.mark.parametrize("answer_field", ["official", "final_verified"])
def test_fixture_validator_rejects_answers_in_staged_content(staged, answer_field) -> None:
    question = staged.exam.sections[0].questions[0]
    answer = AnswerRecord(
        accepted_choice_positions=(1,),
        status=AnswerStatus.ACCEPTED,
    )
    answers = replace(question.answers, **{answer_field: answer})
    changed = _replace_first_vocabulary_question(staged.exam, replace(question, answers=answers))

    assert "UNEXPECTED_ANSWER" in _error_codes(changed)


def test_fixture_validator_rejects_inconsistent_provenance_source(staged) -> None:
    changed = _replace_first_marker_provenance(staged.exam, source_filename="other.pdf")

    assert "PROVENANCE_SOURCE" in _error_codes(changed)


def test_fixture_validator_rejects_nonpositive_page_number(staged) -> None:
    changed = _replace_first_marker_provenance(staged.exam, page_number=0)

    codes = _error_codes(changed)
    assert "PROVENANCE_PAGE_NUMBER" in codes
    assert "PROVENANCE_PAGE" not in codes


def test_fixture_validator_rejects_page_outside_english_section(staged) -> None:
    changed = _replace_first_marker_provenance(staged.exam, page_number=6)

    codes = _error_codes(changed)
    assert "PROVENANCE_PAGE" in codes
    assert "PROVENANCE_PAGE_NUMBER" not in codes


@pytest.mark.parametrize("method", ["", "UNSUPPORTED_METHOD"])
def test_fixture_validator_rejects_unsupported_extraction_method(staged, method) -> None:
    changed = _replace_first_marker_provenance(staged.exam, extraction_method=method)

    assert "PROVENANCE_METHOD" in _error_codes(changed)


def test_fixture_validator_rejects_malformed_bbox(staged) -> None:
    item = staged.exam.sections[0].questions[0].raw_number_marker.provenance[0]
    changed = _replace_first_marker_provenance(
        staged.exam,
        bbox=replace(item.bbox, x1=item.bbox.x0),
    )

    assert "PROVENANCE_BBOX" in _error_codes(changed)


def test_fixture_validator_rejects_empty_provenance_raw_text(staged) -> None:
    changed = _replace_first_marker_provenance(staged.exam, raw_text="")

    assert "PROVENANCE_RAW_TEXT" in _error_codes(changed)


def test_fixture_validator_rejects_inconsistent_provenance_fragment(staged) -> None:
    changed = _replace_first_marker_provenance(staged.exam, raw_text="different")

    assert "PROVENANCE_FRAGMENT" in _error_codes(changed)
