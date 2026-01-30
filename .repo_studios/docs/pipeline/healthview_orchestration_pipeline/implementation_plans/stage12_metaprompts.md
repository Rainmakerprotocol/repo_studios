---
title: Stage 12 Metaprompts — Phase 4 Walkthrough
tier: tier-2
audience:
  - coding_agent
  - human_developer
owners:
  - repo_studios_team@rainmakerprotocol.dev
role:
  - metaprompt
  - workflow-guide
status: active
version: 1.0.0
updated_at: 2026-01-29
tags:
  - pipeline
  - healthview
  - phase-4
  - metaprompt
related_files:
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/implementation_plans/stage12_template_development_plan.md
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/templates/tier2_producer_template.md
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/tier2_test_execution_telemetry_roster.md
  - .github/instructions/markdown.instructions.md
---

<!-- markdownlint-disable-next-line MD025 -->
# Stage 12 Metaprompts — Phase 4 Walkthrough

> **Purpose:** Sequential prompts for Phase 4 script compliance. One script per walkthrough.
>
> **Final output:** Updated roster section + build document per script.

---

## How to Use

1. Execute prompts in order (1 → 8)
2. Complete each prompt fully before proceeding
3. Each prompt has explicit DONE criteria — verify before moving on

---

## Prompt 1 — Establish Context

**Intent:** Load working context into agent memory. No file changes.

**User provides:**

```yaml
stage: "Stage 2.1"  # Which stage we're working on
roster_path: ".repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/tier2_docs_health_overview_roster.md"
example_roster: ".repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/tier2_test_execution_telemetry_roster.md"
build_doc_dir: ".repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/working_docs/stage_2_1/"
template_path: ".repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/templates/tier2_producer_template.md"
```

**Agent tasks:**

1. Read `example_roster` — understand the AFTER format (TER-001, TER-002 pattern)
2. Read `roster_path` — identify scripts needing Phase 4 work
3. Note: Old workstream checkboxes (A/B/C/D/E) are LEGACY — ignore them

**Phase 4 workflow summary:**

```
Inspect → Fix → Build Doc → Roster Section
```

**Deliverables per script:**

| Artifact | Location | Purpose |
|----------|----------|---------|
| Build doc | `{build_doc_dir}/{RECORD_ID}_{script}_build.md` | Comprehensive inspection + evidence |
| Roster section | In `roster_path` | Clean YAML block (REPLACES old content) |

**DONE when:**

- [ ] Agent read example roster (Stage 1.1 format)
- [ ] Agent read target roster
- [ ] Agent lists scripts available for Phase 4
- [ ] Agent asks: "Which script to process?"

**Next:** Prompt 2 (Select script and template)

---

## Prompt 2 — Select Script and Template

**Intent:** Lock in which script we're processing. No file changes yet.

**User provides:**

```yaml
record_id: "S21R-002"
script_name: "generate_doc_index.py"
script_path: ".repo_studios/scripts/producers/generate_doc_index.py"
test_path: ".repo_studios/tests/tests_producers/test_generate_doc_index.py"
category: "producer"  # producer | consumer | aggregator | summarizer | orchestrator | utility
```

**Template mapping:**

| Category | Template |
|----------|----------|
| producer | `tier2_producer_template.md` |
| consumer | `tier2_consumer_template.md` |
| aggregator | `tier2_aggregator_template.md` |
| summarizer | `tier2_summarizer_template.md` |
| orchestrator | `tier2_orchestrator_template.md` |
| utility | `tier2_utility_template.md` |

**Agent tasks:**

1. Read the appropriate template (based on category)
2. Identify required sections:
   - Section 1: Script Identity
   - Section 2: Current State Analysis (CLI, entry points, outputs)
   - Section 2.5: Output Quality Assessment (QA verification)
   - Section 3: Gap Analysis
   - Section 4: Changes Made
   - Section 5: Evidence
3. Note the Universal Interface Contract requirements:
   - `run(argv)` must return `dict[str, Any]`
   - Required keys: `status`, `exit_code`, `run_dir`, `output_dir`, `run_id`, `manifest`, `telemetry`, `summary`

**DONE when:**

- [ ] Agent confirms: record_id, script_name, script_path, test_path, category
- [ ] Agent confirms which template applies
- [ ] Agent lists the key sections to fill
- [ ] Agent states the return payload requirements

**Next:** Prompt 3 (Locate roster section to replace)

---

## Prompt 3 — Locate Roster Section

**Intent:** Identify what to DELETE from roster. No file changes yet.

**Inputs:**

```yaml
roster_path: ".repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/tier2_docs_health_overview_roster.md"
record_id: "S21R-002"
```

**Agent tasks:**

1. Read the roster file
2. Find the `## [RECORD_ID]` section (e.g., `## S21R-002 — generate_doc_index.py`)
3. Identify section boundaries:
   - **Start:** The `## S21R-XXX` heading line
   - **End:** The line before the next `## S21R-XXX` heading (or EOF)
4. Extract from the YAML block:
   - `script_path:`
   - `test_path:`
   - `category:`

