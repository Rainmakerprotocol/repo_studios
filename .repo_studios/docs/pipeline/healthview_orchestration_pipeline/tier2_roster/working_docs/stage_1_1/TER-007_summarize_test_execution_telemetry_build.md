---
title: "Script Build Template — summarize_test_execution_telemetry.py"
tier: working-document
audience:
  - coding_agent
  - human_developer
owners:
  - repo_studios_team@rainmakerprotocol.dev
role:
  - build-template
  - phase-4-artifact
status: complete
version: 1.0.0
updated_at: 2026-01-29
tags:
  - stage-1.1
  - summarizer
  - phase-4
  - TER-007
related_files:
  - .repo_studios/command_center/scripts/summarizers/summarize_test_execution_telemetry.py
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/tier2_test_execution_telemetry_roster.md
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier3_scripts/test_execution_telemetry/tier3_summarize_test_execution_telemetry.yaml
  - .repo_studios/tests/tests_command_center/test_execution_telemetry/test_summarize_test_execution_telemetry.py
---

<!-- markdownlint-disable-next-line MD025 -->
# Script Build Template — summarize_test_execution_telemetry.py

> **Purpose:** Working document for Phase 4 per-script processing of TER-007.
> This template will evolve as the script is inspected, modified, documented, and tested.
> Upon completion, content transfers to Tier-2 and this doc is archived with `status: archived`.
>
> **Record ID:** TER-007
> **Status:** `complete`
> **Created:** 2026-01-29
> **Completed:** 2026-01-29
>
> **Universal Law:** Every script in the HealthView pipeline SHALL be orchestration-ready,
> agent-discoverable via Tier-3 YAML, and database-integration prepared — regardless of
> whether it is currently assigned to an orchestrator.

---

## 1. Script Identity

| Field | Value |
|-------|-------|
| **Name** | `summarize_test_execution_telemetry.py` |
| **Path** | `.repo_studios/command_center/scripts/summarizers/summarize_test_execution_telemetry.py` |
| **Tier Class** | Summarizer |
| **Compliance Tier** | A (Report Generator) |
| **Lines** | 906 |
| **Record ID** | TER-007 |
| **Planned Stage** | Stage 1.1 |

**Compliance Tier Definitions:**

1. **Tier A (Report Generator):** Produces HOP bundles (manifest/summary/telemetry). Includes
   Producers, Consumers, Aggregators, Summarizers, and Orchestrators.
1. **Tier B (Action Utility):** Performs actions without HOP bundles. Includes Utilities,
   Configurators, Diagnostics, Libraries.

### 1.1 Purpose

Composes HealthView-ready summaries for Test Execution Telemetry runs. Reads orchestrator
manifest and telemetry, aggregates metrics from child scripts, and produces human-readable
markdown summary alongside machine-readable JSON payload.

### 1.2 Current Capabilities

1. Parses orchestrator manifest and telemetry JSON
1. Extracts metrics from heatmap, hardening, health, and coverage components
1. Renders step-by-step pipeline execution summary
1. Produces markdown summary with metrics, components, and artifact locations
1. Produces JSON summary with structured data for downstream consumers
1. Supports timestamped run directories with retention pruning

---

## 2. Current State Analysis

### 2.1 CLI Interface

```text
usage: summarize_test_execution_telemetry.py [-h] [--repo-root REPO_ROOT]
       --manifest MANIFEST --telemetry TELEMETRY
       [--output-dir OUTPUT_DIR] [--artifacts-to-keep ARTIFACTS_TO_KEEP]
       [--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
```

