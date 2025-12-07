# Healthview Command Center Onboarding

**Last updated:** 2025-12-05

## Purpose

This guide equips Command Center operators and automation engineers with the steps required to
publish, surface, and validate Healthview artifacts alongside existing CommandView data. It
summarises the wiring required for selector manifests, viewer tabs, and the supporting CSS/JS so the
new diagnostics surface launches without disrupting current dashboards.

## Audience and Scope

- **Audience:** Command Center maintainers, documentation owners, and AI agents automating the
  Healthview rollout.
- **Out of scope:** Legacy CommandView-only workflows and orchestrator implementation details
  (see `docs/automation/orchestrator_automation_hooks.md` for individual CLI guidance).

## Prerequisites

1. Phase 4 topic orchestrators produce timestamped bundles under
   `.repo_studios/command_center/reports/healthview/<topic>/<timestamp>/`.
2. `REPORT_NAMING_STANDARDS.md` is enforced (no `latest_*` aliases; viewer/topic/timestamp naming).
3. `reports_naming_audit.py` passes with zero violations for the Healthview directory tree.
4. Command Center viewer tooling is available on the active machine (`PYTHONPATH=".repo_studios"`
   and `.venv` configured).

## Healthview Bundle Layout

Healthview artifacts mirror CommandView filenames but live under the `healthview` viewer slug. Each
orchestrator run emits:

```
.repo_studios/command_center/reports/healthview/<topic>/<timestamp>/
  manifest.json
  summary.md
  telemetry.json
```

Key expectations:

- `<topic>` uses kebab-case (for example `docs_health`, `dependency_import_hygiene`).
- `<timestamp>` follows `YYYYMMDD-HHMM` (UTC) and matches the manifest payload.
- Summaries follow `docs/standards/global/std-global-markdown-authoring.md`.
- Telemetry payloads include shared counters from
  `command_center/scripts/libraries/telemetry_emitters.py`.

## Selector Wiring

Healthview appears in the viewer once selector entries include the `healthview` slug. Use the
standard tooling:

1. Refresh selector payloads after orchestrator runs:

   ```powershell
   .venv\Scripts\python.exe -m command_center.viewer.generate_selector --repo-root .
   ```

2. Confirm `selector.json` contains a top-level entry whose `slug` equals `"healthview"` and that
   each option references the Healthview directory via `relative_path`, `absolute_path`, and
   `target_repo_relative` values. Use the layout stub in
   `docs/automation/orchestrator_implementation.md` → *Healthview Viewer Wiring Reference* as a
   template.

3. If a CI job publishes selector artifacts, ensure the job runs after the topic orchestrators and
   stores the new `selector.json` alongside CommandView outputs.

## Viewer Tab Integration

When introducing the Healthview tab to the Command Center viewer:

1. Update `viewer/ui/index.html` to add a `data-viewer="healthview"` tab button (mirroring the
   existing CommandView entry) so the tab strip can toggle between viewers.
2. Extend `viewer/ui/viewer.js` by registering a new viewer descriptor inside the existing viewer
   registry (search for `VIEWER_DEFINITIONS`). The handler should:
   - Surface Healthview options inside `renderSelector` while preserving CommandView behaviour.
   - Use `buildArtifactUrl()` to fetch Healthview manifests; do not handcraft URLs.
   - Render Markdown summaries into the status panel until bespoke diagrams ship.
3. Ensure `viewer/ui/viewer.css` inherits styling by applying the existing `.view-tab` and
   `.viewer-surface` classes. Limit custom selectors so theme overrides remain compatible.
4. Re-run `npm run lint` (if the viewer lint pipeline is active) or the documented lint workflow to
   confirm no style regressions.

## JavaScript and CSS Considerations

- Keep IDs and class names ASCII-only; follow
  `.repo_studios/docs/standards/global/std-global-css-authoring.md` for specificity limits and dark
  theme contrast rules.
- Healthview tab logic must continue to respect the memoisation and caching described in
  `viewer-wiring-trace.md`. Use existing helper functions (`setEntries`, `renderViewTabs`,
  `updateStatus`) instead of duplicating state management.
- Any new fetch paths must pass through `buildArtifactUrl()` so deployments that host reports on a
  different origin remain functional.
- Provide console logging that mirrors existing patterns (`console.info("Healthview:", ...)`) and
  guard failures with `try/catch` blocks that surface errors in the status panel.

## Validation Checklist

- [ ] `reports_naming_audit.py` run shows zero Healthview violations.
- [ ] `selector.json` includes the `healthview` entry with all orchestrator options.
- [ ] Viewer tab renders locally via `serve_viewer.py` with the new tab visible and responsive.
- [ ] Markdown summaries render without layout overflow; audit using browser responsive mode.
- [ ] Telemetry JSON loads successfully (verify via browser developer tools).

## Operational Notes

- Healthview onboarding is tracked under Phase 6 of
  `docs/automation/orchestrator_implementation.md`; update that plan after completing the above
  checklist.
- CI jobs that publish viewer artifacts should call `generate_selector.py` after the orchestrators
  complete and rerun `reports_naming_audit.py` before uploading.
- Agent prompts referencing CommandView must be updated to detect the new `healthview` slug so they
  do not assume a single viewer.

## References

- `docs/automation/orchestrator_implementation.md`
- `REPORT_NAMING_STANDARDS.md`
- `.repo_studios/command_center/viewer/viewer-wiring-trace.md`
- `.repo_studios/command_center/viewer/README.md`
- `.repo_studios/command_center/scripts/libraries/guardrails.py`