**IGNORE legacy content:**

These appear in old roster entries. DO NOT preserve them:
- Workstream A/B/C/D/E checkboxes
- December 2025 "DONE" markers
- "Discovery Findings", "Migration Plan", "Implementation Evidence" sections

**DONE when:**

- [ ] Agent confirms roster path exists
- [ ] Agent states start line number for record section
- [ ] Agent states end line number for record section
- [ ] Agent confirms script_path from YAML matches Prompt 2
- [ ] Agent confirms category from YAML matches Prompt 2

**Next:** Prompt 4 (Inspect script and document issues)

---

## Prompt 4 — Inspect Script and Document Issues

**Intent:** Read everything, run checks, document issues. No fixes yet.

**Inputs:**

```yaml
script_path: ".repo_studios/scripts/producers/generate_doc_index.py"
test_path: ".repo_studios/tests/tests_producers/test_generate_doc_index.py"
tier3_yaml_path: ".repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier3_yaml/tier3_generate_doc_index.yaml"
db_integration_doc_path: ".repo_studios/command_center/docs/db_integrations/generate_doc_index.md"
build_doc_output: ".repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/working_docs/stage_2_1/S21R-002_generate_doc_index_build.md"
```

**Agent tasks:**

### Part A — Script inspection

1. Read script, note:
   - CLI arguments
   - Entry point function name
   - Output artifacts

2. Check return payload — does `run(argv)` return dict with required keys?
   - `status`, `exit_code`, `run_dir`, `output_dir`, `run_id`, `manifest`, `telemetry`, `summary`

### Part B — Lint checks (run ALL 4 commands)

| Target | Command |
|--------|---------|
| Script ruff | `ruff check [script_path]` |
| Script mypy | `mypy --strict [script_path]` |
| Test ruff | `ruff check [test_path]` |
| Test mypy | `mypy --strict [test_path]` |

### Part C — Test execution

3. Run tests: `pytest [test_path] -v`
4. Run script: `python [script_path] --repo-root . --log-level INFO`

### Part D — Supporting doc verification

5. Read tier3_yaml_path — verify against actual script:
   - script_path matches?
   - entry_function correct?
   - CLI flags complete?
   - output artifacts listed?

6. Read db_integration_doc_path — verify against actual script:
   - producer path correct?
   - output bundle paths correct?
   - DB_INTEGRATION_MARKER comments present in script?

### Part E — Document findings

7. Create build document at `build_doc_output`
8. Fill Section 1 (Script Identity)
9. Fill Section 2 (Inspection Findings) — list ALL issues with file + line number

**DONE when:**

- [ ] Agent ran ruff on script (report: pass or N errors)
- [ ] Agent ran mypy --strict on script (report: pass or N errors)
- [ ] Agent ran ruff on test file (report: pass or N errors)
- [ ] Agent ran mypy --strict on test file (report: pass or N errors)
- [ ] Agent ran pytest (report: pass or N failures)
- [ ] Agent ran script execution (report: pass or error)
- [ ] Agent verified tier3 YAML accuracy (report: accurate or N discrepancies)
- [ ] Agent verified db_integration doc accuracy (report: accurate or N discrepancies)
- [ ] Build document created with issues list

**Next:** Prompt 5 (Fix identified issues)

---

## Prompt 5 — Fix Identified Issues

**Intent:** Apply fixes for each documented issue. No verification yet.

**Inputs:**

```yaml
build_doc_path: ".repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/working_docs/stage_2_1/S21R-002_generate_doc_index_build.md"
issues_from_prompt_4: "Read Section 2 of build doc"
```

**Agent tasks:**

For each issue in the build doc Section 2:

1. **Return payload issues** — Add missing keys to `run()` return dict
2. **Ruff issues** — Run `ruff check [path] --fix` then manual fixes
3. **Mypy issues** — Add type hints, fix type errors
4. **Tier3 YAML issues** — Update YAML to match actual script
5. **DB Integration doc issues** — Update doc to match actual script

**For each fix:**
- Make the code/doc change
- Add entry to build doc Section 4 (Changes Made):
  - File changed
  - What was changed
  - Line numbers affected

**DONE when:**

- [ ] All issues from Section 2 have corresponding fixes in Section 4
- [ ] Build doc Section 4 lists every change made
- [ ] Agent states total number of files modified

**Next:** Prompt 6 (Verify all checks pass)

---

## Prompt 6 — Verify Ruff/Mypy/Tests Pass

**Goal:** Confirm all code quality checks pass after fixes.

```text
Now let's verify that all fixes are working.

Run these commands and report results:

1. **Ruff check:**
   ```
   ruff check [SCRIPT_PATH]
   ```
   Expected: No issues (or "All checks passed")

2. **Mypy check:**
   ```
   mypy --strict [SCRIPT_PATH]
   ```
   Expected: "Success: no issues found"

3. **Pytest:**
   ```
   pytest [TEST_FILE_PATH] -v
   ```
   Expected: All tests pass

4. **Run the script** (if safe to run):
   ```
   python [SCRIPT_PATH] --repo-root . [OTHER_FLAGS]
   ```
   Verify it produces output without errors.

Update the build document Section 4 (QA Evidence) with:
- Ruff result (pass/fail + any notes)
- Mypy result (pass/fail + any notes)
- Pytest result (X/X passed)
- Script execution result (if applicable)

If any check fails, go back to Prompt 5 and fix the remaining issues.
Only proceed to Prompt 7 when ALL checks pass.
```

