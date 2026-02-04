---
title: "Orchestrator Build Template"
tier: working-document
audience:
  - coding_agent
  - human_developer
owners:
  - repo_studios_team@rainmakerprotocol.dev
role:
  - build-template
  - phase-4-artifact
status: active
category: orchestrator
schema_version: "1.0.0"
registry_version: "1.0.0"
valid_until: <YYYY-MM-DD>
version: 1.1.0
updated_at: 2026-02-03
tags:
  - stage-12
  - orchestrator
  - phase-4
  - <RECORD_ID>
related_files:
  - <SCRIPT_PATH>
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/stage12_templates/manifest.yaml
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/tier2_available_scripts_roster.md
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/implementation_plans/stage12_template_development_plan.md
  - .repo_studios/command_center/scripts/libraries/topic_pipeline.py
  - .repo_studios/command_center/scripts/libraries/database_integration.py
---

<!--
EXECUTION_ORDER:
  PROMPT-01-SETUP: 0. INPUT (CHECKPOINT-0, STOP_GATE) → 1. IDENTIFY (CHECKPOINT-1)
  PROMPT-2A-ANALYZE: 2.1-2.4 (CHECKPOINT-2A)
  PROMPT-2B-VERIFY: 2.5-2.7 (CHECKPOINT-2B, STOP_GATE)
  PROMPT-34-PREPARE: 3. Tier-3 (CHECKPOINT-3) → 4. DB (CHECKPOINT-4)
  PROMPT-5-GAPS: 5. Gaps (CHECKPOINT-5)
  PROMPT-67-EVIDENCE: 6. Changes (CHECKPOINT-6) → 7. Evidence (CHECKPOINT-7)
  PROMPT-8-ORCHESTRATOR: 8. Pipeline Config (CHECKPOINT-8)
  PROMPT-910-CLOSE: 9. Attest (CHECKPOINT-9, STOP_GATE) → 10. Finalize (CHECKPOINT-10, STOP_GATE)

CRITICAL_PATH: CHECKPOINT-0 → CHECKPOINT-2B → CHECKPOINT-9 → CHECKPOINT-10
STOP_GATES: CHECKPOINT-0, CHECKPOINT-2B, CHECKPOINT-9, CHECKPOINT-10
-->

<!-- markdownlint-disable-next-line MD025 -->
# Orchestrator Build Template — <SCRIPT_NAME>

> **Purpose:** Working document for Phase 4 per-script processing of <RECORD_ID>.
> This template will evolve as the orchestrator is inspected, modified, documented, and tested.
> Upon completion, content transfers to Tier-2 and this doc is archived with `status: archived`.
>
> **Record ID:** <RECORD_ID>
> **Status:** `active`
> **Created:** <YYYY-MM-DD>
> **Completed:** (pending)
>
> **Category:** Orchestrator
>
> **Orchestrator Principle:** Orchestrators coordinate the execution of MULTIPLE scripts
> in a defined sequence. They manage TopicStep lists, handle step failures, and produce
> HOP bundles containing pipeline telemetry and artifact references.
>
> **Universal Law:** Every script in the HealthView pipeline SHALL be orchestration-ready,
> agent-discoverable via Tier-3 YAML, and database-integration prepared — regardless of
> whether it is currently assigned to an orchestrator.

> **Note:** Nested orchestration (orchestrator calling orchestrator) is not supported.
> Each orchestrator manages its own topic independently.

---

## Status Values Legend

| Status | Meaning | Agent Action |
|--------|---------|--------------|
| `PENDING` | Not yet verified | Agent must verify and update |
| `PASS` | Requirement met | No action — evidence provided |
| `FAIL` | Requirement not met | Agent must fix before proceeding |
| `SKIP` | Not applicable to this tier | Agent skips this check |
| `N/A` | Explicitly not applicable | Agent acknowledges and moves on |

---

## Requirements Registry

> **Purpose:** Single source of truth for all compliance requirements.
> Other sections reference these IDs instead of repeating requirements.

### Universal Interface Contract (UIC) — Tier A & B

| ID | Requirement | Evidence Location |
|----|-------------|-------------------|
| UIC-001 | `run(argv)` entry point exists | `<path>:<line>` |
| UIC-002 | `run()` returns `dict[str, Any]` | `<path>:<line>` |
| UIC-003 | Return dict has `status` key | `<path>:<line>` |
| UIC-004 | Return dict has `exit_code` key | `<path>:<line>` |
| UIC-005 | `--repo-root` flag supported | `<path>:<line>` |
| UIC-006 | `--log-level` flag supported | `<path>:<line>` |
| UIC-007 | Google-style docstring on `run()` | `<path>:<line>` |
| UIC-008 | No `sys.exit()` inside `run()` | grep confirms |
| UIC-009 | No `input()` prompts | grep confirms |
| UIC-010 | Exceptions return error payload | `<path>:<line>` |

### HOP Bundle Contract (HOP) — Tier A Only

| ID | Requirement | Evidence Location |
|----|-------------|-------------------|
| HOP-001 | Base package: manifest.json | `<path>:<line>` |
| HOP-002 | Base package: summary.md | `<path>:<line>` |
| HOP-003 | Base package: telemetry.json | `<path>:<line>` |
| HOP-004 | Uses `build_topic_path()` or `create_storage()` | `<path>:<line>` |
| HOP-005 | Uses `prune_run_directories()` | `<path>:<line>` |
| HOP-006 | No `latest_*` pointer files | grep confirms |
| HOP-007 | Directory format `YYYYMMDD-HHMM` | `<path>:<line>` |
| HOP-008 | `--artifacts-to-keep` flag supported | `<path>:<line>` |

### Agent Discoverability (AGT) — Tier A & B

| ID | Requirement | Evidence Location |
|----|-------------|-------------------|
| AGT-001 | Tier-3 YAML exists | `<tier3_path>` |
| AGT-002 | Tier-3 `tool.id` matches script | `<tier3_path>` |
| AGT-003 | Tier-3 `invocation.script_path` correct | `<tier3_path>` |
| AGT-004 | Tier-3 `cli_surfaces` complete | `<tier3_path>` |

### Database Integration (DBI) — Tier A & B

| ID | Requirement | Evidence Location |
|----|-------------|-------------------|
| DBI-001 | Uses `create_storage()` for writes | `<path>:<line>` |
| DBI-002 | `DB_INTEGRATION_MARKER:` at write points | `<path>:<line>` |
| DBI-003 | Gated by `REPO_STUDIOS_DB_ENABLED` | `<path>:<line>` |

### Orchestration Readiness (ORC) — Tier A & B

| ID | Requirement | Evidence Location |
|----|-------------|-------------------|
| ORC-001 | Can be dynamically imported | importlib test |
| ORC-002 | Idempotent (safe to re-run) | test confirms |
| ORC-003 | Pipeline configuration documented | Section 8 |

### Pipeline Coordination (PPC) — Orchestrator Only

> **Purpose:** Orchestrator-specific requirements for multi-script pipeline coordination.
> These requirements are IN ADDITION to UIC/HOP/AGT/DBI/ORC.

| ID | Requirement | Evidence Location |
|----|-------------|-------------------|
| PPC-001 | TopicStep list defines execution order | Section 2.5 |
| PPC-002 | Per-step skip flags (`--skip-{step}`) supported | Section 2.6 |
| PPC-003 | Per-step output directories configurable | `<path>:<line>` |
| PPC-004 | Per-step keep budgets configurable | `<path>:<line>` |
| PPC-005 | Step failure propagation policy documented | Section 2.7 |
| PPC-006 | Step dependencies resolved correctly | Section 2.5 |
| PPC-007 | Uses TopicPipeline execution pattern (inline closures OR `build_topic_pipeline()`) | `<path>:<line>` |
| PPC-008 | Supports `--timestamp` for shared run timestamp | `<path>:<line>` |
| PPC-009 | Uses `write_report_artifacts()` for HOP bundle creation | `<path>:<line>` |

> **Registry Usage:** During inspection, fill the Evidence Location column with actual `<path>:<line>`
> references. Section 2.4 tables provide expanded context for each check.
>
> At completion, every row in this registry MUST have either:
>
> - Actual evidence location (e.g., `run_docs_health.py:1954`)
> - `grep confirms` (for negative checks like "no sys.exit")
> - `DEVIATION: <reason>` (for permitted deviations)
> - `N/A` (for tier-conditional requirements)

---

## 0. INPUT: Assignment Contract

<!-- METAPROMPT: PROMPT-01-SETUP -->
<!-- CHECKPOINT_ID: CHECKPOINT-0 -->
<!-- STOP_CONDITION: All REQUIRED inputs have Status = PASS -->
<!-- PROCEED_SIGNAL: "CHECKPOINT-0: Inputs verified — SCRIPT_PATH, RECORD_ID, COMPLIANCE_TIER, TARGET_STAGE confirmed" -->
<!-- REENTRY_POINT: PROMPT-01-SETUP (restart from beginning) -->

