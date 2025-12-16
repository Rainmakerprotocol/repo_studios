# Script Refactoring Prompt Templates (Working Draft)

**Purpose:** Multi-prompt workflow for standardizing 77 scripts  
**Status:** Draft - Building collaboratively  
**Target:** Artifact naming + DB integration + positional encoding alignment

---

## Workflow Overview

``` text
Phase 1: Analysis       → Understand current state
Phase 2: Planning       → Generate implementation plan
Phase 3: Execution      → Apply changes with validation
```

---

## Phase 1: Script Analysis Prompt

**Goal:** Examine script and document current state (awareness)

### Prompt Template

```text
We are reviewing scripts in:
`.repo_studios/scripts/producers/`
to align with positional encoding and database integration standards.

Analyze the following script:
`<SCRIPT_PATH>`
`collect_test_log_reports.py`

Report the following information:

1. **Purpose:** What information does this script report/generate?

2. **Current Output Location:** Where are artifacts written?
   - Full path to output directory
   - Does it follow positional encoding (<viewer>/<topic>/<timestamp>/<artifact>)?

3. **Output File Types:** What artifacts are generated?
   - List all files created (e.g., report.json, summary.md, log.txt)
   - Note file extensions (.json, .md, .csv, .txt)

4. **Naming Conventions:** What are the current artifact filenames?
   - Are names generic (report.json) or specific (coverage.json)?
   - Do filenames include timestamps or viewer prefixes?

5. **Timestamp Format:** What format is used in output paths?
   - YYYYMMDD_HHMMSS (legacy)
   - YYYYMMDD-HHMM (standard)
   - Other format

6. **Legacy Pointers:** Are there `latest_*` outputs?
   - If yes, list all latest_* files generated

7. **Pruning Behavior:** Does the script prune old reports?
   - **Pruning Mode:** Overwrite (keep=1) or History (keep>1)?
   - Does it use `prune_run_directories()` from `prune_logs.py`? ✅
   - Does it use `prune_to_latest()` from `prune_logs.py`? ✅ (overwrite mode)
   - Does it have inline pruning logic (shutil.rmtree)? ❌ (needs migration)
   - If history mode, how many runs are retained? (DEFAULT_KEEP value)
   - Is retention configurable via CLI argument?
   - Rationale for mode choice (why overwrite vs history?)

8. **Documentation:** What documentation exists for this script?
   - README sections
   - Docstrings
   - Companion markdown files

9. **Database Integration Status:**
   - Does it use `create_storage()` from database_integration.py?
   - Are there DB_INTEGRATION_MARKER tags?
   - Any database-related comments, stubs, or TODOs?

10. **Make Target:** Is there a Make target for this script?
    - Target name
    - Full command invocation

11. **Viewer/Topic Mapping:**
    - Which viewer should consume this report? (healthview, commandview, rawview, jarvis, vscode)
    - What is the appropriate topic slug?

12. **Dependencies:** What inputs does this script require?
    - Upstream artifacts
    - Configuration files
    - Environment variables
```

### Expected Output

A structured report covering:

- Script purpose and current behavior
- Output paths, artifact names, and formats
- Timestamp format and legacy pointer status
- Pruning configuration
- Documentation state
- Database integration readiness
- Make target details
- Recommended viewer/topic mapping
- Gap analysis vs positional encoding standards

---

## Phase 2: Implementation Plan

**Goal:** Convert awareness into detailed implementation plan (planning)

```text
Based on the analysis of:
`<SCRIPT_PATH>`
`collect_test_log_reports.py`

Generate a detailed implementation plan to align this script with
positional encoding and database integration standards.
```

### Target Standards

**Positional Encoding (Path Structure):**

```text
<reports_root>/<viewer_slug>/<topic>/<timestamp>/<artifact>
               └─────1─────┘ └───2──┘ └────3────┘ └───4───┘

Position 1: Viewer context (who/what consumes this)
Position 2: Topic/scope (what aspect of the system)
Position 3: When (temporal identifier - YYYYMMDD-HHMM UTC)
Position 4: What (artifact role per registry)
```

**Path Rules:**

