---
title: "Phase 3: Gaps + Evidence"
tier: metaprompt
audience:
  - coding_agent
  - human_operator
phase: 3
checkpoints:
  - CHECKPOINT-5
  - CHECKPOINT-6
  - CHECKPOINT-7
  - CHECKPOINT-8
version: 1.0.0
updated_at: 2026-02-02
related_files:
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/stage12_templates/common/review_metaprompts.md
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/stage12_templates/producer/build_template.md
---

# PHASE 3: GAPS + EVIDENCE

> **HOP_ROOT:** `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/`
>
> All paths in this document are relative to repository root unless noted.

---

## Purpose

Phase 3 identifies what's missing (gaps), documents what was changed (changes), and captures
proof of work (evidence). This phase transforms the verified analysis into actionable items.

**Why a separate phase?**
- Gap analysis requires Phase 2 verification to be complete first
- Changes must be documented AFTER they're made, not planned
- Evidence capture is distinct from execution

---

## SCOPE

This phase covers three prompts and four checkpoints:

| Prompt | Purpose | Checkpoint | Build Doc Sections |
|--------|---------|------------|-------------------|
| PROMPT-5-GAPS | Identify gaps, assign priority | CHECKPOINT-5 | 5 |
| PROMPT-67-EVIDENCE | Document changes + capture evidence | CHECKPOINT-6, CHECKPOINT-7 | 6, 7 |
| PROMPT-8-ORCHESTRATOR | Orchestrator readiness | CHECKPOINT-8 | 8 |

**NOT in scope:** External file updates (Phase 4), final cleanup (Phase 4).

---

## PREREQUISITES

Before starting Phase 3, confirm:

| Requirement | How to verify |
|-------------|---------------|
| Phase 2 complete | CHECKPOINT-2A, 2B, 3, 4 signals received |
| Output truth verified | Human confirmed `VERIFICATION_METHOD: ACTUAL_EXECUTION` |
| Tier-3 YAML exists | File at path documented in Section 3 |
| Human approved | Human explicitly delivered Phase 3 prompt |

**If any prerequisite is missing, STOP and request Phase 2 completion.**

---

## DELIVERABLES

When Phase 3 completes, the following will exist:

| Artifact | Status |
|----------|--------|
| Section 5 (Gaps) | Real gaps listed OR "No gaps found" documented |
| Section 6 (Changes) | Changes with commit SHA OR "N/A — already compliant" |
| Section 7 (Evidence) | Actual line numbers, test results, file paths |
| Section 8 (Orchestrator) | ScriptConfig documented, readiness checklist complete |
| Example rows | **DELETED** from all tables |
| Four checkpoint signals | CHECKPOINT-5, 6, 7, 8 emitted |

---

## INSTRUCTIONS

### Step 1: Load Required References

Read these files before proceeding:

```text
1. {HOP_ROOT}/stage12_templates/common/review_metaprompts.md
   → PROMPT-5-GAPS section
   → PROMPT-67-EVIDENCE section
   → PROMPT-8-ORCHESTRATOR section

2. The build document from Phase 1
   → Review Sections 1-4 completed in Phase 2
```

---

### Step 2: Execute PROMPT-5-GAPS

**Goal:** Identify compliance gaps and assign priority.

#### CRITICAL: Delete Example Rows First

The build template contains example rows like:

```markdown
| GAP-001 | Example: Missing `--artifacts-to-keep` flag | HIGH | 2h |
```

**DELETE ALL EXAMPLE ROWS** before adding real gaps. Do NOT leave examples in the table.

#### Gap Analysis Process

1. **Review Phase 2 findings:**
   - Compliance tier (A or B)?
   - Missing HOP patterns?
   - Output path issues?
   - Missing retention logic?

2. **For each gap found:**
   - Assign unique ID: `GAP-001`, `GAP-002`, etc.
   - Write clear description
   - Assign priority: `HIGH`, `MEDIUM`, or `LOW`
   - Estimate effort: `1h`, `2h`, `4h`, `1d`, etc.

3. **If NO gaps found:**

```markdown
| — | No gaps identified. Script is fully HOP-compliant. | — | — |
```

**This is valid!** A compliant script should have no gaps. But you MUST explicitly state it.

#### Priority Guidelines

| Priority | Criteria |
|----------|----------|
| **HIGH** | Blocks deployment, breaks orchestration, data loss risk |
| **MEDIUM** | Non-compliant but functional, technical debt |
| **LOW** | Nice-to-have, documentation, minor improvements |

**Output after Step 2:**

