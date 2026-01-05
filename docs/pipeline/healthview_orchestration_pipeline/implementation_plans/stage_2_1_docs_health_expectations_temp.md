---
title: "TEMP — Stage 2.1 Docs Health: Expectation Hardening Plan"
tier: "Tier-2"
audience:
  - "Copilot"
  - "Agents"
  - "Developers"
owners:
  - "Repo_Studios"
status: "TEMP"
version: "0.1"
updated_at: "2026-01-04"
tags:
  - "healthview"
  - "docs-health"
  - "stage-2.1"
  - "implementation-plan"
  - "expectations"
related_files:
  - ".repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py"
  - ".repo_studios/scripts/producers/generate_doc_index.py"
  - ".repo_studios/scripts/producers/generate_anchor_inventory.py"
  - ".repo_studios/scripts/producers/validate_markdown_anchors.py"
  - ".repo_studios/scripts/producers/verify_docs_integrity.py"
  - ".repo_studios/scripts/producers/validate_metrics_anchor_stubs.py"
  - ".repo_studios/scripts/producers/generate_code_doc_churn_report.py"
  - ".repo_studios/scripts/producers/generate_undocumented_logic_report.py"
  - ".repo_studios/scripts/aggregators/aggregate_docs_health_signals.py"
  - ".repo_studios/Makefile"
---

# TEMP — Stage 2.1 Docs Health: Expectation Hardening Plan

See [.github/instructions/markdown.instructions.md](../../../../.github/instructions/markdown.instructions.md) for repo-wide Markdown rules and [.github/instructions/pipeline_doc_tiers.instructions.md](../../../../.github/instructions/pipeline_doc_tiers.instructions.md) for tiering policy.

## Goals

- Convert Stage 2.1 outputs into decision-ready, low-friction “expectations”.
- Improve traceability from orchestrator → producer → aggregator artifacts.
- Clarify what each step measures (scope), what “good” means, and when “ok” is low-signal.
- Perform work in strict sequence: **one script at a time + verify the matching Make target**, then move on.
- Include documentation alignment work:
  - Tier-1 / Tier-2 / Tier-3 docs (healthview pipeline set).
  - `db_integrations` docs (coverage, correctness, discoverability).

## Non-goals

- No code changes in this TEMP file.
- No “batch editing” across multiple scripts.
- No redesign of the pipeline scoring model in one pass.

## Pass 1 — Scope Lock + Baseline (Run 20260104-1731)

### Invariants (must hold after every change)

- Preserve the Stage 2.1 step set and sequencing unless explicitly approved.
- Preserve the base artifact contract for every bundle: `manifest.json`, `summary.md`, `telemetry.json`.
- Extra artifacts are allowed when they improve usability (examples: `doc_index.csv`, aggregator `signals.csv/.tsv`).
- If a step reports success, the orchestrator must include a resolvable pointer to its run directory and primary artifacts.
- Every script change must be verified via `make -C .repo_studios studio-orchestrate-docs-health` before moving to the next script.

### Baseline inventory (artifact locations, metrics, gaps)

| Step | Role | Run directory | Base artifacts | Key baseline metrics | Known gaps / interpretation notes |
| --- | --- | --- | --- | --- | --- |
| docs_health | orchestrator | `.repo_studios/reports/healthview/orchestrator_reports/docs_health/20260104-1731/` | ✅ | steps=8, failed=0 | Summary is index-only; manifest has null pointers for some step artifacts. |
| doc-index | producer | `.repo_studios/reports/healthview/producer_reports/doc_index/20260104-1731/` | ✅ + `doc_index.csv` | docs=346, headings=2490, links=283 | `summary.md` embeds huge JSON payload; decision-friendly but heavy. |
| anchor-inventory | producer | `.repo_studios/reports/healthview/producer_reports/anchor_inventory/20260104-1731/` | ✅ | docs=142, slugs=779, duplicates=81, missing_h1=7, missing_h2=3 | Fixed in `20260105-0143`: `summary.md` now lists missing-H1 paths and scan roots. |
| markdown_anchor_validation | producer | `.repo_studios/reports/healthview/producer_reports/markdown_anchor_validation/20260104-1731/` | ✅ | files_scanned=142, issues=0 | Orchestrator step detail showed “status=unknown” even though producer is `ok`. |
| docs_integrity_validation | producer | `.repo_studios/reports/healthview/producer_reports/docs_integrity_validation/20260104-1731/` | ✅ | documents_processed=1, mismatches=0 | Scope is narrow by design; summary doesn’t say which document was processed. |
| metrics_anchor_stub_validation | producer | `.repo_studios/reports/healthview/producer_reports/metrics_anchor_stub_validation/20260104-1731/` | ✅ | files_checked=35, anchors_referenced=0, missing=0 | “ok” is low-signal here: no references observed ≠ validated references. |
| code-doc-churn | producer | `.repo_studios/reports/healthview/producer_reports/code_doc_churn/20260104-1731/` | ✅ | churn_modules=3, missing_doc_updates=2 | Doc updates may include generated report paths (risk of overcount). |
| undocumented-logic | producer | `.repo_studios/reports/healthview/producer_reports/undocumented_logic/20260104-1731/` | ✅ | modules_scanned=84, entities_scanned=895, missing_docs=392, coverage=56.2% | Orchestrator manifest does not point to this report (null artifact pointer). |
| docs_health_signals | aggregator | `.repo_studios/reports/healthview/aggregator_reports/docs_health_signals/20260104-1731/` | ✅ (`report.md`/`report.json`) + `signals.csv/.tsv` | overall_score=49.08, critical=4, healthy=1 | Best decision artifact; should be first-read for humans and agents. |

