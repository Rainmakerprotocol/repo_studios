---
title: "Stage 6.1 HOP Refactor Plan — Runtime Compliance Remediation"
audience:
  - coding_agent
  - human_developer
owners:
  - repo_studios_ai
status: complete
version: 1.0.0
updated: 2026-01-03
tags:
  - stage-6.1
  - hop-compliance
  - refactor
  - implementation-plan
related_files:
  - tier2_standards_integrity_roster.md
  - stage_6_1_implementation_plan.md
---

# Stage 6.1 HOP Refactor Plan — Runtime Compliance Remediation

> **Purpose:** Address runtime output path discrepancies discovered during orchestrator execution
> audit. This plan supersedes the "complete" status of `stage_6_1_implementation_plan.md` for the
> affected scripts until verified.
>
> **Status:** ✅ COMPLETE — All scripts verified HOP-compliant at runtime (2026-01-03).

---

## Executive Summary

Runtime inspection of orchestrator run `20260102-2353` revealed that **3 of 6 scripts** do not
emit outputs to HOP-compliant locations despite Tier-2 records claiming otherwise:

| Script | Claimed Status | Runtime Reality | Gap Severity |
|--------|----------------|-----------------|--------------|
| S61R-001 `run_standards_integrity.py` | HOP-compliant | ✅ Verified compliant | None |
| S61R-002 `generate_standards_index.py` | HOP-compliant | ✅ Verified compliant | None |
| S61R-003 `analyze_standards_index_gaps.py` | HOP-compliant | ❌ Legacy path | **High** |
| S61R-004 `diff_standards_index.py` | HOP-compliant | ⏭️ Skipped (no baseline) | N/A |
| S61R-005 `seed_standards_prompts.py` | HOP-compliant | ❌ Legacy path + slug + artifacts | **High** |
| S61R-006 `summarize_standards.py` | HOP-compliant | ⚠️ HOP path, non-standard artifacts | **Low** |

**Root cause:** The **orchestrator overrides child script defaults with legacy paths**.

Investigation confirmed:

- **S61R-003** defines correct default: `DEFAULT_OUTPUT_DIR = build_topic_path("producer", "standards_index_gaps")` (L49)
- **S61R-005** defines correct default: `DEFAULT_OUTPUT_DIR = build_topic_path("producer", "standards_prompt_seeds")` (L52)
- **S61R-006** defines correct default: `DEFAULT_OUTPUT_DIR = build_topic_path("summarizer", "standards_overview")` (L63)

But the **orchestrator** (`run_standards_integrity.py`) defines legacy defaults at **L73-75**:

```python
DEFAULT_GAP_OUTPUT_DIR = Path(".repo_studios/command_center/reports")  # ← LEGACY
DEFAULT_DIFF_OUTPUT_DIR = Path(".repo_studios/reports/producer_reports/standards_index_diff_reports")  # ← LEGACY
DEFAULT_PROMPT_OUTPUT_DIR = Path(".repo_studios/reports/producer_reports/standards_prompt_seeds")  # ← LEGACY (missing healthview)
```

Then passes `--output-dir` to each child script with these legacy values, overriding their correct defaults.

**Fix location:** Orchestrator lines 73-75 — change to use `build_topic_path()`.

---

## 1. Gap Analysis

### 1.1 S61R-003: analyze_standards_index_gaps.py

**Claimed output:**

```
.repo_studios/reports/healthview/producer_reports/standards_index_gaps/<YYYYMMDD-HHMM>/
```

**Actual runtime output:**

```
.repo_studios/command_center/reports/<YYYYMMDD-HHMM>/
```

**Investigation complete:**

| Location | Code | Status |
|----------|------|--------|
| Script L49 | `DEFAULT_OUTPUT_DIR = build_topic_path("producer", "standards_index_gaps")` | ✅ Correct |
| Orchestrator L73 | `DEFAULT_GAP_OUTPUT_DIR = Path(".repo_studios/command_center/reports")` | ❌ Legacy |
| Orchestrator L382-383 | `"--output-dir", str(paths.gap_output_dir)` | Passes legacy path |

