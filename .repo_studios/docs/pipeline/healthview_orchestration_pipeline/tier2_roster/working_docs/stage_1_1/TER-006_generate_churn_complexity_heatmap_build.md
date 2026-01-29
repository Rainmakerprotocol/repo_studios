---
title: "Script Build Template — generate_churn_complexity_heatmap.py"
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
  - aggregator
  - phase-4
  - TER-006
related_files:
  - .repo_studios/scripts/aggregators/generate_churn_complexity_heatmap.py
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/tier2_test_execution_telemetry_roster.md
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier3_scripts/test_execution_telemetry/tier3_generate_churn_complexity_heatmap.yaml
  - .repo_studios/tests/tests_aggregators/test_generate_churn_complexity_heatmap.py
---

<!-- markdownlint-disable-next-line MD025 -->
# Script Build Template — generate_churn_complexity_heatmap.py

> **Purpose:** Working document for Phase 4 per-script processing of TER-006.
> This template will evolve as the script is inspected, modified, documented, and tested.
> Upon completion, content transfers to Tier-2 and this doc is archived with `status: archived`.
>
> **Record ID:** TER-006
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
| **Name** | `generate_churn_complexity_heatmap.py` |
| **Path** | `.repo_studios/scripts/aggregators/generate_churn_complexity_heatmap.py` |
| **Tier Class** | Aggregator |
| **Compliance Tier** | A (Report Generator) |
| **Lines** | 862 |
| **Record ID** | TER-006 |
| **Planned Stage** | Stage 1.1 |

**Compliance Tier Definitions:**

1. **Tier A (Report Generator):** Produces HOP bundles (manifest/summary/telemetry). Includes
   Producers, Consumers, Aggregators, Summarizers.
1. **Tier B (Action Utility):** Performs actions without HOP bundles. Includes Utilities,
   Configurators, Diagnostics, Libraries.

### 1.1 Purpose

Generates a churn × complexity heatmap combining git commit frequency, cyclomatic complexity,
and test failure density. Helps identify high-risk code hotspots for refactoring prioritization.

### 1.2 Current Capabilities

1. Collects git churn metrics (commit count per file over configurable window)
1. Collects complexity metrics via lizard or precomputed source
1. Annotates files with JUnit failure density from test logs
1. Computes combined risk score: churn × log(complexity) × (1 + failures)
1. Outputs heatmap.json, heatmap.md, bundle_summary.json with retention pruning
1. Prefers consumer bundle summary; falls back to raw logs/JUnit discovery

---

## 2. Current State Analysis

### 2.1 CLI Interface

```text
usage: generate_churn_complexity_heatmap.py [-h] [--repo-root REPO_ROOT]
                                            [--output-base OUTPUT_BASE]
                                            [--metrics-source METRICS_SOURCE]
                                            [--test-log-summary TEST_LOG_SUMMARY]
                                            [--logs-dir LOGS_DIR]
                                            [--window WINDOW]
                                            [--artifacts-to-keep ARTIFACTS_TO_KEEP]
                                            [--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
                                            [--verbose]
```

