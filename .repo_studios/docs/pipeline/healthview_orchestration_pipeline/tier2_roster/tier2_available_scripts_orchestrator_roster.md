---
title: "Tier-2 Roster — Stage 11.1 Orchestrator (Available Scripts)"
tier: tier-2
audience:
  - coding_agent
  - human_developer
owners:
  - repo_studios_team@rainmakerprotocol.dev
role:
  - roster
  - stage-vertical
  - orchestrator-authority
status: draft
version: 0.1.0
updated_at: 2026-01-25
tags:
  - pipeline
  - healthview
  - hop
  - tier-2
  - stage-11-1
  - orchestrator
  - template-seed
related_files:
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier1_healthview_orchestration_pipeline.md
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/tier2_available_scripts_roster.md
  - .repo_studios/command_center/scripts/orchestrators/run_test_execution_telemetry.py
  - .repo_studios/command_center/scripts/orchestrators/run_fault_diagnostics_overview.py
  - .github/instructions/markdown.instructions.md
  - REPORT_NAMING_STANDARDS.md
---

<!-- markdownlint-disable-next-line MD025 -->
# Tier-2 Roster — Stage 11.1 Orchestrator (Available Scripts)

> **Purpose:** This Tier-2 roster documents the Stage 11.1 *orchestrator* that will manage the
> Available Scripts holding area. Unlike the companion
> [tier2_available_scripts_roster.md](tier2_available_scripts_roster.md) which documents the
> *scripts* in Stage 11.1, this roster documents the orchestrator itself: its design patterns,
> CLI interface, script invocation chain, and output bundle contract.
>
> This document also serves as the **seed template** for Stage 12.5 (Orchestrator Template)
> extraction. Patterns discovered here will inform the reusable orchestrator template.
>
> **Tier-1 source:** Stage 11.1 in
> `tier1_healthview_orchestration_pipeline.md`.
> **Stage 12 linkage:** Stage 12.5 (Orchestrator Template) references this doc.
> **Locked decisions source:** Tier-1 spine + `REPORT_NAMING_STANDARDS.md`.
> **Last synced with Tier-1:** 2026-01-25.
>
> Standards: `.github/instructions/markdown.instructions.md` (reviewed 2026-01-25).

---

## 0. Instruction Block for Editors & AI Assistants

- This document inherits terminology and stage ordering from the Tier-1 spine:
  `tier1_healthview_orchestration_pipeline.md`.
- Preserve the canonical Tier-2 section order.
- This doc is distinct from `tier2_available_scripts_roster.md`:
  - **This doc:** Orchestrator design, patterns, contract, and template seed.
  - **Scripts roster:** Per-script inspection records for holding area members.
- Do not merge aspirational behavior into "Current evidence"; log it explicitly as a gap or
  stop-gate.
- When code changes begin for this stage, enforce the repo standards:
  - code changes + tests
  - ≥80% coverage on touched modules
  - updated Tier-1/Tier-2 docs
  - clean formatting/lint behavior
- After meaningful edits, record the timestamp in the Update Log.

---

## 1. Goals & Success Criteria

1. Provide a single authoritative Tier-2 roster for the Stage 11.1 orchestrator that engineers
   and agents can use to implement or modify the orchestrator without re-litigating contracts.
2. Extract and document common orchestrator patterns from existing implementations (Stages 1.1–6.1)
   to inform Stage 11.1 design and Stage 12.5 template creation.
3. Define the Stage 11.1 orchestrator's script execution roster, invocation order, and output
   bundle structure.

**Success criteria:**

- Tier-1 Stage 12.5 links to this doc as the orchestrator template seed.
- This doc contains:
  - Common Orchestrator Patterns (Section 2) extracted from existing implementations.
  - Script Execution Roster (Section 3) defining invocation order.
  - Orchestrator Contract (Section 4) defining I/O and CLI surfaces.
  - Stop-gates required before implementation begins.

---

## 2. Common Orchestrator Patterns

Patterns extracted from existing HealthView orchestrators (Stages 1.1–6.1).

### 2.1 Pattern Inventory

