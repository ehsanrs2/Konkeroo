"""Local-only key-excluded packets from confirmed M3 staging databases."""

import argparse
import hashlib
import json
import sqlite3
from pathlib import Path

CONFIRMED = "OWNER_CONFIRMED_TRANSCRIPTION"
FIELDS = {
    "exam_section": ("section, printed_title, directions", "section"),
    "exam_passage": ("passage_id, kind, printed_label, body, pdf_pages_json", "passage_id"),
    "exam_passage_emphasis": ("passage_id, term", "passage_id, term"),
    "exam_question": (
        "question_number, question_id, section, stem, cloze_blank_number, passage_id, pdf_page",
        "question_number",
    ),
    "exam_option": ("question_number, position, body", "question_number, position"),
}


def export_packet(database: Path, year: int, booklet: str) -> dict:
    """Return only explicit content fields; do not query keys or solutions."""
    digest = hashlib.sha256(database.read_bytes()).hexdigest()
    con = sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True)
    try:
        con.row_factory = sqlite3.Row
        con.execute("BEGIN")
        identity = con.execute(
            "SELECT exam_booklet_code, first_question, last_question FROM exam_alignment "
            "WHERE year = ?",
            (year,),
        ).fetchone()
        if identity is None or identity[0] != booklet:
            raise ValueError("Exam identity mismatch")
        review = con.execute("SELECT status FROM content_review WHERE year = ?", (year,)).fetchone()
        if review is None or review[0] != CONFIRMED:
            raise ValueError("Content not confirmed")
        pending = con.execute(
            "SELECT count(*) FROM exam_question WHERE year = ? AND content_review_status != ?",
            (year, CONFIRMED),
        ).fetchone()[0]
        if pending:
            raise ValueError("Unconfirmed questions")
        packet = {"year": year, "booklet": booklet, "source_db_sha256": digest}
        for table, (fields, order) in FIELDS.items():
            packet[table] = [
                dict(row)
                for row in con.execute(
                    f"SELECT {fields} FROM {table} WHERE year = ? ORDER BY {order}", (year,)
                )
            ]
        numbers = list(range(identity[1], identity[2] + 1))
        questions = packet["exam_question"]
        if not numbers or [q["question_number"] for q in questions] != numbers:
            raise ValueError("Unexpected question coverage")
        if len({q["question_id"] for q in questions}) != len(numbers):
            raise ValueError("Duplicate question IDs")
        expected = [(n, pos) for n in numbers for pos in range(1, 5)]
        options = packet["exam_option"]
        if [(o["question_number"], o["position"]) for o in options] != expected:
            raise ValueError("Unexpected option coverage")
        sections = {s["section"] for s in packet["exam_section"]}
        passages = {p["passage_id"]: p["kind"] for p in packet["exam_passage"]}
        for q in questions:
            section = q["section"]
            passage = q["passage_id"]
            if section not in sections:
                raise ValueError("Unknown section")
            if section == "vocabulary":
                if passage is not None or not q["stem"] or q["cloze_blank_number"] is not None:
                    raise ValueError("Invalid vocabulary question")
            elif section in {"reading", "cloze"}:
                if passages.get(passage) != section:
                    raise ValueError("Invalid passage association")
                if section == "reading" and (not q["stem"] or q["cloze_blank_number"] is not None):
                    raise ValueError("Invalid reading question")
                if section == "cloze" and (
                    q["stem"] is not None or q["cloze_blank_number"] != q["question_number"]
                ):
                    raise ValueError("Invalid cloze question")
            else:
                raise ValueError("Unsupported section")
        if any(e["passage_id"] not in passages for e in packet["exam_passage_emphasis"]):
            raise ValueError("Unknown emphasized passage")
    finally:
        con.close()
    if hashlib.sha256(database.read_bytes()).hexdigest() != digest:
        raise ValueError("Database changed during export")
    return packet


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("database", type=Path)
    parser.add_argument("year", type=int)
    parser.add_argument("booklet")
    parser.add_argument("output", type=Path, help="New private JSON file outside public Git")
    args = parser.parse_args()
    packet = export_packet(args.database, args.year, args.booklet)
    with args.output.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(packet, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
