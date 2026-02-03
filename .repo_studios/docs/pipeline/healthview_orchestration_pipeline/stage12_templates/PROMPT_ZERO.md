---
title: "Prompt Zero — First Contact"
tier: metaprompt
audience:
  - human_operator
  - coding_agent
  - autonomous_system
status: active
version: 2.0.0
updated_at: 2026-02-02
template_version: "3.4.0"
related_files:
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/stage12_templates/BOOTSTRAP.md
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/stage12_templates/manifest.yaml
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/stage12_templates/common/review_metaprompts.md
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/stage12_templates/PROMPT_PHASE1_BOOTSTRAP.md
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/stage12_templates/PROMPT_PHASE2_ANALYSIS.md
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/stage12_templates/PROMPT_PHASE3_EVIDENCE.md
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/stage12_templates/PROMPT_PHASE4_FINALIZE.md
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/stage_prefix_index.yaml
---

# PROMPT ZERO — First Contact

> **For humans:** Deliver Phase 1 first, verify, then deliver Phase 2, etc.
> **For trained agents:** Execute ONE PHASE at a time, STOP after each.
> **For autonomous systems:** NOT RECOMMENDED — human verification required between phases.

---

## ════════════════════════════════════════════════════════════════
## ⚠️ MAJOR CHANGE: 4-PHASE WORKFLOW (v2.0.0)
## ════════════════════════════════════════════════════════════════

**This system now uses a 4-phase workflow with human verification between phases.**

### Why We Made This Change

In live testing with v1.x (single-prompt workflow), we observed critical failures:

| Failure | What Happened |
|---------|---------------|
| **STOP_GATEs ignored** | LLMs cannot pause mid-response; they run through gates |
| **False completion claims** | Agent checked "Tier-2 updated" without editing the file |
| **Attention degradation** | Quality dropped in later sections of long responses |
| **Wrong Record IDs** | Agent generated IDs without checking roster for existing assignments |

**The 4-phase architecture fixes these by forcing human verification between phases.**

### The 4-Phase Architecture

| Phase | File | Checkpoints | Human Verifies |
|-------|------|-------------|----------------|
| **1: Bootstrap** | `PROMPT_PHASE1_BOOTSTRAP.md` | 0, 1 | Build doc created, correct ID |
| **2: Analysis** | `PROMPT_PHASE2_ANALYSIS.md` | 2A, 2B, 3, 4 | Script actually executed |
| **3: Evidence** | `PROMPT_PHASE3_EVIDENCE.md` | 5, 6, 7, 8 | Gaps real, evidence specific |
| **4: Finalize** | `PROMPT_PHASE4_FINALIZE.md` | 9, 10 | Git diff proves updates |

### Workflow Diagram