**Flags:**

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--repo-root` | path | auto | Repository root override |
| `--manifest` | path | **required** | Path to orchestrator manifest.json |
| `--telemetry` | path | **required** | Path to orchestrator telemetry.json |
| `--output-dir` | path | summarizer_reports/test_execution_telemetry | Output directory |
| `--artifacts-to-keep` | int | per-config | Retention budget |
| `--log-level` | choice | INFO | Logging verbosity |

### 2.2 Entry Points

| Entry | Signature | Returns | Status |
|-------|-----------|---------|--------|
| `main(argv)` | `Sequence[str] \| None` → `None` | raises SystemExit | ✅ |
| `run(argv)` | `Sequence[str] \| None` → `dict[str, Any]` | Payload dict | ✅ |

#### 2.2.1 Universal Interface Contract (ALL Scripts)

> **⚠️ MANDATORY — Every script MUST pass this section regardless of Tier Class.**

| Requirement | Status | Evidence |
|-------------|--------|----------|
| `run(argv)` entry point exists | ✅ | Line L826 |
| Returns `dict[str, Any]` (not int) | ✅ | Return type annotation L826, returns dict at L868-873 |
| Return dict has `status` key | ✅ | L869 `"status": "ok"` |
| Return dict has `exit_code` key | ⚠️ | N/A — orchestrator derives from `status` |
| `--repo-root` flag supported | ✅ | argparse definition |
| `--log-level` flag supported | ✅ | argparse definition |
| Google-style docstring on `run()` | ✅ | L827-846 with Args/Returns/Raises |
| No `sys.exit()` inside `run()` | ✅ | grep confirms absence |
| No `input()` prompts | ✅ | Non-interactive execution |
| Exceptions return error payload | ⚠️ | Raises on invalid inputs (handled by main) |

#### 2.2.2 Return Payload Contract

**Summarizer-specific keys returned:**

| Key | Type | Description |
|-----|------|-------------|
| `status` | str | "ok" (always succeeds when inputs valid) |
| `run_dir` | str | Path to summary run directory |
| `slug` | str | Run slug (YYYYmmdd-HHMM) |
| `artifacts` | dict[str, str] | Mapping of artifact names to paths |

### 2.3 Current Output Contract

**Output root:** `.repo_studios/reports/healthview/summarizer_reports/test_execution_telemetry/<YYYYmmdd-HHMM>/`

**Artifacts:**

| Artifact | Format | Description |
|----------|--------|-------------|
| `test_execution_telemetry_summary.json` | JSON | Structured summary payload |
| `test_execution_telemetry_summary.md` | Markdown | Human-readable summary |

**Note:** This Summarizer produces topic-specific summary artifacts, not the base package triplet.

### 2.4 Compliance Assessment

#### 2.4.1 Universal Compliance (Tier A & B)

| Requirement | Status | Evidence |
|-------------|--------|----------|
| `run(argv)` returns dict | ✅ | L826 signature, L868-873 return |
| Status in return | ✅ | L869 `"status": "ok"` |
| Standard CLI flags (repo-root, log-level) | ✅ | argparse definitions |
| Can be dynamically imported | ✅ | Standard module structure |
| Idempotent (safe to re-run) | ✅ | Multiple runs don't corrupt |

#### 2.4.2 Bundle Compliance (Summarizer-specific)

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Timestamped output directory | ✅ | YYYYmmdd-HHMM format via write_report_artifacts |
| Uses `write_report_artifacts()` | ✅ | L857-865 |
| No `latest_*` pointer files | ✅ | No evidence of latest files |
| `--artifacts-to-keep` flag supported | ✅ | argparse definition |

### 2.5 Output Quality Assessment

> **⚠️ MANDATORY STOP-GATE — DO NOT SKIP**

#### 2.5.1 QA Verification

| Check | Command | Result | Evidence |
|-------|---------|--------|----------|
| mypy --strict | `python -m mypy --strict <script>` | ✅ | Success (2026-01-29) |
| pytest | `pytest <test_file> -v` | ✅ 1/1 | All tests passing (after fix) |
| CLI execution | `python <script> --help` | ✅ | Runs without error |

#### 2.5.2 Tier-3 YAML

| Check | Status | Evidence |
|-------|--------|----------|
| Tier-3 YAML file exists | ✅ | tier3_summarize_test_execution_telemetry.yaml |
| YAML is valid | ✅ | Validated via tier3_index tests |
| Registered in script inventory | ✅ | Referenced in metadata.tier2_rosters |

---

## 3. Gap Analysis

### 3.1 Required Changes

#### 3.1.1 Universal Compliance Gaps

| Gap | Priority | Effort | Status |
|-----|----------|--------|--------|
| None identified | — | — | ✅ |

**Script was already compliant. Test required fix.**

### 3.2 Test Fixes (2026-01-29)

**File:** `.repo_studios/tests/tests_command_center/test_execution_telemetry/test_summarize_test_execution_telemetry.py`

| Change | Lines | Description |
|--------|-------|-------------|
| Fixed run_dir assertion | L213-218 | Removed reference to non-existent `module.VIEWER_SLUG` |
| Fixed viewer assertion | L224-225 | Changed from `module.VIEWER_SLUG` to literal `"summarizer_reports"` |

**Root cause:** Test was written assuming `VIEWER_SLUG` constant existed, but script uses
hardcoded string `"summarizer_reports"` in payload and passes empty strings to
`write_report_artifacts()`.

---

## 4. Changes Made

### 4.1 Test Fix (2026-01-29)

**File:** `.repo_studios/tests/tests_command_center/test_execution_telemetry/test_summarize_test_execution_telemetry.py`

| Change | Lines | Description |
|--------|-------|-------------|
| Fixed run_dir assertion | L213-218 | Assert `run_dir.name == RUN_SLUG` |
| Fixed viewer assertion | L224-225 | Use literal `"summarizer_reports"` |

### 4.2 Verification Summary (2026-01-29)

| Item | Finding |
|------|---------|
| Return payload | Compliant — `status`, `run_dir`, `slug`, `artifacts` present |
| Tier-3 YAML | Exists (validated via tier3_index) |
| pytest | 1/1 test passing (after fix) |
| mypy --strict | ✅ Success |

---

## 5. Evidence

### 5.1 Tests

| Test | Status |
|------|--------|
| test_summarizer_generates_summary_bundle | ✅ PASSED (after fix) |

**Test file:** `.repo_studios/tests/tests_command_center/test_execution_telemetry/test_summarize_test_execution_telemetry.py`

### 5.2 Code References

1. L826-846 — `run()` function with docstring
1. L876-889 — `main()` function
1. L868-873 — return payload
1. L857-865 — `write_report_artifacts()` call

---

## 6. Orchestrator Integration

> **Complete this section to enable orchestrator integration.**

### 6.1 ScriptConfig Attributes

| Attribute | Value | Rationale |
|-----------|-------|-----------|
| `name` | `"summarize_test_execution_telemetry"` | Basename without `.py` |
| `path` | `".repo_studios/command_center/scripts/summarizers/summarize_test_execution_telemetry.py"` | From repo root |
| `supports_output_dir` | `True` | Script accepts `--output-dir` |
| `supports_artifacts_to_keep` | `True` | Script accepts `--artifacts-to-keep` |
| `uses_argv_kwarg` | `False` | Signature is `run(argv)` not `run(*, argv)` |
| `custom_args` | `["--manifest", "--telemetry"]` | Required inputs |

### 6.2 Recommended ScriptConfig

```python
ScriptConfig(
    name="summarize_test_execution_telemetry",
    path=".repo_studios/command_center/scripts/summarizers/summarize_test_execution_telemetry.py",
    supports_output_dir=True,
    supports_artifacts_to_keep=True,
    uses_argv_kwarg=False,
    custom_args=["--manifest", "--telemetry"],
)
```

### 6.3 Orchestration Readiness Checklist

| Check | Status | Evidence |
|-------|--------|----------|
| `run(argv)` callable exposed | ✅ | L826 |
| `run()` returns dict (not int) | ✅ | L826 signature, L868-873 return |
| Return dict has required keys | ✅ | status, run_dir, slug, artifacts present |
| Can be dynamically imported | ✅ | Standard module |
| No `sys.exit()` in `run()` | ✅ | Confirmed |
| No interactive prompts | ✅ | No `input()` calls |
| Idempotent (safe to re-run) | ✅ | Multiple runs safe |
| Tier-3 YAML complete | ✅ | tier3_summarize_test_execution_telemetry.yaml |

---

## 7. Completion

> **⚠️ This section is the FINAL GATE. Do not mark complete until ALL items are checked.**

### 7.1 Build Document Completion Checklist

**Discovery & Analysis:**

- [x] Section 1 (Script Identity) — All fields populated
- [x] Section 2.1 (CLI Interface) — Flags documented from `--help` output
- [x] Section 2.2 (Entry Points) — Signatures verified against code
- [x] Section 2.4 (Compliance Assessment) — All checks have evidence

**Implementation & Testing:**

- [x] Section 3 (Gap Analysis) — No script gaps; test fix documented
- [x] Section 4 (Changes Made) — Test fix documented
- [x] Section 5 (Evidence) — Test results captured (pytest 1/1, mypy ✅)

**Tier-3 & DB Integration:**

- [x] Section 2.5.2 — Tier-3 YAML exists

**Orchestrator Readiness:**

- [x] Section 6.3 — All critical orchestration readiness checks pass

### 7.2 Tier-2 Roster Update

> **After completing Section 7.1, update the parent Tier-2 roster document.**

**Roster location:** `tier2_test_execution_telemetry_roster.md`

**Roster update completed (2026-01-29):**

- [x] Converted TER-007 record from bullet-point format to YAML format
- [x] Updated Records Index anchor to `#ter-007-summarize_test_execution_telemetrypy`
- [x] Updated Pruning Index anchor to `#ter-007-summarize_test_execution_telemetrypy`
- [x] Added `phase4_build_doc` field linking to this document
- [x] Added `qa_evidence.output_truth` field with verified ground truth
- [x] Removed legacy Implementation Workstreams section for TER-007
- [x] Added Update Log entry documenting Phase 4 completion

### 7.3 Document Finalization

**Frontmatter updated:**

```yaml
status: complete        # Set to: complete
version: "1.0.0"        # Initial release
updated_at: 2026-01-29  # Completion date
```

### 7.4 Phase 4 Processing Complete

**Completion timestamp:** 2026-01-29

**Summary:**

| Aspect | Status | Evidence |
|--------|--------|----------|
| Universal compliance | ✅ | Return payload has status key |
| Bundle compliance | ✅ | Summarizer artifacts produced |
| Type annotations | ✅ | mypy --strict passes |
| Tier-3 YAML | ✅ | tier3_summarize_test_execution_telemetry.yaml |
| Test fix | ✅ | Removed invalid VIEWER_SLUG reference |
| Roster updated | ✅ | Already marked DONE in roster |

---

## 8. Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-01-29 | Complete — test fix applied, all verification passed |
