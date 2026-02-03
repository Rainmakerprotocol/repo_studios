---
title: "Phase 2: Analysis + Verification"
tier: metaprompt
audience:
  - coding_agent
  - human_operator
phase: 2
checkpoints:
  - CHECKPOINT-2A
  - CHECKPOINT-2B
  - CHECKPOINT-3
  - CHECKPOINT-4
version: 1.0.0
updated_at: 2026-02-02
related_files:
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/stage12_templates/common/review_metaprompts.md
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/stage12_templates/producer/build_template.md
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier3_scripts/
---

# PHASE 2: ANALYSIS + VERIFICATION

> **HOP_ROOT:** `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/`
>
> All paths in this document are relative to repository root unless noted.

---

## Purpose

Phase 2 performs deep analysis of the script and **verifies claims against actual execution**.
This is the most critical phase because it establishes the factual foundation for the inspection.

**Why a separate phase?**
- Forces verification BEFORE gap analysis begins
- Prevents "claiming without checking" behavior
- Ensures Tier-3 YAML exists before finalization

---

## SCOPE

This phase covers three prompts and four checkpoints:

| Prompt | Purpose | Checkpoint | Build Doc Sections |
|--------|---------|------------|-------------------|
| PROMPT-2A-ANALYZE | Static analysis of script | CHECKPOINT-2A | 2.1, 2.2, 2.3, 2.4 |
| PROMPT-2B-VERIFY | **Execute script, verify outputs** | CHECKPOINT-2B | 2.5 |
| PROMPT-34-PREPARE | Tier-3 YAML + DB markers | CHECKPOINT-3, CHECKPOINT-4 | 3, 4 |

**NOT in scope:** Gap detection (Phase 3), external file updates (Phase 4).

---

## PREREQUISITES

Before starting Phase 2, confirm:

| Requirement | How to verify |
|-------------|---------------|
| Phase 1 complete | CHECKPOINT-0 and CHECKPOINT-1 signals received |
| Build doc exists | File at `{HOP_ROOT}/tier2_roster/working_docs/stage_{X_X}/{RECORD_ID}_{script}_build.md` |
| Section 1 filled | Script identity captured (not placeholders) |
| Human approved | Human explicitly delivered Phase 2 prompt |

**If any prerequisite is missing, STOP and request Phase 1 completion.**

---

## DELIVERABLES

When Phase 2 completes, the following will exist:

| Artifact | Status |
|----------|--------|
| Section 2.1 (CLI surfaces) | Filled with actual flags from script |
| Section 2.2 (Entry points) | Documented `run(argv)` or `main(argv)` |
| Section 2.3 (Dependencies) | Internal + external deps listed |
| Section 2.4 (Compliance tier) | A or B with reasoning |
| Section 2.5 (Output Truth) | **Verified against actual execution** |
| Section 3 (Tier-3 YAML) | Created/validated, path recorded |
| Section 4 (DB Integration) | Markers documented |
| Four checkpoint signals | CHECKPOINT-2A, 2B, 3, 4 emitted |

---

## INSTRUCTIONS

### Step 1: Load Required References

Read these files before proceeding:

```text
1. {HOP_ROOT}/stage12_templates/common/review_metaprompts.md
   → PROMPT-2A-ANALYZE section
   → PROMPT-2B-VERIFY section  
   → PROMPT-34-PREPARE section

2. The build document created in Phase 1
   → Get SCRIPT_PATH from Section 1
```

---

### Step 2: Execute PROMPT-2A-ANALYZE

**Goal:** Complete static analysis of the script without executing it.

#### 2.1 CLI Surfaces

1. Open the script at `SCRIPT_PATH`
2. Find `argparse.ArgumentParser()` or equivalent
3. Document ALL flags:
   - Flag name (e.g., `--repo-root`)
   - Type (str, int, Path, etc.)
   - Default value
   - Required or optional
4. Fill Section 2.1 in build doc

#### 2.2 Entry Points

1. Search for `def run(argv` or `def main(argv`
2. Document which pattern the script uses
3. Note if it's importable by orchestrators
4. Fill Section 2.2 in build doc

#### 2.3 Dependencies

1. Scan import statements at top of file
2. Categorize:
   - **Internal:** `from command_center.scripts...`
   - **External:** `import requests`, `from pydantic...`
   - **Standard library:** `import os`, `from pathlib...`
3. Fill Section 2.3 in build doc

#### 2.4 Compliance Tier

1. Check for HOP-compliant patterns:
   - Uses `build_topic_path()` for output paths?
   - Has `--artifacts-to-keep` flag?
   - Uses `prune_run_directories()`?
   - Writes manifest.json, summary.md, telemetry.json?
2. Assign tier:
   - **Tier A:** Fully HOP-compliant
   - **Tier B:** Needs migration work
3. Fill Section 2.4 in build doc

**Output after Step 2:**