```text
═══════════════════════════════════════════════════════════════════
CHECKPOINT-5: GAP ANALYSIS COMPLETE
═══════════════════════════════════════════════════════════════════
GAPS_FOUND: {N}
HIGH_PRIORITY: {N}
MEDIUM_PRIORITY: {N}
LOW_PRIORITY: {N}
EXAMPLE_ROWS_DELETED: YES

GAP ANALYSIS COMPLETE — Ready for PROMPT-67-EVIDENCE
═══════════════════════════════════════════════════════════════════
```

---

### Step 3: Execute PROMPT-67-EVIDENCE

**Goal:** Document changes made and capture evidence.

#### Section 6: Changes Made

This section documents modifications made to close gaps.

##### If Changes Were Made:

```markdown
| Change | File | Lines | Commit |
|--------|------|-------|--------|
| Added `--artifacts-to-keep` flag | `generate_foo.py` | L45-52 | `abc1234` |
| Updated REPORTS_ROOT to HOP path | `generate_foo.py` | L31 | `abc1234` |
```

**Commit SHA requirements:**
- If committed: Use first 7 characters of SHA (e.g., `abc1234`)
- If uncommitted: Write `UNCOMMITTED`
- If staged but not committed: Write `STAGED`

##### If No Changes Needed:

```markdown
| — | N/A — Script already HOP-compliant | — | — |
```

**This is valid!** But you MUST explicitly state it, not leave the table empty.

#### Section 7: Evidence

Evidence must be **specific and verifiable**.

##### Good Evidence:

```markdown
**Test Results:**
- Pytest: `pytest tests/tests_producers/test_generate_foo.py` → 3 passed in 0.45s
- Mypy: `mypy .repo_studios/scripts/producers/generate_foo.py` → Success: no issues

**Code References:**
- Entry point: `.repo_studios/scripts/producers/generate_foo.py#L156-L162`
- Retention logic: `.repo_studios/scripts/producers/generate_foo.py#L89-L95`
- Bundle writer: `.repo_studios/scripts/producers/generate_foo.py#L201-L215`

**Execution Evidence:**
- Command: `.venv/Scripts/python.exe -u .repo_studios/scripts/producers/generate_foo.py --repo-root .`
- Exit code: 0
- Bundle path: `.repo_studios/reports/healthview/producer_reports/foo_topic/20260202-1430/`
```

##### Bad Evidence (DO NOT DO THIS):

```markdown
**Test Results:**
- Tests pass

**Code References:**
- See script for details

**Execution Evidence:**
- Script runs successfully
```

**Output after Step 3:**

```text
═══════════════════════════════════════════════════════════════════
CHECKPOINT-6: CHANGES DOCUMENTED
═══════════════════════════════════════════════════════════════════
CHANGES_MADE: {N}
COMMITS_REFERENCED: {N}
UNCOMMITTED_CHANGES: {YES|NO}

CHANGES DOCUMENTED — Continuing to evidence capture
═══════════════════════════════════════════════════════════════════

═══════════════════════════════════════════════════════════════════
CHECKPOINT-7: EVIDENCE CAPTURED
═══════════════════════════════════════════════════════════════════
TEST_RESULTS_RECORDED: YES
CODE_REFS_WITH_LINES: {N}
EXECUTION_EVIDENCE: YES

EVIDENCE CAPTURED — Ready for PROMPT-8-ORCHESTRATOR
═══════════════════════════════════════════════════════════════════
```

---

### Step 4: Execute PROMPT-8-ORCHESTRATOR

**Goal:** Document orchestrator integration readiness.

#### Section 8: Orchestrator Readiness

1. **Check entry point compatibility:**

```python
# Orchestrators expect this pattern:
def run(argv: list[str] | None = None) -> dict:
    ...
    return {"status": "success", ...}
```

If script uses `main(argv)` instead, document it.

2. **Document ScriptConfig:**

```yaml
# Example ScriptConfig for orchestrator integration
script_name: "generate_foo.py"
entry_point: "run"  # or "main"
required_args:
  - "--repo-root"
optional_args:
  - "--output-dir"
  - "--artifacts-to-keep"
  - "--log-level"
returns: "dict with status, artifacts, metrics"
```

3. **Complete readiness checklist:**

```markdown
- [x] Entry point documented
- [x] Required args identified
- [x] Return type documented
- [x] Error handling documented
- [ ] Integration tested with orchestrator (if applicable)
```

**Output after Step 4:**

```text
═══════════════════════════════════════════════════════════════════
CHECKPOINT-8: ORCHESTRATOR READINESS COMPLETE
═══════════════════════════════════════════════════════════════════
ENTRY_POINT: {run|main}
REQUIRED_ARGS: {N}
OPTIONAL_ARGS: {N}
RETURN_TYPE: {dict|int|None}
ORCHESTRATOR_COMPATIBLE: {YES|NO|PARTIAL}

