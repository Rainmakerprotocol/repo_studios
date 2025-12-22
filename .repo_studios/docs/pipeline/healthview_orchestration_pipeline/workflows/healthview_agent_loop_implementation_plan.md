---
title: HealthView Agent Execution Loop — Implementation Draft Plan
status: draft
version: 2025-12-21
last_updated: 2025-12-21
updated_at: 2025-12-21
owners:
  - repo_studios_command_center
role:
  - plan
  - pipeline-automation
  - agentic-ops
audience:
  - Copilot
  - Agents
  - Developers
tags:
  - healthview
  - orchestration
  - workflow
  - agent-loop
  - onboarding
  - doc-index
related_files:
  - .repo_studios/Makefile
  - .repo_studios/scripts/utilities/validate_healthview_agent_workflow_spec.py
  - .repo_studios/scripts/orchestrators/healthview/run_healthview_agent_loop.py
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/workflows/healthview_agent_execution_loop.v1.yaml
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/workflows/schema/healthview_agent_execution_loop.schema.json
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier1_healthview_orchestration_pipeline.md
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/tier2_available_scripts_roster.md
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/tier2_full_suite_overview_roster.md
---

# HealthView Agent Execution Loop — Implementation Draft Plan

This document formalizes the agreed design for deterministic, agentic operation of the HealthView
pipeline using Tier-1 as the control plane, Tier-2 as the evidence plane, and Tier-3 as runnable
execution recipes.

See `.github/instructions/markdown.instructions.md` for repo-wide authoring rules.

## Goals

- Provide one canonical agent entry point that always selects the next Tier-1 checkbox deterministically.
- Keep the loop safe (explicit approval gates) and auditable (stable outputs, evidence trail).
- Make onboarding tools discoverable without forcing them into Stage taxonomy.
- Establish a Tier-3 template format that supports today’s operator-guided execution and later agentic
  execution.

## System Context

### Layer boundaries and responsibilities

- Tier-1 is the queue and control plane:
  - Source of truth for “what’s next” is the checkbox report (`checkbox_report.csv`),
    filtered to a Tier-1 allowlist, and ordered deterministically.
  - Tier-1 checkboxes link to Tier-2 records (anchors) and remain the canonical work backlog.
- Tier-2 is the evidence plane:
  - Tier-2 records contain the runnable steps, acceptance criteria, evidence capture, and explicit DONE
    return instructions back to Tier-1.
- Tier-3 is execution glue:
  - Tier-3 YAMLs are runnable recipes invoked from Tier-2, not the loop entry point.

### What already exists (implementation completed)

- Workflow control spec (loop contract):
  - `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/workflows/healthview_agent_execution_loop.v1.yaml`
  - Schema:
    - `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/workflows/schema/healthview_agent_execution_loop.schema.json`
  - Validator:
    - `.repo_studios/scripts/utilities/validate_healthview_agent_workflow_spec.py`
  - Runner:
    - `.repo_studios/scripts/orchestrators/healthview/run_healthview_agent_loop.py`
  - Make targets:
    - `healthview-agent-next`, `healthview-agent-next-compact`, `healthview-agent-validate-workflow`

### Key invariant

- There is exactly one canonical “what’s next” selector:
  - `make -C .repo_studios healthview-agent-next-compact LOG_LEVEL=INFO`

## Agent Instructions

<!-- agents:begin:healthview_agent_loop_contract -->
```yaml
entry_point:
  tier1_anchor: "Agent Execution Loop (Entry Point)"
  selector_command: "make -C .repo_studios healthview-agent-next-compact LOG_LEVEL=INFO"
  selection_source:
    csv: ".repo_studios/docs/pipeline/checkbox_report/outputs/checkbox_report.csv"
    filter:
      tier1_gate_files:
        - ".repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier1_healthview_orchestration_pipeline.md"
    ordering:
      - stage
      - kind_priority
      - line_number
outputs:
  compact_packet:
    - "tier1=<file_path>:<line_number>"
    - "tier2=<relative_link>#<anchor>"
approval_gates:
  require_user_approval_for:
    - begin_implementation
    - check_done
    - update_tier1
    - create_tier3_yaml
post_iteration:
  refresh_queue:
    command: "make -C .repo_studios doc-index LOG_LEVEL=INFO"
```
<!-- agents:end:healthview_agent_loop_contract -->

Operational rules:

