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
  - producer
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
| **Tier Class** | Producer |
| **Lines** | <LINE_COUNT> |
| **Record ID** | <RECORD_ID> |
| **Planned Stage** | <TARGET_STAGE> |

### 1.1 Purpose

<Brief description of what this producer generates and why>

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
| <additional flags> | | | |

### 2.2 Entry Points

| Entry | Signature | Returns |
|-------|-----------|---------|
| `main(argv)` | `list[str] \| None` → `int` | Exit code |
| `run(argv)` | `list[str] \| None` → `dict[str, Any]` | Payload dict |

### 2.3 Current Output Contract

**Output root:** `.repo_studios/reports/healthview/producer_reports/<TOPIC>/<YYYYMMDD-HHMM>/`

**Artifacts:**

| Artifact | Format | Description |
|----------|--------|-------------|
| `manifest.json` | JSON | Schema version, status, inputs |
| `summary.md` | Markdown | Human-readable summary |
| `telemetry.json` | JSON | Execution metrics |
| <additional artifacts> | | |

### 2.4 HOP Compliance Assessment

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Base package (manifest/summary/telemetry) | ⚠️/✅ | <evidence> |
| Uses `build_topic_path()` or `create_storage()` | ⚠️/✅ | <evidence> |
| Uses `prune_run_directories()` | ⚠️/✅ | <evidence> |
| No `latest_*` pointer files | ⚠️/✅ | <evidence> |
| `run(argv)` entry point | ⚠️/✅ | <evidence> |
| Directory format `YYYYMMDD-HHMM` | ⚠️/✅ | <evidence> |

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

| Check | Status | Evidence |
|-------|--------|----------|
| DB_INTEGRATION_MARKER present | ⚠️/✅ | Line numbers where markers exist |
| Marker at manifest.json write | ⚠️/✅ | L<xxx> |
| Marker at summary.md write | ⚠️/✅ | L<xxx> |
| Marker at telemetry.json write | ⚠️/✅ | L<xxx> |

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

## 3. Gap Analysis

### 3.1 Required Changes

| Gap | Priority | Effort |
|-----|----------|--------|
| <Gap 1> | High/Med/Low | S/M/L |
| <Gap 2> | High/Med/Low | S/M/L |

### 3.2 Alteration Locations

| Location | Change | Standard |
|----------|--------|----------|
| `<file>#L<start>-L<end>` | <description> | <HOP requirement> |

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
| `<SCRIPT_NAME>` | Script filename (e.g., `validate_inventory.py`) |
| `<SCRIPT_PATH>` | Full path (e.g., `.repo_studios/scripts/producers/validate_inventory.py`) |
| `<RECORD_ID>` | ASR record ID (e.g., `ASR-008`) |
| `<YYYY-MM-DD>` | ISO date |
| `<LINE_COUNT>` | Script line count |
| `<TARGET_STAGE>` | Destination stage (e.g., `Stage 4.2`) |
| `<TOPIC>` | Topic slug (e.g., `inventory_validation`) |
