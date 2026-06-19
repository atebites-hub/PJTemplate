<!--
This is the single canonical task-completion checklist for this template.
It is DOCUMENTATION, not the enforcement layer: the hard gate is the pre-commit hook
+ CI (scripts/check-task-compliance.sh) and ./scripts/test-suite.sh. Items marked
(enforced) are blocked automatically; the rest are reviewer-verified.
See docs/agents/enforcement_matrix.md for the three-tier model.
-->

## Summary

<!-- What changed and why. Link the sprint task in docs/agents/implementation_plan.md. -->

## Completion checklist

- [ ] **Task memory** updated under `docs/memories/` for this sprint task _(enforced — C1)_
- [ ] **Reasoning recorded** in the memory: `Context`, `Evaluation`, and `### Key Challenges & Analysis` filled _(enforced — C3)_
- [ ] **`docs/code/` mirror** created/updated for every changed `src/**` code file _(enforced — C2)_
- [ ] **Tests + coverage**: `./scripts/test-suite.sh` passes; coverage meets the floor in `docs/agents/testing_guidelines.md`
- [ ] **Security**: supply-chain gates clean (`./scripts/security/supply-chain-audit.sh`); no high/critical findings
- [ ] **Docs**: `docs/tests/` updated for new tests; affected `docs/agents/` docs reviewed
- [ ] **Scope**: change stays within the current sprint / 10 core documents (else consulted per `AGENTS.md`)

## Notes for reviewers

<!-- Risks, follow-ups, anything intentionally deferred (and where it's tracked). -->
