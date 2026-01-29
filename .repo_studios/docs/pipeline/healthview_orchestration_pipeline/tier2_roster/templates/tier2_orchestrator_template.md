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
  - orchestrator
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
> **Orchestrator Special Status:** Orchestrators are meta-scripts that invoke other scripts.
> They are **themselves** orchestration-ready (can be invoked by higher-level orchestrators),
> agent-discoverable, and database-integration prepared for their own report bundles.

---

## 1. Script Identity

| Field | Value |
|-------|-------|
| **Name** | `<SCRIPT_NAME>` |
| **Path** | `<SCRIPT_PATH>` |
| **Tier Class** | Orchestrator |
| **Compliance Tier** | A (Report Generator) — orchestrators produce HOP bundles |
| **Lines** | <LINE_COUNT> |
| **Record ID** | <RECORD_ID> |
| **Stage** | <STAGE_ID> |

### 1.1 Purpose

<Brief description of what script chain this orchestrator coordinates and what final bundle it produces>

### 1.2 Current Capabilities

- Chains: <list of scripts in execution order>
- Produces: <orchestrated bundle description>
- Error handling: <fail-fast / continue-on-error>
- <Additional capability>

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
| `--fail-fast` | flag | false | Stop on first script failure |
| <additional flags> | | | |

### 2.2 Entry Points

| Entry | Signature | Returns | Status |
|-------|-----------|---------|--------|
| `main(argv)` | `list[str] \| None` → `int` | Exit code | ⚠️/✅ |
| `run(argv)` | `list[str] \| None` → `dict[str, Any]` | Payload dict with child outcomes | ⚠️/✅ |

#### 2.2.1 Universal Interface Contract (ALL Scripts)

> **⚠️ MANDATORY — Even orchestrators MUST pass this section.**

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

**Orchestrator (Tier A Report Generator) — REQUIRED keys:**

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `status` | str | ✅ | "ok", "error", "partial" |
| `exit_code` | int | ✅ | 0=all passed, 1=partial, 2=error |
| `run_dir` | str | ✅ | Path to orchestrator's output bundle |
| `output_dir` | str | ✅ | Parent output directory |
| `run_id` | str | ✅ | Timestamp slug (YYYYMMDD-HHMM) |
| `manifest` | dict | ✅ | Full manifest content |
| `telemetry` | dict | ✅ | Full telemetry content including child timing |
| `summary` | dict | ✅ | Summary metrics subset |
| `child_outcomes` | list[dict] | ✅ | List of child script outcomes |
| `scripts_run` | int | ✅ | Number of scripts executed |
| `scripts_passed` | int | ✅ | Number of scripts that succeeded |
| `scripts_failed` | int | ✅ | Number of scripts that failed |

### 2.3 Script Chain

| Order | Script | Type | Invocation |
|-------|--------|------|------------|
| 1 | `<script_1>` | producer | `run(argv)` / subprocess |
| 2 | `<script_2>` | consumer | `run(argv)` / subprocess |
| 3 | `<script_3>` | aggregator | `run(argv)` / subprocess |

### 2.4 Current Output Contract

**Output root:** `.repo_studios/reports/healthview/orchestrator_reports/<TOPIC>/<YYYYMMDD-HHMM>/`

**Artifacts:**

| Artifact | Format | Description |
|----------|--------|-------------|
| `manifest.json` | JSON | Schema version, status, child outcomes |
| `summary.md` | Markdown | Human-readable orchestration report |
| `telemetry.json` | JSON | Execution metrics, timing, child statuses |
| <additional artifacts> | | |

### 2.5 Compliance Assessment

#### 2.5.1 Universal Compliance (Tier A & B)

| Requirement | Status | Evidence |
|-------------|--------|----------|
| `run(argv)` returns dict | ⚠️/✅ | <evidence> |
| Status/exit_code in return | ⚠️/✅ | <evidence> |
| Standard CLI flags (repo-root, log-level) | ⚠️/✅ | <evidence> |
| Can be dynamically imported | ⚠️/✅ | `importlib.util` works |
| Idempotent (safe to re-run) | ⚠️/✅ | Multiple runs don't corrupt |

