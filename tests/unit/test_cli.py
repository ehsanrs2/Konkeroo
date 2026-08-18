from pathlib import Path

from english_exam.cli import main
from english_exam.serialization import write_json_atomic

ROOT = Path(__file__).parents[2]


def test_cli_rejects_unknown_year(tmp_path: Path, capsys) -> None:
    result = main(
        [
            "extract",
            "--year",
            "1400",
            "--source",
            str(tmp_path / "1400.pdf"),
            "--output",
            str(tmp_path / "output.json"),
        ]
    )

    assert result == 2
    assert "only the 1396 fixture is supported" in capsys.readouterr().err


def test_cli_protects_repository_source_when_input_is_elsewhere(tmp_path: Path, capsys) -> None:
    external_source = tmp_path / "96.pdf"
    output = ROOT / "dataset" / ".." / "source" / "generated.json"

    result = main(
        [
            "extract",
            "--year",
            "1396",
            "--source",
            str(external_source),
            "--output",
            str(output),
        ]
    )

    assert result == 2
    assert "must not be written under source/" in capsys.readouterr().err
    assert not (ROOT / "source" / "generated.json").exists()


def test_cli_rejects_output_through_symlink_to_repository_source(tmp_path: Path, capsys) -> None:
    source_alias = tmp_path / "source-alias"
    source_alias.symlink_to(ROOT / "source", target_is_directory=True)

    result = main(
        [
            "extract",
            "--year",
            "1396",
            "--source",
            str(tmp_path / "96.pdf"),
            "--output",
            str(source_alias / "generated.json"),
        ]
    )

    assert result == 2
    assert "must not be written under source/" in capsys.readouterr().err
    assert not (ROOT / "source" / "generated.json").exists()


def test_atomic_writer_requires_force(tmp_path: Path) -> None:
    output = tmp_path / "staged.json"
    write_json_atomic(output, "first\n", force=False)

    try:
        write_json_atomic(output, "second\n", force=False)
    except FileExistsError:
        pass
    else:
        raise AssertionError("existing output was replaced without --force")

    write_json_atomic(output, "second\n", force=True)
    assert output.read_text(encoding="utf-8") == "second\n"
