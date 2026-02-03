---
title: "Script Review Metaprompts"
tier: metaprompt
audience:
  - coding_agent
  - human_operator
status: active
version: 1.3.0
updated_at: 2026-02-02
template_version: "3.4.0"
template_file: ../{CLASS}/build_template.md
related_files:
  - ../producer/build_template.md
  - ../consumer/build_template.md
  - ../aggregator/build_template.md
  - ../summarizer/build_template.md
  - ../utility/build_template.md
  - ../orchestrator/build_template.md
  - ../promotion/build_template.md
  - ../manifest.yaml
  - ../BOOTSTRAP.md
---

# Script Review Metaprompts

> **Purpose:** Guided prompts for inspecting an EXISTING script (any class) and bringing it
> to Phase 4 compliance.
>
> **Applies to all script classes:** producer, consumer, aggregator, summarizer, utility,
> orchestrator, promotion.
>
> **Use when:** Script exists but needs compliance review, gap closure, or re-inspection.
>
> **Do NOT use when:** Designing a new script from scratch (use class-specific
> `create_metaprompts.md` instead, when available).

---

## How to Use This Document

1. **Human operator** copies a prompt and delivers it to the coding agent
2. **Coding agent** executes the prompt against the target script
3. **Coding agent** outputs the PROCEED_SIGNAL when checkpoint is complete
4. **Human operator** verifies output, then delivers next prompt
5. **Repeat** until CHECKPOINT-10 signals completion

**STOP_GATE prompts** require human verification before proceeding.

**Note:** The template file is class-specific (e.g., `producer/build_template.md`,
`consumer/build_template.md`). BOOTSTRAP.md determines the correct template based
on script location.

---

## Execution Flow

```text
PROMPT-01-SETUP ──► PROMPT-2A-ANALYZE ──► PROMPT-2B-VERIFY ──► PROMPT-34-PREPARE
    (STOP_GATE)                              (STOP_GATE)
        │                                        │
        ▼                                        ▼
   CHECKPOINT-0                             CHECKPOINT-2B
   CHECKPOINT-1                                  │
        │                                        │
        └────────────────────────────────────────┘
                            │
                            ▼
PROMPT-5-GAPS ──► PROMPT-67-EVIDENCE ──► PROMPT-8-ORCHESTRATOR ──► PROMPT-910-CLOSE
                                                                      (STOP_GATE)
        │                 │                      │                        │
        ▼                 ▼                      ▼                        ▼
   CHECKPOINT-5      CHECKPOINT-6           CHECKPOINT-8            CHECKPOINT-9
                     CHECKPOINT-7                                   CHECKPOINT-10
```

**CRITICAL_PATH:** CHECKPOINT-0 → CHECKPOINT-2B → CHECKPOINT-9 → CHECKPOINT-10

---

## Pre-Flight: Verify Build Document

> **⚠️ IMPORTANT:** If you arrived here via BOOTSTRAP.md, the build document already exists.
> **DO NOT WAIT** — proceed directly to PROMPT-01-SETUP to begin the inspection.
>
> Only use this section if you need to create a build document manually (rare).

**If build document does NOT exist:**

```text
TASK: Create the build document from template.

1. Copy the template:
   SOURCE: .repo_studios/docs/pipeline/healthview_orchestration_pipeline/stage12_templates/{CLASS}/build_template.md
   DESTINATION: .repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/working_docs/stage_{STAGE}/{RECORD_ID}_{SCRIPT_STEM}_build.md

   Where:
   - {CLASS} = Script class (producer, consumer, aggregator, etc.)
   - {STAGE} = Stage number with underscore (e.g., 11_1 for Stage 11.1)
   - {RECORD_ID} = Assigned record ID (e.g., ASR-012)
   - {SCRIPT_STEM} = Script filename without .py (e.g., scan_duplicates)

2. Create destination folder if needed:
   tier2_roster/working_docs/stage_{STAGE}/

3. Replace frontmatter placeholders:
   - <RECORD_ID> → actual record ID (e.g., ASR-008)
   - <SCRIPT_PATH> → actual script path
   - <SCRIPT_NAME> → script filename
   - updated_at → today's date (YYYY-MM-DD)
   - valid_until → today + 90 days

4. STOP and confirm: "Build document created at {path}"
```

**If build document EXISTS (normal BOOTSTRAP flow):**

```text
TASK: Verify build document is ready.

1. Confirm BUILD_DOC path was provided by BOOTSTRAP
2. Verify file exists at that path
3. Proceed to PROMPT-01-SETUP
```

---

## PROMPT-01-SETUP

