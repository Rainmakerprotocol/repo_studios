---
title: "Utility Build Template"
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
category: utility
schema_version: "1.0.0"
registry_version: "1.0.0"
valid_until: <YYYY-MM-DD>
version: 1.0.0
updated_at: 2026-02-04
tags:
  - stage-12
  - utility
  - phase-4
  - <RECORD_ID>
related_files:
  - <SCRIPT_PATH>
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/stage12_templates/manifest.yaml
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/tier2_available_scripts_roster.md
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/implementation_plans/stage12_template_development_plan.md
---

<!--
EXECUTION_ORDER:
  PROMPT-00-DETECT: 0. DETECT (CHECKPOINT-0, STOP_GATE, BRANCH_POINT)
    ├─ B-CLI: Continue to Section 1
    └─ B-LIB: Jump to Section 11 (Library Checklist)
  PROMPT-01-SETUP: 1. IDENTIFY (CHECKPOINT-1)
  PROMPT-2A-ANALYZE: 2.1-2.3 (CHECKPOINT-2A)
  PROMPT-2B-VERIFY: 2.4 (CHECKPOINT-2B, STOP_GATE)
  PROMPT-34-PREPARE: 3. Tier-3 (CHECKPOINT-3) → 4. DB (CHECKPOINT-4)
  PROMPT-5-GAPS: 5. Gaps (CHECKPOINT-5)
  PROMPT-67-EVIDENCE: 6. Changes (CHECKPOINT-6) → 7. Evidence (CHECKPOINT-7)
  PROMPT-8-UTILITY: 8. ScriptConfig (CHECKPOINT-8)
  PROMPT-910-CLOSE: 9. Attest (CHECKPOINT-9, STOP_GATE) → 10. Finalize (CHECKPOINT-10, STOP_GATE)

CRITICAL_PATH: CHECKPOINT-0 → CHECKPOINT-2B → CHECKPOINT-9 → CHECKPOINT-10
STOP_GATES: CHECKPOINT-0 (branch), CHECKPOINT-2B, CHECKPOINT-9, CHECKPOINT-10
BRANCH_POINT: CHECKPOINT-0 (B-CLI → full path, B-LIB → Section 11)
-->

<!-- markdownlint-disable-next-line MD025 -->
# Utility Build Template — <SCRIPT_NAME>

> **Purpose:** Working document for Phase 4 per-script processing of <RECORD_ID>.
> This template handles utilities — scripts that perform actions WITHOUT producing HOP bundles.
> Upon completion, content transfers to Tier-2 and this doc is archived with `status: archived`.
>
> **Record ID:** <RECORD_ID>
> **Status:** `active`
> **Created:** <YYYY-MM-DD>
> **Completed:** (pending)
>
> **Utility Principle:** Utilities perform actions or provide helper functions WITHOUT
> producing HOP bundles. They fall into two sub-classes:
> - **B-CLI:** Command-line utilities with `run(argv)` that produce rawview outputs
> - **B-LIB:** Pure libraries that export functions/classes (no CLI, no bundle output)
>
> **Compliance Tier:** B (Non-HOP) — Utilities do NOT produce manifest/summary/telemetry bundles.

> **⚠️ IMPORTANT:** If a script produces HOP bundles (manifest/summary/telemetry), it should
> be reclassified as Producer/Consumer/Aggregator/Summarizer and use the appropriate template.

---

## Status Values Legend

| Status | Meaning | Agent Action |
|--------|---------|--------------|
| `PENDING` | Not yet verified | Agent must verify and update |
| `PASS` | Requirement met | No action — evidence provided |
| `FAIL` | Requirement not met | Agent must fix before proceeding |
| `SKIP` | Not applicable to this sub-class | Agent skips this check |
| `N/A` | Explicitly not applicable | Agent acknowledges and moves on |

---

## Requirements Registry

> **Purpose:** Single source of truth for utility compliance requirements.
> **Note:** HOP requirements (HOP-001 through HOP-008) DO NOT APPLY to utilities (Tier B).

### Universal Interface Contract (UIC) — B-CLI Only

> **Applies to:** B-CLI utilities only. Skip for B-LIB libraries.

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

### HOP Bundle Contract (HOP) — NOT APPLICABLE

> **⚠️ TIER B:** Utilities do NOT produce HOP bundles.
> HOP-001 through HOP-008 are explicitly **N/A** for this template.
>
> If a script produces HOP bundles, reclassify it as Tier A and use the appropriate template.

### Utility Compliance (UTL) — B-CLI Only

> **Applies to:** B-CLI utilities only. Skip for B-LIB libraries.

| ID | Requirement | Evidence Location |
|----|-------------|-------------------|
| UTL-001 | Output uses `rawview/` path (not `healthview/`) | `<path>:<line>` |
| UTL-002 | Return payload includes `action_taken` string | `<path>:<line>` |
| UTL-003 | Supports `--dry-run` flag (recommended) | `<path>:<line>` or `N/A` |
| UTL-004 | Supports `--force` flag for destructive ops | `<path>:<line>` or `N/A` |
| UTL-005 | `latest_*` pointers allowed (rawview exception) | `<path>:<line>` or `N/A` |

### Agent Discoverability (AGT) — B-CLI Only

> **Applies to:** B-CLI utilities only. B-LIB libraries do NOT require Tier-3 YAMLs.

| ID | Requirement | Evidence Location |
|----|-------------|-------------------|
| AGT-001 | Tier-3 YAML exists | `<tier3_path>` |
| AGT-002 | Tier-3 `tool.id` matches script | `<tier3_path>` |
| AGT-003 | Tier-3 `invocation.script_path` correct | `<tier3_path>` |
| AGT-004 | Tier-3 `cli_surfaces` complete | `<tier3_path>` |

### Database Integration (DBI) — B-CLI Only

> **Applies to:** B-CLI utilities only. Skip for B-LIB libraries.
> **Note:** B-CLI utilities use `action_log` table, NOT `report_runs`.

| ID | Requirement | Evidence Location |
|----|-------------|-------------------|
| DBI-001 | Uses `action_log` table (not `report_runs`) | `<path>:<line>` |
| DBI-002 | `DB_INTEGRATION_MARKER:` at action points | `<path>:<line>` |
| DBI-003 | Gated by `REPO_STUDIOS_DB_ENABLED` | `<path>:<line>` |

