"""Layout-aware PDF extraction built on permissively licensed pdfplumber."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from statistics import mean

import pdfplumber

from english_exam.domain import BBox, ExtractedText, SourceProvenance

EXTRACTION_METHOD = "PDFPLUMBER_PDFMINER_TEXT_LAYER"
SUPPORTED_EXTRACTION_METHODS = frozenset({EXTRACTION_METHOD})


@dataclass(frozen=True, slots=True)
class LayoutChar:
    text: str
    bbox: BBox


@dataclass(frozen=True, slots=True)
class LayoutWord:
    text: str
    bbox: BBox
    font_name: str | None
    font_size: float | None
    chars: tuple[LayoutChar, ...] = ()


@dataclass(frozen=True, slots=True)
class TextLine:
    page_number: int
    words: tuple[LayoutWord, ...]

    @property
    def bbox(self) -> BBox:
        return union_bbox(word.bbox for word in self.words)

    @property
    def raw_text(self) -> str:
        return " ".join(word.text for word in self.words)


@dataclass(frozen=True, slots=True)
class PageLayout:
    page_number: int
    width: float
    height: float
    lines: tuple[TextLine, ...]


@dataclass(frozen=True, slots=True)
class PdfLayoutDocument:
    source_filename: str
    page_count: int
    pages: tuple[PageLayout, ...]


def union_bbox(boxes: Iterable[BBox]) -> BBox:
    collected = tuple(boxes)
    if not collected:
        raise ValueError("cannot union an empty set of bounding boxes")
    return BBox(
        x0=round(min(box.x0 for box in collected), 3),
        y0=round(min(box.y0 for box in collected), 3),
        x1=round(max(box.x1 for box in collected), 3),
        y1=round(max(box.y1 for box in collected), 3),
    )


def slice_layout_word(word: LayoutWord, start: int, end: int) -> LayoutWord:
    """Return an exact character-backed slice of a layout word."""

    if not 0 <= start < end <= len(word.text):
        raise ValueError(f"invalid word slice [{start}:{end}] for {word.text!r}")
    if start == 0 and end == len(word.text):
        return word
    if not word.chars or "".join(char.text for char in word.chars) != word.text:
        raise ValueError(f"cannot safely derive substring geometry for {word.text!r}")

    chars = word.chars[start:end]
    return LayoutWord(
        text=word.text[start:end],
        bbox=union_bbox(char.bbox for char in chars),
        font_name=word.font_name,
        font_size=word.font_size,
        chars=chars,
    )


def extracted_substring_from_words(
    words: Sequence[LayoutWord],
    *,
    start: int,
    end: int,
    source_filename: str,
    page_number: int,
) -> ExtractedText:
    """Extract a substring from geometrically ordered words without inventing a box."""

    raw_text = " ".join(word.text for word in words)
    if not 0 <= start < end <= len(raw_text):
        raise ValueError(f"invalid text slice [{start}:{end}] for {raw_text!r}")

    sliced_words: list[LayoutWord] = []
    cursor = 0
    for word in words:
        word_start = cursor
        word_end = word_start + len(word.text)
        overlap_start = max(start, word_start)
        overlap_end = min(end, word_end)
        if overlap_start < overlap_end:
            sliced_words.append(
                slice_layout_word(
                    word,
                    overlap_start - word_start,
                    overlap_end - word_start,
                )
            )
        cursor = word_end + 1

    if not sliced_words:
        raise ValueError("cannot assign geometry to a whitespace-only substring")

    fragment = raw_text[start:end]
    return ExtractedText(
        raw_text=fragment,
        provenance=(
            SourceProvenance(
                source_filename=source_filename,
                page_number=page_number,
                bbox=union_bbox(word.bbox for word in sliced_words),
                raw_text=fragment,
                extraction_method=EXTRACTION_METHOD,
            ),
        ),
    )


def group_words_into_lines(
    words: Sequence[LayoutWord],
    *,
    page_number: int,
    baseline_tolerance: float = 3.0,
) -> tuple[TextLine, ...]:
    """Group words by their visual baseline instead of PDF content-stream order."""

    clusters: list[list[LayoutWord]] = []
    baselines: list[float] = []

    for word in sorted(words, key=lambda item: (item.bbox.y1, item.bbox.x0)):
        if clusters:
            distances = [abs(word.bbox.y1 - baseline) for baseline in baselines]
            best_index = min(range(len(distances)), key=distances.__getitem__)
        else:
            best_index = -1
            distances = []

        if best_index >= 0 and distances[best_index] <= baseline_tolerance:
            clusters[best_index].append(word)
            baselines[best_index] = mean(item.bbox.y1 for item in clusters[best_index])
        else:
            clusters.append([word])
            baselines.append(word.bbox.y1)

    lines = [
        TextLine(page_number, tuple(sorted(cluster, key=lambda item: item.bbox.x0)))
        for cluster in clusters
    ]
    return tuple(sorted(lines, key=lambda line: (line.bbox.y0, line.bbox.x0)))


def extracted_text_from_lines(
    lines: Sequence[TextLine],
    *,
    source_filename: str,
) -> ExtractedText:
    if not lines:
        raise ValueError("cannot create extracted text from no lines")
    provenance = tuple(
        SourceProvenance(
            source_filename=source_filename,
            page_number=line.page_number,
            bbox=line.bbox,
            raw_text=line.raw_text,
            extraction_method=EXTRACTION_METHOD,
        )
        for line in lines
    )
    return ExtractedText(
        raw_text="\n".join(line.raw_text for line in lines),
        provenance=provenance,
    )


def extracted_text_from_word_groups(
    groups: Sequence[tuple[int, Sequence[LayoutWord]]],
    *,
    source_filename: str,
) -> ExtractedText:
    nonempty = tuple((page, tuple(words)) for page, words in groups if words)
    if not nonempty:
        raise ValueError("cannot create extracted text from no words")
    provenance = tuple(
        SourceProvenance(
            source_filename=source_filename,
            page_number=page,
            bbox=union_bbox(word.bbox for word in words),
            raw_text=" ".join(word.text for word in words),
            extraction_method=EXTRACTION_METHOD,
        )
        for page, words in nonempty
    )
    return ExtractedText(
        raw_text="\n".join(item.raw_text for item in provenance),
        provenance=provenance,
    )


def extract_pdf_layout(
    source_path: Path,
    *,
    page_numbers: Sequence[int],
    crop_top: float,
) -> PdfLayoutDocument:
    pages: list[PageLayout] = []
    with pdfplumber.open(source_path) as pdf:
        for page_number in page_numbers:
            page = pdf.pages[page_number - 1]
            cropped = page.crop((0, crop_top, page.width, page.height))
            raw_words = cropped.extract_words(
                x_tolerance=2,
                y_tolerance=2,
                keep_blank_chars=False,
                use_text_flow=False,
                return_chars=True,
            )
            words: list[LayoutWord] = []
            for item in raw_words:
                raw_chars = item.get("chars") or ()
                font_name = raw_chars[0].get("fontname") if raw_chars else None
                sizes = [float(char["size"]) for char in raw_chars if char.get("size") is not None]
                chars = tuple(
                    LayoutChar(
                        text=char["text"],
                        bbox=BBox(
                            x0=round(float(char["x0"]), 3),
                            y0=round(float(char["top"]), 3),
                            x1=round(float(char["x1"]), 3),
                            y1=round(float(char["bottom"]), 3),
                        ),
                    )
                    for char in raw_chars
                )
                words.append(
                    LayoutWord(
                        text=item["text"],
                        bbox=BBox(
                            x0=round(float(item["x0"]), 3),
                            y0=round(float(item["top"]), 3),
                            x1=round(float(item["x1"]), 3),
                            y1=round(float(item["bottom"]), 3),
                        ),
                        font_name=font_name,
                        font_size=round(mean(sizes), 3) if sizes else None,
                        chars=chars,
                    )
                )
            pages.append(
                PageLayout(
                    page_number=page_number,
                    width=round(float(page.width), 3),
                    height=round(float(page.height), 3),
                    lines=group_words_into_lines(words, page_number=page_number),
                )
            )
        return PdfLayoutDocument(
            source_filename=source_path.name,
            page_count=len(pdf.pages),
            pages=tuple(pages),
        )
