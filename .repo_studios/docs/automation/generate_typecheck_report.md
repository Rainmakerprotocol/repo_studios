---
title: Typecheck Report Producer
audience: [Copilot, Agents, Developer]
role: [AutomationDoc]
owners: [repo_studios_team@rainmakerprotocol.dev]
status: active
version: 2.1.0
updated_at: 2025-12-17
tags: [producer, healthview, typecheck]
related_files:
  - .repo_studios/scripts/producers/generate_typecheck_report.py
  - .repo_studios/tests/tests_producers/test_generate_typecheck_report.py
  - .repo_studios/Makefile
---

# Typecheck Report Producer

The `generate_typecheck_report.py` producer runs `mypy` with the repository defaults and emits a canonical 3-artifact bundle for observability.

## Goals

* Run `mypy` with repo defaults (or configured overrides) and summarize the outcome for observability.
* Emit a canonical Repo Studios 3-artifact positional bundle (no mutable `latest_*`).
* Prune historical bundles according to `--artifacts-to-keep`.

## System Context

Default output:

* `.repo_studios/reports/producer_reports/healthview/typecheck_report/<YYYYMMDD-HHMM>/`
  * `manifest.json`
  * `summary.md`
  * `telemetry.json`

## Invocation

Preferred (standard): run via the Make target from `/.repo_studios/`.

```bash
make -C .repo_studios typecheck LOG_LEVEL=INFO
```

This runs a full-repo typecheck by default (equivalent to `--all`).

Direct CLI (from repo root):

```bash
python .repo_studios/scripts/producers/generate_typecheck_report.py \
  --repo-root . \
  --all \
  --output-dir .repo_studios/reports/producer_reports \
  --artifacts-to-keep 10 \
  --log-level INFO
```

To override targets:

```bash
python .repo_studios/scripts/producers/generate_typecheck_report.py \
  --repo-root . \
  --targets api agents/core \
  --output-dir .repo_studios/reports/producer_reports \
  --log-level INFO
```

Key flags:

* `--timestamp` — optional ISO8601 timestamp; omit to use current UTC.
* `--artifacts-to-keep` — number of historical runs to retain (default 10).
* `--log-level` — standard logging level.

Environment overrides:

* `TYPECHECK_TARGETS` — whitespace separated targets to check instead of the `pyproject.toml` list.
* `TYPECHECK_STRICT` — when truthy, append `--strict` to the `mypy` invocation.
* `HEALTH_TYPECHECK_FAST` — when truthy and no explicit targets are supplied, limit execution to curated fast-mode prefixes.

## Agent Instructions

* Treat `manifest.json` as the structured payload (includes raw mypy output and sampled errors).
* Keep `summary.md` human-readable and stable for diffing.
* Do not add extra artifacts beyond the canonical three.

## Testing

```bash
python -m pytest .repo_studios/tests/tests_producers/test_generate_typecheck_report.py
```

## Update Log

* 2025-12-17 — Migrated to canonical `healthview/typecheck_report/<YYYYMMDD-HHMM>/` bundle and removed legacy `latest_*` artifacts.