<!-- STOP_GATE: TRUE -->

> **Purpose:** Define what information must be provided BEFORE starting this template.
> Agent cannot proceed until all REQUIRED inputs are supplied.

### 0.1 Required Inputs

| Input | Source | Example | Status |
|-------|--------|---------|--------|
| `SCRIPT_PATH` | Assignment or discovery | `.repo_studios/command_center/scripts/orchestrators/run_docs_health.py` | `PENDING` |
| `RECORD_ID` | Tier-2 roster or assigned | `S21R-001` | `PENDING` |
| `COMPLIANCE_TIER` | Classification (A or B) | `A` | `PENDING` |
| `TARGET_STAGE` | Assignment | `Stage 21` | `PENDING` |

### 0.2 Orchestrated Steps — REQUIRED

> ⚠️ **ORCHESTRATOR REQUIREMENT:** Document ALL steps this orchestrator coordinates.
> Add rows as needed — one per TopicStep in the pipeline.

| # | Step Name | Script | Record ID | Skip Flag | Output Dir Flag | Keep Flag |
|---|-----------|--------|-----------|-----------|-----------------|-----------|
| 1 | `<step_name_1>` | `<script_1.py>` | `<S##R-###>` | `--skip-<step1>` | `--<step1>-output-dir` | `--<step1>-artifacts-to-keep` |
| 2 | `<step_name_2>` | `<script_2.py>` | `<S##R-###>` | `--skip-<step2>` | `--<step2>-output-dir` | `--<step2>-artifacts-to-keep` |
| 3 | `<step_name_3>` | `<script_3.py>` | `<S##R-###>` | `--skip-<step3>` | `--<step3>-output-dir` | `--<step3>-artifacts-to-keep` |
<!-- Add additional rows for each step in the pipeline -->

**Step count:** `<N>` steps documented

**How to discover steps:**

1. Search for `TopicStep(` or `build_topic_pipeline(` in the script
2. Look for step runner functions (e.g., `_execute_*`, `*_step`)
3. Check `--help` output for `--skip-*` flags
4. Review the script's docstring for pipeline description

### 0.3 Classification Rules

**How to determine COMPLIANCE_TIER:**

| If script... | Then Tier = | Rationale |
|--------------|-------------|-----------|
| Coordinates multiple scripts via TopicStep and produces HOP bundle | **A** | Orchestrator (Report Generator) |
| Coordinates scripts but produces no HOP bundle | **B** | Orchestrator (Utility) |
| Is unclear | **A** | Default to stricter requirements |

**Classification Decision:** Tier {A|B} — {rationale}

> **Note:** Most orchestrators are Tier A because they produce pipeline telemetry bundles.
> Tier B orchestrators are rare and typically used for one-off coordination tasks.

<!-- PROCEED_WHEN: All REQUIRED inputs have status PASS -->

> **⚠️ STOP:** Do not proceed to Section 1 until all REQUIRED inputs are provided.

---

## 1. IDENTIFY: Script Identity

<!-- METAPROMPT: PROMPT-01-SETUP -->
<!-- CHECKPOINT_ID: CHECKPOINT-1 -->
<!-- STOP_CONDITION: All fields in identity table populated, 1.1 and 1.2 completed -->
<!-- PROCEED_SIGNAL: "CHECKPOINT-1: Script identity captured — {SCRIPT_NAME} is Tier {A/B}, {N} steps" -->
<!-- REENTRY_POINT: PROMPT-01-SETUP -->

<!-- PROCEED_WHEN: All fields in identity table populated -->

| Field | Value |
|-------|-------|
| **Name** | `<SCRIPT_NAME>` |
| **Path** | `<SCRIPT_PATH>` |
| **Tier Class** | Orchestrator |
| **Compliance Tier** | A (Report Generator) / B (Utility Orchestrator) |
| **Lines** | <LINE_COUNT> |
| **Record ID** | <RECORD_ID> |
| **Planned Stage** | <TARGET_STAGE> |
| **Step Count** | <N> (from Section 0.2) |

**Compliance Tier Definitions:**

- **Tier A (Report Generator):** Produces HOP bundles (manifest/summary/telemetry). Includes
  Producers, Consumers, Aggregators, Summarizers, and most Orchestrators.
- **Tier B (Utility Orchestrator):** Coordinates scripts without producing HOP bundles.
  Rare — typically one-off coordination tasks.

### 1.1 DESCRIBE: Purpose

<Brief description of what this orchestrator coordinates and why>

### 1.2 LIST: Current Capabilities

- <Capability 1: e.g., "Executes 8 health check scripts in sequence">
- <Capability 2: e.g., "Aggregates results into unified health report">
- <Capability 3: e.g., "Supports per-step skip flags for selective execution">

### 1.3 Verification Log

| Date | Inspector | Findings | Status |
|------|-----------|----------|--------|
| <YYYY-MM-DD> | <agent/human> | <summary of verification> | `PASS` / `FAIL` / `GAPS_FOUND` |

---

## 2. ANALYZE: Current State

<!-- METAPROMPT: PROMPT-2A-ANALYZE -->
<!-- CHECKPOINT_ID: CHECKPOINT-2A -->
<!-- STOP_CONDITION: Sections 2.1-2.4 complete, all Status columns != PENDING -->
<!-- PROCEED_SIGNAL: "CHECKPOINT-2A: Static analysis complete — UIC checklist has {X} PASS, {Y} FAIL, {N} steps documented" -->
<!-- REENTRY_POINT: PROMPT-2A-ANALYZE -->
<!-- TIER_CHECK: If COMPLIANCE_TIER == "B", skip sections 2.2.2(Tier A), 2.3, 2.4.2 -->

### 2.1 DOCUMENT: CLI Interface

```text
usage: <SCRIPT_NAME> [-h] [--repo-root REPO_ROOT] ...
```

