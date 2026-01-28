---
title: "Script Build Template — <SCRIPT_NAME>"
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
version: 2.0.0
updated_at: <YYYY-MM-DD>
tags:
  - stage-12
  - utility
  - phase-4
  - <RECORD_ID>
related_files:
  - <SCRIPT_PATH>
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/tier2_available_scripts_roster.md
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/implementation_plans/stage12_template_development_plan.md
  - .repo_studios/command_center/scripts/libraries/database_integration.py
---

<!-- markdownlint-disable-next-line MD025 -->
# Script Build Template — <SCRIPT_NAME>

> **Purpose:** Working document for Phase 4 per-script processing of <RECORD_ID>.
> This template will evolve as the script is inspected, modified, documented, and tested.
> Upon completion, content transfers to Tier-2 and this doc is archived with `status: archived`.
>
> **Record ID:** <RECORD_ID>
> **Status:** `active`
> **Created:** <YYYY-MM-DD>
> **Completed:** (pending)
>
> **Universal Law:** Every script in the HealthView pipeline SHALL be orchestration-ready,
> agent-discoverable via Tier-3 YAML, and database-integration prepared — regardless of
> whether it is currently assigned to an orchestrator.
>
> **Tier B Note:** Utility scripts perform actions without producing HOP bundles. They still
> follow the Universal Interface Contract and are orchestration-ready, but have a lighter
> output contract focused on action logging rather than report generation.

---

## 1. Script Identity

| Field | Value |
|-------|-------|
| **Name** | `<SCRIPT_NAME>` |
| **Path** | `<SCRIPT_PATH>` |
| **Tier Class** | Utility / Configurator / Diagnostic / Faulthandler |
| **Compliance Tier** | B (Action Utility) |
| **Lines** | <LINE_COUNT> |
| **Record ID** | <RECORD_ID> |
| **Planned Stage** | <TARGET_STAGE> |

**Compliance Tier B Characteristics:**

- **NO HOP bundles:** Does not produce manifest/summary/telemetry artifacts
- **Action-focused:** Performs operations like cleanup, configuration, validation, diagnostics
- **Lightweight output:** Returns status and action description, not report data
- **Still orchestration-ready:** Can be invoked by orchestrators via `run(argv)`
- **Still agent-discoverable:** Has Tier-3 YAML for agent invocation
- **Still DB-prepared:** Has markers for future action logging

### 1.1 Purpose

<Brief description of what action this utility performs and why>

### 1.2 Current Capabilities

- <Action 1>
- <Action 2>
- <Action 3>

### 1.3 Action Classification

| Classification | Value |
|----------------|-------|
| **Action Type** | cleanup / configure / validate / diagnose / transform / migrate |
| **Idempotent** | Yes / No — <explanation> |
| **Destructive** | Yes / No — <what gets modified/deleted> |
| **Requires Confirmation** | Yes / No — <when confirmation needed> |

---

## 2. Current State Analysis

### 2.1 CLI Interface

```text
usage: <SCRIPT_NAME> [-h] [--repo-root REPO_ROOT] ...
```

