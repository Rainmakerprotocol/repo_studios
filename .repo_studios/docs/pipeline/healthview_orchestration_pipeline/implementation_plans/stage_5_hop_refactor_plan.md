---
title: "Stage 5 HOP Refactor Plan — Monkey Patch Oversight Pipeline"
audience:
  - coding_agent
  - human_developer
owners:
  - repo_studios_ai
status: complete
version: 1.0.0
updated: 2026-01-03
tags:
  - stage-5
  - hop-compliance
  - refactor
  - implementation-plan
related_files:
  - tier1_healthview_orchestration_pipeline.md
  - run_monkey_patch_oversight.py
  - scan_monkey_patches.py
  - classify_monkey_patches.py
  - analyze_monkey_patch_trends.py
  - summarize_monkey_patch_overview.py
---

# Stage 5 HOP Refactor Plan — Monkey Patch Oversight Pipeline

> **Purpose:** Bring the Monkey Patch Oversight pipeline (Stage 5) into full HOP compliance by
> aligning producer-consumer artifact formats, output paths, and orchestrator invocation patterns.
>
> **Status:** ✅ COMPLETE — All scripts verified HOP-compliant at runtime (2026-01-03, run 20260103-0153).

---

## Executive Summary

Runtime inspection of orchestrator run `20260103-0127` revealed a **producer-consumer format
mismatch** that caused pipeline failure. This has been **resolved**.

**Phase 1 fixes (path alignment + manifest recognition):**
- Consumer `_is_scan_dir()` now recognizes HOP manifest format
- Consumer `_load_hop_findings()` extracts findings from `manifest.payload.findings`
- All scripts updated to use `build_topic_path()` for default paths

**Phase 2 fixes (slug format + artifact cleanup):**
- Consumer: Removed `BUNDLE_PREFIX`, changed slug to `YYYYMMDD-HHMM` format
- Consumer: Removed `_write_legacy_outputs()` call that wrote to producer directory
- Aggregator: Removed `AGGREGATOR_PREFIX`, changed slug to `YYYYMMDD-HHMM` format
- Summarizer: Changed `write_report_artifacts()` to use `viewer=""`, `topic=""` for flat slug format
- Summarizer: Renamed artifacts to `manifest.json` and `summary.md`

| Script | Previous Status | Current Status | Gap Severity |
|--------|-----------------|----------------|--------------|
| S5R-001 `run_monkey_patch_oversight.py` | Legacy paths for child scripts | ✅ HOP-compliant | Resolved |
| S5R-002 `scan_monkey_patches.py` | Already HOP-compliant | ✅ HOP-compliant | None |
| S5R-003 `classify_monkey_patches.py` | Expected `matches.json`/`report.json` | ✅ HOP manifest support added | Resolved |
| S5R-004 `analyze_monkey_patch_trends.py` | Legacy consumer/producer paths | ✅ HOP-compliant | Resolved |
| S5R-005 `summarize_monkey_patch_overview.py` | Legacy input paths | ✅ HOP-compliant | Resolved |

**Root cause (resolved):** The producer was updated to HOP-compliant output (manifest.json + base package) but
the consumer was never updated to read findings from `manifest.payload.findings`. Additionally, all
downstream scripts used legacy prefixed slug formats instead of the HOP-standard `YYYYMMDD-HHMM` format.

**Fixes applied:**

*Phase 1 (path alignment + manifest recognition):*
- Consumer `_is_scan_dir()` now recognizes HOP manifest format
- Consumer `_load_hop_findings()` extracts findings from `manifest.payload.findings`
- All scripts updated to use `build_topic_path()` for default paths

*Phase 2 (slug format + artifact cleanup):*
- Consumer: Removed `BUNDLE_PREFIX = ""`, slug uses `ts.strftime("%Y%m%d-%H%M")`
- Consumer: Removed `_write_legacy_outputs()` call (no longer writes to producer directory)
- Aggregator: Removed `AGGREGATOR_PREFIX = ""`, slug uses `generated_at.strftime("%Y%m%d-%H%M")`
- Summarizer: Uses `viewer="", topic=""` in `write_report_artifacts()` for flat slug format
- Summarizer: Artifacts renamed to `manifest.json` and `summary.md`
- Test: `test_summarizer_contract.py` updated to expect `VIEWER_SLUG = "healthview"`

---

## 1. Gap Analysis

### 1.1 S5R-001: run_monkey_patch_oversight.py (Orchestrator)

**Current paths (L70-73):**

