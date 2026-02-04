---
title: "Phase 4: Finalization + Propagation"
tier: metaprompt
audience:
  - coding_agent
  - human_operator
phase: 4
checkpoints:
  - CHECKPOINT-9
  - CHECKPOINT-10
version: 1.4.0
updated_at: 2026-02-03
related_files:
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/stage12_templates/common/review_metaprompts.md
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/stage12_templates/producer/build_template.md
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier1_healthview_orchestration_pipeline.md
---

# PHASE 4: FINALIZATION + PROPAGATION

> **HOP_ROOT:** `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/`
>
> All paths in this document are relative to repository root unless noted.

---

## Purpose

Phase 4 finalizes the inspection and **propagates changes to external tracking files**.
This is the MOST CRITICAL phase because it requires PROOF that external files were updated.

**Why this phase exists:**

In live testing, agents have:
- ✅ Checked the "Tier-2 roster updated" box
- ✅ Checked the "Tier-1 registry updated" box
- ❌ But the actual files were NEVER MODIFIED

**This phase requires git diff evidence to prove the work was done.**

---

## ════════════════════════════════════════════════════════════════
## ⚠️ CRITICAL: EXTERNAL FILE UPDATE VERIFICATION
## ════════════════════════════════════════════════════════════════

**YOU CANNOT CLAIM COMPLETION WITHOUT GIT DIFF PROOF.**

This phase is different from Phases 1-3. Those phases fill in sections of the build document.
This phase requires you to **EDIT EXTERNAL FILES** and **PROVE YOU DID IT**.

### The Verification Requirement

Before emitting CHECKPOINT-10, you MUST:

1. **Actually edit** the Tier-2 roster file
2. **Actually edit** the Tier-1 registry file
3. **Run `git diff`** on both files
4. **Paste the diff output** into your completion signal

If you cannot produce git diff output showing changes, **you have not completed Phase 4**.

---

## SCOPE

This phase covers one prompt with two checkpoints:

| Prompt | Purpose | Checkpoint | Build Doc Sections |
|--------|---------|------------|-------------------|
| PROMPT-910-CLOSE | Attestation + External updates | CHECKPOINT-9, CHECKPOINT-10 | 9, 10 |

**Key actions:**
- Sign attestation (Section 9)
- Update Tier-2 roster (external file)
- Update Tier-1 registry (external file)
- Sweep for placeholders
- Finalize build document

---

## PREREQUISITES

Before starting Phase 4, confirm:

| Requirement | How to verify |
|-------------|---------------|
| Phase 3 complete | CHECKPOINT-5, 6, 7, 8 signals received |
| All sections filled | Sections 1-8 complete in build doc |
| No placeholder text | Quick scan shows no `<PLACEHOLDER>` |
| Human approved | Human explicitly delivered Phase 4 prompt |

**If any prerequisite is missing, STOP and request Phase 3 completion.**

---

## DELIVERABLES

When Phase 4 completes, the following will exist:

| Artifact | Status |
|----------|--------|
| Section 9 (Attestation) | Signed with agent ID and date |
| Section 10.1 (Verification) | All checkboxes marked [x] |
| Section 10.2 (Tier-2 Roster) | **ACTUALLY UPDATED** with git diff proof |
| Section 10.3 (Tier-1 Registry) | **ACTUALLY UPDATED** with git diff proof |
| Section 10.4 (Placeholder Sweep) | Grep output showing 0 matches |
| Build doc frontmatter | Status updated to `complete` |
| Git diff evidence | Pasted in completion signal |

---

## INSTRUCTIONS

### Step 1: Load Required References

Read these files before proceeding:

```text
1. {HOP_ROOT}/stage12_templates/common/review_metaprompts.md
   → PROMPT-910-CLOSE section

2. The build document from Phase 1
   → Get RECORD_ID, SCRIPT_NAME, TARGET_STAGE
```

---

### Step 2: Complete Attestation (Section 9)

Fill Section 9 with:

```markdown
## Section 9: Attestation

**Inspected by:** {Agent ID or "GitHub Copilot"}
**Date:** 2026-02-02
**Build document version:** 1.0.0

I attest that:
- [x] All sections of this document have been completed
- [x] All claims are supported by evidence
- [x] Output truth was verified by actual execution
- [x] Tier-3 YAML exists and is valid
- [x] External tracking files will be updated in Section 10
```