**Flags:**

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--repo-root` | path | auto | Repository root override |
| `--dry-run` | flag | false | Show what would be done without doing it |
| `--force` | flag | false | Skip confirmation prompts |
| `--log-level` | choice | INFO | Logging verbosity |
| <additional flags> | | | |

> **Note:** Utilities typically support `--dry-run` and `--force` flags for safe operation.

### 2.2 Entry Points

| Entry | Signature | Returns | Status |
|-------|-----------|---------|--------|
| `main(argv)` | `list[str] \| None` → `int` | Exit code | ⚠️/✅ |
| `run(argv)` | `list[str] \| None` → `dict[str, Any]` | Payload dict | ⚠️/✅ |

#### 2.2.1 Universal Interface Contract (ALL Scripts)

> **⚠️ MANDATORY — Every script MUST pass this section regardless of Tier Class.**

| Requirement | Status | Evidence |
|-------------|--------|----------|
| `run(argv)` entry point exists | ⚠️/✅ | Line L<xxx> |
| Returns `dict[str, Any]` (not int) | ⚠️/✅ | Return type annotation |
| Return dict has `status` key | ⚠️/✅ | <evidence> |
| Return dict has `exit_code` key | ⚠️/✅ | <evidence> |
| `--repo-root` flag supported | ⚠️/✅ | argparse definition at L<xxx> |
| `--log-level` flag supported | ⚠️/✅ | argparse definition at L<xxx> |
| Google-style docstring on `run()` | ⚠️/✅ | Args/Returns documented |
| No `sys.exit()` inside `run()` | ⚠️/✅ | grep confirms absence |
| No `input()` prompts | ⚠️/✅ | Non-interactive execution |
| Exceptions return error payload | ⚠️/✅ | try/except wraps logic |

#### 2.2.2 Return Payload Contract

**Tier B (Action Utility) — REQUIRED keys:**

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `status` | str | ✅ | "ok", "error", "skipped", "dry_run" |
| `exit_code` | int | ✅ | 0=success, 1=skipped/warning, 2=error |
| `action_taken` | str | ✅ | Human-readable description of action performed |
| `artifacts` | None | ✅ | Explicit `None` — utilities do NOT produce bundles |
| `details` | dict | ⚠️ | Optional additional context about the action |

**Example Return Payloads:**

```python
# Success case
{
    "status": "ok",
    "exit_code": 0,
    "action_taken": "Deleted 5 orphan directories from reports/healthview/",
    "artifacts": None,
    "details": {
        "deleted_paths": ["path1", "path2", ...],
        "bytes_freed": 12345,
        "dry_run": False
    }
}

# Dry-run case
{
    "status": "dry_run",
    "exit_code": 0,
    "action_taken": "Would delete 5 orphan directories (dry-run mode)",
    "artifacts": None,
    "details": {
        "would_delete": ["path1", "path2", ...],
        "would_free_bytes": 12345,
        "dry_run": True
    }
}

# Nothing to do case
{
    "status": "skipped",
    "exit_code": 1,
    "action_taken": "No orphan directories found — nothing to clean",
    "artifacts": None,
    "details": {"reason": "no_targets"}
}