## System Context

Stage 2.1 “Docs Health Overview” currently chains:

- Producers: `doc_index`, `anchor_inventory`, `markdown_anchor_validation`, `docs_integrity_validation`, `metrics_anchor_stub_validation`, `code_doc_churn`, `undocumented_logic`.
- Aggregator: `docs_health_signals`.
- Orchestrator: `docs_health`.

Reference run used for observations:

- Orchestrator bundle: `.repo_studios/reports/healthview/orchestrator_reports/docs_health/20260104-1731/`
- Aggregator bundle: `.repo_studios/reports/healthview/aggregator_reports/docs_health_signals/20260104-1731/`

## Current Observations (from run 20260104-1731)

### Output quantity and readability

- Orchestrator `summary.md` is intentionally tiny (index-like). It’s not sufficient by itself for decisions.
- Aggregator `report.md` is the best “one page” decision artifact today.
- `doc_index/summary.md` is extremely large because it embeds a full JSON payload inline; good for forensics but heavy for quick review.

### Traceability gaps

- Orchestrator `manifest.json` does not consistently record the run directories for some producer steps (even when their bundles exist).
- Orchestrator step detail shows `anchor-validation: success (status=unknown)` while the producer `markdown_anchor_validation` reports `status: ok`.

### Scope/meaning ambiguities

- `metrics_anchor_stub_validation` reports `ok` but also `anchors_referenced: 0` — this is “nothing referenced” more than “validated”.
- `code_doc_churn` doc-updates context may include generated report paths (depending on what’s committed), which can distort the “docs updated” signal.

## Desired “Useful Expectations” (Definition)

For each Stage 2.1 step, the summary should make it easy to answer:

- **What was scanned?** (roots, patterns, counts)
- **What is the pass/fail meaning?** (what does `ok` guarantee?)
- **What are the top 3 actions?** (if non-healthy)
- **Where are the drill-down details?** (explicit artifacts and paths)
- **Are there common false positives / low-signal states?** (e.g., anchors referenced = 0)

## Execution Contract (Strict Sequencing)

We will follow this contract for the remainder of Stage 2.1 hardening:

1. Pick **exactly one script** to change.
2. Before changing anything, identify and record:
   - The script CLI behavior and default inputs.
   - The Make target that exercises it in the Stage 2.1 path.
   - The expected artifact set (base trio + extras).
3. Make the change.
4. Run the Make target.
5. Inspect the new run bundle(s) and verify expectations are met.
6. Only then move to the next script.

## Pass 2 — Acceptance Criteria (Per Script)

**Stop-gate rule:** If any acceptance checkbox fails for the current script, we stop and fix that script before touching the next script (even if the next change seems trivial).

## Work Items (One Script at a Time)

### Script 0 — Orchestrator: record accurate step outputs

**Script**
- `.repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py`

**Make target checkpoint**
- `make -C .repo_studios studio-orchestrate-docs-health`

**Acceptance checklist**

- [ ] Running the Make target completes successfully and produces a new orchestrator run directory under `.repo_studios/reports/healthview/orchestrator_reports/docs_health/<slug>/`.
- [ ] Orchestrator `manifest.json` includes non-null pointers for every executed step (run dir + at least one primary artifact path).
- [ ] Orchestrator step detail does not contradict producer state (example: avoid `status=unknown` when producer status is `ok`).
- [ ] Orchestrator `summary.md` remains brief but includes a reliable “next reads” pointer to the aggregator report directory.