- `viewer_slug`: One of {healthview, commandview, rawview, jarvis, vscode}
- `topic`: kebab-case or underscore_case slug (stable identifier, no timestamps)
- `timestamp`: YYYYMMDD-HHMM format (UTC, sortable, 13 chars)
- `artifact`: Role-based filename from canonical registry

**Output Format Standard (3 File Types Preferred):**

**Required Outputs:**

- `manifest.json` - Pipeline metadata (viewer_slug, topic, timestamp, catalog, inputs, provenance)
- `summary.md` - Human-readable digest with findings and recommendations
- `telemetry.json` - Extracted metrics for time-series DB ingestion

**Optional Output (Exception Basis):**

- `matrix.csv` - Tabular data when spreadsheet analysis adds value (duplicates, coverage thresholds)

**Strongly Preferred File Types:**

1. `.json` - All structured data (DB ingestion, AI agent queries)
1. `.md` - All human-readable content (documentation, summaries)
1. `.csv` - Tabular exports ONLY when format provides clear benefit

**Flexibility Clause:**
If this script has legitimate requirements for additional file types or formats not covered above, explain:

- Why the additional format is necessary
- What use case it serves that .json/.md/.csv cannot
- Whether it can be consolidated into one of the standard formats
- Recommendation: keep or add the exception

**Maximum Output Guideline:**
Target ≤3 output files per report run. Acknowledge that some scripts may require
exceptions (e.g., raw tool outputs, specialized formats), but justify any deviation
from this guideline.

**Deprecated Formats (Remove During Refactoring):**

- `log.txt` - Embed in manifest.json or write to stdout only
- `report.json` - Too generic; split into manifest.json + telemetry.json
- `bundle_summary.json` - Rename to manifest.json
- `.tsv` files - Convert to .csv
- `latest_*` files - Remove all mutable pointers
- `raw.txt` - Convert to raw.json or embed in manifest (exception: lizard/radon if exact format needed)

**Forbidden:**

- `latest_*` or `current_*` aliases
- Timestamps in topic names
- Viewer prefixes in artifact names (e.g., `healthview_coverage.json`)
- Generic names without path context (e.g., standalone `report.json`)

**Database Integration:**

- Use `create_storage()` from `scripts/libraries/database_integration.py`
- Add `DB_INTEGRATION_MARKER` comments above write operations
- Extract telemetry for `test_metrics` table
- Populate `manifest.json` with catalog, inputs, provenance

### Implementation Plan Requirements

Generate a plan covering:

1. **Path Migration:**
   - Current path: (from Phase 1)
   - Target path: `<reports_root>/<viewer>/<topic>/<YYYYMMDD-HHMM>/`
   - Viewer selection rationale
   - Topic slug choice

1. **Output Format Alignment:**
   - Target: ≤3 files (manifest.json, summary.md, telemetry.json)
   - List all current → target filename mappings
   - Remove any `latest_*` file generation
   - Ensure lowercase filenames
   - Consolidate multiple .json files into manifest + telemetry
   - Convert any .txt logs to manifest.json embeddings
   - Justify any exceptions to 3-file guideline

1. **Timestamp Conversion:**
   - Current format → YYYYMMDD-HHMM
   - Update folder name generation logic
   - Update any timestamp parsing code

1. **manifest.json Creation:**
   - Structure with: viewer_slug, topic, run_timestamp, git_sha, status
   - Populate catalog array with script roles
   - Include inputs JSONB with configuration
   - Add provenance: requested_by, trigger_type

1. **telemetry.json Extraction:**
   - Identify metrics to extract (coverage_pct, test counts, complexity, etc.)
   - Map to `test_metrics` table columns
   - Handle JSONB fields for nested data

1. **Database Integration:**
   - Replace file writes with `storage.write_manifest(data)`
   - Replace summary writes with `storage.write_summary(content)`
   - Add `DB_INTEGRATION_MARKER: <description>` tags
   - Ensure graceful degradation if DB disabled

