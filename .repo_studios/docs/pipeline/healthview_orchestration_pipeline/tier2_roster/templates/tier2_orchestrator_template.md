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
version: 1.0.0
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

---

## 1. Script Identity

| Field | Value |
|-------|-------|
| **Name** | `<SCRIPT_NAME>` |
| **Path** | `<SCRIPT_PATH>` |
| **Tier Class** | Orchestrator |
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

| Entry | Signature | Returns |
|-------|-----------|---------|
| `main(argv)` | `list[str] \| None` → `int` | Exit code |
| `run(argv)` | `list[str] \| None` → `dict[str, Any]` | Payload dict with child outcomes |

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

### 2.5 HOP Compliance Assessment

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Base package (manifest/summary/telemetry) | ⚠️/✅ | <evidence> |
| Uses `build_topic_path()` or `create_storage()` | ⚠️/✅ | <evidence> |
| Uses `prune_run_directories()` | ⚠️/✅ | <evidence> |
| No `latest_*` pointer files | ⚠️/✅ | <evidence> |
| `run(argv)` entry point | ⚠️/✅ | <evidence> |
| Directory format `YYYYMMDD-HHMM` | ⚠️/✅ | <evidence> |
| Child script invocation via `run(argv)` | ⚠️/✅ | <evidence> |
| Outcome dataclass pattern | ⚠️/✅ | <evidence> |

---

## 3. Gap Analysis

### 3.1 Required Changes

| Gap | Priority | Effort |
|-----|----------|--------|
| <Gap 1> | High/Med/Low | S/M/L |

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

## 6. Completion

**Phase 4 processing complete (<YYYY-MM-DD>)**

- [ ] Frontmatter updated: `status: archived`
- [ ] Tier-2 roster record updated
- [ ] Working document archived

---

## Template Variables

Replace these placeholders when using this template:

| Variable | Description |
|----------|-------------|
| `<SCRIPT_NAME>` | Script filename |
| `<SCRIPT_PATH>` | Full path |
| `<RECORD_ID>` | ASR record ID |
| `<YYYY-MM-DD>` | ISO date |
| `<LINE_COUNT>` | Script line count |
| `<STAGE_ID>` | Stage this orchestrator manages |
| `<TOPIC>` | Topic slug |
