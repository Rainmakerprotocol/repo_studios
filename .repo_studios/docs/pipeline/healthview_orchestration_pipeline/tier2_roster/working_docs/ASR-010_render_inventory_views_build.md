---
title: "Phase 4 Build Document — ASR-010 render_inventory_views.py"
audience: [Copilot, Agents, Developers]
role: [Documentation, Implementation]
owners: [command_center]
status: complete
version: "1.0.0"
updated_at: "2026-01-28"
tags: [phase-4, ASR-010, inventory-overview, build-doc, stage-11.1]
related_files:
  - .repo_studios/scripts/producers/render_inventory_views.py
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier3_scripts/available_scripts_oversight/tier3_render_inventory_views.yaml
  - .repo_studios/command_center/docs/db_integrations/db_integration_render_inventory_views.md
---

# Phase 4 Build Document — ASR-010 render_inventory_views.py

## Script Identity

| Field | Value |
|-------|-------|
| ASR ID | ASR-010 |
| Script | `render_inventory_views.py` |
| Path | `.repo_studios/scripts/producers/render_inventory_views.py` |
| Category | producer |
| Stage | 11.1 — Available Scripts Oversight |
| Lines | 576 |
| Tier-3 YAML | `tier3_render_inventory_views.yaml` |

**Purpose:** HOP-compliant producer that renders structured inventory views and maintains legacy compatibility.

---

## Current State (2026-01-28)

| Aspect | Status | Notes |
|--------|--------|-------|
| Entry Point | ✅ `run(argv)` | Returns payload dict with 7 keys |
| Artifact Names | ✅ HOP-compliant | `manifest.json`, `summary.md`, `telemetry.json` via create_storage() |
| Pointer Files | None | HOP-compliant (no `latest_*`) |
| Output Root | HOP-compliant | Uses `DEFAULT_OUTPUT_DIR / TOPIC_SLUG / slug` |
| Directory Format | HOP-compliant | `YYYYMMDD-HHMM` |

---

## Evidence

### Code References

| Location | Content |
|----------|---------|
| L1-L10 | Module docstring (note: path in docstring is stale) |
| L30-L33 | `VIEWER_SLUG`, `TOPIC_SLUG`, `DEFAULT_OUTPUT_DIR` |
| L42-L47 | `create_storage` import |
| L538-L544 | Storage writes with DB_INTEGRATION_MARKER tags |
| L450-L571 | `run(argv)` entry point |

### DB Integration Markers

| Line | Marker | Artifact |
|------|--------|----------|
| L539 | `DB_INTEGRATION_MARKER: write manifest` | manifest.json |
| L541 | `DB_INTEGRATION_MARKER: write summary` | summary.md |
| L543 | `DB_INTEGRATION_MARKER: write telemetry` | telemetry.json |

### Tests (2/2 passing)

- `test_render_inventory_views_structured_output` (PASSED)
- `test_run_returns_payload_dict` (PASSED)

---

## Orchestrator Integration

**ScriptConfig in `run_available_scripts_oversight.py`:**

```python
ScriptConfig(
    name="render_inventory_views",
    path=".repo_studios/scripts/producers/render_inventory_views.py",
    supports_artifacts_to_keep=False,  # Uses --timestamp only, hard-coded keep=1
    supports_output_dir=False,  # Uses topic-aware default with VIEWER_SLUG/TOPIC_SLUG
)
```

> **⚠️ SAFETY WARNING — supports_output_dir**
>
> This script uses `create_storage(output_dir, "", TOPIC_SLUG, timestamp=slug)` for
> HOP-compliant output paths. Setting `supports_output_dir=True` would override this
> behavior, causing outputs to land in a generic parent directory and enabling
> cross-topic pruning incidents. The `False` setting preserves the script's
> topic-aware default path behavior.
>
> **Lesson from ASR-011 incident (2026-01-28):** A `supports_output_dir=True`
> misconfiguration caused 343 files to be deleted across unrelated topics.

---

## DB Integration Status

| Field | Status | Notes |
|-------|--------|-------|
| Uses create_storage() | ✅ Yes | L538 — full dual-write capable |
| DB_INTEGRATION_MARKERs | ✅ Present | L539, L541, L543 |
| db_integration doc | ✅ Accurate | Already describes create_storage() pattern |

**Note:** This is the only Stage 11.1 script that uses `create_storage()` — others use direct file writes.

---

## Special Characteristics

1. **Hard-coded retention:** `prune_run_directories(topic_dir, keep=1)` — no `--artifacts-to-keep` flag
2. **Legacy compatibility:** Writes redirect stubs to `views_dir` for backward compatibility
3. **Docstring path stale:** Says `reports/producer_reports/healthview` but actual is `reports/healthview/producer_reports`

---

## Update Log

| Date | Author | Changes | Status |
|------|--------|---------|--------|
| 2026-01-26 | Agent | Code compliance: run(argv) entry added | Complete |
| 2026-01-28 | Agent | Doc compliance: Tier-3 YAML, build doc, orchestrator integration | Complete |
