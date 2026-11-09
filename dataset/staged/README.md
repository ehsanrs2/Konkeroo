# Staged datasets

Full staged exam and answer-key datasets are generated locally and ignored by
Git. Tracked manifests record deterministic hashes and structural expectations
without publishing extracted exam or answer-key text.

Generate the 1396 exam artifact with:

```bash
uv run english-exam extract --year 1396 --source source/96.pdf \
  --output dataset/staged/1396.json
```

Generate the independent 1395 official-key artifact with:

```bash
uv run english-exam key extract --exam-id iran-ce-msc-1395 \
  --source source/95_Key.pdf --output dataset/staged/1395-key.json
```

The 1395 key artifact contains all source-key entries. It does not assume an
English question range and is not reconciled with an exam dataset in this
milestone.
