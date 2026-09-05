# Upgrade & Maintenance Guide

> **Purpose.** How to refresh this template's pinned artifacts (deps, actions,
> scanner images, the ODW and J-Space submodules) and how a project derived from this
> template pulls in upstream template fixes. This is a process doc, not one of
> the 10 core documents.
>
> **One rule above all:** *everything is pinned* (Python deps by hash, GitHub
> Actions by commit SHA, scanner containers by image digest, OpenGrep by
> SHA-256, ODW and J-Space by submodule commit). An upgrade is a deliberate, reviewed pin
> rotation — never a floating reference.

---

## 1. Python dependencies

Lockfiles (`requirements.txt`, `requirements-dev.txt`, `requirements-notebooks.txt`)
are **compiled** from the `.in` sources with hashes. Never edit a `.txt`
directly; bump the `.in` and re-compile.

```bash
# Edit the source pins (e.g. bump a floor, add a dep) in requirements*.in,
# then regenerate every lockfile WITH hashes from a clean Python 3.12 env:
pip-compile --generate-hashes --allow-unsafe --resolver=backtracking \
  requirements.in -o requirements.txt
pip-compile --generate-hashes --allow-unsafe --resolver=backtracking \
  requirements-dev.in -o requirements-dev.txt
pip-compile --generate-hashes --allow-unsafe --resolver=backtracking \
  requirements-notebooks.in -o requirements-notebooks.txt
```

The `[tool.pip-tools]` block in `pyproject.toml` already sets those flags, so a
bare `pip-compile requirements.in` honors them. Track CVE floors with comments
in the `.in` files (e.g. `# CVE-2026-XXXX fixed in >=X.Y.Z`).

Verify before committing:

```bash
python -m pip install --require-hashes -r requirements-dev.txt && python -m pip check
./scripts/security/supply-chain-audit.sh   # pip-audit + OSV-Scanner over BOTH lockfiles
```

> **Dependabot does NOT do this.** `.github/dependabot.yml` excludes the `pip`
> ecosystem on purpose — Dependabot mutates the compiled `.txt` directly and
> fights `--require-hashes`. Python bumps are always the manual `.in` →
> `pip-compile` flow above.

---

## 2. GitHub Actions (SHA-pinned)

Every `uses:` in `.github/workflows/*.yml` is pinned to a 40-char commit SHA with
a trailing `# vX` comment. Bump via Dependabot (it rewrites both the SHA and the
comment) or manually:

```bash
# Resolve a tag/branch to its commit SHA (dereferences annotated tags, no auth):
git ls-remote --tags https://github.com/actions/checkout v6 | sort -t/ -k3 -V | tail -1
# -> <sha>\trefs/tags/v6^{}`   (the peeled/dereferenced line you copy the SHA from)
# Paste the SHA into the workflow uses: line, keep the "# vX" comment in sync.
```

---

## 3. Scanner images (digest-pinned)

OSV-Scanner, GuardDog, and Trivy run via `docker run` against images pinned by
`@sha256:…`. Refresh a digest when you want a newer scanner version:

```bash
# Resolve the current digest for a tag (no auth; works for ghcr.io and Docker Hub):
TAG=0.72.0
TOKEN="$(curl -s "https://ghcr.io/token?scope=repository:aquasecurity/trivy:pull" \
  | python3 -c 'import sys,json;print(json.load(sys.stdin)["token"])')"
curl -sI -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/vnd.oci.image.index.v1+json" \
  "https://ghcr.io/v2/aquasecurity/trivy/manifests/$TAG" | grep -i docker-content-digest
# Replace the @sha256:... in ci.yml and re-run the scanner locally.
```

For a Docker Hub image (if you ever use the Hub mirror instead of GHCR — this
repo pulls all three scanners from GHCR), swap the token endpoint to
`https://auth.docker.io/token?service=registry.docker.io&scope=repository:<image>:pull`
and the registry to `registry-1.docker.io`.

> **Trivy via image, not the action.** `aquasecurity/trivy-action` was compromised
> 2026-03-19 (CVE-2026-33634 / GHSA-69fq-xp46-6x23); use the digest-pinned OCI
> image. See the "Supply-chain security gates" section of `AGENTS.md`.

