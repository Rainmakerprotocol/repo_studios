# Fault Diagnostics Summary

Generated (UTC): 2025-01-03T00:06:00+00:00

## Summary

- signature_count: 2
- active_signature_count: 2
- thread_block_count: 2
- top_frame_limit: 10
- stack_log_exists: True
- stack_text_bytes: 123
- first_seen_utc: 2025-12-26T18:10:27+00:00
- last_seen_utc: 2025-12-26T18:10:27+00:00

## Severity Buckets

- repeat_offender: 0
- multi_hit: 0
- single_hit: 2

## Dumps

- combined.txt

## Top Signatures

| count | signature_id | top | file:line | threads |
|------:|--------------|-----|----------:|---------|
| 1 | 50ef56fbf16d4669 | helper.assist | /svc/helper.py:3 | Thread 0x0002: |
| 1 | a34ea19ba723d047 | worker.work | /svc/worker.py:8 | Current thread 0x0001: |

<!-- markdownlint-disable-next-line MD013 -->
## Source References

- Run Directory: `C:\Users\genet\AppData\Local\Temp\pytest-of-genet\pytest-697\test_fault_artifacts_prunes_hi0\repo\.repo_studios\command_center\reports\rawview\fault_diagnostics_runs\2025-01-03_000000`
- Source Type: scan
- Run Summary: `C:\Users\genet\AppData\Local\Temp\pytest-of-genet\pytest-697\test_fault_artifacts_prunes_hi0\repo\.repo_studios\command_center\reports\rawview\fault_diagnostics_runs\2025-01-03_000000\SUMMARY.md`
- Stacks CSV: `C:\Users\genet\AppData\Local\Temp\pytest-of-genet\pytest-697\test_fault_artifacts_prunes_hi0\repo\.repo_studios\command_center\reports\rawview\fault_diagnostics_runs\2025-01-03_000000\stacks.csv`
- Combined Stack Text: `C:\Users\genet\AppData\Local\Temp\pytest-of-genet\pytest-697\test_fault_artifacts_prunes_hi0\repo\.repo_studios\command_center\reports\rawview\fault_diagnostics_runs\2025-01-03_000000\dumps\combined.txt`
