---
title: "Summarizer Build Template"
tier: working-document
audience:
  - coding_agent
  - human_developer
owners:
  - repo_studios_team@rainmakerprotocol.dev
role:
  - build-template
  - phase-4-artifact
status: active
category: summarizer
schema_version: "1.0.0"
registry_version: "1.0.0"
valid_until: <YYYY-MM-DD>
version: 3.0.0
updated_at: 2026-02-02
tags:
  - stage-12
  - summarizer
  - phase-4
  - <RECORD_ID>
related_files:
  - <SCRIPT_PATH>
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/stage12_templates/manifest.yaml
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/tier2_available_scripts_roster.md
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/implementation_plans/stage12_template_development_plan.md
  - .repo_studios/command_center/scripts/libraries/database_integration.py
---

<!--
EXECUTION_ORDER:
  PROMPT-01-SETUP: 0. INPUT (CHECKPOINT-0, STOP_GATE) → 1. IDENTIFY (CHECKPOINT-1)
  PROMPT-2A-ANALYZE: 2.1-2.4 (CHECKPOINT-2A)
  PROMPT-2B-VERIFY: 2.5 (CHECKPOINT-2B, STOP_GATE)
  PROMPT-34-PREPARE: 3. Tier-3 (CHECKPOINT-3) → 4. DB (CHECKPOINT-4)
  PROMPT-5-GAPS: 5. Gaps (CHECKPOINT-5)
  PROMPT-67-EVIDENCE: 6. Changes (CHECKPOINT-6) → 7. Evidence (CHECKPOINT-7)
  PROMPT-8-ORCHESTRATOR: 8. Orchestrator (CHECKPOINT-8)
  PROMPT-910-CLOSE: 9. Attest (CHECKPOINT-9, STOP_GATE) → 10. Finalize (CHECKPOINT-10, STOP_GATE)

CRITICAL_PATH: CHECKPOINT-0 → CHECKPOINT-2B → CHECKPOINT-9 → CHECKPOINT-10
STOP_GATES: CHECKPOINT-0, CHECKPOINT-2B, CHECKPOINT-9, CHECKPOINT-10
-->

<!-- markdownlint-disable-next-line MD025 -->
# Script Build Template — <SCRIPT_NAME>

> **Purpose:** Working document for Phase 4 per-script processing of <RECORD_ID>.
> This template will evolve as the script is inspected, modified, documented, and tested.
> Upon completion, content transfers to Tier-2 and this doc is archived with `status: archived`.
>
> **Record ID:** <RECORD_ID>
> **Category:** Summarizer
> **Status:** `active`
> **Created:** <YYYY-MM-DD>
> **Completed:** (pending)
>
> **Universal Law:** Every script in the HealthView pipeline SHALL be orchestration-ready,
> agent-discoverable via Tier-3 YAML, and database-integration prepared — regardless of
> whether it is currently assigned to an orchestrator.

---

## Status Values Legend

| Status | Meaning | Agent Action |
|--------|---------|--------------|
| `PENDING` | Not yet verified | Agent must verify and update |
| `PASS` | Requirement met | No action — evidence provided |
| `FAIL` | Requirement not met | Agent must fix before proceeding |
| `SKIP` | Not applicable to this tier | Agent skips this check |
| `N/A` | Explicitly not applicable | Agent acknowledges and moves on |

---

## Requirements Registry

> **Purpose:** Single source of truth for all compliance requirements.
> Other sections reference these IDs instead of repeating requirements.

### Universal Interface Contract (UIC) — Tier A & B

| ID | Requirement | Evidence Location |
|----|-------------|-------------------|
| UIC-001 | `run(argv)` entry point exists | `<path>:<line>` |
| UIC-002 | `run()` returns `dict[str, Any]` | `<path>:<line>` |
| UIC-003 | Return dict has `status` key | `<path>:<line>` |
| UIC-004 | Return dict has `exit_code` key | `<path>:<line>` |
| UIC-005 | `--repo-root` flag supported | `<path>:<line>` |
| UIC-006 | `--log-level` flag supported | `<path>:<line>` |
| UIC-007 | Google-style docstring on `run()` | `<path>:<line>` |
| UIC-008 | No `sys.exit()` inside `run()` | grep confirms |
| UIC-009 | No `input()` prompts | grep confirms |
| UIC-010 | Exceptions return error payload | `<path>:<line>` |

### HOP Bundle Contract (HOP) — Tier A Only

| ID | Requirement | Evidence Location |
|----|-------------|-------------------|
| HOP-001 | Base package: manifest.json | `<path>:<line>` |
| HOP-002 | Base package: summary.md | `<path>:<line>` |
| HOP-003 | Base package: telemetry.json | `<path>:<line>` |
| HOP-004 | Uses `build_topic_path()` or `create_storage()` | `<path>:<line>` |
| HOP-005 | Uses `prune_run_directories()` | `<path>:<line>` |
| HOP-006 | No `latest_*` pointer files | grep confirms |
| HOP-007 | Directory format `YYYYMMDD-HHMM` | `<path>:<line>` |
| HOP-008 | `--artifacts-to-keep` flag supported | `<path>:<line>` |

### Agent Discoverability (AGT) — Tier A & B

| ID | Requirement | Evidence Location |
|----|-------------|-------------------|
| AGT-001 | Tier-3 YAML exists | `<tier3_path>` |
| AGT-002 | Tier-3 `tool.id` matches script | `<tier3_path>` |
| AGT-003 | Tier-3 `invocation.script_path` correct | `<tier3_path>` |
| AGT-004 | Tier-3 `cli_surfaces` complete | `<tier3_path>` |

### Database Integration (DBI) — Tier A & B

| ID | Requirement | Evidence Location |
|----|-------------|-------------------|
| DBI-001 | Uses `create_storage()` for writes | `<path>:<line>` |
| DBI-002 | `DB_INTEGRATION_MARKER:` at write points | `<path>:<line>` |
| DBI-003 | Gated by `REPO_STUDIOS_DB_ENABLED` | `<path>:<line>` |

### Orchestration Readiness (ORC) — Tier A & B

| ID | Requirement | Evidence Location |
|----|-------------|-------------------|
| ORC-001 | Can be dynamically imported | importlib test |
| ORC-002 | Idempotent (safe to re-run) | test confirms |
| ORC-003 | ScriptConfig documented | Section 8.2 |

---

## 0. INPUT: Assignment Contract

