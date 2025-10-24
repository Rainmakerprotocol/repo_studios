# Placeholder Scan Report

- Status: `ok`
- Timestamp: `2025-10-23T12:28:59.813560+00:00`
- Scan Root: `.`
- Total Matches: 1175
- Patterns: FIXME, NOTE, OPTIMIZE, REVIEW, TODO, XXX
- Extensions: .js, .json, .md, .py, .ts, .txt, .yaml, .yml
- Allowlist Entries: 0

## Matches by Pattern

| Pattern | Count |
| --- | ---: |
| `FIXME` | 32 |
| `NOTE` | 391 |
| `OPTIMIZE` | 16 |
| `REVIEW` | 16 |
| `TODO` | 657 |
| `XXX` | 63 |

## Sample Findings

| Path | Line | Pattern | Snippet |
| --- | ---: | --- | --- |
| .repo_studios/agent_notes/meta/phase1_foundation_review_2025-10-18_0138.md | 1 | `REVIEW` | # Phase 1 Foundation Review |
| .repo_studios/docs/governance/alignment-ledger.md | 80 | `REVIEW` | * Review UI benchmarking doc against current Chainlit standards and schedule an update if discrepancies remain after Batch 2. |
| .repo_studios/docs/governance/alignment-ledger.md | 81 | `REVIEW` | * Validate faulthandler rollout evidence (blocklist/allowlist artifacts) before the mid-term milestone review. |
| .repo_studios/docs/governance/alignment-ledger.md | 761 | `REVIEW` | *Source: Batch 1; Inventory #8, #36.* **Owner:** Diagnostics owner *(human evidence review).* **Automation:** |
| .repo_studios/docs/governance/alignment-ledger.md | 877 | `NOTE` | **Note:** Ensure PromQL examples reference final metric names. |
| .repo_studios/docs/governance/alignment-ledger.md | 908 | `NOTE` | **Note:** Ensure placeholders replaced with milestone dates. |
| .repo_studios/docs/governance/alignment-ledger.md | 936 | `NOTE` | **Note:** Should reference observability roadmap linkage. |
| .repo_studios/docs/governance/alignment-ledger.md | 967 | `REVIEW` | **[2025-10-01 Pending KPI]** Success metric still under review with agents performance lead. |
| .repo_studios/docs/governance/alignment-ledger.md | 989 | `REVIEW` | **⚠️ Gap:** Need roadmap review outcomes. |
| .repo_studios/docs/governance/alignment-ledger.md | 990 | `REVIEW` | **[2025-10-01 Pending Owner Matrix]** Owner assignments awaiting roadmap review sign-off. |
| .repo_studios/docs/governance/alignment-ledger.md | 1031 | `REVIEW` | * [ ] Review residual payloads under `models/` and `ledger_tmp/`, archiving or deleting non-doc files |
| .repo_studios/docs/governance/alignment-ledger.md | 1043 | `NOTE` | *Source: Inventory #4.* **Owner:** Tooling governance. **Automation:** repo to note policy after |
| .repo_studios/docs/templates/agent_note_template.md | 1 | `NOTE` | # Agent Note Template |
| .repo_studios/scripts/orchestrators/run_pytest_log_capture.py | 172 | `NOTE` | # Note idle but avoid sending signals that may terminate pytest |
| .repo_studios/scripts/producers/extract_standards_rules.py | 178 | `NOTE` | # Ignore silently (could add error note in future) |
| .venv/Lib/site-packages/_pytest/_code/code.py | 100 | `XXX` | # XXX maybe try harder like the weird logic |
| .venv/Lib/site-packages/_pytest/_code/code.py | 452 | `XXX` | # XXX needs a test |
| .venv/Lib/site-packages/_pytest/_code/code.py | 1048 | `XXX` | #    # XXX |
| .venv/Lib/site-packages/_pytest/_code/code.py | 1484 | `XXX` | # xxx let decorators etc specify a sane ordering |
| .venv/Lib/site-packages/_pytest/_code/code.py | 1485 | `NOTE` | # NOTE: this used to be done in _pytest.compat.getfslineno, initially added |