**Output after Step 2:**

```text
═══════════════════════════════════════════════════════════════════
CHECKPOINT-9: ATTESTATION COMPLETE
═══════════════════════════════════════════════════════════════════
ATTESTED_BY: {agent_id}
DATE: {YYYY-MM-DD}
ATTESTATION_SIGNED: YES

ATTESTATION COMPLETE — Proceeding to external updates
═══════════════════════════════════════════════════════════════════
```

---

### Step 3: Final Verification Checklist (Section 10.1)

Review and check each item:

```markdown
## Section 10.1: Final Verification

- [x] Section 1 (Identity): Script path, name, line count filled
- [x] Section 2 (Analysis): CLI, entry points, dependencies, compliance documented
- [x] Section 2.5 (Output Truth): Verified by ACTUAL execution
- [x] Section 3 (Tier-3): YAML exists and validated
- [x] Section 4 (DB Integration): Markers documented
- [x] Section 5 (Gaps): Real gaps OR "No gaps" documented, examples deleted
- [x] Section 6 (Changes): Changes with commits OR "N/A" documented
- [x] Section 7 (Evidence): Line numbers and test results recorded
- [x] Section 8 (Orchestrator): Entry point and config documented
- [x] Section 9 (Attestation): Signed
```

**Do NOT check boxes you cannot verify.** If any item is incomplete, go back and complete it.

---

### Step 4: UPDATE Tier-2 Roster (Section 10.2) — CRITICAL

> ⚠️ **YOU MUST ACTUALLY EDIT THE EXTERNAL FILE**
>
> Do not just check the checkbox. Open the file, make the edit, save it.

#### 4A. Locate the Roster File

**ROSTER_MAP:**

| Stage | Roster File |
|-------|-------------|
| 1.1 (TER) | `{HOP_ROOT}/tier2_roster/tier2_test_execution_roster.md` |
| 2.1 (S21R) | `{HOP_ROOT}/tier2_roster/tier2_docs_health_overview_roster.md` |
| 6.1 (SIR) | `{HOP_ROOT}/tier2_roster/tier2_inventory_management_roster.md` |
| 11.1 (ASR) | `{HOP_ROOT}/tier2_roster/tier2_adhoc_scripts_roster.md` |

#### 4B. Find the Script's Record

Search for the RECORD_ID (e.g., `S21R-003`) in the roster file.

```powershell
Select-String -Path "{roster_path}" -Pattern "{RECORD_ID}"
```

#### 4C. Update the Workstream Checkboxes

Locate the "Implementation Workstreams" section for your script.
Mark ALL workstream checkboxes as complete:

```markdown
#### Implementation Workstreams (checkbox-driven) — {script_name}

Workstream A — Discovery
- [x] Inspect outputs + pruning/retention surfaces; record findings

Workstream B — Plan
- [x] Draft plan to close output-root/base-package stop-gates

Workstream C — Implement
- [x] Implement accepted plan; update record and stop-gate status with evidence.

Workstream D — Tier-3 YAML
- [x] Confirm Tier-3 is appropriate for this script; record decision (create vs defer)
- [x] Inspect Tier-3 template requirements
- [x] Draft `tier3_{script_stem}.yaml`
- [x] Validate Tier-3 YAML

Workstream E — QA & Evidence
- [x] Pytest evidence captured
- [x] Mypy evidence captured or marked N/A (in record)
- [x] Coverage ≥80% (or exception recorded) + doc-index timestamp recorded

- [x] DONE — {script_name} complete; update Tier-1 Stage {X.X} script gate
```

#### 4D. Verify with Git Diff

**RUN THIS COMMAND:**

```powershell
git diff "{HOP_ROOT}/tier2_roster/{roster_file}"
```

**Expected output (VALID):**

```diff
diff --git a/.repo_studios/docs/pipeline/.../tier2_docs_health_overview_roster.md b/.repo_studios/docs/pipeline/.../tier2_docs_health_overview_roster.md
index abc1234..def5678 100644
--- a/.repo_studios/docs/pipeline/.../tier2_docs_health_overview_roster.md
+++ b/.repo_studios/docs/pipeline/.../tier2_docs_health_overview_roster.md
@@ -523,7 +523,7 @@ Workstream A — Discovery
-- [ ] Inspect outputs + pruning/retention surfaces; record findings
+- [x] Inspect outputs + pruning/retention surfaces; record findings
```

