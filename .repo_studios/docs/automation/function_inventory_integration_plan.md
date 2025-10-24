# Function Inventory Integration Plan

**Status:** Draft

This living checklist captures the sequential work required to integrate the Jarvis Function Inventory System into Repo Studios. We will refine and approve these steps before implementation.

## Step-by-step Plan

1. Review existing phased plan deliverables and confirm scope.
2. Inventory current scripts, automation docs, and tests related to inventory generation.
3. Decide target location and naming conventions for the production-grade scripts.
4. Define structured artifact output format, including module-level first-line, signature, and line-count metadata, plus retention policy for the primary index.
5. Capture companion analysis objectives, schema expectations, retention assumptions, and required machine-readable outputs.
6. Map out required command-line interface and configuration options shared by both producers.
7. Draft refactor plan for `generate_inventory.py` to meet Repo Studios standards.
8. Outline pytest coverage needs and fixtures spanning inventory and analysis behaviors.
9. Determine Makefile wiring and parameter passing strategy for dual-output execution.
10. Design GitHub Actions integration (job placement, cache impacts, artifact upload).
11. Specify documentation updates (automation docs, script inventory entries, README links).
12. Confirm `.gitignore` and `.gitattributes` adjustments for co-located index directories.
13. Establish rollout/communication plan to downstream consumers (Copilot, agents).
14. Schedule validation runs on representative modules and capture baseline outputs.
15. Finalize quality gates (lint, schema validation, size limits) for generated artifacts.
16. Define post-integration monitoring and maintenance ownership.

## Implementation Plan (Phased Checklist)

### Phase A – Alignment & Scoping

* [x] Reconfirm objectives with stakeholders using `inventory_system_phased_plan.yaml` and update scope notes if requirements shift. _(2025-10-24: Objectives affirmed—focus on co-located JSON indices for targeted folders to accelerate Copilot discovery.)_
* [x] Document the final decision on co-located artifact policy and communicate how it coexists with `.repo_studios/reports` conventions. _(Co-located `<folder>_index/` directories remain source of truth; no shadow copies under `.repo_studios/reports/` are required.)_
* [x] Capture JSON schema expectations (fields, types, `schema_version`) and circulate for review. _(2025-10-24: v1 schema refreshed to document signatures, line counts, and module-first-line metadata.)_
  * Schema (v1) overview:
    * `schema_version` (int)
    * `metadata`: `generated_at` (ISO string), `folder_path`, `folder_name`, `total_files`, `total_functions`, `total_classes`, `scan_depth`
    * `files[]`: `path`, `relative_path`, `line_count`, `module_first_line`, `functions[]`, `classes[]`, `imports[]`
    * `functions[]` / `methods[]`: `name`, `line`, `type`, `is_async`, `is_private`, `docstring`, `signature`, `line_count`
    * `classes[]`: `name`, `line`, `docstring`, `line_count`, `methods[]`
    * `statistics`: `total_lines_of_code`, `files_by_type`, `private_functions`, `public_functions`, `async_functions`
* [ ] Inventory current manual usages (`tools/generate_inventory.py`) to plan deprecation messaging and overlap timeline.
  * Observed entry point: `python3 tools/generate_inventory.py modules -v` (usage captured in PowerShell command history and developer workflow notes). Deprecation messaging must highlight Make target replacement and CI integration timeline.

### Phase B – Script Hardening

* [x] Port or alias `phase1/generate_inventory.py` into `.repo_studios/scripts/producers/` with a repo-root aware CLI. _(`generate_function_inventory.py` now lives under `.repo_studios/scripts/producers/` with target resolution relative to `--repo-root`.)_
* [x] Replace ad-hoc printing with structured logging consistent with other producers (INFO summaries, DEBUG diagnostics). _(Logging wired via `logging.basicConfig`; warnings captured and surfaced.)_
* [x] Add CLI flags for repo root resolution, optional verbose mode, and future-proofing (e.g., `--schema-version`). _(`--repo-root`, positional `target`, `--schema-version`, and `--log-level` implemented.)_
* [x] Introduce explicit exit codes (0 success, non-zero on fatal errors) and ensure error messages surface in CI logs. _(Script returns 1 for validation failures and logs details before exiting.)_

