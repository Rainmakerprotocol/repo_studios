# Mermaid Viewer Documentation Index

## Purpose

Provide a single discovery point for the Command Center Mermaid viewer so contributors, operators, and AI agents can locate the right artifact before diving into implementation details.

## 5W1H Overview

- **Who**: Command Center maintainers, Repo Studios engineers, and automation agents needing CommandView insight.
- **What**: Progressive-detail viewer documentation covering roadmap, decisions, view specifications, and operational notes.
- **When**: Consult before launching or modifying the viewer, and whenever Phase 8+ backlog items are evaluated for a new release.
- **Where**: Core assets live under `.repo_studios/command_center/viewer/` (implementation) and `.repo_studios/command_center/docs/mermaid/` (governance + specs).
- **Why**: Centralizes knowledge so future contributors can understand context, trace decisions, and extend the viewer without relearning history.
- **How**: Follow the navigation map below, starting with the viewer README for runtime steps and the roadmap for strategic planning.

## Navigation Map

- `mermaid_viewer.md` — Phase-based delivery plan, backlog, and status notes (treat Phase 8+ as v2 planning placeholders).
- `decision_log.md` — Chronological log of architectural and process choices impacting the viewer.
- `inventory_migration_notes.md` — Historical notes on CommandView inventory alignment that underpin the viewer’s data contracts.
- `mermaid_integration_checklist.md` — Tracking document for integration milestones and verification steps.
- `view_specs/` — Detailed specifications for each view/builder, including required data slices and expected outputs.
- `../viewer/README.md` — Operational quick start, troubleshooting, and 5W1H summary for running the viewer.
- `../viewer/TROUBLESHOOTING.md` — Deep dive into runtime failure modes beyond the quick-start guidance.

## Standards & References

- Follow `docs/standards/global/std-global-markdown-authoring.md` when updating these files.
- Reference `docs/standards/global/std-global-python-engineering.md` for docstring expectations in supporting scripts.
- Capture new decisions in `decision_log.md` and annotate `mermaid_viewer.md` when roadmap items progress or are replaced.

## Future Contributions

- Validate new documentation links here whenever files move or new assets are added.
- If v2 planning supersedes Phase 8–10, update this index to reflect the revised scope and retire obsolete entries.
