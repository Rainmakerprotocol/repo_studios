---
title: Lizard Complexity Report Producer
audience:
  - coding_agent
  - human_developer
owners:
  - repo_studios_team@rainmakerprotocol.dev
status: active
version: 2.0.0
updated: 2025-12-16
tags:
  - producer
  - healthview
  - complexity
related_files:
  - ../../scripts/producers/generate_lizard_report.py
  - ../../tests/tests_producers/test_generate_lizard_report.py
  - ../../Makefile
---

# generate_lizard_report.py

## Goals

* Produce a Repo Studios positional bundle summarizing cyclomatic complexity and long-function offenders.
* Remain tolerant: always return exit code `0`, encoding failures inside the telemetry payload.
* Avoid mutable `latest_*` pointers; rely on timestamped run directories + pruning.

## System Context

This producer runs `python -m lizard` against selected targets inside the repo and writes a canonical 3-artifact bundle.

Default output:

* `.repo_studios/reports/producer_reports/healthview/lizard_report/<YYYYMMDD-HHMM>/`
  * `manifest.json`
  * `summary.md`
  * `telemetry.json`

## Agent Instructions

* Treat `telemetry.json` as the machine-readable source of truth.
* Use `summary.md` for human review.
* Do not reintroduce `latest_*` pointers.

## Invocation

```bash
python .repo_studios/scripts/producers/generate_lizard_report.py \
  --repo-root . \
  --targets src package_a \
  --output-dir .repo_studios/reports/producer_reports \
  --max-ccn 15 \
  --max-length 80 \
  --artifacts-to-keep 10
```

### Key arguments

* `--repo-root` (default `.`): working tree root used to resolve relative targets.
* `--targets` (optional): explicit directories/packages to scan. When omitted the script probes the default set `("agents", "api", "scripts")` under the repo root (or `LIZARD_TARGETS` if set).
* `--extra-args`: verbatim switches appended before the targets (passes directly to `lizard`).
* `--output-dir` (default `.repo_studios/reports/producer_reports`): base reports directory.
* `--timestamp`: ISO8601 string (UTC preferred) to seed the run directory timestamp (`YYYYMMDD-HHMM`).
* `--max-ccn`, `--max-length`: thresholds for flagging high-complexity or long functions (defaults respect `LIZARD_MAX_CCN` / `LIZARD_MAX_LENGTH` environment overrides).
* `--artifacts-to-keep` (default `10`): retention window applied after each run.
* `--log-level` (default `INFO`): Python logging verbosity during execution.

Notes:

* The producer injects `-Ejson -i -1` ahead of any provided extra arguments so the lizard run emits JSON and never fails the producer because of warning counts.
* On first use the script may auto-install a lightweight `lizard_ext.lizardjson` helper (vendored under `.repo_studios/vendor/lizard_ext/lizardjson.py`) into the active environment when it is absent.
* `lizard` must be installed in the active Python environment (`pip install lizard`).

## Human Notes

* `telemetry.json.payload.offenders` contains the full offender list with deltas.
* `telemetry.json.payload.log_text` preserves a diff-friendly key/value view.
* `telemetry.json.payload.raw` contains truncated stdout/stderr and a small JSON sample for debugging.

## Update Log

* 2025-12-16 — Migrated to canonical positional bundle under `healthview/lizard_report/<YYYYMMDD-HHMM>/` with `manifest.json`, `summary.md`, and `telemetry.json`. Removed `latest_*` pointers and folded legacy raw/log artifacts into the telemetry payload.
