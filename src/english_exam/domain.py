"""Parser-independent domain models for staged exam data."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class DatasetState(StrEnum):
    STAGED = "STAGED"


class SectionKind(StrEnum):
    VOCABULARY = "VOCABULARY"
    CLOZE = "CLOZE"
    READING = "READING"


class QuestionKind(StrEnum):
    SENTENCE_COMPLETION = "SENTENCE_COMPLETION"
    CLOZE_BLANK = "CLOZE_BLANK"
    READING_COMPREHENSION = "READING_COMPREHENSION"


class PassageKind(StrEnum):
    CLOZE = "CLOZE"
    READING = "READING"


class AnswerStatus(StrEnum):
    UNCHECKED = "UNCHECKED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class IssueSeverity(StrEnum):
    WARNING = "WARNING"
    ERROR = "ERROR"


@dataclass(frozen=True, slots=True)
class BBox:
    x0: float
    y0: float
    x1: float
    y1: float
    units: str = "pt"
    origin: str = "top-left"


@dataclass(frozen=True, slots=True)
class SourceProvenance:
    source_filename: str
    page_number: int
    bbox: BBox
    raw_text: str
    extraction_method: str


@dataclass(frozen=True, slots=True)
class ExtractedText:
    raw_text: str
    normalized_text: str | None = None
    corrected_text: str | None = None
    provenance: tuple[SourceProvenance, ...] = ()


@dataclass(frozen=True, slots=True)
class Blank:
    marker: ExtractedText


@dataclass(frozen=True, slots=True)
class Choice:
    position: int
    raw_marker: ExtractedText
    text: ExtractedText


@dataclass(frozen=True, slots=True)
class AnswerRecord:
    accepted_choice_positions: tuple[int, ...]
    status: AnswerStatus
    confidence: float | None = None
    provenance: tuple[SourceProvenance, ...] = ()


@dataclass(frozen=True, slots=True)
class AnswerSet:
    official: AnswerRecord | None = None
    ai: AnswerRecord | None = None
    final_verified: AnswerRecord | None = None


@dataclass(frozen=True, slots=True)
class Question:
    id: str
    number: int
    raw_number_marker: ExtractedText
    kind: QuestionKind
    stem: ExtractedText | None
    blank: Blank | None
    choices: tuple[Choice, ...]
    answers: AnswerSet = field(default_factory=AnswerSet)


@dataclass(frozen=True, slots=True)
class Passage:
    id: str
    kind: PassageKind
    heading: ExtractedText | None
    body: ExtractedText
    questions: tuple[Question, ...]


@dataclass(frozen=True, slots=True)
class Section:
    id: str
    kind: SectionKind
    heading: ExtractedText
    directions: ExtractedText
    questions: tuple[Question, ...] = ()
    passages: tuple[Passage, ...] = ()


@dataclass(frozen=True, slots=True)
class SourceDocument:
    source_filename: str
    sha256: str
    page_count: int
    page_width: float
    page_height: float
    english_pdf_pages: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class Exam:
    id: str
    year: int
    state: DatasetState
    source_document: SourceDocument
    sections: tuple[Section, ...]


@dataclass(frozen=True, slots=True)
class ExtractionIssue:
    code: str
    severity: IssueSeverity
    message: str
    entity_id: str | None = None
    provenance: tuple[SourceProvenance, ...] = ()


@dataclass(frozen=True, slots=True)
class ValidationReport:
    fixture: str
    status: str
    errors: tuple[ExtractionIssue, ...]
    warnings: tuple[ExtractionIssue, ...]


@dataclass(frozen=True, slots=True)
class GeneratorInfo:
    name: str
    version: str
    extraction_method: str
    pdfplumber_version: str
    pdfminer_version: str


@dataclass(frozen=True, slots=True)
class StagedDataset:
    schema_version: str
    generator: GeneratorInfo
    exam: Exam
    validation: ValidationReport
