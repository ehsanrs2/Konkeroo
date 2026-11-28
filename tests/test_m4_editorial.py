import pytest

from english_exam.m4_editorial import EducationalEdit, text_sha256


def test_edit_preserves_source_and_uses_exact_occurrence():
    source = "α and and β; and and γ"
    edit = EducationalEdit(text_sha256(source), 2, "and ", "")
    assert edit.apply(source) == "α and β; and and γ"
    assert source == "α and and β; and and γ"
    assert edit.apply(source) == edit.apply(source)


def test_stale_revision_rejected():
    edit = EducationalEdit(text_sha256("abc"), 1, "b", "x")
    with pytest.raises(ValueError, match="revision mismatch"):
        edit.apply("abd")


@pytest.mark.parametrize(
    ("start", "original", "replacement", "message"),
    [
        (-1, "a", "x", "span mismatch"),
        (3, "a", "x", "span mismatch"),
        (0, "b", "x", "span mismatch"),
        (0, "", "x", "unchanged edit"),
        (0, "a", "a", "unchanged edit"),
    ],
)
def test_invalid_edits_rejected(start, original, replacement, message):
    edit = EducationalEdit(text_sha256("abc"), start, original, replacement)
    with pytest.raises(ValueError, match=message):
        edit.apply("abc")
