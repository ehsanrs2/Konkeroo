# Reading-2 original-PDF gate: question ownership regression

Original-source integration reported by the maintainer on the merged [PR #33](https://github.com/ehsanrs2/Konkeroo/pull/33) revision (`ffcb72f`):

```text
staged.validation.status == PASSED
preview.status == BLOCKED
expected ASSISTANT_PROVISIONAL
```

## Root cause

The importer `src/english_exam/importers/exam_1396.py` assigns Q20 to Reading Passage 1 (`READING_QUESTION_RANGES["reading-1"] = range(16, 21)`) and Q21–Q25 to Reading Passage 2 (`range(21, 26)`). The Reading-2 provisional helper erroneously required **Q20 through Q25 inside Reading-2**. This invalid guard was hidden because its synthetic unit stage inserted an impossible Q20 into Reading-2, while the original-source integration was skipped in CI without the LFS PDF.

The fix aligns the helper's question-set guard with the real importer: **exactly 21, 22, 23, 24, 25**. Synthetic fixtures now mirror that same membership. Rejection tests cover an extraneous Q20 as well as an omitted Q21. The actual-source test asserts Q20 belongs to Reading-1 and Q21–25 to Reading-2, and surfaces `preview.errors` in an assertion failure.

The original PDF `source/96.pdf` is unchanged. Its SHA-256 is `69bc3434ae61c05c85bc9fabffd0b2ce13e5b39bc71b1dfd71c16709c9638ba2`. Independent inspection of its text layer shows Q21–24 on original PDF page 4 and Q25 on page 5, while Q20 sits above the Passage-2 heading on page 4. This *supports* but does not substitute for a complete original-source integration run.

## Local acceptance after merging

```bash
git pull --ff-only
uv sync --locked --dev
uv run --dev python -m pytest -q -ra tests/integration/test_1396_reading2_source.py
```

The relevant source-present test must **pass**, not skip. Public CI can pass all synthetic tests while this particular test is skipped when the original LFS payload is absent. If still blocked, print the structured failure rather than weakening any remaining guards:

```bash
uv run --dev python - <<'PY'
import json
from pathlib import Path
from english_exam.pipeline import extract_staged_1396
from english_exam.reading2_provisional import preview_1396_reading2

root = Path("dataset/review")
review = json.loads((root / "1396-reading-text-review.json").read_text(encoding="utf-8"))
ledger = json.loads((root / "1396-review-ledger.json").read_text(encoding="utf-8"))
stage = extract_staged_1396(Path("source/96.pdf"))
report = preview_1396_reading2(stage, review, ledger)
print("Status:", report.status)
print("Errors:", report.errors)
print("Q21–25 source membership:", tuple(
    q.number for q in next(p for s in stage.exam.sections
    if s.id == "reading" for p in s.passages if p.id == "reading-2").questions
))
PY
```

No release gate, human review decision, original source, raw text, answer key or prior proposal is changed. This is a regression bug fix, not a new claim of independent verification.
