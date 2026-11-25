"""Source-bound, metadata-only 1392–1394 rendered-key acceptance diagnostics.

A matching Git LFS SHA-256 proves repository-object identity only. It is not
publisher authentication, visual answer decoding, or final answer validation.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from english_exam.batch_inventory import (
    KEY_RENDERED_LFS_SHA,
    BatchInventory,
    inventory_sources,
)
from english_exam.rendered_key_batch import (
    RenderedFamilyBatch,
    process_rendered_family,
)
from english_exam.visual_grid_cells import CellBatch, process_cell_family
from english_exam.visual_grid_regions import RegionBatch, process_region_family

RENDERED_YEARS = (1392, 1393, 1394)
SOURCE_SIZES_RECORDED_BY_REPO_LFS = {1392: 260186, 1393: 602063, 1394: 129773}


@dataclass(frozen=True, slots=True)
class PageAcceptance:
    page_number: int
    region_status: str
    cell_status: str
    candidate_regions: int
    cell_lattices: int
    incomplete_lattices: int


@dataclass(frozen=True, slots=True)
class YearAcceptance:
    year: int
    filename: str | None
    source_status: str
    expected_repo_lfs_sha256: str
    expected_repo_lfs_size: int
    observed_sha256: str | None
    identity_scope: str
    media_status: str
    region_status: str
    cell_status: str
    status: str
    pages: tuple[PageAcceptance, ...]
    flags: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RenderedAcceptance:
    schema_version: str
    scope: str
    status: str
    years: tuple[YearAcceptance, ...]
    sources_pinned: int
    provisional_geometry_years: int
    exceptions: int


def assemble_acceptance(
    inventory: BatchInventory,
    media: RenderedFamilyBatch,
    regions: RegionBatch,
    cells: CellBatch,
) -> RenderedAcceptance:
    """Cross-check the independent stages; do not promote source or answer authority."""
    source = {item.year: item.key for item in inventory.years}
    triage = {item.year: item for item in media.years}
    detected = {item.year: item for item in regions.years}
    mapped = {item.year: item for item in cells.years}
    results: list[YearAcceptance] = []

    for year in RENDERED_YEARS:
        key = source[year]
        med = triage[year]
        reg = detected[year]
        cell = mapped[year]
        flags: list[str] = ["NO_OFFICIAL_ANSWER_VALIDATION"]
        pinned = key.status == "LOCAL_SOURCE_PINNED"
        if not pinned:
            flags.append("ORIGINAL_MEDIA_NOT_READY")
        if (
            key.expected_sha256 != KEY_RENDERED_LFS_SHA[year]
            or any(item.source_status != key.status for item in (med, reg, cell))
            or any(item.source_sha256 != key.actual_sha256 for item in (med, reg, cell))
        ):
            flags.append("STAGE_SOURCE_IDENTITY_CONFLICT")

        pages: list[PageAcceptance] = []
        if pinned:
            if (
                med.status != "MEDIA_TRIAGED_VISUAL_MAPPING_PENDING"
                or med.page_count is None
                or len(reg.pages) != med.page_count
                or len(cell.pages) != med.page_count
            ):
                flags.append("STAGE_PAGE_COVERAGE_CONFLICT")
            for index, (rpage, cpage) in enumerate(zip(reg.pages, cell.pages), start=1):
                if (
                    rpage.page_number != index
                    or cpage.page_number != index
                    or rpage.status != cpage.region_status
                    or rpage.width_px != cpage.width_px
                    or rpage.height_px != cpage.height_px
                    or len(rpage.regions) != len(cpage.regions)
                ):
                    flags.append("STAGE_PAGE_METADATA_CONFLICT")
                complete = sum(item.status == "UNVERIFIED_CELL_LATTICE" for item in cpage.regions)
                pages.append(
                    PageAcceptance(
                        page_number=index,
                        region_status=rpage.status,
                        cell_status=cpage.status,
                        candidate_regions=len(rpage.regions),
                        cell_lattices=complete,
                        incomplete_lattices=len(cpage.regions) - complete,
                    )
                )
            if len(reg.pages) > 1:
                flags.append("MULTIPAGE_CONTINUATION_UNRESOLVED")
        elif (
            med.status != "SOURCE_NOT_READY"
            or reg.status != "SOURCE_NOT_READY"
            or cell.status != "SOURCE_NOT_READY"
            or reg.pages
            or cell.pages
        ):
            flags.append("STAGE_UNAVAILABLE_SOURCE_CONFLICT")

        if any(flag.startswith("STAGE_") for flag in flags):
            status = "STAGE_EVIDENCE_CONFLICT"
        elif not pinned:
            status = "SOURCE_NOT_READY"
        elif (
            pages
            and reg.status == "UNVERIFIED_REGIONS_PER_PAGE"
            and cell.status == "UNVERIFIED_CELL_LATTICES_PER_PAGE"
            and all(page.cell_lattices > 0 and page.incomplete_lattices == 0 for page in pages)
        ):
            status = "PROVISIONAL_GEOMETRY_OBSERVED"
        else:
            status = "SOURCE_PRESENT_GEOMETRY_UNRESOLVED"
            flags.append("SOURCE_PRESENT_NEEDS_VISUAL_FOLLOWUP")

        results.append(
            YearAcceptance(
                year=year,
                filename=key.filename,
                source_status=key.status,
                expected_repo_lfs_sha256=KEY_RENDERED_LFS_SHA[year],
                expected_repo_lfs_size=SOURCE_SIZES_RECORDED_BY_REPO_LFS[year],
                observed_sha256=key.actual_sha256,
                identity_scope="REPOSITORY_LFS_OBJECT_ONLY" if pinned else "NOT_ATTESTED",
                media_status=med.status,
                region_status=reg.status,
                cell_status=cell.status,
                status=status,
                pages=tuple(pages),
                flags=tuple(dict.fromkeys(flags)),
            )
        )

    pinned_count = sum(row.source_status == "LOCAL_SOURCE_PINNED" for row in results)
    geometry = sum(row.status == "PROVISIONAL_GEOMETRY_OBSERVED" for row in results)
    conflicts = sum(row.status == "STAGE_EVIDENCE_CONFLICT" for row in results)
    return RenderedAcceptance(
        schema_version="1.0",
        scope="REPO_LFS_IDENTITY_AND_GEOMETRY_ONLY",
        status=(
            "STAGE_EVIDENCE_CONFLICT"
            if conflicts
            else "ALL_SOURCES_PRESENT_PROVISIONAL_GEOMETRY_ONLY"
            if geometry == len(RENDERED_YEARS)
            else "DIAGNOSTICS_INCOMPLETE"
        ),
        years=tuple(results),
        sources_pinned=pinned_count,
        provisional_geometry_years=geometry,
        exceptions=len(RENDERED_YEARS) - geometry,
    )


def audit_rendered_sources(source_dir: Path) -> RenderedAcceptance:
    """Run the same existing stages once per technical family, metadata-only."""
    inventory = inventory_sources(source_dir)
    return assemble_acceptance(
        inventory,
        process_rendered_family(source_dir),
        process_region_family(source_dir),
        process_cell_family(source_dir),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Rendered-key original-media acceptance diagnostics"
    )
    parser.add_argument("--source-dir", type=Path, default=Path("source"))
    parser.add_argument(
        "--require-sources",
        action="store_true",
        help="Exit 2 unless all three exact LFS SHA-matched media bytes are available",
    )
    parser.add_argument(
        "--require-provisional-geometry",
        action="store_true",
        help="Exit 3 unless all three sources have complete provisional page geometry",
    )
    args = parser.parse_args(argv)
    report = audit_rendered_sources(args.source_dir)
    print(json.dumps(asdict(report), ensure_ascii=False, sort_keys=True, indent=2))
    if args.require_sources and report.sources_pinned != len(RENDERED_YEARS):
        return 2
    if args.require_provisional_geometry and (
        report.sources_pinned != len(RENDERED_YEARS)
        or report.provisional_geometry_years != len(RENDERED_YEARS)
    ):
        return 3
    return 0  # Reporting is never proof of official answers.


if __name__ == "__main__":
    raise SystemExit(main())