#### 2.5.2 HOP Bundle Compliance (Tier A — Orchestrator)

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Base package (manifest/summary/telemetry) | ⚠️/✅ | <evidence> |
| Uses `build_topic_path()` or `create_storage()` | ⚠️/✅ | <evidence> |
| Uses `prune_run_directories()` | ⚠️/✅ | <evidence> |
| No `latest_*` pointer files | ⚠️/✅ | <evidence> |
| `run(argv)` entry point | ⚠️/✅ | <evidence> |
| Directory format `YYYYMMDD-HHMM` | ⚠️/✅ | <evidence> |
| Child script invocation via `run(argv)` | ⚠️/✅ | <evidence> |
| ScriptConfig for each child | ⚠️/✅ | <evidence> |
| Outcome dataclass pattern | ⚠️/✅ | <evidence> |
| `--artifacts-to-keep` flag supported | ⚠️/✅ | <evidence> |

### 2.6 Output Quality Assessment

> **⚠️ MANDATORY STOP-GATE — DO NOT SKIP**
>
> This section is the **PROOF OF THE ORCHESTRATOR**. An orchestrator that passes mypy/pytest but
> produces incorrect child outcome reports, misleading timings, or unverifiable claims is
> **WORTHLESS**. Every claim in the output artifacts MUST be verified against actual child runs.
>
> **Agent Instruction:** You MUST run the orchestrator, read every output file, and verify each
> claim against the actual child script outcomes. Do not proceed until all claims are TRUE.

**MANDATORY: Run orchestrator and inspect actual output before completing this section.**

#### 2.6.1 QA Verification

| Check | Command | Result | Evidence |
|-------|---------|--------|----------|
| mypy --strict | `python -m mypy --strict <script>` | ⚠️/✅ | <error count or "Success"> |
| pytest | `pytest <test_file> -v` | ⚠️/✅ | <X/Y passed in Z.ZZs> |
| CLI execution | `python <script> --help` | ⚠️/✅ | <runs without error> |
| Actual run | `python <script> --log-level DEBUG` | ⚠️/✅ | <output path confirmed> |

#### 2.6.2 summary.md Quality (Aesthetics & Lint)

| Check | Status | Evidence |
|-------|--------|----------|
| Markdownlint clean | ⚠️/✅ | `npx markdownlint-cli2 <summary.md>` — 0 errors |
| Single H1 heading | ⚠️/✅ | <heading text> |
| No bare URLs | ⚠️/✅ | <all links are descriptive> |
| Tables properly formatted | ⚠️/✅ | <alignment, header row present> |
| Child script status table | ⚠️/✅ | <shows pass/fail for each child> |
| Timing breakdown present | ⚠️/✅ | <per-script timing visible> |
| No hardcoded absolute paths | ⚠️/✅ | <paths are relative or parameterized> |

#### 2.6.3 Machine-Readable Artifacts (JSON Quality)

| Check | Status | Evidence |
|-------|--------|----------|
| manifest.json valid JSON | ⚠️/✅ | `python -m json.tool <file>` |
| telemetry.json valid JSON | ⚠️/✅ | `python -m json.tool <file>` |
| Schema version present | ⚠️/✅ | `schema_version` field in manifest |
| Timestamp ISO 8601 format | ⚠️/✅ | `YYYY-MM-DDTHH:MM:SS+00:00` |
| Status field present | ⚠️/✅ | `status: ok\|error\|partial` |
| Consistent key naming | ⚠️/✅ | snake_case throughout |
| child_outcomes array valid | ⚠️/✅ | Each outcome has name, status, exit_code |

#### 2.6.4 DB Integration Markers

> **⚠️ MANDATORY — Every script MUST have DB Integration markers for future database migration.**
>
> Orchestrators have additional markers for child outcome writes.

| Check | Status | Evidence |
|-------|--------|----------|
| `from libraries.database_integration import create_storage` | ⚠️/✅ | Import at L<xxx> |
| DB_INTEGRATION_MARKER comments present | ⚠️/✅ | Line numbers where markers exist |
| Marker at manifest.json write | ⚠️/✅ | `# DB_INTEGRATION_MARKER:` at L<xxx> |
| Marker at summary.md write | ⚠️/✅ | `# DB_INTEGRATION_MARKER:` at L<xxx> |
| Marker at telemetry.json write | ⚠️/✅ | `# DB_INTEGRATION_MARKER:` at L<xxx> |
| Marker at child_outcomes write | ⚠️/✅ | `# DB_INTEGRATION_MARKER:` at L<xxx> |
| Uses `create_storage()` for writes | ⚠️/✅ | `storage.write_*()` calls |
| Marker describes target table/column | ⚠️/✅ | Comments specify DB schema intent |

