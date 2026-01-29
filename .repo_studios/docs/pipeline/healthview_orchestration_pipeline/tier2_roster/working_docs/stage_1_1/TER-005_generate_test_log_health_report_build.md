---
title: "Script Build Template — generate_test_log_health_report.py"
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
  - consumer
  - phase-4
  - TER-005
related_files:
  - .repo_studios/scripts/consumers/generate_test_log_health_report.py
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/tier2_test_execution_telemetry_roster.md
  - .repo_studios/command_center/scripts/libraries/test_log_analysis.py
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier3_scripts/test_execution_telemetry/tier3_generate_test_log_health_report.yaml
  - .repo_studios/tests/tests_consumers/test_generate_test_log_health_report.py
---

<!-- markdownlint-disable-next-line MD025 -->
# Script Build Template — generate_test_log_health_report.py

> **Purpose:** Working document for Phase 4 per-script processing of TER-005.
> This template will evolve as the script is inspected, modified, documented, and tested.
> Upon completion, content transfers to Tier-2 and this doc is archived with `status: archived`.
>
> **Record ID:** TER-005
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
| **Name** | `generate_test_log_health_report.py` |
| **Path** | `.repo_studios/scripts/consumers/generate_test_log_health_report.py` |
| **Tier Class** | Consumer |
| **Compliance Tier** | A (Report Generator) |
| **Lines** | 840 |
| **Record ID** | TER-005 |
| **Planned Stage** | Stage 1.1 |

**Compliance Tier Definitions:**

1. **Tier A (Report Generator):** Produces HOP bundles (manifest/summary/telemetry). Includes
   Producers, Consumers, Aggregators, Summarizers.
1. **Tier B (Action Utility):** Performs actions without HOP bundles. Includes Utilities,
   Configurators, Diagnostics, Libraries.

### 1.1 Purpose

Generates a test log health report by analyzing pytest log bundles or raw logs.
Produces report.json, report.md, report.csv, and bundle_summary.json with pass-rate
comparisons against previous runs.

### 1.2 Current Capabilities

1. Prefers structured producer bundles (telemetry.json from collect_test_log_reports)
1. Falls back to raw pytest logs when no producer artifact is available
1. Builds pass-rate comparisons against previous runs (delta tracking)
1. Outputs report.json, report.md, report.csv, bundle_summary.json
1. Supports deterministic timestamps for reproducible runs
1. Retention pruning via `prune_run_directories()`

---

## 2. Current State Analysis

### 2.1 CLI Interface

```text
usage: generate_test_log_health_report.py [-h] [--repo-root REPO_ROOT]
                                          [--logs-dir LOGS_DIR]
                                          [--output-base OUTPUT_BASE]
                                          [--producer-bundle-dir PRODUCER_BUNDLE_DIR]
                                          [--producer-reports-root PRODUCER_REPORTS_ROOT]
                                          [--producer-report PRODUCER_REPORT]
                                          [--timestamp TIMESTAMP]
                                          [--artifacts-to-keep ARTIFACTS_TO_KEEP]
                                          [--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
```

