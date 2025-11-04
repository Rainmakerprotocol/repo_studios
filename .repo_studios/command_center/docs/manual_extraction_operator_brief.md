# Manual Extraction Operator Brief

**Status:** Draft (2025-10-30)

This note packages the key resources operators need when executing Phase 3 manual extractions. Share this document with anyone running the checklist so they align with the latest tooling and report outputs.

---

## Required Inputs

- Latest duplicate pipeline artifacts for the chosen target (inventory, analysis, duplicate scan) mirrored under:
  - `<target>/<name>_index/`
  - `.repo_studios/command_center/reports/<slug>_duplicate_scan/`
- Latest lizard complexity report in `.repo_studios/reports/producer_reports/lizard_reports/`. The `report.md` file now surfaces the top 10 offenders with path, line numbers, delta over thresholds, and recommended actions.
- Manual extraction checklist: `.repo_studios/command_center/docs/manual_extraction_checklist.md`
- Run-folder summary template: `.repo_studios/command_center/docs/run_folder_summary_template.md`

---

## Execution Checklist

1. **Review Top Offenders**  
   Open `latest_report.md` from the lizard report directory. Note any functions highlighted in orchestrator scripts or shared helpers. Confirm whether they overlap with the duplicate groups scheduled for extraction.
2. **Refresh Duplicate Artifacts**  
   Run the command center orchestrator (`python .repo_studios/command_center/scripts/orchestrators/run_command_center_pipeline.py <target> --repo-root .`) or the individual scripts to generate fresh inventory, analysis, and duplicate scan artifacts.
3. **Walk the Manual Checklist**  
   Use the manual extraction checklist to track each required step (naming confirmation, library destination, tests, documentation). Capture deviations or blockers inline.
4. **Populate Run Folder Summary**  
   For each extraction session, copy the run-folder template into the slugged report directory (`reports/<timestamp>/SUMMARY.md`) and record duplicates addressed, tests run, and follow-up actions.
5. **Coordinate Tests**  
   Ensure both library unit tests and affected producer tests are executed. Document the commands and outcomes in the run summary.
6. **Flag Feedback**  
   Log checklist improvements, missing guidance, or Windows-specific hurdles in the alignment checklist so documentation stays current.

---

## Quick Reference Commands

```powershell
# Refresh command center pipeline for scripts target
python .repo_studios/command_center/scripts/orchestrators/run_command_center_pipeline.py `
    .repo_studios/scripts --repo-root . --log-level INFO

# Generate focused lizard report (top 10 offenders table)
python .repo_studios/scripts/producers/generate_lizard_report.py --repo-root . `
    --targets .repo_studios/scripts
```

---

## Feedback Loop

- Capture operator feedback directly in `.repo_studios/command_center/docs/library_integration_checklist.md` under Phase 3 updates.
- Raise blockers in the run summary and link supporting artifacts (logs, reports).
- Update this brief when the manual checklist or report formats change.