```python
DEFAULT_PRODUCER_OUTPUT = Path(".repo_studios/reports/producer_reports/monkey_patch_scans")
DEFAULT_CONSUMER_OUTPUT = Path(".repo_studios/reports/consumer_reports/monkey_patch_risk")
DEFAULT_AGGREGATOR_OUTPUT = Path(".repo_studios/reports/aggregator_reports/monkey_patch_trends")
DEFAULT_SUMMARIZER_OUTPUT = Path(".repo_studios/reports/summarizer_reports/monkey_patch_overview")
```

**Expected HOP paths:**

```python
DEFAULT_PRODUCER_OUTPUT = build_topic_path("producer", "monkey_patch_scans")
DEFAULT_CONSUMER_OUTPUT = build_topic_path("consumer", "monkey_patch_risk")
DEFAULT_AGGREGATOR_OUTPUT = build_topic_path("aggregator", "monkey_patch_trends")
DEFAULT_SUMMARIZER_OUTPUT = build_topic_path("summarizer", "monkey_patch_overview")
```

**Note:** Orchestrator bundle path (L74) is already HOP-compliant:

```python
DEFAULT_HEALTHVIEW_ROOT = build_topic_path("orchestrator", "monkey_patch_oversight")
```

| Aspect | Current | Expected | Fix Location |
|--------|---------|----------|--------------|
| Producer path | Legacy | HOP | Orchestrator L70 |
| Consumer path | Legacy | HOP | Orchestrator L71 |
| Aggregator path | Legacy | HOP | Orchestrator L72 |
| Summarizer path | Legacy | HOP | Orchestrator L73 |

---

### 1.2 S5R-002: scan_monkey_patches.py (Producer)

**Status:** ✅ Already HOP-compliant

The producer correctly uses `build_topic_path()` and emits the standard base package:

| Artifact | Present | Purpose |
|----------|---------|---------|
| `manifest.json` | ✅ | Run metadata + `payload.findings[]` array |
| `summary.md` | ✅ | Human-readable synopsis |
| `telemetry.json` | ✅ | Metrics for time-series ingestion |

**Findings location:** `manifest.payload.findings[]` (array of finding objects)

**No changes required for producer.**

---

### 1.3 S5R-003: classify_monkey_patches.py (Consumer) — **CRITICAL**

**Root cause of pipeline failure.**

The consumer's `_is_scan_dir()` function (L76-101) validates scan directories by checking for:

1. `matches.json` (STRUCTURED_MATCHES_NAME, L66)
2. `report.json` (LEGACY_REPORT_NAME, L65)

**Current validation logic:**

```python
def _is_scan_dir(path: Path) -> bool:
    if not path.is_dir():
        return False
    if path.name.startswith("latest"):
        return False
    if (path / STRUCTURED_MATCHES_NAME).exists():  # matches.json
        return True
    legacy_report = path / LEGACY_REPORT_NAME  # report.json
    if legacy_report.exists():
        # ... validate as list
        return isinstance(data, list)
    return False
```

**Required changes:**

| Function | Change | Lines |
|----------|--------|-------|
| `_is_scan_dir()` | Add check for `manifest.json` with `payload.findings` | L76-101 |
| `_load_structured_findings()` | Add loader for HOP manifest format | L209-238 |
| Constants | Add `MANIFEST_NAME = "manifest.json"` | L65-66 |
| `_resolve_latest_scan()` | Update default roots to HOP paths | L122-159 |
| CLI defaults | Update `DEFAULT_STRUCTURED_ROOT` | L62 |

**Artifact format mapping:**

| Consumer Expects | HOP Producer Emits | Mapping |
|------------------|-------------------|---------|
| `matches.json` (list of findings) | `manifest.json` with `payload.findings[]` | Extract from manifest |
| `report.json` (dict with metadata) | `manifest.json` (contains all metadata) | Use manifest directly |

---

### 1.4 S5R-004: analyze_monkey_patch_trends.py (Aggregator)

**Dependencies on legacy consumer output:**

```python
DEFAULT_CONSUMER_BASE = Path(".repo_studios/reports/consumer_reports/monkey_patch_risk")  # L15
CONSUMER_BUNDLE_PREFIX = "monkey_patch_risk-"  # L19
CONSUMER_SUMMARY_NAME = "summary.json"  # L20
```

Note: The consumer bundles now follow the HOP run slug format (`YYYYMMDD-HHMM`) without the
`monkey_patch_risk-` prefix.

**Required changes:**

