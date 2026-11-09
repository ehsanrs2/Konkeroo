from english_exam.answer_keys.domain import RecognitionStatus
from english_exam.serialization import to_json


def test_answer_key_serialization_is_byte_deterministic() -> None:
    value = {
        "canonical_exam_id": "synthetic-exam",
        "recognition_status": RecognitionStatus.NOT_REQUIRED,
        "accepted_choice_positions": (2,),
    }
    first = to_json(value)
    second = to_json(value)

    assert first == second
    assert '"canonical_exam_id": "synthetic-exam"' in first
