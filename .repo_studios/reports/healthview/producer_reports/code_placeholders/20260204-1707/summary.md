# Placeholder Scan Report

- Status: `ok`
- Run Timestamp: `20260204-1707`
- Scan Root: `.`
- Total Matches: 11
- Patterns: FIXME, NOTE, OPTIMIZE, REVIEW, TODO, XXX
- Extensions: .js, .json, .md, .py, .ts, .txt, .yaml, .yml
- Allowlist Entries: 5

## Matches by Pattern

| Pattern | Count |
| --- | ---: |
| `NOTE` | 2 |
| `TODO` | 4 |
| `XXX` | 5 |

## Sample Findings

| Path | Line | Pattern | Snippet |
| --- | ---: | --- | --- |
| .repo_studios/command_center/scripts/libraries/retention_policy.py | 253 | `NOTE` | # NOTE: We intentionally do NOT call get_script_retention(script_key) here. |
| .repo_studios/docs/pipeline/healthview_orchestration_pipeline/stage12_templates/common/review_metaprompts.md | 555 | `XXX` | * Gap ID(s) Resolved: Link to GAP-XXX from Section 5 |
| .repo_studios/docs/pipeline/healthview_orchestration_pipeline/stage12_templates/PROMPT_PHASE4_FINALIZE.md | 307 | `XXX` | ##### S21R-XXX {script_name} |
| .repo_studios/docs/pipeline/healthview_orchestration_pipeline/stage12_templates/PROMPT_PHASE4_FINALIZE.md | 320 | `XXX` | <!-- AGENT_ROUTER:START S21R-XXX --> |
| .repo_studios/docs/pipeline/healthview_orchestration_pipeline/stage12_templates/PROMPT_PHASE4_FINALIZE.md | 321 | `XXX` | ### S21R-XXX — {script_name} |
| .repo_studios/docs/pipeline/healthview_orchestration_pipeline/stage12_templates/PROMPT_PHASE4_FINALIZE.md | 323 | `XXX` | <!-- AGENT_ROUTER:END S21R-XXX --> |
| .repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/stage_prefix_index.yaml | 113 | `NOTE` | # NOTE: library/ removed 2026-02-02 — no library scripts exist yet. |
| .repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/tier2_dependency_import_hygiene_roster.md | 608 | `TODO` | **Keywords:** `placeholders`, `technical-debt`, `code-quality`, `TODO`, `producer` |
| .repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/working_docs/stage_2_1/S21R-004_validate_markdown_anchors_build.md | 822 | `TODO` | **Command:** `Select-String -Path "BUILD_DOC_PATH" -Pattern "<[A-Z_]+>\|TODO\|TBD\|PLACEHOLDER"` |
| .repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/working_docs/stage_4_1/S41R-004_scan_code_placeholders_build.md | 643 | `TODO` | **Command:** `Select-String -Path "{BUILD_DOC_PATH}" -Pattern "<[A-Z_]+>\|TODO\|TBD\|PLACEHOLDER"` |
| .repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/working_docs/stage_4_1/S41R-005_generate_typecheck_report_build.md | 701 | `TODO` | **Command:** `Select-String -Path "<BUILD_DOC>" -Pattern "<[A-Z_]+>\|TODO\|TBD\|PLACEHOLDER"` |