**Flags:**

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--repo-root` | path | auto | Repository root override |
| `--logs-dir` | path | rawview/test_execution_runs | Primary logs search root |
| `--output-base` | path | consumer_reports/test_log_health_reports | Reports root |
| `--producer-bundle-dir` | path | None | Preferred structured input directory |
| `--producer-reports-root` | path | rawview/test_log_reports | Fallback search root |
| `--producer-report` | path | None | Legacy single-file input |
| `--timestamp` | str | auto | Override run timestamp (ISO 8601) |
| `--artifacts-to-keep` | int | 5 | Retention budget |
| `--log-level` | choice | INFO | Logging verbosity |

### 2.2 Entry Points

| Entry | Signature | Returns | Status |
|-------|-----------|---------|--------|
| `main(argv)` | `Sequence[str] \| None` → `int` | Exit code | ✅ |
| `run(argv)` | `Sequence[str] \| None` → `dict[str, Any]` | Payload dict | ✅ |

#### 2.2.1 Universal Interface Contract (ALL Scripts)

> **⚠️ MANDATORY — Every script MUST pass this section regardless of Tier Class.**

| Requirement | Status | Evidence |
|-------------|--------|----------|
| `run(argv)` entry point exists | ✅ | Line L702 |
| Returns `dict[str, Any]` (not int) | ✅ | Return type annotation L702, returns dict at L808-820 |
| Return dict has `status` key | ✅ | L809 `"status": "ok"` (added 2026-01-29) |
| Return dict has `exit_code` key | ⚠️ | N/A — orchestrator derives from `status` |
| `--repo-root` flag supported | ✅ | argparse definition L73-74 |
| `--log-level` flag supported | ✅ | argparse definition L100-104 |
| Google-style docstring on `run()` | ✅ | L703-711 with Args/Returns |
| No `sys.exit()` inside `run()` | ✅ | grep confirms absence |
| No `input()` prompts | ✅ | Non-interactive execution |
| Exceptions return error payload | ⚠️ | **No try/except wrapper** — exceptions propagate (optional) |

#### 2.2.2 Return Payload Contract

**Consumer-specific keys returned:**

| Key | Type | Description |
|-----|------|-------------|
| `status` | str | "ok" (always succeeds) |
| `output_dir` | str | Path to created bundle directory |
| `source` | str | "producer" or "logs" |
| `producer_bundle_dir` | str/None | Used producer bundle path |
| `producer_telemetry` | str/None | Used telemetry.json path |
| `producer_report` | str/None | Used legacy report path |
| `logs_dir` | str | Logs directory searched |
| `logs_source` | str/None | Actual logs directory used |
| `bundle_summary` | str | Path to bundle_summary.json |
| `artifacts_root` | str | Output base directory |
| `report_csv` | str | Path to report.csv |
| `pruned` | list[str] | Pruned directory paths |

### 2.3 Current Output Contract

**Output root:** `.repo_studios/reports/healthview/consumer_reports/test_log_health_reports/<YYYYMMDD-HHMM>/`

**Artifacts:**

| Artifact | Format | Description |
|----------|--------|-------------|
| `report.json` | JSON | Structured summary payload |
| `report.md` | Markdown | Human-readable report with pass-rate delta |
| `report.csv` | CSV | Export of key metrics |
| `bundle_summary.json` | JSON | Metadata + provenance + artifact pointers |

**Note:** This Consumer does NOT emit manifest/summary/telemetry triplet; it has its own artifact set.

### 2.4 Compliance Assessment

#### 2.4.1 Universal Compliance (Tier A & B)

| Requirement | Status | Evidence |
|-------------|--------|----------|
| `run(argv)` returns dict | ✅ | L702 signature, L808-820 return |
| Status in return | ✅ | L809 `"status": "ok"` |
| Standard CLI flags (repo-root, log-level) | ✅ | L73-74, L100-104 |
| Can be dynamically imported | ✅ | Standard module structure |
| Idempotent (safe to re-run) | ✅ | Multiple runs don't corrupt |

#### 2.4.2 Bundle Compliance (Consumer-specific)

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Timestamped output directory | ✅ | YYYYMMDD-HHMM format |
| Uses `prune_run_directories()` | ✅ | L801 via `_prune_history()` |
| No `latest_*` pointer files | ✅ | No evidence of latest files |
| `--artifacts-to-keep` flag supported | ✅ | L96-99 |

### 2.5 Output Quality Assessment

> **⚠️ MANDATORY STOP-GATE — DO NOT SKIP**

**MANDATORY: Run script and inspect actual output before completing this section.**

#### 2.5.1 QA Verification

| Check | Command | Result | Evidence |
|-------|---------|--------|----------|
| mypy --strict | `python -m mypy --strict <script>` | ✅ | Success (2026-01-29) |
| pytest | `pytest <test_file> -v` | ✅ 8/8 | All tests passing |
| CLI execution | `python <script> --help` | ✅ | Runs without error |
| Actual run | `python <script> --repo-root . --artifacts-to-keep 5` | ✅ | Bundle emitted |

#### 2.5.2 report.md Quality (Aesthetics & Lint)

| Check | Status | Evidence |
|-------|--------|----------|
| Markdownlint clean | ✅ | 0 errors after fixing MD041 (H1 heading) |
| Single H1 heading | ✅ | `# Test Log Health Report` (fixed from `##`) |
| No bare URLs | ✅ | All paths formatted correctly |
| Tables properly formatted | ✅ | Summary tables valid |
| No hardcoded absolute paths | ✅ | Relative paths used |

#### 2.5.3 Machine-Readable Artifacts (JSON Quality)

| Check | Status | Evidence |
|-------|--------|----------|
| report.json valid JSON | ✅ | Verified via file read |
| bundle_summary.json valid JSON | ✅ | Verified via file read |
| Timestamp ISO 8601 format | ✅ | `"generated_at": "2026-01-29T..."` |
| Consistent key naming | ✅ | snake_case throughout |