### Orchestration Readiness (ORC) — B-CLI Only

> **Applies to:** B-CLI utilities only. Skip for B-LIB libraries.

| ID | Requirement | Evidence Location |
|----|-------------|-------------------|
| ORC-001 | Can be dynamically imported | importlib test |
| ORC-002 | Idempotent (safe to re-run) | test confirms |
| ORC-003 | ScriptConfig documented | Section 8 |

### Library Compliance (LIB) — B-LIB Only

> **Applies to:** B-LIB libraries only. Skip for B-CLI utilities.
> Use Section 11 (Library Checklist) for B-LIB inspection.

| ID | Requirement | Evidence Location |
|----|-------------|-------------------|
| LIB-001 | `__all__` exports defined | `<path>:<line>` |
| LIB-002 | Google docstrings on all exports | Count: X/Y |
| LIB-003 | No side effects at import | grep confirms |
| LIB-004 | No `sys.exit()` calls | grep confirms |
| LIB-005 | No `input()` prompts | grep confirms |
| LIB-006 | Tests exist | `test_<module>.py` |

---

## 0. DETECT: Script Type & Branching

<!-- METAPROMPT: PROMPT-00-DETECT -->
<!-- CHECKPOINT_ID: CHECKPOINT-0 -->
<!-- STOP_CONDITION: Script type detected, appropriate path selected -->
<!-- PROCEED_SIGNAL: "CHECKPOINT-0: Utility type detected — {B-CLI | B-LIB}, path selected" -->
<!-- BRANCH_POINT: TRUE — B-CLI continues, B-LIB jumps to Section 11 -->

<!-- STOP_GATE: TRUE -->

> **⚠️ CRITICAL BRANCH POINT:** Detect script type BEFORE proceeding.
> This determines which path to follow for the rest of the template.

### 0.1 Script Type Detection — MANDATORY

**Run these commands to classify the script:**

| Check | Command | Result |
|-------|---------|--------|
| Has `def run(argv` | `grep -n "def run(argv" <script>` | `YES: line X` / `NO` |
| Has `def main(` | `grep -n "def main(" <script>` | `YES: line X` / `NO` |
| Has `__all__` | `grep -n "^__all__" <script>` | `YES: line X` / `NO` |
| Line count | `wc -l <script>` | `<N> lines` |

**Classification Results:**

| Detection | Value |
|-----------|-------|
| `run(argv)` exists | `YES: line X` / `NO` |
| `main()` exists | `YES: line X` / `NO` |
| `__all__` exists | `YES: line X` / `NO` |
| Line count | `<N>` |

### 0.2 Classification Rules

| If... | Then Type = | Action |
|-------|-------------|--------|
| `run(argv)` exists | **B-CLI** | Continue to Section 0.3, then Sections 1-10 |
| No `run()` but has `__all__` | **B-LIB** | **→ Jump to Section 11 (Library Checklist)** |
| `main()` only (no `run()`) | **B-CLI (non-compliant)** | Continue to Section 0.3, flag GAP for UIC refactoring |
| No entry points, no `__all__` | **B-LIB (undocumented)** | **→ Jump to Section 11**, flag GAP for `__all__` |

### 0.3 Detected Type

| Field | Value |
|-------|-------|
| **Detected Type** | `{B-CLI | B-LIB | B-CLI (non-compliant) | B-LIB (undocumented)}` |
| **Classification Confidence** | `HIGH` / `MEDIUM` / `LOW` |
| **Rationale** | `<why this classification was chosen>` |

> **⚠️ BRANCH POINT:**
>
> | If Type = | Then |
> |-----------|------|
> | **B-LIB** or **B-LIB (undocumented)** | **→ Skip to Section 11 (Library Checklist)** — SHORT PATH |
> | **B-CLI** or **B-CLI (non-compliant)** | **→ Continue to Section 0.4** — FULL PATH |

### 0.4 Required Inputs (B-CLI Only)

> **Skip this section if B-LIB** — Jump to Section 11.

| Input | Source | Example | Status |
|-------|--------|---------|--------|
| `SCRIPT_PATH` | Assignment | `.repo_studios/scripts/utilities/refresh_mypy_baselines.py` | `PENDING` |
| `RECORD_ID` | Tier-2 roster | `S41R-006` | `PENDING` |
| `COMPLIANCE_TIER` | Fixed | `B` (Non-HOP) | `PENDING` |
| `TARGET_STAGE` | Assignment | `Stage 4.1` | `PENDING` |

### 0.5 Sub-Tier Classification (B-CLI)

> **Skip this section if B-LIB** — Jump to Section 11.

| If script... | Then Sub-Tier = | Rationale |
|--------------|-----------------|-----------|
| Has `run(argv)` returning `dict` | **B-CLI (compliant)** | Full UIC compliance |
| Has `main()` only, returns `int` | **B-CLI (legacy)** | Needs UIC refactoring |
| Produces rawview output | **B-CLI (file-producing)** | Standard utility |
| Side effects only (no files) | **B-CLI (action-only)** | Action utility |

**Selected Sub-Tier:** `<sub-tier>`

<!-- PROCEED_WHEN: Type detected and appropriate path selected -->

---

## 1. IDENTIFY: Script Identity

<!-- METAPROMPT: PROMPT-01-SETUP -->
<!-- CHECKPOINT_ID: CHECKPOINT-1 -->
<!-- STOP_CONDITION: All fields in identity table populated, 1.1 and 1.2 completed -->
<!-- PROCEED_SIGNAL: "CHECKPOINT-1: Script identity captured — {SCRIPT_NAME} is B-CLI utility" -->
<!-- REENTRY_POINT: PROMPT-01-SETUP -->
<!-- B-LIB: SKIP — Use Section 11 -->

> **⚠️ B-LIB SKIP:** If Type = B-LIB, skip Sections 1-10. Go to Section 11.

<!-- PROCEED_WHEN: All fields in identity table populated -->

| Field | Value |
|-------|-------|
| **Name** | `<SCRIPT_NAME>` |
| **Path** | `<SCRIPT_PATH>` |
| **Tier Class** | Utility |
| **Compliance Tier** | B (Non-HOP) |
| **Sub-Tier** | `<B-CLI (compliant) | B-CLI (legacy) | B-CLI (file-producing) | B-CLI (action-only)>` |
| **Lines** | `<LINE_COUNT>` |
| **Record ID** | `<RECORD_ID>` |
| **Planned Stage** | `<TARGET_STAGE>` |