- Always run the selector first unless you were handed a specific Tier-2 link from a prior iteration.
- Never check a Tier-1 checkbox until its linked Tier-2 record’s DONE step is satisfied.
- After completing an iteration (Tier-2 DONE + Tier-1 update), run doc-index to refresh the queue.

### Completion Semantics (Reward, Closure, Ceremony)

This loop is designed to optimize for completeness with quality and closure.

- **Reward (Workstream D — Tier-3 YAML):** converting proof into a reusable Tier-3 recipe.
  - If Tier-3 YAML is allowed/required (Tier-2 says allowed and Tier-1 says eligible), complete
    Workstream D and check its checkbox.
  - If Tier-3 YAML is not allowed/required, do not silently skip D: explicitly record
    "Deferred: Tier-3 not allowed" (or similar) in the Tier-2 record.
- **Closure (Tier-2 DONE):** the script no longer requires mindfulness for this stage.
  - DONE means Workstreams A–C are satisfied, Workstream E is satisfied, and Workstream D is either
    satisfied (if required) or explicitly deferred (if not required).
- **Ceremony (Tier-1 checkbox update):** the control plane advances only after closure.

<!-- agents:begin:healthview_iteration_graduation_packet_v1 -->
```yaml
schema: HealthViewIterationGraduationPacketV1
required_fields:
  - stage
  - tier1_checkbox
  - tier2_record
  - reward_status
  - closure_status
  - ceremony_status
  - evidence
reward_status:
  meaning: "Tier-3 YAML created (if allowed/required) OR explicitly deferred with a reason."
closure_status:
  meaning: "Tier-2 DONE criteria satisfied (A–C + E + D decision recorded)."
ceremony_status:
  meaning: "Tier-1 checkbox updated only after Tier-2 DONE."
evidence:
  require:
    - commands_run
    - key_output_paths
    - pytest_results
    - mypy_results_or_na
    - coverage_results_or_exception
    - doc_index_timestamp
```
<!-- agents:end:healthview_iteration_graduation_packet_v1 -->

Example graduation packet (filled; replace values with observed facts):

```yaml
stage: "Stage 1.1 — Test Execution Telemetry"
tier1_checkbox: ".repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier1_healthview_orchestration_pipeline.md:491"
tier2_record: "tier2_roster/tier2_test_execution_telemetry_roster.md#record--collect_test_log_reportspy"
reward_status:
  tier3_required: false
  outcome: "deferred"
  reason: "Tier-2 record indicates Tier-3 not allowed yet"
closure_status:
  tier2_done: false
  remaining:
    - "Workstream E: mypy evidence missing"
    - "Workstream E: coverage evidence/exception missing"
ceremony_status:
  tier1_updated: false
  reason: "Tier-1 updates only after Tier-2 DONE"
evidence:
  commands_run:
    - "make -C .repo_studios healthview-agent-validate-workflow LOG_LEVEL=INFO"
    - "make -C .repo_studios doc-index LOG_LEVEL=INFO"
  key_output_paths:
    - ".repo_studios/docs/pipeline/checkbox_report/outputs/checkbox_report.csv"
  pytest_results: "(paste command + summary)"
  mypy_results_or_na: "(paste command + summary, or N/A + justification)"
  coverage_results_or_exception: "(paste command + summary, or exception record)"
  doc_index_timestamp: "(YYYYMMDD-HHMM)"
```

## Reference Prompts

### Meta Prompt — HealthView Agent Execution Loop (trigger)

Use this as the “start prompt” for an AI coding agent operating inside this repo.

```text
You are a coding agent operating inside the Repo_Studios workspace.

Mission
- Execute exactly one full iteration of the HealthView Agent Execution Loop, end-to-end.
- Do not start a second iteration unless the user explicitly says “continue”.

Non-negotiable constraints
- Tier-1 is the queue and control plane; Tier-2 is the evidence plane; Tier-3 is execution glue.
- The selector output is the source of truth for “what’s next”. Do not pick work manually.
- Never add checkboxes to the Tier-1 entry point section.
- Honor approval gates: you must pause and ask the user for approval before any action tagged as an
  approval gate.
- Follow repo authoring rules: `.github/instructions/markdown.instructions.md`.

Inputs (authoritative)
- Workflow spec:
  `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/workflows/healthview_agent_execution_loop.v1.yaml`
- Tier-1 gate file:
  `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier1_healthview_orchestration_pipeline.md`
- Tier-2 roster location:
  `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/`

Step 0 — Validate + select next work (always)
1) Validate the workflow spec:
   `make -C .repo_studios healthview-agent-validate-workflow LOG_LEVEL=INFO`
2) Select the next Tier-1 checkbox deterministically:
   `make -C .repo_studios healthview-agent-next-compact LOG_LEVEL=INFO`
3) Capture and echo the exact two lines:
   - `tier1=<file_path>:<line_number>`
   - `tier2=<relative_link>#<anchor>`