**Flags:**

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--repo-root` | path | auto | Repository root override |
| `--output-dir` | path | HOP default | Output directory for pipeline bundle |
| `--timestamp` | str | auto | ISO timestamp override (shared across steps) |
| `--log-level` | choice | INFO | Logging verbosity |
| `--artifacts-to-keep` | int | 5 | Retention budget for pipeline bundles |
| `--skip-<step1>` | flag | false | Skip step 1 |
| `--skip-<step2>` | flag | false | Skip step 2 |
<!-- Add --skip-* flags for each step from Section 0.2 -->
| <additional flags> | | | |

### 2.2 INSPECT: Entry Points

| Entry | Signature | Returns | Status |
|-------|-----------|---------|--------|
| `main(argv)` | `list[str] \| None` → `int` | Exit code | `PENDING` |
| `run(argv)` | `list[str] \| None` → `dict[str, Any]` | Payload dict | `PENDING` |

#### 2.2.1 Universal Interface Contract (ALL Scripts)

<!-- TIER: A,B -->
<!-- PROCEED_WHEN: All Status columns = PASS or SKIP -->

> **Applies to:** All scripts (Tier A and B)

> **⚠️ MANDATORY — Every script MUST pass this section regardless of Tier Class.**

| Requirement | ID | Status | Evidence |
|-------------|----|--------|----------|
| `run(argv)` entry point exists | UIC-001 | `PENDING` | `<path>:<line>` |
| Returns `dict[str, Any]` (not int) | UIC-002 | `PENDING` | `<path>:<line>` |
| Return dict has `status` key | UIC-003 | `PENDING` | `<path>:<line>` |
| Return dict has `exit_code` key | UIC-004 | `PENDING` | `<path>:<line>` |
| `--repo-root` flag supported | UIC-005 | `PENDING` | `<path>:<line>` |
| `--log-level` flag supported | UIC-006 | `PENDING` | `<path>:<line>` |
| Google-style docstring on `run()` | UIC-007 | `PENDING` | `<path>:<line>` |
| No `sys.exit()` inside `run()` | UIC-008 | `PENDING` | grep confirms |
| No `input()` prompts | UIC-009 | `PENDING` | grep confirms |
| Exceptions return error payload | UIC-010 | `PENDING` | `<path>:<line>` |

#### 2.2.2 Return Payload Contract

<!-- TIER: A -->
<!-- SKIP_IF: compliance_tier == "B" -->

> **Applies to:** Tier A (Report Generators) only
> **Skip if:** Compliance Tier = B

**Tier A (Orchestrators) — REQUIRED keys:**

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `status` | str | ✅ | "ok", "error", "partial" (some steps failed) |
| `exit_code` | int | ✅ | 0=all success, 1=partial, 2=error |
| `run_dir` | str | ✅ | Path to pipeline bundle directory |
| `output_dir` | str | ✅ | Parent output directory |
| `run_id` | str | ✅ | Timestamp slug (YYYYMMDD-HHMM) |
| `manifest` | dict | ✅ | Full manifest content |
| `telemetry` | dict | ✅ | Full telemetry including per-step timing |
| `summary` | dict | ✅ | Summary with pipeline status table |
| `steps` | list | ✅ | Per-step outcomes (name, status, duration) |

<!-- TIER: B -->
<!-- SKIP_IF: compliance_tier == "A" -->

> **Applies to:** Tier B (Utility Orchestrators) only
> **Skip if:** Compliance Tier = A

**Tier B (Utility Orchestrators) — REQUIRED keys:**

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `status` | str | `PASS` | "ok" or "error" |
| `exit_code` | int | `PASS` | 0=success, non-zero=failure |
| `steps_executed` | int | `PASS` | Number of steps completed |
| `artifacts` | None | `PASS` | Explicit null (no bundle produced) |
| `details` | dict | `PENDING` | Optional per-step details |

### 2.3 DOCUMENT: Output Contract

<!-- TIER: A -->
<!-- SKIP_IF: compliance_tier == "B" -->

> **Applies to:** Tier A (Report Generators) only
> **Skip if:** Compliance Tier = B

**Output root:** `.repo_studios/reports/healthview/producer_reports/<TOPIC>/<YYYYMMDD-HHMM>/`

> **Note:** Orchestrators use `producer_reports/` like other Tier A scripts, not a separate
> `orchestrator_reports/` directory. The exact path may vary by viewer/topic configuration.

**Artifacts:**

| Artifact | Format | Description |
|----------|--------|-------------|
| `manifest.json` | JSON | Schema version, step list, overall status |
| `summary.md` | Markdown | Human-readable pipeline status table |
| `telemetry.json` | JSON | Per-step timing, dependencies, outcomes |
| <additional artifacts> | | |

### 2.4 ASSESS: Compliance

<!-- PROCEED_WHEN: All compliance checks have Status != PENDING -->

#### 2.4.1 Universal Compliance (Tier A & B)

<!-- TIER: A,B -->

> **Applies to:** All scripts (Tier A and B)

| Requirement | Status | Evidence |
|-------------|--------|----------|
| `run(argv)` returns dict | `PENDING` | <evidence> |
| Status/exit_code in return | `PENDING` | <evidence> |
| Standard CLI flags (repo-root, log-level) | `PENDING` | <evidence> |
| Can be dynamically imported | `PENDING` | `importlib.util` works |
| Idempotent (safe to re-run) | `PENDING` | Multiple runs don't corrupt |

> **⚠️ ORCHESTRATOR-SPECIFIC DEVIATION:** UIC-002 permits orchestrators to return `int` (exit code)
> instead of `dict[str, Any]`. This is acceptable because:
>
> 1. Orchestrators are top-level entry points, not consumed by other scripts
> 2. Nested orchestration is not supported (stated in template header)
> 3. Pipeline telemetry captures all diagnostic information in the bundle
>
> **Exit code semantics (if `int` return):**
>
> | Exit Code | Meaning |
> |-----------|---------|
> | `0` | All steps succeeded |
> | `1` | One or more steps failed |
> | `2` | Pipeline error (couldn't complete) |
>
> If `int` is returned, mark UIC-002 as `DEVIATION: int return acceptable for orchestrators`

#### 2.4.2 HOP Bundle Compliance (Tier A Only)

<!-- TIER: A -->
<!-- SKIP_IF: compliance_tier == "B" -->

> **Applies to:** Tier A (Report Generators) only
> **Skip if:** Compliance Tier = B

| Requirement | ID | Status | Evidence |
|-------------|----|--------|----------|
| Base package: manifest.json | HOP-001 | `PENDING` | `<path>:<line>` |
| Base package: summary.md | HOP-002 | `PENDING` | `<path>:<line>` |
| Base package: telemetry.json | HOP-003 | `PENDING` | `<path>:<line>` |
| Uses `build_topic_path()` or `create_storage()` | HOP-004 | `PENDING` | `<path>:<line>` |
| Uses `prune_run_directories()` | HOP-005 | `PENDING` | `<path>:<line>` |
| No `latest_*` pointer files | HOP-006 | `PENDING` | grep confirms |
| Directory format `YYYYMMDD-HHMM` | HOP-007 | `PENDING` | `<path>:<line>` |
| `--artifacts-to-keep` flag supported | HOP-008 | `PENDING` | `<path>:<line>` |

### 2.5 DOCUMENT: TopicStep Registry — MANDATORY FOR ORCHESTRATORS

<!-- ORCHESTRATOR_SPECIFIC: TRUE -->
<!-- PPC_CHECK: PPC-001, PPC-006 -->

> ⚠️ **ORCHESTRATOR REQUIREMENT:** The TopicStep registry MUST be documented.
> This section captures all steps in the pipeline and their execution order.

#### 2.5.1 Pipeline Definition

**Pipeline construction code location:** `<path>:#L<line>`

**Two valid patterns:**

**Pattern A — Inline step closures** (recommended for complex orchestrators):

```python
def step_name_step(_: TopicContext) -> TopicStepOutcome:
    if options.skip_step:
        return step_skipped(detail="step skipped")
    try:
        outcome = _execute_step(paths, options)
    except Exception as exc:
        return step_failed(detail=str(exc))
    return step_success(detail=..., payload=...)

steps = [
    TopicStep(name="step-1", runner=step_1_step),
    TopicStep(name="step-2", runner=step_2_step),
    ...
]
result = TopicPipeline(steps=steps).execute(ctx)
```

- Full control over skip logic and error handling
- Each step is a closure function returning `TopicStepOutcome`

**Pattern B — `build_topic_pipeline()` helper** (recommended for simple orchestrators):

```python
pipeline = build_topic_pipeline(
    scripts=[
        ScriptConfig(name="script_1", path="..."),
        ScriptConfig(name="script_2", path="..."),
    ],
    options=options,
)
result = pipeline.execute(ctx)
```

- Declarative script list using `ScriptConfig`
- Less boilerplate, but less flexibility

**Pattern used:** `{inline_closures | build_topic_pipeline}`

#### 2.5.2 Step Details

| # | Step Name | Runner Function | Script Invoked | Dependencies | Code Reference |
|---|-----------|-----------------|----------------|--------------|----------------|
| 1 | `<step_name>` | `<runner_func>()` | `<script.py>` | (none) | `<path>:#L<line>` |
| 2 | `<step_name>` | `<runner_func>()` | `<script.py>` | Step 1 | `<path>:#L<line>` |
<!-- Add row for each TopicStep -->

#### 2.5.3 Execution Order Verification

| Check | Status | Evidence |
|-------|--------|----------|
| Steps execute in documented order | `PENDING` | Pipeline run log shows sequential execution |
| Dependencies respected | `PENDING` | Later steps receive earlier step outputs |
| No circular dependencies | `PENDING` | Execution completes without loops |

### 2.6 DOCUMENT: Skip Flag Matrix — MANDATORY FOR ORCHESTRATORS

<!-- ORCHESTRATOR_SPECIFIC: TRUE -->
<!-- PPC_CHECK: PPC-002 -->

> ⚠️ **ORCHESTRATOR REQUIREMENT:** All skip flags MUST be documented.

| Flag | Default | Step Skipped | Effect on Pipeline | Code Reference |
|------|---------|--------------|-------------------|----------------|
| `--skip-<step1>` | `false` | Step 1: `<step_name>` | Downstream steps may fail if dependent | `<path>:#L<line>` |
| `--skip-<step2>` | `false` | Step 2: `<step_name>` | `<effect>` | `<path>:#L<line>` |
<!-- Add row for each skip flag -->

**Total skip flags:** `<N>`

**Skip flag verification:**

```bash
python <script> --help | grep -E "skip"
```

### 2.7 DOCUMENT: Failure Propagation Policy — MANDATORY FOR ORCHESTRATORS

<!-- ORCHESTRATOR_SPECIFIC: TRUE -->
<!-- PPC_CHECK: PPC-005 -->

> ⚠️ **ORCHESTRATOR REQUIREMENT:** The failure policy MUST be documented.

#### 2.7.1 Default Behavior

| Setting | Value | Code Reference |
|---------|-------|----------------|
| `stop_on_failure` | `true` / `false` | `<path>:#L<line>` |
| `continue_on_failure` | `true` / `false` | `<path>:#L<line>` |
| `raise_for_failure()` called | `YES` / `NO` | `<path>:#L<line>` |

#### 2.7.2 Per-Step Failure Behavior

