# Library Integration Protocol

**Status:** Draft (2025-10-24)

**Purpose:** Provide a dedicated home for duplicate-analysis artifacts and the step-by-step playbook that Repo Studios agents follow when extracting shared utilities into `.repo_studios/library/`. Point any AI coding agent to this folder before asking for remediation so they ingest the full workflow.

---

## Directory Layout

```
.repo_studios/library_integration/
├── reports/              # Timestamped duplicate detection + extraction run logs
├── checklists/           # Living checklists (e.g., library_integration_checklist.md snapshot copies)
├── docs/                 # Supplemental guides or decision logs for specific campaigns
└── README.md             # This protocol overview
```

> **Note:** Keep raw producer reports elsewhere (e.g., `.repo_studios/reports/producer_reports/`). Only place library-integration-specific artifacts here so this workspace stays focused.

---

## Micro-Cycle Blueprint

Use this repeatable loop every time you address duplicate functions.

1. **Detect & Stage**  
   - Run the duplicate-report workflow (folder-level index + repo-wide duplicate analyzer).  
   - Save outputs under `reports/<YYYYMMDD_HHMMSS>/`. Include both raw JSON and any summarized Markdown.
2. **Align & Plan**  
   - Update `checklists/library_integration_checklist.md` (or paste a dated copy) with detected groups, priorities, and decisions.  
   - Cross-reference naming conventions to pick the target library path.
3. **Extract & Implement**  
   - Move the canonical implementation into the library (verb_noun.py), honoring naming conventions.  
   - Add or extend tests under `.repo_studios/tests/tests_library/…` and update producer tests that import the function.
4. **Replace & Validate**  
   - Replace duplicates with imports.  
   - Run targeted tests and any affected producer suites. Capture summaries back in the run folder.
5. **Document & Commit**  
   - Record results in `reports/<timestamp>/SUMMARY.md` (duplicates resolved, tests run, outstanding items).  
   - Update decision logs or docs under `docs/` if process adjustments were required.
6. **Repeat**  
   - Proceed to the next duplicate group only after documentation, tests, and reports are current.

---

## Usage Instructions

### For Humans

1. **Point the agent here** when requesting duplicate remediation.
2. **Deposit fresh reports** into `reports/<timestamp>/` using consistent naming (e.g., `duplicates_report.json`, `index_snapshot.json`).
3. **Annotate the checklist** with any prioritization decisions, edge cases, or approvals.
4. **Review the agent’s updates** by comparing the run folder and checklist changes; sign off when satisfied.

### For AI Coding Agents

1. **Read this README** to ingest expectations.  
2. **Inspect the latest report folder** to understand current duplicate groups and decisions.  
3. **Follow the micro-cycle**: extract → test → replace → document.  
4. **Update artifacts** (tests run, imports added, follow-up items) before signaling completion.  
5. **Leave run notes** in `reports/<timestamp>/SUMMARY.md` or append to the checklist.

### Duplicate Scanner CLI

- Run `python .repo_studios/scripts/library_integration/duplicates/scan_duplicates.py --help`
   for CLI options (supports target overrides, retention limits, and log level control).
- Each invocation writes artifacts to a timestamped folder named
   `<YYYYMMDD-HHMMSS>-duplicate_scan/` under `reports/` **and** mirrors
   `duplicate_matrix.json` + `duplicate_matrix_summary.md` into
   `reports/code_duplicates_report/latest/` for quick reference.
- Default behaviour automatically merges the latest producers analysis, so
   `duplicate_matrix.json` contains both producer findings and scanner-only
   groups.

---

## References

- `que_for_integration/refactor_library/library_integration_checklist.md` – alignment plan with phase status and decisions.  
- `docs/templates/library_integration_alignment_template.md` – reusable template for future initiatives.  
- `que_for_integration/refactor_library/naming_conventions.md` – canonical folder/file naming rules.  
- `que_for_integration/refactor_library/phase_3/PHASE_3_MANUAL_EXTRACTION_GUIDE.md` – detailed manual extraction walkthrough.

---

## Onboarding Checklist

Before starting a new remediation batch:

- [ ] Latest duplicate reports copied into `reports/<timestamp>/`.  
- [ ] Checklist updated with priority targets and assigned owners.  
- [ ] Target library paths confirmed against naming conventions.  
- [ ] Tests identified/apportioned for library and producer impacts.  
- [ ] Rollback plan documented (backup locations, restore steps).

---

*Update this README whenever the protocol changes so future contributors and agents remain aligned.*