# Error case
{
    "status": "error",
    "exit_code": 2,
    "action_taken": "Failed to delete orphan directories",
    "artifacts": None,
    "details": {"error": "Permission denied: path/to/dir"}
}
```

### 2.3 Dependencies

| Dependency | Type | Description |
|------------|------|-------------|
| `<module>` | stdlib / internal / external | <what it's used for> |

### 2.4 Compliance Assessment

#### 2.4.1 Universal Compliance (Tier A & B)

| Requirement | Status | Evidence |
|-------------|--------|----------|
| `run(argv)` returns dict | ⚠️/✅ | <evidence> |
| Status/exit_code in return | ⚠️/✅ | <evidence> |
| Standard CLI flags (repo-root, log-level) | ⚠️/✅ | <evidence> |
| Can be dynamically imported | ⚠️/✅ | `importlib.util` works |
| Idempotent (safe to re-run) | ⚠️/✅ | Multiple runs don't corrupt |

#### 2.4.2 Utility-Specific Compliance (Tier B)

> **These replace HOP Bundle Compliance for Tier B scripts.**

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Returns `artifacts: None` explicitly | ⚠️/✅ | <evidence> |
| Returns `action_taken` string | ⚠️/✅ | <evidence> |
| Supports `--dry-run` flag | ⚠️/✅ | <evidence> |
| Dry-run actually prevents changes | ⚠️/✅ | Tested |
| Logs actions at INFO level | ⚠️/✅ | <evidence> |
| Handles "nothing to do" gracefully | ⚠️/✅ | Returns skipped status |

### 2.5 Action Quality Assessment

> **⚠️ MANDATORY STOP-GATE — DO NOT SKIP**
>
> This section is the **PROOF OF THE UTILITY**. A utility that passes mypy/pytest but performs
> incorrect, dangerous, or unverifiable actions is **WORTHLESS**. Every action claim MUST be
> verified against actual system state changes. If any action claim is false, the utility is
> BROKEN regardless of test results.
>
> **Agent Instruction:** You MUST run the utility in dry-run mode first, verify the proposed
> actions, then run for real and verify the actual changes. Do not proceed until all claims are TRUE.

**MANDATORY: Run utility and verify actual actions before completing this section.**

#### 2.5.1 QA Verification

| Check | Command | Result | Evidence |
|-------|---------|--------|----------|
| mypy --strict | `python -m mypy --strict <script>` | ⚠️/✅ | <error count or "Success"> |
| pytest | `pytest <test_file> -v` | ⚠️/✅ | <X/Y passed in Z.ZZs> |
| CLI execution | `python <script> --help` | ⚠️/✅ | <runs without error> |
| Dry-run | `python <script> --dry-run` | ⚠️/✅ | <shows proposed actions> |
| Actual run | `python <script> --log-level DEBUG` | ⚠️/✅ | <action completed> |

#### 2.5.2 Dry-Run Verification

| Check | Status | Evidence |
|-------|--------|----------|
| Dry-run produces output | ⚠️/✅ | <output shows what would happen> |
| Dry-run makes NO changes | ⚠️/✅ | <filesystem unchanged after dry-run> |
| Dry-run returns `status: "dry_run"` | ⚠️/✅ | <return payload verified> |
| Dry-run `action_taken` is accurate | ⚠️/✅ | <describes proposed action> |

#### 2.5.3 Action Verification (CRITICAL)

> **⚠️ THIS IS THE MOST IMPORTANT CHECK**
>
> Run the utility for real and verify every claimed action actually happened.
> A utility that claims "deleted 5 files" but actually deleted 3 is **LYING**.
> A utility that claims "no changes needed" when changes were needed is **BROKEN**.

| Claimed Action | Verification Method | Actual Result | Verdict |
|----------------|---------------------|---------------|---------|
| <action from action_taken> | <how to verify> | <actual outcome> | ✅/❌ |
| <files deleted/modified> | `Test-Path` or `ls` | <paths exist/don't exist> | ✅/❌ |
| <config changed> | Read config file | <actual config state> | ✅/❌ |

**If ANY claimed action is FALSE, the utility is BROKEN. Fix it before proceeding.**

#### 2.5.4 Safety Verification

| Check | Status | Evidence |
|-------|--------|----------|
| No unintended side effects | ⚠️/✅ | <only intended changes made> |
| Rollback possible (if applicable) | ⚠️/✅ | <how to undo> |
| Error handling prevents partial state | ⚠️/✅ | <atomic or all-or-nothing> |
| Confirmation required for destructive ops | ⚠️/✅ | `--force` required or prompt |

#### 2.5.5 DB Integration Markers

> **⚠️ MANDATORY — Even Tier B scripts MUST have DB Integration markers.**
>
> Utilities don't produce HOP bundles, but they DO log actions. When database integration
> is enabled, action logs will be written to the database for audit trails.

| Check | Status | Evidence |
|-------|--------|----------|
| `from libraries.database_integration import log_action` | ⚠️/✅ | Import at L<xxx> (or equivalent) |
| DB_INTEGRATION_MARKER at action point | ⚠️/✅ | `# DB_INTEGRATION_MARKER:` at L<xxx> |
| Marker describes `utility_actions` table | ⚠️/✅ | Comment specifies intent |
| Action payload is JSON-serializable | ⚠️/✅ | No complex objects |

**Tier B DB Marker Format:**

```python
# DB_INTEGRATION_MARKER: utility_actions.action_log — Action audit trail
result = {
    "status": "ok",
    "exit_code": 0,
    "action_taken": "Deleted 5 orphan directories",
    "artifacts": None,
    "details": {...}
}
# Future: log_action(script_name, result)
return result
```

---

## 2.6 Agent Discoverability (Tier-3 YAML)

> **⚠️ MANDATORY — Every script MUST have a Tier-3 YAML for agent discoverability.**
>
> Agents discover and invoke utilities via Tier-3 metadata. A utility without Tier-3 YAML
> is invisible to agents. Tier-3 helps agents understand when to invoke the utility.

### 2.6.1 Tier-3 YAML Location

**Expected path:** `<SCRIPT_DIR>/<SCRIPT_NAME>.tier3.yaml` or inline in script inventory

| Check | Status | Evidence |
|-------|--------|----------|
| Tier-3 YAML file exists | ⚠️/✅ | Path: <path> |
| YAML is valid (no syntax errors) | ⚠️/✅ | `python -c "import yaml; yaml.safe_load(...)"` |
| Registered in script inventory | ⚠️/✅ | Inventory record at <location> |

### 2.6.2 Tier-3 Required Fields

