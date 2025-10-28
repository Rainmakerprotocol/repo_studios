# Repo Studios Automation Hub

**Status:** Draft (2025-10-28)

This directory houses the automation runtime that keeps Repo Studios scripts, reports, and tests aligned. Every CLI under `.repo_studios/scripts/` follows the same `run(argv)` pattern so they can be imported safely in orchestrators, tests, and notebooks without spawning subprocesses.

---

## What lives here

- `command_center/` – duplicate remediation protocol, reports, checklists, and the new pipeline orchestrator.
- `command_center/scripts/libraries/` – shared helpers (`slugify_relative`, `copy_latest_artifact`, upcoming `write_report_artifacts`) used across Command Center producers and aggregators.
- `scripts/` – tiered automation (producers, consumers, aggregators, orchestrators, summarizers, utilities).
- `tests/` – pytest suites mirroring the script tiers (unit, integration, and smoke coverage).
- `reports/` – shared mirrors that slug targets for repeatable artifact names (inventory, analysis, duplicate scans).
- `tools/` – supporting helpers (lint hooks, retention utilities, schema validators).

---

## Primary entry points

### Command Center pipeline orchestrator

- **File:** `.repo_studios/command_center/scripts/orchestrators/run_command_center_pipeline.py`
- **Purpose:** Single make-style command that refreshes the function inventory, analysis, and duplicate scan for any repository slice.
- **How it works:** Dynamically imports each script's `run(argv)` helper, executes them sequentially (inventory → analysis → duplicate scan), applies a shared log level, and aborts on first failure. Fresh inventory and analysis paths are captured and handed to the duplicate scan so the aggregator always consumes the newest dataset.
- **Outputs:** Emits no additional artifacts; the delegated scripts rewrite `<target>/<name>_index/`, `.repo_studios/command_center/reports/<slug>_analysis/`, and `.repo_studios/command_center/reports/<slug>_duplicate_scan/` with a single timestamped matrix/summary pair while pruning stale siblings.
- **Benefits:** Keeps sequencing deterministic, gives humans a single command before library extraction, and guarantees slug-based retention stays tidy across reruns.

```bash
python .repo_studios/command_center/scripts/orchestrators/run_command_center_pipeline.py \
    <target> --repo-root . --log-level INFO
```

```powershell
make -C .repo_studios command-center COMMAND_CENTER_TARGET=/.repo_studios/scripts/summarizers/ `
    PYTHON=.venv/Scripts/python.exe
```

### Direct script families

- **Producers:** Harvest inventories and screening summaries into `<target>/<name>_index/` plus slugged mirrors.
- **Summarizers:** Enrich producer data (e.g., analysis reports) and mirror to `.repo_studios/command_center/reports/<slug>_analysis/`.
- **Aggregators:** Blend multi-source findings (duplicate scans) and mirror to `.repo_studios/command_center/reports/<slug>_duplicate_scan/`; pass `--skip-upstream` when orchestration already ran. The helper now deletes stale timestamped outputs before writing the new pair in both locations.

---

## Working agreements

- Always resolve targets within the declared `--repo-root`; scripts enforce this guardrail before they mutate artifacts.
- Prefer importing the `run(argv)` helpers over shelling out so automated tests and orchestrators remain lightweight.
- Logging flows through the `--log-level` flag; avoid `print` and rely on structured log lines for traceability.
- When adding new automation, update this README plus the relevant tier-specific documentation so future contributors can discover it quickly.
