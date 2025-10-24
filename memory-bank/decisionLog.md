# Decision Log

- 2025-10-18 — Migrated project-level operating standard and monkey patch governance into `.repo_studios/docs/standards/` with updated inventory metadata to replace legacy guidance.

| Date | Decision | Rationale |
|------|----------|-----------|
| 2025-10-18 | Migrated project operating and monkey patch standards into `.repo_studios/docs/standards/` with updated inventory metadata. | Replaced legacy guidance to align inventories and agent instructions with the new Repo Studios structure. |
| 2025-10-21 | Established mirrored reports directory hierarchy under `.repo_studios/reports/` matching the six-tier script taxonomy and documented artifact destinations. | Keeps future report outputs aligned with the reorganized scripts while we defer code rewires. |
| 2025-10-21 | Refreshed `scripts_manifest.yaml` to match the producer→consumer→aggregator→orchestrator→summarizer→utility taxonomy and recorded each script's new report target. | Gives agents a single manifest tying legacy script names to current locations and report destinations before code rewires begin. |
| 2025-10-21 | Refactored `generate_anchor_inventory.py` to emit structured reports with pruning, latest pointers, and matching tests plus Make wiring. | Aligns anchor inventory producer with remediation loop expectations and keeps artifacts parseable for downstream agents. |
| 2025-10-21 | Refactored `analyze_standards_index_gaps.py` with structured JSON/MD/TSV artifacts, pruning, tests, and Make wiring. | Keeps gap detection aligned with producer standards and provides reusable artifacts for standards triage agents. |
| 2025-10-22 | Refactored `check_inventory_health.py` to emit structured JSON/MD/log artifacts with pruning and dedicated pytest coverage. | Aligns the inventory health producer with the remediation loop expectations and preserves CI visibility into threshold breaches. |
| 2025-10-22 | Curated `generate_import_graph_report.py` defaults to scan `.repo_studios` and `legacy`, moved artifacts under producer reports, and documented the change. | Ensures import graph runs populate the unified reports hierarchy while capturing real module coverage for Repo Studios code. |
| 2025-10-22 | Began refactoring `generate_lizard_report.py` to emit structured artifacts under `producer_reports`, add logs/latest pointers, and introduce pytest coverage. | Aligns the complexity producer with the refactor loop blueprint while preserving tolerant behavior and history pruning. |
| 2025-10-23 | Refactored `validate_inventory.py` with repo-root aware path resolution, structured artifact bundles, pruning, pytest coverage, and automation docs. | Keeps the inventory validator aligned with the producer standards and surfaces missing legacy assets while preserving the legacy `--json` interface. |
| 2025-10-23 | Extended inventory roles enum with `governance` and updated inventory paths off `.repo_studios_legacy/`. | Unblocked validator runs by recognizing governance documents and pointing catalog records at the migrated `.repo_studios/` and `legacy/` assets. |
| 2025-10-23 | Initiated remediation loop for `verify_docs_integrity.py` with focus on structured artifacts, pruning, tests, and documentation. | Documents the next producer refactor target and aligns work with the standard remediation blueprint. |
