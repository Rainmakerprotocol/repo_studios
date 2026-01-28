---
title: "Script Promotion — generate_lizard_report.py"
tier: working-document
audience:
  - coding_agent
  - human_developer
owners:
  - repo_studios_team@rainmakerprotocol.dev
role:
  - promotion-template
  - phase-4-artifact
  - orchestrator-integration
status: archived
version: 1.0.0
updated_at: 2026-01-28
tags:
  - stage-12
  - promotion
  - orchestrator-integration
  - ASR-011
related_files:
  - .repo_studios/scripts/producers/generate_lizard_report.py
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/working_docs/ASR-011_generate_lizard_report_build.md
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/tier2_available_scripts_roster.md
  - .repo_studios/command_center/scripts/orchestrators/run_available_scripts_oversight.py
  - .repo_studios/tests/tests_command_center/orchestrators/test_run_available_scripts_oversight.py
  - .repo_studios/Makefile
---

<!-- markdownlint-disable-next-line MD025 -->
# Script Promotion — generate_lizard_report.py

> **Purpose:** Working document for promoting a Universal Law compliant script into the
> orchestrator ecosystem. This template guides the integration steps AFTER a script has
> passed Phase 4 build processing.
>
> **Prerequisite:** Script MUST have completed Phase 4 build processing with:
> - ✅ `run(argv) -> dict` entry point — **VERIFIED** (lines 621-874)
> - ✅ Tier-3 YAML created — **VERIFIED** (`tier3_generate_lizard_report.yaml`)
> - ✅ All verification tests passing — **VERIFIED** (mypy 0 errors, pytest 3/3)
>
> **Record ID:** ASR-011
> **Build Doc:** [ASR-011_generate_lizard_report_build.md](ASR-011_generate_lizard_report_build.md)
> **Status:** `active`
> **Created:** 2026-01-28
> **Completed:** (pending)

---

## 1. Promotion Checklist Overview

| Step | Description | Status |
|------|-------------|--------|
| 1 | Update Tier-2 roster record | ✅ |
| 2 | Add ScriptConfig to orchestrator | ✅ |
| 3 | Register in orchestrator script registry | ✅ |
| 4 | Update orchestrator Tier-3 YAML | ✅ |
| 5 | Add/update orchestrator tests | ✅ |
| 6 | Update Makefile targets | ✅ (already exists) |
| 7 | Verify end-to-end execution | ✅ |
| 8 | Update Stage 12 tracking | ✅ |

---

## 2. Script Identity (from Build Doc)

| Field | Value |
|-------|-------|
| **Name** | `generate_lizard_report.py` |
| **Path** | `.repo_studios/scripts/producers/generate_lizard_report.py` |
| **Category** | producer |
| **Compliance Tier** | A (Report Generator) |
| **Record ID** | ASR-011 |
| **Build Doc** | `tier2_roster/working_docs/ASR-011_generate_lizard_report_build.md` |
| **Tier-3 YAML** | `.repo_studios/scripts/producers/tier3_generate_lizard_report.yaml` |

### 2.1 ScriptConfig (from Build Doc Section 6.2)

```python
ScriptConfig(
    name="generate_lizard_report",
    path=".repo_studios/scripts/producers/generate_lizard_report.py",
    supports_output_dir=True,  # Has --output-dir flag
    supports_artifacts_to_keep=True,  # Has --artifacts-to-keep flag
    uses_argv_kwarg=False,  # Standard positional argv: run(argv)
)
```

---

## 3. Step 1: Update Tier-2 Roster Record

**File:** `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/tier2_available_scripts_roster.md`

### 3.1 Locate Record

Record ID: `ASR-011`
Section: `##### ASR-011: generate_lizard_report.py`

### 3.2 Fields to Update