```text
┌─────────────────────────────────────────────────────────────────┐
│  HUMAN: Deliver Phase 1 prompt + script path                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  AGENT: Execute Phase 1 → CHECKPOINT-0, CHECKPOINT-1            │
│  AGENT: Output "PHASE 1 COMPLETE — AWAITING HUMAN VERIFICATION" │
│  AGENT: *** STOP ***                                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  HUMAN: Verify build doc exists, Record ID correct              │
│  HUMAN: Deliver Phase 2 prompt                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  AGENT: Execute Phase 2 → CHECKPOINT-2A, 2B, 3, 4               │
│  AGENT: Output "PHASE 2 COMPLETE — AWAITING HUMAN VERIFICATION" │
│  AGENT: *** STOP ***                                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  HUMAN: Verify script was executed, output truth has evidence   │
│  HUMAN: Deliver Phase 3 prompt                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  AGENT: Execute Phase 3 → CHECKPOINT-5, 6, 7, 8                 │
│  AGENT: Output "PHASE 3 COMPLETE — AWAITING HUMAN VERIFICATION" │
│  AGENT: *** STOP ***                                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  HUMAN: Verify gaps are real, evidence has line numbers         │
│  HUMAN: Deliver Phase 4 prompt                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  AGENT: Execute Phase 4 → CHECKPOINT-9, 10 with GIT DIFF PROOF  │
│  AGENT: Output "PHASE 4 COMPLETE — AWAITING FINAL VERIFICATION" │
│  AGENT: *** STOP ***                                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  HUMAN: Verify git diff shows Tier-2 + Tier-1 actually updated  │
│  HUMAN: Commit changes                                          │
│  ✅ INSPECTION COMPLETE                                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## PREREQUISITES

**Before starting, confirm your agent has these capabilities:**

- [ ] **File system access** — Can read and write files in the repository
- [ ] **Terminal execution** — Can run Python scripts and shell commands
- [ ] **File creation** — Can create new markdown files
- [ ] **Git access** — Can run `git diff` to verify changes (required for Phase 4)

**If ANY capability is missing:**

```text
STOP. This workflow requires all four capabilities.
Inform the human which capability is unavailable.
```

---

## CONTEXT (First-time users read this)

### Path Constants

> **HOP_ROOT:** `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/`
>
> All paths in this document are relative to repository root unless prefixed with `./` or `../`.
> When a path starts with `stage12_templates/` or `tier2_roster/`, prepend HOP_ROOT.

### What Is This System?

This is the **HealthView Orchestration Pipeline (HOP)** script inspection system. It provides
a structured workflow to:

1. **Inspect** existing Python scripts for compliance
2. **Document** their capabilities, contracts, and gaps
3. **Prepare** them for orchestrator integration
4. **Attest** that inspection was conducted properly

### Where Are The Files?

```text
.repo_studios/docs/pipeline/healthview_orchestration_pipeline/
├── stage12_templates/           ← Templates and metaprompts
│   ├── PROMPT_ZERO.md          ← YOU ARE HERE
│   ├── BOOTSTRAP.md            ← Discovery and build doc creation
│   ├── PROMPT_PHASE1_BOOTSTRAP.md  ← Phase 1 instructions
│   ├── PROMPT_PHASE2_ANALYSIS.md   ← Phase 2 instructions
│   ├── PROMPT_PHASE3_EVIDENCE.md   ← Phase 3 instructions
│   ├── PROMPT_PHASE4_FINALIZE.md   ← Phase 4 instructions
│   ├── manifest.yaml           ← Machine-readable template registry
│   ├── common/                 ← Shared templates (review_metaprompts.md)
│   ├── producer/               ← Producer-specific templates
│   │   └── build_template.md   ← The inspection form
│   ├── consumer/
│   ├── aggregator/
│   └── ...
├── tier2_roster/
│   ├── stage_prefix_index.yaml ← Stage/prefix mappings
│   ├── tier2_docs_health_overview_roster.md ← Stage 2.1 roster
│   └── working_docs/           ← Where build documents live
│       ├── stage_1_1/          ← TER-* records
│       ├── stage_2_1/          ← S21R-* records
│       └── stage_11_1/         ← ASR-* records
├── tier1_healthview_orchestration_pipeline.md ← Master registry
```

### What Is The Goal?

Transform a script from "exists in repo" to "production-ready with documentation":

```text
BEFORE: Script exists, undocumented, unknown compliance status
AFTER:  Build doc complete, Tier-3 YAML exists, orchestrator-ready
```

### How Long Does This Take?

| Script Complexity | Compliance Tier | Estimated Time |
|-------------------|-----------------|----------------|
| Simple utility | Tier B | 1.5-2 hours (4 phases) |
| Standard producer | Tier A | 2.5-3 hours (4 phases) |
| Complex orchestrator | Tier A | 3.5-4.5 hours (4 phases) |

**Note:** Times include human verification between phases (~5-10 min per phase).

---

## MODES

Choose your mode based on your situation:

| Mode | Status | Best For |
|------|--------|----------|
| **A: SINGLE** | ✅ Ready (4-phase) | One specific script to inspect |
| **B: DISCOVERY** | 🔜 Coming Soon | Find scripts needing inspection |
| **C: RESUME** | ✅ Ready | Continue interrupted inspection at any phase |
| **D: BATCH** | 🔜 Coming Soon | Process multiple scripts in sequence |

---

### Mode A: SINGLE ✅ (4-Phase Workflow)

**Use when:** You have one specific script to inspect.

**⚠️ This mode now uses the 4-phase workflow.** You will deliver 4 separate prompts
with verification between each phase.

**Step 1:** Copy the Phase 1 BEGIN block below
**Step 2:** Replace `<PASTE YOUR SCRIPT PATH HERE>` with your script path
**Step 3:** Deliver to agent
**Step 4:** When Phase 1 completes, verify and deliver Phase 2, etc.

---

### Mode B: DISCOVERY 🔜 Coming Soon

> **Status:** Not yet implemented in BOOTSTRAP.md. Use SINGLE mode for now.

**Use when:** You don't know which scripts need inspection.

```text
MODE: DISCOVERY
SCOPE: <folder to search>
```

**Example:**
```text
MODE: DISCOVERY
SCOPE: .repo_studios/scripts/producers/
```

**Planned behavior:**
1. List all Python scripts in the scope
2. Check which have existing build documents
3. Present candidates for inspection
4. You select one to proceed

**Workaround:** Manually identify scripts, then use SINGLE mode.

---

### Mode C: RESUME ✅

**Use when:** You have an interrupted inspection to continue.

```text
MODE: RESUME
BUILD_DOC: <path to existing build document>
RESUME_AT_PHASE: <1|2|3|4>
```

**Example:**
```text
MODE: RESUME
BUILD_DOC: .repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/working_docs/stage_11_1/ASR-012_generate_lizard_report_build.md
RESUME_AT_PHASE: 2
```

**The agent will:**
1. Read the build document
2. Verify completed sections match the target phase
3. Execute the specified phase
4. STOP at the end of that phase for human verification

**Determining which phase to resume:**

| If these sections are complete... | Resume at Phase |
|-----------------------------------|-----------------|
| None or only frontmatter | 1 |
| Sections 1-4 (through Tier-3) | 2 (re-verify) or 3 |
| Sections 1-8 (through Orchestrator) | 4 |
| All sections | Already complete |

---

### Mode D: BATCH 🔜 Coming Soon

> **Status:** Not yet implemented in BOOTSTRAP.md. Use SINGLE mode repeatedly for now.

**Use when:** You have multiple scripts to inspect in sequence.

```text
MODE: BATCH
SCRIPT_PATHS:
  - <path 1>
  - <path 2>
  - <path 3>