### Phase C – Artifact Structure & Schema

* [x] Embed `schema_version`, timestamps, and ownership metadata in the JSON output. _(Payload metadata now stamps version, generated timestamp, and folder identifiers.)_
* [x] Ensure overwriting behavior is atomic (write to temp file then replace) to prevent partial files. _(Temp file replace implemented in writer.)_
* [x] Capture enriched per-file context (`module_first_line`, function signatures, line counts) to support downstream analysis. _(2025-10-24: Inventory producer now persists these fields.)_
* [x] Add optional `latest.json` pointer or README stub inside `<folder_name>_index/` to guide consumers. _(Pointer now mirrors the freshest index payload for simple tooling access.)_
* [x] Draft initial JSON schema document (even if informal) to support future validation tooling. _(Schemas now live under `docs/schemas/function_inventory.schema.json` and `function_analysis.schema.json`, providing validation anchors.)_

### Phase D – Companion Analysis Script

* [x] Define analysis objectives with duplicate detection as the primary focus (hotspots optional, anomaly surfacing deferred) and capture required data from the structural index. _(Signature + docstring grouping now leveraged from enriched index data.)_
* [x] Specify companion artifact schema (`schema_version`, provenance metadata, `findings[]`, severities, recommended actions, machine-readable action items) and circulate for review. _(Schema captured 2025-10-24 with `findings[].instances[]` including signatures, line counts, docstrings.)_
* [x] Implement companion producer (e.g., `.repo_studios/scripts/producers/generate_function_analysis.py`) with CLI parity (`--repo-root`, positional `target`, `--schema-version`, `--log-level`).
* [x] Ensure the companion script ingests the freshly generated index and emits `<folder_name>_analysis-YYYY-MM-DD.json` using atomic writes. _(Analysis run replaces legacy files and writes dated artifacts atomically.)_
* [x] Record provenance in the analysis payload (generator version, timestamp, source index reference/hash) to support traceability. _(Metadata includes `analysis_version`, index path, generated timestamp, and SHA-256 digest.)_
* [x] Profile runtime on representative folders and document acceptable thresholds so dual-output execution stays within team expectations. _(2025-10-24: `.repo_studios/scripts/producers/` execution completes in under 2s, surfacing 52 duplicate groups/416 duplicates.)_
* [x] Draft initial interpretation guide outlining how consumers should read the analysis findings and what actions they unlock, highlighting machine-readable cues. _(`docs/automation/function_analysis_guide.md` captures interpretation guidance and action workflows.)_

### Phase E – Testing & Quality Gates

* [x] Build pytest coverage for AST parsing, error handling, and overwrite scenarios (tests under `.repo_studios/tests/tests_producers/`). _(Tests now verify module-first-line capture, signature/line-count extraction, and duplicate instance metadata.)_
* [ ] Add integration tests that generate indices for curated fixtures (empty dirs, nested trees, syntax-error files, large modules). _(Initial round-trip test added in `.repo_studios/tests/tests_producers/test_function_inventory_integration.py`; dependency note: `jsonschema` already pinned so payload validation can run once fixture matrix expands.)_
* [ ] Create golden snapshot and/or JSON schema validation tests to guard against regressions in structure and metadata.
* [ ] Provide cross-platform fixture paths (Windows/Posix) and ensure line endings are normalized in assertions.
* [ ] Add performance smoke test to ensure typical folders (hundreds of `.py` files) run within acceptable bounds.
* [ ] Configure lint and formatting checks (e.g., `ruff`, `black`) for the inventory and companion analysis producers.
* [ ] Extend schema validation to cover both structural and analysis artifacts, blocking unexpected changes in CI.
* [ ] Verify sequencing logic: companion analysis must fail fast when the index generation errors, preventing stale insights.
* [x] Pin `jsonschema` (currently validated with 4.22.0) in `requirements.txt` and CI environments so schema validation and integration tests run consistently. _(Verified 2025-10-24: `requirements.txt` lists `jsonschema==4.22.0`; ensure CI environments consume this lock when running producers/tests.)_