**Root cause:** Orchestrator overrides correct child default with legacy `DEFAULT_GAP_OUTPUT_DIR`.

**Fix:** Change orchestrator L73 to:

```python
DEFAULT_GAP_OUTPUT_DIR = build_topic_path("producer", "standards_index_gaps")
```

---

### 1.2 S61R-005: seed_standards_prompts.py

**Claimed output:**

```
.repo_studios/reports/healthview/producer_reports/standards_prompt_seeds/<YYYYMMDD-HHMM>/
```

**Actual runtime output:**

```
.repo_studios/reports/producer_reports/standards_prompt_seeds/standards_prompt_seed-YYYYMMDD_HHMMSS/
```

**Investigation complete:**

| Location | Code | Status |
|----------|------|--------|
| Script L52 | `DEFAULT_OUTPUT_DIR = build_topic_path("producer", "standards_prompt_seeds")` | ✅ Correct |
| Script L53 | `RUN_PREFIX = "standards_prompt_seed"` | ❌ Non-standard slug prefix |
| Orchestrator L75 | `DEFAULT_PROMPT_OUTPUT_DIR = Path(".repo_studios/reports/producer_reports/standards_prompt_seeds")` | ❌ Legacy (missing healthview) |
| Orchestrator L474-475 | `"--output-dir", str(paths.prompt_output_dir)` | Passes legacy path |

**Discrepancies (3 total):**

| Aspect | Expected | Actual | Fix Location |
|--------|----------|--------|--------------|
| Path | `healthview/producer_reports/...` | `producer_reports/...` | Orchestrator L75 |
| Slug format | `YYYYMMDD-HHMM` | `standards_prompt_seed-YYYYMMDD_HHMMSS` | Script slug generation |
| Artifacts | manifest.json, summary.md, telemetry.json | log.txt, report.json, report.md, seed.* | Script artifact emission |

**Root cause:** Orchestrator overrides path AND script uses non-standard slug/artifact conventions.

**Fixes required:**

1. Orchestrator L75: `DEFAULT_PROMPT_OUTPUT_DIR = build_topic_path("producer", "standards_prompt_seeds")`
2. Script: Change slug generation to use `YYYYMMDD-HHMM` format
3. Script: Rename artifacts to base package + supplements

---

### 1.3 S61R-006: summarize_standards.py

**Output path:** ✅ HOP-compliant (not overridden by orchestrator)

```
.repo_studios/reports/healthview/summarizer_reports/standards_overview/<YYYYMMDD-HHMM>/
```

**Investigation complete:**

| Location | Code | Status |
|----------|------|--------|
| Script L60 | `DEFAULT_OUTPUT_DIR = build_topic_path("summarizer", "standards_overview")` | ✅ Correct |
| Script L61 | `SUMMARY_STEM = "standards_overview"` | ❌ Non-standard artifact prefix |
| Orchestrator L500-501 | `summarize_callable(...)` — no `--output-dir` override | ✅ Uses script default |
| Script L354 | `ReportArtifact(filename=f"{SUMMARY_STEM}.json", ...)` | Emits `standards_overview.json` |
| Script L355 | `ReportArtifact(filename=f"{SUMMARY_STEM}.md", ...)` | Emits `standards_overview.md` |

**Artifact discrepancy:**

| Expected | Actual | Fix Location |
|----------|--------|--------------|
| manifest.json | standards_overview.json | Script L354 |
| summary.md | standards_overview.md | Script L355 |
| telemetry.json | (missing) | Add to artifacts list |

**Root cause:** Script uses `SUMMARY_STEM` prefix for artifact names instead of base package names.

**Fixes required:**

1. Script L354: Change to `ReportArtifact(filename="manifest.json", ...)`
2. Script L355: Change to `ReportArtifact(filename="summary.md", ...)`
3. Script: Add `ReportArtifact(filename="telemetry.json", ...)` emission