ORCHESTRATOR READINESS COMPLETE — Phase 3 finished
═══════════════════════════════════════════════════════════════════
```

---

## COMPLETION SIGNALS

Emit ALL FOUR checkpoint signals before stopping:

```text
═══════════════════════════════════════════════════════════════════
PHASE 3 COMPLETE
═══════════════════════════════════════════════════════════════════
CHECKPOINT-5: GAP ANALYSIS COMPLETE ✓
  - Gaps found: {N}
  - Example rows deleted: YES
CHECKPOINT-6: CHANGES DOCUMENTED ✓
  - Changes made: {N}
  - Commit references: {N}
CHECKPOINT-7: EVIDENCE CAPTURED ✓
  - Code refs with line numbers: {N}
  - Test results recorded: YES
CHECKPOINT-8: ORCHESTRATOR READINESS COMPLETE ✓
  - Entry point: {run|main}
  - Orchestrator compatible: {YES|NO|PARTIAL}

Build Document Sections Filled: 5, 6, 7, 8
Example Rows: DELETED
Evidence Quality: VERIFIED WITH LINE NUMBERS

PHASE 3 DELIVERABLES READY — AWAITING HUMAN VERIFICATION
═══════════════════════════════════════════════════════════════════
```

---

## ════════════════════════════════════════════════════════════════
## STOP — AWAIT HUMAN VERIFICATION
## ════════════════════════════════════════════════════════════════

**DO NOT PROCEED TO PHASE 4.**

After emitting the completion signals above, **STOP** and wait for the human operator.

### What human will verify:

| Check | How to verify |
|-------|---------------|
| **Example rows deleted** | No rows containing "Example:" in any table |
| **Gaps are real** | Each gap describes actual non-compliance, not hypothetical |
| **"No gaps" is explicit** | If 0 gaps, table says "No gaps identified" not empty |
| **Changes have commits** | Each change row has SHA or explicit `UNCOMMITTED` |
| **Evidence has line numbers** | Code refs use `#L123-L145` format |
| **No placeholders** | No `<PLACEHOLDER>`, `TODO`, or `TBD` text |

### Red flags that indicate incomplete work:

| Red Flag | What it looks like |
|----------|-------------------|
| Example rows remain | `GAP-001 | Example: Missing flag | HIGH | 2h` |
| Empty tables | Section 5 table has only headers |
| Generic evidence | "Tests pass" without command or count |
| Missing line numbers | `generate_foo.py` without `#L123` |
| Vague gaps | "Needs improvement" without specifics |
| Missing commit info | Changes listed but no SHA column filled |

### Human decision:

| Outcome | Action |
|---------|--------|
| All checks pass | Human delivers Phase 4 prompt |
| Example rows remain | Human requires deletion before Phase 4 |
| Evidence incomplete | Human requires specific line numbers |
| Gaps unclear | Human requires rewrite with specifics |

---

## Troubleshooting

### "I found 0 gaps — is that okay?"

Yes! A well-maintained script may have no gaps. Document it explicitly:

```markdown
| — | No gaps identified. Script is fully HOP-compliant. | — | — |
```

### "Changes were made but not committed yet"

Use `UNCOMMITTED` in the Commit column:

```markdown
| Added retention flag | `generate_foo.py` | L45-52 | UNCOMMITTED |
```

Human will decide whether to commit before Phase 4.

### "Script uses main(argv) not run(argv)"

This is valid. Document it in Section 8:

```markdown
**Entry Point:** `main(argv)` — note: orchestrators must invoke via `main()` or subprocess
```

### "I can't find line numbers for evidence"

Use grep or editor search:

```powershell
# Find specific function
Select-String -Path {SCRIPT_PATH} -Pattern "def run\(" | Select-Object LineNumber

# Find retention logic
Select-String -Path {SCRIPT_PATH} -Pattern "prune_run_directories" | Select-Object LineNumber
```

### "Gap priority is unclear"

Use this decision tree:
1. Does it block deployment? → **HIGH**
2. Does it cause data loss? → **HIGH**
3. Does it break orchestration? → **HIGH**
4. Is it non-compliant but works? → **MEDIUM**
5. Is it nice-to-have? → **LOW**

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-02-02 | Initial phase extraction from monolithic workflow |
