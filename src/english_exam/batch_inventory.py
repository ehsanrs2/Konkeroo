"""Read-only 1391–1405 source inventory for batch-first assistant development.

Discover exact, explicitly catalogued source files; never infer an official
answer or a parser merely because a file exists. Git LFS pointers are not PDFs.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path
from typing import Literal

EXAM_1396_SHA = "69bc3434ae61c05c85bc9fabffd0b2ce13e5b39bc71b1dfd71c16709c9638ba2"
KEY_1396_SHA = "5d421dcddc780120b13a08753fd2559e7ec02a60200c7c88f4211d70429cba61"
KEY_1395_SHA = "298efdeb70dc84b3bf92872f96bf2f15394f617e8c9e8d6cb9364e50789b3d9b"

SourceRole = Literal["EXAM", "OFFICIAL_KEY"]
MediaKind = Literal["PDF", "JPEG"]


@dataclass(frozen=True, slots=True)
class SourceSpec:
    year: int
    role: SourceRole
    filename: str
    media_kind: MediaKind
    family: str
    expected_sha256: str | None = None


@dataclass(frozen=True, slots=True)
class SourceObservation:
    year: int
    role: SourceRole
    filename: str | None
    media_kind: MediaKind | None
    family: str
    status: str
    actual_sha256: str | None
    expected_sha256: str | None
    lfs_oid_sha256: str | None
    exception: str | None


@dataclass(frozen=True, slots=True)
class YearInventory:
    year: int
    exam: SourceObservation
    key: SourceObservation
    can_attempt_exam: bool
    can_attempt_key: bool


@dataclass(frozen=True, slots=True)
class BatchInventory:
    schema_version: str
    status: str
    years: tuple[YearInventory, ...]
    exam_media_available: int
    key_media_available: int
    exceptions: int


# Explicitly observed repository filenames, not a guessed naming convention.
# "Family" groups technical processing; it is not a key or correctness claim.
YEAR_SOURCES: tuple[tuple[int, str, str | None, str], ...] = (
    (1391, "91.pdf", "91_Key.pdf", "LEGACY_FOUR_BOOKLETS"),
    (1392, "92.pdf", "92_key.pdf", "RENDERED_GRID"),
    (1393, "93.pdf", "93_key.pdf", "RENDERED_GRID"),
    (1394, "94.pdf", "94-key.jpg", "RENDERED_GRID"),
    (1395, "95.pdf", "95_Key.pdf", "NATIVE_PAIRED_GRID"),
    (1396, "96.pdf", "96_Key.pdf", "VISUAL_INITIAL_KEY"),
    (1397, "97.pdf", "97_Key.pdf", "BROKEN_FONT_PAIRED_GRID"),
    (1398, "98.pdf", "98_Key.pdf", "BROKEN_FONT_PAIRED_GRID"),
    (1399, "99.pdf", "99_Key.pdf", "BROKEN_FONT_PAIRED_GRID"),
    (1400, "1400.pdf", "1400_Key.pdf", "RASTER_PERSONALIZED_REPORT"),
    (1401, "1401.pdf", "1401_Key.pdf", "NATIVE_PAIRED_GRID"),
    (1402, "1402.pdf", "1402_Key.pdf", "NATIVE_PAIRED_GRID"),
    (1403, "1403.pdf", "1403_Key.pdf", "NATIVE_PERSONALIZED_REPORT"),
    (1404, "1404.pdf", "1404-key.pdf", "NATIVE_PAIRED_GRID"),
    (1405, "1405.pdf", None, "NO_OFFICIAL_KEY"),
)


def _specs() -> tuple[tuple[SourceSpec, SourceSpec | None], ...]:
    specs = []
    for year, exam_name, key_name, family in YEAR_SOURCES:
        exam = SourceSpec(
            year,
            "EXAM",
            exam_name,
            "PDF",
            "EXAM_PAPER",
            EXAM_1396_SHA if year == 1396 else None,
        )
        key = (
            SourceSpec(
                year,
                "OFFICIAL_KEY",
                key_name,
                "JPEG" if key_name.lower().endswith(".jpg") else "PDF",
                family,
                KEY_1395_SHA if year == 1395 else KEY_1396_SHA if year == 1396 else None,
            )
            if key_name is not None
            else None
        )
        specs.append((exam, key))
    return tuple(specs)


def _sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _lfs_oid(header: bytes) -> tuple[bool, str | None]:
    if not header.startswith(b"version https://git-lfs.github.com/spec/v1\n"):
        return False, None
    lines = header.decode("ascii", errors="replace").splitlines()
    candidates = [line[11:] for line in lines if line.startswith("oid sha256:")]
    if len(candidates) != 1:
        return True, None
    oid = candidates[0]
    if len(oid) != 64 or any(c not in "0123456789abcdef" for c in oid):
        return True, None
    return True, oid


def observe_source(root: Path, source: SourceSpec) -> SourceObservation:
    """Classify a file without publishing its contents or treating LFS as media."""
    path = root / source.filename
    state = "SOURCE_MISSING"
    observed_sha: str | None = None
    oid: str | None = None
    exception: str | None = "SOURCE_MISSING"
    if path.is_file():
        with path.open("rb") as handle:
            header = handle.read(512)
        is_lfs, oid = _lfs_oid(header)
        if is_lfs:
            state = "LFS_POINTER_ONLY" if oid is not None else "MALFORMED_LFS_POINTER"
            exception = state
            if oid is not None and source.expected_sha256 and oid != source.expected_sha256:
                state = exception = "SOURCE_IDENTITY_CONFLICT"
        elif not (
            header.startswith(b"%PDF-")
            if source.media_kind == "PDF"
            else header.startswith(b"\xff\xd8\xff")
        ):
            state = exception = "MEDIA_SIGNATURE_MISMATCH"
        else:
            observed_sha = _sha256_file(path)
            if source.expected_sha256 and observed_sha != source.expected_sha256:
                state = exception = "SOURCE_HASH_MISMATCH"
            else:
                state = "LOCAL_SOURCE_PINNED" if source.expected_sha256 else "LOCAL_SOURCE_UNPINNED"
                exception = None
    return SourceObservation(
        year=source.year,
        role=source.role,
        filename=source.filename,
        media_kind=source.media_kind,
        family=source.family,
        status=state,
        actual_sha256=observed_sha,
        expected_sha256=source.expected_sha256,
        lfs_oid_sha256=oid,
        exception=exception,
    )


def inventory_sources(source_dir: Path) -> BatchInventory:
    """Scan 15 explicitly catalogued years in one pass; no PDF text is extracted."""
    rows: list[YearInventory] = []
    for exam_spec, key_spec in _specs():
        exam = observe_source(source_dir, exam_spec)
        key = (
            observe_source(source_dir, key_spec)
            if key_spec is not None
            else SourceObservation(
                year=exam_spec.year,
                role="OFFICIAL_KEY",
                filename=None,
                media_kind=None,
                family="NO_OFFICIAL_KEY",
                status="NO_OFFICIAL_KEY_RECORDED",
                actual_sha256=None,
                expected_sha256=None,
                lfs_oid_sha256=None,
                exception=None,
            )
        )
        rows.append(
            YearInventory(
                year=exam_spec.year,
                exam=exam,
                key=key,
                can_attempt_exam=exam.status.startswith("LOCAL_SOURCE_"),
                can_attempt_key=key.status.startswith("LOCAL_SOURCE_"),
            )
        )
    exam_available = sum(row.can_attempt_exam for row in rows)
    key_available = sum(row.can_attempt_key for row in rows)
    exceptions = sum(row.exam.exception is not None for row in rows) + sum(
        row.key.exception is not None for row in rows
    )
    # An inventory completes even without all media; that is not source success.
    state = "ALL_MEDIA_AVAILABLE" if exceptions == 0 else "SOURCES_INCOMPLETE"
    return BatchInventory("1.0", state, tuple(rows), exam_available, key_available, exceptions)


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only 1391–1405 batch source inventory")
    parser.add_argument("--source-dir", type=Path, default=Path("source"))
    args = parser.parse_args()
    report = inventory_sources(args.source_dir)
    print(json.dumps(asdict(report), sort_keys=True, ensure_ascii=False, indent=2))
    return 0  # Inventory success, not proof of original-source or answer verification.


if __name__ == "__main__":
    raise SystemExit(main())