1. **Pruning Standardization:**

   **Determine Pruning Mode:**

   - **Overwrite Mode (keep=1):**
     - Intent: Expensive operations where only latest state matters, no trend analysis needed
     - Use: `prune_to_latest()` from `command_center.scripts.libraries.prune_logs`
     - Behavior: Always retains exactly 1 run (most recent)
     - No CLI argument needed (hardcoded to 1)
     - Examples: function_analysis (expensive), standards_index (latest-state-only)
     - Import: `from command_center.scripts.libraries.prune_logs import prune_to_latest`

   - **History Mode (keep≥5):**
     - Intent: Time-series data, trend analysis, historical comparison
     - Use: `prune_run_directories(keep=N)` from `command_center.scripts.libraries.prune_logs`
     - Behavior: Retains N most recent runs for historical queries
     - Default: 5 runs (configurable via `--keep` CLI argument)
     - Examples: test_coverage, duplicate_scan, monkey_patch_tracking
     - Import: `from command_center.scripts.libraries.prune_logs import prune_run_directories`

   **Migration Steps:**
   - Replace inline pruning logic (shutil.rmtree) with library function
   - For overwrite mode: Call `prune_to_latest(base_dir, stem_prefix="topic-", current_run=run_dir, logger=logger)`
   - For history mode: Add `--keep` CLI argument with default=5, call
      `prune_run_directories(base_dir, keep=keep, stem_prefix="topic-", current_run=run_dir, logger=logger)`
   - Remove custom `prune_old_runs()` or `_prune_history()` functions
   - Ensure current_run is passed to protect it from pruning
   - Log pruning results via returned `PruneResult` object
   - Update path construction to work with new viewer/topic structure

1. **Code Changes:**
   - Function signatures to update
   - Import statements to add
   - Configuration parameters to change
   - Error handling for storage writes

1. **Test Updates:**
   - Which test files need updating?
   - Path assertions to change
   - Artifact name assertions to update
   - Add DB integration tests (optional)

1. **Documentation Updates:**
    - Update docstrings
    - Revise README sections
    - Create `db_integration_<script_name>.md`

1. **Rollback Plan:**
    - How to revert if issues arise
    - Backward compatibility considerations

### Output Format

Provide the plan as:

- Numbered checklist of tasks
- Before/after code snippets for key changes
- File tree showing old vs new structure
- Risk assessment (low/medium/high)

### Expected Output

A comprehensive implementation plan including:

- Path migration strategy with viewer/topic justification
- Complete artifact renaming table (before → after)
- Timestamp conversion approach
- manifest.json structure with all required fields
- telemetry.json extraction logic
- Database integration points with marker tags
- Test update checklist
- Documentation update requirements
- Rollback strategy

---

## Phase 3: Implementation Execution Prompt

**Goal:** Execute implementation plan with validation (execution)

### Prompt Template

````text
Execute the implementation plan for:
`<SCRIPT_PATH>`
`collect_test_log_reports.py`

Follow the detailed plan from Phase 2.

### Execution Requirements

**Code Changes:**
1. Update output path construction to use positional encoding
2. Replace file writes with `storage.write_*()` calls from database_integration.py
3. Rename artifacts per canonical registry
4. Convert timestamp format to YYYYMMDD-HHMM
5. Remove `latest_*` pointer generation
6. Add `DB_INTEGRATION_MARKER` tags above storage writes
7. Generate manifest.json with catalog, inputs, provenance
8. Extract telemetry.json with metrics for DB ingestion
9. Update pruning logic to work with new paths
10. Import `create_storage()` from libraries.database_integration

**Test Updates:**
1. Update test fixtures to use new path structure
2. Change artifact name assertions (report.json → summary.md, etc.)
3. Update timestamp format assertions
4. Verify manifest.json contains required fields
5. Verify telemetry.json extraction works correctly
6. Remove tests for `latest_*` pointers
7. Ensure tests pass with `REPO_STUDIOS_DB_ENABLED=false` (dormant DB writes)

**Documentation Updates:**
1. Update script docstrings with new output paths
2. Revise README sections referencing this script
3. Create `db_integration_<script_name>.md` in `command_center/docs/`
   - Document database tables written to
   - Show manifest.json → report_runs mapping
   - Show telemetry.json → test_metrics mapping
   - Provide example SQL queries for agents

**Validation Checks (MUST PASS):**

1. **Tests:**
   ```bash
   pytest tests/tests_<tier>/test_<script_name>.py -v
   # Expected: All tests GREEN
   ```

