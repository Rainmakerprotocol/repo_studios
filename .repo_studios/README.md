# Repo Studios Automation Hub

**Status:** Draft (2025-10-27)

This directory houses the automation runtime that keeps Repo Studios scripts, reports, and tests aligned. Every CLI under `.repo_studios/scripts/` follows the same `run(argv)` pattern so they can be imported safely in orchestrators, tests, and notebooks without spawning subprocesses.

---

## What lives here

- `command_center/` – duplicate remediation protocol, reports, checklists, and the new pipeline orchestrator.
- `scripts/` – tiered automation (producers, consumers, aggregators, orchestrators, summarizers, utilities).
- `tests/` – pytest suites mirroring the script tiers (unit, integration, and smoke coverage).
- `reports/` – shared mirrors that slug targets for repeatable artifact names (inventory, analysis, duplicate scans).
- `tools/` – supporting helpers (lint hooks, retention utilities, schema validators).

---

## Primary entry points

### Command Center pipeline orchestrator

- **File:** `.repo_studios/command_center/scripts/orchestrators/run_command_center_pipeline.py`
- **Purpose:** Single make-style command that refreshes the function inventory, analysis, and duplicate scan for any repository slice.
- **How it works:** Dynamically imports each script's `run(argv)` helper, executes them sequentially (inventory → analysis → duplicate scan), applies a shared log level, and aborts on first failure. It passes `--skip-upstream` to the aggregator so upstream stages are not duplicated.
- **Outputs:** Emits no additional artifacts; the delegated scripts rewrite `<target>/<name>_index/`, `.repo_studios/command_center/reports/<slug>_analysis/`, and `.repo_studios/command_center/reports/<slug>_duplicate_scan/` in place.
- **Benefits:** Keeps sequencing deterministic, gives humans a single command before library extraction, and guarantees slug-based retention stays tidy across reruns.

```bash
python .repo_studios/command_center/scripts/orchestrators/run_command_center_pipeline.py \
    <target> --repo-root . --log-level INFO
```

### Direct script families

- **Producers:** Harvest inventories and screening summaries into `<target>/<name>_index/` plus slugged mirrors.
- **Summarizers:** Enrich producer data (e.g., analysis reports) and mirror to `.repo_studios/command_center/reports/<slug>_analysis/`.
- **Aggregators:** Blend multi-source findings (duplicate scans) and mirror to `.repo_studios/command_center/reports/<slug>_duplicate_scan/`; pass `--skip-upstream` when orchestration already ran.

---

## Working agreements

- Always resolve targets within the declared `--repo-root`; scripts enforce this guardrail before they mutate artifacts.
- Prefer importing the `run(argv)` helpers over shelling out so automated tests and orchestrators remain lightweight.
- Logging flows through the `--log-level` flag; avoid `print` and rely on structured log lines for traceability.
- When adding new automation, update this README plus the relevant tier-specific documentation so future contributors can discover it quickly.
