# Phase 7 CI Integration Strategy (Draft 2025-11-04)

## Goals

- Provide a staging plan for surfacing duplicate remediation guardrails in CI without blocking ongoing manual work prematurely.
- Align automation success criteria with GitHub Actions workflows so manual and automated runs share enforcement signals.
- Define rollout increments (warning → gated) tied to validation evidence and metric baselines.

## Pipeline Overview

| Stage | Description | Guardrails Enforced | Artifacts | Blocking Mode |
| --- | --- | --- | --- | --- |
| `preflight-locks` | Runs `verify-command-center-locks` to ensure no active remediation lock before automation jobs start. | Run-lock presence, timestamp freshness | Lock audit logs | Warning → Blocking after two clean sprints |
| `duplicate-scan` | Executes `studio-detect-duplicates` make target (or PowerShell fallback) and uploads duplicate matrix. | `max_files_per_run`, orchestration success, duplicate matrix retention | Duplicate matrix JSON + summary | Warning until automation manifest adoption hits 80% |
| `automation-manifest` | Invokes `generate_automation_manifest.py` with metrics summary capture. | Manifest schema validation, guardrail compliance (`max_files_per_run`, evidence bundle completeness) | `manifest.json`, `metrics_summary.json`, README | Blocking for automation branches; warning for manual pull requests |
| `post-run-tests` | Runs library integration + targeted producer pytest suites. | Test suite pass requirement (`--maxfail=1`), duration tracking | Pytest logs, coverage report (optional) | Blocking for main branch merges |
| `reporting-brief` | Generates weighted progress briefing summary for artifacts touched. | Template completeness, decision log linkage | Markdown briefing, decision log pointer | Warning; manual review required |

## Rollout Phases

1. **Observation (Weeks 1–2)**
   - Enable all jobs in warning mode on automation feature branch.
   - Collect metrics on guardrail compliance, manifest completeness, and test durations.
   - Bookmark failures in `phase_7/CI_ROLLOUT_LOG.md` (to add) with remediation actions.
2. **Stabilization (Weeks 3–4)**
   - Transition `preflight-locks` and `automation-manifest` to blocking for automation-targeted PRs.
   - Keep duplicate scan + reporting jobs advisory while teams adjust workflows.
   - Require PASS validation dry-runs (Phase 6) before toggling blocking modes.
3. **Enforcement (Week 5+)**
   - Expand blocking to `duplicate-scan` and `post-run-tests` once failure rate <5% over two sprints.
   - Publish escalation path for overrides (requires decision log entry and follow-up run).
   - Integrate weighted progress briefing output into release notes or weekly summaries.

## Success Criteria

- All guardrail jobs report PASS/WARN/FAIL with actionable messaging.
- No automation PR merges without manifest + metrics artifacts attached.
- Duplicate matrix retention stays within policy (keep=3 with `.keep` override).
- Weighted briefing generated automatically for each automation run and linked in decision log.

## Dependencies

- `verify-command-center-locks.yaml` workflow available (Phase 4 deliverable).
- Make targets (`studio-detect-duplicates`, `studio-refactor-duplicates`) reviewed and implemented.
- Prompt library directs agents to produce guardrail evidence (Phase 6 complete).
- Metric baseline plan (this phase) guides thresholds for duplicate reduction and coverage.

## Next Actions

- Create `CI_ROLLOUT_LOG.md` template to track warning → blocking transitions.
- Align with developer reviewer on gating criteria and communication plan.
- Update automation README/FAQ once final blocking schedule is approved.
