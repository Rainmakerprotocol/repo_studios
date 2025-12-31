# Report Paths Migration Pattern

## Overview

This document defines the systematic, recursive pattern for converting all scripts that output to `/.repo_studios/reports/` to use the centralized `report_paths.py` library.

## Migration Checklist Per Script

For each script, complete these steps in order:

### Phase 1: Script Analysis

1. **Identify DEFAULT constants** — Search for `DEFAULT_OUTPUT_DIR`, `DEFAULT_*_OUTPUT`, `OUTPUT_DIR`
2. **Identify CLI arguments** — Search for `--output-dir` in argparse setup
3. **Identify PathSpec usage** — Search for `PathSpec(field="output_dir"...)`
4. **Identify tier class** — Determine if producer, consumer, aggregator, summarizer, orchestrator, or utility
5. **Identify topic slug** — The artifact topic name (e.g., `anchor_inventory`, `fault_artifacts`)

### Phase 2: Script Update

1. **Add import** — Add `from libraries.report_paths import ...` (appropriate constants/functions)
2. **Replace DEFAULT constant** — Change hardcoded path to imported constant or `build_topic_path()` call
3. **Update PathSpec default** — If using `PathSpec`, update the `default=` argument
4. **Validate docstrings** — Ensure output path documentation matches new location

### Phase 3: Test Update

1. **Locate test file** — Usually in `tests/tests_<tier>/test_<script_name>.py`
2. **Update path assertions** — Replace hardcoded path strings with `report_paths` imports
3. **Update mock paths** — If tests mock output directories, use new paths
4. **Run tests** — Verify all tests pass

### Phase 4: Configuration Update

1. **Update Make target** — If script has a Makefile target, update output path argument
2. **Update tier-3 YAML** — If script has documentation YAML, update path patterns
3. **Update manifest** — If listed in `scripts_manifest.yaml`, verify artifact_target path

### Phase 5: Validation

1. **Run script** — Execute via Make target or CLI
2. **Verify output location** — Confirm artifacts appear at correct HOP path
3. **Run test suite** — Ensure no regressions

---

## Script Inventory

### Legend

| Status | Meaning |
|--------|---------|
| ⏳ | Not started |
| 🔄 | In progress |
| ✅ | Completed |
| ➖ | N/A (utility/no reports) |

---

### TIER: PRODUCERS (`.repo_studios/scripts/producers/`)

