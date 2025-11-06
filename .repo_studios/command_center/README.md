# Library Integration Protocol

**Status:** Draft (2025-10-28)

**Purpose:** Provide a dedicated home for duplicate-analysis artifacts and the step-by-step playbook that Repo Studios agents follow when extracting shared utilities into `.repo_studios/library/`. Point any AI coding agent to this folder before asking for remediation so they ingest the full workflow.

---

## Directory Layout

```text
.repo_studios/command_center/
├── reports/              # Slugged duplicate detection mirrors and run folders
├── checklists/           # Living checklists (e.g., command_center_checklist.md snapshot copies)
├── docs/                 # Supplemental guides or decision logs for specific campaigns
└── README.md             # This protocol overview
```

> **Note:** Keep raw producer reports elsewhere (e.g., `.repo_studios/reports/producer_reports/`). Only place library-integration-specific artifacts and slugged mirrors here so this workspace stays focused.

---

## Shared Helper Modules

Centralise duplicate-prone helpers in `.repo_studios/command_center/scripts/libraries/` so producers, summarisers, and orchestrators share the same implementation. This folder is a **staging area** until the canonical `.repo_studios/library/` hierarchy exists, so every addition must comply with the naming blueprint in `que_for_integration/refactor_library/phase_1/naming_conventions.md` (training copy at `docs/naming_conventions.md`) and retain a documented destination for the eventual promotion step.

- `pathing.py` – exports `slugify_relative` for building slug-safe report directories; scripts keep `_slugify_relative` aliases for backward compatibility.
- `artifacts.py` – exports `copy_latest_artifact` (hardlink-first mirror helper) and `write_report_artifacts`, which centralises JSON/Markdown/log writers, mirrors `latest_*` pointers, and enforces timestamped run retention (respecting `.keep` sentinels).
- `cli.py` – exports path/keep-count configuration helpers (`resolve_repo_root`, `resolve_path`, `build_paths`, `build_keep_counts`) and config-driven shims (`PathsConfig`, `OptionsConfig`, `build_standard_paths`, `build_standard_options`) so duplicated CLI glue can converge before extraction. All Command Center producers now consume these configs, which means timestamped outputs, repo-root guards, and retention rules stay consistent across scripts.
- `__init__.py` – re-exports available helpers so dynamic imports in tests/orchestrators stay simple (`from libraries import slugify_relative, copy_latest_artifact, build_paths, …`).

When adding new helpers, keep them importable without mutating `sys.path` (matching current dynamic-import fallback), log the staging decision in the active checklist, and backfill unit tests under `.repo_studios/tests/tests_library_integration/libraries/`.

---

## Artifact Retention Policy

- Command Center scripts write artifacts through `write_report_artifacts`, which keeps the latest three timestamped runs by default while honoring `.keep` sentinels for extended history.
- Automation bundles (manifest, metrics summary, rollback assets) inherit the same default (`keep=3`) per Implementation Note 10 in `.repo_studios/command_center/docs/guardrails/library_extraction_guardrails.md`; raise overrides in the guardrail log when longer retention is required.
- When onboarding new producers or aggregators, ensure they call the shared helper (or pass `--keep` overrides deliberately) so duplicate matrices, manifest bundles, and metrics summaries all respect the retention budget and remain reviewable.

---

## Micro-Cycle Blueprint

Use this repeatable loop every time you address duplicate functions.

1. **Detect & Stage**  
   - Run the orchestrator (or individual scripts) to refresh the inventory, analysis, and duplicate scan for the current target.  
   - Inspect outputs under `<target>/<name>_index/` and `.repo_studios/command_center/reports/<slug>_duplicate_scan/`. Each run rewrites a single timestamped matrix/summary pair and removes stale siblings before mirroring the fresh files into both locations (helpers default to keeping the latest three runs and honor `.keep` guards), so capture history via commits rather than adding new folders.
2. **Align & Plan**  
   - Update `checklists/command_center_checklist.md` (or paste a dated copy) with detected groups, priorities, and decisions.  
   - Cross-reference naming conventions to pick the target library path.
