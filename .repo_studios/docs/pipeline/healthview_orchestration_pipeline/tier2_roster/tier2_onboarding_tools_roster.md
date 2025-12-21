---
title: "Tier-2 Roster — Onboarding Tools (Agent Loop Evidence Contract)"
tier: tier-2
audience:
  - coding_agent
  - human_developer
owners:
  - repo_studios_team@rainmakerprotocol.dev
role:
  - roster
  - onboarding
status: draft
version: 0.1.0
updated_at: 2025-12-21
tags:
  - pipeline
  - healthview
  - hop
  - tier-2
  - onboarding
  - agent-loop
related_files:
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier1_healthview_orchestration_pipeline.md
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/workflows/healthview_agent_execution_loop.v1.yaml
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/workflows/tier3_agent_pipeline_template.yaml
  - .repo_studios/Makefile
  - .github/instructions/markdown.instructions.md
  - .github/instructions/pipeline_doc_tiers.instructions.md
  - .github/instructions/tier_doc_operating_model.instructions.md
  - REPORT_NAMING_STANDARDS.md
---

<!-- markdownlint-disable-next-line MD025 -->
# Tier-2 Roster — Onboarding Tools (Agent Loop Evidence Contract)

> **Purpose:** This Tier-2 roster defines the onboarding evidence contract for HealthView tooling.
> It tells humans and agents how to promote a script from “exists in repo” into “recognized and
> runnable” within the deterministic agent loop.
>
> **Tier-1 source:**
> `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier1_healthview_orchestration_pipeline.md`.
> **Loop contract source:**
> `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/workflows/healthview_agent_execution_loop.v1.yaml`.
> **Last synced with Tier-1:** 2025-12-21.
>
> Standards: `.github/instructions/markdown.instructions.md` (reviewed 2025-12-21) and
> `.github/instructions/pipeline_doc_tiers.instructions.md` (reviewed 2025-12-21).

---

## 0. Instruction Block for Editors & AI Assistants

- This document inherits terminology and loop semantics from the Tier-1 spine and the workflow spec.
- Preserve the canonical Tier-2 section order.
- Do not encode selection logic here; selection lives in the workflow spec + runner.
- Treat “onboarded” as an evidence-backed claim: document commands, outputs, and proofs.
- After meaningful checklist edits, run `make -C .repo_studios doc-index` and record evidence.

---

## 1. Goals & Success Criteria

1. Provide a single, executable onboarding contract that does not require ad-hoc tribal knowledge.
1. Define what counts as “onboarded” for a script in HealthView.
1. Capture the explicit exception: onboarding tools may emit outputs outside the HOP bundle root.

**Success criteria:**

- A new script can be onboarded by following this document end-to-end.
- The onboarding record includes:
  - required make targets,
  - expected outputs (including the base output exception),
  - evidence capture requirements,
  - an explicit DONE return instruction to Tier-1.

---

## 2. System Context

### 2.1 Tier Alignment

- **Tier-1:** HealthView Orchestration Pipeline (control plane and checkbox queue)
- **Tier-2 scope:** Onboarding tools contract (evidence plane)
- **Tier-3 (future):** Onboarding execution template invoked from Tier-2 (not loop entry point)

### 2.2 Key invariant: deterministic loop entry point

The canonical selector is:

- `make -C .repo_studios healthview-agent-next-compact LOG_LEVEL=INFO`

It selects a Tier-1 checkbox and returns a Tier-2 anchor to execute.

### 2.3 Onboarding contract exception: base outputs and output location

Onboarding work is allowed to run tools whose outputs do not match the HOP bundle contract.

- This roster governs onboarding evidence for tools and scripts.
- It does not retroactively require every onboarding tool to emit a HealthView bundle.
- Once a tool is promoted into an orchestrator stage, the HOP output contract becomes gating.

### 2.4 Tier-3 onboarding execution template

Tier-2 records may reference the HealthView-local Tier-3 template:

- `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/workflows/tier3_agent_pipeline_template.yaml`

How to use it:

1. Copy the template into a new Tier-3 YAML named `tier3_<topic>.yaml`.
1. Replace placeholders with the specific make target(s) and expected outputs.
1. Reference the new Tier-3 YAML from the Tier-2 record that invokes it.

---

## 3. Records & Contracts

### 3.1 Records Index

- ONB-001 — Onboarding tools evidence contract — [ONB-001](#onb-001-onboarding-tools-evidence-contract)

### 3.2 Record — ONB-001 Onboarding tools evidence contract

#### ONB-001 Onboarding tools evidence contract

**Scope:**

- Applies when onboarding a script into HealthView discovery surfaces.
- Applies when creating or updating Tier-2 roster records for “eligible / available scripts.”
- Applies when claiming a tool is “recognized properly” by humans and agents.

**Definition: what “onboarded” means (Tier-2 evidence contract):**

A script is considered onboarded when all items below are satisfied.

- Documentation wiring:
  - The script is listed in the appropriate Tier-2 roster (stage roster or holding roster).
  - The Tier-2 roster record provides an anchor that Tier-1 can link to.
- Runnable entry points:
  - The Tier-2 record cites the make target(s) used to run or validate the script.
  - The record includes at least one concrete invocation (PowerShell commands).
- Evidence captured:
  - The record captures the observed output paths and key artifacts.
  - The record captures a minimal "what changed" summary if code was modified.
- Explicit exceptions declared:
  - If outputs are not under the HOP bundle root, the record states the exception clearly.

**Required commands (preferred):**

- Validate workflow spec:
  - `make -C .repo_studios healthview-agent-validate-workflow LOG_LEVEL=INFO`
- Select next Tier-1 work item (compact packet):
  - `make -C .repo_studios healthview-agent-next-compact LOG_LEVEL=INFO`
- Refresh queue and doc inventories:
  - `make -C .repo_studios doc-index LOG_LEVEL=INFO`

**Evidence capture checklist (paste into Tier-2 records as needed):**

- Command run:
  - `<paste command>`
- Timestamp:
  - `<YYYY-MM-DD HH:MM>`
- Outputs observed:
  - `<paste output paths>`
- Artifacts observed:
  - `<list artifacts>`
- Notes:
  - `<short notes: anomalies, exceptions, or follow-ups>`

**Stop conditions (do not proceed without escalation):**

- The record cannot identify a stable make target or CLI entry point.
- The record cannot state where outputs were written.
- The record relies on absolute paths or machine-specific configuration.

---

## 4. Agent Instructions

<!-- agents:begin:healthview_onboarding_contract -->
```yaml
intent: "Onboard a HealthView tool with evidence"
entry_point:
  selector_command: "make -C .repo_studios healthview-agent-next-compact LOG_LEVEL=INFO"
required_evidence:
  - "command_run"
  - "timestamp"
  - "outputs_observed"
  - "artifacts_observed"
  - "exception_declared_if_not_hop_bundle"
post_iteration:
  refresh_doc_index_command: "make -C .repo_studios doc-index LOG_LEVEL=INFO"
```
<!-- agents:end:healthview_onboarding_contract -->

---

## 5. DONE Return Instructions (Tier-2 → Tier-1)

When the onboarding work is complete:

1. Ensure the Tier-2 roster record contains the evidence captured (commands, outputs, exceptions).
1. If Tier-1 routing needs a new link, update Tier-1 to reference the Tier-2 anchor.
1. Run `make -C .repo_studios doc-index LOG_LEVEL=INFO`.

**DONE:**

- [ ] ONB-001 DONE — onboarding contract applied, evidence captured, and Tier-1 routing updated if
  required.

---

## Update Log

| Date | Change | Doc-index evidence | Regression suites |
| --- | --- | --- | --- |
| 2025-12-21 | Drafted onboarding evidence contract (ONB-001). | make doc-index | N/A |