| Field | Status | Value |
|-------|--------|-------|
| `name` | ⚠️/✅ | `<SCRIPT_NAME>` |
| `path` | ⚠️/✅ | `<SCRIPT_PATH>` |
| `category` | ⚠️/✅ | utility / configurator / diagnostic / faulthandler |
| `compliance_tier` | ⚠️/✅ | B (Action Utility) |
| `entry_point` | ⚠️/✅ | `run` |
| `description` | ⚠️/✅ | <one-line description> |
| `inputs` | ⚠️/✅ | List of input parameters with types |
| `outputs` | ⚠️/✅ | Description of return payload |
| `orchestrator_ready` | ⚠️/✅ | `true` / `false` |
| `db_integration_ready` | ⚠️/✅ | `true` / `false` |
| `action_type` | ⚠️/✅ | cleanup / configure / validate / diagnose / transform |
| `destructive` | ⚠️/✅ | `true` / `false` |
| `supports_dry_run` | ⚠️/✅ | `true` / `false` |

### 2.6.3 Tier-3 YAML Template

```yaml
# Tier-3 Metadata for <SCRIPT_NAME>
# Agent-discoverable utility definition
name: <SCRIPT_NAME>
path: <SCRIPT_PATH>
category: utility  # or: configurator, diagnostic, faulthandler
compliance_tier: B
entry_point: run
description: "<One-line description of what action this utility performs>"
version: "1.0.0"

# Utility-specific metadata
action_type: cleanup  # cleanup, configure, validate, diagnose, transform, migrate
destructive: true     # Does this modify/delete data?
idempotent: true      # Safe to run multiple times?
supports_dry_run: true

inputs:
  - name: repo_root
    type: path
    required: false
    description: "Repository root override"
  - name: dry_run
    type: bool
    required: false
    default: false
    description: "Show what would be done without doing it"
  - name: force
    type: bool
    required: false
    default: false
    description: "Skip confirmation prompts"
  - name: log_level
    type: choice
    choices: [DEBUG, INFO, WARNING, ERROR]
    default: INFO
    description: "Logging verbosity"
  # <additional inputs>

outputs:
  status: "ok|error|skipped|dry_run"
  exit_code: "0=success, 1=skipped, 2=error"
  action_taken: "Human-readable description of action"
  artifacts: "null (utilities don't produce bundles)"
  details: "Optional dict with action-specific data"

orchestrator_ready: true
db_integration_ready: true

# When should agents invoke this utility?
triggers:
  - "<condition that warrants running this utility>"
  - "<another trigger condition>"

tags:
  - <tag1>
  - <tag2>

consumers:
  - coding_agent
  - human_developer
  - ci_pipeline
```

---

## 2.7 Database Integration Preparation

> **⚠️ MANDATORY — Every script MUST be database-integration prepared.**
>
> When database integration is enabled, utilities will log their actions to the database
> for audit trails and operational visibility. Unlike Tier A scripts, utilities write to
> `utility_actions` not `hop_*` tables.

### 2.7.1 DB Schema Intent

**For Utility (Tier B Action Utility):**

| Data Point | Target Table | Key Columns |
|------------|--------------|-------------|
| Action log | `utility_actions` | script_name, action_type, action_taken, status, timestamp |
| Details | `utility_actions` | details_json (serialized details dict) |

### 2.7.2 DB Integration Readiness Checklist

| Check | Status | Evidence |
|-------|--------|----------|
| Return payload is JSON-serializable | ⚠️/✅ | No datetime, Path objects |
| `action_taken` is descriptive string | ⚠️/✅ | Not empty or generic |
| `details` dict is JSON-serializable | ⚠️/✅ | All values are primitives |
| DB_INTEGRATION_MARKER present | ⚠️/✅ | At return statement |

### 2.7.3 DB Integration Marker Format

```python
def run(argv: list[str] | None = None) -> dict[str, Any]:
    """Run the utility."""
    # ... action logic ...
    
    # DB_INTEGRATION_MARKER: utility_actions.action_log — Audit trail for utility execution
    result = {
        "status": status,
        "exit_code": exit_code,
        "action_taken": action_description,
        "artifacts": None,  # Tier B: no bundles
        "details": {
            "items_processed": count,
            "dry_run": args.dry_run,
            # ... other details ...
        }
    }
    return result
```

---

## 3. Gap Analysis

### 3.1 Required Changes

#### 3.1.1 Universal Compliance Gaps