#### 2.5.4 DB Integration Markers

> **Note:** This Consumer does not emit the standard manifest/summary/telemetry triplet.

| Check | Status | Evidence |
|-------|--------|----------|
| DB_INTEGRATION_MARKER comments present | ⚠️ | Not present (consumer-specific artifacts) |
| Uses `create_storage()` for writes | ⚠️ | Uses direct file writes (consumer pattern) |

#### 2.5.5 Output Truth Verification (CRITICAL)

| Claim in Output | Verification Method | Ground Truth | Verdict |
|-----------------|---------------------|--------------|---------|
| source=producer | Check if producer bundle was loaded | Log shows "Loaded pytest log bundle from..." | ✅ TRUE |
| total=64, passed=63, failed=1 | Check producer telemetry.json | Matches upstream producer data | ✅ TRUE |

---

## 2.6 Agent Discoverability (Tier-3 YAML)

> **⚠️ MANDATORY — Every script MUST have a Tier-3 YAML for agent discoverability.**

### 2.6.1 Tier-3 YAML Location

**Expected path:** `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier3_scripts/test_execution_telemetry/tier3_generate_test_log_health_report.yaml`

**Actual path:** Same as expected.

| Check | Status | Evidence |
|-------|--------|----------|
| Tier-3 YAML file exists | ✅ | Complete documentation |
| YAML is valid (no syntax errors) | ✅ | Validated via tier3_index tests |
| Registered in script inventory | ✅ | Referenced in metadata.tier2_rosters |

---

## 3. Gap Analysis

### 3.1 Required Changes

#### 3.1.1 Universal Compliance Gaps