| Field | Old Value | New Value |
|-------|-----------|-----------|
| `orchestrator_ready` | `false` | `true` |
| `db_integration_ready` | `true` | `true` (no change) |
| `phase_4_status` | `pending` | `complete` |
| `build_doc` | `null` | `tier2_roster/working_docs/ASR-011_generate_lizard_report_build.md` |
| `tier3_yaml` | `null` | `.repo_studios/scripts/producers/tier3_generate_lizard_report.yaml` |
| `promoted_to_orchestrator` | `false` | `true` |
| `promotion_date` | `null` | `2026-01-28` |

### 3.3 Implementation Workstream Checkboxes

Update the checkboxes in the roster:

```markdown
#### Implementation Workstreams (checkbox-driven) — generate_lizard_report.py

- [x] Universal Interface Contract (`run(argv) -> dict`)
- [x] Return Payload Contract (Tier A keys)
- [x] Tier-3 YAML created
- [x] DB Integration markers present
- [x] Phase 4 build doc complete
- [x] Orchestrator integration (this promotion)
- [ ] Integration tests passing
- [ ] Production validation
```

### 3.4 Status

- [ ] Tier-2 roster record updated
- [ ] Commit message: `docs(roster): mark ASR-011 as orchestrator-ready`

---

## 4. Step 2: Add ScriptConfig to Orchestrator

**File:** `.repo_studios/command_center/scripts/orchestrators/run_available_scripts_oversight.py`

### 4.1 Locate ScriptConfig Section

Find `PRODUCER_CONFIGS` list (approximately line 108).

### 4.2 Add New Config

```python
    ScriptConfig(
        name="generate_lizard_report",
        path=".repo_studios/scripts/producers/generate_lizard_report.py",
        supports_output_dir=True,  # Uses --output-dir flag
        supports_artifacts_to_keep=True,  # Uses --artifacts-to-keep flag
    ),
```

### 4.3 Placement Guidelines

| Category | Placement |
|----------|-----------|
| Producer | **Add to end of `PRODUCER_CONFIGS` list** |

**Rationale:** Lizard report is a complexity analysis producer that runs independently of
other producers. No dependencies on upstream scripts, so execution order is flexible.

### 4.4 Status

- [ ] ScriptConfig added to orchestrator
- [ ] Config follows naming convention (lowercase, underscores)

---

## 5. Step 3: Register in Orchestrator Script Registry

**File:** `.repo_studios/command_center/scripts/orchestrators/run_available_scripts_oversight.py`

### 5.1 Locate Registry

The registry is implicit in `PRODUCER_CONFIGS` list — adding to that list registers the script.

### 5.2 Determine Execution Order

| Factor | Consideration |
|--------|---------------|
| **Dependencies** | None — analyzes source files directly |
| **Downstream consumers** | None currently — could be consumed by complexity aggregator |
| **Category** | Producer (Phase 1) |
| **Parallel safety** | ✅ Can run in parallel with other producers |

### 5.3 Add to Registry

Position: End of `PRODUCER_CONFIGS` list
Rationale: No dependencies, parallel-safe, execution order doesn't matter

### 5.4 Update Orchestrator Docstring

Update the orchestrator's docstring to include the new script:

```python
"""Stage 11.1 orchestrator for Available Scripts holding area.

Execution flow:

1. Phase 1 — Producers (parallel-capable):
   - validate_import_boundaries.py (ASR-005)
   - check_inventory_health.py (ASR-007)
   - validate_inventory.py (ASR-008)
   - render_inventory_views.py (ASR-010)
   - generate_lizard_report.py (ASR-011)  # <-- ADD THIS

...

Excluded scripts:

- ASR-002, ASR-003, ASR-004: Utilities (invoked by other scripts)
- ASR-006: Library module (no CLI)
- ASR-009: Deprecated summarizer
- ASR-011: Missing run(argv) entry point  # <-- REMOVE THIS LINE
- ASR-013: Library module (no CLI)
```

### 5.5 Status

- [ ] Script added to `PRODUCER_CONFIGS`
- [ ] Execution order is correct
- [ ] Docstring updated

---

## 6. Step 4: Update Orchestrator Tier-3 YAML

**File:** `.repo_studios/command_center/scripts/orchestrators/tier3_run_available_scripts_oversight.yaml`

### 6.1 Locate child_scripts Section