```

**Example:**
```text
MODE: BATCH
SCRIPT_PATHS:
  - .repo_studios/scripts/producers/generate_lizard_report.py
  - .repo_studios/scripts/producers/validate_inventory.py
  - .repo_studios/scripts/consumers/analyze_test_hardening.py
```

The agent will:
1. Process scripts in order
2. Complete each inspection before starting the next
3. Report summary at the end

---

## PARAMETERS

**Minimum required input:**

| Parameter | Required | Description |
|-----------|----------|-------------|
| `MODE` | Yes | SINGLE, DISCOVERY, RESUME, or BATCH |
| `SCRIPT_PATH` | For SINGLE | Full path to script |
| `BUILD_DOC` | For RESUME | Path to existing build document |
| `SCOPE` | For DISCOVERY | Folder to search for scripts |
| `SCRIPT_PATHS` | For BATCH | List of script paths |

**Optional parameters:**

| Parameter | Default | Description |
|-----------|---------|-------------|
| `COMPLIANCE_TIER` | Auto-detect | Force A or B (skip detection) |
| `TARGET_STAGE` | Auto-assign | Force specific stage (skip matching) |
| `TEMPLATE_VERSION` | 3.4.0 | Use specific template version |
| `SKIP_EXISTING_CHECK` | false | Create new build doc even if one exists |

---

## EXPECTED DELIVERABLES

At the end of a successful inspection, you will have:

### 1. Build Document

Complete inspection record at:
```text
tier2_roster/working_docs/stage_{X.X}/{RECORD_ID}_{script}_build.md
```

### 2. Tier-3 YAML (if applicable)

Machine-readable metadata at:
```text
{script_dir}/{script_name}.tier3.yaml
```

### 3. Roster Entry

Script registered in the appropriate stage roster.

### 4. Final Confirmation

```text
"CHECKPOINT-10: PHASE 4 COMPLETE — {RECORD_ID} ready for production"
```

---

## BEGIN — PHASE 1 (Bootstrap + Setup)

**Copy everything below this line and deliver to your coding agent:**

---

```text
═══════════════════════════════════════════════════════════════════
SCRIPT INSPECTION REQUEST — PHASE 1
═══════════════════════════════════════════════════════════════════

MODE: SINGLE
SCRIPT_PATH: <PASTE YOUR SCRIPT PATH HERE>

═══════════════════════════════════════════════════════════════════
PHASE 1 INSTRUCTIONS
═══════════════════════════════════════════════════════════════════

Execute Phase 1 of the HealthView script inspection workflow.

Read these files FIRST:
1. .repo_studios/docs/pipeline/healthview_orchestration_pipeline/stage12_templates/BOOTSTRAP.md
2. .repo_studios/docs/pipeline/healthview_orchestration_pipeline/stage12_templates/PROMPT_PHASE1_BOOTSTRAP.md