<!-- METAPROMPT: PROMPT-01-SETUP -->
<!-- CHECKPOINT_ID: CHECKPOINT-0 -->
<!-- STOP_CONDITION: All REQUIRED inputs have Status = PASS -->
<!-- PROCEED_SIGNAL: "CHECKPOINT-0: Inputs verified — SCRIPT_PATH, RECORD_ID, COMPLIANCE_TIER, TARGET_STAGE confirmed" -->
<!-- REENTRY_POINT: PROMPT-01-SETUP (restart from beginning) -->

<!-- STOP_GATE: TRUE -->

> **Purpose:** Define what information must be provided BEFORE starting this template.
> Agent cannot proceed until all REQUIRED inputs are supplied.

### 0.1 Required Inputs

| Input | Source | Example | Status |
|-------|--------|---------|--------|
| `SCRIPT_PATH` | Assignment or discovery | `.repo_studios/scripts/summarizers/summarize_health_suite.py` | `PENDING` |
| `RECORD_ID` | Tier-2 roster or assigned | `ASR-008` | `PENDING` |
| `COMPLIANCE_TIER` | Classification (A or B) | `A` | `PENDING` |
| `TARGET_STAGE` | Assignment | `Stage 1.1` | `PENDING` |

### 0.2 Optional Inputs

| Input | Source | Default | Status |
|-------|--------|---------|--------|
| `TOPIC` | Derived from script purpose | Script name slug | `PENDING` |
| `ASSIGNEE` | Human or orchestrator | Current agent | `PENDING` |
| `INPUT_BUNDLE` | Upstream producer/orchestrator bundle path | (none) | `PENDING` |

### 0.3 Classification Rules

**How to determine COMPLIANCE_TIER:**

| If script... | Then Tier = | Rationale |
|--------------|-------------|----------|
| Produces HOP bundle (manifest/summary/telemetry) | **A** | Report Generator |
| Transforms input bundle without HOP output | **B** | Transformer |
| Is unclear | **A** | Default to stricter requirements |

**Classification Decision:** Tier {A|B} — {rationale}

<!-- PROCEED_WHEN: All REQUIRED inputs have status PASS -->

> **⚠️ STOP:** Do not proceed to Section 1 until all REQUIRED inputs are provided.

---

## 1. IDENTIFY: Script Identity

<!-- METAPROMPT: PROMPT-01-SETUP -->
<!-- CHECKPOINT_ID: CHECKPOINT-1 -->
<!-- STOP_CONDITION: All fields in identity table populated, 1.1 and 1.2 completed -->
<!-- PROCEED_SIGNAL: "CHECKPOINT-1: Script identity captured — {SCRIPT_NAME} is Tier {A/B}" -->
<!-- REENTRY_POINT: PROMPT-01-SETUP -->

<!-- PROCEED_WHEN: All fields in identity table populated -->

| Field | Value |
|-------|-------|
| **Name** | `<SCRIPT_NAME>` |
| **Path** | `<SCRIPT_PATH>` |
| **Tier Class** | Producer / Consumer / Aggregator / Summarizer / Utility / Library |
| **Compliance Tier** | A (Report Generator) / B (Action Utility) |
| **Lines** | <LINE_COUNT> |
| **Record ID** | <RECORD_ID> |
| **Planned Stage** | <TARGET_STAGE> |

**Compliance Tier Definitions:**

- **Tier A (Report Generator):** Produces HOP bundles (manifest/summary/telemetry). Includes
  Producers, Consumers, Aggregators, Summarizers.
- **Tier B (Action Utility):** Performs actions without HOP bundles. Includes Utilities,
  Configurators, Diagnostics, Libraries.

### 1.1 DESCRIBE: Purpose

<Brief description of what this script does and why>

### 1.2 LIST: Current Capabilities

- <Capability 1>
- <Capability 2>
- <Capability 3>

### 1.3 Verification Log

| Date | Inspector | Findings | Status |
|------|-----------|----------|--------|
| <YYYY-MM-DD> | <agent/human> | <summary of verification> | `PASS` / `FAIL` / `GAPS_FOUND` |

---

## 2. ANALYZE: Current State

<!-- METAPROMPT: PROMPT-2A-ANALYZE -->
<!-- CHECKPOINT_ID: CHECKPOINT-2A -->
<!-- STOP_CONDITION: Sections 2.1-2.4 complete, all Status columns != PENDING -->
<!-- PROCEED_SIGNAL: "CHECKPOINT-2A: Static analysis complete — UIC checklist has {X} PASS, {Y} FAIL" -->
<!-- REENTRY_POINT: PROMPT-2A-ANALYZE -->
<!-- TIER_CHECK: If COMPLIANCE_TIER == "B", skip sections 2.2.2(Tier A), 2.3, 2.4.2 -->

### 2.1 DOCUMENT: CLI Interface

```text
usage: <SCRIPT_NAME> [-h] [--repo-root REPO_ROOT] ...
```