<!-- TEMPLATE_SECTIONS: 0, 1 -->
<!-- CHECKPOINT_IDS: CHECKPOINT-0, CHECKPOINT-1 -->
<!-- STOP_GATE: TRUE -->
<!-- ESTIMATED_TIME: 10-15 minutes -->

**Delivers to agent:**

```text
TASK: Verify inputs and capture script identity.

BUILD_DOC: {path to build document}
SCRIPT_PATH: {path to target script}
RECORD_ID: {record ID}
COMPLIANCE_TIER: {A or B}
TARGET_STAGE: {stage}

INSTRUCTIONS:

SECTION 0 — INPUT CONTRACT:
1. Open the build document at BUILD_DOC
2. Navigate to Section 0. INPUT: Assignment Contract
3. For each REQUIRED input in 0.1:
   - Verify the value is provided above
   - Copy the value into the "Actual Value" column
   - Update Status column: PENDING → PASS if provided, PENDING → FAIL if missing
4. For OPTIONAL inputs in 0.2:
   - Fill defaults where applicable
   - Mark Status: PENDING → PASS or PENDING → N/A

⚠️ STOP_GATE: If ANY required input has Status = FAIL, STOP immediately.
   Output: "CHECKPOINT-0: BLOCKED — missing required input: {input_name}"

SECTION 1 — SCRIPT IDENTITY:
5. Read the script at SCRIPT_PATH
6. Fill the identity table in Section 1:
   - Name: extract from filename
   - Path: use SCRIPT_PATH
   - Tier Class: determine from script location/purpose
   - Compliance Tier: use COMPLIANCE_TIER provided
   - Lines: count lines in file
   - Record ID: use RECORD_ID provided
   - Planned Stage: use TARGET_STAGE provided

7. Complete Section 1.1 DESCRIBE: Write 1-2 sentence purpose statement
8. Complete Section 1.2 LIST: Extract 3-5 current capabilities from code
9. Add verification log entry in 1.3

PROCEED_SIGNAL when done:
"CHECKPOINT-0: Inputs verified — SCRIPT_PATH, RECORD_ID, COMPLIANCE_TIER, TARGET_STAGE confirmed"
"CHECKPOINT-1: Script identity captured — {SCRIPT_NAME} is Tier {A/B}"
```

**Human verification checklist:**

- [ ] All required inputs have Status = PASS
- [ ] Identity table is fully populated
- [ ] Purpose statement matches actual script behavior
- [ ] Capabilities list is accurate

**If FAIL:** Re-deliver PROMPT-01-SETUP with corrected inputs.

---

## PROMPT-2A-ANALYZE

<!-- TEMPLATE_SECTIONS: 2.1, 2.2, 2.3, 2.4 -->
<!-- CHECKPOINT_IDS: CHECKPOINT-2A -->
<!-- STOP_GATE: FALSE -->
<!-- ESTIMATED_TIME: 20-30 minutes -->
<!-- TIER_CHECK: If COMPLIANCE_TIER == "B", skip sections 2.2.2(Tier A), 2.3, 2.4.2 -->

**Delivers to agent:**