#### 2.6.5 Output Truth Verification (CRITICAL)

> **⚠️ THIS IS THE MOST IMPORTANT CHECK**
>
> Read every claim in summary.md and manifest.json. Verify each against actual child outcomes.
> An orchestrator that reports "all scripts passed" when a child failed is **LYING**.
> An orchestrator that shows incorrect timing is **BROKEN**.

| Claim in Output | Verification Method | Ground Truth | Verdict |
|-----------------|---------------------|--------------|---------|
| <scripts_passed count> | Count actual child outcomes | <actual count> | ✅/❌ |
| <scripts_failed count> | Count actual child outcomes | <actual count> | ✅/❌ |
| <child X passed> | Check child's return payload | <actual status> | ✅/❌ |
| <child X timing> | Cross-reference telemetry | <actual duration> | ✅/❌ |
| <all child bundles exist> | Check filesystem | <paths exist> | ✅/❌ |

**If ANY claim is FALSE, the orchestrator is BROKEN. Fix it before proceeding.**

---

## 2.7 Child Script Management

> **Orchestrator-Specific Section:** Documents how this orchestrator manages its child scripts.

### 2.7.1 ScriptConfig Registry

> **⚠️ CRITICAL: `supports_output_dir` Safety Warning for Child Scripts**
>
> When adding child scripts to the orchestrator, **default `supports_output_dir=False`** unless
> you have a specific reason to override. This is a safety-critical setting:
>
> | Setting | Orchestrator Behavior | Child Script Pruning | Safety |
> |---------|----------------------|---------------------|--------|
> | `False` | Child uses internal `build_topic_path()` | Topic-scoped ✅ | **SAFE** |
> | `True` | Orchestrator passes generic parent dir | Cross-topic ❌ | **DANGEROUS** |
>
> **Incident Reference:** Setting `supports_output_dir=True` caused orchestrator to pass
> `--output-dir producer_reports/` to a child script, which then called `prune_run_directories()`
> on the parent directory — deleting 343 files across ALL topic subdirectories.
>
> **Rule:** If a child script uses `build_topic_path()` for its default output directory,
> set `supports_output_dir=False` in its ScriptConfig to preserve topic-aware pruning.

| Script | Config | Status |
|--------|--------|--------|
| `<script_1>` | `ScriptConfig(name="...", path="...", supports_output_dir=False, ...)` | ⚠️/✅ |
| `<script_2>` | `ScriptConfig(name="...", path="...", supports_output_dir=False, ...)` | ⚠️/✅ |
| `<script_3>` | `ScriptConfig(name="...", path="...", supports_output_dir=False, ...)` | ⚠️/✅ |

### 2.7.2 Child Invocation Pattern

| Check | Status | Evidence |
|-------|--------|----------|
| Uses `ScriptConfig` dataclass | ⚠️/✅ | Import at L<xxx> |
| Uses `ScriptRunner` or equivalent | ⚠️/✅ | L<xxx> |
| Dynamic import via `importlib.util` | ⚠️/✅ | L<xxx> |
| Calls child `run(argv)` not subprocess | ⚠️/✅ | L<xxx> |
| Captures child return payload | ⚠️/✅ | L<xxx> |
| Handles child exceptions gracefully | ⚠️/✅ | L<xxx> |

### 2.7.3 Child Outcome Dataclass

| Field | Type | Captured |
|-------|------|----------|
| `name` | str | ⚠️/✅ |
| `path` | str | ⚠️/✅ |
| `status` | str | ⚠️/✅ |
| `exit_code` | int | ⚠️/✅ |
| `run_dir` | str | ⚠️/✅ |
| `duration` | float | ⚠️/✅ |
| `error` | str \| None | ⚠️/✅ |

---

## 2.8 Agent Discoverability (Tier-3 YAML)

