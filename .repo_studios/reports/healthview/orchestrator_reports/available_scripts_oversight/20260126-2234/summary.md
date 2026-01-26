# Available Scripts Oversight Run

Run: `20260126-2234` | Completed: 2026-01-26T22:34:47.863853+00:00

## Pipeline Status

| Phase | Step | Status | Detail |
| --- | --- | --- | --- |
| Producer | validate_import_boundaries | ✅ ok | exit_code=0 |
| Producer | check_inventory_health | ✅ ok | exit_code=0 |
| Producer | validate_inventory | ✅ ok | exit_code=0 |
| Producer | render_inventory_views | ✅ ok | exit_code=0 |
| Consumer | generate_anchor_health_report | ✅ ok | exit_code=None |

---

## Producer Artifacts

- **validate_import_boundaries:** `C:\Users\genet\repo_studios\.repo_studios\reports\healthview\producer_reports`
- **check_inventory_health:** `C:\Users\genet\repo_studios\.repo_studios\reports\healthview\producer_reports\healthview\inventory_health\20260126-2234`
- **validate_inventory:** `C:\Users\genet\repo_studios\.repo_studios\reports\healthview\producer_reports\20260126-2234`
- **render_inventory_views:** `C:\Users\genet\repo_studios\.repo_studios\reports\healthview\producer_reports\healthview\inventory_overview\20260126-2234`

## Consumer Artifacts

- **generate_anchor_health_report:** `C:\Users\genet\repo_studios\.repo_studios\reports\healthview\consumer_reports`

---

## Excluded Scripts

The following scripts are excluded from orchestration:

- ASR-002, ASR-003, ASR-004: Utilities (invoked by other scripts)
- ASR-006: Library module (no CLI)
- ASR-009: Deprecated summarizer
- ASR-011: Missing run(argv) entry point
- ASR-013: Library module (no CLI)
