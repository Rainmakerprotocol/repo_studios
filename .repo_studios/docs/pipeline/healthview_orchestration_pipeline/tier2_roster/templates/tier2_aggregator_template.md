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
  - aggregator
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
| **Tier Class** | Aggregator |
| **Compliance Tier** | A (Report Generator) |
| **Lines** | <LINE_COUNT> |
| **Record ID** | <RECORD_ID> |
| **Planned Stage** | <TARGET_STAGE> |

### 1.1 Purpose

<Brief description of what multiple sources this aggregator combines and what blended output it produces>

### 1.2 Current Capabilities

- Combines: <list of upstream sources>
- Produces: <aggregated output description>
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
| `--source-dirs` | paths | auto | Directories containing upstream artifacts |
| `--timestamp` | str | auto | ISO timestamp override |
| `--log-level` | choice | INFO | Logging verbosity |
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

**Aggregator (Tier A Report Generator) — REQUIRED keys:**

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
| `sources` | list | ✅ | List of upstream source artifacts aggregated |
| `source_count` | int | ✅ | Number of sources processed |

### 2.3 Upstream Dependencies

| Source | Type | Artifact | Description |
|--------|------|----------|-------------|
| `<source_1>` | producer/consumer | `<artifact_path>` | <what data is consumed> |
| `<source_2>` | producer/consumer | `<artifact_path>` | <what data is consumed> |

### 2.4 Current Output Contract

**Output root:** `.repo_studios/reports/healthview/aggregator_reports/<TOPIC>/<YYYYMMDD-HHMM>/`

**Artifacts:**

| Artifact | Format | Description |
|----------|--------|-------------|
| `manifest.json` | JSON | Schema version, status, inputs, source refs |
| `summary.md` | Markdown | Human-readable aggregated report |
| `telemetry.json` | JSON | Execution metrics, source counts |
| `matrix.json` | JSON | Cross-reference matrix (if applicable) |
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

#### 2.4.2 HOP Bundle Compliance (Tier A — Aggregator)

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Base package (manifest/summary/telemetry) | ⚠️/✅ | <evidence> |
| Uses `build_topic_path()` or `create_storage()` | ⚠️/✅ | <evidence> |
| Uses `prune_run_directories()` | ⚠️/✅ | <evidence> |
| No `latest_*` pointer files | ⚠️/✅ | <evidence> |
| `run(argv)` entry point | ⚠️/✅ | <evidence> |
| Directory format `YYYYMMDD-HHMM` | ⚠️/✅ | <evidence> |
| Multi-source timestamp resolution | ⚠️/✅ | <evidence> |
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
| Status field present | ⚠️/✅ | `status: ok\|error\|violations` |
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
| Marker at matrix.json write (if applicable) | ⚠️/✅ | `# DB_INTEGRATION_MARKER:` at L<xxx> |
| Uses `create_storage()` for writes | ⚠️/✅ | `storage.write_*()` calls |
| Marker describes target table/column | ⚠️/✅ | Comments specify DB schema intent |

#### 2.5.5 Output Truth Verification (CRITICAL)

> **⚠️ THIS IS THE MOST IMPORTANT CHECK**
>
> Read every claim in summary.md and manifest.json. Verify each against ground truth.
> A script that reports "0 violations" when it failed to load input data is **LYING**.
> A script that references paths that don't exist is **BROKEN**.

| Claim in Output | Verification Method | Ground Truth | Verdict |
|-----------------|---------------------|--------------|----------|
| <claim from summary.md> | <how to verify> | <actual state> | ✅/❌ |
| <all upstream sources loaded> | Check logs for each source | <loaded count vs expected> | ✅/❌ |
| <aggregated count is accurate> | Sum of upstream counts | <actual sum> | ✅/❌ |

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
| `category` | ⚠️/✅ | aggregator |
| `compliance_tier` | ⚠️/✅ | A (Report Generator) |
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
category: aggregator
compliance_tier: A
entry_point: run
description: "<One-line description of what sources this aggregator combines>"
version: "1.0.0"

inputs:
  - name: repo_root
    type: path
    required: false
    description: "Repository root override"
  - name: source_dirs
    type: paths
    required: false
    description: "Directories containing upstream artifacts"
  - name: log_level
    type: choice
    choices: [DEBUG, INFO, WARNING, ERROR]
    default: INFO
    description: "Logging verbosity"
  # <additional inputs>

outputs:
  status: "ok|error|issues"
  exit_code: "0=success, 1=issues, 2=error"
  sources: "List of upstream source artifacts aggregated"
  source_count: "Number of sources processed"
  # <additional outputs>

orchestrator_ready: true
db_integration_ready: true

upstream_dependencies:
  - source: <source_1>
    type: producer|consumer
    artifact: <artifact_path>
  - source: <source_2>
    type: producer|consumer
    artifact: <artifact_path>

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

**For Aggregator (Tier A Report Generator):**