> **⚠️ MANDATORY — Even orchestrators MUST have a Tier-3 YAML for agent discoverability.**
>
> Orchestrators can be invoked by agents or higher-level orchestrators. The Tier-3 YAML
> must document both the orchestrator's interface AND the scripts it chains.

### 2.8.1 Tier-3 YAML Location

**Expected path:** `<SCRIPT_DIR>/<SCRIPT_NAME>.tier3.yaml` or inline in script inventory

| Check | Status | Evidence |
|-------|--------|----------|
| Tier-3 YAML file exists | ⚠️/✅ | Path: <path> |
| YAML is valid (no syntax errors) | ⚠️/✅ | `python -c "import yaml; yaml.safe_load(...)"` |
| Registered in script inventory | ⚠️/✅ | Inventory record at <location> |

### 2.8.2 Tier-3 Required Fields

| Field | Status | Value |
|-------|--------|-------|
| `name` | ⚠️/✅ | `<SCRIPT_NAME>` |
| `path` | ⚠️/✅ | `<SCRIPT_PATH>` |
| `category` | ⚠️/✅ | orchestrator |
| `compliance_tier` | ⚠️/✅ | A (Report Generator) |
| `entry_point` | ⚠️/✅ | `run` |
| `description` | ⚠️/✅ | <one-line description> |
| `inputs` | ⚠️/✅ | List of input parameters with types |
| `outputs` | ⚠️/✅ | Description of return payload |
| `orchestrator_ready` | ⚠️/✅ | `true` (can be invoked by higher-level orchestrators) |
| `db_integration_ready` | ⚠️/✅ | `true` / `false` |
| `child_scripts` | ⚠️/✅ | List of scripts this orchestrator chains |

### 2.8.3 Tier-3 YAML Template

```yaml
# Tier-3 Metadata for <SCRIPT_NAME>
# Agent-discoverable orchestrator definition
name: <SCRIPT_NAME>
path: <SCRIPT_PATH>
category: orchestrator
compliance_tier: A
entry_point: run
description: "<One-line description of what this orchestrator coordinates>"
version: "1.0.0"

inputs:
  - name: repo_root
    type: path
    required: false
    description: "Repository root override"
  - name: fail_fast
    type: bool
    required: false
    default: false
    description: "Stop on first script failure"
  - name: log_level
    type: choice
    choices: [DEBUG, INFO, WARNING, ERROR]
    default: INFO
    description: "Logging verbosity"
  # <additional inputs>

outputs:
  status: "ok|error|partial"
  exit_code: "0=all passed, 1=partial, 2=error"
  child_outcomes: "List of child script outcome dicts"
  scripts_run: "Number of scripts executed"
  scripts_passed: "Number of scripts that succeeded"
  scripts_failed: "Number of scripts that failed"

orchestrator_ready: true
db_integration_ready: true

# Orchestrator-specific: list of chained scripts
child_scripts:
  - name: <script_1>
    path: <path_1>
    type: producer
  - name: <script_2>
    path: <path_2>
    type: consumer
  - name: <script_3>
    path: <path_3>
    type: aggregator

tags:
  - <tag1>
  - <tag2>

consumers:
  - coding_agent
  - human_developer
  - ci_pipeline
```

---

## 2.9 Database Integration Preparation

> **⚠️ MANDATORY — Every script MUST be database-integration prepared.**
>
> When database integration is enabled, orchestrators will write their own bundles
> AND aggregate child outcomes to the database.

### 2.9.1 DB Schema Intent

**For Orchestrator (Tier A Report Generator):**

| Artifact | Target Table | Key Columns |
|----------|--------------|-------------|
| manifest.json | `hop_manifests` | viewer_slug, topic, run_timestamp, schema_version, child_refs |
| summary.md | `hop_summaries` | viewer_slug, topic, run_timestamp, content_md |
| telemetry.json | `hop_telemetry` | viewer_slug, topic, run_timestamp, metrics_json |
| child_outcomes | `orchestrator_runs` | orchestrator_name, run_timestamp, child_name, child_status, duration |

### 2.9.2 DB Integration Readiness Checklist

