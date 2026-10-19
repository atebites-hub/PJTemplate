# Task Memory: Remove weekly artifact-cleanup cron

## Description
- Delete `.github/workflows/cleanup-artifacts.yml` (Monday `15 6 * * 1` schedule).
- Remove checks and docs that exist only to require that file.
- Leave `retention-days: 3` on `actions/upload-artifact` and the other workflows unchanged.

## Related Memories
- [2026-09-05 short Actions artifact retention](2026-09-05-actions-artifact-retention.md) — added the cron plus `retention-days: 3`. This task removes only the cron.

## Task (TCREI)
- **Task**: Remove the weekly artifact-cleanup GitHub Actions workflow and anything that exists only to support it, then open a PR that lists what was removed.
- **Scope**: inline
- **Context**: Retrieved `.github/workflows/cleanup-artifacts.yml`, `ci.yml` / `cd.yml` / `dependency-review.yml` (left alone), `tests/unit/test_artifact_retention.py` (`test_cleanup_artifacts_workflow_is_scheduled_and_pinned` is the only assertion that the file exists), `docs/tests/artifact_retention.md`, `docs/agents/upgrade.md` §5 (mentions the 3-day download window, not the cron), `scripts/` and `config/` (no cleanup-only scripts or template checks). `docs/agents/implementation_plan.md` is not in the tree (only the template). `sequentialthinking` is not registered in this harness; reasoning is recorded here. Prior memory: `docs/memories/2026-09-05-actions-artifact-retention.md`.
- **Rules**: Delete only the cleanup workflow and support that requires that file. Do not edit other workflows, do not drop `retention-days` on uploads, do not add a new cleaner.
- **Evaluation**: verifiable. Gate: `test ! -e .github/workflows/cleanup-artifacts.yml && python -m pytest -q tests/unit/test_artifact_retention.py`. Decorrelated check: PR review of the deleted workflow and the updated retention test (fresh CI runner).
- **Iteration**: If the retention test still names `cleanup-artifacts.yml`, delete that assertion only; do not weaken the `retention-days` bounds.
- **Plan**:
  1. Delete `.github/workflows/cleanup-artifacts.yml`.
  2. Drop `test_cleanup_artifacts_workflow_is_scheduled_and_pinned` and the unused SHA pin regex from `tests/unit/test_artifact_retention.py`.
  3. Update `docs/tests/artifact_retention.md` so it no longer requires the weekly job.
  4. Point the 2026-09-05 memory at this removal so the old plan is not read as a current requirement.
  5. Open a PR against `main` whose description lists the removed files.

## Status
- state: in_progress
- started: 2026-10-19T23:10:00Z
- updated: 2026-10-19T23:15:00Z
- completed:

## Lessons
### Background & Motivation
The owner asked to remove the weekly artifact-cleanup cron. New uploads already set `retention-days: 3` in `.github/workflows/ci.yml`, so the scheduled delete job is no longer wanted.

### Key Challenges & Analysis
- Assumptions: `retention-days` on each upload is the remaining TTL control; nothing else in CI invokes the cleanup workflow by name; the unit test file should stay because it still guards upload retention.
- Counterpoints: Artifacts already stored keep their original TTL until they expire, so removing the sweeper stops draining leftovers older than three days. The owner asked for the cron to go anyway.
- Alternatives: Keep the workflow and disable the schedule only — still leaves a `workflow_dispatch` deleter with `actions: write`. Delete the whole test module — would drop the `retention-days` guard that is not cleanup-only. Chose delete the workflow and the one test that requires it.
- Risks: A future upload that omits `retention-days` would sit for the Actions default (~90 days) with no sweeper. `test_every_upload_artifact_sets_short_retention` still fails that case.

### Feedback & Assistance
- Owner: delete `.github/workflows/cleanup-artifacts.yml` and anything that exists only to support it; update checks so they do not fail; leave other workflows alone; PR description lists what was removed. Done when the PR is open and no cleanup-artifacts workflow remains.

### Learnings
- The only machine check that required the workflow file was `test_cleanup_artifacts_workflow_is_scheduled_and_pinned`. No script or template-setup check referenced it.