PHASE 1 SCOPE:
- PROMPT-00-BOOTSTRAP: Discover script, assign stage, create build doc
- PROMPT-01-SETUP: Capture script identity, verify inputs

PHASE 1 CHECKPOINTS:
- CHECKPOINT-0: Bootstrap complete (build doc created, ID assigned)
- CHECKPOINT-1: Setup complete (script identity captured)

═══════════════════════════════════════════════════════════════════
EXECUTION RULES
═══════════════════════════════════════════════════════════════════

1. Check Tier-2 roster for existing script assignment BEFORE generating new ID
2. Output checkpoint signals as you complete each step
3. After CHECKPOINT-1, output "PHASE 1 COMPLETE — AWAITING HUMAN VERIFICATION"
4. *** STOP *** — Do NOT proceed to Phase 2

═══════════════════════════════════════════════════════════════════
BEGIN PHASE 1 NOW
═══════════════════════════════════════════════════════════════════
```

---

## PHASE 2 PROMPT (deliver after Phase 1 verified)

**Verify Phase 1 first:** Build doc exists, Record ID correct, Section 1 filled.

```text
═══════════════════════════════════════════════════════════════════
CONTINUE INSPECTION — PHASE 2
═══════════════════════════════════════════════════════════════════

BUILD_DOC: <PASTE BUILD DOC PATH FROM PHASE 1>

═══════════════════════════════════════════════════════════════════
PHASE 2 INSTRUCTIONS
═══════════════════════════════════════════════════════════════════

Read: .repo_studios/docs/pipeline/healthview_orchestration_pipeline/stage12_templates/PROMPT_PHASE2_ANALYSIS.md

PHASE 2 SCOPE (Sections 2-4):
- PROMPT-2A-ANALYZE: CLI, entry points, dependencies, compliance tier
- PROMPT-2B-VERIFY: Execute script, verify outputs (CRITICAL)
- PROMPT-34-PREPARE: Tier-3 YAML, DB integration markers

PHASE 2 CHECKPOINTS:
- CHECKPOINT-2A: Static analysis complete
- CHECKPOINT-2B: Output verification complete (MUST EXECUTE SCRIPT)
- CHECKPOINT-3: Tier-3 YAML complete
- CHECKPOINT-4: DB integration complete

After CHECKPOINT-4, output "PHASE 2 COMPLETE — AWAITING HUMAN VERIFICATION"
*** STOP *** — Do NOT proceed to Phase 3

═══════════════════════════════════════════════════════════════════
BEGIN PHASE 2 NOW
═══════════════════════════════════════════════════════════════════
```

---

## PHASE 3 PROMPT (deliver after Phase 2 verified)

**Verify Phase 2 first:** Script was actually executed, Output Truth has real evidence.

```text
═══════════════════════════════════════════════════════════════════
CONTINUE INSPECTION — PHASE 3
═══════════════════════════════════════════════════════════════════

BUILD_DOC: <PASTE BUILD DOC PATH>

═══════════════════════════════════════════════════════════════════
PHASE 3 INSTRUCTIONS
═══════════════════════════════════════════════════════════════════

Read: .repo_studios/docs/pipeline/healthview_orchestration_pipeline/stage12_templates/PROMPT_PHASE3_EVIDENCE.md

PHASE 3 SCOPE (Sections 5-8):
- PROMPT-5-GAPS: Gap analysis with priority assignment
- PROMPT-67-EVIDENCE: Changes made + evidence capture
- PROMPT-8-ORCHESTRATOR: Orchestrator readiness

PHASE 3 CHECKPOINTS:
- CHECKPOINT-5: Gap analysis complete (delete example rows!)
- CHECKPOINT-6: Changes documented
- CHECKPOINT-7: Evidence captured (with line numbers!)
- CHECKPOINT-8: Orchestrator config complete

After CHECKPOINT-8, output "PHASE 3 COMPLETE — AWAITING HUMAN VERIFICATION"
*** STOP *** — Do NOT proceed to Phase 4

═══════════════════════════════════════════════════════════════════
BEGIN PHASE 3 NOW
═══════════════════════════════════════════════════════════════════
```

---

## PHASE 4 PROMPT (deliver after Phase 3 verified)

**Verify Phase 3 first:** Gaps are real, evidence has line numbers, no placeholders.

```text
═══════════════════════════════════════════════════════════════════
CONTINUE INSPECTION — PHASE 4 (FINAL)
═══════════════════════════════════════════════════════════════════

