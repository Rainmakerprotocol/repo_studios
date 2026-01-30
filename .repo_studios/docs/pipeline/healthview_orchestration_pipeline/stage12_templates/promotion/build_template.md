---
title: "Promotion Build Template"
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
status: active
version: 1.0.0
updated_at: <YYYY-MM-DD>
tags:
  - stage-12
  - promotion
  - orchestrator-integration
  - <RECORD_ID>
related_files:
  - <SCRIPT_PATH>
  - <BUILD_DOC_PATH>
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/tier2_available_scripts_roster.md
  - .repo_studios/scripts/orchestrators/run_healthview_pipeline.py
  - .repo_studios/tests/tests_orchestrators/test_run_healthview_pipeline.py
  - .repo_studios/Makefile
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/stage12_templates/manifest.yaml
---

<!-- markdownlint-disable-next-line MD025 -->
# Script Promotion Template — <SCRIPT_NAME>

> **Purpose:** Working document for promoting a Universal Law compliant script into the
> orchestrator ecosystem. This template guides the integration steps AFTER a script has
> passed Phase 4 build processing.
>
> **Prerequisite:** Script MUST have completed Phase 4 build processing with:
>
> - ✅ `run(argv) -> dict` entry point
> - ✅ Tier-3 YAML created
> - ✅ All verification tests passing
>
> **Record ID:** <RECORD_ID>
> **Build Doc:** <BUILD_DOC_PATH>
> **Status:** `active`
> **Created:** <YYYY-MM-DD>
> **Completed:** (pending)

---

## 1. Promotion Checklist Overview

| Step | Description | Status |
|------|-------------|--------|
| 1 | Update Tier-2 roster record | ⬜ |
| 2 | Add ScriptConfig to orchestrator | ⬜ |
| 3 | Register in orchestrator script registry | ⬜ |
| 4 | Update orchestrator Tier-3 YAML | ⬜ |
| 5 | Add/update orchestrator tests | ⬜ |
| 6 | Update Makefile targets | ⬜ |
| 7 | Verify end-to-end execution | ⬜ |
| 8 | Update Stage 12 tracking | ⬜ |

---

## 2. Script Identity (from Build Doc)

| Field | Value |
|-------|-------|
| **Name** | `<SCRIPT_NAME>` |
| **Path** | `<SCRIPT_PATH>` |
| **Category** | <producer/consumer/aggregator/summarizer/utility> |
| **Compliance Tier** | <A/B> |
| **Record ID** | <RECORD_ID> |
| **Build Doc** | <BUILD_DOC_PATH> |
| **Tier-3 YAML** | <TIER3_YAML_PATH> |

### 2.1 ScriptConfig (from Build Doc Section 6.2)

```python
ScriptConfig(
    name="<script_name_without_py>",
    path="<relative_path_from_repo_root>",
    supports_output_dir=<True/False>,
    supports_artifacts_to_keep=<True/False>,
    uses_argv_kwarg=<True/False>,
    custom_args=<None or list>,
)
```

---

## 3. Step 1: Update Tier-2 Roster Record

**File:** `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/tier2_available_scripts_roster.md`

### 3.1 Locate Record

Record ID: `<RECORD_ID>`
Section: `##### <RECORD_ID>: <SCRIPT_NAME>`

### 3.2 Fields to Update

| Field | Old Value | New Value |
|-------|-----------|-----------|
| `orchestrator_ready` | `false` | `true` |
| `db_integration_ready` | `<check>` | `true` |
| `phase_4_status` | `pending` | `complete` |
| `build_doc` | `null` | `<BUILD_DOC_PATH>` |
| `tier3_yaml` | `null` | `<TIER3_YAML_PATH>` |
| `promoted_to_orchestrator` | `false` | `true` |
| `promotion_date` | `null` | `<YYYY-MM-DD>` |

### 3.3 Implementation Workstream Checkboxes

Update the checkboxes in the roster:

```markdown
#### Implementation Workstreams (checkbox-driven) — <SCRIPT_NAME>

- [x] Universal Interface Contract (`run(argv) -> dict`)
- [x] Return Payload Contract (Tier A/B keys)
- [x] Tier-3 YAML created
- [x] DB Integration markers present
- [x] Phase 4 build doc complete
- [x] Orchestrator integration (this promotion)
- [ ] Integration tests passing
- [ ] Production validation
```