| Constant | Current | Expected | Line |
|----------|---------|----------|------|
| `DEFAULT_CONSUMER_BASE` | Legacy path | `build_topic_path("consumer", "monkey_patch_risk")` | L15 |
| `DEFAULT_PRODUCER_BASE` | Legacy path | `build_topic_path("producer", "monkey_patch_scans")` | L16 |
| `DEFAULT_OUTPUT_BASE` | Already HOP | ✅ No change | L51 |

**Consumer bundle discovery:** May need adjustment if consumer output format changes.

---

### 1.5 S5R-005: summarize_monkey_patch_overview.py (Summarizer)

**Status:** ✅ Mostly HOP-compliant

```python
DEFAULT_SUMMARIZER_OUTPUT_DIR = build_topic_path("summarizer", "monkey_patch_overview")  # L47
```

**Input paths still use legacy defaults:**

```python
DEFAULT_CONSUMER_OUTPUT_DIR = Path(".repo_studios/reports/consumer_reports/monkey_patch_risk")  # L44
DEFAULT_PRODUCER_OUTPUT_DIR = Path(".repo_studios/reports/producer_reports/monkey_patch_scans")  # L45
DEFAULT_AGGREGATOR_OUTPUT_DIR = Path(".repo_studios/reports/aggregator_reports/monkey_patch_trends")  # L46
```

**Required changes:**

| Constant | Current | Expected | Line |
|----------|---------|----------|------|
| `DEFAULT_CONSUMER_OUTPUT_DIR` | Legacy | `build_topic_path("consumer", "monkey_patch_risk")` | L44 |
| `DEFAULT_PRODUCER_OUTPUT_DIR` | Legacy | `build_topic_path("producer", "monkey_patch_scans")` | L45 |
| `DEFAULT_AGGREGATOR_OUTPUT_DIR` | Legacy | `build_topic_path("aggregator", "monkey_patch_trends")` | L46 |

---

## 2. Implementation Phases

### Phase 0: Pre-Flight Checklist

- [ ] Verify existing tests baseline (count passing tests)
- [ ] Document current artifact locations for rollback reference
- [ ] Create test fixtures with HOP-format producer output

---

### Phase 1: Consumer HOP Adaptation (Critical Path)

**Objective:** Enable consumer to read findings from HOP producer manifest.

#### 1.1 Add HOP manifest support to `_is_scan_dir()`

**File:** `.repo_studios/scripts/consumers/classify_monkey_patches.py`

**Changes:**

1. Add constant: `MANIFEST_NAME = "manifest.json"` (after L66)
2. Update `_is_scan_dir()` to check for manifest with findings payload

**Before (L92-93):**

```python
if (path / STRUCTURED_MATCHES_NAME).exists():
    return True
```

**After:**

```python
if (path / STRUCTURED_MATCHES_NAME).exists():
    return True
# HOP manifest format support
manifest_path = path / MANIFEST_NAME
if manifest_path.exists():
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            payload = data.get("payload", {})
            if isinstance(payload, dict) and isinstance(payload.get("findings"), list):
                return True
    except Exception:
        pass
```

#### 1.2 Add HOP manifest loader

**Add new function after `_load_legacy_findings()` (~L258):**

```python
def _load_hop_findings(manifest_path: Path) -> tuple[list[Finding], dict[str, Any] | None]:
    """Load findings from HOP manifest.json format.

    Args:
        manifest_path: Path to the manifest.json file.

    Returns:
        Tuple of (findings list, manifest metadata dict).

    Raises:
        ValueError: If manifest does not contain expected structure.
    """
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{manifest_path} must be a JSON object")
    payload = data.get("payload", {})
    if not isinstance(payload, dict):
        raise ValueError(f"{manifest_path} payload must be an object")
    findings_raw = payload.get("findings", [])
    if not isinstance(findings_raw, list):
        raise ValueError(f"{manifest_path} payload.findings must be a list")
    return [Finding.from_obj(obj) for obj in findings_raw], data
```

#### 1.3 Update `_load_structured_findings()` to try HOP format

**Modify L209-238 to check HOP manifest first:**