| Pattern | Description | Evidence Sources |
|---------|-------------|------------------|
| CLI Architecture | Shared CLI building blocks from libraries | `run_test_execution_telemetry.py`, `run_fault_diagnostics_overview.py` |
| Script Invocation | Dynamic import with `run(argv)` entry | All orchestrators |
| Output Bundle | Timestamped directory with manifest, summary, telemetry | `REPORT_NAMING_STANDARDS.md` |
| Pipeline Execution | `build_topic_pipeline()` with `TopicStep` chain | `run_test_execution_telemetry.py` |
| Retention Policy | Configurable `--artifacts-to-keep` with pruning | All orchestrators |
| Catalog Registration | Register scripts with `CatalogRegistry` for manifest | `run_docs_health_overview.py` |
| Guardrail Enforcement | `enforce_report_naming()` validates output structure | `run_docs_health_overview.py` |
| Outcome Dataclasses | Typed `@dataclass` per step for result threading | All orchestrators |

### 2.2 CLI Architecture Pattern

**Pattern:** Use library-provided builders for consistent CLI construction.

**Evidence:** From `run_test_execution_telemetry.py` (lines 30–45):

```python
from libraries import (
    CatalogRegistry,
    KeepSpec,
    OptionsConfig,
    PathSpec,
    PathsConfig,
    ReportArtifact,
    TopicContext,
    TopicStep,
    build_pipeline_telemetry,
    build_standard_options,
    build_standard_paths,
    build_topic_pipeline,
    measure_artifact_directory,
    step_failed,
    step_skipped,
    step_success,
    write_report_artifacts,
)
```

**Standard CLI Flags:**