```text
TASK: Analyze script structure and compliance.

BUILD_DOC: {path to build document}
SCRIPT_PATH: {path to target script}
COMPLIANCE_TIER: {A or B}

INSTRUCTIONS:

SECTION 2.1 — CLI INTERFACE:
1. Get CLI help output:

   **Python invocation (try in order until one works):**
   ```python
   import subprocess
   import sys
   
   # Use the same Python that's running this script
   result = subprocess.run(
       [sys.executable, SCRIPT_PATH, '--help'],
       capture_output=True, text=True
   )
   print(result.stdout or result.stderr)
   ```
   
   **Or from terminal (try in order):**
   - `python {SCRIPT_PATH} --help`
   - `python3 {SCRIPT_PATH} --help`
   - `.venv/Scripts/python.exe {SCRIPT_PATH} --help` (Windows venv)
   - `.venv/bin/python {SCRIPT_PATH} --help` (Unix venv)

2. Document the usage string in Section 2.1
3. Fill the Flags table with all CLI arguments

SECTION 2.2 — ENTRY POINTS:
4. Search for `def run(` and `def main(` in the script
5. Fill Section 2.2.1 tables with:
   - Function signatures
   - Return types
   - Expected payloads
6. Update Status for UIC-001 through UIC-003 based on findings

⚠️ TIER_CHECK: If COMPLIANCE_TIER == "B":
   - Skip Section 2.2.2 (Tier A Return Contract) — mark N/A
   - Skip Section 2.3 (Output Files)
   - Skip Section 2.4.2 (HOP Package Requirements)

SECTION 2.3 — OUTPUT FILES (Tier A only):
7. List all files the script creates
8. Document output structure and format

SECTION 2.4 — COMPLIANCE ASSESSMENT:
9. Complete Section 2.4.1 UIC checklist:
   - Run code inspection for each requirement
   - Record evidence with path:line references
   - Mark Status as PASS, FAIL, or N/A
10. Complete Section 2.4.2 HOP checklist (Tier A only):
    - Verify manifest/summary/telemetry generation
    - Check for build_topic_path() or create_storage() usage
    - Verify prune_run_directories() implementation

PROCEED_SIGNAL when done:
"CHECKPOINT-2A: Static analysis complete — UIC checklist has {X} PASS, {Y} FAIL"
```

**Human verification checklist:**

- [ ] CLI documentation matches actual --help output
- [ ] Entry point signatures verified against code
- [ ] All applicable UIC checks have evidence
- [ ] Tier B skips are properly marked N/A

**If FAIL:** Re-deliver PROMPT-2A-ANALYZE for specific sections needing correction.

---

## PROMPT-2B-VERIFY

<!-- TEMPLATE_SECTIONS: 2.5 -->
<!-- CHECKPOINT_IDS: CHECKPOINT-2B -->
<!-- STOP_GATE: TRUE -->
<!-- ESTIMATED_TIME: 30-45 minutes -->
<!-- TIER_CHECK: If COMPLIANCE_TIER == "B", skip sections 2.5.2, 2.5.3 -->

**Delivers to agent:**

```text
TASK: Execute script and verify output truth.

BUILD_DOC: {path to build document}
SCRIPT_PATH: {path to target script}
COMPLIANCE_TIER: {A or B}

⚠️ THIS IS A MANDATORY STOP-GATE — OUTPUT TRUTH MUST BE VERIFIED

INSTRUCTIONS:

SECTION 2.5.1 — QA VERIFICATION:

**FIRST: Discover required flags:**
```python
import subprocess
result = subprocess.run(['python', '{SCRIPT_PATH}', '--help'], capture_output=True, text=True)
print(result.stdout)
# Look for "required arguments" or flags without [brackets] (optional)
```

1. Execute the script with appropriate parameters:
   - **Minimum:** `python {SCRIPT_PATH} --repo-root . --log-level DEBUG`
   - **If --target required:** Add `--target <appropriate_path>` (check --help output)
   - **If other flags required:** Add them based on --help output

   > **Timeout guidance:** If script runs >5 minutes, consider:
   > - Adding `--dry-run` flag if available
   > - Running in background: `python {SCRIPT_PATH} ... &`
   > - Documenting in Section 2.5.1 that full execution was skipped due to time

2. For each check in 2.5.1 QA table:
   - Run the verification command
   - Record actual result
   - Update Status: PASS or FAIL
   - Add CI/Artifact link if available

SECTION 2.5.2 — OUTPUT INSPECTION (Tier A only):
3. Locate the output directory created by the script
4. For each artifact in the output:
   - Read the file content
   - Document structure in 2.5.2 table
   - Verify content accuracy

SECTION 2.5.3 — ARTIFACT CONTENT SPOT-CHECK (Tier A only):
5. For manifest.json:
   - Verify all keys present
   - Check timestamps are valid
   - Confirm paths are correct
6. For summary.md:
   - Verify statistics match actual counts
   - Check all sections populated
7. For telemetry.json:
   - Verify metrics are numeric
   - Check for required fields

SECTION 2.5.4 — STRUCTURED OUTPUT (Tier A only):
8. Document the JSON structure returned by run()
9. Verify against expected schema

SECTION 2.5.5 — OUTPUT TRUTH TABLE:
⚠️ CRITICAL — EVERY CLAIM MUST BE TRUE

10. Identify claims to verify from script output:
    - Claims from summary.md (e.g., "42 files analyzed", "3 violations found")
    - Claims from manifest.json (e.g., output paths, record counts)
    - Claims from console output (e.g., "Written to X", "Completed in Y seconds")

11. For each claim, add a row to the Output Truth table:
    | Claim in Output | Verification Method | Ground Truth | Verdict |
    - "Claim in Output": Copy the exact claim text from script output
    - "Verification Method": How to verify (e.g., "wc -l on output file", "ls output dir")
    - "Ground Truth": What you actually observed (e.g., "43 lines counted", "file exists")
    - "Verdict": ✅ if claim matches truth, ❌ if claim is false

12. Execute each verification and fill the table

⚠️ STOP_GATE: If ANY verdict is ❌ (FALSE), the script is BROKEN.
   Output: "CHECKPOINT-2B: BLOCKED — output claim FALSE: {claim description}"
   Do NOT proceed. Document the discrepancy and await human decision.

PROCEED_SIGNAL when all verdicts ✅:
"CHECKPOINT-2B: Output truth verified — script executed, all claims TRUE"
```

**Human verification checklist:**

- [ ] Script was actually executed (not assumed)
- [ ] Output files exist at documented paths
- [ ] Truth table verdicts verified against actual state
- [ ] No FALSE verdicts in 2.5.5

**If FAIL:** Fix the script, then re-deliver PROMPT-2B-VERIFY from scratch.

---

## PROMPT-34-PREPARE

<!-- TEMPLATE_SECTIONS: 3, 4 -->
<!-- CHECKPOINT_IDS: CHECKPOINT-3, CHECKPOINT-4 -->
<!-- STOP_GATE: FALSE -->
<!-- ESTIMATED_TIME: 15-20 minutes -->

**Delivers to agent:**

```text
TASK: Verify Tier-3 YAML and database integration readiness.

BUILD_DOC: {path to build document}
SCRIPT_PATH: {path to target script}
SCRIPT_NAME: {script filename without extension}

INSTRUCTIONS:

SECTION 3 — TIER-3 YAML:
1. Check for Tier-3 YAML file at:
   {SCRIPT_DIR}/{SCRIPT_NAME}.tier3.yaml

2. If file exists:
   - Validate YAML syntax: python -c "import yaml; yaml.safe_load(open('{path}'))"
   - Fill Section 3.1 table with Status = PASS
   - Verify Section 3.2 required fields against actual content
   - Mark each field Status as PASS or FAIL

3. If file does NOT exist:
   - Create it using Section 3.3 REFERENCE: Tier-3 YAML Template as your guide
   - The template shows all required fields with example values
   - Fill all fields based on script analysis from PROMPT-2A
   - Re-verify Section 3.1 and 3.2

4. Add verification log entry in Section 3 log

SECTION 4 — DATABASE INTEGRATION:
5. Document DB schema intent in Section 4.1:
   - What data would this script write to DB?
   - Which tables/collections would receive data?

6. Complete Section 4.2 DB Integration Checklist:
   - Search script for create_storage() usage
   - Search for DB_INTEGRATION_MARKER comments
   - Check for storage.write_* calls
   - Mark Status: PASS, FAIL, or N/A for each item

7. If script lacks DB integration markers:
   - Document where markers should be added in Section 4.3
   - Create a GAP entry for Section 5

8. Add verification log entry in Section 4.4

PROCEED_SIGNAL when done:
"CHECKPOINT-3: Tier-3 YAML verified at {tier3_path}"
"CHECKPOINT-4: DB integration markers present — {count} write points covered"
```

**Human verification checklist:**

- [ ] Tier-3 YAML exists and is valid
- [ ] All required fields populated in YAML
- [ ] DB integration documented or N/A justified

**If FAIL:** Re-deliver PROMPT-34-PREPARE with specific guidance on missing items.

---

## PROMPT-5-GAPS

<!-- TEMPLATE_SECTIONS: 5 -->
<!-- CHECKPOINT_IDS: CHECKPOINT-5 -->
<!-- STOP_GATE: FALSE -->
<!-- ESTIMATED_TIME: 15-25 minutes -->

**Delivers to agent:**

```text
TASK: Identify and document all compliance gaps.

BUILD_DOC: {path to build document}
COMPLIANCE_TIER: {A or B}

INSTRUCTIONS:

SECTION 5 — GAP IDENTIFICATION:

1. Review all sections completed so far (0-4):
   - Any Status = FAIL in UIC checklist? → Create gap
   - Any Status = FAIL in HOP checklist? → Create gap
   - Any missing DB integration markers? → Create gap
   - Any Tier-3 YAML fields missing? → Create gap

2. Navigate to Section 5.1 LIST: Required Changes

3. DELETE all example rows (GAP-001 through GAP-017):
   ⚠️ These are EXAMPLES only — remove before adding real gaps
   HOW TO DELETE:
   - Select each table row from GAP-001 through GAP-017
   - Delete the entire line (including the | pipe characters)
   - Keep the table header row intact
   - You should have an empty table with just headers when done

4. For each actual gap found:
   - Assign sequential Gap ID (GAP-001, GAP-002, etc.) — reuse IDs from deleted examples
   - Link to Req ID (UIC-001, HOP-003, etc.)
   - Write clear description
   - Assign Priority: HIGH (blocks compliance), MEDIUM (should fix), LOW (nice to have)
   - Set Status: OPEN

5. Document gaps in appropriate subsection:
   - 5.1.1 Universal Compliance Gaps (UIC requirements)
   - 5.1.2 HOP Package Gaps (Tier A only)
   - 5.1.3 DB Integration Gaps
   - 5.1.4 Documentation Gaps
   - 5.1.5 Testing Gaps
   - 5.1.6 Orchestrator Gaps

6. To mark a subsection as N/A:
   - Add this text directly below the subsection heading:
     > **N/A** — {reason, e.g., "Script is Tier B; HOP package not required"}
   - Leave the subsection table empty or remove it

7. Add verification log entry

⚠️ IMPORTANT: If COMPLIANCE_TIER == "B", mark 5.1.2 as N/A

PROCEED_SIGNAL when done:
"CHECKPOINT-5: Gap analysis complete — {X} HIGH, {Y} MEDIUM, {Z} total gaps"
```

**Human verification checklist:**

- [ ] All example rows deleted
- [ ] Gaps trace back to actual FAIL statuses
- [ ] HIGH priority gaps are genuine blockers
- [ ] No gaps invented without evidence

**If FAIL:** Re-deliver PROMPT-5-GAPS with clarification on gap categorization.

---

## PROMPT-67-EVIDENCE

<!-- TEMPLATE_SECTIONS: 6, 7 -->
<!-- CHECKPOINT_IDS: CHECKPOINT-6, CHECKPOINT-7 -->
<!-- STOP_GATE: FALSE -->
<!-- ESTIMATED_TIME: 20-30 minutes (depends on number of changes) -->

**Delivers to agent:**

```text
TASK: Record changes made and capture evidence.

BUILD_DOC: {path to build document}
SCRIPT_PATH: {path to target script}

⚠️ PREREQUISITE: This prompt assumes gaps from Section 5 have been FIXED.
   If gaps are still OPEN, fix them first, then run this prompt.

INSTRUCTIONS:

SECTION 6 — RECORD CHANGES:

1. For each gap that was fixed:
   - Add row to Section 6.1 Change Log table
   - Fill all columns:
     * #: Sequential number
     * Category: Entry Point / CLI Flags / Return Contract / etc.
     * Location: path:line reference
     * Description: What was changed
     * Gap ID(s) Resolved: Link to GAP-XXX from Section 5
     * Commit SHA: Git commit hash (if committed), or "UNCOMMITTED" if not yet committed

2. Delete the example row comment block

3. For each change, update corresponding gap in Section 5:
   - Change Status: OPEN → CLOSED
   - Add Closed Date

4. Add verification log entry in 6.2

SECTION 7 — CAPTURE EVIDENCE:

5. Run all tests related to this script:
   pytest {test_file} -v

6. Fill Section 7.1 Tests table:
   - Test File: path to test file
   - Test Name: specific test function
   - Result: PASS or FAIL
   - Commit SHA: Current commit, or "UNCOMMITTED" if working copy has uncommitted changes
   - CI Link: CI run URL if available

7. Document code references in Section 7.2:
   - Key functions: path:start-end
   - Important logic blocks
   - Integration points

8. Add verification log entry in 7.3

PROCEED_SIGNAL when done:
"CHECKPOINT-6: {N} changes recorded with commit references"
"CHECKPOINT-7: Evidence captured — {X} tests, {Y} code references"
```

**Human verification checklist:**

- [ ] All changes link to Gap IDs
- [ ] Commit SHAs are real (not placeholder)
- [ ] Tests actually ran (check for test output)
- [ ] Code references point to real locations

**If FAIL:** Re-deliver PROMPT-67-EVIDENCE with specific sections to complete.

---

## PROMPT-8-ORCHESTRATOR

<!-- TEMPLATE_SECTIONS: 8 -->
<!-- CHECKPOINT_IDS: CHECKPOINT-8 -->
<!-- STOP_GATE: FALSE -->
<!-- ESTIMATED_TIME: 10-15 minutes -->

**Delivers to agent:**

```text
TASK: Configure orchestrator integration.

BUILD_DOC: {path to build document}
SCRIPT_PATH: {path to target script}
SCRIPT_NAME: {script name}

INSTRUCTIONS:

SECTION 8 — ORCHESTRATOR INTEGRATION:

1. Read Section 8.1 safety warning about supports_output_dir
   ⚠️ Default to False unless you have a specific reason

2. Fill Section 8.2 ScriptConfig table:
   - script_id: Use SCRIPT_NAME
   - entry_point: Usually "run"
   - supports_output_dir: False (default) or True (with justification)
   - supports_log_level: True if --log-level flag exists
   - timeout_seconds: Estimate based on script complexity
   - retry_on_failure: True for network/IO operations
   - max_retries: Usually 2-3

3. Complete Section 8.3 Orchestrator Readiness Checklist:
   - Verify each requirement against actual code
   - Mark Status: PASS, FAIL, or N/A
   - Add evidence with path:line references

4. If any 8.3 checks are FAIL:
   - Document what needs to change
   - Create gap entry in Section 5 if not already present

5. Add verification log entry in 8.4

PROCEED_SIGNAL when done:
"CHECKPOINT-8: Orchestrator config ready — ScriptConfig documented"
```

**Human verification checklist:**

- [ ] supports_output_dir is False (or justified if True)
- [ ] All readiness checks have evidence
- [ ] ScriptConfig values are reasonable

**If FAIL:** Re-deliver PROMPT-8-ORCHESTRATOR with specific corrections.

---

## PROMPT-910-CLOSE

<!-- TEMPLATE_SECTIONS: 9, 10 -->
<!-- CHECKPOINT_IDS: CHECKPOINT-9, CHECKPOINT-10 -->
<!-- STOP_GATE: TRUE -->
<!-- ESTIMATED_TIME: 10-15 minutes -->

**Delivers to agent:**

```text
TASK: Complete attestation and finalize build document.

BUILD_DOC: {path to build document}
ASSIGNEE: {your name or agent ID}
DATE: {today's date YYYY-MM-DD}

⚠️ THIS IS THE FINAL STOP-GATE — ALL PREVIOUS CHECKPOINTS MUST BE COMPLETE

INSTRUCTIONS:

PRE-CHECK — VERIFY ALL CHECKPOINTS:
1. Search the build document for each checkpoint signal. Use this command:
   
   from pathlib import Path
   doc = Path('{BUILD_DOC}').read_text()
   for cp in ['CHECKPOINT-0', 'CHECKPOINT-1', 'CHECKPOINT-2A', 'CHECKPOINT-2B', 
              'CHECKPOINT-3', 'CHECKPOINT-4', 'CHECKPOINT-5', 'CHECKPOINT-6',
              'CHECKPOINT-7', 'CHECKPOINT-8']:
       if cp in doc:
           print(f"✅ {cp} found")
       else:
           print(f"❌ {cp} MISSING")

2. Verify the verification log in each section shows completion:
   - CHECKPOINT-0: Section 0.3 verification log entry exists
   - CHECKPOINT-1: Section 1.3 verification log entry exists
   - CHECKPOINT-2A: Section 2.4 verification log entry exists
   - CHECKPOINT-2B: Section 2.5.5 truth table filled + log entry
   - CHECKPOINT-3: Section 3 verification log entry exists
   - CHECKPOINT-4: Section 4.4 verification log entry exists
   - CHECKPOINT-5: Section 5 verification log entry exists
   - CHECKPOINT-6: Section 6.2 verification log entry exists
   - CHECKPOINT-7: Section 7.3 verification log entry exists
   - CHECKPOINT-8: Section 8.4 verification log entry exists

⚠️ STOP_GATE: If any checkpoint is incomplete, do NOT proceed.
   Output: "CHECKPOINT-9: BLOCKED — prerequisite incomplete: {checkpoint}"

SECTION 9 — ATTESTATION:

2. Fill Section 9.1 Attestation Record table:
   - Inspector: {ASSIGNEE}
   - Date: {DATE}
   - Signature/ID: Your agent ID or initials

3. Complete Section 9.2 Attestation Statement:
   - Check each checkbox ONLY if the statement is TRUE
   - Do NOT check boxes for unverified claims

4. Add attestation date at bottom of 9.2

SECTION 10 — FINALIZE:

5. Complete Section 10.1 checklist:
   - Go through EVERY checkbox
   - Mark checked ONLY if actually verified
   - For unchecked items, document why

═══════════════════════════════════════════════════════════════════
SECTION 10.2 — TIER-2 ROSTER UPDATE (MANDATORY)
═══════════════════════════════════════════════════════════════════

⚠️ THIS IS AN EXTERNAL FILE UPDATE — You must EDIT the roster file, not just check boxes in this build document.

**Step 6a. Locate the Tier-2 roster file:**

Use the stage from Section 0.1 to find the roster:
```python
# Stage-to-roster mapping
ROSTER_MAP = {
    "1.1": "tier2_test_execution_telemetry_roster.md",
    "2.1": "tier2_docs_health_overview_roster.md",
    "3.1": "tier2_fault_diagnostics_overview_roster.md",
    "4.1": "tier2_dependency_import_hygiene_roster.md",
    "5.1": "tier2_monkey_patch_oversight_roster.md",
    "6.1": "tier2_standards_integrity_roster.md",
    "10.1": "tier2_full_suite_overview_roster.md",
    "11.1": "tier2_available_scripts_roster.md",
}
roster_path = f"{HOP_ROOT}/tier2_roster/{ROSTER_MAP[TARGET_STAGE]}"
```

**Step 6b. Open the Tier-2 roster file and find the script's record:**

- Search for `{SCRIPT_NAME}` in the roster
- Navigate to the "Implementation Workstreams" section for this script
- If no section exists for this script, CREATE one using the standard format

**Step 6c. UPDATE the workstream checkboxes:**

Find the checkbox section and REPLACE with completed state:
```markdown
#### Implementation Workstreams — {SCRIPT_NAME}

- [x] A. Discovery — CLI surfaces, outputs, retention, consumers documented
- [x] B. Plan — gap closure plan drafted (or N/A if already compliant)
- [x] C. Implement — code changes applied (or N/A if already compliant)
- [x] D. Evidence — tests passing, static analysis verified
- [x] E. Bug fix — issues addressed (or N/A if none found)
- [x] F. Output truth verification — script executed, output claims verified TRUE
- [x] G. Tier-3 YAML — created/updated at {TIER3_PATH}
- [x] H. Orchestrator integration — ScriptConfig documented
- [x] **DONE** — Phase 4 compliance complete ({DATE})

**Build Document:** `{BUILD_DOC_PATH}`
**Tier-3 YAML:** `{TIER3_PATH}`
```

⚠️ If the existing section is formatted incorrectly, REPLACE THE ENTIRE SECTION with the correct format above.

**Step 6d. SAVE the Tier-2 roster file**

**Step 6e. Return to THIS build document and verify Section 10.2 checklist is complete**

PROCEED_SIGNAL: "Tier-2 roster updated at {roster_path}"

═══════════════════════════════════════════════════════════════════
SECTION 10.3 — TIER-1 PIPELINE REGISTRY UPDATE (MANDATORY)
═══════════════════════════════════════════════════════════════════

⚠️ THIS IS AN EXTERNAL FILE UPDATE — You must EDIT the Tier-1 pipeline document.

**Step 7a. Locate the Tier-1 pipeline document:**

```
{HOP_ROOT}/tier1_healthview_orchestration_pipeline.md
```

**Step 7b. Find the script registry section:**

Search for the "Script Registry" or "Available Scripts" table in the Tier-1 document.

**Step 7c. UPDATE or ADD the script entry:**

- If script exists in registry: UPDATE its row
- If script does NOT exist: ADD a new row

Registry entry format:

| Script | Record ID | Stage | Tier | Status | Build Doc | Last Verified |
|--------|-----------|-------|------|--------|-----------|---------------|
| {SCRIPT_NAME} | {RECORD_ID} | {TARGET_STAGE} | {COMPLIANCE_TIER} | ✅ Phase 4 Complete | {BUILD_DOC_PATH} | {DATE} |

**Step 7d. SAVE the Tier-1 pipeline document**

PROCEED_SIGNAL: "Tier-1 registry updated — {SCRIPT_NAME} marked Phase 4 Complete"

═══════════════════════════════════════════════════════════════════
SECTION 10.4 — FINAL CLEANUP
═══════════════════════════════════════════════════════════════════

8. Search entire document for <PLACEHOLDER> or <PENDING>:
   - Replace all remaining placeholders with actual values
   - If any cannot be filled, document why

9. Update frontmatter:
   - status: complete
   - updated_at: {DATE}

⚠️ STOP_GATE: If any checkbox cannot be checked, document the blocker.
   Output: "CHECKPOINT-10: BLOCKED — cannot finalize: {reason}"

PROCEED_SIGNAL when complete:
"CHECKPOINT-9: Attestation complete — signed by {ASSIGNEE} on {DATE}"
"CHECKPOINT-10: PHASE 4 COMPLETE — {RECORD_ID} ready for production"
"PROPAGATION: Tier-2 roster updated, Tier-1 registry updated"
```

**Human verification checklist:**

- [ ] All attestation checkboxes represent truth
- [ ] No <PLACEHOLDER> remains in document
- [ ] Frontmatter shows status: complete
- [ ] Tier-2 roster file was actually modified (not just claimed)
- [ ] Tier-1 registry was actually modified (not just claimed)
- [ ] Document can be archived

**If FAIL:** Re-deliver PROMPT-910-CLOSE after resolving blockers.

---

## Recovery: Re-Entry Points

If a checkpoint fails, use these re-entry points:

| Failed Checkpoint | Re-Entry Point | Instructions |
|-------------------|----------------|--------------|
| CHECKPOINT-0 | PROMPT-01-SETUP | Provide missing inputs |
| CHECKPOINT-1 | PROMPT-01-SETUP | Re-verify identity |
| CHECKPOINT-2A | PROMPT-2A-ANALYZE | Fix specific failing checks |
| CHECKPOINT-2B | PROMPT-2B-VERIFY | Fix script, re-verify from scratch |
| CHECKPOINT-3 | PROMPT-34-PREPARE | Create/fix Tier-3 YAML |
| CHECKPOINT-4 | PROMPT-34-PREPARE | Add DB integration markers |
| CHECKPOINT-5 | PROMPT-5-GAPS | Re-analyze gaps |
| CHECKPOINT-6 | PROMPT-67-EVIDENCE | Record missing changes |
| CHECKPOINT-7 | PROMPT-67-EVIDENCE | Capture missing evidence |
| CHECKPOINT-8 | PROMPT-8-ORCHESTRATOR | Fix orchestrator config |
| CHECKPOINT-9 | PROMPT-910-CLOSE | Complete prerequisite checkpoints |
| CHECKPOINT-10 | PROMPT-910-CLOSE | Resolve finalization blockers |

---

## Quick Reference: Checkpoint Signals

| Checkpoint | Signal Pattern |
|------------|----------------|
| CHECKPOINT-0 | "CHECKPOINT-0: Inputs verified — SCRIPT_PATH, RECORD_ID, COMPLIANCE_TIER, TARGET_STAGE confirmed" |
| CHECKPOINT-1 | "CHECKPOINT-1: Script identity captured — {SCRIPT_NAME} is Tier {A/B}" |
| CHECKPOINT-2A | "CHECKPOINT-2A: Static analysis complete — UIC checklist has {X} PASS, {Y} FAIL" |
| CHECKPOINT-2B | "CHECKPOINT-2B: Output truth verified — script executed, all claims TRUE" |
| CHECKPOINT-3 | "CHECKPOINT-3: Tier-3 YAML verified at {tier3_path}" |
| CHECKPOINT-4 | "CHECKPOINT-4: DB integration markers present — {count} write points covered" |
| CHECKPOINT-5 | "CHECKPOINT-5: Gap analysis complete — {X} HIGH, {Y} MEDIUM, {Z} total gaps" |
| CHECKPOINT-6 | "CHECKPOINT-6: {N} changes recorded with commit references" |
| CHECKPOINT-7 | "CHECKPOINT-7: Evidence captured — {X} tests, {Y} code references" |
| CHECKPOINT-8 | "CHECKPOINT-8: Orchestrator config ready — ScriptConfig documented" |
| CHECKPOINT-9 | "CHECKPOINT-9: Attestation complete — signed by {ASSIGNEE} on {DATE}" |
| CHECKPOINT-10 | "CHECKPOINT-10: PHASE 4 COMPLETE — {RECORD_ID} ready for production" |

---

## Tier B Express Path

For **Tier B (Action Utility)** scripts, these sections are skipped or marked N/A:

| Section | Tier B Action |
|---------|---------------|
| 2.2.2 Tier A Return Contract | Skip — mark N/A |
| 2.3 Output Files | Skip — mark N/A |
| 2.4.2 HOP Package Requirements | Skip — mark N/A |
| 2.5.2 Output Inspection | Skip — mark N/A |
| 2.5.3 Artifact Spot-Check | Skip — mark N/A |
| 5.1.2 HOP Package Gaps | Skip — mark N/A |

**Estimated Tier B completion time:** 1.5-2 hours (vs 2.5-3 hours for Tier A)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.1.1 | 2026-02-02 | PROMPT-2A: Added flexible Python invocation with `sys.executable` and fallback commands for venv environments |
| 1.1.0 | 2026-02-02 | Relocated from `producer/` to `common/` — now shared by all script classes; updated title, description, and related_files to reflect class-agnostic usage |
| 1.0.1 | 2026-02-02 | Fixed path conflict: Pre-Flight now uses `tier2_roster/working_docs/stage_{STAGE}/` to match BOOTSTRAP.md; added guidance for BOOTSTRAP flow vs manual creation |
| 1.0.0 | 2026-02-01 | Initial release with 8 prompts aligned to template v3.4.0 |
