---
title: "Phase 4 Build Document — ASR-001 generate_anchor_health_report.py"
audience: [Copilot, Agents, Developers]
role: [Documentation, Implementation]
owners: [command_center]
status: complete
version: "1.0.0"
updated_at: "2026-01-28"
tags: [phase-4, ASR-001, anchor-health, build-doc, stage-11.1]
related_files:
  - .repo_studios/scripts/consumers/generate_anchor_health_report.py
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier3_scripts/available_scripts_oversight/tier3_generate_anchor_health_report.yaml
  - .repo_studios/command_center/docs/db_integrations/db_integration_anchor_health_report.md
---

# Phase 4 Build Document — ASR-001 generate_anchor_health_report.py

## Script Identity

| Field | Value |
|-------|-------|
| ASR ID | ASR-001 |
| Script | `generate_anchor_health_report.py` |
| Path | `.repo_studios/scripts/consumers/generate_anchor_health_report.py` |
| Category | consumer |
| Stage | 11.1 — Available Scripts Oversight |
| Lines | 645 |
| Tier-3 YAML | `tier3_generate_anchor_health_report.yaml` |

**Purpose:** HOP-compliant consumer that generates anchor health reports for markdown heading duplication analysis.

---

## Current State (2026-01-28)

| Aspect | Status | Notes |
|--------|--------|-------|
| Entry Point | ✅ `run(*, argv=...)` | Keyword-args signature with argv passthrough |
| Artifact Names | ✅ HOP-compliant | `manifest.json`, `summary.md`, `telemetry.json` + supplementary |
| Pointer Files | None | HOP-compliant (no `latest_*`) |
| Output Root | HOP-compliant | Uses `build_topic_path("consumer", TOPIC_SLUG)` |
| Directory Format | HOP-compliant | `anchor_health-YYYY-MM-DD_HHMM` |

---

## Evidence

### Code References

| Location | Content |
|----------|---------|
| L1-L27 | Module docstring with HOP compliance documentation |
| L51 | `TOPIC_SLUG = "anchor_health"` |
| L292 | `OUTPUT_DIR = build_topic_path("consumer", TOPIC_SLUG)` |
| L405-L513 | `write_artifacts()` — base package + supplementary |
| L558-L625 | `run(*, argv=...)` — orchestrator entry point |

### Tests (3/3 passing)

- `test_anchor_health_uses_inventory_artifacts` (PASSED)
- `test_anchor_health_falls_back_to_docs_scan` (PASSED)
- `test_anchor_health_prunes_history` (PASSED)

---

## Orchestrator Integration

**ScriptConfig in `run_available_scripts_oversight.py`:**

```python
ScriptConfig(
    name="generate_anchor_health_report",
    path=".repo_studios/scripts/consumers/generate_anchor_health_report.py",
    uses_argv_kwarg=True,  # run(*, ..., argv=...) signature
    supports_output_dir=False,  # Uses topic-aware default: build_topic_path("consumer", "anchor_health")
)
```

> **⚠️ SAFETY WARNING — supports_output_dir**
>
> This script uses `build_topic_path("consumer", TOPIC_SLUG)` for default output.
> Setting `supports_output_dir=True` would override this behavior, causing
> outputs to land in a generic parent directory and enabling cross-topic
> pruning incidents. The `False` setting preserves the script's topic-aware
> default path behavior.
>
> **Lesson from ASR-011 incident (2026-01-28):** A `supports_output_dir=True`
> misconfiguration caused 343 files to be deleted across unrelated topics.

---

## DB Integration Status

| Field | Status | Notes |
|-------|--------|-------|
| Uses create_storage() | ❌ No | Uses direct file writes via write_artifacts() |
| DB_INTEGRATION_MARKERs | ❌ Missing | Would need retrofit for dual-write support |
| db_integration doc | ⚠️ Stale | Says "Planned Stage: 2.2" but script is in Stage 11.1 orchestrator |

**Action needed:** Update `db_integration_anchor_health_report.md` to reflect Stage 11.1 integration.

---

## Update Log

| Date | Author | Changes | Status |
|------|--------|---------|--------|
| 2026-01-25 | Agent | Code compliance: run() entry, HOP artifacts | Complete |
| 2026-01-26 | Agent | Bug fix: main() argv handling; multi-root scanning | Complete |
| 2026-01-28 | Agent | Doc compliance: Tier-3 YAML, build doc, orchestrator integration | Complete |