### 3.4 Status

- [ ] Tier-2 roster record updated
- [ ] Commit message: `docs(roster): mark <RECORD_ID> as orchestrator-ready`

---

## 4. Step 2: Add ScriptConfig to Orchestrator

**File:** `.repo_studios/scripts/orchestrators/run_healthview_pipeline.py`

### 4.1 Locate ScriptConfig Section

Find the section where `ScriptConfig` instances are defined (typically near the top after imports).

### 4.2 Add New Config

> **⚠️ CRITICAL: `supports_output_dir` Safety Warning**
>
> **Default to `False` unless you have a specific reason to override.**
>
> When `supports_output_dir=True`, the orchestrator passes a **generic parent directory**
> (e.g., `producer_reports/`) to the script via `--output-dir`. This causes:
>
> 1. Script creates output at wrong level: `producer_reports/20260128-1129/` (no topic slug)
> 2. Script's `prune_run_directories()` operates on the parent directory
> 3. **ALL topics' historical runs get pruned** — catastrophic cross-topic data loss
>
> When `supports_output_dir=False` (safe default):
>
> 1. Script uses its internal `build_topic_path()` default with topic slug
> 2. Output goes to correct location: `producer_reports/<topic_slug>/20260128-1129/`
> 3. Pruning is scoped to the script's own topic directory only ✅
>
> **Rule:** If the script uses `build_topic_path()` for its default output directory,
> set `supports_output_dir=False` to preserve that topic-aware behavior.

```python
# <SCRIPT_NAME> — <brief description>
<CONFIG_VAR_NAME> = ScriptConfig(
    name="<script_name_without_py>",
    path="<relative_path_from_repo_root>",
    supports_output_dir=False,  # ⚠️ Safe default — preserves topic-aware path
    supports_artifacts_to_keep=<True/False>,
    uses_argv_kwarg=<True/False>,
    custom_args=<None or list>,
)
```

### 4.3 Placement Guidelines

| Category | Placement |
|----------|-----------|
| Producer | After other producer configs |
| Consumer | After producer configs, before aggregator configs |
| Aggregator | After consumer configs |
| Summarizer | After aggregator configs |
| Utility | At end or in dedicated utility section |

### 4.4 Status

- [ ] ScriptConfig added to orchestrator
- [ ] Config variable follows naming convention: `<CATEGORY>_<NAME>_CONFIG`

---

## 5. Step 3: Register in Orchestrator Script Registry

**File:** `.repo_studios/scripts/orchestrators/run_healthview_pipeline.py`

### 5.1 Locate Registry

Find the script registry (typically a list or dict that defines execution order).

```python
# Example registry patterns:
PIPELINE_SCRIPTS = [
    PRODUCER_INVENTORY_CONFIG,
    PRODUCER_LIZARD_CONFIG,  # <-- Add new script here
    CONSUMER_ANALYSIS_CONFIG,
    ...
]

# OR
SCRIPT_REGISTRY = {
    "producers": [PRODUCER_INVENTORY_CONFIG, ...],
    "consumers": [...],
    ...
}
```

### 5.2 Determine Execution Order

| Factor | Consideration |
|--------|---------------|
| **Dependencies** | Does this script depend on output from another? |
| **Downstream consumers** | Do other scripts consume this script's output? |
| **Category** | Producers → Consumers → Aggregators → Summarizers |
| **Parallel safety** | Can this run in parallel with others? |

### 5.3 Add to Registry

Position: <describe where in the registry>
Rationale: <why this position>

### 5.4 Status

- [ ] Script added to registry
- [ ] Execution order is correct
- [ ] Dependencies documented

---

## 6. Step 4: Update Orchestrator Tier-3 YAML

**File:** `.repo_studios/scripts/orchestrators/tier3_run_healthview_pipeline.yaml`

### 6.1 Locate child_scripts Section

```yaml
child_scripts:
  - name: generate_commandview_inventory
    path: .repo_studios/scripts/producers/generate_commandview_inventory.py
    category: producer
  # Add new script here
```

### 6.2 Add Child Script Entry

```yaml
  - name: <script_name_without_py>
    path: <relative_path_from_repo_root>
    category: <producer/consumer/aggregator/summarizer/utility>
    description: "<brief description>"
    depends_on: [<list of script names this depends on, or empty>]
```