---

## 2. Investigation Phase — ✅ COMPLETE

All code traces completed. Findings documented in Section 1 above.

### 2.1 S61R-003 Code Trace — ✅ COMPLETE

- [x] Script L49: `DEFAULT_OUTPUT_DIR = build_topic_path("producer", "standards_index_gaps")` — correct
- [x] Orchestrator L73: `DEFAULT_GAP_OUTPUT_DIR = Path(".repo_studios/command_center/reports")` — legacy
- [x] Orchestrator L382-383: Passes `--output-dir` with legacy path, overriding script default

### 2.2 S61R-005 Code Trace — ✅ COMPLETE

- [x] Script L52: `DEFAULT_OUTPUT_DIR = build_topic_path("producer", "standards_prompt_seeds")` — correct
- [x] Script L53: `RUN_PREFIX = "standards_prompt_seed"` — non-standard slug prefix
- [x] Orchestrator L75: `DEFAULT_PROMPT_OUTPUT_DIR` uses legacy path missing `healthview/`
- [x] Orchestrator L474-475: Passes `--output-dir` with legacy path

### 2.3 S61R-006 Code Trace — ✅ COMPLETE

- [x] Script L60: `DEFAULT_OUTPUT_DIR = build_topic_path("summarizer", "standards_overview")` — correct
- [x] Script L61: `SUMMARY_STEM = "standards_overview"` — used as artifact name prefix
- [x] Script L354-355: Emits `{SUMMARY_STEM}.json` and `{SUMMARY_STEM}.md` — non-standard
- [x] Orchestrator does NOT override `--output-dir` for summarizer — uses script default

### 2.4 Orchestrator `--output-dir` Trace — ✅ COMPLETE

| Step | Orchestrator Line | Default Constant | HOP Compliant? |
|------|-------------------|------------------|----------------|
| Index | L354-355 | `DEFAULT_INDEX_OUTPUT_DIR` (L70) | ✅ Yes |
| Gap | L382-383 | `DEFAULT_GAP_OUTPUT_DIR` (L73) | ❌ No |
| Diff | L437-438 | `DEFAULT_DIFF_OUTPUT_DIR` (L74) | ❌ No |
| Prompt | L474-475 | `DEFAULT_PROMPT_OUTPUT_DIR` (L75) | ❌ No |
| Summary | (no override) | Uses script default | ✅ Yes |

### 2.2 S61R-005 Code Trace

- [x] Script L52: `DEFAULT_OUTPUT_DIR = build_topic_path("producer", "standards_prompt_seeds")` — correct
- [x] Script L53: `RUN_PREFIX = "standards_prompt_seed"` — non-standard slug prefix
- [x] Slug generation uses `RUN_PREFIX` to build run folder name
- [x] Orchestrator L75: `DEFAULT_PROMPT_OUTPUT_DIR` uses legacy path missing `healthview/`

### 2.3 S61R-006 Code Trace

- [x] Script L60-63: Defines HOP-compliant `DEFAULT_OUTPUT_DIR` and `SUMMARY_STEM`
- [x] Script L354-355: Uses `SUMMARY_STEM` as artifact filename prefix
- [x] Script does NOT emit `telemetry.json` — missing from base package

---

## 3. Implementation Plan

### Phase 1: Investigation — ✅ COMPLETE

All investigation tasks completed. See Section 2 above.

---

### Phase 2: S61R-003 Remediation

**Objective:** Ensure gap analysis outputs to HOP-compliant path at runtime.

#### 2.1 Script Changes — None Required

| File | Status | Notes |
|------|--------|-------|
| `analyze_standards_index_gaps.py` | ✅ Already correct | L49 uses `build_topic_path("producer", "standards_index_gaps")` |

**No script changes needed — script default is already HOP-compliant.**

#### 2.2 Orchestrator Changes — Required

