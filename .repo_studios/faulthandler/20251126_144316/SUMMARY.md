# Fault Diagnostics Summary

Generated (UTC): 2025-11-26T15:14:13+00:00

## Summary

- signature_count: 2
- active_signature_count: 2
- thread_block_count: 2
- top_frame_limit: 10
- stack_log_exists: True
- stack_text_bytes: 123
- first_seen_utc: 2025-11-26T15:14:13+00:00
- last_seen_utc: 2025-11-26T15:14:13+00:00

## Severity Buckets

- repeat_offender: 0
- multi_hit: 0
- single_hit: 2

## Dumps

- combined.txt

## Top Signatures

| count | signature_id | top | file:line | threads |
|------:|--------------|-----|----------:|---------|
| 1 | 32af38317e8bad7c | helper.assist | /svc/helper.py:3 | Thread 0x0002: |
| 1 | 650320c2bda19304 | worker.work | /svc/worker.py:8 | Current thread 0x0001: |