**Flags:**

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--repo-root` | path | auto | Repository root override |
| `--output-dir` | path | HOP default | Output directory for artifacts |
| `--timestamp` | str | auto | ISO timestamp override |
| `--log-level` | choice | INFO | Logging verbosity |
| `--artifacts-to-keep` | int | 5 | Retention budget (Tier A only) |
| <additional flags> | | | |

### 2.2 INSPECT: Entry Points

| Entry | Signature | Returns | Status |
|-------|-----------|---------|--------|
| `main(argv)` | `list[str] \| None` → `int` | Exit code | `PENDING` |
| `run(argv)` | `list[str] \| None` → `dict[str, Any]` | Payload dict | `PENDING` |

#### 2.2.1 Universal Interface Contract (ALL Scripts)

<!-- TIER: A,B -->
<!-- PROCEED_WHEN: All Status columns = PASS or SKIP -->

> **Applies to:** All scripts (Tier A and B)

> **⚠️ MANDATORY — Every script MUST pass this section regardless of Tier Class.**

| Requirement | ID | Status | Evidence |
|-------------|----|--------|----------|
| `run(argv)` entry point exists | UIC-001 | `PENDING` | `<path>:<line>` |
| Returns `dict[str, Any]` (not int) | UIC-002 | `PENDING` | `<path>:<line>` |
| Return dict has `status` key | UIC-003 | `PENDING` | `<path>:<line>` |
| Return dict has `exit_code` key | UIC-004 | `PENDING` | `<path>:<line>` |
| `--repo-root` flag supported | UIC-005 | `PENDING` | `<path>:<line>` |
| `--log-level` flag supported | UIC-006 | `PENDING` | `<path>:<line>` |
| Google-style docstring on `run()` | UIC-007 | `PENDING` | `<path>:<line>` |
| No `sys.exit()` inside `run()` | UIC-008 | `PENDING` | grep confirms |
| No `input()` prompts | UIC-009 | `PENDING` | grep confirms |
| Exceptions return error payload | UIC-010 | `PENDING` | `<path>:<line>` |

#### 2.2.2 Return Payload Contract

<!-- TIER: A -->
<!-- SKIP_IF: compliance_tier == "B" -->

> **Applies to:** Tier A (Report Generators) only  
> **Skip if:** Compliance Tier = B

**Tier A (Report Generators) — REQUIRED keys:**

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `status` | str | ✅ | "ok", "error", "issues", "no_targets" |
| `exit_code` | int | ✅ | 0=success, 1=issues, 2=error |
| `run_dir` | str | ✅ | Path to output bundle directory |
| `output_dir` | str | ✅ | Parent output directory |
| `run_id` | str | ✅ | Timestamp slug (YYYYMMDD-HHMM) |
| `manifest` | dict | ✅ | Full manifest content |
| `telemetry` | dict | ✅ | Full telemetry content |
| `summary` | dict | ✅ | Summary metrics subset |

<!-- TIER: B -->
<!-- SKIP_IF: compliance_tier == "A" -->

> **Applies to:** Tier B (Action Utilities) only  
> **Skip if:** Compliance Tier = A

**Tier B (Action Utilities) — REQUIRED keys:**

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `status` | str | `PASS` | "ok" or "error" |
| `exit_code` | int | `PASS` | 0=success, non-zero=failure |
| `action_taken` | str | `PASS` | Description of action performed |
| `artifacts` | None | `PASS` | Explicit null (no bundle produced) |
| `details` | dict | `PENDING` | Optional additional context |

### 2.3 DOCUMENT: Output Contract

<!-- TIER: A -->
<!-- SKIP_IF: compliance_tier == "B" -->

> **Applies to:** Tier A (Report Generators) only  
> **Skip if:** Compliance Tier = B

**Output root:** `.repo_studios/reports/healthview/summarizer_reports/<TOPIC>/<YYYYMMDD-HHMM>/`

**Artifacts:**

| Artifact | Format | Description |
|----------|--------|-------------|
| `manifest.json` | JSON | Schema version, status, inputs |
| `summary.md` | Markdown | Human-readable summary |
| `telemetry.json` | JSON | Execution metrics |
| <additional artifacts> | | |

### 2.4 ASSESS: Compliance

<!-- PROCEED_WHEN: All compliance checks have Status != PENDING -->

#### 2.4.1 Universal Compliance (Tier A & B)

<!-- TIER: A,B -->

> **Applies to:** All scripts (Tier A and B)

| Requirement | Status | Evidence |
|-------------|--------|----------|
| `run(argv)` returns dict | `PENDING` | <evidence> |
| Status/exit_code in return | `PENDING` | <evidence> |
| Standard CLI flags (repo-root, log-level) | `PENDING` | <evidence> |
| Can be dynamically imported | `PENDING` | `importlib.util` works |
| Idempotent (safe to re-run) | `PENDING` | Multiple runs don't corrupt |

#### 2.4.2 HOP Bundle Compliance (Tier A Only)

<!-- TIER: A -->
<!-- SKIP_IF: compliance_tier == "B" -->

> **Applies to:** Tier A (Report Generators) only  
> **Skip if:** Compliance Tier = B

| Requirement | ID | Status | Evidence |
|-------------|----|--------|----------|
| Base package: manifest.json | HOP-001 | `PENDING` | `<path>:<line>` |
| Base package: summary.md | HOP-002 | `PENDING` | `<path>:<line>` |
| Base package: telemetry.json | HOP-003 | `PENDING` | `<path>:<line>` |
| Uses `build_topic_path()` or `create_storage()` | HOP-004 | `PENDING` | `<path>:<line>` |
| Uses `prune_run_directories()` | HOP-005 | `PENDING` | `<path>:<line>` |
| No `latest_*` pointer files | HOP-006 | `PENDING` | grep confirms |
| Directory format `YYYYMMDD-HHMM` | HOP-007 | `PENDING` | `<path>:<line>` |
| `--artifacts-to-keep` flag supported | HOP-008 | `PENDING` | `<path>:<line>` |

### 2.5 VERIFY: Output Quality

<!-- METAPROMPT: PROMPT-2B-VERIFY -->
<!-- CHECKPOINT_ID: CHECKPOINT-2B -->
<!-- STOP_CONDITION: 2.5.1 QA all PASS, 2.5.5 truth table all Verdict = TRUE -->
<!-- PROCEED_SIGNAL: "CHECKPOINT-2B: Output truth verified — script executed, all claims TRUE" -->
<!-- REENTRY_POINT: PROMPT-2B-VERIFY (critical gate — must re-verify from scratch) -->
<!-- TIER_CHECK: If COMPLIANCE_TIER == "B", skip sections 2.5.2, 2.5.3 -->

> **⚠️ MANDATORY STOP-GATE — DO NOT SKIP**
>
> This section is the **PROOF OF THE SCRIPT**. A script that passes mypy/pytest but produces
> incorrect, misleading, or unverifiable output is **WORTHLESS**. Every claim in the output
> artifacts MUST be verified against ground truth. If any claim is false, the script is BROKEN
> regardless of test results.
>
> **Agent Instruction:** You MUST run the script, read every output file, and verify each claim
> against the actual filesystem/codebase state. Do not proceed until all claims are TRUE.

**MANDATORY: Run script and inspect actual output before completing this section.**

#### 2.5.1 QA Verification

| Check | Command | Result | Evidence | CI/Artifact Link |
|-------|---------|--------|----------|------------------|
| mypy --strict | `python -m mypy --strict <script>` | `PENDING` | <error count or "Success"> | `<CI_URL or N/A>` |
| pytest | `pytest <test_file> -v` | `PENDING` | <X/Y passed in Z.ZZs> | `<CI_URL or N/A>` |
| CLI execution | `python <script> --help` | `PENDING` | <runs without error> | `N/A` |
| Actual run | `python <script> --log-level DEBUG` | `PENDING` | <output path confirmed> | `<artifact_path>` |

#### 2.5.2 summary.md Quality (Aesthetics & Lint)

<!-- TIER: A -->
<!-- SKIP_IF: compliance_tier == "B" -->

> **Applies to:** Tier A (Report Generators) only  
> **Skip if:** Compliance Tier = B

| Check | Status | Evidence |
|-------|--------|----------|
| Markdownlint clean | `PENDING` | `npx markdownlint-cli2 <summary.md>` — 0 errors |
| Single H1 heading | `PENDING` | <heading text> |
| No bare URLs | `PENDING` | <all links are descriptive> |
| Tables properly formatted | `PENDING` | <alignment, header row present> |
| Actionable next-steps section | `PENDING` | <checkbox items present> |
| No hardcoded absolute paths | `PENDING` | <paths are relative or parameterized> |

#### 2.5.3 Machine-Readable Artifacts (JSON Quality)

<!-- TIER: A -->
<!-- SKIP_IF: compliance_tier == "B" -->

> **Applies to:** Tier A (Report Generators) only  
> **Skip if:** Compliance Tier = B

| Check | Status | Evidence |
|-------|--------|----------|
| manifest.json valid JSON | `PENDING` | `python -m json.tool <file>` |
| telemetry.json valid JSON | `PENDING` | `python -m json.tool <file>` |
| Schema version present | `PENDING` | `schema_version` field in manifest |
| Timestamp ISO 8601 format | `PENDING` | `YYYY-MM-DDTHH:MM:SS+00:00` |
| Status field present | `PENDING` | `status: ok\|error\|violations` |
| Consistent key naming | `PENDING` | snake_case throughout |

#### 2.5.4 DB Integration Markers

> **⚠️ MANDATORY — Every script MUST have DB Integration markers for future database migration.**
>
> Even if database writes are currently dormant, the markers MUST be present so that when
> database integration is enabled, the script is ready without code changes.

| Check | Status | Evidence |
|-------|--------|----------|
| `from libraries.database_integration import create_storage` | `PENDING` | `<path>:<line>` |
| DB_INTEGRATION_MARKER comments present | `PENDING` | `<path>:<line>` |
| Marker at manifest.json write | `PENDING` | `<path>:<line>` |
| Marker at summary.md write | `PENDING` | `<path>:<line>` |
| Marker at telemetry.json write | `PENDING` | `<path>:<line>` |
| Uses `create_storage()` for writes | `PENDING` | `<path>:<line>` |
| Marker describes target table/column | `PENDING` | `<path>:<line>` |

**Tier B (Action Utilities) DB Markers:**

| Check | Status | Evidence |
|-------|--------|----------|
| DB_INTEGRATION_MARKER at action log point | `PENDING` | `<path>:<line>` |
| Marker describes action_log table intent | `PENDING` | `<path>:<line>` |

#### 2.5.5 Output Truth Verification (CRITICAL)

<!-- STOP_GATE: TRUE -->
<!-- PROCEED_WHEN: All claims in truth table have Verdict = TRUE -->

> **⚠️ MANDATORY STOP — DO NOT PROCEED UNTIL ALL CLAIMS VERIFIED**
>
> Read every claim in summary.md and manifest.json. Verify each against ground truth.
> A script that reports "0 violations" when it failed to load input data is **LYING**.
> A script that references paths that don't exist is **BROKEN**.

| Claim in Output | Verification Method | Ground Truth | Verdict |
|-----------------|---------------------|--------------|---------|
| <claim from summary.md> | <how to verify> | <actual state> | ✅/❌ |
| <input file path exists> | `Test-Path <path>` | <true/false> | ✅/❌ |
| <upstream data loaded> | Check logs for "loaded" vs "not found" | <loaded/skipped> | ✅/❌ |
| <count/metric is accurate> | Manual count or cross-reference | <actual count> | ✅/❌ |

**If ANY claim is FALSE, the script is BROKEN. Fix it before proceeding.**

### 2.6 Verification Log

| Date | Inspector | Findings | Status |
|------|-----------|----------|--------|
| <YYYY-MM-DD> | <agent/human> | <summary of verification> | `PASS` / `FAIL` / `GAPS_FOUND` |

---

## 3. PREPARE: Tier-3 YAML

> **⚠️ MANDATORY — Every script MUST have a Tier-3 YAML for agent discoverability.**
>
> Agents discover and invoke scripts via Tier-3 metadata. A script without Tier-3 YAML is
> invisible to agents. Even Utilities and Libraries need Tier-3 for agents to know they exist.

<!-- METAPROMPT: PROMPT-34-PREPARE -->
<!-- CHECKPOINT_ID: CHECKPOINT-3 -->
<!-- STOP_CONDITION: Tier-3 YAML exists, 3.2 fields all Status = PASS -->
<!-- PROCEED_SIGNAL: "CHECKPOINT-3: Tier-3 YAML verified at {tier3_path}" -->
<!-- REENTRY_POINT: PROMPT-34-PREPARE -->

### 3.1 LOCATE: Tier-3 YAML

**Expected path:** `<SCRIPT_DIR>/<SCRIPT_NAME>.tier3.yaml` or inline in script inventory

| Check | Status | Evidence |
|-------|--------|----------|
| Tier-3 YAML file exists | `PENDING` | Path: <path> |
| YAML is valid (no syntax errors) | `PENDING` | `python -c "import yaml; yaml.safe_load(...)"` |
| Registered in script inventory | `PENDING` | Inventory record at <location> |

### 3.2 VERIFY: Tier-3 Required Fields

| Field | Status | Value |
|-------|--------|-------|
| `name` | `PENDING` | `<SCRIPT_NAME>` |
| `path` | `PENDING` | `<SCRIPT_PATH>` |
| `category` | `PENDING` | producer/consumer/aggregator/summarizer/utility/library |
| `compliance_tier` | `PENDING` | A (Report Generator) / B (Action Utility) |
| `entry_point` | `PENDING` | `run` |
| `description` | `PENDING` | <one-line description> |
| `inputs` | `PENDING` | List of input parameters with types |
| `outputs` | `PENDING` | Description of return payload |
| `orchestrator_ready` | `PENDING` | `true` / `false` |
| `db_integration_ready` | `PENDING` | `true` / `false` |

### 3.3 REFERENCE: Tier-3 YAML Template

```yaml
# Tier-3 Metadata for <SCRIPT_NAME>
# Agent-discoverable script definition
name: <SCRIPT_NAME>
path: <SCRIPT_PATH>
category: <producer|consumer|aggregator|summarizer|utility|library>
compliance_tier: <A|B>
entry_point: run
description: "<One-line description of what this script does>"
version: "1.0.0"