### 1.1 DESCRIBE: Purpose

<Brief description of what this utility does and why>

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
<!-- STOP_CONDITION: Sections 2.1-2.3 complete, all Status columns != PENDING -->
<!-- PROCEED_SIGNAL: "CHECKPOINT-2A: Static analysis complete — UIC checklist has {X} PASS, {Y} FAIL" -->
<!-- REENTRY_POINT: PROMPT-2A-ANALYZE -->
<!-- B-LIB: SKIP — Use Section 11 -->

> **⚠️ B-LIB SKIP:** If Type = B-LIB, skip Sections 1-10. Go to Section 11.

### 2.1 DOCUMENT: CLI Interface

```text
usage: <SCRIPT_NAME> [-h] [--repo-root REPO_ROOT] ...
```

**Flags:**

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--repo-root` | path | auto | Repository root override |
| `--log-level` | choice | INFO | Logging verbosity |
| `--dry-run` | flag | false | Preview changes without applying (UTL-003) |
| `--force` | flag | false | Skip confirmations for destructive ops (UTL-004) |
| <additional flags> | | | |

### 2.2 INSPECT: Entry Points

| Entry | Signature | Returns | Status |
|-------|-----------|---------|--------|
| `main(argv)` | `list[str] \| None` → `int` | Exit code | `PENDING` |
| `run(argv)` | `list[str] \| None` → `dict[str, Any]` | Payload dict | `PENDING` |

#### 2.2.1 Universal Interface Contract (B-CLI)

<!-- TIER: B-CLI -->
<!-- PROCEED_WHEN: All Status columns = PASS or SKIP -->

> **Applies to:** B-CLI utilities only.

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

#### 2.2.2 Utility Compliance Contract (B-CLI)

<!-- TIER: B-CLI -->
<!-- PROCEED_WHEN: All Status columns = PASS or N/A -->

> **Applies to:** B-CLI utilities only.

| Requirement | ID | Status | Evidence |
|-------------|----|--------|----------|
| Output uses `rawview/` path | UTL-001 | `PENDING` | `<path>:<line>` |
| Return payload includes `action_taken` | UTL-002 | `PENDING` | `<path>:<line>` |
| Supports `--dry-run` flag | UTL-003 | `PENDING` | `<path>:<line>` or `N/A` |
| Supports `--force` flag | UTL-004 | `PENDING` | `<path>:<line>` or `N/A` |
| `latest_*` pointers allowed | UTL-005 | `PENDING` | `<path>:<line>` or `N/A` |

#### 2.2.3 Return Payload Contract (B-CLI)

> **Applies to:** B-CLI utilities only.

**Tier B (Utilities) — REQUIRED keys:**

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `status` | str | ✅ | "success", "failure", "partial" |
| `exit_code` | int | ✅ | 0=success, non-zero=failure |
| `action_taken` | str | ✅ | Human-readable description of action performed |
| `artifacts` | list[str] \| None | ✅ | Paths to created files, or `None` if no output |
| `metrics` | dict | Optional | Statistics (files changed, etc.) |
| `details` | dict | Optional | Additional context |

**Example return payload:**

```python
return {
    "status": "success",
    "exit_code": 0,
    "action_taken": "Refreshed 12 mypy baseline files",
    "artifacts": [".repo_studios/reports/rawview/mypy_baselines/baselines.json"],
    "metrics": {"files_updated": 12, "files_unchanged": 3}
}
```

### 2.3 DOCUMENT: Output Contract (Non-HOP)

<!-- UTILITY_SPECIFIC: TRUE -->

> **⚠️ UTILITY NOTE:** Utilities produce rawview outputs, NOT HOP bundles.
> There is NO manifest.json, summary.md, or telemetry.json requirement.

#### 2.3.1 Output Artifacts

| Output | Type | Location | Persistent |
|--------|------|----------|------------|
| `<artifact_name>` | `<JSON/MD/CSV>` | `<rawview_path>/<timestamp>/` | `YES/NO` |

**Output root:** `.repo_studios/reports/healthview/rawview_reports/<TOPIC>/<YYYYMMDD-HHMM>/`

> **Note:** `latest_*` pointer files ARE allowed for rawview utilities (UTL-005 exception).
> This differs from Tier A scripts which must NOT use `latest_*` pointers.

#### 2.3.2 Output Path Verification

| Check | Status | Evidence |
|-------|--------|----------|
| Uses `rawview/` (not `healthview/producer_reports/`) | `PENDING` | `<path>:<line>` |
| Timestamp format `YYYYMMDD-HHMM` | `PENDING` | `<path>:<line>` |
| `latest_*` pointer (if used) | `PENDING` | `<path>:<line>` or `N/A` |

### 2.4 VERIFY: Output Quality

<!-- METAPROMPT: PROMPT-2B-VERIFY -->
<!-- CHECKPOINT_ID: CHECKPOINT-2B -->
<!-- STOP_CONDITION: 2.4.1 QA all PASS, 2.4.4 truth table all Verdict = TRUE -->
<!-- PROCEED_SIGNAL: "CHECKPOINT-2B: Output truth verified — utility executed, all claims TRUE" -->
<!-- REENTRY_POINT: PROMPT-2B-VERIFY (critical gate — must re-verify from scratch) -->

> **⚠️ MANDATORY STOP-GATE — DO NOT SKIP**
>
> This section is the **PROOF OF THE UTILITY**. A utility that passes mypy/pytest but performs
> incorrect actions or produces misleading output is **WORTHLESS**. Every claim in the output
> and `action_taken` string MUST be verified against ground truth.
>
> **Agent Instruction:** You MUST run the utility, observe the actual effects, and verify each
> claim against the actual filesystem/codebase state. Do not proceed until all claims are TRUE.

**MANDATORY: Run utility and inspect actual effects before completing this section.**

#### 2.4.1 QA Verification

| Check | Command | Result | Evidence | CI/Artifact Link |
|-------|---------|--------|----------|------------------|
| mypy --strict | `python -m mypy --strict <script>` | `PENDING` | <error count or "Success"> | `<CI_URL or N/A>` |
| pytest | `pytest <test_file> -v` | `PENDING` | <X/Y passed in Z.ZZs> | `<CI_URL or N/A>` |
| CLI execution | `python <script> --help` | `PENDING` | <runs without error> | `N/A` |
| Actual run | `python <script> --log-level DEBUG` | `PENDING` | <action_taken value> | `<artifact_path>` |

#### 2.4.2 Action Verification — MANDATORY FOR UTILITIES

<!-- UTILITY_SPECIFIC: TRUE -->
<!-- STOP_CONDITION: All claimed actions verified against ground truth -->

> **⚠️ UTILITY REQUIREMENT:** The utility's claimed actions MUST be verified against reality.
> What the utility says it did (in `action_taken`) must match what actually happened.

**Run the utility:**

```bash
python <script> --repo-root . --log-level DEBUG
```

**Action Claims vs Reality:**

| Claimed Action (from `action_taken`) | Verification Method | Actual Result | Verdict |
|--------------------------------------|---------------------|---------------|---------|
| `<what the utility claims it did>` | `<how to verify>` | `<what actually happened>` | ✅ / ❌ |

**Dry Run Verification (if UTL-003 applies):**

| Test | Command | Expected | Actual | Status |
|------|---------|----------|--------|--------|
| Dry run makes no changes | `python <script> --dry-run` | No files modified | `<actual>` | `PENDING` |
| Dry run reports what WOULD happen | Check stdout | Lists planned actions | `<actual>` | `PENDING` |

**Idempotency Verification:**

| Test | Command | Expected | Actual | Status |
|------|---------|----------|--------|--------|
| Run twice in succession | `python <script> && python <script>` | Same result, no errors | `<actual>` | `PENDING` |
| Second run acknowledges no-op | Check `action_taken` | "Nothing to do" or similar | `<actual>` | `PENDING` |

#### 2.4.3 DB Integration Markers (B-CLI)

> **Note:** B-CLI utilities use `action_log` table, NOT `report_runs` or HOP tables.

| Check | Status | Evidence |
|-------|--------|----------|
| `DB_INTEGRATION_MARKER:` at action points | `PENDING` | `<path>:<line>` |
| Marker describes `action_log` table intent | `PENDING` | `<path>:<line>` |
| Gated by `REPO_STUDIOS_DB_ENABLED` | `PENDING` | `<path>:<line>` |

**Example DB marker for utilities:**

```python
# DB_INTEGRATION_MARKER: utility_actions.action_log — Record utility execution
if os.environ.get("REPO_STUDIOS_DB_ENABLED"):
    log_utility_action(script_name=__name__, action_taken=result["action_taken"])
