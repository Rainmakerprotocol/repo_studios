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
  - producer
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

---

## 1. Script Identity

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

### 1.1 Purpose

<Brief description of what this script does and why>

### 1.2 Current Capabilities

- <Capability 1>
- <Capability 2>
- <Capability 3>

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
| `--output-dir` | path | HOP default | Output directory for artifacts |
| `--timestamp` | str | auto | ISO timestamp override |
| `--log-level` | choice | INFO | Logging verbosity |
| `--artifacts-to-keep` | int | 5 | Retention budget (Tier A only) |
| <additional flags> | | | |

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

**Tier B (Action Utilities) — REQUIRED keys:**

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `status` | str | ✅ | "ok" or "error" |
| `exit_code` | int | ✅ | 0=success, non-zero=failure |
| `action_taken` | str | ✅ | Description of action performed |
| `artifacts` | None | ✅ | Explicit null (no bundle produced) |
| `details` | dict | ⚠️ | Optional additional context |

### 2.3 Current Output Contract

**Output root:** `.repo_studios/reports/healthview/producer_reports/<TOPIC>/<YYYYMMDD-HHMM>/`

**Artifacts:**

| Artifact | Format | Description |
|----------|--------|-------------|
| `manifest.json` | JSON | Schema version, status, inputs |
| `summary.md` | Markdown | Human-readable summary |
| `telemetry.json` | JSON | Execution metrics |
| <additional artifacts> | | |

### 2.4 Compliance Assessment

#### 2.4.1 Universal Compliance (Tier A & B)

| Requirement | Status | Evidence |
|-------------|--------|----------|
| `run(argv)` returns dict | ⚠️/✅ | <evidence> |
| Status/exit_code in return | ⚠️/✅ | <evidence> |
| Standard CLI flags (repo-root, log-level) | ⚠️/✅ | <evidence> |
| Can be dynamically imported | ⚠️/✅ | `importlib.util` works |
| Idempotent (safe to re-run) | ⚠️/✅ | Multiple runs don't corrupt |

#### 2.4.2 HOP Bundle Compliance (Tier A Only)

> **Skip this section if Compliance Tier = B**

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Base package (manifest/summary/telemetry) | ⚠️/✅ | <evidence> |
| Uses `build_topic_path()` or `create_storage()` | ⚠️/✅ | <evidence> |
| Uses `prune_run_directories()` | ⚠️/✅ | <evidence> |
| No `latest_*` pointer files | ⚠️/✅ | <evidence> |
| Directory format `YYYYMMDD-HHMM` | ⚠️/✅ | <evidence> |
| `--artifacts-to-keep` flag supported | ⚠️/✅ | <evidence> |

### 2.5 Output Quality Assessment

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

| Check | Command | Result | Evidence |
|-------|---------|--------|----------|
| mypy --strict | `python -m mypy --strict <script>` | ⚠️/✅ | <error count or "Success"> |
| pytest | `pytest <test_file> -v` | ⚠️/✅ | <X/Y passed in Z.ZZs> |
| CLI execution | `python <script> --help` | ⚠️/✅ | <runs without error> |
| Actual run | `python <script> --log-level DEBUG` | ⚠️/✅ | <output path confirmed> |

#### 2.5.2 summary.md Quality (Aesthetics & Lint)

| Check | Status | Evidence |
|-------|--------|----------|
| Markdownlint clean | ⚠️/✅ | `npx markdownlint-cli2 <summary.md>` — 0 errors |
| Single H1 heading | ⚠️/✅ | <heading text> |
| No bare URLs | ⚠️/✅ | <all links are descriptive> |
| Tables properly formatted | ⚠️/✅ | <alignment, header row present> |
| Actionable next-steps section | ⚠️/✅ | <checkbox items present> |
| No hardcoded absolute paths | ⚠️/✅ | <paths are relative or parameterized> |

#### 2.5.3 Machine-Readable Artifacts (JSON Quality)