```text
═══════════════════════════════════════════════════════════════════
CHECKPOINT-2A: STATIC ANALYSIS COMPLETE
═══════════════════════════════════════════════════════════════════
CLI_FLAGS_COUNT: {N}
ENTRY_POINT: {run(argv)|main(argv)|other}
DEPENDENCIES_INTERNAL: {N}
DEPENDENCIES_EXTERNAL: {N}
COMPLIANCE_TIER: {A|B}

STATIC ANALYSIS COMPLETE — Ready for PROMPT-2B-VERIFY
═══════════════════════════════════════════════════════════════════
```

---

### Step 3: Execute PROMPT-2B-VERIFY (CRITICAL)

> ⚠️ **THIS IS THE MOST CRITICAL STEP**
>
> You MUST actually execute the script and observe real output.
> Do NOT fill the Output Truth Table based on "what the code says it does."
> Fill it based on "what actually happened when I ran it."

#### Why This Matters

In live testing, agents have:
- Claimed outputs exist that were never created
- Filled "evidence" fields with code excerpts instead of execution results
- Checked completion boxes without running anything

**This phase exists to prevent those failures.**

#### Execution Steps

1. **Identify safe execution command:**

```bash
# Typical pattern for producers
.venv/Scripts/python.exe -u {SCRIPT_PATH} --repo-root . --log-level DEBUG
```

2. **Run the script and capture output:**

```powershell
# PowerShell
$output = & .venv/Scripts/python.exe -u {SCRIPT_PATH} --repo-root . --log-level DEBUG 2>&1
$output | Out-File -FilePath "tmp_script_output.txt"
```

3. **Verify artifacts were created:**

```powershell
# Check output directory exists
Get-ChildItem -Path ".repo_studios/reports/healthview/producer_reports/{TOPIC_SLUG}/" | 
    Sort-Object LastWriteTime -Descending | 
    Select-Object -First 1
```

4. **Inspect bundle contents:**

```powershell
# List files in latest bundle
$latest = Get-ChildItem ".repo_studios/reports/healthview/producer_reports/{TOPIC_SLUG}/" | 
    Sort-Object LastWriteTime -Descending | 
    Select-Object -First 1
Get-ChildItem $latest.FullName
```

#### Fill Output Truth Table

For EACH claimed output, record:

| Output | Claimed Location | Actually Exists? | File Size | Timestamp |
|--------|------------------|------------------|-----------|-----------|
| manifest.json | `{path}` | YES/NO | {bytes} | {YYYYMMDD-HHMM} |
| summary.md | `{path}` | YES/NO | {bytes} | {YYYYMMDD-HHMM} |
| telemetry.json | `{path}` | YES/NO | {bytes} | {YYYYMMDD-HHMM} |

**Evidence format:**

```text
EXECUTION_TIMESTAMP: 2026-02-02T14:30:00
COMMAND_USED: .venv/Scripts/python.exe -u .repo_studios/scripts/producers/generate_anchor_inventory.py --repo-root . --log-level DEBUG
EXIT_CODE: 0
BUNDLE_PATH: .repo_studios/reports/healthview/producer_reports/anchor_inventory/20260202-1430/
ARTIFACTS_FOUND:
  - manifest.json (1,245 bytes)
  - summary.md (892 bytes)
  - telemetry.json (15,678 bytes)
```

**Output after Step 3:**

```text
═══════════════════════════════════════════════════════════════════
CHECKPOINT-2B: OUTPUT VERIFICATION COMPLETE
═══════════════════════════════════════════════════════════════════
SCRIPT_EXECUTED: YES
EXIT_CODE: {0|N}
BUNDLE_CREATED: YES
ARTIFACTS_VERIFIED: {manifest.json|summary.md|telemetry.json}
VERIFICATION_METHOD: ACTUAL_EXECUTION

OUTPUT VERIFICATION COMPLETE — Ready for PROMPT-34-PREPARE
═══════════════════════════════════════════════════════════════════
```

---

### Step 4: Execute PROMPT-34-PREPARE

**Goal:** Ensure Tier-3 YAML exists and DB integration markers are documented.

#### Section 3: Tier-3 YAML

1. **Check if Tier-3 already exists:**

```powershell
$tier3Path = ".repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier3_scripts/docs_health_overview/tier3_{script_stem}.yaml"
Test-Path $tier3Path
```

2. **If missing, create from template:**

```text
Template: {HOP_ROOT}/tier3_scripts/tier3_script_template.yaml
Target: {HOP_ROOT}/tier3_scripts/{topic}/tier3_{script_stem}.yaml
```

3. **Validate YAML syntax:**

```powershell
.venv/Scripts/python.exe -c "import yaml; yaml.safe_load(open('{tier3_path}'))"
```

4. **Update tier3_scripts_index.yaml** if new entry added

5. **Fill Section 3 in build doc:**
   - Tier-3 path
   - Created or already existed
   - Validation status

#### Section 4: DB Integration Markers

1. **Search script for DB markers:**

