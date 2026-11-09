"""Parser-independent models for staged official answer keys."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from english_exam.domain import BBox, DatasetState, ValidationReport


class MediaType(StrEnum):
    PDF = "PDF"
    JPEG = "JPEG"


class OfficialKeyAvailability(StrEnum):
    AVAILABLE = "AVAILABLE"
    NO_OFFICIAL_KEY = "NO_OFFICIAL_KEY"


class AnswerKeyEdition(StrEnum):
    INITIAL = "INITIAL"
    UNSPECIFIED = "UNSPECIFIED"


class AnswerKeyFamily(StrEnum):
    NATIVE_REGULAR_PAIRED_GRID = "NATIVE_REGULAR_PAIRED_GRID"


class AnswerDisposition(StrEnum):
    ANSWERED = "ANSWERED"
    DELETED = "DELETED"
    BLANK = "BLANK"
    SPECIAL = "SPECIAL"


class ProvenanceKind(StrEnum):
    TEXT = "TEXT"
    VISUAL = "VISUAL"


class RecognitionStatus(StrEnum):
    NOT_REQUIRED = "NOT_REQUIRED"
    RECOGNIZED = "RECOGNIZED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    VERIFIED = "VERIFIED"


@dataclass(frozen=True, slots=True)
class SourcePage:
    page_number: int
    width: float
    height: float
    units: str = "pt"
    origin: str = "top-left"


@dataclass(frozen=True, slots=True)
class SourceRegionProvenance:
    source_filename: str
    page_number: int
    bbox: BBox
    kind: ProvenanceKind
    extraction_method: str
    source_text: str | None = None


@dataclass(frozen=True, slots=True)
class RawSourceValue:
    raw_representation: str
    provenance: tuple[SourceRegionProvenance, ...]
    recognition_status: RecognitionStatus = RecognitionStatus.NOT_REQUIRED
    confidence: float | None = None


@dataclass(frozen=True, slots=True)
class AnswerKeyAnnotation:
    value: RawSourceValue


@dataclass(frozen=True, slots=True)
class AnswerKeyEntry:
    question_number: int
    raw_question_number: RawSourceValue
    raw_answer: RawSourceValue
    accepted_choice_positions: tuple[int, ...]
    disposition: AnswerDisposition
    annotations: tuple[AnswerKeyAnnotation, ...] = ()


@dataclass(frozen=True, slots=True)
class AnswerKeyVariant:
    id: str
    booklet_code: str | None
    raw_booklet_code: RawSourceValue | None
    entries: tuple[AnswerKeyEntry, ...]


@dataclass(frozen=True, slots=True)
class KeySourceDescriptor:
    canonical_exam_id: str
    year: int
    source_filename: str
    media_type: MediaType
    sha256: str
    pages: tuple[SourcePage, ...]
    family: AnswerKeyFamily
    edition: AnswerKeyEdition
    availability: OfficialKeyAvailability


@dataclass(frozen=True, slots=True)
class AnswerKeyGeneratorInfo:
    name: str
    version: str
    extraction_method: str
    pdfplumber_version: str
    pdfminer_version: str


@dataclass(frozen=True, slots=True)
class AnswerKeyDataset:
    schema_version: str
    state: DatasetState
    generator: AnswerKeyGeneratorInfo
    source: KeySourceDescriptor
    variants: tuple[AnswerKeyVariant, ...]
    validation: ValidationReport