Step 1 — Execute the selected Tier-2 record (evidence plane)
- Open the Tier-2 link (file + anchor) and follow its record structure.
- Perform Workstream A (Discovery) first, then proceed per that Tier-2 record.
- When you need to change code or docs, do so with minimal, focused edits.
- If the Tier-2 record requires creating or updating a Tier-3 YAML, treat that as an approval-gated
  action.
- As you complete each Tier-2 workstream (A–E), check its checkbox in the Tier-2 record so progress
  is visible in `checkbox_report.csv`.
- Workstream D is conditional:
  - If the Tier-2 record says Tier-3 is not allowed (or Tier-1 does not require Tier-3), do not
    try to complete D.
  - Do explicitly record "Deferred: Tier-3 not allowed" (or similar) in the Tier-2 record so D is
    not silently overlooked.
  - If Tier-3 is allowed/required, complete Workstream D and check its checkbox.

Approval gates (stop and ask)
- Ask approval questions one-at-a-time and include enough context to be unambiguous:
  - include the Stage label (from the Tier-1 heading), and
  - include the exact Tier-2 record anchor or Tier-1 checkbox location.
- Never ask (or offer) to update Tier-1 until after Tier-2 DONE is checked.
- Before “begin implementation” actions: ask the user:
  `Approve begin_implementation (Stage <stage>, tier2=<path>#<anchor>)? (y/n)`
- Before marking work as DONE (Tier-2): ask the user:
  `Approve check_done (Stage <stage>, tier2=<path>#<anchor>)? (y/n)`
- Only after Tier-2 DONE is checked, before updating Tier-1: ask the user:
  `Approve update_tier1 (Stage <stage>, tier1=<file>:<line>)? (y/n)`
- Before creating or editing Tier-3 YAML recipes: ask the user:
  `Approve create_tier3_yaml (Stage <stage>, tier2=<path>#<anchor>)? (y/n)`

Step 2 — Close the loop (only after Tier-2 DONE criteria are satisfied)
1) Update Tier-1 by checking the specific checkbox selected in Step 0.
2) Run doc-index to refresh queue artifacts:
   `make -C .repo_studios doc-index LOG_LEVEL=INFO`
3) Rerun selection once to prove the queue advanced:
   `make -C .repo_studios healthview-agent-next-compact LOG_LEVEL=INFO`

Final report (required)
- Selected work: include the exact `tier1=...` and `tier2=...` lines from Step 0.
- Evidence summary: what changed (files), what commands ran, and the key outputs produced.
- Completion: explicitly state whether Tier-2 DONE criteria are satisfied and whether Tier-1 was
  updated.
- Queue health: include the post-iteration selector output (the new next item).

If blocked
- Stop immediately and report:
  - what you attempted,
  - what failed (exact error),
  - the smallest next action you recommend.
```

### Meta Prompt — HealthView Agent Execution Loop (continuous mode)

Use this when you want the agent to run multiple iterations back-to-back.

```text
You are a coding agent operating inside the Repo_Studios workspace.

Mission
- Execute the HealthView Agent Execution Loop continuously until one of these stop conditions
  occurs:
  - the selector reports no eligible Tier-1 candidates,
  - you hit an approval gate and the user says “no”,
  - you encounter a blocking error,
  - the user says “stop”.

Non-negotiable constraints
- The selector output is the source of truth for “what’s next”. Do not pick work manually.
- Never add checkboxes to the Tier-1 entry point section.
- Honor approval gates every iteration (ask first; do not assume consent carries forward).
- Follow repo authoring rules: `.github/instructions/markdown.instructions.md`.

Inputs (authoritative)
- Workflow spec:
  `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/workflows/healthview_agent_execution_loop.v1.yaml`

Preflight (once)
1) Validate the workflow spec:
   `make -C .repo_studios healthview-agent-validate-workflow LOG_LEVEL=INFO`