### OpenGrep (SHA-256-pinned binary)

The OpenGrep binary is pinned by SHA-256 in `ci.yml` and
`scripts/security/supply-chain-audit.sh`. To bump: download the new release,
`sha256sum` it, and replace both the URL version and the hash in both files.

---

## 4. ODW submodule (commit-pinned)

```bash
git submodule update --remote vendor/open-dynamic-workflows   # advance to upstream HEAD
cd vendor/open-dynamic-workflows && git checkout <reviewed-commit> && cd -
git add vendor/open-dynamic-workflows                         # records the new commit
cd vendor/open-dynamic-workflows && npm ci && npm run build   # rebuild dist/cli.js
```

The setup gate's S7 checks `dist/cli.js` exists; S6 checks the submodule is
initialized when `odw_runtime = "keep"`.

---

## 4b. J-Space submodule (commit-pinned)

No npm build. Pin rotation only:

```bash
git submodule update --remote vendor/j-space-cognition-suite   # advance to upstream HEAD
cd vendor/j-space-cognition-suite && git checkout <reviewed-commit> && cd -
git add vendor/j-space-cognition-suite                         # records the new commit
```

Confirm `.agents/skills/j-space` still points at `j-space/` inside the tree
(`SKILL.md` must resolve). The setup gate's **S10** checks the submodule and
symlink when `jspace_skill = "keep"`.

---

## 4c. Taskboard plugin (marketplace `ref: main`)

The Go binary is not vendored. Rotate the **reviewed HEAD** comment in
`AGENTS.md` after you merge plugin changes on [atebites-hub/taskboard](https://github.com/atebites-hub/taskboard):

```bash
git -C /path/to/taskboard rev-parse HEAD
# record that SHA next to atebites-hub/taskboard in AGENTS.md
# keep extraKnownMarketplaces.taskboard.source.ref = "main"
```

Copy `skills/taskboard-workflow/SKILL.md` and `scripts/{session,commit}-sync.sh`
into this repo (`.agents/skills/taskboard-workflow/` and
`scripts/hooks/taskboard-sync.sh`) when those files change. The setup gate's
**S11** checks marketplace registration and the skill file when
`taskboard_plugin = "keep"`.

---

## 5. Promote a report-only scanner to blocking

OSV-Scanner, GuardDog, and Trivy ship **report-only** (`continue-on-error`).
Promote one after curating its ignore file:

1. Run CI once, download the `supply-chain-reports` artifact (retained 3 days), read the JSON.
2. Add each accepted finding's ID to the matching ignore file
   (`config/security/osv-scanner.toml`, `guarddog.json`, or `trivyignore`) with
   an owner + reason.
3. Remove `continue-on-error: true` from that step (for Trivy also add
   `--exit-code 1 --severity HIGH,CRITICAL`).

---

## 6. Re-syncing a derived project with upstream template fixes

A project created from this template can still pull in template improvements
(bug fixes, new gates, scanner refreshes) as long as it kept the template as an
upstream remote:

```bash
git remote add template https://github.com/<owner>/PJTemplate.git
git fetch template
git merge template/main --allow-unrelated-histories   # or cherry-pick specific commits
```

Expect conflicts in `README.md`, `AGENTS.md`, `config/setup.toml`, and any file
you customized. The setup gate (`scripts/check-template-setup.sh`) tells you
which template transformations are incomplete after the merge — work through
`docs/agents/template_setup_checklist.md` until it reports OK.

> If the derivation deleted a subsystem the upstream change touches (e.g. you
> stripped observability and upstream fixed a metric), resolve in favor of your
> derivation and drop the upstream hunk. The checklist's keep/strip decisions in
> `config/setup.toml` are the source of truth for what stays.

---

## 7. Cadence

- **Weekly:** review Dependabot PRs (github-actions + docker image patches).
- **Monthly:** `pip-compile` refresh of the lockfiles; resolve any new
  pip-audit / OSV findings (curate ignores or bump).
- **On advisory:** refresh a scanner digest or action SHA the day a CVE lands.