```

#### 2.4.4 Output Truth Verification (CRITICAL)

<!-- STOP_GATE: TRUE -->
<!-- PROCEED_WHEN: All claims in truth table have Verdict = TRUE -->

> **⚠️ MANDATORY STOP — DO NOT PROCEED UNTIL ALL CLAIMS VERIFIED**
>
> Verify that the utility's `action_taken` string accurately describes what happened.
> A utility that reports "Updated 12 files" when it actually updated 0 is **LYING**.

| Claim in Output | Verification Method | Ground Truth | Verdict |
|-----------------|---------------------|--------------|---------|
| `<action_taken claim>` | <how to verify> | <actual state> | ✅/❌ |
| `<artifact path exists>` | `Test-Path <path>` | <true/false> | ✅/❌ |
| `<files changed count>` | `git status` or `ls` | <actual count> | ✅/❌ |

**If ANY claim is FALSE, the utility is BROKEN. Fix it before proceeding.**

### 2.5 Verification Log

| Date | Inspector | Findings | Status |
|------|-----------|----------|--------|
| <YYYY-MM-DD> | <agent/human> | <summary of verification> | `PASS` / `FAIL` / `GAPS_FOUND` |

---

## 3. PREPARE: Tier-3 YAML (B-CLI Only)

<!-- METAPROMPT: PROMPT-34-PREPARE -->
<!-- CHECKPOINT_ID: CHECKPOINT-3 -->
<!-- STOP_CONDITION: Tier-3 YAML exists, 3.2 fields all Status = PASS -->
<!-- PROCEED_SIGNAL: "CHECKPOINT-3: Tier-3 YAML verified at {tier3_path}" -->
<!-- REENTRY_POINT: PROMPT-34-PREPARE -->
<!-- B-LIB: SKIP — Libraries do NOT require Tier-3 YAMLs -->

> **⚠️ B-CLI ONLY:** This section applies to B-CLI utilities only.
> B-LIB libraries do NOT require Tier-3 YAMLs — skip to Section 11 if B-LIB.

### 3.1 LOCATE: Tier-3 YAML

**Expected path:** `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier3_scripts/<stage>/<script_name>.yaml`

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
| `category` | `PENDING` | `utility` |
| `compliance_tier` | `PENDING` | `B` |
| `entry_point` | `PENDING` | `run` |
| `description` | `PENDING` | <one-line description> |
| `inputs` | `PENDING` | List of input parameters with types |
| `outputs` | `PENDING` | Description of return payload |
| `orchestrator_ready` | `PENDING` | `true` / `false` |
| `db_integration_ready` | `PENDING` | `true` / `false` |

### 3.3 REFERENCE: Tier-3 YAML Template (Utility)

```yaml
# Tier-3 Metadata for <SCRIPT_NAME>
# Agent-discoverable utility definition
tool:
  id: <script_stem>
  name: <SCRIPT_NAME>
  version: "1.0.0"
  description: "<One-line description of what this utility does>"

classification:
  category: utility
  compliance_tier: B
  hop_bundle: false  # Utilities do NOT produce HOP bundles

invocation:
  script_path: <SCRIPT_PATH>
  entry_point: run
  supports_dry_run: <true|false>
  supports_force: <true|false>

cli_surfaces:
  - name: repo_root
    flag: "--repo-root"
    type: path
    required: false
    description: "Repository root override"
  - name: log_level
    flag: "--log-level"
    type: choice
    choices: [DEBUG, INFO, WARNING, ERROR]
    default: INFO
    description: "Logging verbosity"
  # <additional flags>

