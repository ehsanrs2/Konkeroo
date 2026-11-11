"""Presentation-only uniform blank markers for 1396 Cloze reviewer handoffs.

This never changes the extracted PDF layer, proposed full-field text, the
review ledger or any verified-answer artifact.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from english_exam.cloze_full_preview import FullClozePreview
from english_exam.cloze_order_review import ANOMALY_ID

# The original PDF renders five gaps; its text layer encodes the leaders using
# mixed dot-and-dash glyphs. Restrict display normalization to exact identities
# and immediate source-context anchors in this one source-specific passage.
_BLANK_PATTERN = re.compile(r"\([ \t]*(?P<number>1[1-5])\)[ \t]*(?P<leader>[-·]+)")
_EXPECTED_CONTEXTS = {
    11: ("children, ", "a book"),
    12: ("humans since ", ": Plato"),
    13: ("birth ", "on the impression"),
    14: ("years, though, ", "systematic"),
    15: ("visual materials ", "more recent"),
}
_BLANK_NUMBERS = (11, 12, 13, 14, 15)


@dataclass(frozen=True, slots=True)
class ClozeBlankDisplay:
    status: str
    text: str | None
    blank_numbers: tuple[int, ...]
    errors: tuple[str, ...]


def format_1396_cloze_blanks_for_review(preview: FullClozePreview) -> ClozeBlankDisplay:
    """Render five `(N) ____` placeholders, preserving the source-field content.

    A punctuation mark adjacent to a text-layer gap (e.g. the colon after
    blank 12) is preserved, *not* declared source-verified. A synthetic
    separating space is added only when the raw leader runs into a word.
    """
    if (
        preview.status != "PENDING_FULL_FIELD_HUMAN_REVIEW"
        or preview.proposed_full_text is None
        or preview.errors
        or preview.technical_candidate_anomaly_id != ANOMALY_ID
    ):
        return ClozeBlankDisplay("BLOCKED", None, (), ("unreviewed or invalid full preview",))

    source = preview.proposed_full_text
    matches = list(_BLANK_PATTERN.finditer(source))
    numbers = tuple(int(match.group("number")) for match in matches)
    errors: list[str] = []
    if numbers != _BLANK_NUMBERS:
        errors.append("Cloze gaps must occur once each and in Q11–15 order")

    for match in matches:
        number = int(match.group("number"))
        before, after = _EXPECTED_CONTEXTS[number]
        if not source[: match.start()].endswith(before):
            errors.append(f"blank {number}: unexpected preceding context")
        if not source[match.end() :].lstrip(" \t").startswith(after):
            errors.append(f"blank {number}: unexpected following context")

    if errors:
        return ClozeBlankDisplay("BLOCKED", None, (), tuple(errors))

    # Build from the end so every replacement uses offsets from the original.
    displayed = source
    for match in reversed(matches):
        number = int(match.group("number"))
        next_character = source[match.end() : match.end() + 1]
        separator = " " if next_character.isalpha() or next_character.isdigit() else ""
        replacement = f"({number}) ____{separator}"
        displayed = displayed[: match.start()] + replacement + displayed[match.end() :]

    return ClozeBlankDisplay(
        status="PENDING_BLANK_DISPLAY_REVIEW",
        text=displayed,
        blank_numbers=numbers,
        errors=(),
    )