| Scenario | Orchestrator Behavior | Exit Code | Code Reference |
|----------|----------------------|-----------|----------------|
| Step 1 fails | `<STOP / CONTINUE>` | `<code>` | `<path>:#L<line>` |
| Middle step fails | `<STOP / CONTINUE>` | `<code>` | `<path>:#L<line>` |
| Last step fails | `<STOP / CONTINUE>` | `<code>` | `<path>:#L<line>` |
| All steps succeed | Normal completion | `0` | `<path>:#L<line>` |

#### 2.7.3 Failure Recovery Options

| Option | Supported? | How to Use |
|--------|------------|------------|
| Resume from failed step | `YES` / `NO` | `<command or N/A>` |
| Skip failed step and continue | `YES` / `NO` | `<command or N/A>` |
| Retry failed step | `YES` / `NO` | `<command or N/A>` |

### 2.8 VERIFY: Output Quality

<!-- METAPROMPT: PROMPT-2B-VERIFY -->
<!-- CHECKPOINT_ID: CHECKPOINT-2B -->
<!-- STOP_CONDITION: 2.8.1 QA all PASS, 2.8.5 truth table all Verdict = TRUE -->
<!-- PROCEED_SIGNAL: "CHECKPOINT-2B: Output truth verified — script executed, all claims TRUE, {N} steps executed" -->
<!-- REENTRY_POINT: PROMPT-2B-VERIFY (critical gate — must re-verify from scratch) -->
<!-- TIER_CHECK: If COMPLIANCE_TIER == "B", skip sections 2.8.2, 2.8.3 -->

> **⚠️ MANDATORY STOP-GATE — DO NOT SKIP**
>
> This section is the **PROOF OF THE ORCHESTRATOR**. A script that passes mypy/pytest but
> produces incorrect, misleading, or unverifiable output is **WORTHLESS**. Every claim in
> the output artifacts MUST be verified against ground truth. If any claim is false, the
> script is BROKEN regardless of test results.
>
> **Agent Instruction:** You MUST run the orchestrator, read every output file, and verify
> each claim against the actual filesystem/codebase state. Do not proceed until all claims
> are TRUE.

**MANDATORY: Run orchestrator and inspect actual output before completing this section.**

#### 2.8.1 QA Verification

| Check | Command | Result | Evidence | CI/Artifact Link |
|-------|---------|--------|----------|------------------|
| mypy --strict | `python -m mypy --strict <script>` | `PENDING` | <error count or "Success"> | `<CI_URL or N/A>` |
| pytest | `pytest <test_file> -v` | `PENDING` | <X/Y passed in Z.ZZs> | `<CI_URL or N/A>` |
| CLI execution | `python <script> --help` | `PENDING` | <runs without error> | `N/A` |
| Actual run | `python <script> --log-level DEBUG` | `PENDING` | <output path confirmed> | `<artifact_path>` |

#### 2.8.2 summary.md Quality (Pipeline Status)

<!-- TIER: A -->
<!-- SKIP_IF: compliance_tier == "B" -->

> **Applies to:** Orchestrators — checks for pipeline-specific content

| Check | Status | Evidence |
|-------|--------|----------|
| Markdownlint clean | `PENDING` | `npx markdownlint-cli2 <summary.md>` — 0 errors |
| Single H1 heading | `PENDING` | `<heading text>` |
| Pipeline Status table present | `PENDING` | Table shows per-step success/failure |
| Per-step timing included | `PENDING` | Each step shows duration |
| Artifact references included | `PENDING` | Links to step output bundles |
| Overall pipeline result shown | `PENDING` | SUCCESS / PARTIAL / FAILED status |

#### 2.8.3 Machine-Readable Artifacts (JSON Quality)

<!-- TIER: A -->
<!-- SKIP_IF: compliance_tier == "B" -->

> **Applies to:** Tier A (Report Generators) only
> **Skip if:** Compliance Tier = B

| Check | Status | Evidence |
|-------|--------|----------|
| manifest.json valid JSON | `PENDING` | `python -m json.tool <file>` |
| telemetry.json valid JSON | `PENDING` | `python -m json.tool <file>` |
| Schema version present | `PENDING` | `schema_version` field in manifest |
| Timestamp ISO 8601 format | `PENDING` | `YYYY-MM-DDTHH:MM:SS+00:00` |
| Status field present | `PENDING` | `status: ok\|error\|partial` |
| Consistent key naming | `PENDING` | snake_case throughout |
| Steps array present | `PENDING` | `steps` field in telemetry |

#### 2.8.4 DB Integration Markers

> **⚠️ MANDATORY — Every script MUST have DB Integration markers for future database migration.**
>
> Even if database writes are currently dormant, the markers MUST be present so that when
> database integration is enabled, the script is ready without code changes.

| Check | Status | Evidence |
|-------|--------|----------|
| `from libraries.database_integration import create_storage` | `PENDING` | `<path>:<line>` |
| DB_INTEGRATION_MARKER comments present | `PENDING` | `<path>:<line>` |
| Marker at manifest.json write | `PENDING` | `<path>:<line>` |
| Marker at summary.md write | `PENDING` | `<path>:<line>` |
| Marker at telemetry.json write | `PENDING` | `<path>:<line>` |
| Uses `create_storage()` for writes | `PENDING` | `<path>:<line>` |
| Marker describes target table/column | `PENDING` | `<path>:<line>` |

**Tier B (Utility Orchestrators) DB Markers:**

| Check | Status | Evidence |
|-------|--------|----------|
| DB_INTEGRATION_MARKER at action log point | `PENDING` | `<path>:<line>` |
| Marker describes action_log table intent | `PENDING` | `<path>:<line>` |

#### 2.8.5 Output Truth Verification (CRITICAL)

<!-- STOP_GATE: TRUE -->
<!-- PROCEED_WHEN: All claims in truth table have Verdict = TRUE -->

> **⚠️ MANDATORY STOP — DO NOT PROCEED UNTIL ALL CLAIMS VERIFIED**
>
> Read every claim in summary.md and manifest.json. Verify each against ground truth.
> An orchestrator that reports "8/8 steps succeeded" when 2 steps were skipped is **LYING**.
> An orchestrator that references output paths that don't exist is **BROKEN**.

| Claim in Output | Verification Method | Ground Truth | Verdict |
|-----------------|---------------------|--------------|---------|
| <claim from summary.md> | <how to verify> | <actual state> | ✅/❌ |
| <step count is accurate> | Count TopicSteps in code | <actual count> | ✅/❌ |
| <all step outputs exist> | `Test-Path` for each | <true/false> | ✅/❌ |
| <per-step timing accurate> | Cross-reference logs | <durations match> | ✅/❌ |
| <failure propagation correct> | Induce failure, verify behavior | <behavior matches policy> | ✅/❌ |

**If ANY claim is FALSE, the orchestrator is BROKEN. Fix it before proceeding.**

### 2.9 Verification Log

| Date | Inspector | Findings | Status |
|------|-----------|----------|--------|
| <YYYY-MM-DD> | <agent/human> | <summary of verification> | `PASS` / `FAIL` / `GAPS_FOUND` |

---

## 3. PREPARE: Tier-3 YAML

> **⚠️ MANDATORY — Every script MUST have a Tier-3 YAML for agent discoverability.**
>
> Agents discover and invoke scripts via Tier-3 metadata. A script without Tier-3 YAML is
> invisible to agents. Even Orchestrators need Tier-3 for agents to know they exist.

<!-- METAPROMPT: PROMPT-34-PREPARE -->
<!-- CHECKPOINT_ID: CHECKPOINT-3 -->
<!-- STOP_CONDITION: Tier-3 YAML exists, 3.2 fields all Status = PASS -->
<!-- PROCEED_SIGNAL: "CHECKPOINT-3: Tier-3 YAML verified at {tier3_path}" -->
<!-- REENTRY_POINT: PROMPT-34-PREPARE -->

### 3.1 LOCATE: Tier-3 YAML

**Expected path:** `<SCRIPT_DIR>/<SCRIPT_NAME>.tier3.yaml` or inline in script inventory

| Check | Status | Evidence |
|-------|--------|----------|
| Tier-3 YAML file exists | `PENDING` | Path: <path> |
| YAML is valid (no syntax errors) | `PENDING` | `python -c "import yaml; yaml.safe_load(...)"` |
| Registered in script inventory | `PENDING` | Inventory record at <location> |

### 3.2 VERIFY: Tier-3 Required Fields

| Field | Status | Value |
|-------|--------|-------|
| `name` | `PENDING` | `<SCRIPT_NAME>` |
| `path` | `PENDING` | `<SCRIPT_PATH>` |
| `category` | `PENDING` | orchestrator |
| `compliance_tier` | `PENDING` | A (Report Generator) / B (Utility Orchestrator) |
| `entry_point` | `PENDING` | `run` |
| `description` | `PENDING` | <one-line description> |
| `inputs` | `PENDING` | List of input parameters including skip flags |
| `outputs` | `PENDING` | Description of return payload |
| `orchestrator_ready` | `PENDING` | `true` (orchestrators are self-managing) |
| `db_integration_ready` | `PENDING` | `true` / `false` |
| `steps` | `PENDING` | List of orchestrated steps (orchestrator-specific) |