| Gap | Priority | Effort |
|-----|----------|--------|
| Missing `run()` entry point | High | M |
| `run()` returns int not dict | High | M |
| Missing `--repo-root` flag | High | S |
| Missing `--log-level` flag | Medium | S |
| Missing DB_INTEGRATION_MARKER comments | Medium | S |
| Missing Tier-3 YAML | High | M |

#### 3.1.2 Utility-Specific Gaps (Tier B)

| Gap | Priority | Effort |
|-----|----------|--------|
| Missing `--dry-run` flag | High | M |
| Dry-run doesn't prevent changes | High | M |
| Missing `action_taken` in return | High | S |
| Missing `artifacts: None` in return | Medium | S |
| Missing `details` dict | Low | S |
| Interactive prompts without `--force` bypass | Medium | M |

#### 3.1.3 Agent/DB Readiness Gaps

| Gap | Priority | Effort |
|-----|----------|--------|
| No Tier-3 YAML | High | M |
| Tier-3 YAML incomplete | Medium | S |
| Missing `action_type` in Tier-3 | Medium | S |
| Missing `destructive` flag in Tier-3 | Medium | S |
| Payload not JSON-serializable | High | M |
| Missing DB_INTEGRATION_MARKER | Medium | S |

### 3.2 Alteration Locations

| Location | Change | Standard |
|----------|--------|----------|
| `<file>#L<start>-L<end>` | <description> | <Universal/Utility requirement> |

---

## 4. Changes Made

1. **<Change category>** (lines X-Y):
   - <Detail 1>
   - <Detail 2>

2. **<Change category>** (lines X-Y):
   - <Detail 1>

---

## 5. Evidence

### 5.1 Tests

| Test | Status |
|------|--------|
| `<test_file>::<test_name>` | PASSED/FAILED |

### 5.2 Code References

- `<file>#L<start>-L<end>` — <description>

---

## 6. Orchestrator Integration

> **Complete this section to enable orchestrator integration.**
>
> Even Tier B utilities can be invoked by orchestrators. They just don't contribute
> HOP bundles to the orchestrator's output.

### 6.1 ScriptConfig Attributes

| Attribute | Value | Rationale |
|-----------|-------|-----------|
| `name` | `"<script_name>"` | Basename without `.py` |
| `path` | `"<relative_path>"` | From repo root |
| `supports_output_dir` | `False` | Utilities don't produce bundles |
| `supports_artifacts_to_keep` | `False` | No artifacts to prune |
| `uses_argv_kwarg` | `True/False` | Is signature `run(*, argv=...)` or `run(argv)`? |
| `custom_args` | `["--dry-run"]` or `None` | Utility-specific args |

### 6.2 Recommended ScriptConfig

```python
ScriptConfig(
    name="<script_name>",
    path="<relative_path>",
    supports_output_dir=False,  # Tier B: no bundle output
    supports_artifacts_to_keep=False,  # Tier B: no artifacts
    uses_argv_kwarg=<True/False>,  # <rationale>
)
```

### 6.3 Orchestration Readiness Checklist

> **All scripts MUST pass this checklist before being considered "ready" — even if never
> assigned to an orchestrator.**

| Check | Status | Evidence |
|-------|--------|----------|
| `run(argv)` callable exposed | ⚠️/✅ | `from <module> import run` works |
| `run()` returns dict (not int) | ⚠️/✅ | `isinstance(result, dict)` |
| Return dict has required keys | ⚠️/✅ | status, exit_code, action_taken, artifacts |
| Can be dynamically imported | ⚠️/✅ | `importlib.util.spec_from_file_location` |
| No `sys.exit()` in `run()` | ⚠️/✅ | grep for `sys.exit` |
| No interactive prompts (or `--force` bypass) | ⚠️/✅ | Non-blocking execution |
| Exceptions wrapped gracefully | ⚠️/✅ | Returns error payload vs raising |
| Idempotent (safe to re-run) | ⚠️/✅ | Multiple runs don't corrupt state |
| Tier-3 YAML complete | ⚠️/✅ | All required fields populated |
| DB Integration markers present | ⚠️/✅ | Marker at return statement |

### 6.4 Orchestrator Outcome Handling

> **How orchestrators should handle Tier B utility outcomes:**