**Invalid output (FAKE/MISSING):**

```text
# Empty output — NO CHANGES DETECTED
```

```text
# Error message
fatal: path 'tier2_roster/...' did not match any files
```

**If git diff shows no changes, YOU HAVE NOT COMPLETED THE UPDATE.**

---

### Step 4E: REPLACE Script Section with Agent Router — CRITICAL

> ⚠️ **REPLACE REGARDLESS PRINCIPLE**
>
> Do NOT check if the existing section is "already complete."
> Do NOT skip this step because "it looks fine."
> **REPLACE the entire script section with the standardized template, EVERY TIME.**
>
> Why? Existing data may be stale, formats may not match, and we need machine-parseable output.

#### 4E.1 Locate the Script Section in Roster

Find the `<!-- AGENT_ROUTER:START {RECORD_ID} -->` marker, OR find the `### {RECORD_ID}` heading.

#### 4E.2 DELETE the Existing Section — CRITICAL

> ⚠️ **YOU MUST DELETE BEFORE INSERTING**
>
> The git diff MUST show deleted lines (`-`) for the old content.
> If your diff only shows additions (`+`), you have NOT replaced — you have duplicated.

**How to identify the section to delete:**

The old section may be in ONE of these formats:

**Format A: Old YAML record block**

```text
##### S21R-XXX {script_name}

```yaml
record_id: "S21R-XXX"
script:
  path: "..."
...
```
```

**Format B: Previous Agent Router (if re-inspecting)**

```text
<!-- AGENT_ROUTER:START S21R-XXX -->
### S21R-XXX — {script_name}
...
<!-- AGENT_ROUTER:END S21R-XXX -->
```

**Boundaries to delete:**

| If format is... | Start boundary | End boundary |
|-----------------|----------------|---------------|
| Old YAML block | `##### S21R-XXX` heading | Next `##### S21R-` heading OR next `---` separator OR `<!-- AGENT_ROUTER:START` |
| Previous Agent Router | `<!-- AGENT_ROUTER:START S21R-XXX -->` | `<!-- AGENT_ROUTER:END S21R-XXX -->` |

**Python snippet to locate boundaries:**

```python
import re
from pathlib import Path

roster_path = Path("{ROSTER_PATH}")
content = roster_path.read_text(encoding='utf-8')
record_id = "{RECORD_ID}"  # e.g., "S21R-005"

# Pattern for old YAML block
yaml_pattern = rf'(##### {record_id}.*?(?=##### S21R-|<!-- AGENT_ROUTER:START|---\n\n##|\Z))'

# Pattern for existing Agent Router
router_pattern = rf'(<!-- AGENT_ROUTER:START {record_id} -->.*?<!-- AGENT_ROUTER:END {record_id} -->)'

# Find and remove old content
content_cleaned = re.sub(yaml_pattern, '', content, flags=re.DOTALL)
content_cleaned = re.sub(router_pattern, '', content_cleaned, flags=re.DOTALL)

# Now insert new Agent Router at appropriate location
# (after the workstream checkboxes for this script)
```

**Verification requirement:**

Your git diff for Tier-2 roster MUST show:
1. **Deleted lines (`-`)** — The old YAML block or old Agent Router
2. **Added lines (`+`)** — The new Agent Router template

**Example of VALID git diff:**

```diff
-##### S21R-005 verify docs integrity
-
-```yaml
-record_id: "S21R-005"
-script:
-  path: ".repo_studios/scripts/producers/verify_docs_integrity.py"
-  name: "verify_docs_integrity.py"
-  category: "producer"
-...
-```
+<!-- AGENT_ROUTER:START S21R-005 -->
+### S21R-005 — verify_docs_integrity.py
+...
+<!-- AGENT_ROUTER:END S21R-005 -->
```

**Example of INVALID git diff (duplication detected):**

```diff
 - [x] DONE — verify_docs_integrity.py complete

+<!-- AGENT_ROUTER:START S21R-005 -->
+### S21R-005 — verify_docs_integrity.py
```

☝️ **This is WRONG** — no deletions shown, old content still exists.

