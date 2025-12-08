# Repo Studios Automation Hub

**Status:** Draft (2025-10-28)

This directory houses the automation runtime that keeps Repo Studios scripts, reports, and tests
aligned. Every CLI under `.repo_studios/scripts/` follows the same `run(argv)` pattern so they can
be imported safely in orchestrators, tests, and notebooks without spawning subprocesses.

---

## What lives here

- `command_center/` – duplicate remediation protocol, reports, checklists, and the new pipeline orchestrator.
- `command_center/scripts/libraries/` – staging area for shared helpers (`slugify_relative`,
    `copy_latest_artifact`, `write_report_artifacts`, CLI utilities) used across Command Center
    producers and aggregators; the artifact helper mirrors `latest_*` pointers and prunes historical
    runs. Naming and staging must follow
    `que_for_integration/refactor_library/phase_1/naming_conventions.md` (training copy at
    `.repo_studios/command_center/docs/naming_conventions.md`) so modules can move cleanly into
    `.repo_studios/library/` when that hierarchy lands. The CLI module now ships config-first
    builders (`PathsConfig`, `OptionsConfig`, `build_standard_paths`, `build_standard_options`)
    and every producer in this workspace is wired through them for consistent repo-root guards
    and retention defaults.
- `scripts/` – tiered automation (producers, consumers, aggregators, orchestrators, summarizers, utilities).
- `tests/` – pytest suites mirroring the script tiers (unit, integration, and smoke coverage).
- `reports/` – shared mirrors that slug targets for repeatable artifact names (inventory,
    analysis, duplicate scans).
- `tools/` – supporting helpers (lint hooks, retention utilities, schema validators).

---

## Primary entry points

### Command Center pipeline orchestrator

- **File:** `.repo_studios/command_center/scripts/orchestrators/run_command_center_pipeline.py`
- **Purpose:** Single make-style command that refreshes the CommandView inventory, analysis, and
    duplicate scan for any repository slice.
- **How it works:** Dynamically imports each script's `run(argv)` helper, executes them sequentially
    (CommandView inventory → analysis → duplicate scan), applies a shared log level, and aborts on
    first failure. Fresh inventory and analysis paths are captured and handed to the duplicate scan
    so the aggregator always consumes the newest dataset.
- **Outputs:** Emits no additional artifacts; the delegated scripts rewrite
    `<target>/<name>_index/`, `.repo_studios/command_center/reports/<slug>_analysis/`, and
    `.repo_studios/command_center/reports/<slug>_duplicate_scan/` with a single timestamped
    matrix/summary pair while pruning stale siblings.
- **Benefits:** Keeps sequencing deterministic, gives humans a single command before library
    extraction, and guarantees slug-based retention stays tidy across reruns.

```bash
python .repo_studios/command_center/scripts/orchestrators/run_command_center_pipeline.py \
    <target> --repo-root . --log-level INFO
```

```powershell
make -C .repo_studios command-center COMMAND_CENTER_TARGET=/.repo_studios/scripts/summarizers/ `
    PYTHON=.venv/Scripts/python.exe
```

### Direct script families

- **Producers:** Harvest CommandView inventories and screening summaries into
    `<target>/<name>_index/` plus slugged mirrors.
- **Summarizers:** Enrich producer data (e.g., analysis reports) and mirror to
    `.repo_studios/command_center/reports/<slug>_analysis/`.
- **Aggregators:** Blend multi-source findings (duplicate scans) and mirror to
    `.repo_studios/command_center/reports/<slug>_duplicate_scan/`; pass `--skip-upstream`
    when orchestration already ran. The helper now deletes stale timestamped outputs before
    writing the new pair in both locations.

---

## Working agreements

- Always resolve targets within the declared `--repo-root`; scripts enforce this guardrail before
    they mutate artifacts.
- Prefer importing the `run(argv)` helpers over shelling out so automated tests and orchestrators
    remain lightweight.
- Logging flows through the `--log-level` flag; avoid `print` and rely on structured log lines
    for traceability.
- When adding new automation, update this README plus the relevant tier-specific documentation
    so future contributors can discover it quickly.

### Library staging & naming conventions

- Treat `.repo_studios/command_center/scripts/libraries/` as a temporary staging ground for helpers
    until the canonical `.repo_studios/library/` tree is created.
- Follow the naming contract in `que_for_integration/refactor_library/phase_1/naming_conventions.md`
    (training copy at `.repo_studios/command_center/docs/naming_conventions.md`): three-level
    hierarchy, `verb_noun.py` modules, and primary functions that match filenames.
- When introducing or relocating a shared helper, update the relevant checklist entry and note the
    eventual library destination so the promotion step stays traceable.