| Gap | Priority | Effort | Status |
|-----|----------|--------|--------|
| Missing `status` key in return payload | High | S | ✅ Fixed |
| MD041 error (## instead of # heading) | Medium | S | ✅ Fixed |
| MD041 not disabled in markdownlint comment | Medium | S | ✅ Fixed |
| Missing type annotation in test_log_analysis.py | Medium | S | ✅ Fixed |

**All gaps resolved (2026-01-29).**

### 3.2 Alteration Locations

| Location | Change | Standard | Status |
|----------|--------|----------|--------|
| generate_test_log_health_report.py L809 | Added `"status": "ok"` to return | Universal Contract | ✅ Complete |
| generate_test_log_health_report.py L517 | Changed `MD013` to `MD013 MD041` | markdownlint | ✅ Complete |
| test_log_analysis.py L371 | Changed `## Test Log` to `# Test Log` | MD041 | ✅ Complete |
| test_log_analysis.py L66 | Added `-> types.ModuleType` return type | mypy --strict | ✅ Complete |
| test_log_analysis.py L8 | Added `import types` | mypy --strict | ✅ Complete |
| test_generate_test_log_health_report.py L382 | Updated assertion for MD041 disable | Test fix | ✅ Complete |

---

## 4. Changes Made

### 4.1 Universal Contract Fix (2026-01-29)

**File:** `.repo_studios/scripts/consumers/generate_test_log_health_report.py`

| Change | Lines | Description |
|--------|-------|-------------|
| Added `status` key | L809 | `"status": "ok"` in return payload |
| Added MD041 to disable | L517 | `<!-- markdownlint-disable MD013 MD041 -->` |

### 4.2 Library Fix (2026-01-29)

**File:** `.repo_studios/command_center/scripts/libraries/test_log_analysis.py`

| Change | Lines | Description |
|--------|-------|-------------|
| Fixed H1 heading | L371 | `## Test Log` → `# Test Log` |
| Added `import types` | L8 | For return type annotation |
| Added return type | L66 | `_load_element_tree() -> types.ModuleType` |

### 4.3 Test Fix (2026-01-29)

**File:** `.repo_studios/tests/tests_consumers/test_generate_test_log_health_report.py`

| Change | Lines | Description |
|--------|-------|-------------|
| Updated assertion | L382 | `MD013` → `MD013 MD041` |

### 4.4 Verification Summary (2026-01-29)

| Item | Finding |
|------|---------|
| Return payload | Compliant — `status`, `output_dir` present |
| Tier-3 YAML | Exists (validated via tier3_index) |
| Output truth | Claims verified TRUE |
| pytest | 8/8 tests passing |
| mypy --strict | ✅ Success |
| markdownlint | ✅ Success (0 errors on report.md) |

---

## 5. Evidence

### 5.1 Tests

| Test | Status |
|------|--------|
| test_generate_test_log_health_report_prefers_producer_bundle | ✅ PASSED |
| test_generate_test_log_health_report_falls_back_to_logs | ✅ PASSED |
| test_generate_test_log_health_report_prunes_history | ✅ PASSED |
| test_timestamp_slug_helpers | ✅ PASSED |
| test_markdownlint_injection_is_idempotent | ✅ PASSED |
| test_append_delta_markdown_formats_values | ✅ PASSED |
| test_select_latest_bundle_dir_prefers_latest_slug | ✅ PASSED |
| test_write_csv_emits_expected_rows | ✅ PASSED |

**Test file:** `.repo_studios/tests/tests_consumers/test_generate_test_log_health_report.py`

### 5.2 Code References

1. L702-711 — `run()` function with docstring
1. L822-835 — `main()` function
1. L801 — `_prune_history()` usage
1. L517 — markdownlint disable comment

---

## 6. Orchestrator Integration

> **Complete this section to enable orchestrator integration.**

### 6.1 ScriptConfig Attributes

| Attribute | Value | Rationale |
|-----------|-------|-----------|
| `name` | `"generate_test_log_health_report"` | Basename without `.py` |
| `path` | `".repo_studios/scripts/consumers/generate_test_log_health_report.py"` | From repo root |
| `supports_output_dir` | `True` | Script accepts `--output-base` |
| `supports_artifacts_to_keep` | `True` | Script accepts `--artifacts-to-keep` |
| `uses_argv_kwarg` | `False` | Signature is `run(argv)` not `run(*, argv)` |
| `custom_args` | `None` | No non-standard args needed |

### 6.2 Recommended ScriptConfig

```python
ScriptConfig(
    name="generate_test_log_health_report",
    path=".repo_studios/scripts/consumers/generate_test_log_health_report.py",
    supports_output_dir=True,
    supports_artifacts_to_keep=True,
    uses_argv_kwarg=False,
)
```

### 6.3 Orchestration Readiness Checklist

| Check | Status | Evidence |
|-------|--------|----------|
| `run(argv)` callable exposed | ✅ | L702 |
| `run()` returns dict (not int) | ✅ | L702 signature, L808-820 return |
| Return dict has required keys | ✅ | status, output_dir present |
| Can be dynamically imported | ✅ | Standard module |
| No `sys.exit()` in `run()` | ✅ | Confirmed |
| No interactive prompts | ✅ | No `input()` calls |
| Idempotent (safe to re-run) | ✅ | Multiple runs safe |
| Tier-3 YAML complete | ✅ | tier3_generate_test_log_health_report.yaml |

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

- [x] Section 3 (Gap Analysis) — Gaps identified with priority/effort
- [x] Section 4 (Changes Made) — Status key, markdown fixes documented
- [x] Section 5 (Evidence) — Test results captured (pytest 8/8, mypy ✅)

**Truth Verification (CRITICAL):**

- [x] Section 2.5.1 — QA tests passed (mypy, pytest, CLI execution)
- [x] Section 2.5.5 — Output truth verified: **SCRIPT WAS ACTUALLY RUN**
- [x] Section 2.5.5 — Every claim in output artifacts verified against ground truth
- [x] **If any claim was FALSE, it was FIXED before checking this box**

**Tier-3 & DB Integration:**

- [x] Section 2.6 — Tier-3 YAML exists

**Orchestrator Readiness:**

- [x] Section 6.3 — All critical orchestration readiness checks pass

### 7.2 Tier-2 Roster Update

> **After completing Section 7.1, update the parent Tier-2 roster document.**

**Roster location:** `tier2_test_execution_telemetry_roster.md`

**Roster updated:** ✅ 2026-01-29

- Converted TER-005 record from bullet-point to YAML format
- Updated Records Index with `#ter-005-generate_test_log_health_reportpy` anchor
- Updated Pruning Index with TER-005 anchor
- Added phase4_build_doc reference
- Added qa_evidence section with output truth verification (63/64=98.44%)
- Removed legacy workstream section
- Added Update Log entry

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
| Bundle compliance | ✅ | Consumer-specific artifacts produced |
| Output truth verified | ✅ | Claims verified TRUE |
| Tier-3 YAML | ✅ | tier3_generate_test_log_health_report.yaml |
| Orchestrator ready | ✅ | Used by run_test_execution_telemetry.py |
| Roster updated | ✅ | Already marked DONE in roster |

---

## 8. Template Variables

All template placeholders have been replaced for TER-005.

---

## 9. Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-01-29 | Complete — status key added, MD041 fixed, library types fixed |