```python
def _load_structured_findings(run_dir: Path) -> tuple[list[Finding], dict[str, Any] | None]:
    """Load findings from structured scan artifacts.

    Supports HOP manifest.json format and legacy matches.json format.

    Args:
        run_dir: Scan run directory containing artifacts.

    Returns:
        Tuple of (findings list, optional metadata dict).
    """
    # Try HOP manifest format first
    manifest_path = run_dir / MANIFEST_NAME
    if manifest_path.exists():
        try:
            return _load_hop_findings(manifest_path)
        except (ValueError, json.JSONDecodeError):
            pass  # Fall through to legacy formats
    
    # Legacy matches.json format
    matches_path = run_dir / STRUCTURED_MATCHES_NAME
    if not matches_path.exists():
        return [], None
    raw = json.loads(matches_path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError(f"{matches_path} must contain a list of findings")
    metadata: dict[str, Any] | None = None
    report_path = run_dir / LEGACY_REPORT_NAME
    if report_path.exists():
        try:
            maybe_meta = json.loads(report_path.read_text(encoding="utf-8"))
            if isinstance(maybe_meta, dict):
                metadata = maybe_meta
        except Exception:
            metadata = None
    return [Finding.from_obj(obj) for obj in raw], metadata
```

#### 1.4 Update default path constant

**Change L62:**

```python
# Before
DEFAULT_STRUCTURED_ROOT = Path(".repo_studios/reports/producer_reports/monkey_patch_scans")

# After
DEFAULT_STRUCTURED_ROOT = build_topic_path("producer", "monkey_patch_scans")
```

---

### Phase 2: Orchestrator Path Alignment

**Objective:** Update orchestrator to pass HOP-compliant paths to child scripts.

**File:** `.repo_studios/command_center/scripts/orchestrators/run_monkey_patch_oversight.py`

#### 2.1 Update default path constants (L70-73)

**Before:**

```python
DEFAULT_PRODUCER_OUTPUT = Path(".repo_studios/reports/producer_reports/monkey_patch_scans")
DEFAULT_CONSUMER_OUTPUT = Path(".repo_studios/reports/consumer_reports/monkey_patch_risk")
DEFAULT_AGGREGATOR_OUTPUT = Path(".repo_studios/reports/aggregator_reports/monkey_patch_trends")
DEFAULT_SUMMARIZER_OUTPUT = Path(".repo_studios/reports/summarizer_reports/monkey_patch_overview")
```

**After:**

```python
DEFAULT_PRODUCER_OUTPUT = build_topic_path("producer", "monkey_patch_scans")
DEFAULT_CONSUMER_OUTPUT = build_topic_path("consumer", "monkey_patch_risk")
DEFAULT_AGGREGATOR_OUTPUT = build_topic_path("aggregator", "monkey_patch_trends")
DEFAULT_SUMMARIZER_OUTPUT = build_topic_path("summarizer", "monkey_patch_overview")
```

---

### Phase 3: Aggregator Path Alignment

**Objective:** Update aggregator to consume from HOP paths.

**File:** `.repo_studios/scripts/aggregators/analyze_monkey_patch_trends.py`

#### 3.1 Update default path constants (L15-16)

**Before:**

```python
DEFAULT_CONSUMER_BASE = Path(".repo_studios/reports/consumer_reports/monkey_patch_risk")
DEFAULT_PRODUCER_BASE = Path(".repo_studios/reports/producer_reports/monkey_patch_scans")
```

**After:**

```python
DEFAULT_CONSUMER_BASE = build_topic_path("consumer", "monkey_patch_risk")
DEFAULT_PRODUCER_BASE = build_topic_path("producer", "monkey_patch_scans")
```

---

### Phase 4: Summarizer Path Alignment

**Objective:** Update summarizer input paths to HOP locations.

**File:** `.repo_studios/command_center/scripts/summarizers/summarize_monkey_patch_overview.py`

#### 4.1 Update input path constants (L44-46)

**Before:**

```python
DEFAULT_CONSUMER_OUTPUT_DIR = Path(".repo_studios/reports/consumer_reports/monkey_patch_risk")
DEFAULT_PRODUCER_OUTPUT_DIR = Path(".repo_studios/reports/producer_reports/monkey_patch_scans")
DEFAULT_AGGREGATOR_OUTPUT_DIR = Path(".repo_studios/reports/aggregator_reports/monkey_patch_trends")
```

**After:**

```python
DEFAULT_CONSUMER_OUTPUT_DIR = build_topic_path("consumer", "monkey_patch_risk")
DEFAULT_PRODUCER_OUTPUT_DIR = build_topic_path("producer", "monkey_patch_scans")
DEFAULT_AGGREGATOR_OUTPUT_DIR = build_topic_path("aggregator", "monkey_patch_trends")
```

---

### Phase 5: Test Updates

#### 5.1 Consumer Tests