| # | Script | Current Path | Target Path | Status |
|---|--------|--------------|-------------|--------|
| 1 | `generate_anchor_inventory.py` | `.repo_studios/reports/healthview` | `producer_reports/anchor_inventory` | ⏳ |
| 2 | `generate_code_doc_churn_report.py` | `.repo_studios/reports` | `producer_reports/code_doc_churn` | ⏳ |
| 3 | `generate_doc_index.py` | `.repo_studios/reports/healthview` | `producer_reports/doc_index` | ⏳ |
| 4 | `generate_import_graph_report.py` | `.repo_studios/reports/producer_reports` | `producer_reports/import_graph` | ⏳ |
| 5 | `generate_lizard_report.py` | `.repo_studios/reports/producer_reports` | `producer_reports/lizard_metrics` | ⏳ |
| 6 | `generate_standards_index.py` | `.repo_studios/reports/producer_reports` | `producer_reports/standards_index` | ⏳ |
| 7 | `generate_test_coverage_inventory.py` | `.repo_studios/reports/healthview` | `producer_reports/test_coverage_inventory` | ⏳ |
| 8 | `generate_typecheck_report.py` | `.repo_studios/reports/producer_reports` | `producer_reports/typecheck` | ⏳ |
| 9 | `generate_undocumented_logic_report.py` | `.repo_studios/reports` | `producer_reports/undocumented_logic` | ⏳ |
| 10 | `render_inventory_views.py` | `.repo_studios/reports/producer_reports` | `producer_reports/inventory_views` | ⏳ |
| 11 | `scan_code_placeholders.py` | `.repo_studios/reports/producer_reports` | `producer_reports/code_placeholders` | ⏳ |
| 12 | `scan_monkey_patches.py` | `.repo_studios/reports/producer_reports` | `producer_reports/monkey_patches` | ⏳ |
| 13 | `seed_standards_prompts.py` | `.repo_studios/reports/producer_reports/standards_prompt_seeds` | `producer_reports/standards_prompt_seeds` | ⏳ |
| 14 | `validate_import_boundaries.py` | `.repo_studios/reports/producer_reports/import_boundary_reports` | `producer_reports/import_boundaries` | ⏳ |
| 15 | `validate_inventory.py` | `.repo_studios/reports/producer_reports/validate_inventory` | `producer_reports/validate_inventory` | ⏳ |
| 16 | `validate_markdown_anchors.py` | `REPORTS_ROOT` (variable) | `producer_reports/markdown_anchor_validation` | ⏳ |
| 17 | `validate_metrics_anchor_stubs.py` | `REPORTS_ROOT` (variable) | `producer_reports/metrics_anchor_stub_validation` | ⏳ |
| 18 | `verify_docs_integrity.py` | TBD | `producer_reports/docs_integrity_validation` | ⏳ |
| 19 | `check_inventory_health.py` | `.repo_studios/command_center/reports` | `producer_reports/inventory_health` | ⏳ |
| 20 | `collect_faulthandler_reports.py` | `.repo_studios/command_center/reports` | `producer_reports/faulthandler_reports` | ⏳ |
| 21 | `collect_test_log_reports.py` | `.repo_studios/reports/healthview` | `producer_reports/test_log_reports` | ⏳ |
| 22 | `generate_dependency_hygiene_report.py` | TBD | `producer_reports/dependency_hygiene` | ⏳ |
| 23 | `diff_standards_index.py` | TBD | `producer_reports/standards_diff` | ⏳ |
| 24 | `analyze_standards_index_gaps.py` | TBD | `producer_reports/standards_gap` | ⏳ |

---

### TIER: CONSUMERS (`.repo_studios/scripts/consumers/`)

| # | Script | Current Path | Target Path | Status |
|---|--------|--------------|-------------|--------|
| 1 | `classify_monkey_patches.py` | `.repo_studios/reports/consumer_reports/monkey_patch_risk` | `consumer_reports/monkey_patch_risk` | ⏳ |
| 2 | `generate_anchor_health_report.py` | `.repo_studios/reports/consumer_reports/anchor_health_reports` | `consumer_reports/anchor_health` | ⏳ |
| 3 | `generate_fault_artifacts.py` | TBD | `consumer_reports/fault_artifacts` | ⏳ |
| 4 | `generate_test_log_health_report.py` | TBD | `consumer_reports/test_log_health` | ⏳ |

---

### TIER: AGGREGATORS (`.repo_studios/scripts/aggregators/`)

| # | Script | Current Path | Target Path | Status |
|---|--------|--------------|-------------|--------|
| 1 | `aggregate_docs_health_signals.py` | `.repo_studios/reports/aggregator_reports/docs_health_signals` | `aggregator_reports/docs_health_signals` | ⏳ |
| 2 | `analyze_monkey_patch_trends.py` | `.repo_studios/reports/aggregator_reports/monkey_patch_trends` | `aggregator_reports/monkey_patch_trends` | ⏳ |
| 3 | `generate_churn_complexity_heatmap.py` | TBD | `aggregator_reports/churn_complexity_heatmap` | ⏳ |

---

### TIER: SUMMARIZERS

#### `.repo_studios/scripts/summarizers/`

| # | Script | Current Path | Target Path | Status |
|---|--------|--------------|-------------|--------|
| 1 | `summarize_health_suite.py` | TBD | `summarizer_reports/health_suite` | ⏳ |
| 2 | `summarize_standards.py` | `.repo_studios/command_center/reports` | `summarizer_reports/standards_summary` | ⏳ |

#### `.repo_studios/command_center/scripts/summarizers/`