outputs:
  return_type: dict
  keys:
    status: "success|failure|partial"
    exit_code: "0=success, non-zero=failure"
    action_taken: "Human-readable action description"
    artifacts: "List of created file paths, or None"
  artifacts_path: "<rawview_path>"

orchestrator_ready: <true|false>
db_integration_ready: <true|false>

tags:
  - utility
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

## 4. PREPARE: Database Integration (B-CLI Only)

<!-- METAPROMPT: PROMPT-34-PREPARE -->
<!-- CHECKPOINT_ID: CHECKPOINT-4 -->
<!-- STOP_CONDITION: 4.2 checklist all Status = PASS or N/A -->
<!-- PROCEED_SIGNAL: "CHECKPOINT-4: DB integration markers present for action_log" -->
<!-- REENTRY_POINT: PROMPT-34-PREPARE -->
<!-- B-LIB: SKIP — Libraries do NOT require DB integration -->

> **⚠️ B-CLI ONLY:** This section applies to B-CLI utilities only.
> B-LIB libraries do NOT require DB integration — skip to Section 11 if B-LIB.

### 4.1 DOCUMENT: DB Schema Intent

> **Note:** Utilities use `action_log` table, NOT the HOP tables used by Tier A scripts.

**For B-CLI Utilities:**

| Action | Target Table | Key Columns |
|--------|--------------|-------------|
| Action log | `utility_actions` | script_name, action_taken, status, timestamp, metrics_json |

### 4.2 CHECK: DB Integration Readiness

| Check | Status | Evidence |
|-------|--------|----------|
| `DB_INTEGRATION_MARKER:` at action points | `PENDING` | `<path>:<line>` |
| Marker describes `utility_actions` table | `PENDING` | `<path>:<line>` |
| Gated by `REPO_STUDIOS_DB_ENABLED` env var | `PENDING` | `<path>:<line>` |
| Payload is JSON-serializable | `PENDING` | No datetime objects, Path objects |

### 4.3 REFERENCE: DB Integration Marker Format (Utility)

