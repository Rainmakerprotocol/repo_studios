# run_standards_index_cli.py (Retired Shim)

**Last updated:** 2025-12-10

## Status

The legacy CLI wrapper was removed during Phase 8 of the orchestrator rollout. All automation should now invoke
`command_center/scripts/orchestrators/run_standards_integrity.py` or the meta orchestrator instead of the shim. Historical
artifacts previously stored in `.repo_studios/reports/orchestrator_runs/standards_index_cli/` have been deleted; the Standards
Integrity topic orchestrator produces canonical bundles under `.repo_studios/reports/healthview/orchestrator_reports/standards_integrity/<YYYYMMDD-HHMM>/`.

## Replacement Workflow

Run the topic orchestrator directly:

```bash
python .repo_studios/command_center/scripts/orchestrators/run_standards_integrity.py \
  --repo-root . \
  --log-level INFO
```

This entry point refreshes the standards index, gap analysis, diff, and prompt seeds, then publishes Healthview bundles and
publishes HealthView/HOP bundles.

For ad-hoc exploration, load the standards index JSON/YAML directly or build small utilities on top of the producer output. The
deprecated CLI subcommands (`list`, `search`, `show`, `stats`) are intentionally absent to reduce maintenance overhead; replicate
them by querying `.repo_studios/scripts/repo_standards_index.yaml` inside a notebook or script when necessary.

## Testing

Validate orchestrator behaviour with:

```bash
.venv/Scripts/python.exe -m pytest \
  .repo_studios/tests/tests_command_center/standards_integrity/test_run_standards_integrity.py
```

The suite exercises catalog registration, retention budgets, manifest emission, and Healthview wiring.

## Operational Notes

- Remove any lingering references to `run_standards_index_cli.py` in scripts or playbooks; the module no longer ships with the
  repository.
- Standards catalog consumers should ingest the HealthView manifest or read `.repo_studios/scripts/repo_standards_index.yaml`; the
  pipeline refreshes both surfaces.
- If a future CLI interface is required, prefer adding a subcommand to the Standards Integrity orchestrator so retention, logging,
  and output contracts stay aligned with the new pipeline.