| Check | Status | Evidence |
|-------|--------|----------|
| Uses `create_storage()` (not raw file writes) | ⚠️/✅ | <evidence> |
| Passes `viewer_slug` correctly | ⚠️/✅ | Empty string or valid slug |
| Passes `topic` correctly | ⚠️/✅ | TOPIC_SLUG constant |
| Passes `timestamp` correctly | ⚠️/✅ | YYYYMMDD-HHMM format |
| All writes go through `storage.write_*()` | ⚠️/✅ | No direct `Path.write_text()` |
| Payload is JSON-serializable | ⚠️/✅ | No datetime objects, Path objects |
| Child outcomes are JSON-serializable | ⚠️/✅ | No dataclasses with complex types |

### 2.9.3 DB Integration Marker Format

```python
# DB_INTEGRATION_MARKER: <table_name>.<column_name> — <description>
storage.write_manifest(manifest)

# DB_INTEGRATION_MARKER: hop_summaries.content_md — Human-readable orchestration report
storage.write_summary({"markdown": summary_md}, format="md")

# DB_INTEGRATION_MARKER: hop_telemetry.metrics_json — Execution metrics with child timing
storage.write_telemetry(telemetry)

# DB_INTEGRATION_MARKER: orchestrator_runs.child_outcomes — Child script outcomes
storage.write_artifact("child_outcomes.json", child_outcomes_list)
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

#### 3.1.2 HOP Bundle Gaps (Orchestrator)

| Gap | Priority | Effort |
|-----|----------|--------|
| Not using `build_topic_path()` | High | M |
| Not using `create_storage()` | High | M |
| Missing `manifest.json` | High | L |
| Absolute paths in summary.md | Medium | M |
| No pruning support | Medium | M |
| Missing `--artifacts-to-keep` flag | Medium | S |
| Not using ScriptConfig | High | M |
| Not using Outcome dataclass | High | M |

#### 3.1.3 Agent/DB Readiness Gaps

| Gap | Priority | Effort |
|-----|----------|--------|
| No Tier-3 YAML | High | M |
| Tier-3 YAML incomplete | Medium | S |
| Missing child_scripts in Tier-3 | High | S |
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

## 6. Orchestrator-Specific Validation

> **Orchestrators have additional validation requirements beyond standard scripts.**

### 6.1 Child Script Validation

| Check | Status | Evidence |
|-------|--------|----------|
| All child scripts have `run(argv)` | ⚠️/✅ | Manual verification |
| All child scripts return dict | ⚠️/✅ | Manual verification |
| All child ScriptConfigs correct | ⚠️/✅ | Flags match script capabilities |
| Child Tier-3 YAMLs exist | ⚠️/✅ | Paths verified |

### 6.2 Integration Test

| Check | Status | Evidence |
|-------|--------|----------|
| Full pipeline runs without error | ⚠️/✅ | Terminal output |
| All child bundles created | ⚠️/✅ | Filesystem check |
| Orchestrator bundle created | ⚠️/✅ | Path verified |
| child_outcomes matches actual results | ⚠️/✅ | Cross-reference |

---

## 7. Completion

> **⚠️ This section is the FINAL GATE. Do not mark complete until ALL items are checked.**
>
> The build.md is NOT done when you fill in the sections. It is done when:
>
> 1. The orchestrator has been RUN and outputs verified TRUE
> 2. ALL child scripts executed successfully
> 3. The Tier-3 YAML exists and is validated
> 4. The roster checkboxes are all checked including DONE
> 5. This document's frontmatter shows `status: complete`

### 7.1 Build Document Completion Checklist

**Discovery & Analysis:**

- [ ] Section 1 (Script Identity) — All fields populated
- [ ] Section 2.1 (CLI Interface) — Flags documented from `--help` output
- [ ] Section 2.2 (Entry Points) — Signatures verified against code
- [ ] Section 2.4 (Compliance Assessment) — All checks have evidence

**Implementation & Testing:**

- [ ] Section 3 (Gap Analysis) — Gaps identified with priority/effort
- [ ] Section 4 (Changes Made) — All modifications documented with line numbers
- [ ] Section 5 (Evidence) — Test results captured (pytest/mypy/coverage)

**Truth Verification (CRITICAL):**

- [ ] Section 2.6.1 — QA tests passed (mypy, pytest, CLI execution)
- [ ] Section 2.6.5 — Output truth verified: **ORCHESTRATOR WAS ACTUALLY RUN**
- [ ] Section 2.6.5 — Every claim in manifest/summary/telemetry verified against ground truth
- [ ] Section 2.7 — All child scripts executed in correct order
- [ ] **If any claim was FALSE, it was FIXED before checking this box**

**Tier-3 & DB Integration:**

- [ ] Section 2.8 — Tier-3 YAML created/updated and validated
- [ ] Section 2.9 — DB Integration markers present at all write points

**Orchestrator-Specific Validation:**

- [ ] Section 6 — All orchestrator validation checks pass
- [ ] Child script registry complete
- [ ] ScriptConfig entries verified for all children

### 7.2 Tier-2 Roster Update

> **After completing Section 7.1, update the parent Tier-2 roster document.**

**Roster location:** `../tier2_<stage>_roster.md`

**Workstream checkboxes to update:**

```markdown
#### Implementation Workstreams (checkbox-driven) — <SCRIPT_NAME>

