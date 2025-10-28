# Library Integration Protocol

**Status:** Draft (2025-10-27)

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

## Micro-Cycle Blueprint

Use this repeatable loop every time you address duplicate functions.

1. **Detect & Stage**  
   - Run the orchestrator (or individual scripts) to refresh the inventory, analysis, and duplicate scan for the current target.  
   - Inspect outputs under `<target>/<name>_index/` and `.repo_studios/command_center/reports/<slug>_duplicate_scan/`. Each run rewrites the same date-stamped files, so retain history via commits rather than appending folders.
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
- **How it works:** Dynamically loads each script's `run(argv)` helper, executes them sequentially (inventory → analysis → duplicate scan), applies a shared log level, and aborts on the first non-zero exit code.
- **Outputs:** Emits no new artifacts; it simply rewrites the producer inventory and analysis within `<target>/<name>_index/` and mirrors duplicate matrices/markdown into `.repo_studios/command_center/reports/<slug>_duplicate_scan/`.
- **Triggers:** `producers/generate_function_inventory.py`, `summarizers/generate_function_analysis.py`, and `aggregators/scan_duplicates.py` (with `--skip-upstream`).
- **Benefits:** Guarantees consistent sequencing, keeps slug retention tidy, and creates the one-shot command we need before Phase 3 extraction begins.

```bash
python .repo_studios/command_center/scripts/orchestrators/run_command_center_pipeline.py \
    .repo_studios/command_center/scripts --repo-root . --log-level INFO
```

### Direct script usage

- `producers/generate_function_inventory.py <target>` refreshes `<target>/<name>_index/<name>_index-YYYY-MM-DD.json` and the screening summary in both the target and slugged mirror.
- `summarizers/generate_function_analysis.py <target>` consumes the latest inventory (or an explicit `--inventory-file`) and mirrors analysis payloads to `<target>/<name>_analysis-YYYY-MM-DD.json` and `.repo_studios/command_center/reports/<slug>_analysis/`.
- `aggregators/scan_duplicates.py --target <target>` merges scanner output with the analysis and mirrors duplicate matrices/markdown to `.repo_studios/command_center/reports/<slug>_duplicate_scan/`. Add `--skip-upstream` when inventory and analysis were already run.

---

## Usage Instructions

### For Humans

1. **Point the agent here** when requesting duplicate remediation.
2. **Trigger the orchestrator** (or run scripts manually) so the chosen target’s slug directories refresh.
3. **Review the mirrored artifacts** under `<target>/<name>_index/` and `.repo_studios/command_center/reports/<slug>_duplicate_scan/` before prioritising work.
4. **Annotate the checklist** with decisions, edge cases, or approvals, then review changes before sign-off.

### For AI Coding Agents

1. **Read this README** to ingest expectations.  
2. **Inspect the latest slugged mirrors** (`<target>/<name>_index/` and `.repo_studios/command_center/reports/<slug>_duplicate_scan/`) to understand duplicate groups and stock decisions.  
3. **Follow the micro-cycle**: extract → test → replace → document.  
4. **Update artifacts** (tests run, imports added, follow-up items) before signaling completion.  
5. **Leave run notes** in the duplicate summary markdown (`<target>/<name>_duplicate_summary-YYYY-MM-DD.md`) or append to the checklist.

---

## References

- `que_for_integration/refactor_library/command_center_checklist.md` – alignment plan with phase status and decisions.  
- `docs/templates/command_center_alignment_template.md` – reusable template for future initiatives.  
- `que_for_integration/refactor_library/naming_conventions.md` – canonical folder/file naming rules.  
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
