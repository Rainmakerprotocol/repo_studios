# Placeholder Scan Report

- Status: `ok`
- Run Timestamp: `20260124-1338`
- Scan Root: `.`
- Total Matches: 5
- Patterns: FIXME, NOTE, OPTIMIZE, REVIEW, TODO, XXX
- Extensions: .js, .json, .md, .py, .ts, .txt, .yaml, .yml
- Allowlist Entries: 0

## Matches by Pattern

| Pattern | Count |
| --- | ---: |
| `NOTE` | 2 |
| `XXX` | 3 |

## Sample Findings

| Path | Line | Pattern | Snippet |
| --- | ---: | --- | --- |
| .repo_studios/command_center/docs/db_integration_template.md | 161 | `XXX` | # Line ~XXX in main() or run() |
| .repo_studios/command_center/docs/db_integration_template.md | 172 | `XXX` | # Line ~XXX - write manifest |
| .repo_studios/command_center/docs/db_integration_template.md | 175 | `XXX` | # Line ~XXX - write telemetry |
| .repo_studios/command_center/scripts/libraries/retention_policy.py | 244 | `NOTE` | # NOTE: We intentionally do NOT call get_script_retention(script_key) here. |
| .repo_studios/scripts/producers/scan_monkey_patches.py | 94 | `NOTE` | # NOTE: Keep the producer default topic aligned with the Stage 5.1 orchestrator naming. |
