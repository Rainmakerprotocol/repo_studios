---
title: generate_doc_index.py
audience: [Copilot, Agents, Developer]
role: [Operational-Doc]
owners: [repo_studios_team@rainmakerprotocol.dev]
status: live
version: 2.0.0
updated: 2025-12-29
tags: [docs, producer, healthview, doc-index]
related_files:
  - .repo_studios/scripts/producers/generate_doc_index.py
  - .repo_studios/tests/tests_producers/test_generate_doc_index.py
  - .repo_studios/command_center/scripts/libraries/database_integration.py
  - .repo_studios/command_center/scripts/libraries/prune_logs.py
  - REPORT_NAMING_STANDARDS.md
---

# generate_doc_index.py

## Goals

`generate_doc_index.py` emits a repo-wide inventory of Markdown documents so AI agents and operators can locate
content, follow cross-links, and understand section structure without rescanning the filesystem.

## System Context

- Producer script: `.repo_studios/scripts/producers/generate_doc_index.py`
- Viewer/topic: `producer_reports/doc_index`
- Output base: `.repo_studios/reports/healthview/`

## Agent Instructions

- Prefer `make -C .repo_studios doc-index` for normal refreshes (also refreshes checkbox report + Tier-3 index).
- Canonical bundle location: `.repo_studios/reports/healthview/producer_reports/doc_index/<YYYYMMDD-HHMM>/`.
- For structured ingestion, read `telemetry.json` and use `payload` as the authoritative JSON.

## Output Contract

- Writes a positional bundle under `.repo_studios/reports/healthview/producer_reports/doc_index/<YYYYMMDD-HHMM>/`.
- Each run directory contains:
  - `manifest.json`
  - `summary.md`
  - `telemetry.json`
- Additionally, the run directory includes a human-facing export:
  - `doc_index.csv`
- Mutable `latest_*` pointers are not written.
- Retention defaults to one run; older run directories are pruned (configurable via `--artifacts-to-keep`).
- When `--db-target` is supplied the run records placeholder metadata; no DB-specific behavior is required.

## Data Shape

- The full doc index payload is retained under `telemetry.json` → `payload`.
- `telemetry.json` also includes a compact `metrics` block for quick downstream consumption.
- `summary.md` embeds JSON/YAML/CSV renderings for human review and disables line-length lint within the bundle.

Each document entry (in `telemetry.json` → `payload` → `documents`) includes:

- `folder`, `filename`, `slug`
- `h1_headings`, `h2_headings` (with 1-based line numbers + parent linkage)
- `links` (ordered, de-duplicated; image links excluded)
- `description` (first qualifying paragraph after H1, trimmed)
- `size_bytes`, `modified_utc`
- `tags`, `owners`, `status`, `frontmatter`
- `contains_placeholder`

## CLI Reference

- `--repo-root`: override repository root discovery (defaults to script location depth traversal).
- `--output-dir`: base reports directory (default: `.repo_studios/reports/healthview`).
- `--artifacts-to-keep`: retention count (defaults to `1`).
- `--timestamp`: ISO-8601 timestamp override for deterministic tests.
- `--db-target`: optional sink identifier; recorded as placeholder metadata.
- `--log-level`: standard logging verbosity flag.

## Implementation Summary

- Uses `build_standard_paths` / `build_standard_options` for repo-root + retention parsing.
- Persists artifacts via `create_storage(...)` and prunes with `prune_run_directories(...)`.
- Writes are annotated with `DB_INTEGRATION_MARKER` comments at each storage write site.

## Notes for AI Consumers

- Prefer `telemetry.json` → `payload` for structured ingestion.
- The embedded JSON/YAML/CSV in `summary.md` mirrors the payload for human review.

## Update Log

- 2025-12-16: Migrated to positional bundle contract (`manifest.json`, `summary.md`, `telemetry.json`) and removed
  legacy `latest_*` pointers.
- 2025-12-29: Migrated output root to the HealthView HOP layout (`.repo_studios/reports/healthview/producer_reports/doc_index/<ts>/`).