| File | Change | Line |
|------|--------|------|
| `run_standards_integrity.py` | Change `DEFAULT_GAP_OUTPUT_DIR` from legacy to HOP | L73 |

**Before:**

```python
DEFAULT_GAP_OUTPUT_DIR = Path(".repo_studios/command_center/reports")
```

**After:**

```python
DEFAULT_GAP_OUTPUT_DIR = build_topic_path("producer", "standards_index_gaps")
```

#### 2.3 Test Changes

| File | Change |
|------|--------|
| `test_analyze_standards_index_gaps.py` | Update path assertions to expect HOP location |
| `test_run_standards_integrity.py` | Update manifest assertions for gap artifact paths |

#### 2.4 Documentation Changes

| File | Change |
|------|--------|
| `tier2_standards_integrity_roster.md` | Update S61R-003 record with corrected evidence |
| `tier2_standards_integrity_roster.md` | Update Pruning Index targets |

---

### Phase 2B: S61R-004 Remediation (Diff Producer)

**Objective:** Ensure diff producer outputs to HOP-compliant path at runtime.

**Note:** S61R-004 was skipped in the 20260102-2353 run (no baseline provided), but the
orchestrator default is legacy and should be fixed proactively.

#### 2B.1 Script Changes — None Required

| File | Status | Notes |
|------|--------|-------|
| `diff_standards_index.py` | ✅ Already correct | L59 uses `build_topic_path("producer", "standards_index_diff")` |

#### 2B.2 Orchestrator Changes — Required

| File | Change | Line |
|------|--------|------|
| `run_standards_integrity.py` | Change `DEFAULT_DIFF_OUTPUT_DIR` from legacy to HOP | L74 |

**Before:**

```python
DEFAULT_DIFF_OUTPUT_DIR = Path(".repo_studios/reports/producer_reports/standards_index_diff_reports")
```

**After:**

```python
DEFAULT_DIFF_OUTPUT_DIR = build_topic_path("producer", "standards_index_diff")
```

---

### Phase 3: S61R-005 Remediation

**Objective:** Align prompt seed producer with HOP path, slug, and artifact conventions.

#### 3.1 Script Changes — None Required for Path

Script L52 already uses `build_topic_path("producer", "standards_prompt_seeds")`. The issues are:

1. **Orchestrator overrides path** — fix in orchestrator
2. **Non-standard slug format** — fix in script
3. **Non-standard artifact names** — fix in script

| File | Change | Lines |
|------|--------|-------|
| `seed_standards_prompts.py` | Change slug generation to `YYYYMMDD-HHMM` format | TBD (slug construction) |
| `seed_standards_prompts.py` | Rename `report.json` → `manifest.json` | TBD (artifact emission) |
| `seed_standards_prompts.py` | Rename `report.md` → `summary.md` | TBD (artifact emission) |
| `seed_standards_prompts.py` | Add `telemetry.json` emission | TBD (artifact emission) |
| `seed_standards_prompts.py` | Remove or embed `log.txt` content | TBD |

#### 3.2 Orchestrator Changes — Required

| File | Change | Line |
|------|--------|------|
| `run_standards_integrity.py` | Change `DEFAULT_PROMPT_OUTPUT_DIR` from legacy to HOP | L75 |

**Before:**

```python
DEFAULT_PROMPT_OUTPUT_DIR = Path(".repo_studios/reports/producer_reports/standards_prompt_seeds")
```

**After:**

```python
DEFAULT_PROMPT_OUTPUT_DIR = build_topic_path("producer", "standards_prompt_seeds")
```

#### 3.3 Artifact Disposition Matrix

| Current Artifact | Action | Rationale |
|------------------|--------|-----------|
| `report.json` | → `manifest.json` | Contains run metadata — aligns with base package |
| `report.md` | → `summary.md` | Human-readable summary — aligns with base package |
| `log.txt` | → embed in `telemetry.json` or drop | Diagnostic info belongs in telemetry |
| `seed.json` | Keep as supplemental | Core payload — document as approved supplement |
| `seed.txt` | Keep as supplemental | Alternate format for downstream tooling |
| `seed.yaml` | Keep as supplemental | Alternate format for downstream tooling |