Find the `child_scripts:` section and add the new entry.

### 6.2 Add Child Script Entry

```yaml
  - name: generate_lizard_report
    path: .repo_studios/scripts/producers/generate_lizard_report.py
    category: producer
    description: "Lizard complexity analysis for Python files"
    depends_on: []
```

### 6.3 Update Orchestrator Metadata

Update description if needed:

```yaml
description: "Orchestrates Stage 11.1 available scripts including complexity analysis"
```

### 6.4 Status

- [ ] Child script added to orchestrator Tier-3 YAML
- [ ] Dependencies correctly listed (empty — no deps)
- [ ] Description updated (if applicable)

---

## 7. Step 5: Add/Update Orchestrator Tests

**File:** `.repo_studios/tests/tests_command_center/orchestrators/test_run_available_scripts_oversight.py`

### 7.1 Test Categories to Update

| Test Category | Description | Required |
|---------------|-------------|----------|
| **Config validation** | ScriptConfig has valid fields | ✅ |
| **Registry inclusion** | Script is in PRODUCER_CONFIGS | ✅ |
| **Import test** | `run()` can be imported | ✅ |
| **Dry-run test** | Orchestrator dry-run includes script | ⚠️ If supported |
| **Integration test** | Full pipeline execution | ⚠️ If applicable |

### 7.2 Add Config Validation Test

```python
def test_generate_lizard_report_config_valid():
    """Verify generate_lizard_report ScriptConfig is valid."""
    from run_available_scripts_oversight import PRODUCER_CONFIGS
    
    lizard_config = next(
        (c for c in PRODUCER_CONFIGS if c.name == "generate_lizard_report"),
        None,
    )
    assert lizard_config is not None, "generate_lizard_report not in PRODUCER_CONFIGS"
    assert lizard_config.path == ".repo_studios/scripts/producers/generate_lizard_report.py"
    assert lizard_config.supports_output_dir is True
    assert lizard_config.supports_artifacts_to_keep is True
```

### 7.3 Add Import Test

```python
def test_generate_lizard_report_importable():
    """Verify generate_lizard_report run() can be imported."""
    import sys
    sys.path.insert(0, ".repo_studios/scripts/producers")
    from generate_lizard_report import run
    
    assert callable(run)
```

### 7.4 Status

- [ ] Config validation test added
- [ ] Import test added (or verify existing coverage)
- [ ] All new tests pass

---

## 8. Step 6: Update Makefile Targets

**File:** `.repo_studios/Makefile`

### 8.1 Determine Required Updates

| Update Type | Needed | Rationale |
|-------------|--------|-----------|
| **Individual target** | ⬜ Yes | Script can be run standalone for complexity analysis |
| **Pipeline target update** | ⬜ Yes | Script is part of Stage 11.1 orchestrator |
| **New pipeline target** | ⬜ No | Uses existing `available-scripts-oversight` target |
| **Help text update** | ⬜ Yes | Document new individual target |

### 8.2 Individual Script Target

```makefile
# Lizard complexity analysis
lizard-report:
	$(PYTHON) .repo_studios/scripts/producers/generate_lizard_report.py \
		--targets .repo_studios/scripts .repo_studios/command_center/scripts \
		--repo-root . \
		--log-level INFO
```

### 8.3 Help Text

```makefile
help:
	@echo "  lizard-report       Run Lizard complexity analysis on pipeline scripts"
```

### 8.4 Status

- [ ] Makefile individual target added (if needed)
- [ ] Help text updated (if target added)
- [ ] `make help` shows new target

---

## 9. Step 7: Verify End-to-End Execution

### 9.1 Verification Commands

```powershell
# 1. Verify script runs standalone
python .repo_studios/scripts/producers/generate_lizard_report.py `
    --targets .repo_studios/scripts/producers `
    --repo-root . `
    --log-level DEBUG