inputs:
  - name: repo_root
    type: path
    required: false
    description: "Repository root override"
  - name: log_level
    type: choice
    choices: [DEBUG, INFO, WARNING, ERROR]
    default: INFO
    description: "Logging verbosity"
  # <additional inputs>

outputs:
  status: "ok|error|issues"
  exit_code: "0=success, 1=issues, 2=error"
  # <additional outputs per compliance tier>

orchestrator_ready: true
db_integration_ready: true

tags:
  - <tag1>
  - <tag2>

consumers:
  - coding_agent
  - human_developer
  - ci_pipeline
```

### 3.4 Verification Log

| Date | Inspector | Findings | Status |
|------|-----------|----------|--------|
| <YYYY-MM-DD> | <agent/human> | <summary of verification> | `PASS` / `FAIL` / `GAPS_FOUND` |

---

## 4. PREPARE: Database Integration

<!-- METAPROMPT: PROMPT-34-PREPARE -->
<!-- CHECKPOINT_ID: CHECKPOINT-4 -->
<!-- STOP_CONDITION: 4.2 checklist all Status = PASS or N/A -->
<!-- PROCEED_SIGNAL: "CHECKPOINT-4: DB integration markers present — {count} write points covered" -->
<!-- REENTRY_POINT: PROMPT-34-PREPARE -->

> **⚠️ MANDATORY — Every script MUST be database-integration prepared.**
>
> When database integration is enabled, scripts will write to both filesystem AND database.
> The `create_storage()` helper handles this transparently, but scripts must be structured
> correctly for the dual-write to work.

### 4.1 DOCUMENT: DB Schema Intent

**For Tier A (Report Generators):**

| Artifact | Target Table | Key Columns |
|----------|--------------|-------------|
| manifest.json | `hop_manifests` | viewer_slug, topic, run_timestamp, schema_version |
| summary.md | `hop_summaries` | viewer_slug, topic, run_timestamp, content_md |
| telemetry.json | `hop_telemetry` | viewer_slug, topic, run_timestamp, metrics_json |

**For Tier B (Action Utilities):**

| Action | Target Table | Key Columns |
|--------|--------------|-------------|
| Action log | `utility_actions` | script_name, action_taken, status, timestamp |

### 4.2 CHECK: DB Integration Readiness

| Check | Status | Evidence |
|-------|--------|----------|
| Uses `create_storage()` (not raw file writes) | `PENDING` | <evidence> |
| Passes `viewer_slug` correctly | `PENDING` | Empty string or valid slug |
| Passes `topic` correctly | `PENDING` | TOPIC_SLUG constant |
| Passes `timestamp` correctly | `PENDING` | YYYYMMDD-HHMM format |
| All writes go through `storage.write_*()` | `PENDING` | No direct `Path.write_text()` |
| Payload is JSON-serializable | `PENDING` | No datetime objects, Path objects |

### 4.3 REFERENCE: DB Integration Marker Format

```python
# DB_INTEGRATION_MARKER: <table_name>.<column_name> — <description>
storage.write_manifest(manifest)

