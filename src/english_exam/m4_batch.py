"""Prepare private key-excluded packets for an explicit list of exam years."""

import argparse
import hashlib
import json
import sqlite3
from contextlib import closing
from pathlib import Path

from english_exam.m4_packet import export_packet


def json_bytes(value: dict) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def prepare_batch(database: Path, expected_sha256: str, years: list[int]) -> dict[str, bytes]:
    """Validate all selected packets before returning any output files."""
    if not years or len(years) != len(set(years)):
        raise ValueError("Select distinct exam years")
    digest = hashlib.sha256(database.read_bytes()).hexdigest()
    if digest != expected_sha256:
        raise ValueError("Input digest mismatch")
    with closing(sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True)) as con:
        if con.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
            raise ValueError("Database integrity failure")
        if con.execute("PRAGMA foreign_key_check").fetchone() is not None:
            raise ValueError("Foreign key violation")
        identities = dict(con.execute("SELECT year, exam_booklet_code FROM exam_alignment"))
    files = {}
    entries = []
    seen_ids = set()
    for year in sorted(years):
        if year not in identities:
            raise ValueError("Unknown exam year")
        packet = export_packet(database, year, identities[year])
        if packet["source_db_sha256"] != digest:
            raise ValueError("Input changed during export")
        ids = {q["question_id"] for q in packet["exam_question"]}
        if seen_ids.intersection(ids):
            raise ValueError("Duplicate question identity across exams")
        seen_ids.update(ids)
        name = f"packet_{year}.json"
        data = json_bytes(packet)
        files[name] = data
        entries.append(
            {
                "year": year,
                "booklet": identities[year],
                "questions": len(ids),
                "file": name,
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        )
    if hashlib.sha256(database.read_bytes()).hexdigest() != digest:
        raise ValueError("Input changed during batch")
    files["manifest.json"] = json_bytes(
        {
            "status": "PACKETS_PREPARED_NOT_SOLVED",
            "publication_status": "BLOCKED",
            "source_db_sha256": digest,
            "questions": len(seen_ids),
            "packets": entries,
        }
    )
    return files


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("database", type=Path)
    parser.add_argument("expected_sha256")
    parser.add_argument("output", type=Path, help="New private directory outside public Git")
    parser.add_argument("years", nargs="+", type=int)
    args = parser.parse_args()
    files = prepare_batch(args.database, args.expected_sha256, args.years)
    args.output.mkdir()
    for name, data in files.items():
        with (args.output / name).open("xb") as handle:
            handle.write(data)


if __name__ == "__main__":
    main()