### 3.3 REFERENCE: Tier-3 YAML Template (Orchestrator)

```yaml
# Tier-3 Metadata for <SCRIPT_NAME>
# Agent-discoverable orchestrator definition
name: <SCRIPT_NAME>
path: <SCRIPT_PATH>
category: orchestrator
compliance_tier: <A|B>
entry_point: run
description: "<One-line description of what this orchestrator coordinates>"
version: "1.0.0"

inputs:
  - name: repo_root
    type: path
    required: false
    description: "Repository root override"
  - name: log_level
    type: choice
    choices: [DEBUG, INFO, WARNING, ERROR]
    default: INFO
    description: "Logging verbosity"
  - name: timestamp
    type: string
    required: false
    description: "Shared timestamp for all steps (YYYYMMDD-HHMM)"
  - name: skip_<step1>
    type: flag
    default: false
    description: "Skip <step1> execution"
  # <additional skip flags per step>

outputs:
  status: "ok|error|partial"
  exit_code: "0=all success, 1=partial, 2=error"
  steps: "Array of per-step outcomes"
  # <additional outputs per compliance tier>

orchestrator_ready: true  # Orchestrators manage themselves
db_integration_ready: true

# Orchestrator-specific: list of coordinated steps
steps:
  - name: <step1>
    script: <script1.py>
    record_id: <S##R-###>
  - name: <step2>
    script: <script2.py>
    record_id: <S##R-###>
  # <additional steps>

tags:
  - orchestrator
  - <topic>

consumers:
  - coding_agent
  - human_developer
  - ci_pipeline
```

### 3.4 Verification Log

| Date | Inspector | Findings | Status |
|------|-----------|----------|--------|
| <YYYY-MM-DD> | <agent/human> | <summary of verification> | `PASS` / `FAIL` / `GAPS_FOUND` |

---

## 4. PREPARE: Database Integration

<!-- METAPROMPT: PROMPT-34-PREPARE -->
<!-- CHECKPOINT_ID: CHECKPOINT-4 -->
<!-- STOP_CONDITION: 4.2 checklist all Status = PASS or N/A -->
<!-- PROCEED_SIGNAL: "CHECKPOINT-4: DB integration markers present — {count} write points covered" -->
<!-- REENTRY_POINT: PROMPT-34-PREPARE -->

> **⚠️ MANDATORY — Every script MUST be database-integration prepared.**
>
> When database integration is enabled, scripts will write to both filesystem AND database.
> The `create_storage()` helper handles this transparently, but scripts must be structured
> correctly for the dual-write to work.

### 4.1 DOCUMENT: DB Schema Intent

**For Tier A (Orchestrators):**

| Artifact | Target Table | Key Columns |
|----------|--------------|-------------|
| manifest.json | `hop_manifests` | viewer_slug, topic, run_timestamp, schema_version, steps_count |
| summary.md | `hop_summaries` | viewer_slug, topic, run_timestamp, content_md, pipeline_status |
| telemetry.json | `hop_telemetry` | viewer_slug, topic, run_timestamp, metrics_json, step_timings |

**For Tier B (Utility Orchestrators):**

| Action | Target Table | Key Columns |
|--------|--------------|-------------|
| Action log | `utility_actions` | script_name, steps_executed, status, timestamp |

### 4.2 CHECK: DB Integration Readiness

| Check | Status | Evidence |
|-------|--------|----------|
| Uses `create_storage()` (not raw file writes) | `PENDING` | <evidence> |
| Passes `viewer_slug` correctly | `PENDING` | Empty string or valid slug |
| Passes `topic` correctly | `PENDING` | TOPIC_SLUG constant |
| Passes `timestamp` correctly | `PENDING` | YYYYMMDD-HHMM format |
| All writes go through `storage.write_*()` | `PENDING` | No direct `Path.write_text()` |
| Payload is JSON-serializable | `PENDING` | No datetime objects, Path objects |
| Step outcomes are JSON-serializable | `PENDING` | All step data can be stored |

### 4.3 REFERENCE: DB Integration Marker Format

```python
# DB_INTEGRATION_MARKER: <table_name>.<column_name> — <description>
storage.write_manifest(manifest)

# DB_INTEGRATION_MARKER: hop_summaries.content_md — Pipeline status summary
storage.write_summary({"markdown": summary_md}, format="md")

# DB_INTEGRATION_MARKER: hop_telemetry.metrics_json — Per-step timing and outcomes
storage.write_telemetry(telemetry)
```

### 4.4 Verification Log

| Date | Inspector | Findings | Status |
|------|-----------|----------|--------|
| <YYYY-MM-DD> | <agent/human> | <summary of verification> | `PASS` / `FAIL` / `GAPS_FOUND` |

---

## 5. IDENTIFY: Gaps

<!-- METAPROMPT: PROMPT-5-GAPS -->
<!-- CHECKPOINT_ID: CHECKPOINT-5 -->
<!-- STOP_CONDITION: All gaps documented, example rows deleted or updated, HIGH priority gaps identified -->
<!-- PROCEED_SIGNAL: "CHECKPOINT-5: Gap analysis complete — {X} HIGH, {Y} MEDIUM, {Z} total gaps (including PPC)" -->
<!-- REENTRY_POINT: PROMPT-5-GAPS -->

### 5.1 LIST: Required Changes

<!-- PROCEED_WHEN: All HIGH priority gaps have Status != OPEN -->

> **Gap Status Values:**
> - `OPEN` — Gap identified, not yet fixed
> - `CLOSED` — Fix applied, awaiting verification
> - `VERIFIED` — Fix confirmed working

> **⚠️ EXAMPLE ROWS BELOW:** The GAP-001 through GAP-027 entries are EXAMPLES showing common gaps.
> **DELETE rows that don't apply.** Keep and update rows that match actual findings.
> **ADD new rows** for gaps not covered by examples.

#### 5.1.1 Universal Compliance Gaps

| Gap ID | Req ID | Description | Priority | Status | Closed Date |
|--------|--------|-------------|----------|--------|-------------|
<!-- EXAMPLE ROWS — Delete if not applicable to this script -->
| GAP-001 | UIC-001 | Missing `run()` entry point | High | `OPEN` | |
| GAP-002 | UIC-002 | `run()` returns int not dict | High | `OPEN` | |
| GAP-003 | UIC-005 | Missing `--repo-root` flag | High | `OPEN` | |
| GAP-004 | UIC-006 | Missing `--log-level` flag | Medium | `OPEN` | |
| GAP-005 | DBI-002 | Missing DB_INTEGRATION_MARKER comments | Medium | `OPEN` | |
| GAP-006 | AGT-001 | Missing Tier-3 YAML | High | `OPEN` | |
<!-- END EXAMPLE ROWS -->

#### 5.1.2 HOP Bundle Gaps (Tier A Only)

| Gap ID | Req ID | Description | Priority | Status | Closed Date |
|--------|--------|-------------|----------|--------|-------------|
<!-- EXAMPLE ROWS — Delete if not applicable to this script -->
| GAP-007 | HOP-004 | Not using `build_topic_path()` | High | `OPEN` | |
| GAP-008 | DBI-001 | Not using `create_storage()` | High | `OPEN` | |
| GAP-009 | HOP-001 | Missing `manifest.json` | High | `OPEN` | |
| GAP-010 | HOP-002 | Missing Pipeline Status table in summary.md | Medium | `OPEN` | |
| GAP-011 | HOP-005 | No pruning support | Medium | `OPEN` | |
| GAP-012 | HOP-008 | Missing `--artifacts-to-keep` flag | Medium | `OPEN` | |
<!-- END EXAMPLE ROWS -->

#### 5.1.3 Agent/DB Readiness Gaps

| Gap ID | Req ID | Description | Priority | Status | Closed Date |
|--------|--------|-------------|----------|--------|-------------|
<!-- EXAMPLE ROWS — Delete if not applicable to this script -->
| GAP-013 | AGT-001 | No Tier-3 YAML | High | `OPEN` | |
| GAP-014 | AGT-002 | Tier-3 YAML incomplete | Medium | `OPEN` | |
| GAP-015 | DBI-001 | Raw file writes instead of `create_storage()` | High | `OPEN` | |
| GAP-016 | UIC-010 | Payload not JSON-serializable | High | `OPEN` | |
| GAP-017 | DBI-002 | Missing DB_INTEGRATION_MARKER at write points | Medium | `OPEN` | |
<!-- END EXAMPLE ROWS -->