| Artifact | Target Table | Key Columns |
|----------|--------------|-------------|
| manifest.json | `hop_manifests` | viewer_slug, topic, run_timestamp, schema_version, sources |
| summary.md | `hop_summaries` | viewer_slug, topic, run_timestamp, content_md |
| telemetry.json | `hop_telemetry` | viewer_slug, topic, run_timestamp, metrics_json |
| matrix.json | `hop_matrices` | viewer_slug, topic, run_timestamp, matrix_json |

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

# DB_INTEGRATION_MARKER: hop_matrices.matrix_json — Cross-reference matrix
storage.write_artifact("matrix.json", matrix_data)
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

#### 3.1.2 HOP Bundle Gaps (Aggregator)

| Gap | Priority | Effort |
|-----|----------|--------|
| Not using `build_topic_path()` | High | M |
| Not using `create_storage()` | High | M |
| Missing `manifest.json` | High | L |
| Absolute paths in summary.md | Medium | M |
| No pruning support | Medium | M |
| Missing `--artifacts-to-keep` flag | Medium | S |
| Missing multi-source timestamp resolution | High | M |

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
| `<file>#L<start>-L<end>` | <description> | <HOP requirement> |

---

## 4. Changes Made

1. **<Change category>** (lines X-Y):
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

| Attribute | Value | Rationale |
|-----------|-------|-----------|
| `name` | `"<script_name>"` | Basename without `.py` |
| `path` | `"<relative_path>"` | From repo root |
| `supports_output_dir` | `True/False` | Does script accept `--output-dir`? |
| `supports_artifacts_to_keep` | `True/False` | Does script accept `--artifacts-to-keep`? |
| `uses_argv_kwarg` | `True/False` | Is signature `run(*, argv=...)` or `run(argv)`? |
| `custom_args` | `None` or `[...]` | Any non-standard args needed |

### 6.2 Recommended ScriptConfig

```python
ScriptConfig(
    name="<script_name>",
    path="<relative_path>",
    supports_output_dir=<True/False>,  # <rationale>
    supports_artifacts_to_keep=<True/False>,  # <rationale>
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

> **⚠️ This section is the FINAL GATE. Do not mark complete until ALL items are checked.**
>
> The build.md is NOT done when you fill in the sections. It is done when:
>
> 1. The script has been RUN and outputs verified TRUE
> 2. The Tier-3 YAML exists and is validated
> 3. The roster checkboxes are all checked including DONE
> 4. This document's frontmatter shows `status: complete`

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

- [ ] Section 2.5.1 — QA tests passed (mypy, pytest, CLI execution)
- [ ] Section 2.5.5 — Output truth verified: **SCRIPT WAS ACTUALLY RUN**
- [ ] Section 2.5.5 — Every claim in output artifacts verified against ground truth
- [ ] **If any claim was FALSE, it was FIXED before checking this box**

**Tier-3 & DB Integration:**

- [ ] Section 2.6 — Tier-3 YAML created/updated and validated
- [ ] Section 2.7 — DB Integration markers present at all write points

**Orchestrator Readiness:**

- [ ] Section 6.3 — All orchestration readiness checks pass

### 7.2 Tier-2 Roster Update

> **After completing Section 7.1, update the parent Tier-2 roster document.**

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
- [x] H. Orchestrator integration — ScriptConfig documented (Section 6.2)
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
| HOP bundle compliance | ✅ | Section 2.4.2 all checked |
| Output truth verified | ✅ | Section 2.5.5 — all claims TRUE |
| Tier-3 YAML | ✅ | `<tier3_yaml_path>` |
| DB Integration ready | ✅ | Markers at L<xxx>, L<yyy>, L<zzz> |
| Orchestrator ready | ✅ | Section 6.3 all checked |
| Roster updated | ✅ | Workstreams A-H + DONE checked |

**Next step:** If this script needs orchestrator wiring, proceed to Phase 4B using
`tier2_promotion_template.md`.

---

## 8. Template Variables

Replace these placeholders when using this template:

| Variable | Description |
|----------|-------------|
| `<SCRIPT_NAME>` | Script filename (e.g., `aggregate_reports.py`) |
| `<SCRIPT_PATH>` | Full path (e.g., `.repo_studios/scripts/aggregators/aggregate_reports.py`) |
| `<SCRIPT_DIR>` | Script directory (e.g., `.repo_studios/scripts/aggregators`) |
| `<RECORD_ID>` | ASR record ID (e.g., `ASR-008`) |
| `<YYYY-MM-DD>` | ISO date |
| `<LINE_COUNT>` | Script line count |
| `<TARGET_STAGE>` | Destination stage (e.g., `Stage 4.2`) |
| `<TOPIC>` | Topic slug (e.g., `report_aggregation`) |

---

## 9. Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.1.0 | 2026-01-28 | Enhanced Section 7 with complete conclusion workflow (truth verification, roster update, finalization steps) |
| 2.0.0 | 2026-01-26 | Added Universal Law, Compliance Tiers, Tier-3 YAML, DB Integration Preparation, Orchestration Readiness Checklist, ScriptConfig section |
| 1.0.0 | (original) | Initial template with HOP compliance focus |