### Phase F – Test Data & Tooling Support

* [x] Create reusable test fixtures under `.repo_studios/tests/fixtures/function_inventory/` with representative module layouts. _(Sample package with duplicate helpers now drives integration coverage.)_
* [ ] Document fixture maintenance guidelines (adding/removing files) to keep snapshots aligned with schema expectations.
* [ ] Wire fixture regeneration helper (Make or script) to update golden outputs when schema changes or new analysis heuristics land.
* [ ] Provide paired golden artifacts (inventory + analysis) to validate dual-output freshness and cleanup behavior.

### Phase G – Tooling & Automation Wiring

* [ ] Define Make target (`studio-generate-function-index` or similar) with parameter validation and help text covering dual-output behavior.
* [ ] Update `.repo_studios/Makefile` hierarchy so the target runs the structural index producer first, then the companion analysis producer, reusing the same timestamp context.
* [ ] Implement shared logging that summarizes both outputs (paths, counts, warnings) and surfaces failure from either stage.
* [ ] Add GitHub Actions job/step (likely in `studio-inventory.yml`) to invoke the Make target on representative directories, asserting both artifacts exist.
* [ ] Decide on artifact upload or retention strategy for generated indices and analyses within CI runs, including cleanup of stale dated files.
* [ ] Ensure the Make target removes previous dated artifacts before regeneration so `<folder_name>_index/` contains only the freshest pair, per retention decision.

### Phase H – Documentation & Communication

* [x] Author intro documentation describing how to consume the new analysis outputs. _(`docs/automation/function_analysis_guide.md` now covers artifact structure, findings interpretation, and follow-on actions; inventory-specific guide pending.)_
* [ ] Update `script_inventory_architecture.md` to reflect remediation status, targets, tests, CI wiring, and the new companion analysis module.
* [ ] Refresh README or contributor docs with instructions for generating and reviewing structural inventories and companion analyses together.
* [ ] Draft communication plan covering manual usage deprecation timeline, insight interpretation guidance, and onboarding for teams adopting the analysis artifact.
* [ ] Publish an interpretation cheat sheet summarizing common analysis findings and recommended next actions.

### Phase I – Rollout & Monitoring

* [ ] Run pilot generation on `.repo_studios/scripts/producers/` and review output for accuracy and performance.
* [ ] Capture baseline index + analysis files for critical folders and commit them as part of the rollout.
* [ ] Establish monitoring checklist (e.g., periodic verification, size checks, schema validation scripts, analysis signal accuracy audits).
* [ ] Schedule post-integration review to assess adoption, gather feedback, and plan future enhancements (additional analyses, cross-folder rollups, API hooks).
* [ ] Track runtime and artifact size growth over time to ensure dual-output remains sustainable.

## Notes Collected

* Project purpose: speed up Copilot function discovery by creating co-located index JSON files (`<folder>_index/<folder>_index.json`).
* Dual-output architecture pairs the structural inventory with an insight-oriented analysis artifact, both generated from a single invocation.
* Design principles emphasize manual control via Make targets, explicit paths, committed artifacts, and atomic operations.
* Current prototype script (`phase1/generate_inventory.py`) performs recursive AST parsing, emits summary statistics, and writes to the co-located index directory.
* Existing workflow already runs `python3 tools/generate_inventory.py modules -v` manually (outside `.repo_studios` standards), implying partial adoption.
* Phased plan outlines phases 1–4 covering script development, Makefile integration, documentation, and validation.
* Example outputs include metadata (counts, timestamps), per-file structure, `module_first_line`, function signatures, line counts, aggregate statistics, and a synced `latest.json` pointer for quick consumption.
* Manual commands rely on explicit path arguments; there is no repo-root resolution or pruning yet.
* Regeneration remains an on-demand, user-triggered action; automation should focus on providing a standardized “point and shoot” flow that overwrites any existing index file in place.
* Ownership sits with the Repo Studios team, with plans to surface timestamps in JSON so review cycles can track freshness.
* Test coverage now depends on the `jsonschema` package for validating generated inventory and analysis payloads; the dependency is already locked in `requirements.txt`.