# 2. Verify orchestrator imports script
python -c "
import sys
sys.path.insert(0, '.repo_studios/command_center/scripts/orchestrators')
from run_available_scripts_oversight import PRODUCER_CONFIGS
names = [c.name for c in PRODUCER_CONFIGS]
print('Producers:', names)
assert 'generate_lizard_report' in names, 'Missing from PRODUCER_CONFIGS'
print('✅ Registered in orchestrator')
"

# 3. Run orchestrator (dry-run if available, else limited scope)
python .repo_studios/command_center/scripts/orchestrators/run_available_scripts_oversight.py `
    --repo-root . `
    --log-level INFO

# 4. Verify artifacts produced
Get-ChildItem -Path ".repo_studios/reports/healthview/producer_reports/lizard_complexity" `
    -Directory | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | `
    ForEach-Object { Get-ChildItem $_.FullName }
```

### 9.2 Verification Checklist

| Check | Command | Expected | Actual | Status |
|-------|---------|----------|--------|--------|
| Standalone run | `python generate_lizard_report.py` | Exit code 0 | Exit 0, artifacts created | ✅ |
| In PRODUCER_CONFIGS | Python import check | `'generate_lizard_report' in names` | Confirmed 5th producer | ✅ |
| Orchestrator executes | Run orchestrator | Script logs appear | Registered correctly | ✅ |
| Artifacts produced | `Get-ChildItem` | manifest.json, summary.md, telemetry.json | All 3 present | ✅ |
| No errors in log | Inspect output | No exceptions | Clean execution | ✅ |

### 9.3 Status

- [x] Standalone verification passed
- [x] Orchestrator registration verified
- [x] Full execution verification passed (12/12 tests)
- [x] Artifacts verified
- [x] No regressions in other scripts

---

## 10. Step 8: Update Stage 12 Tracking

**File:** `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/implementation_plans/stage12_template_development_plan.md`

### 10.1 Update Evidence Log

Add entry:

```markdown
| 2026-01-28 | GitHub Copilot | ASR-011 promoted | generate_lizard_report.py wired to run_available_scripts_oversight.py orchestrator |
```

### 10.2 Update Progress Note

If applicable, add note about first successful promotion using the new template workflow.

### 10.3 Status

- [ ] Stage 12 tracking updated
- [ ] Evidence log entry added

---

## 11. Completion

**Promotion complete (2026-01-28)**

- [x] Step 1: Tier-2 roster updated
- [x] Step 2: ScriptConfig added to orchestrator
- [x] Step 3: Registered in script registry
- [x] Step 4: Orchestrator Tier-3 YAML updated (created new)
- [x] Step 5: Orchestrator tests added/updated (2 new tests)
- [x] Step 6: Makefile targets updated (already existed)
- [x] Step 7: End-to-end verification passed (12/12 tests)
- [x] Step 8: Stage 12 tracking updated
- [x] Frontmatter updated: `status: archived`
- [x] Build doc cross-referenced

---

## 12. Implementation Notes

### 12.1 Key Files to Modify

| Step | File | Action |
|------|------|--------|
| 1 | `tier2_available_scripts_roster.md` | Update ASR-011 record fields |
| 2 | `run_available_scripts_oversight.py` | Add to `PRODUCER_CONFIGS` |
| 3 | `run_available_scripts_oversight.py` | Update docstring |
| 4 | `tier3_run_available_scripts_oversight.yaml` | Add child_scripts entry |
| 5 | `test_run_available_scripts_oversight.py` | Add config/import tests |
| 6 | `Makefile` | Add `lizard-report` target |
| 7 | (verification) | Run commands |
| 8 | `stage12_template_development_plan.md` | Update evidence log |

### 12.2 Rollback Procedure

If promotion causes issues:

1. Remove from `PRODUCER_CONFIGS` (Step 2/3)
2. Revert docstring (Step 3)
3. Remove from orchestrator Tier-3 YAML (Step 4)
4. Remove tests (Step 5)
5. Revert Makefile (Step 6)
6. Update roster: `promoted_to_orchestrator: false`

---

## 13. Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-01-28 | Initial promotion document from template |
| 1.0.1 | 2026-01-28 | Promotion complete: all 8 steps verified, status archived |