#### 4E.3 INSERT the Standardized Agent Router Template

**REPLACE WITH THIS TEMPLATE (populate all fields):**

````markdown
<!-- AGENT_ROUTER:START {RECORD_ID} -->
### {RECORD_ID} — {SCRIPT_NAME}

> **One-liner:** {ONE_LINE_DESCRIPTION}

**Keywords:** `{KEYWORD_1}`, `{KEYWORD_2}`, `{KEYWORD_3}`

#### Resource Paths
| Resource | Path |
|----------|------|
| Script | `{SCRIPT_PATH}` |
| Tier-3 YAML | `{TIER3_YAML_PATH}` |
| Build Doc | `{BUILD_DOC_PATH}` |
| Output Root | `{OUTPUT_ROOT}` |

#### Invocation
```bash
{INVOCATION_COMMAND}
```

| Aspect | Value |
|--------|-------|
| Entry Point | `{ENTRY_FUNCTION}` |
| Typical Runtime | {RUNTIME} |
| Exit Codes | 0=success, 1=error, 2=no-op |

#### Outputs
| Artifact | Format | Description |
|----------|--------|-------------|
| {ARTIFACT_1} | {FORMAT_1} | {DESCRIPTION_1} |
| {ARTIFACT_2} | {FORMAT_2} | {DESCRIPTION_2} |

#### Compliance
| Aspect | Status | Notes |
|--------|--------|-------|
| HOP Bundle | {YES/PARTIAL/NO} | {NOTES} |
| UIC Interface | {YES/PARTIAL/NO} | {NOTES} |
| Tier-3 YAML | {YES/NO} | {NOTES} |

#### Orchestrator
| Pipeline | Status | Config Path |
|----------|--------|-------------|
| {PIPELINE_NAME} | {WIRED/NOT_WIRED/CANDIDATE} | {CONFIG_PATH_OR_NA} |

#### Pipeline Position
| Field | Value |
|-------|-------|
| Step Number | {N} of {TOTAL} |
| Execution Mode | {SEQUENTIAL/PARALLEL/CONDITIONAL} |
| Orchestrator Script | `{ORCHESTRATOR_SCRIPT_PATH}` |

#### Dependencies & Consumers
| Direction | Record ID | Script | Data Flow |
|-----------|-----------|--------|-----------|
| ⬆️ DEPENDS ON | {UPSTREAM_RECORD_ID} | `{UPSTREAM_SCRIPT}` | Requires `{ARTIFACT}` from `{OUTPUT_PATH}` |
| ⬇️ CONSUMED BY | {DOWNSTREAM_RECORD_ID} | `{DOWNSTREAM_SCRIPT}` | Provides `{ARTIFACT}` to `{INPUT_PATH}` |
<!-- If no upstream dependencies: "| ⬆️ DEPENDS ON | (none) | — | First in pipeline, no upstream dependencies |" -->
<!-- If no downstream consumers: "| ⬇️ CONSUMED BY | (none) | — | Terminal node, outputs consumed by orchestrator |" -->

#### Known Limitations
- {LIMITATION_1}
- {LIMITATION_2}
<!-- If none: "None documented." -->

#### Verification
| Field | Value |
|-------|-------|
| Last Verified | {YYYY-MM-DD} |
| Verified By | {AGENT_ID} |
| Build Doc Version | {BUILD_DOC_VERSION} |
<!-- AGENT_ROUTER:END {RECORD_ID} -->
````

#### 4E.4 Field Population Guide

**Where to get each field:**