# DB_INTEGRATION_MARKER: hop_summaries.content_md — Human-readable summary
storage.write_summary({"markdown": summary_md}, format="md")

# DB_INTEGRATION_MARKER: hop_telemetry.metrics_json — Execution metrics
storage.write_telemetry(telemetry)
```

### 4.4 Verification Log

| Date | Inspector | Findings | Status |
|------|-----------|----------|--------|
| <YYYY-MM-DD> | <agent/human> | <summary of verification> | `PASS` / `FAIL` / `GAPS_FOUND` |

---

## 5. IDENTIFY: Gaps

<!-- METAPROMPT: PROMPT-5-GAPS -->
<!-- CHECKPOINT_ID: CHECKPOINT-5 -->
<!-- STOP_CONDITION: All gaps documented, example rows deleted or updated, HIGH priority gaps identified -->
<!-- PROCEED_SIGNAL: "CHECKPOINT-5: Gap analysis complete — {X} HIGH, {Y} MEDIUM, {Z} total gaps" -->
<!-- REENTRY_POINT: PROMPT-5-GAPS -->

### 5.1 LIST: Required Changes

<!-- PROCEED_WHEN: All HIGH priority gaps have Status != OPEN -->

> **Gap Status Values:**
> - `OPEN` — Gap identified, not yet fixed
> - `CLOSED` — Fix applied, awaiting verification
> - `VERIFIED` — Fix confirmed working

> **⚠️ EXAMPLE ROWS BELOW:** The GAP-001 through GAP-017 entries are EXAMPLES showing common gaps.
> **DELETE rows that don't apply.** Keep and update rows that match actual findings.
> **ADD new rows** for gaps not covered by examples.

#### 5.1.1 Universal Compliance Gaps

| Gap ID | Req ID | Description | Priority | Status | Closed Date |
|--------|--------|-------------|----------|--------|-------------|
<!-- EXAMPLE ROWS — Delete if not applicable to this script -->
| GAP-001 | UIC-001 | Missing `run()` entry point | High | `OPEN` | |
| GAP-002 | UIC-002 | `run()` returns int not dict | High | `OPEN` | |
| GAP-003 | UIC-005 | Missing `--repo-root` flag | High | `OPEN` | |
| GAP-004 | UIC-006 | Missing `--log-level` flag | Medium | `OPEN` | |
| GAP-005 | DBI-002 | Missing DB_INTEGRATION_MARKER comments | Medium | `OPEN` | |
| GAP-006 | AGT-001 | Missing Tier-3 YAML | High | `OPEN` | |
<!-- END EXAMPLE ROWS -->

#### 5.1.2 HOP Bundle Gaps (Tier A Only)

| Gap ID | Req ID | Description | Priority | Status | Closed Date |
|--------|--------|-------------|----------|--------|-------------|
<!-- EXAMPLE ROWS — Delete if not applicable to this script -->
| GAP-007 | HOP-004 | Not using `build_topic_path()` | High | `OPEN` | |
| GAP-008 | DBI-001 | Not using `create_storage()` | High | `OPEN` | |
| GAP-009 | HOP-001 | Missing `manifest.json` | High | `OPEN` | |
| GAP-010 | HOP-002 | Absolute paths in summary.md | Medium | `OPEN` | |
| GAP-011 | HOP-005 | No pruning support | Medium | `OPEN` | |
| GAP-012 | HOP-008 | Missing `--artifacts-to-keep` flag | Medium | `OPEN` | |
<!-- END EXAMPLE ROWS -->

#### 5.1.3 Agent/DB Readiness Gaps

| Gap ID | Req ID | Description | Priority | Status | Closed Date |
|--------|--------|-------------|----------|--------|-------------|
<!-- EXAMPLE ROWS — Delete if not applicable to this script -->
| GAP-013 | AGT-001 | No Tier-3 YAML | High | `OPEN` | |
| GAP-014 | AGT-002 | Tier-3 YAML incomplete | Medium | `OPEN` | |
| GAP-015 | DBI-001 | Raw file writes instead of `create_storage()` | High | `OPEN` | |
| GAP-016 | UIC-010 | Payload not JSON-serializable | High | `OPEN` | |
| GAP-017 | DBI-002 | Missing DB_INTEGRATION_MARKER at write points | Medium | `OPEN` | |
<!-- END EXAMPLE ROWS -->

### 5.2 MAP: Alteration Locations

| Location | Change | Standard |
|----------|--------|----------|
| `<path>:<start>-<end>` | <description> | <HOP/Universal requirement> |

### 5.3 Verification Log

| Date | Inspector | Findings | Status |
|------|-----------|----------|--------|
| <YYYY-MM-DD> | <agent/human> | <summary of verification> | `PASS` / `FAIL` / `GAPS_FOUND` |

---

## 6. RECORD: Changes Made

<!-- METAPROMPT: PROMPT-67-EVIDENCE -->
<!-- CHECKPOINT_ID: CHECKPOINT-6 -->
<!-- STOP_CONDITION: All changes logged in 6.1 table with Gap IDs and Commit SHAs -->
<!-- PROCEED_SIGNAL: "CHECKPOINT-6: {N} changes recorded with commit references" -->
<!-- REENTRY_POINT: PROMPT-67-EVIDENCE -->

> **Purpose:** Document all modifications made to the script during this inspection.
> Each change should link to the gap it resolved (if applicable).

### 6.1 Change Log

| # | Category | Location | Description | Gap ID(s) Resolved | Commit SHA |
|---|----------|----------|-------------|-------------------|------------|
| 1 | <category> | `<path>:<line>` | <what was changed> | GAP-XXX | `<sha>` |
| 2 | <category> | `<path>:<line>` | <what was changed> | GAP-XXX | `<sha>` |

<!-- EXAMPLE ROW — Delete after adding real changes:
| 1 | Entry Point | `script.py:45-60` | Added `run(argv)` wrapper returning dict | GAP-001, GAP-002 | `abc123d` |
-->

**Change Categories:**
- `Entry Point` — run()/main() modifications
- `CLI Flags` — argparse additions/changes
- `Return Contract` — payload structure changes
- `Output Format` — manifest/summary/telemetry changes
- `Error Handling` — exception wrapping
- `DB Integration` — create_storage() markers
- `Documentation` — docstrings, comments
- `Testing` — test file additions/modifications
- `Other` — anything else

### 6.2 Verification Log

| Date | Inspector | Findings | Status |
|------|-----------|----------|--------|
| <YYYY-MM-DD> | <agent/human> | <summary of changes recorded> | `PASS` / `FAIL` / `GAPS_FOUND` |

---

## 7. CAPTURE: Evidence

<!-- METAPROMPT: PROMPT-67-EVIDENCE -->
<!-- CHECKPOINT_ID: CHECKPOINT-7 -->
<!-- STOP_CONDITION: Test results captured, code references linked -->
<!-- PROCEED_SIGNAL: "CHECKPOINT-7: Evidence captured — {X} tests, {Y} code references" -->
<!-- REENTRY_POINT: PROMPT-67-EVIDENCE -->

### 7.1 RUN: Tests

| Test File | Test Name | Result | Commit SHA | CI Link |
|-----------|-----------|--------|------------|----------|
| `<test_file>` | `<test_name>` | `PENDING` | `<sha>` | `<CI_URL>` |

### 7.2 LINK: Code References

- `<path>:<start>-<end>` — <description>

### 7.3 Verification Log

| Date | Inspector | Findings | Status |
|------|-----------|----------|--------|
| <YYYY-MM-DD> | <agent/human> | <summary of verification> | `PASS` / `FAIL` / `GAPS_FOUND` |

---

## 8. CONFIGURE: Orchestrator Integration

<!-- METAPROMPT: PROMPT-8-ORCHESTRATOR -->
<!-- CHECKPOINT_ID: CHECKPOINT-8 -->
<!-- STOP_CONDITION: ScriptConfig defined in 8.2, all 8.3 readiness checks = PASS -->
<!-- PROCEED_SIGNAL: "CHECKPOINT-8: Orchestrator config ready — ScriptConfig documented" -->
<!-- REENTRY_POINT: PROMPT-8-ORCHESTRATOR -->

> **Complete this section to enable orchestrator integration.**

### 8.1 DEFINE: ScriptConfig Attributes

> **⚠️ CRITICAL: `supports_output_dir` Safety Warning**
>
> **Default to `False` unless you have a specific reason to override.**
>
> | Setting | Orchestrator Behavior | Pruning Scope | Safety |
> |---------|----------------------|---------------|--------|
> | `False` | Script uses internal `build_topic_path()` default | Topic-scoped ✅ | **SAFE** |
> | `True` | Orchestrator passes generic parent dir | Cross-topic ❌ | **DANGEROUS** |
>
> When `True`, the orchestrator passes `--output-dir producer_reports/` (no topic slug),
> causing the script to create output at the wrong level and prune ALL topics' directories.
>
> **Rule:** If script uses `build_topic_path()` for its default, set `supports_output_dir=False`.

| Attribute | Value | Rationale |
|-----------|-------|-----------|
| `name` | `"<script_name>"` | Basename without `.py` |
| `path` | `"<relative_path>"` | From repo root |
| `supports_output_dir` | `False` (default) | **⚠️ See warning above** — only set `True` if script needs orchestrator path override |
| `supports_artifacts_to_keep` | `True/False` | Does script accept `--artifacts-to-keep`? |
| `uses_argv_kwarg` | `True/False` | Is signature `run(*, argv=...)` or `run(argv)`? |
| `custom_args` | `None` or `[...]` | Any non-standard args needed |

### 8.2 GENERATE: ScriptConfig

```python
ScriptConfig(
    name="<script_name>",
    path="<relative_path>",
    supports_output_dir=False,  # ⚠️ Safe default — preserves topic-aware build_topic_path()
    supports_artifacts_to_keep=<True/False>,  # Script accepts --artifacts-to-keep flag
    uses_argv_kwarg=<True/False>,  # True if run(*, argv=...), False if run(argv)
)
```

> **Note:** Only set `supports_output_dir=True` if the script is specifically designed to
> accept an orchestrator-provided output path AND its pruning logic is safe for cross-topic
> directories. This is rare — most scripts should use `False`.

### 8.3 VERIFY: Orchestration Readiness

<!-- TIER: A,B -->
<!-- PROCEED_WHEN: All Status columns = PASS -->

> **Applies to:** All scripts (Tier A and B)

> **All scripts MUST pass this checklist before being considered "ready" — even if never
> assigned to an orchestrator.**

| Check | ID | Status | Evidence |
|-------|----|--------|----------|
| `run(argv)` callable exposed | UIC-001 | `PENDING` | `from <module> import run` works |
| `run()` returns dict (not int) | UIC-002 | `PENDING` | `isinstance(result, dict)` |
| Return dict has required keys | UIC-003/004 | `PENDING` | Per compliance tier contract |
| Can be dynamically imported | ORC-001 | `PENDING` | `importlib.util.spec_from_file_location` |
| No `sys.exit()` in `run()` | UIC-008 | `PENDING` | grep for `sys.exit` |
| No interactive prompts | UIC-009 | `PENDING` | No `input()` calls |
| Exceptions wrapped gracefully | UIC-010 | `PENDING` | Returns error payload vs raising |
| Idempotent (safe to re-run) | ORC-002 | `PENDING` | Multiple runs don't corrupt state |
| Tier-3 YAML complete | AGT-001—004 | `PENDING` | All required fields populated |
| DB Integration markers present | DBI-001—003 | `PENDING` | `create_storage()` used |

### 8.4 Verification Log

| Date | Inspector | Findings | Status |
|------|-----------|----------|--------|
| <YYYY-MM-DD> | <agent/human> | <summary of verification> | `PASS` / `FAIL` / `GAPS_FOUND` |

---

## 9. ATTEST: Compliance Sign-Off

<!-- METAPROMPT: PROMPT-910-CLOSE -->
<!-- CHECKPOINT_ID: CHECKPOINT-9 -->
<!-- STOP_CONDITION: All attestation checkboxes checked, Inspector row complete -->
<!-- PROCEED_SIGNAL: "CHECKPOINT-9: Attestation complete — signed by {ASSIGNEE} on {DATE}" -->
<!-- REENTRY_POINT: PROMPT-910-CLOSE -->

> **Purpose:** Formal attestation that this inspection was conducted properly.
> Required for audit trail and separation of duties.

### 9.1 Attestation Record

<!-- STOP_GATE: TRUE -->
<!-- PROCEED_WHEN: All attestation checkboxes checked and Inspector row completed -->

| Role | Name | Date | Signature/ID |
|------|------|------|--------------|
| Inspector | <ASSIGNEE> | <YYYY-MM-DD> | <agent_id or initials> |
| Reviewer | <name or N/A> | <YYYY-MM-DD> | <signature or N/A> |
| Approver | <name or N/A> | <YYYY-MM-DD> | <signature or N/A> |

**Role Definitions:**
- **Inspector:** Person or agent who performed the inspection and filled this document
- **Reviewer:** Second pair of eyes who verified evidence quality (optional for low-risk scripts)
- **Approver:** Authority who approved for production use (optional for internal tools)

### 9.2 Attestation Statement

> I attest that:
> - [ ] All sections of this document were completed honestly
> - [ ] All evidence references point to real, verifiable artifacts
> - [ ] All PASS statuses reflect actual verification, not assumption
> - [ ] All gaps identified were either CLOSED+VERIFIED or documented as deferred
> - [ ] The script was actually executed and outputs verified against ground truth

**Inspector attestation date:** `<YYYY-MM-DD>`

---

## 10. FINALIZE: Completion

<!-- METAPROMPT: PROMPT-910-CLOSE -->
<!-- CHECKPOINT_ID: CHECKPOINT-10 -->
<!-- STOP_CONDITION: All 10.1 checkboxes checked, no <PLACEHOLDER> remains, frontmatter updated -->
<!-- PROCEED_SIGNAL: "CHECKPOINT-10: PHASE 4 COMPLETE — {RECORD_ID} ready for production" -->
<!-- REENTRY_POINT: PROMPT-910-CLOSE (final gate — restart close sequence) -->

> **⚠️ This section is the FINAL GATE. Do not mark complete until ALL items are checked.**
>
> The build.md is NOT done when you fill in the sections. It is done when:
>
> 1. The script has been RUN and outputs verified TRUE
> 2. The Tier-3 YAML exists and is validated
> 3. The roster checkboxes are all checked including DONE
> 4. This document's frontmatter shows `status: complete`

### 10.1 CHECK: Build Document Completion

<!-- STOP_GATE: TRUE -->
<!-- PROCEED_WHEN: All checkboxes checked -->

**Discovery & Analysis:**

- [ ] Section 1 (Script Identity) — All fields populated
- [ ] Section 2.1 (CLI Interface) — Flags documented from `--help` output
- [ ] Section 2.2 (Entry Points) — Signatures verified against code
- [ ] Section 2.4 (Compliance Assessment) — All checks have evidence

**Implementation & Testing:**

- [ ] Section 5 (Gap Analysis) — Gaps identified with priority/effort
- [ ] Section 6 (Changes Made) — All modifications documented with line numbers
- [ ] Section 7 (Evidence) — Test results captured (pytest/mypy/coverage)

**Truth Verification (CRITICAL):**

- [ ] Section 2.5.1 — QA tests passed (mypy, pytest, CLI execution)
- [ ] Section 2.5.5 — Output truth verified: **SCRIPT WAS ACTUALLY RUN**
- [ ] Section 2.5.5 — Every claim in output artifacts verified against ground truth
- [ ] **If any claim was FALSE, it was FIXED before checking this box**

**Tier-3 & DB Integration:**

- [ ] Section 3 — Tier-3 YAML created/updated and validated
- [ ] Section 4 — DB Integration markers present at all write points

**Orchestrator Readiness:**

- [ ] Section 8.3 — All orchestration readiness checks pass

### 10.2 UPDATE: Tier-2 Roster

> **After completing Section 10.1, update the parent Tier-2 roster document.**

**Roster location:** `../tier2_<stage>_roster.md`

**Workstream checkboxes to update:**

```markdown
#### Implementation Workstreams (checkbox-driven) — <SCRIPT_NAME>

