"""Stable JSON serialization for staged datasets."""

from __future__ import annotations

import json
from dataclasses import fields, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any


def to_primitive(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {field.name: to_primitive(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple | list):
        return [to_primitive(item) for item in value]
    if isinstance(value, dict):
        return {str(key): to_primitive(item) for key, item in value.items()}
    return value


def to_json(value: Any) -> str:
    return (
        json.dumps(
            to_primitive(value),
            ensure_ascii=False,
            indent=2,
            allow_nan=False,
        )
        + "\n"
    )


def sha256_text(text: str) -> str:
    from hashlib import sha256

    return sha256(text.encode("utf-8")).hexdigest()


def write_json_atomic(path: Path, text: str, *, force: bool) -> None:
    import os
    import tempfile

    path = Path(path)
    if path.exists() and not force:
        raise FileExistsError(f"{path} already exists; pass --force to replace it")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as stream:
            temporary_name = stream.name
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_name, path)
    finally:
        if temporary_name and Path(temporary_name).exists():
            Path(temporary_name).unlink()