3. **Extract & Implement**  
   - Move the canonical implementation into the library (verb_noun.py), honoring naming conventions.  
   - Add or extend tests under `.repo_studios/tests/tests_library/…` and update producer tests that import the function.
4. **Replace & Validate**  
   - Replace duplicates with imports.  
   - Run targeted tests and any affected producer suites. Capture summaries back in the run folder.
5. **Document & Commit**  
   - Record results in the mirrored duplicate summary (`.repo_studios/command_center/reports/<slug>_duplicate_scan/<name>_duplicate_summary-YYYY-MM-DD.md`) with duplicates resolved, tests run, and follow-up items.  
   - Update decision logs or docs under `docs/` if process adjustments were required.
6. **Repeat**  
   - Proceed to the next duplicate group only after documentation, tests, and reports are current.

---

## Automation Entry Points

### `orchestrators/run_command_center_pipeline.py`

- **Purpose:** Offer a single make-style trigger that refreshes the function inventory, analysis, and duplicate scan for any repository subfolder.
- **How it works:** Dynamically loads each script's `run(argv)` helper, executes them sequentially (inventory → analysis → duplicate scan), applies a shared log level, and aborts on the first non-zero exit code. The orchestrator captures the freshly written inventory and analysis paths and threads the analysis file into the duplicate scan so the aggregator always consumes the current dataset.
- **Outputs:** Emits no new standalone artifacts; it rewrites the producer inventory and analysis within `<target>/<name>_index/`, then mirrors timestamped duplicate matrices/markdown into both `<target>/<name>_index/` and `.repo_studios/command_center/reports/<slug>_duplicate_scan/`, pruning older siblings in each location.
- **Triggers:** `producers/generate_commandview_inventory.py`, `summarizers/generate_function_analysis.py`, and `aggregators/scan_duplicates.py` (called with `--skip-upstream` because upstream work already ran).
- **Benefits:** Guarantees consistent sequencing, keeps slug retention tidy, and logs the mirrored artifact paths so humans and agents can locate outputs immediately before Phase 3 extraction begins.

```bash
python .repo_studios/command_center/scripts/orchestrators/run_command_center_pipeline.py \
    .repo_studios/command_center/scripts --repo-root . --log-level INFO
```

```powershell
make -C .repo_studios command-center COMMAND_CENTER_TARGET=/.repo_studios/scripts/summarizers/ `
   PYTHON=.venv/Scripts/python.exe