- [x] A. Discovery — confirm CLI surfaces, outputs, retention, and consumers
- [x] B. Plan — draft gap closure plan
- [x] C. Implement — code changes applied (or N/A if already compliant)
- [x] D. Evidence — tests passing (N/N)
- [x] E. Bug fix — issues addressed (or N/A if none found)
- [x] F. Output truth verification — script run, output claims verified TRUE
- [x] G. Tier-3 YAML — created/updated <tier3_name>.yaml
- [x] H. Orchestrator integration — ScriptConfig documented (Section 8.2)
- [x] DONE — Phase 4 compliance complete (<YYYY-MM-DD>)
```

**Roster update checklist:**

- [ ] Located script record in Tier-2 roster
- [ ] Checked workstream boxes A through H
- [ ] Added DONE marker with date
- [ ] Updated `phase4_build_doc` field to point to this document
- [ ] Updated `tier3_yaml` field to point to Tier-3 YAML path
- [ ] Tier-2 roster file SAVED

### 10.3 UPDATE: Tier-1 Pipeline Registry

> **After completing Section 10.2, update the Tier-1 pipeline document.**

**Registry location:** `{HOP_ROOT}/tier1_healthview_orchestration_pipeline.md`

**Registry entry to add/update:**

| Script | Record ID | Stage | Tier | Status | Build Doc | Last Verified |
|--------|-----------|-------|------|--------|-----------|---------------|
| <SCRIPT_NAME> | <RECORD_ID> | <TARGET_STAGE> | <COMPLIANCE_TIER> | ✅ Phase 4 Complete | `<BUILD_DOC_PATH>` | <YYYY-MM-DD> |

**Registry update checklist:**

- [ ] Opened Tier-1 pipeline document
- [ ] Located "Script Registry" or "Available Scripts" table
- [ ] Added/updated row for this script
- [ ] Status set to "✅ Phase 4 Complete"
- [ ] Build Doc path is correct
- [ ] Tier-1 pipeline document SAVED

### 10.4 CLOSE: Document Finalization

**Update this document's frontmatter:**

```yaml
status: complete        # Changed from: active
version: "1.0.0"        # Changed from: working version
updated_at: <YYYY-MM-DD>
```

**Final verification:**

- [ ] Frontmatter `status` changed to `complete`
- [ ] Frontmatter `version` changed to `1.0.0`
- [ ] Frontmatter `updated_at` reflects completion date
- [ ] No `<PLACEHOLDER>` variables remain in document

### 10.5 CONFIRM: Phase 4 Complete

**Completion timestamp:** `<YYYY-MM-DD HH:MM UTC>`

**Summary:**

| Aspect | Status | Evidence |
|--------|--------|----------|
| Universal compliance | ✅ | Section 2.2.1 all checked |
| HOP bundle compliance | ✅ | Section 2.4.2 all checked |
| Output truth verified | ✅ | Section 2.5.5 — all claims TRUE |
| Tier-3 YAML | ✅ | `<tier3_yaml_path>` |
| DB Integration ready | ✅ | `<path>:<line>`, `<path>:<line>`, `<path>:<line>` |
| Orchestrator ready | ✅ | Section 8.3 all checked |
| Tier-2 roster updated | ✅ | Workstreams A-H + DONE checked, file SAVED |
| Tier-1 registry updated | ✅ | Script entry added/updated, file SAVED |

**Propagation confirmation:**
- Tier-2 roster: `<roster_path>` — SAVED
- Tier-1 registry: `<tier1_path>` — SAVED

**Next step:** If this script needs orchestrator wiring, proceed to Phase 4B using
`tier2_promotion_template.md`.

---

## 11. MAINTAIN: Doc Hygiene

> **Purpose:** After each inspection cycle, clean the document to reflect CURRENT state only.
> Historical context lives in Verification Logs, not in section content.

### 11.1 CHECK: Hygiene Checklist

- [ ] All PENDING statuses resolved (changed to PASS/FAIL/SKIP)
- [ ] All `<placeholder>` values replaced with actual data
- [ ] All gaps either CLOSED+VERIFIED or documented as deferred
- [ ] Stale language removed (no "was", "used to", "previously")
- [ ] Evidence reflects most recent verification
- [ ] Verification Logs updated with inspection date

### 11.2 APPLY: Language Standards

**Use current tense:**
- ✅ "Script returns dict with status key"
- ❌ "Script was updated to return dict"

**Use facts, not narrative:**
- ✅ "Entry point: `run(argv)` at line 45"
- ❌ "We added a run(argv) entry point during Phase 4"

### 11.3 IDENTIFY: Re-Inspection Triggers

This document should be re-inspected when:
- [ ] Requirements Registry changes (new UIC/HOP/AGT/DBI/ORC requirements)
- [ ] Script code is modified
- [ ] Upstream dependencies change
- [ ] Orchestrator integration changes
- [ ] Quarterly audit cycle

---

## 12. REFERENCE: Template Variables

> **Placeholder Conventions:**
> - `<UPPER_SNAKE>`: User-fillable text values (e.g., `<SCRIPT_NAME>`, `<RECORD_ID>`)
> - `<lower_snake>`: Structural references (e.g., `<path>`, `<line>`, `<tier3_path>`)
> - ISO timestamps: `<YYYY-MM-DD>`, `<YYYYMMDD-HHMM>` (kept as-is for standard compliance)

Replace these placeholders when using this template:

| Variable | Description |
|----------|-------------|
| `<SCRIPT_NAME>` | Script filename (e.g., `summarize_health_suite.py`) |
| `<SCRIPT_PATH>` | Full path (e.g., `.repo_studios/scripts/summarizers/summarize_health_suite.py`) |
| `<SCRIPT_DIR>` | Script directory (e.g., `.repo_studios/scripts/summarizers`) |
| `<RECORD_ID>` | ASR record ID (e.g., `ASR-008`) |
| `<YYYY-MM-DD>` | ISO date |
| `<LINE_COUNT>` | Script line count |
| `<TARGET_STAGE>` | Destination stage (e.g., `Stage 4.2`) |
| `<TOPIC>` | Topic slug (e.g., `health_suite_summary`) |
| `<ASSIGNEE>` | Person or agent performing the inspection |
| `<registry_version>` | Version of Requirements Registry in effect |
| `<valid_until>` | Date when this inspection expires (typically +90 days) |
| `<path>:<line>` | Line reference format (e.g., `.repo_studios/scripts/summarizers/script.py:123`) |
| `<path>:<start>-<end>` | Line range format (e.g., `.repo_studios/scripts/summarizers/script.py:45-67`) |
| `<CI_URL>` | CI job URL (e.g., `https://github.com/org/repo/actions/runs/12345`) |
| `<sha>` | Git commit SHA (short form, e.g., `abc123d`) |
| `<artifact_path>` | Path to archived artifact with optional hash |
| `<agent_id>` | Agent identifier (e.g., `copilot-v4`, `claude-3.5`) |

---

## 13. LOG: Version History

| Version | Date | Changes |
|---------|------|---------|
| 3.0.0 | 2026-02-02 | Full rewrite derived from Producer v3.5.0; added Section 0 (INPUT with INPUT_BUNDLE), Requirements Registry, EXECUTION_ORDER block, CHECKPOINT/STOP_GATE markers throughout; updated example paths for summarizer context |
| 2.1.0 | 2026-01-28 | Enhanced Section 7 with complete conclusion workflow (truth verification, roster update, finalization steps) |
| 2.0.0 | 2026-01-26 | Added Universal Law, Compliance Tiers, Tier-3 YAML, DB Integration Preparation, Orchestration Readiness Checklist, ScriptConfig section |
| 1.0.0 | (original) | Initial template with HOP compliance focus |