| # | Script | Current Path | Target Path | Status |
|---|--------|--------------|-------------|--------|
| 1 | `summarize_fault_diagnostics_overview.py` | Mixed (see script) | `summarizer_reports/fault_diagnostics_overview` | ⏳ |
| 2 | `summarize_monkey_patch_overview.py` | `.repo_studios/reports/consumer_reports/monkey_patch_risk` | `summarizer_reports/monkey_patch_overview` | ⏳ |
| 3 | `summarize_test_execution_telemetry.py` | `.repo_studios/reports/healthview` | `summarizer_reports/test_execution_telemetry` | ⏳ |
| 4 | `generate_function_analysis.py` | TBD | `summarizer_reports/function_analysis` | ⏳ |

---

### TIER: ORCHESTRATORS (`.repo_studios/command_center/scripts/orchestrators/`)

| # | Script | Current Path | Target Path | Status |
|---|--------|--------------|-------------|--------|
| 1 | `run_docs_health_overview.py` | ~~Wrong paths~~ | Uses `report_paths` imports | ✅ |
| 2 | `run_fault_diagnostics_overview.py` | TBD | Validate child script paths | ⏳ |
| 3 | `run_dependency_import_hygiene.py` | TBD | Validate child script paths | ⏳ |
| 4 | `run_inventory_update.py` | TBD | Validate child script paths | ⏳ |
| 5 | `run_monkey_patch_oversight.py` | TBD | Validate child script paths | ⏳ |
| 6 | `run_standards_integrity.py` | TBD | Validate child script paths | ⏳ |
| 7 | `run_test_execution_telemetry.py` | TBD | Validate child script paths | ⏳ |
| 8 | `orchestrate_full_diagnostic.py` | TBD | Validate child script paths | ⏳ |

---

### TIER: UTILITIES (`.repo_studios/scripts/utilities/`)

| # | Script | Current Path | Target Path | Status |
|---|--------|--------------|-------------|--------|
| 1 | `refresh_mypy_baselines.py` | `.repo_studios/command_center/reports/rawview/mypy_baselines` | `rawview/mypy_baselines` | ⏳ |
| 2 | `anchor_inventory_loader.py` | Legacy path (loader, not writer) | N/A | ➖ |

---

### TIER: COMMAND_CENTER PRODUCERS (`.repo_studios/command_center/scripts/producers/`)

| # | Script | Current Path | Target Path | Status |
|---|--------|--------------|-------------|--------|
| 1 | `generate_commandview_inventory.py` | TBD | Validate paths | ⏳ |
| 2 | `audit_helper_adoption.py` | TBD | Validate paths | ⏳ |
| 3 | `analyze_standards_index_gaps.py` | TBD | Validate paths | ⏳ |

---

### TIER: COMMAND_CENTER AGGREGATORS (`.repo_studios/command_center/scripts/aggregators/`)

| # | Script | Current Path | Target Path | Status |
|---|--------|--------------|-------------|--------|
| 1 | `generate_automation_manifest.py` | TBD | Validate paths | ⏳ |
| 2 | `generate_metrics_summary.py` | TBD | Validate paths | ⏳ |
| 3 | `scan_duplicates.py` | TBD | Validate paths | ⏳ |

---

## Recursive Execution Pattern

### Step-by-Step Workflow

```
For each script in priority order:
    1. READ script to identify:
       - DEFAULT_OUTPUT_DIR or similar constants
       - argparse --output-dir setup
       - PathSpec usage
       - Docstring path references
    
    2. UPDATE script:
       - Add import: from libraries.report_paths import ...
       - Replace DEFAULT constant with report_paths import
       - Update PathSpec default if applicable
       - Update docstrings
    
    3. LOCATE test file:
       - Check tests/tests_<tier>/test_<script_name>.py
    
    4. UPDATE test:
       - Add report_paths import
       - Replace hardcoded path assertions
       - Update mock directories if needed
    
    5. RUN tests:
       - pytest tests/tests_<tier>/test_<script_name>.py -v
    
    6. CHECK for Make target:
       - grep Makefile for script name
       - Update --output-dir argument if present
    
    7. CHECK for tier-3 YAML:
       - Look in docs/pipeline/.../tier3_*.yaml
       - Update path patterns
    
    8. VALIDATE:
       - Run Make target or CLI
       - Verify output at correct location
    
    9. MARK complete in this document
```