| Utility Status | Orchestrator Behavior |
|----------------|----------------------|
| `"ok"` | Continue to next script |
| `"dry_run"` | Log dry-run, continue (or stop based on config) |
| `"skipped"` | Log skipped, continue (not a failure) |
| `"error"` | Log error, fail-fast or continue based on config |

---

## 7. Completion

**Phase 4 processing complete (<YYYY-MM-DD>)**

- [ ] Universal compliance verified (Section 2.2.1)
- [ ] Utility-specific compliance verified (Section 2.4.2)
- [ ] Action quality verified (Section 2.5)
- [ ] Tier-3 YAML created/updated (Section 2.6)
- [ ] DB Integration prepared (Section 2.7)
- [ ] Orchestration readiness verified (Section 6.3)
- [ ] Frontmatter updated: `status: archived`
- [ ] Tier-2 roster record updated
- [ ] Working document archived

---

## 8. Template Variables

Replace these placeholders when using this template:

| Variable | Description |
|----------|-------------|
| `<SCRIPT_NAME>` | Script filename (e.g., `cleanup_orphan_dirs.py`) |
| `<SCRIPT_PATH>` | Full path (e.g., `.repo_studios/scripts/utilities/cleanup_orphan_dirs.py`) |
| `<SCRIPT_DIR>` | Script directory (e.g., `.repo_studios/scripts/utilities`) |
| `<RECORD_ID>` | ASR record ID (e.g., `ASR-003`) |
| `<YYYY-MM-DD>` | ISO date |
| `<LINE_COUNT>` | Script line count |
| `<TARGET_STAGE>` | Destination stage (e.g., `Stage 4.2`) |

---

## 9. Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.0.0 | 2026-01-26 | Initial version with Universal Law, Tier B compliance, Tier-3 YAML, DB Integration, dry-run verification |

---

## Appendix A: Tier A vs Tier B Comparison

| Aspect | Tier A (Report Generator) | Tier B (Action Utility) |
|--------|---------------------------|-------------------------|
| **Produces HOP bundle** | ✅ manifest/summary/telemetry | ❌ None |
| **Output directory** | `YYYYMMDD-HHMM/` timestamped | None |
| **Return payload** | run_dir, manifest, telemetry, summary | action_taken, artifacts=None, details |
| **DB tables** | `hop_manifests`, `hop_summaries`, `hop_telemetry` | `utility_actions` |
| **Supports --output-dir** | Usually yes | No |
| **Supports --artifacts-to-keep** | Usually yes | No |
| **Supports --dry-run** | Rarely | Usually yes |
| **Examples** | Producers, Consumers, Aggregators, Summarizers | Cleanup, Config, Diagnostic, Faulthandler |

## Appendix B: Common Utility Patterns

### B.1 Cleanup Utility Pattern

```python
def run(argv: list[str] | None = None) -> dict[str, Any]:
    args = parse_args(argv)
    
    targets = find_cleanup_targets(args.repo_root)
    
    if not targets:
        return {
            "status": "skipped",
            "exit_code": 1,
            "action_taken": "No cleanup targets found",
            "artifacts": None,
            "details": {"reason": "no_targets"}
        }
    
    if args.dry_run:
        return {
            "status": "dry_run",
            "exit_code": 0,
            "action_taken": f"Would delete {len(targets)} items",
            "artifacts": None,
            "details": {"would_delete": [str(t) for t in targets]}
        }
    
    deleted = delete_targets(targets)
    
    # DB_INTEGRATION_MARKER: utility_actions.action_log — Cleanup audit trail
    return {
        "status": "ok",
        "exit_code": 0,
        "action_taken": f"Deleted {len(deleted)} items",
        "artifacts": None,
        "details": {"deleted": [str(d) for d in deleted]}
    }
```

### B.2 Validation Utility Pattern

```python
def run(argv: list[str] | None = None) -> dict[str, Any]:
    args = parse_args(argv)
    
    issues = validate_target(args.target)
    
    # DB_INTEGRATION_MARKER: utility_actions.action_log — Validation audit trail
    if issues:
        return {
            "status": "error",
            "exit_code": 2,
            "action_taken": f"Validation failed with {len(issues)} issues",
            "artifacts": None,
            "details": {"issues": issues}
        }
    
    return {
        "status": "ok",
        "exit_code": 0,
        "action_taken": "Validation passed",
        "artifacts": None,
        "details": {"checked": args.target}
    }
```