#### 5.1.4 Pipeline Coordination Gaps (PPC) — Orchestrators Only

| Gap ID | Req ID | Description | Priority | Status | Closed Date |
|--------|--------|-------------|----------|--------|-------------|
<!-- EXAMPLE ROWS — Delete if not applicable to this script -->
| GAP-020 | PPC-001 | TopicStep list not documented | High | `OPEN` | |
| GAP-021 | PPC-002 | Missing skip flags for some steps | Medium | `OPEN` | |
| GAP-022 | PPC-003 | Per-step output dirs not configurable | Medium | `OPEN` | |
| GAP-023 | PPC-004 | Per-step keep budgets not configurable | Low | `OPEN` | |
| GAP-024 | PPC-005 | Failure propagation policy undocumented | Medium | `OPEN` | |
| GAP-025 | PPC-006 | Step dependencies not verified | Medium | `OPEN` | |
| GAP-026 | PPC-007 | Not using build_topic_pipeline() | High | `OPEN` | |
| GAP-027 | PPC-008 | No --timestamp flag support | Low | `OPEN` | |
<!-- END EXAMPLE ROWS -->

### 5.2 MAP: Alteration Locations

| Location | Change | Standard |
|----------|--------|----------|
| `<path>:<start>-<end>` | <description> | <HOP/Universal/PPC requirement> |

### 5.3 Verification Log

| Date | Inspector | Findings | Status |
|------|-----------|----------|--------|
| <YYYY-MM-DD> | <agent/human> | <summary of verification> | `PASS` / `FAIL` / `GAPS_FOUND` |

---

## 6. RECORD: Changes Made

<!-- METAPROMPT: PROMPT-67-EVIDENCE -->
<!-- CHECKPOINT_ID: CHECKPOINT-6 -->
<!-- STOP_CONDITION: All changes logged in 6.1 table with Gap IDs and Commit SHAs -->
<!-- PROCEED_SIGNAL: "CHECKPOINT-6: {N} changes recorded with commit references" -->
<!-- REENTRY_POINT: PROMPT-67-EVIDENCE -->

> **Purpose:** Document all modifications made to the orchestrator during this inspection.
> Each change should link to the gap it resolved (if applicable).

### 6.1 Change Log

| # | Category | Location | Description | Gap ID(s) Resolved | Commit SHA |
|---|----------|----------|-------------|-------------------|------------|
| 1 | <category> | `<path>:<line>` | <what was changed> | GAP-XXX | `<sha>` |
| 2 | <category> | `<path>:<line>` | <what was changed> | GAP-XXX | `<sha>` |

<!-- EXAMPLE ROW — Delete after adding real changes:
| 1 | Pipeline | `script.py:150-200` | Added skip flags for all 8 steps | GAP-021 | `abc123d` |
-->

**Change Categories:**

- `Entry Point` — run()/main() modifications
- `CLI Flags` — argparse additions/changes (including skip flags)
- `Return Contract` — payload structure changes
- `Output Format` — manifest/summary/telemetry changes
- `Pipeline` — TopicStep list, execution order
- `Failure Handling` — stop_on_failure, continue_on_failure
- `Error Handling` — exception wrapping
- `DB Integration` — create_storage() markers
- `Documentation` — docstrings, comments
- `Testing` — test file additions/modifications
- `Other` — anything else

### 6.2 Verification Log

| Date | Inspector | Findings | Status |
|------|-----------|----------|--------|
| <YYYY-MM-DD> | <agent/human> | <summary of changes recorded> | `PASS` / `FAIL` / `GAPS_FOUND` |

---

## 7. CAPTURE: Evidence

<!-- METAPROMPT: PROMPT-67-EVIDENCE -->
<!-- CHECKPOINT_ID: CHECKPOINT-7 -->
<!-- STOP_CONDITION: Test results captured, code references linked, step verification complete, telemetry verified -->
<!-- PROCEED_SIGNAL: "CHECKPOINT-7: Evidence captured — {X} tests, {Y} code refs, STEPS_VERIFIED: {A}/{B}, TELEMETRY_VERIFIED: {YES/NO}" -->
<!-- REENTRY_POINT: PROMPT-67-EVIDENCE -->

### 7.1 RUN: Tests

| Test File | Test Name | Result | Commit SHA | CI Link |
|-----------|-----------|--------|------------|---------|
| `<test_file>` | `<test_name>` | `PENDING` | `<sha>` | `<CI_URL>` |

> **⚠️ TEST DEFERRAL POLICY:**
>
> Unit tests MAY be marked `DEFERRED` if ALL of the following are true:
>
> - [ ] mypy --strict passes (or documented exception)
> - [ ] CLI execution works (`--help` and actual run)
> - [ ] Section 7.3 (Step Execution Verification) is fully verified
> - [ ] Section 7.4 (Pipeline Telemetry Verification) is fully verified
> - [ ] Deferral rationale is documented in this table
>
> Tests MUST NOT be deferred if the orchestrator has known edge cases or untested failure modes.
>
> **If deferring, use this format:**
>
> | `N/A` | `N/A` | `DEFERRED` | N/A | Rationale: Execution evidence in 7.3/7.4 is comprehensive |

### 7.2 LINK: Code References

- `<path>:<start>-<end>` — <description>

### 7.3 VERIFY: Step Execution — MANDATORY FOR ORCHESTRATORS

<!-- ORCHESTRATOR_SPECIFIC: TRUE -->
<!-- STOP_CONDITION: All steps verified -->

> ⚠️ **ORCHESTRATOR REQUIREMENT:** Each step's execution MUST be verified.

#### 7.3.1 Full Pipeline Run

| Check | Command | Result | Evidence |
|-------|---------|--------|----------|
| Full pipeline execution | `python <script> --repo-root . --log-level DEBUG` | `PENDING` | Exit code, bundle path |
| All steps executed | Check log output | `PENDING` | `<N>/<N> steps completed` |
| Bundle created | `Test-Path <bundle_path>` | `PENDING` | Path exists |

#### 7.3.2 Per-Step Verification

| # | Step Name | Executed? | Duration | Output Created? | Status |
|---|-----------|-----------|----------|-----------------|--------|
| 1 | `<step_name>` | YES/NO | `<X.XX>s` | YES/NO | `PENDING` |
| 2 | `<step_name>` | YES/NO | `<X.XX>s` | YES/NO | `PENDING` |
<!-- Add row for each step from Section 0.2 -->

**Generate step list from log:**

```bash
python <script> --log-level DEBUG 2>&1 | grep -E "Step|step|SUCCESS|FAILED|SKIPPED"
```

#### 7.3.3 Skip Flag Verification

| Test | Command | Expected | Actual | Status |
|------|---------|----------|--------|--------|
| Skip step 1 | `python <script> --skip-<step1>` | Step 1 skipped, others run | `<actual>` | `PENDING` |
| Skip last step | `python <script> --skip-<lastN>` | Steps 1-(N-1) run, last skipped | `<actual>` | `PENDING` |

### 7.4 VERIFY: Pipeline Telemetry — MANDATORY FOR ORCHESTRATORS

<!-- ORCHESTRATOR_SPECIFIC: TRUE -->

> ⚠️ **ORCHESTRATOR REQUIREMENT:** Pipeline telemetry MUST be verified.

| Check | Status | Evidence |
|-------|--------|----------|
| telemetry.json contains step timing | `PENDING` | `jq '.steps' <telemetry.json>` |
| telemetry.json contains step statuses | `PENDING` | Each step has success/failure |
| telemetry.json contains artifact paths | `PENDING` | References to step bundles |
| manifest.json contains pipeline metadata | `PENDING` | Step count, duration, status |
| summary.md contains Pipeline Status table | `PENDING` | Visual status per step |

**Telemetry structure verification:**

```bash
python -m json.tool <bundle_path>/telemetry.json | head -50
```

### 7.5 Verification Log

| Date | Inspector | Findings | Status |
|------|-----------|----------|--------|
| <YYYY-MM-DD> | <agent/human> | <summary of verification> | `PASS` / `FAIL` / `GAPS_FOUND` |

---

## 8. CONFIGURE: Pipeline Configuration

<!-- METAPROMPT: PROMPT-8-ORCHESTRATOR -->
<!-- CHECKPOINT_ID: CHECKPOINT-8 -->
<!-- STOP_CONDITION: All pipeline configuration documented, execution readiness verified -->
<!-- PROCEED_SIGNAL: "CHECKPOINT-8: Pipeline configuration documented — {N} steps, {M} skip flags, failure_policy: {STOP/CONTINUE}" -->
<!-- REENTRY_POINT: PROMPT-8-ORCHESTRATOR -->

