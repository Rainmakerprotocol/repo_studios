# Standards Index Diff Report

- generated_at: 2026-01-02T04:22:48.869861+00:00
- run_timestamp: 20260102-0422
- status: error
- old_index: .repo_studios\foo
- new_index: .repo_studios\bar
- fail_policy: any
- change_count: 0
- should_fail: false
- notes: Missing input files: C:\Users\genet\repo_studios\.repo_studios\foo, C:\Users\genet\repo_studios\.repo_studios\bar

## Summary

No rule changes detected.

## How to Reproduce

```bash
python C:\Users\genet\repo_studios\.repo_studios\scripts\producers\diff_standards_index.py .repo_studios\foo .repo_studios\bar --fail-on any
```