| Check | Status | Evidence |
|-------|--------|----------|
| manifest.json valid JSON | ⚠️/✅ | `python -m json.tool <file>` |
| telemetry.json valid JSON | ⚠️/✅ | `python -m json.tool <file>` |
| Schema version present | ⚠️/✅ | `schema_version` field in manifest |
| Timestamp ISO 8601 format | ⚠️/✅ | `YYYY-MM-DDTHH:MM:SS+00:00` |
| Status field present | ⚠️/✅ | `status: ok|error|violations` |
| Consistent key naming | ⚠️/✅ | snake_case throughout |

#### 2.5.4 DB Integration Markers

> **⚠️ MANDATORY — Every script MUST have DB Integration markers for future database migration.**
>
> Even if database writes are currently dormant, the markers MUST be present so that when
> database integration is enabled, the script is ready without code changes.

| Check | Status | Evidence |
|-------|--------|----------|
| `from libraries.database_integration import create_storage` | ⚠️/✅ | Import at L<xxx> |
| DB_INTEGRATION_MARKER comments present | ⚠️/✅ | Line numbers where markers exist |
| Marker at manifest.json write | ⚠️/✅ | `# DB_INTEGRATION_MARKER:` at L<xxx> |
| Marker at summary.md write | ⚠️/✅ | `# DB_INTEGRATION_MARKER:` at L<xxx> |
| Marker at telemetry.json write | ⚠️/✅ | `# DB_INTEGRATION_MARKER:` at L<xxx> |
| Uses `create_storage()` for writes | ⚠️/✅ | `storage.write_*()` calls |
| Marker describes target table/column | ⚠️/✅ | Comments specify DB schema intent |

**Tier B (Action Utilities) DB Markers:**

| Check | Status | Evidence |
|-------|--------|----------|
| DB_INTEGRATION_MARKER at action log point | ⚠️/✅ | L<xxx> |
| Marker describes action_log table intent | ⚠️/✅ | Comment present |

#### 2.5.5 Output Truth Verification (CRITICAL)

> **⚠️ THIS IS THE MOST IMPORTANT CHECK**
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

---

## 2.6 Agent Discoverability (Tier-3 YAML)

> **⚠️ MANDATORY — Every script MUST have a Tier-3 YAML for agent discoverability.**
>
> Agents discover and invoke scripts via Tier-3 metadata. A script without Tier-3 YAML is
> invisible to agents. Even Utilities and Libraries need Tier-3 for agents to know they exist.

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
| `category` | ⚠️/✅ | producer/consumer/aggregator/summarizer/utility/library |
| `compliance_tier` | ⚠️/✅ | A (Report Generator) / B (Action Utility) |
| `entry_point` | ⚠️/✅ | `run` |
| `description` | ⚠️/✅ | <one-line description> |
| `inputs` | ⚠️/✅ | List of input parameters with types |
| `outputs` | ⚠️/✅ | Description of return payload |
| `orchestrator_ready` | ⚠️/✅ | `true` / `false` |
| `db_integration_ready` | ⚠️/✅ | `true` / `false` |

### 2.6.3 Tier-3 YAML Template

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

---

## 2.7 Database Integration Preparation

> **⚠️ MANDATORY — Every script MUST be database-integration prepared.**
>
> When database integration is enabled, scripts will write to both filesystem AND database.
> The `create_storage()` helper handles this transparently, but scripts must be structured
> correctly for the dual-write to work.

### 2.7.1 DB Schema Intent

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

### 2.7.2 DB Integration Readiness Checklist

| Check | Status | Evidence |
|-------|--------|----------|
| Uses `create_storage()` (not raw file writes) | ⚠️/✅ | <evidence> |
| Passes `viewer_slug` correctly | ⚠️/✅ | Empty string or valid slug |
| Passes `topic` correctly | ⚠️/✅ | TOPIC_SLUG constant |
| Passes `timestamp` correctly | ⚠️/✅ | YYYYMMDD-HHMM format |
| All writes go through `storage.write_*()` | ⚠️/✅ | No direct `Path.write_text()` |
| Payload is JSON-serializable | ⚠️/✅ | No datetime objects, Path objects |

