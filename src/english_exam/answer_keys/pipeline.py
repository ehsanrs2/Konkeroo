"""Orchestration for deterministic staged answer-key extraction."""

from __future__ import annotations

from dataclasses import replace
from importlib.metadata import version
from pathlib import Path

from english_exam import __version__
from english_exam.answer_keys.catalog import get_answer_key_source
from english_exam.answer_keys.domain import AnswerKeyDataset, AnswerKeyGeneratorInfo
from english_exam.answer_keys.importers.key_1395 import import_key_1395
from english_exam.answer_keys.validation import validate_key_1395
from english_exam.domain import DatasetState, ValidationReport
from english_exam.pdf_layout import EXTRACTION_METHOD


def extract_staged_key(canonical_exam_id: str, source_path: Path) -> AnswerKeyDataset:
    """Extract a supported official key independently from staged exam content."""

    source_spec = get_answer_key_source(canonical_exam_id)
    if canonical_exam_id != "iran-ce-msc-1395":
        raise ValueError(f"no importer implemented for {canonical_exam_id}")
    source, variants, parser_issues = import_key_1395(Path(source_path), source_spec)
    staged = AnswerKeyDataset(
        schema_version="1.0",
        state=DatasetState.STAGED,
        generator=AnswerKeyGeneratorInfo(
            name="english-exam",
            version=__version__,
            extraction_method=EXTRACTION_METHOD,
            pdfplumber_version=version("pdfplumber"),
            pdfminer_version=version("pdfminer.six"),
        ),
        source=source,
        variants=variants,
        validation=ValidationReport(
            fixture="1395-answer-key",
            status="PENDING",
            errors=(),
            warnings=(),
        ),
    )
    report = validate_key_1395(
        staged,
        source_spec=source_spec,
        parser_issues=parser_issues,
    )
    return replace(staged, validation=report)
