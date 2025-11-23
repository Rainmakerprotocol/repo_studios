# Standards Index Diff Report

- generated_utc: 2025-11-23T17:49:07.993905+00:00
- status: error
- old_index: .repo_studios\reports\producer_reports\standards_index_snapshots\previous.yaml
- new_index: .repo_studios\reports\producer_reports\standards_index_snapshots\current.yaml
- fail_policy: any
- change_count: 0
- should_fail: false
- notes: Missing input files: C:\Users\genet\repo_studios\.repo_studios\reports\producer_reports\standards_index_snapshots\previous.yaml, C:\Users\genet\repo_studios\.repo_studios\reports\producer_reports\standards_index_snapshots\current.yaml

## Summary

No rule changes detected.

## How to Reproduce

```bash
python C:\Users\genet\repo_studios\.repo_studios\scripts\producers\diff_standards_index.py .repo_studios\reports\producer_reports\standards_index_snapshots\previous.yaml .repo_studios\reports\producer_reports\standards_index_snapshots\current.yaml --fail-on any
```
