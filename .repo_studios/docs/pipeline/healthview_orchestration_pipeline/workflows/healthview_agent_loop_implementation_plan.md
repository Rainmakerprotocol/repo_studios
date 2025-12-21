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