BUILD_DOC: <PASTE BUILD DOC PATH>

═══════════════════════════════════════════════════════════════════
PHASE 4 INSTRUCTIONS
═══════════════════════════════════════════════════════════════════

Read: .repo_studios/docs/pipeline/healthview_orchestration_pipeline/stage12_templates/PROMPT_PHASE4_FINALIZE.md

PHASE 4 SCOPE (Sections 9-10):
- Attestation: Sign with agent ID and date
- Tier-2 Roster: ACTUALLY UPDATE the external file
- Tier-1 Registry: ACTUALLY UPDATE the external file
- Placeholder sweep: Verify no <PLACEHOLDER> text remains

⚠️ CRITICAL: You MUST produce git diff evidence proving you updated both files.

PHASE 4 CHECKPOINTS:
- CHECKPOINT-9: Attestation complete
- CHECKPOINT-10: Propagation complete (with GIT DIFF PROOF)

After CHECKPOINT-10, output:
1. Git diff for Tier-2 roster
2. Git diff for Tier-1 registry
3. Placeholder sweep results
4. "PHASE 4 COMPLETE — AWAITING FINAL VERIFICATION"

*** STOP *** — Await human to verify git diff and commit

═══════════════════════════════════════════════════════════════════
BEGIN PHASE 4 NOW
═══════════════════════════════════════════════════════════════════
```

---

## IF SOMETHING GOES WRONG

### To ABORT

Say to the agent:

```text
ABORT INSPECTION — Save current state.

Report:
1. Last successful checkpoint
2. Current section being worked
3. Any blocking issues
```

The agent will preserve progress in the build document.

### To RESUME

Use Mode C (RESUME) with the build document path:

```text
MODE: RESUME
BUILD_DOC: <path to the build document>
```

### Common Issues

| Problem | Solution |
|---------|----------|
| Agent doesn't recognize template | Ensure PYTHONPATH includes .repo_studios |
| Build doc not created | Check file system write permissions |
| Checkpoint signal not received | Ask: "What is the status of CHECKPOINT-X?" |
| Script classification wrong | Override with `COMPLIANCE_TIER: A` or `B` |
| Wrong stage assigned | Override with `TARGET_STAGE: X.X` |

---

## EXAMPLE SESSION (4-Phase Workflow)

### Phase 1: Human delivers

```text
═══════════════════════════════════════════════════════════════════
SCRIPT INSPECTION REQUEST — PHASE 1
═══════════════════════════════════════════════════════════════════

MODE: SINGLE
SCRIPT_PATH: .repo_studios/scripts/producers/generate_lizard_report.py

[... rest of Phase 1 prompt ...]
```

### Phase 1: Agent responds

```text
═══════════════════════════════════════════════════════════════════
PHASE 1 EXECUTING
═══════════════════════════════════════════════════════════════════

[... bootstrap steps ...]

═══════════════════════════════════════════════════════════════════
CHECKPOINT-0: BOOTSTRAP COMPLETE
═══════════════════════════════════════════════════════════════════
BUILD_DOC_PATH: tier2_roster/working_docs/stage_11_1/ASR-012_generate_lizard_report_build.md
RECORD_ID: ASR-012
SCRIPT_CLASS: producer
TARGET_STAGE: 11.1
ID_SOURCE: GENERATED

[... setup steps ...]

═══════════════════════════════════════════════════════════════════
CHECKPOINT-1: SETUP COMPLETE
═══════════════════════════════════════════════════════════════════
SCRIPT_NAME: generate_lizard_report.py
LINE_COUNT: 485
DOCSTRING_CAPTURED: yes
SECTION_1_STATUS: FILLED

═══════════════════════════════════════════════════════════════════
PHASE 1 COMPLETE
═══════════════════════════════════════════════════════════════════
CHECKPOINT-0: BOOTSTRAP COMPLETE ✓
CHECKPOINT-1: SETUP COMPLETE ✓

Build Document: tier2_roster/working_docs/stage_11_1/ASR-012_generate_lizard_report_build.md
Record ID: ASR-012
ID Source: GENERATED