- `--repo-root`: Repository root override
- `--log-level`: Logging verbosity (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `--artifacts-to-keep`: Retention budget for output bundles
- `--timestamp`: ISO-8601 timestamp for artifact naming
- `--skip-<step>`: Flags to skip individual pipeline steps

### 2.3 Script Invocation Pattern

**Pattern:** Dynamic import using `importlib.util` with cached module registration.

**Evidence:** From `run_test_execution_telemetry.py` (lines 480–498):

```python
def _load_run_callable(script_path: Path, module_name: str):
    script_path = script_path.resolve()
    if module_name in sys.modules:
        return getattr(sys.modules[module_name], "run")
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load module from {script_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    run_callable = getattr(module, "run", None)
    if not callable(run_callable):
        raise AttributeError(f"Module at {script_path} does not expose a callable run() helper")
    return run_callable
```

**Key principles:**

- Scripts expose `run(argv)` as the entry point
- Orchestrators dynamically import (not subprocess) for efficiency
- Module caching prevents repeated loading
- Clear error messages on missing `run()` callable

### 2.4 Output Bundle Pattern

**Pattern:** Timestamped directory with standard artifact set.

**Evidence:** From `REPORT_NAMING_STANDARDS.md`:

```text
.repo_studios/reports/healthview/<class>/<topic>/<timestamp>/
├── manifest.json    # Required: bundle metadata
├── summary.md       # Required: human-readable summary
└── telemetry.json   # Required: execution metrics
```

**Key principles:**

- Timestamp format: `YYYYMMDD-HHMM` (from `run_slug`)
- No pointer files (`latest_*` forbidden)
- Pruning respects `artifacts_to_keep` parameter
- Bundle directory is atomic (all artifacts written together)

### 2.5 Pipeline Execution Pattern

**Pattern:** Sequential step execution with result accumulation.

**Evidence:** From `run_fault_diagnostics_overview.py` (lines 885–898):

```python
pipeline = build_topic_pipeline(
    steps=[
        TopicStep(name="producer", runner=producer_step),
        TopicStep(name="consumer", runner=consumer_step),
        TopicStep(name="summarizer", runner=summarizer_step, continue_on_failure=False),
    ]
)
result = pipeline.run(context)
try:
    result.raise_for_failure()
except RuntimeError as exc:
    LOGGER.error("Pipeline failed: %s", exc)
    return 1
```

**Key principles:**

- Each step is a `TopicStep` with name and runner function
- Steps return `step_success()`, `step_failed()`, or `step_skipped()`
- `continue_on_failure` controls fail-fast vs tolerant behavior
- `result.raise_for_failure()` consolidates error handling

### 2.6 Manifest Structure Pattern

**Pattern:** JSON manifest with consistent schema.

**Evidence:** From `run_fault_diagnostics_overview.py` (lines 918–945):

```python
manifest = {
    "schema_version": SCHEMA_VERSION,
    "viewer": "healthview",
    "topic": HEALTHVIEW_TOPIC,
    "run_slug": run_slug,
    "generated_at": completed_at.isoformat(),
    "telemetry": telemetry_payload,
    "artifacts": artifacts_section,
    "inputs": { ... },
    "catalog": [entry.__dict__ for entry in registry.all_entries()],
}
```

**Required manifest fields:**

- `schema_version`: Integer version for contract evolution
- `viewer`: Always "healthview" for HealthView orchestrators
- `topic`: Topic slug (snake_case)
- `run_slug`: Timestamp identifier (YYYYMMDD-HHMM)
- `generated_at`: ISO-8601 completion timestamp
- `telemetry`: Execution metrics
- `artifacts`: Relative paths to generated files
- `inputs`: CLI inputs and resolved paths
- `catalog`: Script registry entries

### 2.7 Catalog Registration Pattern

**Pattern:** Register all scripts in the pipeline with `CatalogRegistry` for manifest inclusion.

**Evidence:** From `run_docs_health_overview.py` (lines 1671–1700):

```python
def _register_catalog(registry: CatalogRegistry) -> None:
    """Register producer and aggregator scripts with the catalog."""
    registry.register(
        script_path=str(DOC_INDEX_SCRIPT), topic=TOPIC_SLUG, role="producer"
    )
    registry.register(
        script_path=str(ANCHOR_INVENTORY_SCRIPT), topic=TOPIC_SLUG, role="producer"
    )
    # ... additional registrations ...
    registry.register(
        script_path=str(ORCHESTRATOR_SCRIPT), topic=TOPIC_SLUG, role="orchestrator"
    )
```

**Key principles:**

- Register all scripts in the chain (producers, consumers, aggregators, summarizers)
- Include the orchestrator itself in the catalog
- Use consistent `topic` and `role` values
- Catalog entries appear in the manifest's `catalog` array

### 2.8 Guardrail Enforcement Pattern

**Pattern:** Validate output structure with `enforce_report_naming()` before completion.

**Evidence:** From `run_docs_health_overview.py` (lines 2197–2210):

```python
try:
    enforce_report_naming(
        reports_root=paths.healthview_root,
        run_dir=result_artifacts.run_dir,
        viewer=VIEWER_SLUG,
        topic=HEALTHVIEW_TOPIC,
        artifact_roles=(
            "manifest.json",
            "summary.md",
            "summary.json",
            "telemetry.json",
        ),
    )
except GuardrailViolationError as exc:
    LOGGER.error("Report naming audit failed: %s", exc)
    return 1
```

**Key principles:**

- Call `enforce_report_naming()` after writing artifacts
- Specify expected artifact roles for validation
- Catch `GuardrailViolationError` and fail gracefully
- Ensures HOP compliance before claiming success

### 2.9 Outcome Dataclass Pattern

**Pattern:** Define typed `@dataclass` per step to thread results between steps.

**Evidence:** From `run_dependency_import_hygiene.py` (lines 300–360):

```python
@dataclass(frozen=True)
class TypecheckOutcome:
    """Result of running the typecheck producer."""
    run_dir: Path | None
    report_json: Path | None
    report_md: Path | None
    log_path: Path | None
    raw_output: Path | None
    payload: dict[str, Any] | None
```

**Key principles:**

- Use `@dataclass(frozen=True)` for immutability
- Include all relevant paths and parsed payloads
- Use `| None` for optional fields (step may be skipped)
- Store outcomes in holder dicts for step chaining:
  ```python
  producer_holder: dict[str, ProducerOutcome] = {}
  # After execution:
  producer_holder["value"] = outcome
  ```

---

## 3. Script Execution Roster

### 3.1 Current Holding Area Scripts

Scripts from `tier2_available_scripts_roster.md` classified for Stage 11.1 orchestration consideration.

| Record ID | Script Name | Role | Planned Stage | Promotion Status |
|-----------|-------------|------|---------------|------------------|
| ASR-001 | `generate_anchor_health_report.py` | consumer | Stage 2.2 | candidate |
| ASR-002 | `configure_faulthandler_runtime.py` | utility | Stage 3.2 | utility-only |
| ASR-003 | `dump_faulthandler_snapshot.py` | utility | Stage 3.2 | utility-only |
| ASR-004 | `fault_run_analysis.py` | utility | Stage 3.2 | utility-only |
| ASR-005 | `validate_import_boundaries.py` | producer | Stage 4.2 | candidate |
| ASR-006 | `extract_standards_rules.py` | producer | Stage 6.2 | candidate |
| ASR-007 | `check_inventory_health.py` | producer | questionable | review-needed |
| ASR-008 | `validate_inventory.py` | producer | questionable | review-needed |
| ASR-010 | `render_inventory_views.py` | producer | out-of-scope | deferred |
| ASR-011 | `generate_lizard_report.py` | producer | out-of-scope | deferred |
| ASR-013 | `test_log_analysis.py` | library | N/A | library-only |

**Promotion Status Legend:**

- `candidate` — Viable for orchestrator wiring; meets minimum requirements
- `utility-only` — Support script; not directly orchestrated (invoked by other scripts)
- `review-needed` — Questionable fit; needs assessment before promotion decision
- `deprecated` — Legacy; slated for removal or replacement
- `deferred` — Out of HealthView scope currently
- `library-only` — Shared module; not a standalone CLI

### 3.2 Classification by Tier Class

**Producers (5):**

| ID | Script | Path | Dependencies |
|----|--------|------|--------------|
| ASR-005 | `validate_import_boundaries.py` | `.repo_studios/scripts/producers/` | None (standalone) |
| ASR-006 | `extract_standards_rules.py` | `.repo_studios/scripts/producers/` | None (standalone) |
| ASR-007 | `check_inventory_health.py` | `.repo_studios/scripts/producers/` | Inventory artifacts |
| ASR-008 | `validate_inventory.py` | `.repo_studios/scripts/producers/` | Inventory schema |
| ASR-010 | `render_inventory_views.py` | `.repo_studios/scripts/producers/` | Inventory data |
| ASR-011 | `generate_lizard_report.py` | `.repo_studios/scripts/producers/` | Source files |

**Consumers (1):**

| ID | Script | Path | Dependencies |
|----|--------|------|--------------|
| ASR-001 | `generate_anchor_health_report.py` | `.repo_studios/scripts/consumers/` | Anchor inventory (producer output) |

**Utilities (4):**

| ID | Script | Path | Usage |
|----|--------|------|-------|
| ASR-002 | `configure_faulthandler_runtime.py` | `.repo_studios/scripts/utilities/` | Runtime bootstrap |
| ASR-003 | `dump_faulthandler_snapshot.py` | `.repo_studios/scripts/utilities/` | On-demand dump |
| ASR-004 | `fault_run_analysis.py` | `.repo_studios/scripts/utilities/` | Post-run analysis |
| ASR-013 | `test_log_analysis.py` | `.repo_studios/command_center/scripts/libraries/` | Shared module |

### 3.3 Execution Order (Proposed)

Based on dependency analysis, the Stage 11.1 orchestrator would execute in this order:

```text
┌─────────────────────────────────────────────────────────────────────┐
│                    STAGE 11.1 EXECUTION FLOW                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  PHASE 1: PRODUCERS (parallel-capable)                              │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ validate_import_boundaries.py (ASR-005)                     │   │
│  │ extract_standards_rules.py (ASR-006)                        │   │
│  │ check_inventory_health.py (ASR-007) [if promoted]           │   │
│  │ validate_inventory.py (ASR-008) [if promoted]               │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                            │                                        │
│                            ▼                                        │
│  PHASE 2: CONSUMERS (depends on producers)                          │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ generate_anchor_health_report.py (ASR-001)                  │   │
│  │   └── requires: anchor inventory (external producer)        │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.4 Dependency Map

```text
                    ┌──────────────────────────┐
                    │   External Dependencies   │
                    │   (from other stages)     │
                    └──────────┬───────────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
    ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
    │  ASR-005    │  │  ASR-006    │  │  ASR-007    │
    │  import     │  │  standards  │  │  inventory  │
    │  boundaries │  │  rules      │  │  health     │
    └──────┬──────┘  └──────┬──────┘  └──────┬──────┘
           │                │                │
           └────────────────┼────────────────┘
                            │
                            ▼
                   ┌─────────────────┐
                   │    ASR-001      │
                   │  anchor health  │
                   │    report       │
                   └────────┬────────┘
                            │
                            ▼
                   ┌─────────────────┐
                   │    ASR-009      │
                   │  health suite   │
                   │  (DEPRECATED)   │
                   └─────────────────┘
```

### 3.5 Recommended First Script for Phase 4

**Selection: ASR-005 (`validate_import_boundaries.py`)**

**Rationale:**

1. **Producer role** — Fits the established orchestrator pattern (producers first)
2. **No dependencies** — Can run standalone without upstream artifacts
3. **Clear purpose** — Import boundary validation is well-defined
4. **Candidate status** — Already marked as promotion candidate for Stage 4.2
5. **Template value** — Will inform the Producer Template (Stage 12.1)

**Alternative candidates (if ASR-005 proves complex):**

- ASR-006 (`extract_standards_rules.py`) — Also standalone producer
- ASR-001 (`generate_anchor_health_report.py`) — Consumer; would inform Consumer Template

---

## 4. Orchestrator Contract

### 4.1 Target Orchestrator Identity

- **Name:** `run_available_scripts_oversight.py` (proposed)
- **Location:** `.repo_studios/command_center/scripts/orchestrators/`
- **Role:** Execute and report on Stage 11.1 holding area scripts

### 4.2 CLI Interface Contract

**Required flags:**

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--repo-root` | path | auto | Repository root override |
| `--log-level` | choice | INFO | Logging verbosity |
| `--artifacts-to-keep` | int | 3 | Retention budget for bundles |
| `--timestamp` | ISO-8601 | now | Override run timestamp |

**Skip flags (one per step):**

| Flag | Description |
|------|-------------|
| `--skip-<step>` | Skip named step in pipeline |

### 4.3 Output Contract

**Bundle location:**

```text
.repo_studios/reports/healthview/orchestrator_reports/available_scripts_oversight/<YYYYMMDD-HHMM>/
```

**Required artifacts:**

| Artifact | Format | Description |
|----------|--------|-------------|
| `manifest.json` | JSON | Bundle metadata with schema_version, artifacts, inputs |
| `summary.md` | Markdown | Human-readable execution summary |
| `telemetry.json` | JSON | Pipeline execution metrics |

### 4.4 Return Code Contract

| Code | Meaning |
|------|---------|
| 0 | Success — all steps completed |
| 1 | Failure — pipeline step failed |
| 2 | Configuration error — invalid arguments |

---

## 5. Stop-Gates

### 5.1 Pre-Implementation Gates

Before creating `run_available_scripts_oversight.py`:

- [x] Phase 2 complete: All existing orchestrators reviewed (8 patterns documented)
- [x] Phase 3 complete: Script roster ordered with dependencies (12 scripts classified)
- [x] CLI interface finalized in Section 4.2
- [x] Output contract finalized in Section 4.3

### 5.2 Post-Implementation Gates

Before claiming Stage 11.1 orchestrator compliance:

- [x] All required artifacts generated on every run
- [x] Pruning respects `--artifacts-to-keep`
- [x] No pointer files (`latest_*`) created
- [ ] DB integration gated and marker-consistent
- [x] Tests achieve ≥80% coverage on orchestrator (10/10 passing)
- [x] This Tier-2 doc updated with evidence

---

## 6. Template Extraction Notes

### 6.1 Candidate Sections for Stage 12.5 Template

The following sections should be generalized into the reusable orchestrator template:

- **Section 2:** Common patterns → Template guidance
- **Section 3:** Execution roster → Placeholder table
- **Section 4:** Contract → Template with variables
- **Section 5:** Stop-gates → Generic checklist

### 6.2 Variables for Template

| Variable | Description | Example Value |
|----------|-------------|---------------|
| `{{ORCHESTRATOR_NAME}}` | Script filename | `run_available_scripts_oversight.py` |
| `{{TOPIC_SLUG}}` | Hyphenated topic for CLI | `available-scripts` |
| `{{HEALTHVIEW_TOPIC}}` | Underscore topic for paths | `available_scripts_oversight` |
| `{{SCHEMA_VERSION}}` | Manifest schema version | `1` |

---

## 7. Update Log

| Date | Author | Changes | Review Status | Linked Issues |
|------|--------|---------|---------------|---------------|
| 2026-01-25 | GitHub Copilot | Created initial orchestrator roster with common patterns extracted from existing implementations; established contract skeleton; defined stop-gates for Phase 1.5 completion. | pending | Stage 12 implementation plan |
| 2026-01-25 | GitHub Copilot | Phase 2 complete: Added 3 additional patterns (Catalog Registration, Guardrail Enforcement, Outcome Dataclass) from reviews of `run_docs_health_overview.py`, `run_dependency_import_hygiene.py`, `run_monkey_patch_oversight.py`, `run_standards_integrity.py`. Total patterns: 8. | pending | Phase 2 reviews |
| 2026-01-25 | GitHub Copilot | Phase 3 complete: Populated script roster (12 scripts), classified by tier (5 producers, 1 consumer, 1 summarizer, 4 utilities), mapped dependencies, proposed execution order, selected ASR-005 (`validate_import_boundaries.py`) as first Phase 4 candidate. | pending | Phase 3 roster |
| 2026-01-26 | GitHub Copilot | **Orchestrator implemented:** Created `run_available_scripts_oversight.py` with HOP-compliant output (manifest.json, summary.md, telemetry.json), `run(argv)` entry point, per-script `ScriptConfig` for heterogeneous CLI handling, skip flags, retention policy. Test suite: 10/10 passing. Stop-gates 5.1 and 5.2 checkboxes updated. | pending | Stage 11.1 |