Loop (repeat)
1) Select the next Tier-1 checkbox deterministically:
   `make -C .repo_studios healthview-agent-next-compact LOG_LEVEL=INFO`
2) If the command fails with “No Tier-1 checkbox candidates found”, stop and report “queue empty”.
3) Capture and echo the exact two lines:
   - `tier1=<file_path>:<line_number>`
   - `tier2=<relative_link>#<anchor>`
4) Execute the selected Tier-2 record.
5) Stop for approvals when required:
  - Ask approvals one-at-a-time with Stage + target context:
    - `Approve begin_implementation (Stage <stage>, tier2=<path>#<anchor>)? (y/n)`
    - `Approve check_done (Stage <stage>, tier2=<path>#<anchor>)? (y/n)`
    - `Approve update_tier1 (Stage <stage>, tier1=<file>:<line>)? (y/n)` (only after Tier-2 DONE)
    - `Approve create_tier3_yaml (Stage <stage>, tier2=<path>#<anchor>)? (y/n)`
6) Close the iteration only when Tier-2 DONE criteria are satisfied:
   - update Tier-1 checkbox
   - run doc-index:
     `make -C .repo_studios doc-index LOG_LEVEL=INFO`
7) After doc-index, immediately select again to confirm progress, then continue.

Reporting requirements
- Maintain an iteration log. For each iteration, record:
  - the Step-0 selection output (tier1/tier2 lines)
  - what commands ran
  - what files changed
  - whether Tier-2 DONE criteria were satisfied
  - whether Tier-1 was updated

