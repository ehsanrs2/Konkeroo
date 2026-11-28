"""Apply an explicit, revision-bound educational edit without changing its source."""

import hashlib
from dataclasses import dataclass


def text_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class EducationalEdit:
    source_sha256: str
    start: int
    original: str
    replacement: str

    def apply(self, source: str) -> str:
        """Return a corrected copy; offsets are zero-based Unicode code points."""
        if text_sha256(source) != self.source_sha256:
            raise ValueError("Source revision mismatch")
        if not self.original or self.original == self.replacement:
            raise ValueError("Empty or unchanged edit")
        end = self.start + len(self.original)
        if self.start < 0 or end > len(source) or source[self.start:end] != self.original:
            raise ValueError("Source span mismatch")
        return source[: self.start] + self.replacement + source[end:]
