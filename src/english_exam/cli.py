"""Command-line interface for deterministic exam and answer-key extraction."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from english_exam.answer_keys.pipeline import extract_staged_key
from english_exam.pipeline import extract_staged_1396
from english_exam.serialization import to_json, write_json_atomic


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="english-exam")
    commands = parser.add_subparsers(dest="command", required=True)
    extract = commands.add_parser("extract", help="extract a staged English exam dataset")
    extract.add_argument("--year", type=int, required=True)
    extract.add_argument("--source", type=Path, required=True)
    extract.add_argument("--output", type=Path, required=True)
    extract.add_argument("--force", action="store_true")

    key = commands.add_parser("key", help="work with official answer-key sources")
    key_commands = key.add_subparsers(dest="key_command", required=True)
    key_extract = key_commands.add_parser(
        "extract",
        help="extract a staged answer-key dataset independently from an exam",
    )
    key_extract.add_argument("--exam-id", required=True)
    key_extract.add_argument("--source", type=Path, required=True)
    key_extract.add_argument("--output", type=Path, required=True)
    key_extract.add_argument("--force", action="store_true")
    return parser


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _repository_source_directory() -> Path:
    project_root = Path(__file__).resolve().parents[2]
    if not (project_root / "pyproject.toml").is_file():
        raise RuntimeError(f"cannot resolve project root from {__file__}")
    return (project_root / "source").resolve()


def _extractor_for(args: argparse.Namespace) -> Callable[[Path], Any] | None:
    if args.command == "extract":
        if args.year != 1396:
            print("only the 1396 fixture is supported", file=sys.stderr)
            return None
        return extract_staged_1396
    if args.command == "key" and args.key_command == "extract":
        return lambda source: extract_staged_key(args.exam_id, source)
    return None


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    extractor = _extractor_for(args)
    if extractor is None:
        return 2

    source = args.source.resolve()
    output = args.output.resolve()
    if _is_relative_to(output, _repository_source_directory()):
        print("output must not be written under source/", file=sys.stderr)
        return 2

    try:
        staged = extractor(source)
        if staged.validation.errors:
            for issue in staged.validation.errors:
                print(f"ERROR {issue.code}: {issue.message}", file=sys.stderr)
            return 1
        write_json_atomic(output, to_json(staged), force=args.force)
    except (FileExistsError, OSError, RuntimeError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 1

    for issue in staged.validation.warnings:
        print(f"WARNING {issue.code}: {issue.message}", file=sys.stderr)
    print(output)
    return 0


def entrypoint() -> None:
    raise SystemExit(main())