### Script 1 — Producer: anchor inventory (structure decision clarity)

**Script**
- `.repo_studios/scripts/producers/generate_anchor_inventory.py`

**Make target checkpoint**
- `make -C .repo_studios studio-orchestrate-docs-health`

**Acceptance checklist**

- [x] `summary.md` states the scan roots (must include both `docs/` and `.repo_studios/docs/` when configured).
- [x] `summary.md` lists the missing-H1 document paths (up to N), not only the count.
- [x] `summary.md` lists the missing-H2 document paths (already present) and keeps the “H2 missing with H1 present” interpretation.
- [x] `telemetry.json` exposes the full set of per-document counts to support deeper drill-down.

### Script 2 — Producer: markdown anchor validation (status + scope)

**Script**
- `.repo_studios/scripts/producers/validate_markdown_anchors.py`

**Make target checkpoint**
- `make -C .repo_studios studio-orchestrate-docs-health`

**Acceptance checklist**

- [x] `summary.md` states the root + patterns used and the number of files scanned.
- [x] `summary.md` clarifies what constitutes an “issue” (anchor missing, broken internal link, etc.).
- [x] When issues exist, the bundle includes an explicit artifact listing them (or the summary links to the artifact path).

### Script 3 — Producer: docs integrity validation (scope clarity)

**Script**
- `.repo_studios/scripts/producers/verify_docs_integrity.py`

**Make target checkpoint**
- `make -C .repo_studios studio-orchestrate-docs-health`

**Acceptance checklist**

- [x] `summary.md` identifies which document(s) were processed (at minimum: the `index_path` target).
- [x] `summary.md` explains what “integrity” guarantees (what is compared/validated) in one sentence.
- [x] `telemetry.json` includes counts for processed documents and mismatches, and those match the summary.

### Script 4 — Producer: metrics anchor stub validation (low-signal states)

**Script**
- `.repo_studios/scripts/producers/validate_metrics_anchor_stubs.py`

**Make target checkpoint**
- `make -C .repo_studios studio-orchestrate-docs-health`

**Acceptance checklist**

- [ ] If `anchors_referenced == 0`, `summary.md` labels the run as “no references observed” (low-signal) and recommends next checks.
- [ ] If `anchors_referenced > 0`, `summary.md` reports missing anchors (count + representative examples) and how to remediate.
- [ ] `telemetry.json` totals match `summary.md` (files checked, anchors referenced, missing count).

### Script 5 — Producer: code ↔ docs churn (reduce noise)

**Script**
- `.repo_studios/scripts/producers/generate_code_doc_churn_report.py`

**Make target checkpoint**
- `make -C .repo_studios studio-orchestrate-docs-health`

**Acceptance checklist**

- [ ] `summary.md` explicitly states whether generated report paths are considered “doc updates” (or excluded).
- [ ] `summary.md` includes a stable, small “Modules Missing Doc Updates” section that is directly actionable.
- [ ] `telemetry.json` exposes the underlying counts (modules with churn, modules without doc updates, allowlist) and aligns with the summary.

### Script 6 — Producer: undocumented logic (coverage decision clarity)

**Script**
- `.repo_studios/scripts/producers/generate_undocumented_logic_report.py`

**Make target checkpoint**
- `make -C .repo_studios studio-orchestrate-docs-health`

**Acceptance checklist**

- [ ] `summary.md` states scan scope (modules/entities scanned) and the coverage percentage.
- [ ] `summary.md` includes a short “top offenders” callout (top N module paths with lowest coverage / most missing entities).
- [ ] The detailed list remains available for remediation (file+symbol+line where possible).

### Script 7 — Producer: doc index (human vs. machine consumption)

**Script**
- `.repo_studios/scripts/producers/generate_doc_index.py`

**Make target checkpoint**
- `make -C .repo_studios studio-orchestrate-docs-health`

**Acceptance checklist**

- [ ] `summary.md` includes a compact human-readable rollup (counts + top advisories) before any large payload.
- [ ] `summary.md` clearly points to the CSV artifact (`doc_index.csv`) and to the machine-readable payload location.
- [ ] `summary.md` contains an interpretation note for “documents outside docs tree” so the signal is decision-usable.

### Script 8 — Aggregator: make the score actionable

**Script**
- `.repo_studios/scripts/aggregators/aggregate_docs_health_signals.py`