Final report (required)
- Summary table of iterations (count + brief outcomes).
- The last selector output (the new next item, or “queue empty”).
- If you stopped early, state the exact stop condition and what the user should do next.
```

## Human Notes

### Decision: single canonical entry point

We do not want multiple equal entry points because it increases the chance of out-of-order work.

- Canonical entry point is Tier-1:
  - Add a single stable “Agent Execution Loop (Entry Point)” section near the top of the Tier-1 doc,
    outside the Stage taxonomy.
  - Placement: put this section before Stage 1 (so it cannot be confused with stage-gate checklists).
  - The section contains no checkboxes (it must not appear in `checkbox_report.csv`).
- Secondary entry points are allowed but must be guarded:
  - Tier-2 records may include a brief “If you landed here directly” note requiring re-selection.
  - Tier-3 YAML templates should explicitly state they are invoked from Tier-2 (not loop entry).

### Decision: keep specs in docs, keep code in scripts

We want pipeline-specific discoverability without mixing executable code under docs.

Recommended structure:

- Specs and schemas remain under:
  - `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/workflows/`
- Executable tooling remains under:
  - `.repo_studios/scripts/...`
- The Tier-1 entry point links only to make targets (not to raw scripts).

Review option (not recommended): colocate Python scripts under the docs workflows folder. This is
possible, but tends to blur doc vs runtime responsibilities and makes packaging/import rules harder.

### Onboarding recognition (what “discoverable and recognized properly” means)

For onboarding tooling to be “recognized properly” by both humans and agents, it must be:

- Discoverable from Tier-1 via the stable entry point section.
- Discoverable from Tier-2 via a roster record that:
  - defines the onboarding contract,
  - references the make targets,
  - references the Tier-3 template,
  - states the exception scope (base outputs/output location are excluded).
- Traceable in doc-index:
  - headings are stable and unique,
  - links are relative and newline-free,
  - Update Logs record doc-index evidence.

### Decision: dedicated onboarding Tier-2 roster

- The onboarding contract lives in a dedicated roster file under `tier2_roster/` to keep onboarding
  guidance separate from stage-driven Tier-2 work.

### Decision: one shared Tier-3 onboarding template

- Use one Tier-3 template shared across all onboarding jobs to keep execution structure consistent.

### Decision: Tier-3 indexing and file placement

- The onboarding template should be indexed by the Tier-3 index tooling.
- Current state: `.repo_studios/docs/pipeline/tier3_index/generate_tier3_index.py` only scans
  `.repo_studios/docs/pipeline/` for `tier3_*.yaml` files (non-recursive).
- Desired state (this plan): update Tier-3 index discovery so it can index `tier3_*.yaml` located under
  `.repo_studios/docs/pipeline/**/` (including the HealthView pipeline subtree), while excluding
  generated output directories.

## Implementation Plan

### Phase 1 — Install Tier-1 entry point (docs-only)

- Add a new section near the top of the Tier-1 doc:
  - Title: “Agent Execution Loop (Entry Point)”
  - Placement: before Stage 1.
  - Contents:
    - selector command
    - spec path
    - approval gates
    - post-iteration doc-index refresh command
  - Constraint: no checkboxes.

Acceptance criteria:

- A prompt/trigger can link to the Tier-1 entry point anchor and consistently start the loop.
- `make doc-index` continues to generate a stable checkbox report (entry point section does not add
  `[ ]` items).

### Phase 2 — Create a Tier-2 onboarding record (evidence contract)

- Add (or extend) a Tier-2 roster record dedicated to onboarding tools for this pipeline.
  - Location: dedicated onboarding roster under `tier2_roster/` (HealthView pipeline folder).
  - Proposed file:
    - `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/tier2_onboarding_tools_roster.md`
  - The record should:
    - define what counts as “onboarded” for a new script,
    - cite the make targets and expected outputs,
    - instruct how to create a Tier-3 YAML derived from the template,
    - contain an explicit DONE return instruction to update the Tier-1 entry point section if needed.

Acceptance criteria:

- A selected Tier-2 onboarding record can be executed without referring to ad-hoc knowledge.
- The record clearly declares the “base outputs/output location” exception.

### Phase 3 — Add `tier3_agent_pipeline_template.yaml` (execution glue)

- Create a Tier-3 YAML template that is invoked from Tier-2 to run onboarding tasks.
- Placement: keep the template inside the HealthView pipeline subtree so it is co-located with the
  pipeline’s workflow tooling.
- Template should include:
  - metadata (id/name/version)
  - inputs (repo_root, parameters)
  - commands (prefer make targets)
  - expected outputs (paths/patterns)
  - evidence capture checklist (what to paste into Tier-2)
  - stop conditions and common failures

Acceptance criteria:

- A Tier-2 onboarding record can reference the template and instruct how to instantiate it for a
  specific script.
- The template remains KISS: it does not encode selection logic (that stays in the loop spec).

### Phase 4 — Make Tier-3 index discover HealthView templates

- Update `.repo_studios/docs/pipeline/tier3_index/generate_tier3_index.py` to discover `tier3_*.yaml`
  recursively under `.repo_studios/docs/pipeline/`.
- Exclude generated output locations (at minimum):
  - `.repo_studios/docs/pipeline/**/outputs/`
  - `.repo_studios/docs/pipeline/**/reports/`
- Extend `.repo_studios/docs/pipeline/tier3_index/test_tier3_index.py` to cover:
  - discovering a `tier3_*.yaml` under a nested folder (example: HealthView workflows subtree)
  - ensuring `outputs/` is not scanned

Acceptance criteria:

- After `make doc-index`, the Tier-3 index includes the onboarding template entry.

### Phase 5 — Discovery hardening (optional)

- Add a compact “tool index” block inside the Tier-1 entry point section (no checkboxes):
  - list make targets
  - list spec/schema/validator/runner paths
- Ensure doc-index + checkbox report outputs remain clean.

## Reference Prompts

- Start/resume loop:
  - “Open the Tier-1 Agent Execution Loop entry point and run the compact selector. Follow the Tier-2
    record at the returned anchor. Do not check Tier-1 until Tier-2 DONE is satisfied. Refresh doc-index
    at the end.”

## Update Log

| Date | Change | Doc-index evidence | Regression suites |
| --- | --- | --- | --- |
| 2025-12-21 | Draft plan created for review | Pending | Pending |
| 2025-12-21 | Recorded review answers; finalized decisions + phases | Pending | Pending |
| 2025-12-21 | Phase 4 complete: recursive Tier-3 discovery excludes outputs/reports + internal templates/index | Tier-3 scripts index: `tier3_scripts_index.yaml` generated_at=2025-12-21T13:18:18Z | `.venv/Scripts/python.exe -m pytest -q .repo_studios/docs/pipeline/tier3_index/test_tier3_index.py` (28 passed) |
| 2025-12-21 | Phase 5 complete: added compact tool index block to Tier-1 entry point section | `make -C .repo_studios doc-index` (Tier-3 scripts index generated_at=2025-12-21T13:29:43Z) | N/A (doc-only) |
| 2025-12-21 | Defined Reward/Closure/Ceremony semantics + required graduation packet output schema for agents | `make -C .repo_studios doc-index` (Tier-3 scripts index generated_at=2025-12-21T20:27:40Z) | N/A (doc-only) |