| Field | Source |
|-------|--------|
| `{ONE_LINE_DESCRIPTION}` | Build Doc Section 1 — Script purpose |
| `{KEYWORD_1,2,3}` | Derive from script purpose and outputs |
| `{SCRIPT_PATH}` | Build Doc Section 1 |
| `{TIER3_YAML_PATH}` | Build Doc Section 3 |
| `{BUILD_DOC_PATH}` | Current document path |
| `{OUTPUT_ROOT}` | Build Doc Section 2.5 — Output Truth |
| `{INVOCATION_COMMAND}` | Build Doc Section 2 — CLI Interface |
| `{ENTRY_FUNCTION}` | Build Doc Section 2 — Entry Points |
| `{RUNTIME}` | Build Doc Section 2.5 — Execution time |
| `{ARTIFACT_N}` | Build Doc Section 2.5 — Output artifacts |
| Compliance status | Build Doc Section 5 — Gaps (YES if no gaps, PARTIAL/NO if gaps) |
| Orchestrator status | Build Doc Section 8 |
| `{N}` / `{TOTAL}` | Orchestrator source code — TopicStep list order |
| `{EXECUTION_MODE}` | Orchestrator source — SEQUENTIAL (most), PARALLEL (if concurrent), CONDITIONAL (if guarded) |
| `{ORCHESTRATOR_SCRIPT_PATH}` | Build Doc Section 8 — orchestrator reference |
| `{UPSTREAM_RECORD_ID}` | Inspect orchestrator for data dependencies; trace `load_*` calls |
| `{DOWNSTREAM_RECORD_ID}` | Inspect aggregators/consumers that import this script's outputs |
| Limitations | Build Doc Section 5 — Gaps (convert to limitations) |

#### 4E.5 Example: Populated Agent Router

```markdown
<!-- AGENT_ROUTER:START S21R-003 -->
### S21R-003 — generate_anchor_inventory.py

> **One-liner:** Extracts markdown anchor targets and references for cross-document link validation.

**Keywords:** `markdown`, `anchors`, `validation`, `links`, `inventory`

#### Resource Paths
| Resource | Path |
|----------|------|
| Script | `.repo_studios/scripts/producers/generate_anchor_inventory.py` |
| Tier-3 YAML | `.repo_studios/scripts/producers/generate_anchor_inventory.tier3.yaml` |
| Build Doc | `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/working_docs/stage_2_1/S21R-003_generate_anchor_inventory_build.md` |
| Output Root | `.repo_studios/reports/healthview/producer_reports/anchor_inventory/` |

#### Invocation
```bash
python -m scripts.producers.generate_anchor_inventory --repo-root . --log-level INFO
```

| Aspect | Value |
|--------|-------|
| Entry Point | `run(argv)` / `main()` |
| Typical Runtime | ~10 seconds |
| Exit Codes | 0=success, 1=error, 2=no-op |

#### Outputs
| Artifact | Format | Description |
|----------|--------|-------------|
| manifest.json | JSON | Bundle metadata with file inventory |
| summary.md | Markdown | Human-readable anchor statistics |
| anchors_targets.json | JSON | All anchor targets extracted |
| anchors_references.json | JSON | All anchor references extracted |

#### Compliance
| Aspect | Status | Notes |
|--------|--------|-------|
| HOP Bundle | YES | Timestamped bundles with manifest |
| UIC Interface | YES | run(argv) entry point |
| Tier-3 YAML | YES | Created during inspection |

#### Orchestrator
| Pipeline | Status | Config Path |
|----------|--------|-------------|
| HealthView | CANDIDATE | N/A — not yet wired |

#### Pipeline Position
| Field | Value |
|-------|-------|
| Step Number | 2 of 8 |
| Execution Mode | SEQUENTIAL |
| Orchestrator Script | `.repo_studios/scripts/orchestrators/run_docs_health_overview.py` |

#### Dependencies & Consumers
| Direction | Record ID | Script | Data Flow |
|-----------|-----------|--------|-----------|
| ⬆️ DEPENDS ON | (none) | — | First in data chain, no upstream dependencies |
| ⬇️ CONSUMED BY | S21R-004 | `validate_markdown_anchors.py` | Provides `anchors_targets.json` for validation |
| ⬇️ CONSUMED BY | S21R-009 | `aggregate_docs_health_signals.py` | Provides anchor data for aggregation |

#### Known Limitations
- None documented.

#### Verification
| Field | Value |
|-------|-------|
| Last Verified | 2026-02-02 |
| Verified By | GitHub Copilot |
| Build Doc Version | 1.0.0 |
<!-- AGENT_ROUTER:END S21R-003 -->
```

---

### Step 5: VERIFY AND UPDATE Tier-1 Registry (Section 10.3) — MANDATORY

