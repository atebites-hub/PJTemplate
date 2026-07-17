# Task Memory: Pyroscope Continuous Profiling

## Description
- Add continuous profiling (Grafana Pyroscope) as the fourth observability pillar beside logs (Loki), metrics (Prometheus), and traces (OTLP → Alloy → Tempo).
- Wire the Python SDK + `pyroscope-otel` span bridge so Tempo can deep-link to flamegraphs.
- Provide infra configs (Pyroscope server + Grafana datasource + Tempo tracesToProfiles) matching the existing `config/infra/` pattern.

## Related Memories
- None prior for profiling; observability spine lives under `src/server/logging/` and `config/infra/`.

## Task (TCREI)
- **Task**: Integrate Pyroscope continuous profiling cleanly with the existing OpenTelemetry / Grafana / Prometheus stack.
- **Scope**: inline
- **Context**: Code `src/server/logging/{telemetry,tracing,metrics,logging}.py`, `src/server/config/settings.py`, `config/defaults.toml`; infra `config/infra/{alloy,grafana,loki,prometheus,tempo}/` (config-only, no compose); docs `docs/code/server/logging/*.md` + settings.md; packages `pyroscope-io` + `pyroscope-otel` (span profiles); Grafana Tempo `tracesToProfiles` → Pyroscope uid `pyro`.
- **Rules**: Off by default (`profiling_enabled = false`); feature-flagged like metrics/tracing; idempotent setup/shutdown; no secrets in TOML; match existing telemetry module patterns; update `docs/code/` mirrors; supply-chain pins via pip-compile hashes.
- **Evaluation**: verifiable. Gate: `./scripts/test-suite.sh`. Risks locked by unit tests (disabled path no-op, enabled path configure kwargs, idempotency, span processor registration when tracing on). Non-trivial infra/docs changes: re-read telemetry docs for consistency.
- **Iteration**: After green suite, refine docs if package API differs at install time.
- **Plan**:
  1. Settings + `defaults.toml` (`observability.profiling_enabled`, `[profiling]` block)
  2. `src/server/logging/profiling.py` (configure/shutdown/tag helpers)
  3. Wire `telemetry.py` (order: logging → tracing → profiling → metrics); shutdown profiling on exit
  4. Span profiles: attach `PyroscopeSpanProcessor` when profiling + tracing + `span_profiles_enabled`
  5. Infra: `config/infra/pyroscope/`, Grafana datasource + Tempo tracesToProfiles, dashboard README UIDs
  6. Deps in `requirements.in` / `pyproject.toml`; `pip-compile`
  7. Unit tests + `docs/code` mirrors

## Status
- state: completed
- started: 2026-07-16T20:15:00-07:00
- updated: 2026-07-16T20:30:00-07:00
- completed: 2026-07-16T20:30:00-07:00

## Lessons
### Background & Motivation
Template already has L/M/T correlation; continuous profiling is the missing fourth pillar and fits Grafana LGT(P) stack.

### Key Challenges & Analysis
- Assumptions: App → Pyroscope HTTP push is simpler than Alloy OTLP profiles for a first cut; no compose file means config-only infra like other backends.
- Counterpoints: Always-on profiling adds overhead and stack weight; keep off by default.
- Alternatives: Parca, ad-hoc py-spy, pure OTel eBPF (Linux-only, weaker local macOS story).
- Risks: Native extension issues on some platforms; multi-process workers each need their own agent; shutdown symmetry (metrics already lack teardown—profiling will have shutdown).

### Feedback & Assistance
- User: proceed; must fit OpenTelemetry/Grafana/Prometheus cleanly.

### Learnings
- Span profiles require both `pyroscope-io` and `pyroscope-otel` (`PyroscopeSpanProcessor` on the OTel `TracerProvider`).
- Tempo provisioning uses `tracesToProfiles.datasourceUid` + `profileTypeId` (e.g. `process_cpu:cpu:nanoseconds:cpu:nanoseconds`).
- basedpyright in this repo fails the suite on *warnings* (not only errors); tests must avoid private-import usage and unknown lambda types.
- Gate `./scripts/test-suite.sh` green: 29 passed after integration.