PHASE 1 DELIVERABLES READY — AWAITING HUMAN VERIFICATION
═══════════════════════════════════════════════════════════════════
```

### Human verifies Phase 1:

- ✅ Build doc exists at the path
- ✅ Record ID ASR-012 not already in roster (GENERATED is valid)
- ✅ Section 1 has script identity filled

### Human delivers Phase 2:

```text
═══════════════════════════════════════════════════════════════════
CONTINUE INSPECTION — PHASE 2
═══════════════════════════════════════════════════════════════════

BUILD_DOC: tier2_roster/working_docs/stage_11_1/ASR-012_generate_lizard_report_build.md

[... rest of Phase 2 prompt ...]
```

### Phase 2: Agent responds

```text
═══════════════════════════════════════════════════════════════════
PHASE 2 EXECUTING
═══════════════════════════════════════════════════════════════════

[... analysis steps ...]

═══════════════════════════════════════════════════════════════════
CHECKPOINT-2B: OUTPUT VERIFICATION COMPLETE
═══════════════════════════════════════════════════════════════════
SCRIPT_EXECUTED: YES
EXIT_CODE: 0
BUNDLE_CREATED: YES
ARTIFACTS_VERIFIED: manifest.json, summary.md, telemetry.json
VERIFICATION_METHOD: ACTUAL_EXECUTION

[... Tier-3 and DB steps ...]

═══════════════════════════════════════════════════════════════════
PHASE 2 COMPLETE
═══════════════════════════════════════════════════════════════════
CHECKPOINT-2A: STATIC ANALYSIS COMPLETE ✓
CHECKPOINT-2B: OUTPUT VERIFICATION COMPLETE ✓
CHECKPOINT-3: TIER-3 YAML COMPLETE ✓
CHECKPOINT-4: DB INTEGRATION COMPLETE ✓

Output Truth: VERIFIED BY EXECUTION
Tier-3 YAML: CREATED

PHASE 2 DELIVERABLES READY — AWAITING HUMAN VERIFICATION
═══════════════════════════════════════════════════════════════════
```

### Human verifies Phase 2:

- ✅ `VERIFICATION_METHOD: ACTUAL_EXECUTION` confirms script ran
- ✅ Output Truth section has real timestamps and file sizes
- ✅ Tier-3 YAML file exists

### (Phases 3-4 follow same pattern)

### Final: Phase 4 with git diff proof

```text
═══════════════════════════════════════════════════════════════════
PHASE 4 COMPLETE
═══════════════════════════════════════════════════════════════════
CHECKPOINT-9: ATTESTATION COMPLETE ✓
CHECKPOINT-10: PROPAGATION COMPLETE ✓

═══════════════════════════════════════════════════════════════════
GIT DIFF EVIDENCE — TIER-2 ROSTER
═══════════════════════════════════════════════════════════════════
diff --git a/tier2_adhoc_scripts_roster.md b/tier2_adhoc_scripts_roster.md
@@ -89,7 +89,7 @@
-- [ ] Inspect outputs + pruning/retention surfaces
+- [x] Inspect outputs + pruning/retention surfaces
 
-- [ ] Draft plan to close output-root
+- [x] Draft plan to close output-root

═══════════════════════════════════════════════════════════════════
GIT DIFF EVIDENCE — TIER-1 REGISTRY
═══════════════════════════════════════════════════════════════════
diff --git a/tier1_healthview_orchestration_pipeline.md b/tier1_...
@@ -167,6 +167,7 @@
 | ASR-011 | generate_foo.py | producer | ✅ Complete | 2026-01-15 |
+| ASR-012 | generate_lizard_report.py | producer | ✅ Complete | 2026-02-02 |

═══════════════════════════════════════════════════════════════════
PLACEHOLDER SWEEP
═══════════════════════════════════════════════════════════════════
Command: Select-String -Path "..." -Pattern "<[A-Z_]+>|TODO|TBD"
Result: NO MATCHES FOUND

