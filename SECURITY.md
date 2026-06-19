# Security Policy

## Reporting a Vulnerability

**Do not open public issues for security vulnerabilities.**

Report suspected vulnerabilities privately to the maintainers:

- Preferred: open a [GitHub private security advisory](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability)
  for this repository (Security → Advisories → "Report a vulnerability").
- Or email the maintainers (replace with your project contact): `security@example.com`.

Please include: affected version/commit, reproduction steps or PoC, impact, and
any suggested remediation.

**Response targets** (adjust for your team):

| Stage | Target |
| --- | --- |
| Acknowledge report | within 3 business days |
| Initial assessment / severity | within 7 business days |
| Fix or mitigation for high/critical | within 30 days |

We will coordinate disclosure timing with you and credit reporters who wish to
be named.

## Supported Versions

Security fixes are applied to the latest release line. Update this table as you
cut releases:

| Version | Supported |
| --- | --- |
| latest `main` | ✅ |
| older | ❌ |

## Supply-chain security controls

This repository ships a defense-in-depth supply-chain stack. See
`AGENTS.md` → "Agent Tooling & Integrations" for usage. Summary:

- **Pinned dependencies** — `requirements*.txt` are compiled with
  `pip-compile --generate-hashes` and installed with `pip --require-hashes`.
  Track CVE-driven version floors with a comment in `requirements*.in`.
- **`pip-audit`** — known-vulnerability scan of the Python lockfile (CI + local).
- **OSV-Scanner** — multi-ecosystem lockfile vulnerability scan, run from a
  digest-pinned container. Exceptions live in `config/security/osv-scanner.toml`
  with a tracked reason, owner, and expiry.
- **GuardDog** — malicious-package heuristics (typosquatting, install scripts,
  bundled binaries, suspicious maintainers) over direct dependencies, from a
  digest-pinned container. Time-bounded exceptions in `config/security/guarddog.json`.
- **OpenGrep** — Semgrep-compatible static analysis with the project's
  secure-coding rules in `config/security/opengrep.yml`. The binary is verified
  by SHA-256 before it runs.
- **Bandit** — Python SAST (`config/security/bandit.yaml`).
- **npm worm / persistence audit** — `scripts/security/npm_worm_audit.py` blocks
  Shai-Hulud / AntV-class IOCs, dangerous npm lifecycle scripts, non-registry
  dependency specs, and monitors agent/IDE persistence files
  (`.vscode/tasks.json`, `.claude/settings.json`) for tampering.
- **Dependency Review** — `.github/workflows/dependency-review.yml` gates PRs
  (where GitHub Code Security is available).
- **Pinned CI actions / images** — GitHub Actions and scanner containers are
  pinned by commit SHA / image digest.

Run the full local gate before pushing:

```bash
./scripts/security/supply-chain-audit.sh
```

Reports are written to `logs/current/supply-chain/`.