> ⚠️ **VERIFY REGARDLESS OF CURRENT STATE**
>
> Even if the Tier-1 entry appears complete, you MUST:
>
> 1. **LOCATE** the script's row in the Tier-1 table
> 2. **VERIFY** the Tier-3 YAML column has the correct link (not `TBD`)
> 3. **VERIFY** the Purpose/Description column is accurate
> 4. **VERIFY** the Category column matches the script class
> 5. **SHOW** evidence of verification (even if no changes needed)
>
> **Do NOT skip this step because the entry "looks fine" or is "already complete."**
> **Do NOT report "NO UPDATE REQUIRED" without showing verification evidence.**

#### 5A. Locate the Tier-1 File

```text
{HOP_ROOT}/tier1_healthview_orchestration_pipeline.md
```

#### 5B. Find the Script Registry Section

Search for "Script Registry" or the stage heading (e.g., "Stage 2.1").

```powershell
Select-String -Path "{HOP_ROOT}/tier1_healthview_orchestration_pipeline.md" -Pattern "Stage {X.X}|Script Registry"
```

#### 5C. Verify Entry Fields (MANDATORY)

Before making any changes, document verification of the existing entry:

```powershell
Select-String -Path "{HOP_ROOT}/tier1_healthview_orchestration_pipeline.md" -Pattern "{SCRIPT_NAME}"
```

**Verification Table (REQUIRED):**

| Field | Expected | Actual | Status |
|-------|----------|--------|--------|
| Script name | `{SCRIPT_NAME}` | `<actual>` | `VERIFIED` / `MISMATCH` |
| Category | `{SCRIPT_CLASS}` | `<actual>` | `VERIFIED` / `MISMATCH` |
| Tier-3 YAML link | `[tier3_{script}.yaml](...)` | `<actual>` | `VERIFIED` / `TBD` / `MISSING` |
| Status | `✅ Complete` | `<actual>` | `VERIFIED` / `NEEDS_UPDATE` |
| Last Verified | `{TODAY}` | `<actual>` | `VERIFIED` / `STALE` |

#### 5D. Add or Update Registry Entry

**Format for new entry:**

```markdown
| {RECORD_ID} | {script_name} | {category} | ✅ Complete | {YYYY-MM-DD} |
```

**Format for update (if entry exists):**

Change status from `🔄 In Progress` or `⏳ Pending` to `✅ Complete`.

#### 5E. Git Diff Verification (REQUIRED)

**RUN THIS COMMAND:**

```powershell
git diff "{HOP_ROOT}/tier1_healthview_orchestration_pipeline.md"
```

**Scenario A: Changes were made (TIER1_UPDATED: YES)**

Expected output:

```diff
diff --git a/.repo_studios/docs/pipeline/.../tier1_healthview_orchestration_pipeline.md b/...
index abc1234..def5678 100644
--- a/.repo_studios/docs/pipeline/.../tier1_healthview_orchestration_pipeline.md
+++ b/.repo_studios/docs/pipeline/.../tier1_healthview_orchestration_pipeline.md
@@ -145,6 +145,7 @@
 | S21R-002 | generate_doc_index.py | producer | ✅ Complete | 2025-12-28 |
+| S21R-003 | generate_anchor_inventory.py | producer | ✅ Complete | 2026-02-02 |
```

**Scenario B: No changes needed — entry already correct (TIER1_VERIFIED: Entry correct)**

If git diff shows NO output, you MUST still document verification:

```text
TIER-1 VERIFICATION: Entry verified correct, no changes needed.
Evidence: Row found at line {LINE_NUMBER} with correct values:
- Script: {SCRIPT_NAME} ✅
- Category: {SCRIPT_CLASS} ✅
- Tier-3 link: [tier3_{script}.yaml](...) ✅
- Status: ✅ Complete ✅
git diff output: (empty — no changes needed)
```

**❌ INVALID OUTPUTS (will cause Phase 4 rejection):**

- "NO UPDATE REQUIRED — Entry already current"
- "Skipped — entry looks complete"
- (no mention of Tier-1 at all)
- "Status unchanged" without verification evidence

**✅ VALID OUTPUTS:**

- `TIER1_UPDATED: YES` — TBD changed to tier3_script.yaml (diff shown)
- `TIER1_VERIFIED: Entry correct at line 830` — all fields verified (table shown)

---

### Step 6: Placeholder Sweep (Section 10.4)

Search the ENTIRE build document for remaining placeholders.

**RUN THIS COMMAND:**

