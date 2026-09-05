# Actions artifact retention

CI uploads (`supply-chain-reports`, `dist`) must expire in 3 days so they do
not fill GitHub Actions storage. A weekly cleanup job deletes leftovers.

## Run

```bash
python -m pytest -q tests/unit/test_artifact_retention.py
```

## Edge cases

| Case | Expected behavior |
|------|-------------------|
| `upload-artifact` without `retention-days` | unit test fails |
| `retention-days` greater than 7 | unit test fails |
| missing `cleanup-artifacts.yml` or unpinned `uses:` | unit test fails |