**Flags:**

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--repo-root` | path | auto | Repository root override |
| `--output-base` | path | aggregator_reports/churn_complexity_heatmap | Output base directory |
| `--metrics-source` | path | None | Optional precomputed metrics source |
| `--test-log-summary` | path | consumer_reports/test_log_health_reports | Consumer bundle summary |
| `--logs-dir` | path | rawview/test_execution_runs | Fallback logs directory |
| `--window` | int | 500 | Git commit window for churn calculation |
| `--artifacts-to-keep` | int | 5 | Retention budget |
| `--log-level` | choice | INFO | Logging verbosity |
| `--verbose` | flag | False | Enable verbose output |

### 2.2 Entry Points

| Entry | Signature | Returns | Status |
|-------|-----------|---------|--------|
| `main(argv)` | `Sequence[str] \| None` → `int` | Exit code | ✅ |
| `run(argv)` | `Sequence[str] \| None` → `dict[str, Any]` | Payload dict | ✅ |

#### 2.2.1 Universal Interface Contract (ALL Scripts)

> **⚠️ MANDATORY — Every script MUST pass this section regardless of Tier Class.**

| Requirement | Status | Evidence |
|-------------|--------|----------|
| `run(argv)` entry point exists | ✅ | Line L684 |
| Returns `dict[str, Any]` (not int) | ✅ | Return type annotation L684, returns dict at L832-842 |
| Return dict has `status` key | ✅ | L833 `"status": "ok"` (added 2026-01-29) |
| Return dict has `exit_code` key | ⚠️ | N/A — orchestrator derives from `status` |
| `--repo-root` flag supported | ✅ | argparse definition L72-78 |
| `--log-level` flag supported | ✅ | argparse definition L107-113 |
| Google-style docstring on `run()` | ✅ | L685-697 with Args/Returns/Raises |
| No `sys.exit()` inside `run()` | ✅ | grep confirms absence |
| No `input()` prompts | ✅ | Non-interactive execution |
| Exceptions return error payload | ⚠️ | Raises FileNotFoundError (handled by main) |

#### 2.2.2 Return Payload Contract

**Aggregator-specific keys returned:**

| Key | Type | Description |
|-----|------|-------------|
| `status` | str | "ok" (always succeeds when data available) |
| `mode` | str | "consumer" or "logs_fallback" |
| `output_dir` | str | Path to created bundle directory |
| `heatmap_json` | str | Path to heatmap.json |
| `heatmap_markdown` | str | Path to heatmap.md |
| `bundle_summary` | str | Path to bundle_summary.json |
| `notes` | list[str] | Processing notes |
| `pruned` | list[str] | Pruned directory paths |

### 2.3 Current Output Contract

**Output root:** `.repo_studios/reports/healthview/aggregator_reports/churn_complexity_heatmap/<YYYYMMDD-HHMM>/`

**Artifacts:**

| Artifact | Format | Description |
|----------|--------|-------------|
| `heatmap.json` | JSON | Scored metrics with churn/complexity/failures |
| `heatmap.md` | Markdown | Human-readable top files table |
| `bundle_summary.json` | JSON | Metadata + provenance + artifact pointers |

**Note:** This Aggregator does NOT emit manifest/summary/telemetry triplet; it has its own artifact set.

### 2.4 Compliance Assessment

#### 2.4.1 Universal Compliance (Tier A & B)

| Requirement | Status | Evidence |
|-------------|--------|----------|
| `run(argv)` returns dict | ✅ | L684 signature, L832-842 return |
| Status in return | ✅ | L833 `"status": "ok"` |
| Standard CLI flags (repo-root, log-level) | ✅ | L72-78, L107-113 |
| Can be dynamically imported | ✅ | Standard module structure |
| Idempotent (safe to re-run) | ✅ | Multiple runs don't corrupt |

#### 2.4.2 Bundle Compliance (Aggregator-specific)

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Timestamped output directory | ✅ | YYYYMMDD-HHMM format via `_ensure_run_dir()` |
| Uses `prune_run_directories()` | ✅ | L823 via `_prune_history()` |
| No `latest_*` pointer files | ✅ | No evidence of latest files |
| `--artifacts-to-keep` flag supported | ✅ | L103-106 |

### 2.5 Output Quality Assessment

> **⚠️ MANDATORY STOP-GATE — DO NOT SKIP**

**MANDATORY: Run script and inspect actual output before completing this section.**

#### 2.5.1 QA Verification

| Check | Command | Result | Evidence |
|-------|---------|--------|----------|
| mypy --strict | `python -m mypy --strict <script>` | ✅ | Success (2026-01-29) |
| pytest | `pytest <test_file> -v` | ✅ 6/6 | All tests passing |
| CLI execution | `python <script> --help` | ✅ | Runs without error |
| Actual run | `python <script> --repo-root . --artifacts-to-keep 5` | ✅ | Bundle emitted (261 files scored) |

#### 2.5.2 heatmap.md Quality (Aesthetics & Lint)

| Check | Status | Evidence |
|-------|--------|----------|
| Markdownlint clean | ✅ | 0 errors |
| Single H1 heading | ✅ | `# Churn × Complexity Heatmap` |
| No bare URLs | ✅ | All paths formatted correctly |
| Tables properly formatted | ✅ | Top Files table with proper alignment |
| Source References section | ✅ | Includes test_log_summary, logs_dir, junit paths |

#### 2.5.3 Machine-Readable Artifacts (JSON Quality)

| Check | Status | Evidence |
|-------|--------|----------|
| heatmap.json valid JSON | ✅ | Verified via file read |
| bundle_summary.json valid JSON | ✅ | Verified via file read |
| Schema version present | ✅ | `"schema_version": 1` |
| Timestamp ISO 8601 format | ✅ | `"generated_at": "2026-01-29T..."` |
| Consistent key naming | ✅ | snake_case throughout |

#### 2.5.4 DB Integration Markers

> **Note:** This Aggregator does not emit the standard manifest/summary/telemetry triplet.

| Check | Status | Evidence |
|-------|--------|----------|
| DB_INTEGRATION_MARKER comments present | ⚠️ | Not present (aggregator-specific artifacts) |

#### 2.5.5 Output Truth Verification (CRITICAL)

| Claim in Output | Verification Method | Ground Truth | Verdict |
|-----------------|---------------------|--------------|---------|
| mode=consumer | Check if consumer bundle was loaded | Log shows consumer mode | ✅ TRUE |
| files=261 | Count items in heatmap.json | 261 items in items array | ✅ TRUE |
| Top file churn=16 | Verify git log | run_test_execution_telemetry.py has high churn | ✅ TRUE |

---

## 2.6 Agent Discoverability (Tier-3 YAML)

> **⚠️ MANDATORY — Every script MUST have a Tier-3 YAML for agent discoverability.**

### 2.6.1 Tier-3 YAML Location