> **⚠️ ORCHESTRATOR-SPECIFIC SECTION**
>
> This section documents the pipeline configuration for THIS orchestrator.
> Unlike other script classes that document ScriptConfig for use BY orchestrators,
> orchestrators document their own pipeline coordination settings.

### 8.1 TopicStep Summary

| # | Step Name | Script | Purpose |
|---|-----------|--------|---------|
| 1 | `<step_name>` | `<script.py>` | `<brief purpose>` |
| 2 | `<step_name>` | `<script.py>` | `<brief purpose>` |
<!-- Add row for each step -->

### 8.2 Skip Flag Defaults

| Flag | Default | Rationale |
|------|---------|-----------|
| `--skip-<step1>` | `false` | `<why default is false/true>` |
| `--skip-<step2>` | `false` | `<why default is false/true>` |
<!-- Add row for each skip flag -->

### 8.3 Keep Budget Defaults

| Flag | Default | Rationale |
|------|---------|-----------|
| `--<step1>-artifacts-to-keep` | `<N>` | `<why this default>` |
| `--<step2>-artifacts-to-keep` | `<N>` | `<why this default>` |
| `--artifacts-to-keep` (global) | `<N>` | `<applies to orchestrator bundle>` |
<!-- Add row for each keep flag -->

### 8.4 Failure Propagation Summary

| Setting | Value | Effect |
|---------|-------|--------|
| Default behavior | `STOP_ON_FAILURE` / `CONTINUE` | Pipeline halts/continues on step failure |
| Configurable per-step? | `YES` / `NO` | Can individual steps override? |
| Recovery supported? | `YES` / `NO` | Can pipeline resume from failure? |

### 8.5 Pipeline Execution Readiness

| Check | Status | Evidence |
|-------|--------|----------|
| All step scripts exist | `PENDING` | `Test-Path` for each script |
| All step scripts have `run(argv)` | `PENDING` | Each script is UIC-compliant |
| All step scripts produce output | `PENDING` | Verified in Section 7.3 |
| Pipeline completes end-to-end | `PENDING` | Full run test passed |
| Failure handling works correctly | `PENDING` | Tested with induced failure |

### 8.6 Verification Log

| Date | Inspector | Findings | Status |
|------|-----------|----------|--------|
| <YYYY-MM-DD> | <agent/human> | <summary of verification> | `PASS` / `FAIL` / `GAPS_FOUND` |

---

## 9. ATTEST: Compliance Sign-Off

<!-- METAPROMPT: PROMPT-910-CLOSE -->
<!-- CHECKPOINT_ID: CHECKPOINT-9 -->
<!-- STOP_CONDITION: All attestation checkboxes checked, Inspector row complete -->
<!-- PROCEED_SIGNAL: "CHECKPOINT-9: Attestation complete — signed by {ASSIGNEE} on {DATE}" -->
<!-- REENTRY_POINT: PROMPT-910-CLOSE -->

> **Purpose:** Formal attestation that this inspection was conducted properly.
> Required for audit trail and separation of duties.

### 9.1 Attestation Record

<!-- STOP_GATE: TRUE -->
<!-- PROCEED_WHEN: All attestation checkboxes checked and Inspector row completed -->

| Role | Name | Date | Signature/ID |
|------|------|------|--------------|
| Inspector | <ASSIGNEE> | <YYYY-MM-DD> | <agent_id or initials> |
| Reviewer | <name or N/A> | <YYYY-MM-DD> | <signature or N/A> |
| Approver | <name or N/A> | <YYYY-MM-DD> | <signature or N/A> |

**Role Definitions:**

- **Inspector:** Person or agent who performed the inspection and filled this document
- **Reviewer:** Second pair of eyes who verified evidence quality (optional for low-risk scripts)
- **Approver:** Authority who approved for production use (optional for internal tools)

### 9.2 Attestation Statement

> I attest that:
>
> - [ ] All sections of this document were completed honestly
> - [ ] All evidence references point to real, verifiable artifacts
> - [ ] All PASS statuses reflect actual verification, not assumption
> - [ ] All gaps identified were either CLOSED+VERIFIED or documented as deferred
> - [ ] The orchestrator was actually executed and outputs verified against ground truth
> - [ ] All TopicSteps were verified (Section 7.3)
> - [ ] Pipeline telemetry was verified (Section 7.4)
> - [ ] Skip flags were tested (Section 7.3.3)

**Inspector attestation date:** `<YYYY-MM-DD>`

---

## 10. FINALIZE: Completion

<!-- METAPROMPT: PROMPT-910-CLOSE -->
<!-- CHECKPOINT_ID: CHECKPOINT-10 -->
<!-- STOP_CONDITION: All 10.1 checkboxes checked, no <PLACEHOLDER> remains, frontmatter updated -->
<!-- PROCEED_SIGNAL: "CHECKPOINT-10: PHASE 4 COMPLETE — {RECORD_ID} ready for production" -->
<!-- REENTRY_POINT: PROMPT-910-CLOSE (final gate — restart close sequence) -->

> **⚠️ This section is the FINAL GATE. Do not mark complete until ALL items are checked.**
>
> The build.md is NOT done when you fill in the sections. It is done when:
>
> 1. The orchestrator has been RUN and outputs verified TRUE
> 2. The Tier-3 YAML exists and is validated
> 3. The roster checkboxes are all checked including DONE
> 4. This document's frontmatter shows `status: complete`

### 10.1 CHECK: Build Document Completion

<!-- STOP_GATE: TRUE -->
<!-- PROCEED_WHEN: All checkboxes checked -->

**Discovery & Analysis:**

- [ ] Section 0.2 (Orchestrated Steps) — All steps documented
- [ ] Section 1 (Script Identity) — All fields populated, Step Count included
- [ ] Section 2.1 (CLI Interface) — Flags documented from `--help` output
- [ ] Section 2.2 (Entry Points) — Signatures verified against code
- [ ] Section 2.4 (Compliance Assessment) — All checks have evidence
- [ ] Section 2.5 (TopicStep Registry) — All steps documented with code refs
- [ ] Section 2.6 (Skip Flag Matrix) — All skip flags documented
- [ ] Section 2.7 (Failure Propagation Policy) — Policy documented

**Implementation & Testing:**

- [ ] Section 5 (Gap Analysis) — Gaps identified with priority/effort (including PPC gaps)
- [ ] Section 6 (Changes Made) — All modifications documented with line numbers
- [ ] Section 7 (Evidence) — Test results captured (pytest/mypy/coverage)
- [ ] Section 7.3 (Step Execution) — All steps verified
- [ ] Section 7.4 (Pipeline Telemetry) — Telemetry verified

**Truth Verification (CRITICAL):**

- [ ] Section 2.8.1 — QA tests passed (mypy, pytest, CLI execution)
- [ ] Section 2.8.5 — Output truth verified: **ORCHESTRATOR WAS ACTUALLY RUN**
- [ ] Section 2.8.5 — Every claim in output artifacts verified against ground truth
- [ ] **If any claim was FALSE, it was FIXED before checking this box**

**Tier-3 & DB Integration:**

- [ ] Section 3 — Tier-3 YAML created/updated and validated
- [ ] Section 4 — DB Integration markers present at all write points

**Pipeline Configuration:**

- [ ] Section 8.1 — TopicStep Summary complete
- [ ] Section 8.2 — Skip Flag Defaults documented
- [ ] Section 8.3 — Keep Budget Defaults documented
- [ ] Section 8.4 — Failure Propagation Summary complete
- [ ] Section 8.5 — Pipeline Execution Readiness all checks pass

### 10.2 UPDATE: Tier-2 Roster

> **After completing Section 10.1, update the parent Tier-2 roster document.**

**Roster location:** `../tier2_<stage>_roster.md`

**Workstream checkboxes to update:**

```markdown
#### Implementation Workstreams (checkbox-driven) — <SCRIPT_NAME>

- [x] A. Discovery — confirm CLI surfaces, outputs, retention, and consumers
- [x] B. Plan — draft gap closure plan
- [x] C. Implement — code changes applied (or N/A if already compliant)
- [x] D. Evidence — tests passing (N/N)
- [x] E. Bug fix — issues addressed (or N/A if none found)
- [x] F. Output truth verification — orchestrator run, output claims verified TRUE
- [x] G. Tier-3 YAML — created/updated <tier3_name>.yaml
- [x] H. Pipeline configuration — Section 8 complete
- [x] I. Step execution verification — Section 7.3 all steps verified
- [x] J. Pipeline telemetry verification — Section 7.4 verified
- [x] DONE — Phase 4 compliance complete (<YYYY-MM-DD>)
```

**Roster update checklist:**

- [ ] Located script record in Tier-2 roster
- [ ] Checked workstream boxes A through J
- [ ] Added DONE marker with date
- [ ] Updated `phase4_build_doc` field to point to this document
- [ ] Updated `tier3_yaml` field to point to Tier-3 YAML path
- [ ] Tier-2 roster file SAVED

