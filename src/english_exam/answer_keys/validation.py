"""Generic and 1395-specific validation for staged official keys."""

from __future__ import annotations

import re
from collections import Counter
from math import isfinite

from english_exam.answer_keys.catalog import AnswerKeySourceSpec
from english_exam.answer_keys.digits import parse_unsigned_integer
from english_exam.answer_keys.domain import (
    AnswerDisposition,
    AnswerKeyDataset,
    KeySourceDescriptor,
    ProvenanceKind,
    RawSourceValue,
    RecognitionStatus,
)
from english_exam.domain import ExtractionIssue, IssueSeverity, ValidationReport
from english_exam.pdf_layout import SUPPORTED_EXTRACTION_METHODS

_LATIN_DIGITS = re.compile(r"[0-9]+", flags=re.ASCII)


def _issue(code: str, message: str, entity_id: str | None = None) -> ExtractionIssue:
    return ExtractionIssue(
        code=code,
        severity=IssueSeverity.ERROR,
        message=message,
        entity_id=entity_id,
    )


def _page_for(source: KeySourceDescriptor, page_number: int):
    return next((page for page in source.pages if page.page_number == page_number), None)


def validate_raw_source_value(
    value: RawSourceValue,
    *,
    source: KeySourceDescriptor,
    entity_id: str,
) -> tuple[ExtractionIssue, ...]:
    errors: list[ExtractionIssue] = []
    if not value.raw_representation:
        errors.append(_issue("KEY_RAW_VALUE", "raw representation is empty", entity_id))
    if not value.provenance:
        errors.append(_issue("KEY_PROVENANCE", "source value has no provenance", entity_id))
        return tuple(errors)

    native_fragments: list[str] = []
    for item in value.provenance:
        if item.source_filename != source.source_filename:
            errors.append(
                _issue(
                    "KEY_PROVENANCE_SOURCE",
                    f"provenance source {item.source_filename!r} does not match key source",
                    entity_id,
                )
            )
        page = _page_for(source, item.page_number)
        if page is None:
            errors.append(
                _issue(
                    "KEY_PROVENANCE_PAGE",
                    f"invalid 1-based source page {item.page_number!r}",
                    entity_id,
                )
            )
        else:
            box = item.bbox
            try:
                finite = all(isfinite(number) for number in (box.x0, box.y0, box.x1, box.y1))
            except TypeError:
                finite = False
            if not (
                finite
                and box.units == page.units
                and box.origin == page.origin
                and 0 <= box.x0 < box.x1 <= page.width + 0.01
                and 0 <= box.y0 < box.y1 <= page.height + 0.01
            ):
                errors.append(
                    _issue("KEY_PROVENANCE_BBOX", "invalid source bounding box", entity_id)
                )
        if item.extraction_method not in SUPPORTED_EXTRACTION_METHODS:
            errors.append(
                _issue(
                    "KEY_PROVENANCE_METHOD",
                    f"unsupported extraction method {item.extraction_method!r}",
                    entity_id,
                )
            )
        if item.kind is ProvenanceKind.TEXT:
            if not item.source_text:
                errors.append(
                    _issue("KEY_PROVENANCE_TEXT", "native source text is empty", entity_id)
                )
            else:
                native_fragments.append(item.source_text)
        elif item.source_text is not None:
            errors.append(
                _issue(
                    "KEY_VISUAL_SOURCE_TEXT",
                    "visual provenance must not pretend to contain native text",
                    entity_id,
                )
            )

    if native_fragments and "\n".join(native_fragments) != value.raw_representation:
        errors.append(
            _issue(
                "KEY_PROVENANCE_FRAGMENT",
                "native provenance does not reconstruct the raw representation",
                entity_id,
            )
        )
    if value.recognition_status is RecognitionStatus.NOT_REQUIRED:
        if value.confidence is not None:
            errors.append(
                _issue(
                    "KEY_NATIVE_CONFIDENCE",
                    "native text must not carry recognition confidence",
                    entity_id,
                )
            )
        if any(item.kind is not ProvenanceKind.TEXT for item in value.provenance):
            errors.append(
                _issue(
                    "KEY_NATIVE_PROVENANCE_KIND",
                    "recognition-free values require text provenance",
                    entity_id,
                )
            )
    elif value.confidence is not None and not 0 <= value.confidence <= 1:
        errors.append(
            _issue("KEY_RECOGNITION_CONFIDENCE", "confidence must be between 0 and 1", entity_id)
        )
    return tuple(errors)


