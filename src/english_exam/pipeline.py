"""Orchestration for deterministic staged extraction."""

from __future__ import annotations

from importlib.metadata import version
from pathlib import Path

from english_exam import __version__
from english_exam.domain import GeneratorInfo, StagedDataset
from english_exam.importers.exam_1396 import import_exam_1396
from english_exam.pdf_layout import EXTRACTION_METHOD
from english_exam.validation import validate_exam_1396


def extract_staged_1396(source_path: Path) -> StagedDataset:
    exam, warnings = import_exam_1396(Path(source_path))
    report = validate_exam_1396(exam, parser_warnings=warnings)
    return StagedDataset(
        schema_version="1.0",
        generator=GeneratorInfo(
            name="english-exam",
            version=__version__,
            extraction_method=EXTRACTION_METHOD,
            pdfplumber_version=version("pdfplumber"),
            pdfminer_version=version("pdfminer.six"),
        ),
        exam=exam,
        validation=report,
    )