```python
# DB_INTEGRATION_MARKER: utility_actions.action_log — Log utility execution
# When DB integration is enabled, this will record:
#   - script_name: __name__
#   - action_taken: result["action_taken"]
#   - status: result["status"]
#   - timestamp: datetime.utcnow()
#   - metrics_json: result.get("metrics", {})
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
<!-- B-LIB: SKIP — Use Section 11 -->

> **⚠️ B-LIB SKIP:** If Type = B-LIB, skip Sections 1-10. Go to Section 11.

### 5.1 LIST: Required Changes

<!-- PROCEED_WHEN: All HIGH priority gaps have Status != OPEN -->

> **Gap Status Values:**
>
> - `OPEN` — Gap identified, not yet fixed
> - `CLOSED` — Fix applied, awaiting verification
> - `VERIFIED` — Fix confirmed working

> **⚠️ EXAMPLE ROWS BELOW:** The GAP-001 through GAP-010 entries are EXAMPLES showing common gaps.
> **DELETE rows that don't apply.** Keep and update rows that match actual findings.
> **ADD new rows** for gaps not covered by examples.

#### 5.1.1 Universal Interface Gaps (B-CLI)

| Gap ID | Req ID | Description | Priority | Status | Closed Date |
|--------|--------|-------------|----------|--------|-------------|
<!-- EXAMPLE ROWS — Delete if not applicable to this script -->
| GAP-001 | UIC-001 | Missing `run()` entry point | High | `OPEN` | |
| GAP-002 | UIC-002 | `run()` returns int not dict | High | `OPEN` | |
| GAP-003 | UIC-005 | Missing `--repo-root` flag | High | `OPEN` | |
| GAP-004 | UIC-006 | Missing `--log-level` flag | Medium | `OPEN` | |
<!-- END EXAMPLE ROWS -->

#### 5.1.2 Utility Compliance Gaps (B-CLI)

| Gap ID | Req ID | Description | Priority | Status | Closed Date |
|--------|--------|-------------|----------|--------|-------------|
<!-- EXAMPLE ROWS — Delete if not applicable to this script -->
| GAP-005 | UTL-001 | Output path not using `rawview/` | High | `OPEN` | |
| GAP-006 | UTL-002 | Missing `action_taken` in return | High | `OPEN` | |
| GAP-007 | UTL-003 | No `--dry-run` support | Medium | `OPEN` | |
<!-- END EXAMPLE ROWS -->

#### 5.1.3 Agent/DB Readiness Gaps (B-CLI)

| Gap ID | Req ID | Description | Priority | Status | Closed Date |
|--------|--------|-------------|----------|--------|-------------|
<!-- EXAMPLE ROWS — Delete if not applicable to this script -->
| GAP-008 | AGT-001 | No Tier-3 YAML | High | `OPEN` | |
| GAP-009 | DBI-002 | Missing DB_INTEGRATION_MARKER | Medium | `OPEN` | |
| GAP-010 | ORC-002 | Not idempotent (side effects on re-run) | High | `OPEN` | |
<!-- END EXAMPLE ROWS -->

### 5.2 MAP: Alteration Locations

| Location | Change | Requirement |
|----------|--------|-------------|
| `<path>:<start>-<end>` | <description> | <UIC/UTL/AGT/DBI/ORC requirement> |

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
<!-- B-LIB: SKIP — Use Section 11 -->

> **⚠️ B-LIB SKIP:** If Type = B-LIB, skip Sections 1-10. Go to Section 11.

### 6.1 Change Log

| # | Category | Location | Description | Gap ID(s) Resolved | Commit SHA |
|---|----------|----------|-------------|-------------------|------------|
| 1 | <category> | `<path>:<line>` | <what was changed> | GAP-XXX | `<sha>` |
| 2 | <category> | `<path>:<line>` | <what was changed> | GAP-XXX | `<sha>` |

**Change Categories:**

- `Entry Point` — run()/main() modifications
- `CLI Flags` — argparse additions/changes
- `Return Contract` — payload structure changes
- `Output Path` — rawview path changes
- `Dry Run` — dry-run support addition
- `Action Logging` — action_taken improvements
- `Error Handling` — exception wrapping
- `DB Integration` — markers, gating
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
<!-- B-LIB: SKIP — Use Section 11 -->

> **⚠️ B-LIB SKIP:** If Type = B-LIB, skip Sections 1-10. Go to Section 11.

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

## 8. CONFIGURE: Orchestrator Integration (B-CLI Only)

<!-- METAPROMPT: PROMPT-8-UTILITY -->
<!-- CHECKPOINT_ID: CHECKPOINT-8 -->
<!-- STOP_CONDITION: ScriptConfig defined in 8.2, all 8.3 readiness checks = PASS -->
<!-- PROCEED_SIGNAL: "CHECKPOINT-8: Orchestrator config ready — ScriptConfig documented" -->
<!-- REENTRY_POINT: PROMPT-8-UTILITY -->
<!-- B-LIB: SKIP — Libraries are not orchestrated -->

> **⚠️ B-LIB SKIP:** If Type = B-LIB, skip Sections 1-10. Go to Section 11.
>
> **Note:** Not all utilities are orchestrator-integrated. If standalone, mark integration
> status as N/A but still document ScriptConfig for future use.

### 8.1 Orchestrator Integration Status

| Question | Answer |
|----------|--------|
| Currently called by an orchestrator? | `YES: <orchestrator>` / `NO` |
| Designed for orchestrator use? | `YES` / `NO (standalone)` |
| Safe to add to pipeline? | `YES` / `NO: <reason>` |

### 8.2 DEFINE: ScriptConfig Attributes

| Attribute | Value | Rationale |
|-----------|-------|-----------|
| `name` | `"<script_name>"` | Basename without `.py` |
| `path` | `"<relative_path>"` | From repo root |
| `supports_output_dir` | `True/False` | Does script accept `--output-dir`? |
| `supports_artifacts_to_keep` | `False` | Utilities typically don't prune |
| `supports_dry_run` | `True/False` | Does script accept `--dry-run`? |
| `supports_force` | `True/False` | Does script accept `--force`? |
| `uses_argv_kwarg` | `True/False` | Is signature `run(*, argv=...)` or `run(argv)`? |
| `custom_args` | `None` or `[...]` | Any non-standard args needed |

### 8.3 GENERATE: ScriptConfig

```python
ScriptConfig(
    name="<script_name>",
    path="<relative_path>",
    supports_output_dir=<True/False>,
    supports_artifacts_to_keep=False,  # Utilities typically don't prune
    supports_dry_run=<True/False>,
    supports_force=<True/False>,
    uses_argv_kwarg=<True/False>,
)
```

### 8.4 VERIFY: Orchestration Readiness (B-CLI)

<!-- TIER: B-CLI -->
<!-- PROCEED_WHEN: All Status columns = PASS -->

> **All B-CLI utilities MUST pass this checklist before being considered "ready" — even if
> never assigned to an orchestrator.**

| Check | ID | Status | Evidence |
|-------|----|--------|----------|
| `run(argv)` callable exposed | UIC-001 | `PENDING` | `from <module> import run` works |
| `run()` returns dict (not int) | UIC-002 | `PENDING` | `isinstance(result, dict)` |
| Return dict has required keys | UIC-003/004 | `PENDING` | `status`, `exit_code`, `action_taken` |
| Can be dynamically imported | ORC-001 | `PENDING` | `importlib.util.spec_from_file_location` |
| No `sys.exit()` in `run()` | UIC-008 | `PENDING` | grep for `sys.exit` |
| No interactive prompts | UIC-009 | `PENDING` | No `input()` calls |
| Exceptions wrapped gracefully | UIC-010 | `PENDING` | Returns error payload vs raising |
| Idempotent (safe to re-run) | ORC-002 | `PENDING` | Multiple runs don't corrupt state |
| Tier-3 YAML complete | AGT-001—004 | `PENDING` | All required fields populated |
| DB Integration markers present | DBI-001—003 | `PENDING` | `action_log` markers |

### 8.5 Verification Log

| Date | Inspector | Findings | Status |
|------|-----------|----------|--------|
| <YYYY-MM-DD> | <agent/human> | <summary of verification> | `PASS` / `FAIL` / `GAPS_FOUND` |

---

## 9. ATTEST: Compliance Sign-Off (B-CLI)

<!-- METAPROMPT: PROMPT-910-CLOSE -->
<!-- CHECKPOINT_ID: CHECKPOINT-9 -->
<!-- STOP_CONDITION: All attestation checkboxes checked, Inspector row complete -->
<!-- PROCEED_SIGNAL: "CHECKPOINT-9: Attestation complete — signed by {ASSIGNEE} on {DATE}" -->
<!-- REENTRY_POINT: PROMPT-910-CLOSE -->
<!-- B-LIB: SKIP — Use Section 11.6 for B-LIB attestation -->

> **⚠️ B-LIB SKIP:** If Type = B-LIB, skip Sections 1-10. Go to Section 11.

### 9.1 Attestation Record

<!-- STOP_GATE: TRUE -->
<!-- PROCEED_WHEN: All attestation checkboxes checked and Inspector row completed -->

| Role | Name | Date | Signature/ID |
|------|------|------|--------------|
| Inspector | <ASSIGNEE> | <YYYY-MM-DD> | <agent_id or initials> |
| Reviewer | <name or N/A> | <YYYY-MM-DD> | <signature or N/A> |
| Approver | <name or N/A> | <YYYY-MM-DD> | <signature or N/A> |

### 9.2 Attestation Statement (B-CLI)

> I attest that:
>
> - [ ] All sections of this document were completed honestly
> - [ ] All evidence references point to real, verifiable artifacts
> - [ ] All PASS statuses reflect actual verification, not assumption
> - [ ] All gaps identified were either CLOSED+VERIFIED or documented as deferred
> - [ ] The utility was actually executed and actions verified against ground truth
> - [ ] The `action_taken` string accurately describes what the utility did

**Inspector attestation date:** `<YYYY-MM-DD>`

---

## 10. FINALIZE: Completion (B-CLI)

<!-- METAPROMPT: PROMPT-910-CLOSE -->
<!-- CHECKPOINT_ID: CHECKPOINT-10 -->
<!-- STOP_CONDITION: All 10.1 checkboxes checked, no <PLACEHOLDER> remains, frontmatter updated -->
<!-- PROCEED_SIGNAL: "CHECKPOINT-10: PHASE 4 COMPLETE — {RECORD_ID} ready for production" -->
<!-- REENTRY_POINT: PROMPT-910-CLOSE (final gate — restart close sequence) -->
<!-- B-LIB: SKIP — Use Section 11.7 for B-LIB finalization -->

> **⚠️ B-LIB SKIP:** If Type = B-LIB, skip Sections 1-10. Go to Section 11.

### 10.1 CHECK: Build Document Completion

<!-- STOP_GATE: TRUE -->
<!-- PROCEED_WHEN: All checkboxes checked -->

**Discovery & Analysis:**

- [ ] Section 0 (Type Detection) — Type classified as B-CLI
- [ ] Section 1 (Script Identity) — All fields populated
- [ ] Section 2.1 (CLI Interface) — Flags documented from `--help` output
- [ ] Section 2.2 (Entry Points) — Signatures verified against code
- [ ] Section 2.3 (Output Contract) — rawview path documented

**Implementation & Testing:**

- [ ] Section 5 (Gap Analysis) — Gaps identified with priority/effort
- [ ] Section 6 (Changes Made) — All modifications documented with line numbers
- [ ] Section 7 (Evidence) — Test results captured (pytest/mypy/coverage)

**Truth Verification (CRITICAL):**

- [ ] Section 2.4.1 — QA tests passed (mypy, pytest, CLI execution)
- [ ] Section 2.4.2 — Action verification: **UTILITY WAS ACTUALLY RUN**
- [ ] Section 2.4.4 — Output truth verified: **action_taken is ACCURATE**
- [ ] **If any claim was FALSE, it was FIXED before checking this box**

**Tier-3 & DB Integration:**

- [ ] Section 3 — Tier-3 YAML created/updated and validated
- [ ] Section 4 — DB Integration markers present at action points

**Orchestrator Readiness:**

- [ ] Section 8.4 — All orchestration readiness checks pass

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
- [x] F. Output truth verification — utility run, action_taken verified TRUE
- [x] G. Tier-3 YAML — created/updated <tier3_name>.yaml
- [x] H. Orchestrator integration — ScriptConfig documented (Section 8.3)
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

**Registry update checklist:**

- [ ] Opened Tier-1 pipeline document
- [ ] Located stage Script Gate Summary section
- [ ] Updated checkbox for this utility script
- [ ] Status set to "complete"
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

### 10.5 CONFIRM: Phase 4 Complete (B-CLI)

**Completion timestamp:** `<YYYY-MM-DD HH:MM UTC>`

**Summary:**

| Aspect | Status | Evidence |
|--------|--------|----------|
| Universal compliance (UIC) | ✅ | Section 2.2.1 all checked |
| Utility compliance (UTL) | ✅ | Section 2.2.2 all checked |
| Action truth verified | ✅ | Section 2.4.2 — action_taken TRUE |
| Tier-3 YAML | ✅ | `<tier3_yaml_path>` |
| DB Integration ready | ✅ | `<path>:<line>` |
| Orchestrator ready | ✅ | Section 8.4 all checked |
| Tier-2 roster updated | ✅ | Workstreams A-H + DONE checked, file SAVED |
| Tier-1 registry updated | ✅ | Script entry updated, file SAVED |

**Propagation confirmation:**

- Tier-2 roster: `<roster_path>` — SAVED
- Tier-1 registry: `<tier1_path>` — SAVED

**B-CLI TEMPLATE COMPLETE.**

---

## 11. LIBRARY CHECKLIST (B-LIB Path)

<!-- METAPROMPT: PROMPT-LIB-CHECKLIST -->
<!-- CHECKPOINT_ID: CHECKPOINT-LIB -->
<!-- STOP_CONDITION: All checks complete, gaps identified -->
<!-- PROCEED_SIGNAL: "CHECKPOINT-LIB: Library checklist complete — {X}/{Y} checks PASS" -->
<!-- REENTRY_POINT: Section 0 (if reclassification needed) -->

> **⚠️ B-LIB PATH:** You jumped here from Section 0 because this is a pure library.
> Libraries have a simplified compliance path — just this checklist.
>
> **B-LIB libraries do NOT require:**
>
> - Tier-3 YAML (no AGT requirements)
> - DB Integration markers (no DBI requirements)
> - Orchestrator integration (no ORC requirements)
> - UIC compliance (no CLI interface)

### 11.1 Library Identity

| Field | Value |
|-------|-------|
| **Name** | `<MODULE_NAME>` |
| **Path** | `<MODULE_PATH>` |
| **Type** | B-LIB (Pure Library) |
| **Lines** | `<LINE_COUNT>` |
| **Record ID** | `<RECORD_ID>` |
| **Target Stage** | `<TARGET_STAGE>` |

### 11.2 Purpose

<Brief description of what this library provides — what functions/classes it exports and why>

### 11.3 Exported API

| Export | Type | Description |
|--------|------|-------------|
| `<function_name>()` | Function | `<what it does>` |
| `<ClassName>` | Class | `<what it represents>` |

**`__all__` contents:** `['<export1>', '<export2>', ...]`

### 11.4 Compliance Checklist (B-LIB)

| ID | Check | Command | Status | Evidence |
|----|-------|---------|--------|----------|
| LIB-001 | `__all__` exports defined | `grep -n "^__all__" <script>` | `PASS` / `FAIL` | Line X |
| LIB-002 | Google docstrings on exports | Manual review | `PASS: X/Y` | Count |
| LIB-003 | No side effects at import | `python -c "import <module>"` | `PASS` / `FAIL` | Silent import |
| LIB-004 | No `sys.exit()` calls | `grep -n "sys.exit" <script>` | `PASS` / `FAIL` | grep result |
| LIB-005 | No `input()` prompts | `grep -n "input(" <script>` | `PASS` / `FAIL` | grep result |
| LIB-006 | Tests exist | `ls test_<module>.py` | `PASS` / `FAIL` | Path |

### 11.5 Gaps Identified (B-LIB)

| Gap ID | Check ID | Description | Priority | Status | Closed Date |
|--------|----------|-------------|----------|--------|-------------|
| GAP-L01 | LIB-001 | Missing `__all__` | High | `OPEN` | |
| GAP-L02 | LIB-002 | Missing docstrings on X exports | Medium | `OPEN` | |
<!-- Add gaps as discovered -->

### 11.6 Attestation (B-LIB)

> I attest that:
>
> - [ ] All checks in Section 11.4 were performed
> - [ ] All gaps identified in Section 11.5
> - [ ] This library is safe to import (no side effects)
> - [ ] This library does NOT require reclassification as B-CLI

**Inspector:** `<ASSIGNEE>`
**Date:** `<YYYY-MM-DD>`

### 11.7 Tier-2 Update (B-LIB)

> **Note:** B-LIB libraries do NOT require Tier-3 YAMLs.
> Update Tier-2 roster with checklist completion status.

**Roster update for B-LIB:**

```markdown
#### <RECORD_ID>: <MODULE_NAME>