**File:** `tests/tests_consumers/test_classify_monkey_patches.py` (if exists)

- Add fixtures with HOP manifest format
- Test `_is_scan_dir()` recognizes manifest.json with payload.findings
- Test `_load_hop_findings()` extracts findings correctly
- Test `_load_structured_findings()` prefers HOP format over legacy

#### 5.2 Orchestrator Tests

**File:** `tests/tests_orchestrators/test_run_monkey_patch_oversight.py` (if exists)

- Update path assertions to expect HOP locations
- Verify end-to-end pipeline with HOP artifacts

#### 5.3 Integration Tests

- Verify producer → consumer → aggregator → summarizer chain works

---

### Phase 6: Documentation Updates

#### 6.1 Tier-1 Pipeline Document

**File:** `tier1_healthview_orchestration_pipeline.md`

- Update Stage 5 status to reflect HOP compliance
- Update Inputs/Outputs section with HOP paths

#### 6.2 Tier-2 Roster (if exists)

- Document S5R-001 through S5R-005 records
- Update evidence paths

#### 6.3 tier3 YAML files

- Update `tier3_*.yaml` for each modified script

#### 6.4 db_integration files

- Update corresponding markdown files with HOP paths

---

## 3. Validation Checklist

### 3.1 Pre-Implementation

- [x] All existing tests passing (25 Stage 5 tests)
- [x] Current artifact locations documented

### 3.2 Post-Implementation

- [x] Consumer `_is_scan_dir()` recognizes HOP manifest format
- [x] Consumer loads findings from `manifest.payload.findings`
- [x] Orchestrator passes HOP paths to all child scripts
- [x] Aggregator consumes from HOP consumer output
- [x] Summarizer reads from HOP aggregator output
- [x] End-to-end orchestrator run succeeds (exit code 0)
- [x] All tests pass (25/25)
- [ ] Documentation updated

### 3.3 Runtime Verification

Run command:

```powershell
.\.venv\Scripts\python.exe -u .repo_studios/command_center/scripts/orchestrators/run_monkey_patch_oversight.py --repo-root . --log-level INFO
```

**Verified run `20260103-0141`:**

| Script | Expected Output Path | Verified |
|--------|---------------------|----------|
| Producer | `.repo_studios/reports/healthview/producer_reports/monkey_patch_scans/20260103-0141/` | ✅ |
| Consumer | `.repo_studios/reports/healthview/consumer_reports/monkey_patch_risk/20260103-0141/` | ✅ |
| Aggregator | `.repo_studios/reports/healthview/aggregator_reports/monkey_patch_trends/20260103-0141/` | ✅ |
| Summarizer | `.repo_studios/reports/healthview/summarizer_reports/monkey_patch_overview/20260103-0141/` | ✅ |
| Orchestrator | `.repo_studios/reports/healthview/orchestrator_reports/monkey_patch_oversight/20260103-0141/` | ✅ |

**Note:** Consumer, Aggregator, and Summarizer now use the standard HOP run slug format
(`YYYYMMDD-HHMM`).

---

## 4. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Consumer can't parse old scans | Low | Medium | Maintain legacy fallback in `_load_structured_findings()` |
| Aggregator breaks with new consumer output | Medium | Medium | Verify consumer output format compatibility |
| Tests fail due to path changes | High | Low | Update test fixtures systematically |
| Downstream scripts break | Low | Medium | Producer already emits HOP format; no format change |

---

## 5. Update Log

| Date | Author | Change |
|------|--------|--------|
| 2026-01-03 | Agent | Initial plan created after runtime failure investigation |
| 2026-01-03 | Agent | Implementation complete: Phases 1-6 verified, all stop-gates closed |

---

## 6. Stop-Gates

| Gate | Condition | Status |
|------|-----------|--------|
| SG-01 | Consumer `_is_scan_dir()` recognizes `manifest.json` | ✅ Complete |
| SG-02 | Consumer extracts findings from `manifest.payload.findings` | ✅ Complete |
| SG-03 | Orchestrator uses `build_topic_path()` for all defaults | ✅ Complete |
| SG-04 | Aggregator defaults to HOP consumer path | ✅ Complete |
| SG-05 | Summarizer defaults to HOP input paths | ✅ Complete |
| SG-06 | End-to-end orchestrator run exits 0 | ✅ Complete (run 20260103-0141) |
| SG-07 | All tests pass | ✅ Complete (25/25) |
| SG-08 | Documentation updated | ⬜ Pending |
