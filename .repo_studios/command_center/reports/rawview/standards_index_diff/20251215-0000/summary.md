# Standards Index Diff Report

- generated_at: 2025-12-16T10:51:07.969273+00:00
- run_timestamp: 20251215-0000
- status: changes
- old_index: tmp_diff_old.yaml
- new_index: tmp_diff_new.yaml
- fail_policy: any
- change_count: 3
- should_fail: true
- integrity_hash_changed: true

## Summary

| Change Kind | Count |
|---|---:|
| added | 1 |
| severity_changed | 1 |
| summary_changed | 1 |

## Changes

| Rule ID | Kind | Details |
|---|---|---|
| STD-001 | severity_changed | low → high |
| STD-001 | summary_changed |  |
| STD-002 | added |  |

## How to Reproduce

```bash
python C:\Users\genet\repo_studios\.repo_studios\scripts\producers\diff_standards_index.py tmp_diff_old.yaml tmp_diff_new.yaml --fail-on any
```