- [x] A. Discovery — confirm CLI surfaces, child scripts, outputs, retention
- [x] B. Plan — draft gap closure plan
- [x] C. Implement — code changes applied (or N/A if already compliant)
- [x] D. Evidence — tests passing (N/N)
- [x] E. Bug fix — issues addressed (or N/A if none found)
- [x] F. Output truth verification — orchestrator run, all claims verified TRUE
- [x] G. Tier-3 YAML — created/updated <tier3_name>.yaml
- [x] H. Child script registry — all children documented with ScriptConfig
- [x] DONE — Phase 4 compliance complete (<YYYY-MM-DD>)
```

**Roster update checklist:**

- [ ] Located script record in Tier-2 roster
- [ ] Checked workstream boxes A through H
- [ ] Added DONE marker with date
- [ ] Updated `phase4_build_doc` field to point to this document
- [ ] Updated `tier3_yaml` field to point to Tier-3 YAML path

### 7.3 Document Finalization

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

### 7.4 Phase 4 Processing Complete

**Completion timestamp:** `<YYYY-MM-DD HH:MM UTC>`

**Summary:**

| Aspect | Status | Evidence |
|--------|--------|----------|
| Universal compliance | ✅ | Section 2.2.1 all checked |
| HOP bundle compliance | ✅ | Section 2.5.2 all checked |
| Output truth verified | ✅ | Section 2.6.5 — all claims TRUE |
| Child scripts executed | ✅ | Section 2.7 — all N children ran |
| Tier-3 YAML | ✅ | `<tier3_yaml_path>` |
| DB Integration ready | ✅ | Markers at L<xxx>, L<yyy>, L<zzz> |
| Roster updated | ✅ | Workstreams A-H + DONE checked |

**Next step:** Orchestrators typically don't need Phase 4B promotion (they ARE the orchestrators).
If this orchestrator is a child of a meta-orchestrator, proceed to Phase 4B.

---

## 8. Template Variables

Replace these placeholders when using this template:

| Variable | Description |
|----------|-------------|
| `<SCRIPT_NAME>` | Script filename (e.g., `orchestrate_stage11.py`) |
| `<SCRIPT_PATH>` | Full path (e.g., `.repo_studios/scripts/orchestrators/orchestrate_stage11.py`) |
| `<SCRIPT_DIR>` | Script directory (e.g., `.repo_studios/scripts/orchestrators`) |
| `<RECORD_ID>` | ASR record ID (e.g., `ASR-012`) |
| `<YYYY-MM-DD>` | ISO date |
| `<LINE_COUNT>` | Script line count |
| `<STAGE_ID>` | Stage this orchestrator manages (e.g., `Stage 11.1`) |
| `<TOPIC>` | Topic slug (e.g., `stage11_orchestration`) |

---

## 9. Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.1.0 | 2026-01-28 | Enhanced Section 7 with complete conclusion workflow (truth verification, child script verification, roster update, finalization steps) |
| 2.0.0 | 2026-01-26 | Added Universal Law, Compliance Tiers, Tier-3 YAML, DB Integration Preparation, Child Script Management, Orchestrator-Specific Validation |
| 1.0.0 | (original) | Initial template with HOP compliance focus |