### 2.7.3 DB Integration Marker Format

```python
# DB_INTEGRATION_MARKER: <table_name>.<column_name> — <description>
storage.write_manifest(manifest)

# DB_INTEGRATION_MARKER: hop_summaries.content_md — Human-readable summary
storage.write_summary({"markdown": summary_md}, format="md")

# DB_INTEGRATION_MARKER: hop_telemetry.metrics_json — Execution metrics
storage.write_telemetry(telemetry)
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

#### 3.1.2 HOP Bundle Gaps (Tier A Only)

| Gap | Priority | Effort |
|-----|----------|--------|
| Not using `build_topic_path()` | High | M |
| Not using `create_storage()` | High | M |
| Missing `manifest.json` | High | L |
| Absolute paths in summary.md | Medium | M |
| No pruning support | Medium | M |
| Missing `--artifacts-to-keep` flag | Medium | S |

#### 3.1.3 Agent/DB Readiness Gaps

| Gap | Priority | Effort |
|-----|----------|--------|
| No Tier-3 YAML | High | M |
| Tier-3 YAML incomplete | Medium | S |
| Raw file writes instead of `create_storage()` | High | M |
| Payload not JSON-serializable | High | M |
| Missing DB_INTEGRATION_MARKER at write points | Medium | S |

### 3.2 Alteration Locations

| Location | Change | Standard |
|----------|--------|----------|
| `<file>#L<start>-L<end>` | <description> | <HOP/Universal requirement> |

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

### 6.1 ScriptConfig Attributes

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

### 6.2 Recommended ScriptConfig

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

### 6.3 Orchestration Readiness Checklist

> **All scripts MUST pass this checklist before being considered "ready" — even if never
> assigned to an orchestrator.**

| Check | Status | Evidence |
|-------|--------|----------|
| `run(argv)` callable exposed | ⚠️/✅ | `from <module> import run` works |
| `run()` returns dict (not int) | ⚠️/✅ | `isinstance(result, dict)` |
| Return dict has required keys | ⚠️/✅ | Per compliance tier contract |
| Can be dynamically imported | ⚠️/✅ | `importlib.util.spec_from_file_location` |
| No `sys.exit()` in `run()` | ⚠️/✅ | grep for `sys.exit` |
| No interactive prompts | ⚠️/✅ | No `input()` calls |
| Exceptions wrapped gracefully | ⚠️/✅ | Returns error payload vs raising |
| Idempotent (safe to re-run) | ⚠️/✅ | Multiple runs don't corrupt state |
| Tier-3 YAML complete | ⚠️/✅ | All required fields populated |
| DB Integration markers present | ⚠️/✅ | `create_storage()` used |

---

## 7. Completion

**Phase 4 processing complete (<YYYY-MM-DD>)**

- [ ] Universal compliance verified (Section 2.2.1)
- [ ] HOP bundle compliance verified (Section 2.4.2, if Tier A)
- [ ] Output quality verified (Section 2.5)
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
| `<SCRIPT_NAME>` | Script filename (e.g., `validate_inventory.py`) |
| `<SCRIPT_PATH>` | Full path (e.g., `.repo_studios/scripts/producers/validate_inventory.py`) |
| `<SCRIPT_DIR>` | Script directory (e.g., `.repo_studios/scripts/producers`) |
| `<RECORD_ID>` | ASR record ID (e.g., `ASR-008`) |
| `<YYYY-MM-DD>` | ISO date |
| `<LINE_COUNT>` | Script line count |
| `<TARGET_STAGE>` | Destination stage (e.g., `Stage 4.2`) |
| `<TOPIC>` | Topic slug (e.g., `inventory_validation`) |

---

## 9. Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.0.0 | 2026-01-26 | Added Universal Law, Compliance Tiers, Tier-3 YAML, DB Integration Preparation, Orchestration Readiness Checklist, ScriptConfig section |
| 1.0.0 | (original) | Initial template with HOP compliance focus |
