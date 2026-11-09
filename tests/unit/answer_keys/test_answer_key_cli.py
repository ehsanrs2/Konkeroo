from pathlib import Path
from types import SimpleNamespace

import pytest

from english_exam import cli
from english_exam.domain import ExtractionIssue, IssueSeverity

ROOT = Path(__file__).parents[3]


def test_key_cli_requires_explicit_source() -> None:
    with pytest.raises(SystemExit) as error:
        cli.main(
            [
                "key",
                "extract",
                "--exam-id",
                "iran-ce-msc-1395",
                "--output",
                "out.json",
            ]
        )

    assert error.value.code == 2


def test_key_cli_rejects_unknown_catalog_identity(tmp_path: Path, capsys) -> None:
    result = cli.main(
        [
            "key",
            "extract",
            "--exam-id",
            "95_Key.pdf",
            "--source",
            str(tmp_path / "95_Key.pdf"),
            "--output",
            str(tmp_path / "out.json"),
        ]
    )

    assert result == 1
    assert "unsupported answer-key source" in capsys.readouterr().err


def test_key_cli_protects_repository_source_with_external_input(
    tmp_path: Path,
    capsys,
) -> None:
    output = ROOT / "dataset" / ".." / "source" / "key-output.json"

    result = cli.main(
        [
            "key",
            "extract",
            "--exam-id",
            "iran-ce-msc-1395",
            "--source",
            str(tmp_path / "95_Key.pdf"),
            "--output",
            str(output),
        ]
    )

    assert result == 2
    assert "must not be written under source/" in capsys.readouterr().err
    assert not (ROOT / "source" / "key-output.json").exists()


def test_key_cli_rejects_source_symlink_output(tmp_path: Path, capsys) -> None:
    source_alias = tmp_path / "source-alias"
    source_alias.symlink_to(ROOT / "source", target_is_directory=True)

    result = cli.main(
        [
            "key",
            "extract",
            "--exam-id",
            "iran-ce-msc-1395",
            "--source",
            str(tmp_path / "95_Key.pdf"),
            "--output",
            str(source_alias / "key-output.json"),
        ]
    )

    assert result == 2
    assert "must not be written under source/" in capsys.readouterr().err


def test_key_cli_does_not_write_failed_validation(tmp_path: Path, monkeypatch, capsys) -> None:
    issue = ExtractionIssue("BROKEN", IssueSeverity.ERROR, "synthetic failure")
    staged = SimpleNamespace(
        validation=SimpleNamespace(errors=(issue,), warnings=()),
    )
    monkeypatch.setattr(cli, "extract_staged_key", lambda _exam_id, _source: staged)
    output = tmp_path / "out.json"

    result = cli.main(
        [
            "key",
            "extract",
            "--exam-id",
            "iran-ce-msc-1395",
            "--source",
            str(tmp_path / "95_Key.pdf"),
            "--output",
            str(output),
        ]
    )

    assert result == 1
    assert "ERROR BROKEN" in capsys.readouterr().err
    assert not output.exists()
