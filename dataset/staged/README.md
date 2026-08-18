# Staged datasets

Full staged exam datasets are generated locally and ignored by Git. The tracked
manifest records deterministic hashes and structural expectations without
publishing the extracted exam text.

Generate the 1396 artifact with:

```bash
uv run english-exam extract --year 1396 --source source/96.pdf \
  --output dataset/staged/1396.json
```
