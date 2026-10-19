# Actions artifact retention

CI uploads (`supply-chain-reports`, `dist`) must expire in 3 days so they do
not fill GitHub Actions storage. GitHub applies that TTL on each new upload.

## Run

```bash
python -m pytest -q tests/unit/test_artifact_retention.py
```

## Edge cases

| Case | Expected behavior |
|------|-------------------|
| `upload-artifact` without `retention-days` | unit test fails |
| `retention-days` greater than 7 | unit test fails |
| no `upload-artifact` steps in workflows | unit test fails |