2. **Test Coverage:**
   ```bash
   pytest --cov=.repo_studios/scripts/<tier>/<script_name>.py --cov-report=term-missing
   # Expected: Coverage ≥ 80%
   ```

3. **Type Checking:**
   ```bash
   mypy .repo_studios/scripts/<tier>/<script_name>.py
   # Expected: No errors
   ```

4. **Script Execution:**
   ```bash
   python .repo_studios/scripts/<tier>/<script_name>.py <args>
   # Expected: Exit code 0
   ```

   Confirm via the Make target (if available for this script):
   ```bash
   make -C .repo_studios <make_target>
   # Example:
   # make -C .repo_studios studio-collect-test-log-reports
   # make -C .repo_studios studio-collect-faulthandler-reports
   # Expected: Exit code 0
   # Expected: Artifacts written under <reports_root>/<viewer>/<topic>/<YYYYMMDD-HHMM>/
   ```

5. **Output Inspection:**
   - Verify new path structure created: `<viewer>/<topic>/<YYYYMMDD-HHMM>/`
   - Verify the newest run folder contains exactly:
     - `manifest.json`
     - `summary.md`
     - `telemetry.json`
   - Verify `manifest.json` and `telemetry.json` parse as valid JSON (no decode errors)
   - Verify manifest.json contains: viewer_slug, topic, run_timestamp, catalog, inputs
   - Verify summary.md exists and is human-readable
   - Verify telemetry.json contains extracted metrics
   - Verify NO `latest_*` files created
   - Verify timestamp format is YYYYMMDD-HHMM (13 chars)
   - **Verify pruning behavior:**
     - **Overwrite mode:** Run script twice, confirm only 1 timestamped folder exists
     - **History mode:** Run script N+1 times (where N=keep), confirm only N folders remain
     - Current run is never pruned (even if older than kept runs)
     - `.keep` sentinel files prevent pruning (if any exist)

6. **Database Integration Status:**
   ```bash
   grep -n "DB_INTEGRATION_MARKER" .repo_studios/scripts/<tier>/<script_name>.py
   # Expected: At least 1 marker found
   
   grep -n "create_storage()" .repo_studios/scripts/<tier>/<script_name>.py
   # Expected: Storage initialization found
   ```

   On Windows (PowerShell), use:
   ```powershell
   Select-String -Path .repo_studios/scripts/<tier>/<script_name>.py -Pattern "DB_INTEGRATION_MARKER"
   Select-String -Path .repo_studios/scripts/<tier>/<script_name>.py -Pattern "create_storage"
   ```

7. **Marker Audit:**
   ```bash
   python .repo_studios/command_center/scripts/utilities/list_db_markers.py --format md
   # Expected: This script appears in output with marker count > 0
   ```

### Execution Steps

1. Apply all code changes from the implementation plan
2. Update all test files
3. Run test suite and verify GREEN
4. Run mypy and verify CLEAN
5. Execute script with test arguments
6. Inspect output artifacts manually
6. Run the Make target and confirm artifacts
7. Verify coverage ≥ 80%
8. Update documentation
9. Run marker audit
10. Commit changes with descriptive message

### Success Criteria

✅ All tests pass (GREEN)  
✅ Test coverage ≥ 80%  
✅ Mypy reports no errors  
✅ Script executes successfully  
✅ Output artifacts follow positional encoding  
✅ manifest.json contains all required fields  
✅ telemetry.json extracted correctly  
✅ NO `latest_*` files generated  
✅ DB_INTEGRATION_MARKER tags present  
✅ Documentation updated  
✅ Marker audit shows script integrated  

### Rollback Trigger

If any validation check fails:
1. Document the failure
2. Revert changes via git
3. Report blocker in implementation plan
4. Do NOT proceed to next script
````

### Expected Output

- All code changes applied per plan
- Tests updated and passing GREEN
- Test coverage ≥ 80%
- Mypy clean
- Script executes successfully
- Output artifacts inspected and validated
- Documentation updated
- DB markers present
- update `script_inventory_architecture.md` with new status

---

## Notes Section

Use this space for observations, edge cases, patterns discovered during refactoring.