## Decisions Captured

* Keep indices co-located with the scanned folders; the tool should create `<folder>_index/` when missing and overwrite existing JSON artifacts when re-run.
* Companion analysis artifacts will live alongside the structural index, sharing timestamps and provenance data to reinforce paired consumption.
* Duplicate detection is the first-wave analysis deliverable, operational via signature+docstring grouping; hotspots are opportunistic add-ons and anomaly surfacing is deferred.
* The analysis bundle ships as a unified pass for all folders (no per-folder toggles initially).
* Retain only the freshest inventory/analysis pair in each `<folder_name>_index/` directory until archival needs emerge.
* Companion analysis outputs will include machine-readable action items alongside human-readable narratives.
* Regeneration cadence is explicitly on demand—no background automation.
* Validation of extracted metadata is underway using `.repo_studios/scripts/producers/` as the first reference dataset; latest analysis surfaced 52 duplicate groups across 416 functions.
* Users decide when and where to run the tool; no additional exclusion list machinery is required beyond the default ignored directories.
* Manual invocation (`python3 tools/...`) will be deprecated once the standardized Make/CI pathway is established to avoid divergence.

## Outstanding Considerations

* Document rationale for keeping artifacts co-located; clarify that Repo Studios centralized reports remain optional and not required for this workflow.
* Monitor repository growth from committed `_index` directories; current expectation is minimal impact, but revisit after initial rollout.
* Decide final script location (likely under `.repo_studios/scripts/producers/`) and migration path from `tools/generate_inventory.py`.
* Define a simple schema versioning approach (e.g., `schema_version` field) so future JSON changes remain traceable.
* Large module handling: leverage line counts and existing reports for deeper analysis; primary aim is first-line summaries and duplicate detection aiding refactors.
* Defer Markdown/HTML outputs; focus on JSON while leaving room for future sorting/filter enhancements once new needs emerge.
* Clarify documentation to position this as the canonical function inventory report while other producers cover complementary domains (classes, dependencies).
* Standard logging with exit code `0` on success and non-zero for fatal errors; ensure CI treats warnings separately from failures.
* Craft a transition plan that communicates deprecation of direct script usage, allowing a short overlap period before enforcing Make/CI pathways.
* Confirm fixture strategy for tests (location, reset tooling) and ensure golden outputs stay lightweight to avoid bloating the repo.
* Plan for cross-platform validation (Windows vs. POSIX path separators) when designing automated tests and CI runners.
* Validate that dual-output cleanup keeps only the freshest inventory/analysis pair per folder, preventing bloat inside `_index` directories.

## design_decisions_required

* None at this time—current design questions have been addressed; revisit as new analysis needs surface.

## Questions to Resolve

* **Artifact placement:** retain co-located `<folder_name>_index/` outputs. Tool execution remains manual (“point and shoot”); it creates the index folder when missing and overwrites existing JSON on rerun.
* **Regeneration cadence:** fully on demand, triggered by contributors as needed.
* **Metadata validation:** start by exercising the tool inside Repo Studios, beginning with `.repo_studios/scripts/producers/`, to inspect generated metadata and iterate on schema accuracy.
* **Scope control:** no additional inclusion/exclusion switches beyond the default ignored directories; users choose the folders they index.
* **Ownership & freshness:** Repo Studios team owns long-term maintenance. Regular reviews plus surfaced timestamps in the JSON will track when indices were last refreshed.
* **Command alignment:** deprecate direct `python3 tools/...` usage after Make/CI wiring is live to prevent divergent behaviors.

## Questions from Agent

* No existing JSON schema is published yet; we may need to author one alongside integration.
* Stick with JSON-only output for this phase; revisit additional formats later.
* No security or privacy blockers identified for CI usage.
* Expected usage targets folders with up to a few hundred Python files; size impacts remain unknown and should be monitored once live.
* We can target Python 3.12+ (aligned with Repo Studios CI), giving us flexibility in implementation choices.