**Make target checkpoint**
- `make -C .repo_studios studio-orchestrate-docs-health`

**Acceptance checklist**

- [ ] `report.md` includes weights and category scores so the overall score is auditable.
- [ ] `report.md` includes “top findings” with stable paths for each non-healthy category.
- [ ] `report.md` calls out low-signal green states (example: integrity ok but narrow scope; metrics stubs ok with 0 references).
- [ ] Tabular exports (`signals.csv` and `signals.tsv`) remain consistent with the markdown report.

## Documentation Alignment Plan

We will update docs only after the corresponding script changes land (one at a time) to avoid getting ahead of implementation.

### Tier-1 / Tier-2 / Tier-3 docs

- Tier-1: Healthview orchestration pipeline narrative must reflect Stage 2.1 definitions.
- Tier-2: Stage 2.1 roster/vertical should enumerate inputs/outputs, failure modes, and expected artifact sets.
- Tier-3: Horizontal script docs should reflect revised summary semantics (especially low-signal states and traceability).

### db_integrations docs

After script-level changes stabilize, update `.repo_studios/command_center/docs/db_integrations/*`:

- Ensure the DB integration docs match the new “expectations” language.
- Ensure navigation points to the current healthview report roots (producer/aggregator/orchestrator).

## Pass 3 — Rollout Wiring (Tests + Docs + Make Target Loop)

### Tests (expected touch points)

As each script is changed, update or add tests adjacent to that script’s tier. The plan expectation is:

- Orchestrator changes: update orchestrator tests under `.repo_studios/tests/tests_command_center/orchestrators/`.
- Producer changes: update producer tests under `.repo_studios/tests/tests_producers/`.
- Aggregator changes: update aggregator tests under `.repo_studios/tests/tests_aggregators/`.

Acceptance for tests in this plan:

- The Make target continues to work as described.
- New/updated tests assert the revised reporting semantics (manifest pointers, status meaning, and low-signal labeling).

### Tier docs (expected touch points)

After each script passes its acceptance checklist, update the tier docs that explain and operationalize that script.

Expected outcomes:

- Tier-1: reflect Stage 2.1 expectations as a stage-level contract (what the stage guarantees and how to consume it).
- Tier-2: reflect step-by-step semantics and the acceptance checklists as the operational implementation guide.
- Tier-3: reflect per-script reporting semantics (especially “ok but low-signal” cases) and artifact contract details.

### db_integrations docs (expected touch points)

After each relevant script passes acceptance, update DB integration docs to keep guidance consistent:

- Ensure any DB integration runbooks that reference docs-health outputs point to the current healthview report roots.
- Ensure terminology matches the expectations language (what each report can and cannot be used to decide).

### Execution loop (the only allowed workflow)

For each script, follow this exact loop:

1. Select the next script (only one).
2. Make the minimal change.
3. Run `make -C .repo_studios studio-orchestrate-docs-health`.
4. Verify the script acceptance checklist using the newly written `summary.md`, `manifest.json`, and `telemetry.json`.
5. If and only if acceptance passes, update the corresponding tests.
6. If and only if tests pass, update Tier-1/Tier-2/Tier-3 docs and the DB integration docs impacted by this script.
7. Only then move to the next script.

## Agent Instructions

<!-- agents:begin:stage_2_1_expectations_plan -->
```yaml
audience: [Copilot, Agents]
constraints:
  - one_script_at_a_time: true
  - verify_make_target_each_step: true
  - no_code_changes_from_this_doc: true
checkpoints:
  - capture_current_state:
      - open_latest_stage_2_1_bundle
      - record_artifact_paths
  - per_script_loop:
      - locate_make_target
      - propose_minimal_change
      - implement_change
      - run_make_target
      - inspect_new_summaries
      - update_docs_only_if_script_is_done
```
<!-- agents:end:stage_2_1_expectations_plan -->

## Human Notes

- This doc is intentionally TEMP and should be replaced by a Tier-2 implementation plan once the first script passes review.
- The sequencing contract is the primary risk-control mechanism: it prevents “docs drifting ahead of code”.

## Reference Prompts

- “Run Stage 2.1 and explain which signals are critical and why.”
- “Which artifacts should a human read first to make a decision?”
- “List any ‘green but low-signal’ statuses and how to interpret them.”

## Update Log

| Date | Change | Doc-index timestamp | Regression suites |
| --- | --- | --- | --- |
| 2026-01-04 | Seed TEMP plan for Stage 2.1 expectation hardening (no code changes). | (not run) | (none) |
