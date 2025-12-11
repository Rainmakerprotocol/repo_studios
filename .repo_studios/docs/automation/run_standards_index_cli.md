# run_standards_index_cli.py (Retired Shim)

**Last updated:** 2025-12-10

## Status

The legacy CLI wrapper was removed during Phase 8 of the orchestrator rollout. All automation should now invoke
`command_center/scripts/orchestrators/run_standards_integrity.py` or the meta orchestrator instead of the shim. Historical
artifacts previously stored in `.repo_studios/reports/orchestrator_runs/standards_index_cli/` have been deleted; the Standards
Integrity topic orchestrator produces canonical bundles under `.repo_studios/command_center/reports/healthview/standards_integrity/<timestamp>/`.

## Replacement Workflow

Run the topic orchestrator directly:

```bash
python .repo_studios/command_center/scripts/orchestrators/run_standards_integrity.py \
  --repo-root . \
  --log-level INFO
```

This entry point refreshes the standards index, gap analysis, diff, and prompt seeds, then publishes Healthview bundles and
updates producer `latest_*` pointers (for example `.repo_studios/reports/producer_reports/standards_index_reports/latest_index.yaml`).

For ad-hoc exploration, load the standards index JSON/YAML directly or build small utilities on top of the producer output. The
deprecated CLI subcommands (`list`, `search`, `show`, `stats`) are intentionally absent to reduce maintenance overhead; replicate
them by querying `latest_index.yaml` inside a notebook or script when necessary.

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
- Standards catalog consumers should ingest the Healthview manifest or `latest_index.yaml`; both remain inside the producer report
  hierarchy that the orchestration pipeline refreshes.
- If a future CLI interface is required, prefer adding a subcommand to the Standards Integrity orchestrator so retention, logging,
  and output contracts stay aligned with the new pipeline.