PHASE 4 DELIVERABLES READY — AWAITING FINAL VERIFICATION
═══════════════════════════════════════════════════════════════════
```

### Human verifies Phase 4:

- ✅ Git diff shows actual checkbox changes in Tier-2
- ✅ Git diff shows new row added to Tier-1
- ✅ No placeholders remain

### Human commits:

```bash
git add tier2_roster/working_docs/stage_11_1/ASR-012_generate_lizard_report_build.md
git add tier2_roster/tier2_adhoc_scripts_roster.md
git add tier1_healthview_orchestration_pipeline.md
git commit -m "Complete inspection for generate_lizard_report.py (ASR-012)"
```

---

## QUICK REFERENCE

### Phase Summary

| Phase | Prompts | Checkpoints | Human Verifies Before Next Phase |
|-------|---------|-------------|----------------------------------|
| **1** | BOOT, SETUP | 0, 1 | Build doc exists, ID correct |
| **2** | ANALYZE, VERIFY, PREPARE | 2A, 2B, 3, 4 | Script executed, output truth real |
| **3** | GAPS, EVIDENCE, ORCHESTRATOR | 5, 6, 7, 8 | Gaps real, evidence specific |
| **4** | CLOSE | 9, 10 | Git diff proves updates |

### Checkpoint Signals

| Checkpoint | Phase | Signal |
|------------|-------|--------|
| 0 | 1 | "CHECKPOINT-0: BOOTSTRAP COMPLETE — ..." |
| 1 | 1 | "CHECKPOINT-1: SETUP COMPLETE — ..." |
| 2A | 2 | "CHECKPOINT-2A: STATIC ANALYSIS COMPLETE — ..." |
| 2B | 2 | "CHECKPOINT-2B: OUTPUT VERIFICATION COMPLETE — ..." |
| 3 | 2 | "CHECKPOINT-3: TIER-3 YAML COMPLETE — ..." |
| 4 | 2 | "CHECKPOINT-4: DB INTEGRATION COMPLETE — ..." |
| 5 | 3 | "CHECKPOINT-5: GAP ANALYSIS COMPLETE — ..." |
| 6 | 3 | "CHECKPOINT-6: CHANGES DOCUMENTED — ..." |
| 7 | 3 | "CHECKPOINT-7: EVIDENCE CAPTURED — ..." |
| 8 | 3 | "CHECKPOINT-8: ORCHESTRATOR READINESS COMPLETE — ..." |
| 9 | 4 | "CHECKPOINT-9: ATTESTATION COMPLETE — ..." |
| 10 | 4 | "CHECKPOINT-10: PROPAGATION COMPLETE — ..." |

### Phase Files

| Phase | Instruction File |
|-------|------------------|
| 1 | `stage12_templates/PROMPT_PHASE1_BOOTSTRAP.md` |
| 2 | `stage12_templates/PROMPT_PHASE2_ANALYSIS.md` |
| 3 | `stage12_templates/PROMPT_PHASE3_EVIDENCE.md` |
| 4 | `stage12_templates/PROMPT_PHASE4_FINALIZE.md` |

### Human Verification Checklists

**After Phase 1:**
- [ ] Build document file exists at reported path
- [ ] Record ID is correct (ROSTER_HIT = use that ID, GENERATED = not in roster)
- [ ] Section 1 has script identity filled (not placeholders)

**After Phase 2:**
- [ ] `VERIFICATION_METHOD: ACTUAL_EXECUTION` in checkpoint signal
- [ ] Output Truth table has real file sizes and timestamps
- [ ] Tier-3 YAML file exists at reported path

**After Phase 3:**
- [ ] Example rows deleted from Section 5 table
- [ ] If 0 gaps, explicitly states "No gaps identified"
- [ ] Evidence has actual line numbers (`#L123-L145` format)
- [ ] Changes have commit SHA or "UNCOMMITTED"

**After Phase 4:**
- [ ] Git diff for Tier-2 shows real checkbox changes
- [ ] Git diff for Tier-1 shows row added/updated
- [ ] Placeholder sweep shows "NO MATCHES FOUND"

---

## VERSION HISTORY

| Version | Date | Changes |
|---------|------|---------|
| 2.0.0 | 2026-02-02 | **MAJOR:** Restructured to 4-phase workflow with mandatory human verification between phases. Added PROMPT_PHASE1-4 files. Replaced single BEGIN block with 4 phase prompts. Added git diff requirement for Phase 4. Added Phase verification checklists. |
| 1.0.4 | 2026-02-02 | Added ROSTER_MAP check in BOOTSTRAP Step 4D |
| 1.0.3 | 2026-02-02 | Mode status: Added mode availability table, marked DISCOVERY and BATCH as "Coming Soon", enhanced RESUME mode description with checkpoint detection details |
| 1.0.2 | 2026-02-02 | Updated related_files to point to `common/review_metaprompts.md` (shared across all classes) |
| 1.0.1 | 2026-02-02 | Path resolution: Added HOP_ROOT constant, converted BEGIN block Read: directives to absolute paths |