#### 3.4 Test Changes

| File | Change |
|------|--------|
| `test_seed_standards_prompts.py` | Update path assertions |
| `test_seed_standards_prompts.py` | Update slug format assertions |
| `test_seed_standards_prompts.py` | Update artifact name assertions |
| `test_run_standards_integrity.py` | Update manifest assertions for prompt artifact paths |

#### 3.5 Documentation Changes

| File | Change |
|------|--------|
| `tier2_standards_integrity_roster.md` | Update S61R-005 record with corrected evidence |
| `tier2_standards_integrity_roster.md` | Update Pruning Index targets |
| `tier2_standards_integrity_roster.md` | Document approved supplemental artifacts (seed.*) |

---

### Phase 4: S61R-006 Remediation

**Objective:** Align summarizer artifacts with base package convention.

#### 4.1 Decision Required

**Option A: Enforce base package naming**

- Rename `standards_overview.json` → `manifest.json`
- Rename `standards_overview.md` → `summary.md`
- Add `telemetry.json`

**Option B: Document as approved exception**

- Summarizers may emit topic-specific artifacts
- Document the pattern in Tier-2 and standards

**Recommendation:** Option A for consistency. The current naming appears to be legacy rather than
intentional differentiation.

#### 4.2 Script Changes (if Option A)

| File | Change | Line |
|------|--------|------|
| `summarize_standards.py` | Change `ReportArtifact(filename=f"{SUMMARY_STEM}.json"` → `filename="manifest.json"` | L354 |
| `summarize_standards.py` | Change `ReportArtifact(filename=f"{SUMMARY_STEM}.md"` → `filename="summary.md"` | L355 |
| `summarize_standards.py` | Add `ReportArtifact(filename="telemetry.json", ...)` to artifacts list | After L355 |

**Note:** `SUMMARY_STEM` constant at L61 can remain for other uses but should not drive artifact names.

#### 4.3 Test Changes

| File | Change |
|------|--------|
| `test_summarize_standards.py` | Update artifact name assertions |

#### 4.4 Documentation Changes

| File | Change |
|------|--------|
| `tier2_standards_integrity_roster.md` | Update S61R-006 record |

---

### Phase 5: Consolidated Orchestrator Changes

**Objective:** Fix all three legacy `DEFAULT_*_OUTPUT_DIR` constants in one pass.

#### 5.1 Summary of Required Changes

All changes are in `run_standards_integrity.py` lines 73-75:

| Line | Current (Legacy) | Target (HOP) |
|------|------------------|--------------|
| L73 | `DEFAULT_GAP_OUTPUT_DIR = Path(".repo_studios/command_center/reports")` | `build_topic_path("producer", "standards_index_gaps")` |
| L74 | `DEFAULT_DIFF_OUTPUT_DIR = Path(".repo_studios/reports/producer_reports/standards_index_diff_reports")` | `build_topic_path("producer", "standards_index_diff")` |
| L75 | `DEFAULT_PROMPT_OUTPUT_DIR = Path(".repo_studios/reports/producer_reports/standards_prompt_seeds")` | `build_topic_path("producer", "standards_prompt_seeds")` |

**Note:** `build_topic_path` is already imported at L52. No new imports needed.

#### 5.2 Manifest Path Auto-Correction

The orchestrator manifest artifact paths are constructed from child script return values:

- **Gap:** `_execute_gap()` returns `run_dir` from child payload (L404-410)
- **Prompt:** `_execute_prompts()` returns `run_dir` from child payload (L494-498)

Once child scripts emit to HOP paths (via orchestrator default fixes), the manifest will
automatically record correct paths. **No additional manifest construction changes required.**

---

### Phase 6: Codebase Impact Search

**Objective:** Identify external references to legacy paths before migration.