### 6.3 Update Orchestrator Metadata

If the new script changes orchestrator capabilities, update:

```yaml
# Update description if needed
description: "Orchestrates HealthView pipeline including <new capability>"

# Update tags if needed
tags:
  - <new_tag_if_applicable>
```

### 6.4 Status

- [ ] Child script added to orchestrator Tier-3 YAML
- [ ] Dependencies correctly listed
- [ ] Description updated (if applicable)

---

## 7. Step 5: Add/Update Orchestrator Tests

**File:** `.repo_studios/tests/tests_orchestrators/test_run_healthview_pipeline.py`

### 7.1 Test Categories to Update

| Test Category | Description | Required |
|---------------|-------------|----------|
| **Config validation** | ScriptConfig has valid fields | ✅ |
| **Registry inclusion** | Script is in registry | ✅ |
| **Import test** | `run()` can be imported | ✅ |
| **Dry-run test** | Orchestrator dry-run includes script | ⚠️ If supported |
| **Integration test** | Full pipeline execution | ⚠️ If applicable |

### 7.2 Add Config Validation Test

```python
def test_<script_name>_config_valid():
    """Verify <SCRIPT_NAME> ScriptConfig is valid."""
    from run_healthview_pipeline import <CONFIG_VAR_NAME>
    
    assert <CONFIG_VAR_NAME>.name == "<script_name_without_py>"
    assert Path(<CONFIG_VAR_NAME>.path).exists()
    assert isinstance(<CONFIG_VAR_NAME>.supports_output_dir, bool)
    assert isinstance(<CONFIG_VAR_NAME>.supports_artifacts_to_keep, bool)
```

### 7.3 Add Registry Inclusion Test

```python
def test_<script_name>_in_registry():
    """Verify <SCRIPT_NAME> is registered in pipeline."""
    from run_healthview_pipeline import PIPELINE_SCRIPTS, <CONFIG_VAR_NAME>
    
    assert <CONFIG_VAR_NAME> in PIPELINE_SCRIPTS
```

### 7.4 Add Import Test

```python
def test_<script_name>_importable():
    """Verify <SCRIPT_NAME> run() can be imported."""
    import sys
    sys.path.insert(0, "<script_dir>")
    from <script_module> import run
    
    assert callable(run)
```

### 7.5 Status

- [ ] Config validation test added
- [ ] Registry inclusion test added
- [ ] Import test added
- [ ] All new tests pass

---

## 8. Step 6: Update Makefile Targets

**File:** `.repo_studios/Makefile`

### 8.1 Determine Required Updates

| Update Type | Needed | Rationale |
|-------------|--------|-----------|
| **Individual target** | ⬜ Yes / ⬜ No | Script needs standalone invocation |
| **Pipeline target update** | ⬜ Yes / ⬜ No | Script is part of existing pipeline |
| **New pipeline target** | ⬜ Yes / ⬜ No | Script starts a new pipeline |
| **Help text update** | ⬜ Yes / ⬜ No | New target needs documentation |

### 8.2 Individual Script Target (if needed)

```makefile
# <SCRIPT_NAME> — <brief description>
<target-name>:
	$(PYTHON) <SCRIPT_PATH> $(ARGS)

.PHONY: <target-name>
```

### 8.3 Pipeline Target Update (if needed)

If the script is added to an existing orchestrator, verify the pipeline target calls the orchestrator:

```makefile
# HealthView Pipeline — runs full orchestrator
healthview-pipeline:
	$(PYTHON) .repo_studios/scripts/orchestrators/run_healthview_pipeline.py $(ARGS)
```

### 8.4 Help Text

```makefile
help:
	@echo "  <target-name>       <description>"
```

### 8.5 Status

- [ ] Makefile targets updated (if needed)
- [ ] Help text updated (if needed)
- [ ] `make help` shows new target

---

## 9. Step 7: Verify End-to-End Execution

### 9.1 Verification Commands