```powershell
Select-String -Path "{BUILD_DOC_PATH}" -Pattern "<[A-Z_]+>|TODO|TBD|PLACEHOLDER"
```

**Expected output (VALID):**

```text
# No output — no matches found
```

**Invalid output (PLACEHOLDERS REMAIN):**

```text
build_doc.md:45: <SCRIPT_PATH>
build_doc.md:89: TODO: fill this section
build_doc.md:156: <LINE_COUNT>
```

**If placeholders are found, go back and fill them before proceeding.**

---

### Step 7: Finalize Document

Update the build document frontmatter:

```yaml
---
status: complete
completed_at: 2026-02-02
---
```

---

## COMPLETION SIGNALS

Emit BOTH checkpoint signals WITH git diff evidence:

```text
═══════════════════════════════════════════════════════════════════
PHASE 4 COMPLETE
═══════════════════════════════════════════════════════════════════
CHECKPOINT-9: ATTESTATION COMPLETE ✓
CHECKPOINT-10: PROPAGATION COMPLETE ✓

═══════════════════════════════════════════════════════════════════
GIT DIFF EVIDENCE — TIER-2 ROSTER
═══════════════════════════════════════════════════════════════════
File: {HOP_ROOT}/tier2_roster/{roster_file}
Command: git diff "{path}"

{PASTE ACTUAL GIT DIFF OUTPUT HERE}

The diff MUST show:
1. Workstream checkboxes changed from `- [ ]` to `- [x]`
2. Agent Router section replaced (look for `<!-- AGENT_ROUTER:START -->`)

═══════════════════════════════════════════════════════════════════
GIT DIFF EVIDENCE — TIER-1 REGISTRY
═══════════════════════════════════════════════════════════════════
File: {HOP_ROOT}/tier1_healthview_orchestration_pipeline.md
Command: git diff "{path}"

{PASTE ACTUAL GIT DIFF OUTPUT HERE}

OR if no changes needed:

TIER-1 VERIFICATION: Entry verified correct, no changes needed.
Evidence: Row found at line {LINE_NUMBER} with correct values:
- Script: {SCRIPT_NAME} ✅
- Category: {SCRIPT_CLASS} ✅
- Tier-3 link: verified ✅
- Status: ✅ Complete ✅

═══════════════════════════════════════════════════════════════════
PLACEHOLDER SWEEP
═══════════════════════════════════════════════════════════════════
Command: Select-String -Path "{BUILD_DOC_PATH}" -Pattern "<[A-Z_]+>|TODO|TBD|PLACEHOLDER"
Result: NO MATCHES FOUND

═══════════════════════════════════════════════════════════════════
SUMMARY
═══════════════════════════════════════════════════════════════════
RECORD_ID: {RECORD_ID}
SCRIPT: {SCRIPT_NAME}
BUILD_DOC: {BUILD_DOC_PATH}
TIER2_UPDATED: YES (diff shown above)
TIER1_UPDATED: YES (diff shown above) | VERIFIED (entry correct, line {N})
PLACEHOLDERS: NONE

PHASE 4 DELIVERABLES READY — AWAITING FINAL HUMAN VERIFICATION
═══════════════════════════════════════════════════════════════════
```

---

## ════════════════════════════════════════════════════════════════
## STOP — FINAL HUMAN VERIFICATION
## ════════════════════════════════════════════════════════════════

**DO NOT CLAIM INSPECTION COMPLETE WITHOUT HUMAN VERIFICATION.**

After emitting the completion signals above, **STOP** and wait for the human operator.

### What human will verify:

| Check | How to verify |
|-------|---------------|
| **Git diff for Tier-2 is real** | Diff output shows actual `- [ ]` → `- [x]` changes |
| **Agent Router replaced** | Diff shows `<!-- AGENT_ROUTER:START -->` markers |
| **Old content deleted** | Diff shows `-` lines removing old YAML block or previous Agent Router |
| **Git diff for Tier-1 is real** | Diff output shows row added/updated OR verification table shown |
| **Tier-1 verified/updated** | `TIER1_UPDATED: YES` (diff shown) OR `TIER1_VERIFIED: Entry correct at line {N}` |
| **No empty diffs without explanation** | Tier-1 section has either diff OR verification evidence |
| **Placeholder sweep clean** | grep result shows 0 matches |
| **Build doc complete** | Open file, scan for any remaining gaps |