```

#### Operations Notes

- **Invocation patterns:** Prefer the `make -C .repo_studios command-center` wrapper for day-to-day runs so the virtual environment path stays consistent; fall back to the Python module invocation when scripting bespoke targets or running from CI. Always pass `--repo-root .` when launching outside the repo root to keep path resolution deterministic.
- **Logging:** The orchestrator shares a single `--log-level` across all delegate scripts (`DEBUG`, `INFO`, `WARNING`, etc.). Logs stream to stdout; set `--log-level DEBUG` when investigating failures so each delegate echoes the resolved inventory/analysis paths before execution.
- **Retention behaviour:** Delegate scripts rely on `write_report_artifacts`, which keeps the latest three timestamped runs in both the target index and slugged report directories while respecting `.keep` sentinels. The orchestrator does not create additional artifacts—it simply surfaces the paths pruned/written during each stage.
- **Failure diagnostics:** A non-zero exit from any delegate stops the pipeline immediately and propagates the exit code. Check the preceding log lines for the failing script, inspect the partially written artifacts in `<target>/<name>_index/`, and re-run with `--skip-upstream` if only the duplicate scan failed so you can reuse the fresh inventory/analysis outputs.

### `orchestrators/run_automation_dry_run.py`

- **Purpose:** Capture rehearsal bundles (manifest, metrics summary, inputs, README) before automation writes are allowed.
- **How it works:** Delegates to `generate_automation_manifest.py`, then snapshots the manifest/metrics outputs alongside the supplied inputs. Pass `--post-run-matrix` (defaults to `que_for_integration/refactor_library/phase_4/POST_RUN_TEST_MATRIX.md`) to copy the latest test matrix into the bundle.
- **Outputs:** Writes `manifest.json`, `metrics_summary.json`, copied input payloads under `inputs/`, and a README summarising the run metadata. Parsed post-run commands from the matrix are mirrored into both JSON artifacts under `post_run_tests` so operators (and tooling) can launch the suites without re-reading markdown.
- **Usage tips:** Include `--guardrail-config` to snapshot the active guardrail YAML. When iterating on the matrix, update the markdown first—each dry-run bundles the exact commands, making regressions obvious in diff review.

### Direct script usage

- `producers/generate_commandview_inventory.py <target>` refreshes `<target>/<name>_index/<name>_index-YYYY-MM-DD.json` and the screening summary in both the target and slugged mirror.
- `summarizers/generate_function_analysis.py <target>` consumes the latest inventory (or an explicit `--inventory-file`) and mirrors analysis payloads to `<target>/<name>_analysis-YYYY-MM-DD.json` and `.repo_studios/command_center/reports/<slug>_analysis/`.
- `aggregators/scan_duplicates.py --target <target>` merges scanner output with the analysis and mirrors duplicate matrices/markdown to `.repo_studios/command_center/reports/<slug>_duplicate_scan/`. Add `--skip-upstream` when inventory and analysis were already run; the helper now removes stale timestamped outputs before writing the new pair in both locations.

---

## Usage Instructions

### For Humans

1. **Point the agent here** when requesting duplicate remediation.
2. **Trigger the orchestrator** (or run scripts manually) so the chosen target’s slug directories refresh.
3. **Review the mirrored artifacts** under `<target>/<name>_index/` and `.repo_studios/command_center/reports/<slug>_duplicate_scan/` before prioritising work.
4. **Consult the latest lizard complexity report** in `.repo_studios/reports/producer_reports/lizard_reports/latest_report.md`—the top-offender table now lists the highest risk functions with file locations, line numbers, and remediation suggestions to help sequence extractions.
5. **Check the naming guides** (`que_for_integration/refactor_library/naming_conventions.md` and `docs/naming_conventions.md`) before adding or moving shared helpers so promotion to `.repo_studios/library/` stays frictionless.
6. **Annotate the checklist** with decisions, edge cases, or approvals, then review changes before sign-off.

### For AI Coding Agents

1. **Read this README** to ingest expectations.  
2. **Inspect the latest slugged mirrors** (`<target>/<name>_index/` and `.repo_studios/command_center/reports/<slug>_duplicate_scan/`) to understand duplicate groups and stock decisions.  
3. **Review `.repo_studios/reports/producer_reports/lizard_reports/latest_report.md`** for a ranked list of the top 10 complexity offenders (with over-threshold deltas and recommended remediation actions) so extraction plans prioritise the highest pay-off targets.
4. **Consult the naming guides** (`que_for_integration/refactor_library/naming_conventions.md` and `docs/naming_conventions.md`) before drafting new helpers; keep modules `verb_noun` and record the eventual library destination.  
5. **Follow the micro-cycle**: extract → test → replace → document.  
6. **Update artifacts** (tests run, imports added, follow-up items) before signaling completion.  
7. **Leave run notes** in the duplicate summary markdown (`<target>/<name>_duplicate_summary-YYYY-MM-DD.md`) or append to the checklist.

---

## References

- `que_for_integration/refactor_library/command_center_checklist.md` – alignment plan with phase status and decisions.  
- `docs/templates/command_center_alignment_template.md` – reusable template for future initiatives.  
- `que_for_integration/refactor_library/naming_conventions.md` – canonical folder/file naming rules (training copy at `docs/naming_conventions.md`).  
- `que_for_integration/refactor_library/phase_3/PHASE_3_MANUAL_EXTRACTION_GUIDE.md` – detailed manual extraction walkthrough.

---

## Onboarding Checklist

Before starting a new remediation batch:

- [ ] Latest duplicate reports mirrored into `.repo_studios/command_center/reports/<slug>_duplicate_scan/`.  
- [ ] Checklist updated with priority targets and assigned owners.  
- [ ] Target library paths confirmed against naming conventions.  
- [ ] Tests identified/apportioned for library and producer impacts.  
- [ ] Rollback plan documented (backup locations, restore steps).

---

*Update this README whenever the protocol changes so future contributors and agents remain aligned.*