- **Type:** B-LIB (Pure Library)
- **Path:** `<MODULE_PATH>`
- **Status:** Phase 4 Complete (<YYYY-MM-DD>)
- **Tier-3 YAML:** N/A (library, no Tier-3 required)
- **Tests:** `test_<module>.py`

**Library Checklist:**
- [x] LIB-001: `__all__` exports defined
- [x] LIB-002: Google docstrings on exports (X/Y)
- [x] LIB-003: No side effects at import
- [x] LIB-004: No `sys.exit()` calls
- [x] LIB-005: No `input()` prompts
- [x] LIB-006: Tests exist
```

**Roster update checklist:**

- [ ] Located script record in Tier-2 roster (or created new entry)
- [ ] Updated Type to B-LIB
- [ ] Marked Tier-3 YAML as N/A
- [ ] Checked library checklist items
- [ ] Added Phase 4 Complete status with date
- [ ] Tier-2 roster file SAVED

**LIBRARY CHECKLIST COMPLETE — No further sections required for B-LIB.**

---

## 12. MAINTAIN: Doc Hygiene

> **Purpose:** After each inspection cycle, clean the document to reflect CURRENT state only.
> Historical context lives in Verification Logs, not in section content.

### 12.1 CHECK: Hygiene Checklist

- [ ] All PENDING statuses resolved (changed to PASS/FAIL/SKIP)
- [ ] All `<placeholder>` values replaced with actual data
- [ ] All gaps either CLOSED+VERIFIED or documented as deferred
- [ ] Stale language removed (no "was", "used to", "previously")
- [ ] Evidence reflects most recent verification
- [ ] Verification Logs updated with inspection date

### 12.2 APPLY: Language Standards

**Use current tense:**

- ✅ "Utility returns dict with status key"
- ❌ "Utility was updated to return dict"

**Use facts, not narrative:**

- ✅ "Entry point: `run(argv)` at line 45"
- ❌ "We added a run(argv) entry point during Phase 4"

### 12.3 IDENTIFY: Re-Inspection Triggers

This document should be re-inspected when:

- [ ] Requirements Registry changes (new UIC/UTL/LIB requirements)
- [ ] Script code is modified
- [ ] Upstream dependencies change
- [ ] Orchestrator integration changes
- [ ] Quarterly audit cycle

---

## 13. REFERENCE: Template Variables

> **Placeholder Conventions:**
>
> - `<UPPER_SNAKE>`: User-fillable text values (e.g., `<SCRIPT_NAME>`, `<RECORD_ID>`)
> - `<lower_snake>`: Structural references (e.g., `<path>`, `<line>`, `<tier3_path>`)
> - ISO timestamps: `<YYYY-MM-DD>`, `<YYYYMMDD-HHMM>` (kept as-is for standard compliance)

Replace these placeholders when using this template:

| Variable | Description |
|----------|-------------|
| `<SCRIPT_NAME>` | Script filename (e.g., `refresh_mypy_baselines.py`) |
| `<SCRIPT_PATH>` | Full path (e.g., `.repo_studios/scripts/utilities/refresh_mypy_baselines.py`) |
| `<MODULE_NAME>` | Module name for B-LIB (e.g., `monkey_patch_risk`) |
| `<MODULE_PATH>` | Full path for B-LIB (e.g., `.repo_studios/scripts/utilities/monkey_patch_risk.py`) |
| `<RECORD_ID>` | Tier-2 record ID (e.g., `S41R-006`) |
| `<YYYY-MM-DD>` | ISO date |
| `<LINE_COUNT>` | Script line count |
| `<TARGET_STAGE>` | Destination stage (e.g., `Stage 4.1`) |
| `<TOPIC>` | Topic slug (e.g., `mypy_baselines`) |
| `<ASSIGNEE>` | Person or agent performing the inspection |
| `<registry_version>` | Version of Requirements Registry in effect |
| `<valid_until>` | Date when this inspection expires (typically +90 days) |
| `<path>:<line>` | Line reference format (e.g., `.repo_studios/scripts/utilities/script.py:123`) |
| `<path>:<start>-<end>` | Line range format (e.g., `.repo_studios/scripts/utilities/script.py:45-67`) |
| `<CI_URL>` | CI job URL (e.g., `https://github.com/org/repo/actions/runs/12345`) |
| `<sha>` | Git commit SHA (short form, e.g., `abc123d`) |
| `<artifact_path>` | Path to archived artifact with optional hash |
| `<agent_id>` | Agent identifier (e.g., `copilot-v4`, `claude-3.5`) |
| `<tier3_path>` | Path to Tier-3 YAML (e.g., `tier3_scripts/.../<script>.yaml`) |
| `<rawview_path>` | Output path for utility (e.g., `.repo_studios/reports/healthview/rawview_reports/<topic>/`) |

---

## 14. LOG: Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-02-04 | Initial Utility template with Option C-1 architecture: (1) Section 0 type detection branching to B-CLI (full path, Sections 1-10) or B-LIB (short path, Section 11); (2) Requirements Registry with UIC (B-CLI), UTL-001—UTL-005 (B-CLI), LIB-001—LIB-006 (B-LIB), AGT (B-CLI only), DBI (B-CLI uses action_log), ORC (B-CLI); (3) HOP requirements explicitly N/A for all utilities; (4) Section 2.3 documents rawview outputs with latest_* pointer exception; (5) Section 2.4.2 Action Verification with dry-run and idempotency checks; (6) Section 8 simplified ScriptConfig for utilities; (7) Section 11 Library Checklist (~100 lines) for B-LIB short path; (8) B-LIB explicitly does NOT require Tier-3 YAML |