```powershell
Select-String -Path {SCRIPT_PATH} -Pattern "DB_INTEGRATION_MARKER|REPO_STUDIOS_DB_ENABLED"
```

2. **Document findings:**
   - Gating variable (usually `REPO_STUDIOS_DB_ENABLED`)
   - Marker string (usually `DB_INTEGRATION_MARKER:`)
   - Locations where markers appear

3. **Fill Section 4 in build doc**

**Output after Step 4:**

```text
═══════════════════════════════════════════════════════════════════
CHECKPOINT-3: TIER-3 YAML COMPLETE
═══════════════════════════════════════════════════════════════════
TIER3_STATUS: {CREATED|ALREADY_EXISTS}
TIER3_PATH: {full path}
YAML_VALID: YES
INDEX_UPDATED: {YES|NO}

TIER-3 YAML COMPLETE
═══════════════════════════════════════════════════════════════════

═══════════════════════════════════════════════════════════════════
CHECKPOINT-4: DB INTEGRATION COMPLETE
═══════════════════════════════════════════════════════════════════
DB_MARKERS_FOUND: {N}
GATING_VARIABLE: REPO_STUDIOS_DB_ENABLED
MARKER_STRING: DB_INTEGRATION_MARKER:

DB INTEGRATION COMPLETE — Phase 2 finished
═══════════════════════════════════════════════════════════════════
```

---

## COMPLETION SIGNALS

Emit ALL FOUR checkpoint signals before stopping:

```text
═══════════════════════════════════════════════════════════════════
PHASE 2 COMPLETE
═══════════════════════════════════════════════════════════════════
CHECKPOINT-2A: STATIC ANALYSIS COMPLETE ✓
CHECKPOINT-2B: OUTPUT VERIFICATION COMPLETE ✓
CHECKPOINT-3: TIER-3 YAML COMPLETE ✓
CHECKPOINT-4: DB INTEGRATION COMPLETE ✓

Build Document Sections Filled: 2.1, 2.2, 2.3, 2.4, 2.5, 3, 4
Output Truth: VERIFIED BY EXECUTION
Tier-3 YAML: {CREATED|VALIDATED}

PHASE 2 DELIVERABLES READY — AWAITING HUMAN VERIFICATION
═══════════════════════════════════════════════════════════════════
```

---

## ════════════════════════════════════════════════════════════════
## STOP — AWAIT HUMAN VERIFICATION
## ════════════════════════════════════════════════════════════════

**DO NOT PROCEED TO PHASE 3.**

After emitting the completion signals above, **STOP** and wait for the human operator.

### What human will verify:

| Check | How to verify |
|-------|---------------|
| **Script was executed** | Look for `VERIFICATION_METHOD: ACTUAL_EXECUTION` |
| **Output Truth has real evidence** | Check for actual file sizes, timestamps, paths |
| **Bundle actually exists** | Navigate to `BUNDLE_PATH` and confirm files present |
| **Tier-3 YAML exists** | Open `TIER3_PATH` and verify valid YAML |
| **No placeholder text** | Search build doc for `<PLACEHOLDER>` or `TODO` |

### Red flags that indicate fake verification:

| Red Flag | What it looks like |
|----------|-------------------|
| No execution timestamp | Missing `EXECUTION_TIMESTAMP` field |
| Generic file sizes | All files "1,024 bytes" |
| Code excerpts as evidence | "Evidence: Line 145 calls create_storage()" |
| Missing bundle path | `BUNDLE_PATH: <to be filled>` |

### Human decision:

| Outcome | Action |
|---------|--------|
| All checks pass | Human delivers Phase 3 prompt |
| Script not executed | Human requires re-execution with evidence |
| Fake evidence detected | Human requires complete redo of Phase 2 |
| Tier-3 missing | Human requires Tier-3 creation before Phase 3 |

---

## Troubleshooting

### "Script won't run — missing dependencies"

```powershell
# Install missing packages
.venv/Scripts/pip.exe install {package}

# Or run with minimal flags
.venv/Scripts/python.exe -u {SCRIPT_PATH} --help
```

### "Script runs but produces no output"

Check if the script requires specific inputs:
- `--repo-root` pointing to actual repo
- `--index` file that must exist
- Input files the script processes

Try with `--log-level DEBUG` to see what's happening.

### "Tier-3 YAML validation fails"

Common issues:
- Missing required fields (check template)
- YAML syntax error (indentation, colons)
- Path references that don't exist

### "Can't find DB markers"

Not all scripts have DB integration. If none found:
- Set `DB_MARKERS_FOUND: 0`
- Note "No DB integration in this script"
- This is valid — not an error

### "Output directory doesn't match expected HOP path"

If script outputs to legacy path (e.g., `.repo_studios/reports/producer_reports/`):
- This indicates Tier B compliance
- Document actual path in Output Truth
- Add GAP entry in Phase 3: "Needs HOP path migration"

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-02-02 | Initial phase extraction from monolithic workflow |