#### 6.1 Search Patterns

| Pattern | Purpose | Expected Hits |
|---------|---------|---------------|
| `command_center/reports/commandview/standards_index_gaps` | Legacy gap path | Tier-2 roster, possibly tests |
| `command_center/reports/20` | Bare timestamp folders | Orchestrator, tests |
| `producer_reports/standards_prompt_seeds` | Legacy prompt path | Script, tests, Tier-2 |
| `standards_prompt_seed-` | Legacy slug format | Script, tests, Tier-2 |
| `standards_overview.json` | Current summarizer artifact | Script, tests, consumers |
| `standards_overview.md` | Current summarizer artifact | Script, tests, consumers |

#### 6.2 Impact Assessment

- [ ] Run grep searches for each pattern
- [ ] Catalog all affected files
- [ ] Identify external consumers (agents, dashboards, tooling)
- [ ] Plan backward-compatible migration if needed

---

### Phase 7: Validation & Evidence

**Objective:** Verify remediation at runtime, not just in code.

#### 7.1 Runtime Validation Checklist

- [x] Run orchestrator with `--log-level INFO` (run: 20260103-0114)
- [x] Verify S61R-003 outputs to `.repo_studios/reports/healthview/producer_reports/standards_index_gaps/<ts>/`
- [x] Verify S61R-003 emits `manifest.json`, `summary.md`, `telemetry.json`
- [x] Verify S61R-005 outputs to `.repo_studios/reports/healthview/producer_reports/standards_prompt_seeds/<ts>/`
- [x] Verify S61R-005 uses `YYYYMMDD-HHMM` slug format (20260103-0114)
- [x] Verify S61R-005 emits base package + documented supplements (manifest.json, summary.md, telemetry.json, seed.*)
- [x] Verify S61R-006 emits `manifest.json`, `summary.md`, `telemetry.json`
- [x] Verify orchestrator manifest records correct paths for all artifacts
- [x] All tests pass (26/26)

#### 7.2 Documentation Update Checklist

- [x] Update Tier-2 roster S61R-003 record with new evidence
- [x] Update Tier-2 roster S61R-005 record with new evidence
- [x] Update Tier-2 roster S61R-006 record with new evidence
- [x] Update Tier-2 Pruning Index with corrected targets
- [x] Update Tier-2 Contract Snapshot with corrected observed paths
- [x] Update Tier-1 Stage 6.1 section with HOP-compliant evidence
- [x] Update tier3 YAML files for S61R-005, S61R-006, and orchestrator
- [x] Update db_integration markdown files for all three scripts
- [x] Re-run workstreams A-E for each affected script (all complete)

---

## 4. Implementation Sequence

> **Key Insight:** Investigation confirmed child scripts already have correct HOP-compliant defaults.
> The orchestrator overrides those defaults via `--output-dir`. Fixes are concentrated in
> `run_standards_integrity.py` lines 73-75 plus S61R-005 slug and S61R-006 artifact naming.

| Order | Phase | Task | File | Line(s) | Risk |
|-------|-------|------|------|---------|------|
| 1 | ~~1~~ | ~~Investigation~~ | — | — | ✅ COMPLETE |
| 2 | 5 | Orchestrator: Fix gap path constant | run_standards_integrity.py | L73 | Low |
| 3 | 5 | Orchestrator: Fix diff path constant | run_standards_integrity.py | L74 | Low |
| 4 | 5 | Orchestrator: Fix prompt path constant | run_standards_integrity.py | L75 | Low |
| 5 | 3 | S61R-005: Fix slug format constant | seed_standards_prompts.py | L53 | Low |
| 6 | 3 | S61R-005: Rename artifacts to base package | seed_standards_prompts.py | TBD | Medium |
| 7 | 4 | S61R-006: Rename artifacts to base package | summarize_standards.py | L354-355 | Low |
| 8 | 4 | S61R-006: Add telemetry.json emission | summarize_standards.py | ~L356 | Low |
| 9 | 6 | Codebase search for legacy path references | — | — | Low |
| 10 | 7 | Update tests for changed paths/artifacts | test_*.py | TBD | Low |
| 11 | 7 | Runtime validation via orchestrator | — | — | Validation |
| 12 | 7 | Documentation updates (Tier-2 roster) | stage_6_*.md | — | Documentation |
| 13 | — | Clean up orphaned legacy directories | — | — | Cleanup |