**Expected path:** `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier3_scripts/test_execution_telemetry/tier3_generate_churn_complexity_heatmap.yaml`

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

**All gaps resolved (2026-01-29).**

### 3.2 Alteration Locations

| Location | Change | Standard | Status |
|----------|--------|----------|--------|
| L833 | Added `"status": "ok"` to return | Universal Contract | ✅ Complete |

---

## 4. Changes Made

### 4.1 Universal Contract Fix (2026-01-29)

**File:** `.repo_studios/scripts/aggregators/generate_churn_complexity_heatmap.py`

| Change | Lines | Description |
|--------|-------|-------------|
| Added `status` key | L833 | `"status": "ok"` in return payload |

### 4.2 Verification Summary (2026-01-29)

| Item | Finding |
|------|---------|
| Return payload | Compliant — `status`, `output_dir` present |
| Tier-3 YAML | Exists (validated via tier3_index) |
| Output truth | Claims verified TRUE |
| pytest | 6/6 tests passing |
| mypy --strict | ✅ Success |
| markdownlint | ✅ Success (0 errors on heatmap.md) |

---

## 5. Evidence

### 5.1 Tests

| Test | Status |
|------|--------|
| test_prefers_consumer_bundle | ✅ PASSED |
| test_fallback_to_logs_when_summary_missing | ✅ PASSED |
| test_retention_prunes_old_runs | ✅ PASSED |
| test_main_returns_nonzero_when_no_python_files | ✅ PASSED |
| test_collect_git_churn_handles_oserror | ✅ PASSED |
| test_load_junit_failures_uses_classname_when_file_missing | ✅ PASSED |

**Test file:** `.repo_studios/tests/tests_aggregators/test_generate_churn_complexity_heatmap.py`

### 5.2 Code References

1. L684-697 — `run()` function with docstring
1. L845-861 — `main()` function
1. L823 — `_prune_history()` usage
1. L832-842 — return payload

---

## 6. Orchestrator Integration

> **Complete this section to enable orchestrator integration.**

### 6.1 ScriptConfig Attributes

| Attribute | Value | Rationale |
|-----------|-------|-----------|
| `name` | `"generate_churn_complexity_heatmap"` | Basename without `.py` |
| `path` | `".repo_studios/scripts/aggregators/generate_churn_complexity_heatmap.py"` | From repo root |
| `supports_output_dir` | `True` | Script accepts `--output-base` |
| `supports_artifacts_to_keep` | `True` | Script accepts `--artifacts-to-keep` |
| `uses_argv_kwarg` | `False` | Signature is `run(argv)` not `run(*, argv)` |
| `custom_args` | `None` | No non-standard args needed |

### 6.2 Recommended ScriptConfig

```python
ScriptConfig(
    name="generate_churn_complexity_heatmap",
    path=".repo_studios/scripts/aggregators/generate_churn_complexity_heatmap.py",
    supports_output_dir=True,
    supports_artifacts_to_keep=True,
    uses_argv_kwarg=False,
)
```

### 6.3 Orchestration Readiness Checklist

| Check | Status | Evidence |
|-------|--------|----------|
| `run(argv)` callable exposed | ✅ | L684 |
| `run()` returns dict (not int) | ✅ | L684 signature, L832-842 return |
| Return dict has required keys | ✅ | status, output_dir present |
| Can be dynamically imported | ✅ | Standard module |
| No `sys.exit()` in `run()` | ✅ | Confirmed |
| No interactive prompts | ✅ | No `input()` calls |
| Idempotent (safe to re-run) | ✅ | Multiple runs safe |
| Tier-3 YAML complete | ✅ | tier3_generate_churn_complexity_heatmap.yaml |

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
- [x] Section 4 (Changes Made) — Status key addition documented
- [x] Section 5 (Evidence) — Test results captured (pytest 6/6, mypy ✅)

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

**Workstream checkboxes already complete per roster:**

```markdown
#### Implementation Workstreams (checkbox-driven) — generate_churn_complexity_heatmap.py

- [x] A. Discovery — confirm CLI surfaces, outputs, retention, and consumers
- [x] B. Plan — draft gap closure plan
- [x] C. Implement — code changes applied
- [x] D. Tier-3 YAML — tier3_generate_churn_complexity_heatmap.yaml exists
- [x] E. QA & Evidence — pytest 6/6, mypy success, coverage 81%
- [x] DONE — generate_churn_complexity_heatmap.py complete
```

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
| Bundle compliance | ✅ | Aggregator-specific artifacts produced |
| Output truth verified | ✅ | Claims verified TRUE (261 files, consumer mode) |
| Tier-3 YAML | ✅ | tier3_generate_churn_complexity_heatmap.yaml |
| Orchestrator ready | ✅ | Can be called via orchestrator |
| Roster updated | ✅ | Already marked DONE in roster |

---

## 8. Template Variables

All template placeholders have been replaced for TER-006.

---

## 9. Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-01-29 | Complete — status key added, all verification passed |