### Priority Order

1. **Orchestrators first** — They pass paths to child scripts
2. **Producers** — Core data generators
3. **Consumers** — Depend on producer output
4. **Aggregators** — Combine multiple sources
5. **Summarizers** — Final digests
6. **Utilities** — Support scripts

### Commands Template

```powershell
# Read script to analyze
# (Use read_file tool)

# Run tests after update
cd .repo_studios
$env:PYTHONPATH = "C:\Users\genet\repo_studios\.repo_studios\command_center\scripts"
..\.venv\Scripts\python.exe -m pytest tests/tests_<tier>/test_<script_name>.py -v

# Check Makefile for targets
grep_search "<script_name>" Makefile

# Run Make target to validate
make studio-<target> PYTHON=..\.venv\Scripts\python.exe
```

---

## Import Patterns

### For Producer Scripts

```python
from libraries.report_paths import PRODUCER_REPORTS, build_topic_path

DEFAULT_OUTPUT_DIR = PRODUCER_REPORTS
# or for scripts that need topic-specific path:
DEFAULT_OUTPUT_DIR = build_topic_path("producer", "anchor_inventory")
```

### For Consumer Scripts

```python
from libraries.report_paths import CONSUMER_REPORTS, build_topic_path

DEFAULT_OUTPUT_DIR = CONSUMER_REPORTS
```

### For Aggregator Scripts

```python
from libraries.report_paths import AGGREGATOR_REPORTS, build_topic_path

DEFAULT_OUTPUT_DIR = AGGREGATOR_REPORTS
```

### For Summarizer Scripts

```python
from libraries.report_paths import SUMMARIZER_REPORTS, build_topic_path

DEFAULT_OUTPUT_DIR = SUMMARIZER_REPORTS
```

### For Orchestrator Scripts

```python
from libraries.report_paths import (
    PRODUCER_REPORTS,
    CONSUMER_REPORTS,
    AGGREGATOR_REPORTS,
    SUMMARIZER_REPORTS,
    build_topic_path,
)

# Use imports for each child script's output location
DEFAULT_ANCHOR_INVENTORY_OUTPUT = build_topic_path("producer", "anchor_inventory")
DEFAULT_DOC_INDEX_OUTPUT = build_topic_path("producer", "doc_index")
# etc.
```

---

## Configuration Files to Update

### Makefile Targets

| Target | Current | Needs Update |
|--------|---------|--------------|
| `studio-generate-undocumented-logic-report` | `.repo_studios/reports/producer_reports` | ✅ Correct |
| `studio-aggregate-docs-health` | `.repo_studios/reports/aggregator_reports/docs_health_signals` | ❌ Missing `/healthview/` |
| `studio-orchestrate-docs-health` | N/A (uses script defaults) | ❌ Fix script defaults |

### Tier-3 YAML Files

Located in `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier3_scripts/`:

| YAML File | Status |
|-----------|--------|
| `tier3_generate_code_doc_churn_report.yaml` | ⏳ |
| (others TBD) | ⏳ |

### scripts_manifest.yaml

Located at `.repo_studios/scripts/manifest/scripts_manifest.yaml` — Contains artifact_target paths for all scripts. May need review for HOP compliance.

---

## Validation Checklist

After all migrations complete:

- [ ] All scripts import from `report_paths.py`
- [ ] No hardcoded `.repo_studios/reports` paths remain in scripts
- [ ] All tests pass
- [ ] All Make targets produce output at correct HOP paths
- [ ] Tier-3 YAMLs reflect correct path patterns
- [ ] `scripts_manifest.yaml` artifact_target paths are HOP-compliant
- [ ] Wayward artifacts cleaned from old locations

---

## Document History

| Date | Change |
|------|--------|
| 2025-12-30 | Initial creation with full inventory |