### Red flags that indicate incomplete finalization:

| Red Flag | What it looks like |
|----------|-------------------|
| Empty git diff | "GIT DIFF EVIDENCE" section is blank |
| "No changes detected" | Diff command ran but produced no output |
| Diff shows wrong file | Path doesn't match ROSTER_MAP lookup |
| Agent Router missing | No `<!-- AGENT_ROUTER:START -->` in diff |
| Agent Router not replaced | Diff shows only checkbox changes, no router block |
| **No deletions in diff** | Diff shows only `+` lines, no `-` lines for old section |
| **Duplicate sections** | Both old YAML block AND new Agent Router exist in file |
| **Wrong section deleted** | Workstream checkboxes deleted instead of YAML block |
| Placeholder sweep skipped | No grep command output shown |
| Checkboxes not actually changed | Diff doesn't show `- [ ]` → `- [x]` |
| Missing Tier-1 entry | Diff doesn't show new/updated row |

### Final Human Decision:

| Outcome | Action |
|---------|--------|
| **All checks pass** | ✅ **INSPECTION COMPLETE** — Human commits changes |
| Git diff missing | Human requires agent to actually edit files |
| Placeholders remain | Human requires cleanup before completion |
| Tier-2 not updated | Human requires actual file edit |
| Tier-1 not updated | Human requires actual file edit |

---

## Post-Completion

Once human verifies Phase 4:

1. **Commit changes:**

```bash
git add "{BUILD_DOC_PATH}" "{TIER2_ROSTER_PATH}" "{TIER1_REGISTRY_PATH}"
git commit -m "Complete inspection for {SCRIPT_NAME} ({RECORD_ID})"
```

2. **Archive build doc (optional):**

Move from `working_docs/` to `completed_inspections/` if that workflow is in use.

3. **Update any downstream tracking:**

If there's a master checklist or kanban board, mark the script as complete.

---

## Troubleshooting

### "Git diff shows no changes but I edited the file"

The file wasn't saved. In VS Code:
- Check for dot (•) next to filename indicating unsaved changes
- Press Ctrl+S to save
- Run git diff again

### "I can't find the roster file"

Use ROSTER_MAP above. If stage doesn't have a roster yet:
1. Document this in build doc: "No roster exists for Stage {X.X}"
2. Create a GAP: "Tier-2 roster missing for this stage"
3. Skip Tier-2 update but document why

### "Tier-1 registry doesn't have a section for this stage"

Add the section:

```markdown
### Stage {X.X} — {Stage Name}

| Record ID | Script | Category | Status | Date |
|-----------|--------|----------|--------|------|
| {RECORD_ID} | {script_name} | {category} | ✅ Complete | {date} |
```

### "Placeholder sweep found matches in example sections"

If placeholders are in EXAMPLE text (like `<EXAMPLE_PATH>`), that's okay IF:
- They're clearly marked as examples
- They're not in actual data fields

If unsure, delete the example text.

### "Git diff command fails"

Check that:
- You're in the repository root
- The file path is correct
- Git is installed and working

```powershell
# Verify git is working
git status

# Verify file exists
Test-Path "{file_path}"
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.4.0 | 2026-02-03 | Strengthened Step 5 (Tier-1 Registry) to MANDATE verification regardless of current state; added verification table requirement (5C); added valid/invalid output examples; updated completion signal to require `TIER1_UPDATED: YES` or `TIER1_VERIFIED: Entry correct`; renamed 5D to 5E |
| 1.3.0 | 2026-02-02 | Strengthened Step 4E.2 with explicit deletion instructions: format identification (YAML vs Router), boundary detection, Python snippet, valid/invalid diff examples; added "Old content deleted" to verification checklist; added red flags for no deletions, duplicate sections, wrong section deleted |
| 1.2.0 | 2026-02-02 | Added Pipeline Position + Dependencies & Consumers sections to Agent Router template; updated Field Population Guide with dependency tracing sources; enhanced example with verbal graph fields |
| 1.1.0 | 2026-02-02 | Added "REPLACE REGARDLESS" principle; added standardized Agent Router template for Tier-2 script sections; added Step 4E |
| 1.0.0 | 2026-02-02 | Initial phase extraction; added mandatory git diff verification |