def validate_answer_key(
    dataset: AnswerKeyDataset,
    *,
    source_spec: AnswerKeySourceSpec,
    parser_issues: tuple[ExtractionIssue, ...] = (),
) -> ValidationReport:
    errors: list[ExtractionIssue] = list(parser_issues)
    source = dataset.source

    if source.canonical_exam_id != source_spec.canonical_exam_id:
        errors.append(_issue("KEY_SOURCE_ID", "canonical source identity does not match catalog"))
    if source.year != source_spec.year:
        errors.append(_issue("KEY_SOURCE_YEAR", "source year does not match catalog"))
    if source.source_filename != source_spec.source_filename:
        errors.append(_issue("KEY_SOURCE_FILENAME", "source filename does not match catalog"))
    if source.sha256 != source_spec.expected_sha256:
        errors.append(_issue("KEY_SOURCE_HASH", "source hash does not match catalog"))
    if source.media_type != source_spec.media_type:
        errors.append(_issue("KEY_SOURCE_MEDIA_TYPE", "source media type does not match catalog"))
    if len(source.pages) != source_spec.expected_page_count:
        errors.append(_issue("KEY_SOURCE_PAGE_COUNT", "source page count does not match catalog"))
    if source.family != source_spec.family or source.edition != source_spec.edition:
        errors.append(_issue("KEY_SOURCE_CLASSIFICATION", "source classification is inconsistent"))
    if source.availability != source_spec.availability:
        errors.append(_issue("KEY_SOURCE_AVAILABILITY", "source availability is inconsistent"))

    page_numbers = tuple(page.page_number for page in source.pages)
    if page_numbers != tuple(range(1, len(source.pages) + 1)):
        errors.append(_issue("KEY_SOURCE_PAGES", "source pages must be unique and 1-based"))
    for page in source.pages:
        if not (
            page.width > 0
            and page.height > 0
            and isfinite(page.width)
            and isfinite(page.height)
            and page.units == "pt"
            and page.origin == "top-left"
        ):
            errors.append(_issue("KEY_SOURCE_PAGE_GEOMETRY", "invalid source page geometry"))

    variant_ids = tuple(variant.id for variant in dataset.variants)
    if len(set(variant_ids)) != len(variant_ids) or any(not value for value in variant_ids):
        errors.append(_issue("KEY_VARIANT_IDS", "variant IDs must be nonempty and unique"))
    booklet_codes = tuple(
        variant.booklet_code for variant in dataset.variants if variant.booklet_code is not None
    )
    if len(set(booklet_codes)) != len(booklet_codes) or any(not value for value in booklet_codes):
        errors.append(_issue("KEY_BOOKLET_CODES", "booklet codes must be nonempty and unique"))

    for variant in dataset.variants:
        if variant.raw_booklet_code is not None:
            errors.extend(
                validate_raw_source_value(
                    variant.raw_booklet_code,
                    source=source,
                    entity_id=variant.id,
                )
            )
        numbers = tuple(entry.question_number for entry in variant.entries)
        duplicates = tuple(
            sorted(number for number, count in Counter(numbers).items() if count > 1)
        )
        if duplicates:
            errors.append(
                _issue(
                    "KEY_DUPLICATE_QUESTIONS",
                    f"duplicate question numbers: {duplicates}",
                    variant.id,
                )
            )
        for entry in variant.entries:
            entity_id = f"{variant.id}:question-{entry.question_number}"
            errors.extend(
                validate_raw_source_value(
                    entry.raw_question_number,
                    source=source,
                    entity_id=f"{entity_id}:number",
                )
            )
            errors.extend(
                validate_raw_source_value(
                    entry.raw_answer,
                    source=source,
                    entity_id=f"{entity_id}:answer",
                )
            )
            try:
                parsed_number = parse_unsigned_integer(entry.raw_question_number.raw_representation)
            except ValueError:
                parsed_number = None
            if parsed_number != entry.question_number:
                errors.append(
                    _issue(
                        "KEY_QUESTION_NORMALIZATION",
                        "normalized question does not match its raw representation",
                        entity_id,
                    )
                )
            positions = entry.accepted_choice_positions
            if positions != tuple(sorted(set(positions))) or any(value <= 0 for value in positions):
                errors.append(
                    _issue(
                        "KEY_ACCEPTED_POSITIONS",
                        "accepted positions must be positive, sorted, and unique",
                        entity_id,
                    )
                )
            if entry.disposition is AnswerDisposition.ANSWERED and not positions:
                errors.append(
                    _issue(
                        "KEY_ANSWERED_WITHOUT_POSITION", "answered entry has no position", entity_id
                    )
                )
            if entry.disposition is not AnswerDisposition.ANSWERED and positions:
                errors.append(
                    _issue(
                        "KEY_NONANSWER_WITH_POSITION",
                        "non-answer disposition carries ordinary positions",
                        entity_id,
                    )
                )
            for annotation in entry.annotations:
                errors.extend(
                    validate_raw_source_value(
                        annotation.value,
                        source=source,
                        entity_id=f"{entity_id}:annotation",
                    )
                )

    return ValidationReport(
        fixture="answer-key-generic",
        status="PASSED" if not errors else "FAILED",
        errors=tuple(errors),
        warnings=(),
    )