```bash
# 1. Run orchestrator in dry-run mode (if supported)
python .repo_studios/scripts/orchestrators/run_healthview_pipeline.py --dry-run

# 2. Verify script appears in execution plan
# Expected: <SCRIPT_NAME> listed in output

# 3. Run orchestrator for real
python .repo_studios/scripts/orchestrators/run_healthview_pipeline.py --log-level INFO

# 4. Verify script executed
# Expected: Log shows "<SCRIPT_NAME> completed" or similar

# 5. Verify artifacts produced
# Check: <expected_output_path>
```

### 9.2 Verification Checklist

| Check | Command | Expected | Actual | Status |
|-------|---------|----------|--------|--------|
| Dry-run includes script | `--dry-run` | Script in plan | | ⬜ |
| Orchestrator executes script | `--log-level DEBUG` | Script logs | | ⬜ |
| Artifacts produced | `Test-Path <path>` | True | | ⬜ |
| No errors in log | Grep logs | No errors | | ⬜ |
| Exit code 0 | `$LASTEXITCODE` | 0 | | ⬜ |

### 9.3 Status

- [ ] Dry-run verification passed
- [ ] Full execution verification passed
- [ ] Artifacts verified
- [ ] No regressions in other scripts

---

## 10. Step 8: Update Stage 12 Tracking

**File:** `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/implementation_plans/stage12_template_development_plan.md`

### 10.1 Update Progress Tracking

Find the script in the Stage 12 tracking and update:

```markdown
| <RECORD_ID> | <SCRIPT_NAME> | ✅ Build | ✅ Promote | ✅ Complete |
```

### 10.2 Update Metrics

If Stage 12 has metrics section:

```markdown
## Progress Metrics

- Scripts processed: X → X+1
- Scripts promoted: Y → Y+1
- Orchestrator coverage: Z% → Z+N%
```

### 10.3 Status

- [ ] Stage 12 tracking updated
- [ ] Metrics updated (if applicable)

---

## 11. Completion

**Promotion complete (<YYYY-MM-DD>)**

- [ ] Step 1: Tier-2 roster updated
- [ ] Step 2: ScriptConfig added to orchestrator
- [ ] Step 3: Registered in script registry
- [ ] Step 4: Orchestrator Tier-3 YAML updated
- [ ] Step 5: Orchestrator tests added/updated
- [ ] Step 6: Makefile targets updated
- [ ] Step 7: End-to-end verification passed
- [ ] Step 8: Stage 12 tracking updated
- [ ] Frontmatter updated: `status: archived`
- [ ] Build doc cross-referenced

---

## 12. Template Variables

| Variable | Description | Value |
|----------|-------------|-------|
| `<SCRIPT_NAME>` | Script filename | |
| `<SCRIPT_PATH>` | Full relative path | |
| `<RECORD_ID>` | ASR record ID | |
| `<BUILD_DOC_PATH>` | Path to Phase 4 build doc | |
| `<TIER3_YAML_PATH>` | Path to script's Tier-3 YAML | |
| `<YYYY-MM-DD>` | ISO date | |
| `<CONFIG_VAR_NAME>` | ScriptConfig variable name | |
| `<script_name_without_py>` | Name without .py extension | |

---

## 13. Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-01-27 | Initial promotion template |

---

## Appendix A: Quick Reference

### A.1 Files to Modify

| Step | File | Action |
|------|------|--------|
| 1 | `tier2_available_scripts_roster.md` | Update record |
| 2 | `run_healthview_pipeline.py` | Add ScriptConfig |
| 3 | `run_healthview_pipeline.py` | Add to registry |
| 4 | `tier3_run_healthview_pipeline.yaml` | Add child_scripts entry |
| 5 | `test_run_healthview_pipeline.py` | Add tests |
| 6 | `Makefile` | Update targets |
| 7 | (verification) | Run commands |
| 8 | `stage12_template_development_plan.md` | Update tracking |

### A.2 Common Issues

| Issue | Solution |
|-------|----------|
| Import fails in orchestrator | Check sys.path includes script directory |
| Script not in execution | Verify registry registration |
| Tests fail | Check ScriptConfig matches actual script |
| Artifacts not produced | Verify output_dir handling |

### A.3 Rollback Procedure

If promotion causes issues:

1. Remove from registry (Step 3)
2. Remove ScriptConfig (Step 2)
3. Revert Tier-3 YAML (Step 4)
4. Remove tests (Step 5)
5. Revert Makefile (Step 6)
6. Update roster: `promoted_to_orchestrator: false`
