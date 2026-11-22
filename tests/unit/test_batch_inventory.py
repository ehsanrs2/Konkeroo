"""Sanitized, source-independent batch inventory tests (no exam/key text)."""

from hashlib import sha256

from english_exam.batch_inventory import (
    EXAM_1396_SHA,
    KEY_1395_SHA,
    KEY_RENDERED_LFS_SHA,
    YEAR_SOURCES,
    SourceSpec,
    inventory_sources,
    observe_source,
)


def _by_year(report):
    return {row.year: row for row in report.years}


def test_explicit_15_year_29_media_catalog_and_absent_1405_key(tmp_path):
    assert [year for year, *_ in YEAR_SOURCES] == list(range(1391, 1406))
    assert len({name for _, exam, key, _ in YEAR_SOURCES for name in (exam, key) if name}) == 29
    report = inventory_sources(tmp_path)
    years = _by_year(report)

    assert report.schema_version == "1.0"
    assert report.status == "SOURCES_INCOMPLETE"
    assert report.exam_media_available == 0
    assert report.key_media_available == 0
    assert report.exceptions == 29
    assert len(report.years) == 15
    assert years[1391].key.family == "LEGACY_FOUR_BOOKLETS"
    assert years[1394].key.media_kind == "JPEG"
    assert years[1397].key.family == "BROKEN_FONT_PAIRED_GRID"
    assert years[1400].key.family == "RASTER_PERSONALIZED_REPORT"
    assert years[1403].key.family == "NATIVE_PERSONALIZED_REPORT"
    assert years[1405].key.status == "NO_OFFICIAL_KEY_RECORDED"
    assert years[1405].key.filename is None
    assert years[1405].key.exception is None
    assert not years[1405].can_attempt_key


def test_actual_media_observed_without_claiming_verification(tmp_path):
    (tmp_path / "91.pdf").write_bytes(b"%PDF-1.4\nfictional test payload\n")
    (tmp_path / "1404-key.pdf").write_bytes(b"%PDF-1.4\nfictional test payload\n")
    report = inventory_sources(tmp_path)
    rows = _by_year(report)

    assert rows[1391].exam.status == "LOCAL_SOURCE_UNPINNED"
    assert rows[1391].exam.actual_sha256 == sha256((tmp_path / "91.pdf").read_bytes()).hexdigest()
    assert rows[1391].can_attempt_exam
    assert rows[1391].key.status == "SOURCE_MISSING"
    assert not rows[1391].can_attempt_key
    assert rows[1404].key.status == "LOCAL_SOURCE_UNPINNED"
    assert rows[1404].can_attempt_key
    assert rows[1404].key.actual_sha256 is not None
    assert rows[1404].key.expected_sha256 is None
    assert report.exam_media_available == 1
    assert report.key_media_available == 1
    assert report.exceptions == 27


def test_lfs_pointer_is_never_counted_as_real_pdf(tmp_path):
    (tmp_path / "95_Key.pdf").write_text(
        f"version https://git-lfs.github.com/spec/v1\noid sha256:{KEY_1395_SHA}\nsize 123\n"
    )
    (tmp_path / "96.pdf").write_text(
        "version https://git-lfs.github.com/spec/v1\n" + "oid sha256:" + "0" * 64 + "\nsize 12\n"
    )
    (tmp_path / "96_Key.pdf").write_text(
        "version https://git-lfs.github.com/spec/v1\noid sha256:not-a-hash\nsize 12\n"
    )
    report = inventory_sources(tmp_path)
    years = _by_year(report)

    assert years[1395].key.status == "LFS_POINTER_ONLY"
    assert years[1395].key.lfs_oid_sha256 == KEY_1395_SHA
    assert not years[1395].can_attempt_key
    assert years[1396].exam.status == "SOURCE_IDENTITY_CONFLICT"
    assert years[1396].exam.lfs_oid_sha256 == "0" * 64
    assert years[1396].exam.expected_sha256 == EXAM_1396_SHA
    assert years[1396].key.status == "MALFORMED_LFS_POINTER"
    assert years[1396].key.lfs_oid_sha256 is None
    assert report.exam_media_available == 0
    assert report.key_media_available == 0


def test_hash_mismatch_and_bad_media_signature_fail_closed(tmp_path):
    (tmp_path / "96.pdf").write_bytes(b"%PDF-1.4\nnot the real original media\n")
    (tmp_path / "92.pdf").write_bytes(b"this is not a PDF")
    report = inventory_sources(tmp_path)
    years = _by_year(report)

    assert years[1396].exam.status == "SOURCE_HASH_MISMATCH"
    assert years[1396].exam.actual_sha256 != EXAM_1396_SHA
    assert years[1396].exam.exception == "SOURCE_HASH_MISMATCH"
    assert not years[1396].can_attempt_exam
    assert years[1392].exam.status == "MEDIA_SIGNATURE_MISMATCH"
    assert years[1392].exam.actual_sha256 is None
    assert not years[1392].can_attempt_exam


def test_custom_source_pin_recognizes_valid_bytes_without_publishing_them(tmp_path):
    payload = b"%PDF-1.7\nfictional test payload\n"
    (tmp_path / "fake.pdf").write_bytes(payload)
    spec = SourceSpec(
        year=1499,
        role="EXAM",
        filename="fake.pdf",
        media_kind="PDF",
        family="EXAM_PAPER",
        expected_sha256=sha256(payload).hexdigest(),
    )
    result = observe_source(tmp_path, spec)
    assert result.status == "LOCAL_SOURCE_PINNED"
    assert result.exception is None
    assert result.actual_sha256 == spec.expected_sha256
    assert result.lfs_oid_sha256 is None


def test_rendered_key_repo_lfs_pins_are_identity_checks_not_real_media(tmp_path):
    for year, filename in ((1392, "92_key.pdf"), (1393, "93_key.pdf"), (1394, "94-key.jpg")):
        (tmp_path / filename).write_text(
            "version https://git-lfs.github.com/spec/v1\\n"
            f"oid sha256:{KEY_RENDERED_LFS_SHA[year]}\\nsize 123\\n"
        )

    report = inventory_sources(tmp_path)
    by_year = _by_year(report)
    for year in KEY_RENDERED_LFS_SHA:
        observed = by_year[year].key
        assert observed.expected_sha256 == KEY_RENDERED_LFS_SHA[year]
        assert observed.lfs_oid_sha256 == KEY_RENDERED_LFS_SHA[year]
        assert observed.status == "LFS_POINTER_ONLY"
        assert observed.actual_sha256 is None
        assert not by_year[year].can_attempt_key

    (tmp_path / "92_key.pdf").write_bytes(b"%PDF-1.7\\nsynthetic source mismatch\\n")
    (tmp_path / "93_key.pdf").write_text(
        "version https://git-lfs.github.com/spec/v1\\n"
        f"oid sha256:{'0' * 64}\\nsize 123\\n"
    )
    refreshed = _by_year(inventory_sources(tmp_path))
    assert refreshed[1392].key.status == "SOURCE_HASH_MISMATCH"
    assert refreshed[1392].key.actual_sha256 != KEY_RENDERED_LFS_SHA[1392]
    assert refreshed[1393].key.status == "SOURCE_IDENTITY_CONFLICT"
    assert refreshed[1394].key.status == "LFS_POINTER_ONLY"
