# Screening Signal Timeline View Spec

**Status:** Prototype builder rendering docstring coverage history with multi-view coexistence verified (2025-11-08)

## Goal

Render a chronological view of Command Center screening scores so reviewers can see when inventories crossed warning or failure thresholds. The timeline should highlight meaningful score deltas, threshold crossings, and streaks to guide remediation plans and release readiness checks.

## Required Inputs

| Source | Fields Needed | Notes |
| --- | --- | --- |
| CommandView screening artifact (`*_commandview_screening_YYYYMMDD-HHMM.json`) | Historical score entries with timestamp, pack identifier, and severity | ✅ Delivered via `score_snapshot` + `score_history` (docstring coverage pack with severity thresholds) emitted by `generate_commandview_inventory.py`. |
| CommandView inventory metadata | `metadata.generated_at`, `metadata.folder_name` | Used to anchor the timeline start/end bounds and title. |
| Index scan analysis bundle (`index_scan_analysis/<slug>_analysis/*.json`) | `findings[].severity`, `findings[].tags` | Optional enrichment to annotate spikes with concrete findings. |

## Transformations (Planned)

1. Normalize score history into chronological events (`timestamp`, `pack`, `score`, `severity`).
2. Detect threshold crossings (e.g., `score >= warning`, `score >= failure`) per pack.
3. Produce contiguous segments representing stability or escalation windows to reduce noise in the Mermaid timeline.
4. Map events to Mermaid nodes using consistent styling for severity levels and annotate significant findings from the analysis bundle when available.

## Mermaid Output Sketch

```
sequenceDiagram
    Participant Inventory as CommandView Inventory
    Note over Inventory: Screening history timeline
    Inventory->>Inventory: <pack>: <score>
    Inventory->>Inventory: Threshold exceeded
```

Implementation will likely adopt a `timeline` or `sequenceDiagram` with custom styling cues for severity and optional annotations that link back to findings.

## Data Gaps

- Broaden scoring beyond docstring coverage (e.g., type hints, complexity, churn) to provide richer Health pack signals once additional packs are prioritized.
- Threshold metadata (warning/failure cutoffs) must remain exported alongside events to avoid hardcoding UI defaults in viewers.

## Next Actions

1. ✅ Extend the screening workflow to persist `score_history` with timestamps and severity buckets (landed 2025-11-08).
2. ✅ Update normalization helpers to ingest the new history block into `state.normalizedData` (new requirement key: `screeningHistory`) — completed 2025-11-08 by GitHub Copilot.
3. ✅ Implement the view builder once history data is available — prototype wired 2025-11-08 by GitHub Copilot.
4. ✅ Align Health pack controls with the new timeline output so operators can open the view even when only snapshot data exists — wired 2025-11-08 by GitHub Copilot.
5. ✅ Add dedicated regression coverage for the timeline wiring and multi-view coexistence — `.repo_studios/tests/tests_command_center/viewer/test_screening_signal_timeline_view.py::test_screening_timeline_definition_is_stable_across_repeated_calls` confirms repeated renders retain state (2025-11-08 by GitHub Copilot).
