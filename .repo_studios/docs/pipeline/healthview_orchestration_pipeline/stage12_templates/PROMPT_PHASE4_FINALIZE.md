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
version: 1.0.0
updated_at: 2026-02-02
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

### Step 5: UPDATE Tier-1 Registry (Section 10.3) — CRITICAL

> ⚠️ **YOU MUST ACTUALLY EDIT THE EXTERNAL FILE**
>
> Do not just check the checkbox. Open the file, make the edit, save it.

#### 5A. Locate the Tier-1 File

```text
{HOP_ROOT}/tier1_healthview_orchestration_pipeline.md
```

#### 5B. Find the Script Registry Section

Search for "Script Registry" or the stage heading (e.g., "Stage 2.1").

```powershell
Select-String -Path "{HOP_ROOT}/tier1_healthview_orchestration_pipeline.md" -Pattern "Stage {X.X}|Script Registry"
```

#### 5C. Add or Update Registry Entry

**Format for new entry:**

```markdown
| {RECORD_ID} | {script_name} | {category} | ✅ Complete | {YYYY-MM-DD} |
```

**Format for update (if entry exists):**

Change status from `🔄 In Progress` or `⏳ Pending` to `✅ Complete`.

#### 5D. Verify with Git Diff

**RUN THIS COMMAND:**

```powershell
git diff "{HOP_ROOT}/tier1_healthview_orchestration_pipeline.md"
```

**Expected output (VALID):**

```diff
diff --git a/.repo_studios/docs/pipeline/.../tier1_healthview_orchestration_pipeline.md b/...
index abc1234..def5678 100644
--- a/.repo_studios/docs/pipeline/.../tier1_healthview_orchestration_pipeline.md
+++ b/.repo_studios/docs/pipeline/.../tier1_healthview_orchestration_pipeline.md
@@ -145,6 +145,7 @@
 | S21R-002 | generate_doc_index.py | producer | ✅ Complete | 2025-12-28 |
+| S21R-003 | generate_anchor_inventory.py | producer | ✅ Complete | 2026-02-02 |
```

**If git diff shows no changes, YOU HAVE NOT COMPLETED THE UPDATE.**

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

═══════════════════════════════════════════════════════════════════
GIT DIFF EVIDENCE — TIER-1 REGISTRY
═══════════════════════════════════════════════════════════════════
File: {HOP_ROOT}/tier1_healthview_orchestration_pipeline.md
Command: git diff "{path}"

{PASTE ACTUAL GIT DIFF OUTPUT HERE}

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
TIER1_UPDATED: YES (diff shown above)
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
| **Git diff for Tier-1 is real** | Diff output shows row added/updated |
| **No empty diffs** | Neither diff section says "no changes" |
| **Placeholder sweep clean** | grep result shows 0 matches |
| **Build doc complete** | Open file, scan for any remaining gaps |

### Red flags that indicate incomplete finalization:

| Red Flag | What it looks like |
|----------|-------------------|
| Empty git diff | "GIT DIFF EVIDENCE" section is blank |
| "No changes detected" | Diff command ran but produced no output |
| Diff shows wrong file | Path doesn't match ROSTER_MAP lookup |
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
| 1.0.0 | 2026-02-02 | Initial phase extraction; added mandatory git diff verification |
