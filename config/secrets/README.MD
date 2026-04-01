# Secrets

This directory is for **local development secrets only**.

## Pattern

Use **one file per secret**.

- filename = the Pydantic settings field name
- file contents = the secret value only
- no quotes
- no `KEY=VALUE`
- no `.env` format

## Example

config/secrets/
  openai_api_key
  anthropic_api_key
  jwt_signing_key
  postgres_password
  redis_password

Example file contents:

`config/secrets/openai_api_key`
```text
sk-xxxxxxxxxxxxxxxx

Runtime behavior

In development:
	•	mount this directory into the container as /run/secrets

In production:
	•	mount your platform secrets into /run/secrets

The app reads secrets from /run/secrets through Pydantic Settings.

Rules
	•	never commit real secrets
	•	keep this folder in .gitignore
	•	keep only .gitkeep and this README in git
	•	rotate secrets outside the repo

Pydantic Settings supports a `secrets_dir` model where each secret is stored in its own file, and Docker Compose secrets are mounted as files under `/run/secrets/<name>`.  [oai_citation:3‡Grafana Labs](https://grafana.com/docs/grafana/latest/datasources/prometheus/configure/)