---

## Prompt 7 — Prepare Tier-2 Roster Section

**Goal:** Create the new roster section that will replace the old one.

```text
Now let's prepare the new Tier-2 roster section.

The new section must follow the format from Stage 1.1 roster (TER-001, TER-002 pattern).

**Naming convention for record_id:**
- Stage 1.1: TER-001, TER-002, etc.
- Stage 2.1: S21R-001, S21R-002, etc.
- Stage 3.1: FDR-001, FDR-002, etc.
- (Use the existing convention for your stage)

**Required YAML structure:**
```yaml
record_id: "[RECORD_ID]"
script:
  path: "[SCRIPT_PATH]"
  name: "[SCRIPT_NAME]"
  category: "[producer/consumer/aggregator/summarizer/orchestrator]"
phase4_build_doc: "[PATH_TO_BUILD_DOC]"
cli_surfaces:
  run_entrypoint: "run(argv)"
  key_flags:
    - "--flag1"
    - "--flag2"
io_contract:
  inputs:
    - "[description of inputs]"
  outputs:
    current:
      root: "[output path]"
      artifacts:
        - "manifest.json"
        - "summary.md"
        - "telemetry.json"
retention:
  surfaces:
    - "--artifacts-to-keep"
  mechanism: "prune_run_directories(...)"
  targets:
    - "[retention target path]"
db_integration:
  gated_by: "REPO_STUDIOS_DB_ENABLED"
  marker_required: true
  marker_string: "DB_INTEGRATION_MARKER:"
evidence:
  code_refs:
    - "[SCRIPT_PATH]#L[START]-L[END]"
  tests:
    - "[TEST_FILE_PATH]"
  fixtures:
    - "[fixture info or 'Uses tmp_path']"
qa_evidence:
  pytest: "✅ X/X passed (2026-01-29)"
  mypy: "✅ clean (2026-01-29)"
  coverage: "[coverage info]"
  output_truth: "[verification of output bundle]"
notes:
  - "Phase 4 compliance completed 2026-01-29"
  - "[other relevant notes]"
```

**Output format:**
- Generate the complete YAML block
- Include the H4 header (e.g., `#### S21R-002: generate_doc_index.py`)
- NO workstream checkboxes
- NO legacy evidence sections

Do NOT edit the roster file yet. Just prepare the content and show me what will be inserted.
```

---

## Prompt 8 — Replace Roster Section and Review

**Goal:** Replace the old roster section with the new one and suggest next steps.

```text
Now let's complete the roster update and review our work.

**Step 1: Replace the roster section**

In the tier2 roster file at: [TIER2_ROSTER_PATH]

DELETE the entire old section for [RECORD_ID], including:
- The H4/H5 header
- The old YAML block
- Any "Implementation Workstreams" sections
- Any "Workstream A/B/C/D/E" checkboxes
- Any "Discovery Findings", "Migration Plan", "Implementation Evidence" content
- Any "DONE" checkboxes

REPLACE with the new section prepared in Prompt 7.

**Step 2: Verify the edit**

After the replacement, confirm:
- The new section is properly formatted
- No old workstream content remains
- The YAML block is valid
- The section follows the TER-001/TER-002 pattern from Stage 1.1

**Step 3: Suggest next script**

From the roster, identify the next script that needs Phase 4 processing.

Report:
1. ✅ [RECORD_ID] — Phase 4 complete
2. 📋 Build document: [PATH]
3. 📋 Roster section: Updated
4. ➡️ Next script: [NEXT_RECORD_ID] ([NEXT_SCRIPT_NAME])

Would you like to proceed with the next script? If yes, start again at Prompt 2 with the new script.
```

---

## Quick Reference — File Locations

| Item | Path |
|------|------|
| Templates | `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/templates/` |
| Build docs | `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/working_docs/[stage]/` |
| Stage 1.1 roster (example) | `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/tier2_test_execution_telemetry_roster.md` |
| Stage 2.1 roster | `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/tier2_docs_health_overview_roster.md` |

---

## Quick Reference — Universal Interface Contract

All scripts with `run(argv)` must return a dict with:

```python
return {
    "status": "success",  # or "error"
    "exit_code": 0,       # or non-zero for error
    "output_dir": str(bundle_dir),
    "run_id": timestamp,
    "manifest": str(manifest_path),
    "telemetry": str(telemetry_path),
    "summary": str(summary_path),
}
```

---

## Update Log

| Date | Author | Action |
|------|--------|--------|
| 2026-01-29 | GitHub Copilot | Created metaprompts walkthrough based on Stage 12 plan clarification request |