def validate_key_1395(
    dataset: AnswerKeyDataset,
    *,
    source_spec: AnswerKeySourceSpec,
    parser_issues: tuple[ExtractionIssue, ...] = (),
) -> ValidationReport:
    generic = validate_answer_key(
        dataset,
        source_spec=source_spec,
        parser_issues=parser_issues,
    )
    errors = list(generic.errors)
    source = dataset.source
    if tuple((page.width, page.height) for page in source.pages) != ((612.0, 792.0),):
        errors.append(_issue("KEY_1395_PAGE_SIZE", "expected one 612x792 point page"))
    if len(dataset.variants) != 1:
        errors.append(_issue("KEY_1395_VARIANT_COUNT", "expected exactly one booklet variant"))
    else:
        variant = dataset.variants[0]
        if variant.id != "booklet-A" or variant.booklet_code != "A":
            errors.append(_issue("KEY_1395_BOOKLET", "expected booklet A", variant.id))
        numbers = tuple(entry.question_number for entry in variant.entries)
        if numbers != tuple(range(1, 122)):
            errors.append(
                _issue("KEY_1395_QUESTION_RANGE", "expected ordered questions 1-121", variant.id)
            )
        for entry in variant.entries:
            entity_id = f"{variant.id}:question-{entry.question_number}"
            if entry.disposition is not AnswerDisposition.ANSWERED:
                errors.append(_issue("KEY_1395_DISPOSITION", "expected ordinary answer", entity_id))
            if len(entry.accepted_choice_positions) != 1 or not (
                1 <= entry.accepted_choice_positions[0] <= 4
            ):
                errors.append(
                    _issue("KEY_1395_OPTION", "expected one option from 1 through 4", entity_id)
                )
            if entry.annotations:
                errors.append(_issue("KEY_1395_ANNOTATION", "unexpected annotation", entity_id))
            for value in (entry.raw_question_number, entry.raw_answer):
                if not _LATIN_DIGITS.fullmatch(value.raw_representation):
                    errors.append(
                        _issue("KEY_1395_DIGIT_SYSTEM", "expected Latin source digits", entity_id)
                    )

    return ValidationReport(
        fixture="1395-answer-key",
        status="PASSED" if not errors else "FAILED",
        errors=tuple(errors),
        warnings=generic.warnings,
    )