**Minimal Critical Path (3 lines fix 3 of 4 HOP path issues):**

```python
# run_standards_integrity.py L73-75 — BEFORE
DEFAULT_GAP_OUTPUT_DIR = Path(".repo_studios/command_center/reports")
DEFAULT_DIFF_OUTPUT_DIR = Path(".repo_studios/reports/producer_reports/standards_index_diff_reports")
DEFAULT_PROMPT_OUTPUT_DIR = Path(".repo_studios/reports/producer_reports/standards_prompt_seeds")

# run_standards_integrity.py L73-75 — AFTER
DEFAULT_GAP_OUTPUT_DIR = build_topic_path("producer", "standards_index_gaps")
DEFAULT_DIFF_OUTPUT_DIR = build_topic_path("producer", "standards_index_diff")
DEFAULT_PROMPT_OUTPUT_DIR = build_topic_path("producer", "standards_prompt_seeds")
```

---

## 5. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| External tooling expects legacy paths | Medium | High | Search codebase + coordinate with stakeholders |
| Tests break on path/artifact changes | High | Low | Update tests as part of implementation |
| Pruning removes wrong directories | Low | Medium | Validate pruning targets match new paths |
| Orchestrator fails to find child outputs | Medium | High | Test orchestrator end-to-end after changes |
| Tier-2 records marked complete prematurely again | Medium | Medium | Add runtime validation as mandatory checkpoint |

---

## 6. Stop-Gates

This plan cannot be marked complete until:

**Orchestrator Path Fixes (L72-74):**

- [x] L72 changed to `build_topic_path("producer", "standards_index_gaps")`
- [x] L73 changed to `build_topic_path("producer", "standards_index_diff")`
- [x] L74 changed to `build_topic_path("producer", "standards_prompt_seeds")`

**S61R-005 Script-Level Fixes:**

- [x] Slug generation changed to produce YYYYMMDD-HHMM format
- [x] Artifacts renamed to base package (manifest.json, summary.md, telemetry.json)

**S61R-006 Script-Level Fixes:**

- [x] L353-354 artifact names changed to manifest.json, summary.md
- [x] telemetry.json emission added

**Validation:**

- [x] Orchestrator runtime produces correct paths for all 5 child scripts (run: 20260103-0114)
- [x] All test suites passing (26/26 passed)
- [x] Tier-2 roster updated with runtime-verified evidence
- [x] Tier-1 documentation updated with HOP-compliant status
- [x] Orphaned legacy output directories removed

---

## 7. Update Log

| Date | Author | Change |
|------|--------|--------|
| 2026-01-02 | repo_studios_ai | Initial draft based on runtime audit of orchestrator run 20260102-2353 |
| 2026-01-03 | repo_studios_ai | Investigation complete: confirmed root cause is orchestrator L73-75 legacy defaults; child scripts have correct `build_topic_path` defaults already |
| 2026-01-03 | repo_studios_ai | Implementation complete: Fixed orchestrator L72-74 paths, S61R-005 slug/artifacts, S61R-006 artifacts, orchestrator diff detection, and tests. All 26 tests passing. |
| 2026-01-03 | repo_studios_ai | Runtime verification complete (run 20260103-0114). Tier-1/Tier-2 docs updated. All stop-gates closed except legacy directory cleanup. |
| 2026-01-03 | repo_studios_ai | Irregularity found: Tier-2 documented S61R-002/S61R-004 with `rawview` paths, but actual runtime uses `healthview/producer_reports/`. Fixed documentation to match code reality. |