### 10.3 UPDATE: Tier-1 Pipeline Registry — MANDATORY

> **⚠️ VERIFICATION REQUIRED** — Even if the entry appears correct, you MUST verify and provide evidence.
> Follow PROMPT_PHASE4_FINALIZE v1.4.0 Step 5 protocol.

**Registry location:** `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier1_healthview_orchestration_pipeline.md`

#### 10.3.1 Verification Checklist

- [ ] Opened Tier-1 pipeline document
- [ ] Located script entry in Stage registry table
- [ ] Verified: Script name matches `<SCRIPT_NAME>`
- [ ] Verified: Category matches `Orchestrator`
- [ ] Verified: Tier-3 YAML column is not `TBD`

#### 10.3.2 Verification Table

| Field | Expected | Actual | Status |
|-------|----------|--------|--------|
| Script name | `<SCRIPT_NAME>` | `<actual>` | `VERIFIED` / `MISMATCH` |
| Category | Orchestrator | `<actual>` | `VERIFIED` / `MISMATCH` |
| Tier-3 YAML link | `[tier3_<script>.yaml](...)` | `<actual>` | `VERIFIED` / `TBD` |

#### 10.3.3 Update Evidence

**Scenario A — Changes were made:**

```diff
- | `old_value` | ... |
+ | `new_value` | ... |
```

**Scenario B — No changes needed:**

> Tier-1 entry verified correct on <YYYY-MM-DD>. No changes required.
> Evidence: `git diff <tier1_path>` returned empty.

### 10.4 CLOSE: Document Finalization

**Update this document's frontmatter:**

```yaml
status: complete        # Changed from: active
version: "1.0.0"        # Changed from: working version
updated_at: <YYYY-MM-DD>
```

**Final verification:**

- [ ] Frontmatter `status` changed to `complete`
- [ ] Frontmatter `version` changed to `1.0.0`
- [ ] Frontmatter `updated_at` reflects completion date
- [ ] No `<PLACEHOLDER>` variables remain in document

### 10.5 CONFIRM: Phase 4 Complete

**Completion timestamp:** `<YYYY-MM-DD HH:MM UTC>`

**Summary:**

| Aspect | Status | Evidence |
|--------|--------|----------|
| Universal compliance | ✅ | Section 2.2.1 all checked |
| HOP bundle compliance | ✅ | Section 2.4.2 all checked |
| Output truth verified | ✅ | Section 2.8.5 — all claims TRUE |
| Tier-3 YAML | ✅ | `<tier3_yaml_path>` |
| DB Integration ready | ✅ | `<path>:<line>`, `<path>:<line>`, `<path>:<line>` |
| Pipeline configuration | ✅ | Section 8 complete |
| Step execution verified | ✅ | Section 7.3 — {N}/{N} steps |
| Telemetry verified | ✅ | Section 7.4 all checks pass |
| Tier-2 roster updated | ✅ | Workstreams A-J + DONE checked, file SAVED |
| Tier-1 registry updated | ✅ | Script entry added/updated, file SAVED |

**Propagation confirmation:**

- Tier-2 roster: `<roster_path>` — SAVED
- Tier-1 registry: `<tier1_path>` — SAVED

**Next step:** If this orchestrator is now ready, it can coordinate its pipeline.
No Phase 4B promotion is needed — orchestrators are self-managing.

---

## 11. MAINTAIN: Doc Hygiene

> **Purpose:** After each inspection cycle, clean the document to reflect CURRENT state only.
> Historical context lives in Verification Logs, not in section content.

### 11.1 CHECK: Hygiene Checklist

- [ ] All PENDING statuses resolved (changed to PASS/FAIL/SKIP)
- [ ] All `<placeholder>` values replaced with actual data
- [ ] All gaps either CLOSED+VERIFIED or documented as deferred
- [ ] Stale language removed (no "was", "used to", "previously")
- [ ] Evidence reflects most recent verification
- [ ] Verification Logs updated with inspection date

### 11.2 APPLY: Language Standards

**Use current tense:**

- ✅ "Orchestrator executes 8 steps in sequence"
- ❌ "Orchestrator was updated to execute 8 steps"

**Use facts, not narrative:**

- ✅ "Pipeline definition: `run()` at line 1954"
- ❌ "We added the pipeline definition during Phase 4"

### 11.3 IDENTIFY: Re-Inspection Triggers

This document should be re-inspected when:

- [ ] Requirements Registry changes (new UIC/HOP/AGT/DBI/ORC/PPC requirements)
- [ ] Orchestrator code is modified
- [ ] Steps are added or removed from the pipeline
- [ ] Upstream step scripts change
- [ ] Failure propagation policy changes
- [ ] Quarterly audit cycle

---

## 12. REFERENCE: Template Variables

> **Placeholder Conventions:**
>
> - `<UPPER_SNAKE>`: User-fillable text values (e.g., `<SCRIPT_NAME>`, `<RECORD_ID>`)
> - `<lower_snake>`: Structural references (e.g., `<path>`, `<line>`, `<tier3_path>`)
> - ISO timestamps: `<YYYY-MM-DD>`, `<YYYYMMDD-HHMM>` (kept as-is for standard compliance)

Replace these placeholders when using this template:

| Variable | Description |
|----------|-------------|
| `<SCRIPT_NAME>` | Script filename (e.g., `run_docs_health_overview.py`) |
| `<SCRIPT_PATH>` | Full path (e.g., `.repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py`) |
| `<SCRIPT_DIR>` | Script directory (e.g., `.repo_studios/command_center/scripts/orchestrators`) |
| `<RECORD_ID>` | Record ID (e.g., `S21R-001`) |
| `<YYYY-MM-DD>` | ISO date |
| `<LINE_COUNT>` | Script line count |
| `<TARGET_STAGE>` | Destination stage (e.g., `Stage 21`) |
| `<TOPIC>` | Topic slug (e.g., `docs_health_overview`) |
| `<ASSIGNEE>` | Person or agent performing the inspection |
| `<registry_version>` | Version of Requirements Registry in effect |
| `<valid_until>` | Date when this inspection expires (typically +90 days) |
| `<path>:<line>` | Line reference format (e.g., `.repo_studios/scripts/orchestrators/script.py:123`) |
| `<path>:<start>-<end>` | Line range format (e.g., `.repo_studios/scripts/orchestrators/script.py:45-67`) |
| `<CI_URL>` | CI job URL (e.g., `https://github.com/org/repo/actions/runs/12345`) |
| `<sha>` | Git commit SHA (short form, e.g., `abc123d`) |
| `<artifact_path>` | Path to archived artifact with optional hash |
| `<agent_id>` | Agent identifier (e.g., `copilot-v4`, `claude-3.5`) |
| `<STEP_COUNT>` | Number of TopicSteps in pipeline |
| `<STEP_NAME_N>` | Nth step name (e.g., `doc-index`) |
| `<STEP_SCRIPT_N>` | Nth step script path |
| `<SKIP_FLAG_N>` | Nth skip flag (e.g., `--skip-doc-index`) |
| `<KEEP_FLAG_N>` | Nth keep flag (e.g., `--doc-index-artifacts-to-keep`) |
| `<FAILURE_POLICY>` | STOP_ON_FAILURE or CONTINUE |

---

## 13. LOG: Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.1.0 | 2026-02-03 | S21R-001 live test findings: (1) Added UIC-002 deviation note for orchestrators returning `int` in Section 2.4.1, (2) Reworded PPC-007 to allow both inline closures and `build_topic_pipeline()` patterns, (3) Expanded Section 2.5.1 with two valid pipeline patterns, (4) Added PPC-009 for `write_report_artifacts()`, (5) Added Registry usage instruction after PPC table, (6) Fixed Section 2.3 output path to `producer_reports/` (not `orchestrator_reports/`), (7) Added test deferral policy to Section 7.1, (8) Added step discovery command to Section 7.3.2, (9) Aligned Section 10.3 with PROMPT_PHASE4_FINALIZE v1.4.0 Step 5 protocol |
| 1.0.0 | 2026-02-03 | Initial Orchestrator template derived from Producer v3.5.0; added PPC requirements (PPC-001 through PPC-008), Section 0.2 ORCHESTRATED_STEPS table, Section 2.5 TopicStep Registry, Section 2.6 Skip Flag Matrix, Section 2.7 Failure Propagation Policy, modified Section 2.8 for pipeline status checks, Section 5.1.4 PPC Gaps, Section 7.3 Step Execution Verification, Section 7.4 Pipeline Telemetry Verification, **completely replaced Section 8** with Pipeline Configuration (removed ScriptConfig documentation), added workstreams I/J for orchestrator-specific verification |
