---
title: Standards Integrity Output Review (2026-01-21)
audience: [Copilot, Agents, Developers]
role: [review, quality]
owners: [repo_studios]
status: draft
version: 1
updated_at: 2026-01-21
tags: [healthview, standards, orchestrator, stage-6.1, agent-ux]
related_files:
  - .repo_studios/command_center/scripts/orchestrators/run_standards_integrity.py
  - .repo_studios/scripts/producers/generate_standards_index.py
  - .repo_studios/scripts/producers/seed_standards_prompts.py
  - .repo_studios/scripts/summarizers/summarize_standards.py
  - .repo_studios/scripts/.repo_studios/standards_seed.yaml
  - .repo_studios/scripts/.repo_studios/standards_categories.yaml
---

# Standards Integrity — Output Quality & Agentic Usability Review

See `.github/instructions/markdown.instructions.md` for repo-wide rules.

## Goals

- Evaluate Stage 6.1 (Standards Integrity) artifacts for correctness, consistency, and traceability.
- Identify changes that improve agent ergonomics without violating HealthView/HOP invariants.
- Capture concrete implementation targets (scripts + fields) for follow-up work.

## System Context

- Latest inspected run slug: `20260121-1138`
- Baseline run slug (pre-fix reference): `20260121-0026`
- Orchestrator bundle:
  - `.repo_studios/reports/healthview/orchestrator_reports/standards_integrity/20260121-1138/`
- Linked bundles:
  - Standards index producer: `.repo_studios/reports/healthview/producer_reports/standards_index/20260121-1138/`
  - Index gaps producer: `.repo_studios/reports/healthview/producer_reports/standards_index_gaps/20260121-1138/`
  - Prompt seeds producer: `.repo_studios/reports/healthview/producer_reports/standards_prompt_seeds/20260121-1138/`
  - Standards overview summarizer: `.repo_studios/reports/healthview/summarizer_reports/standards_overview/20260121-1138/`

Additional validation run slugs referenced in this review:

- `20260121-0202` (first post-fix confirmation)
- `20260121-1132` (orchestrator prompt unique vs assignment counts)
- `20260121-1138` (prompt seed telemetry.json is valid JSON envelope)

## Agent Instructions

<!-- agents:begin:standards_integrity_review -->
```yaml
audience: [Copilot, Agents]
inputs:
  run_slug: 20260121-1138
  primary_artifact_dir: .repo_studios/reports/healthview/orchestrator_reports/standards_integrity/20260121-1138
checks:
  - id: review-001
    title: Confirm orchestrator summary matches producer telemetry
    severity: error
    steps:
      - Open orchestrator summary.md and note index_status/index_rule_count.
      - Open standards_index/telemetry.json and compare status/rule_count/integrity_hash.
  - id: review-002
    title: Interpret prompt seed counts correctly
    severity: warn
    steps:
      - Treat prompt seed total_rules as "unique rules" unless explicitly stated otherwise.
      - If category rule counts sum != total_rules, check for duplicates across categories.
  - id: review-003
    title: Use gaps to propose next seed rules
    severity: warn
    steps:
      - Open standards_index_gaps/summary.md.
      - Pick top 3 sources and convert 3-5 high-value candidate lines into new seed rules.
outputs:
  - docs/automation/reviews/standards_integrity_output_review-YYYY-MM-DD.md
```
<!-- agents:end:standards_integrity_review -->

## Human Notes

### Data lineage (inputs -> outputs -> audiences)

This pipeline is a multi-hop chain. The same underlying facts should be visible in:

- **Structured form** (index rules in YAML)
- **Audit form** (producer bundles with manifest/telemetry)
- **Agent-optimized form** (prompt seeds + overview summaries)

**Primary lineage**

| Step | Script | Inputs | Outputs | Primary audience |
| --- | --- | --- | --- | --- |
| Seed taxonomy | `.repo_studios/scripts/.repo_studios/standards_categories.yaml` | Curated category IDs + titles + source file list | Category taxonomy + scan targets | Humans + automation |
| Seed rules | `.repo_studios/scripts/.repo_studios/standards_seed.yaml` | Curated rule set (id, summary, rationale, severity, applies_to, source) | Structured rules to merge into index | Humans + automation |
| Build index | `.repo_studios/scripts/producers/generate_standards_index.py` | categories + seed (+ optional extraction module) | `.repo_studios/scripts/repo_standards_index.yaml` and producer bundle (`manifest.json`, `summary.md`, `telemetry.json`) | Humans + orchestrators + downstream producers |
| Find gaps | `.repo_studios/command_center/scripts/producers/analyze_standards_index_gaps.py` | index + categories (or index sources fallback) | gap producer bundle (top sources + per-line candidates) | Humans + agents (backlog generation) |
| Seed prompts | `.repo_studios/scripts/producers/seed_standards_prompts.py` | index + include_warn flag | prompt seed bundle (`seed.*`) and summary/manifest | Agents (fast ingestion) |
| Summarize | `.repo_studios/scripts/summarizers/summarize_standards.py` | index + pending extraction file | summarizer bundle (`manifest.json`, `summary.md`, `telemetry.json`) | Humans + Healthview dashboards |
| Orchestrate | `.repo_studios/command_center/scripts/orchestrators/run_standards_integrity.py` | repo-root + output roots + diff baseline (optional) | orchestrator bundle linking upstream bundles | Humans + agents (one entry point) |

**Important concept: consumers vs. audiences**

- The **index YAML** is the canonical machine-consumable rule source.
- The **producer bundles** are the canonical audit trail (who/when/what inputs + run slug).
- The **prompt seed** is an intentionally filtered digest (default excludes warn/info).
- The **overview** is a lightweight dashboard feed, not a full index.

### Script-by-script findings (where data comes from, where it goes)

#### `generate_standards_index.py` (index builder)

**Source of truth inputs**

- Categories + sources list come from `.repo_studios/scripts/.repo_studios/standards_categories.yaml`.
- Seed rules come from `.repo_studios/scripts/.repo_studios/standards_seed.yaml`.
- Optional extraction is gated by environment flags (`ENABLE_STANDARDS_EXTRACTION`, `AUTO_ACCEPT_EXTRACTED`) and a module path.

**Outputs**

- Writes canonical index: `.repo_studios/scripts/repo_standards_index.yaml`.
- Writes producer bundle under `.repo_studios/reports/healthview/producer_reports/standards_index/<run_slug>/`.

**Downstream consumers**

- Orchestrator reads the producer `telemetry.json` (but see mismatch below).
- Gaps, prompt seeding, and summarizer read the index YAML.

**Discovery: schema mismatch vs orchestrator expectations**

- Index producer `telemetry.json` has the shape `{metrics: {...}, payload: {...}}`.
- Orchestrator currently treats the entire telemetry object as if it were the producer payload (expects `status`, `summary`, `integrity_hash` at the top-level).
- Result: `index_status` and `index_rule_count` render as `unknown`, and orchestrator index step payload fields are null.

**Opportunity**

- Define and enforce a standard: when an orchestrator reads a producer telemetry file, it must explicitly unwrap either `telemetry.metrics` (fast summary) or `telemetry.payload` (full payload) and never assume producer payload is top-level.
- Normalize path separators in emitted YAML/JSON:
  - The current index YAML stores `sources[].path` using Windows separators (`.repo_studios\docs\...`).
  - Prefer emitting forward slashes (`.repo_studios/docs/...`) so downstream parsing, linking, and cross-platform diffs remain stable.

#### `analyze_standards_index_gaps.py` (gap detector)

**Inputs**

- Reads index YAML (default `.repo_studios/scripts/repo_standards_index.yaml`).
- Reads categories YAML to find scan sources; if missing, falls back to `index.sources`.

**Core behavior**

- Finds candidate directive lines with an imperative-verb heuristic (bullets + numbered lists supported).
- Uses a token-overlap filter against existing rule IDs and rule summaries:
  - If more than ~60% of extracted words already appear in the index token set, the line is suppressed.

**Outputs**

- Emits structured artifacts: `manifest.json`, `summary.md`, `telemetry.json`.
- Telemetry includes:
  - `metrics`: totals (total_candidates, sources_with_candidates, scanned_sources)
  - `sources`: the per-file candidate payload (line + text)
  - `top_sources`: a ranked list for quick prioritization

**Audience fit**

- This is primarily a backlog generator for humans/agents. It is not a validator (it does not assert compliance).

**Opportunities**

- Consider emitting a machine-usable normalized form (example: `candidates.tsv` or `candidates.jsonl`) for programmatic triage.
- Consider capturing "why suppressed" stats (overlap ratio, token counts) for tuning the heuristic.

#### `seed_standards_prompts.py` (prompt digest)

**Inputs**

- Reads index YAML and filters rules by severity:
  - always include `critical` and `error`
  - include `warn` only when `--include-warn` is set

**Outputs**

- Emits prompt seed bundle:
  - `seed.txt` / `seed.yaml` / `seed.json`
  - plus `manifest.json`, `summary.md`, `telemetry.json`

**Discovery: duplicate assignment vs unique rules**

- A single rule can belong to multiple categories (`category_ids`).
- The prompt seed groups by category, so one rule ID may appear multiple times across categories.
- The current `total_rules` count is computed as a deduped set keyed by `(id, summary)`.

**Opportunity**

- Standardize naming: report both `unique_rule_count` and `assignment_count`.
- Consider dedupe keyed only by `id` (treat summary changes as edits, not new entities).

#### `summarize_standards.py` (Healthview summary)

**Inputs**

- Reads index YAML (or legacy fallback) and pending extraction file.

**Discovery: "Markdown rules" metric is currently an ID-prefix heuristic**

- The summarizer counts markdown rules by rule IDs starting with `markdown-`.
- Our seeded markdown rule IDs are `md-*`, so `markdown_rule_count` reports 0.

**Opportunity**

- Prefer category-based counting: a markdown rule is any rule where `category_ids` includes `markdown`.
- Alternatively, enforce a standards rule naming convention such as `<category>-<slug>` for IDs.

#### `diff_standards_index.py` (optional diff)

**Inputs**

- Takes two index YAML paths (old + new).
- Applies a fail policy (`--fail-on`) to decide whether to exit non-zero.

**Outputs**

- Emits a diff producer bundle with:
  - change classifications (added/removed/severity_changed/etc)
  - summary counts
  - integrity hash comparisons

**Audience fit**

- Primarily for humans + CI policy enforcement.

### Additional standards to enforce via this methodology (candidates)

These are process-level and schema-level standards that emerge from the lineage review:

- **STD-SCHEMA-01 (Telemetry unwrapping):** Orchestrators must treat producer `telemetry.json` as `{metrics, payload}` and explicitly unwrap before summarizing.
- **STD-IDENT-01 (Rule ID stability):** Rule IDs must be stable identifiers; summary changes must not create new logical rules.
- **STD-NAMING-01 (Rule ID convention):** Adopt a convention to align with summarizers (either enforce `<category>-` prefixes or require category-based counting everywhere).
- **STD-PATH-01 (Path normalization):** All emitted file paths in YAML/JSON should use forward slashes (`/`) for cross-platform consumption.
- **STD-METRICS-01 (Unique vs assignments):** Whenever rules are grouped into multiple buckets, reports must publish both `unique_rule_count` and `assignment_count`.

### Who uses what (audience contract)

This clarifies what each artifact is designed for, and what “quality” means for that consumer.

| Artifact | Primary consumer | What it should optimize for | What it must never break |
| --- | --- | --- | --- |
| `.repo_studios/scripts/repo_standards_index.yaml` | Automation + producers | Deterministic structure, stable identifiers, cross-platform paths | Schema stability, parseability, missing required fields |
| `producer_reports/standards_index/*/telemetry.json` | Orchestrators + dashboards | Small, consistent metrics envelope | Telemetry envelope (`metrics`, `payload`) consistency |
| `producer_reports/standards_index_gaps/*/telemetry.json` | Agents + humans | Actionability (source -> line -> text) | Losing source-line provenance |
| `producer_reports/standards_prompt_seeds/*/seed.*` | Agents | High-signal condensed rules | Misleading counts (unique vs assignments), missing severity context |
| `summarizer_reports/standards_overview/*/summary.md` | Humans + dashboards | Quick, correct counts, links to deeper sources | Ambiguous metrics and misleading category counts |
| `orchestrator_reports/standards_integrity/*/summary.md` | Humans + agents | Single-entry navigation + rollup metrics | Broken traceability to upstream runs |

### What’s working well

- Traceability is present: orchestrator manifest points to upstream bundles for index, gaps, and prompt seed runs.
- Gaps report is immediately actionable: it lists file paths, line numbers, and sample candidate directives.
- Prompt seed producer emits multiple formats (`seed.txt`, `seed.yaml`, `seed.json`) and includes an integrity hash.

### Main issues (quality + ergonomics)

- Orchestrator summary has missing index metrics:
  - `index_status` and `index_rule_count` are `unknown` in orchestrator `summary.md`.
  - Orchestrator telemetry has an `index` step payload but all fields are null.
  - The index producer telemetry contains these values (status=ok, rule_count=11, integrity_hash present).
- Prompt seed reporting is confusing without a “unique vs assignments” distinction:
  - The prompt seed output assigns the same rule id to multiple categories (example: `pipeline-doc-no-placeholders` appears under both `markdown` and `project`).
  - `Total Rules` is reported as 4, while per-category rule counts sum to 5. This is consistent if `Total Rules` means unique rule IDs, but the report doesn’t say so.
- Standards overview summarizer metrics are ambiguous:
  - It reports `Markdown rules: 0` even though prompt seeds show markdown rules exist.
  - This may be an actual counting bug, or a naming mismatch (for example “markdown rules” meaning “extracted from markdown docs”). Either way, the field label is not self-explanatory.

### Post-implementation validation (runs `20260121-0202`, `20260121-1132`, `20260121-1138`)

The following checks confirm the P0/P1 changes are reflected in real run artifacts.

- Orchestrator summary now reports index metrics (no `unknown`):
  - `index_status: ok`
  - `index_rule_count: 11`
  - `index_integrity_hash` present
- Prompt seed report now distinguishes unique rules vs assignments:
  - `Unique Rules: 4`
  - `Assignment Count: 5`
- Standards overview now counts markdown rules (no longer 0):
  - `Markdown rules: 10`

Additional confirmations from later runs:

- Orchestrator rollup now surfaces prompt counts as both unique rules and assignments:
  - `prompt_unique_rule_count: 4`
  - `prompt_assignment_count: 5`
- Prompt seed producer `telemetry.json` is now valid JSON (envelope with `metrics` + `payload`).

Remaining minor gaps observed in the same run:

- Standards overview still reports `Extracted count: 0` and `Pending lines: unknown` when the pending
  extraction file is missing/unreadable.

### Recommendations (concrete follow-ups)

1) Propagate index producer telemetry into orchestrator telemetry + summary

- Target: `.repo_studios/command_center/scripts/orchestrators/run_standards_integrity.py`
- After the index step, load `.repo_studios/reports/healthview/producer_reports/standards_index/<run_slug>/telemetry.json` and populate:
  - orchestrator `summary.md`: `index_status`, `index_rule_count`, and (optionally) `index_integrity_hash`
  - orchestrator `telemetry.json`: `steps[].payload` for the `index` step

1) Add “Key Links” to orchestrator `summary.md`

- Target: `.repo_studios/command_center/scripts/orchestrators/run_standards_integrity.py`
- Keep HOP invariants (base artifacts only), but make the summary self-serve for humans/agents:
  - link to index/gap/prompt/summarizer bundle dirs
  - link to each bundle’s `summary.md` and `telemetry.json`

1) Clarify prompt seed counting semantics

- Target: `.repo_studios/scripts/producers/seed_standards_prompts.py`
- Report both:
  - `unique_rule_count` (deduped by rule id)
  - `assignment_count` (sum of per-category assignments)
- Rename `Total Rules` accordingly in `summary.md` and `manifest.json`.

1) Fix or rename summarizer “Markdown rules” metric

- Target: `.repo_studios/scripts/summarizers/summarize_standards.py`
- Either:
  - compute markdown rule count by `category_id == "markdown"` in the index, or
  - rename the metric to clarify what it counts (example: `extracted_markdown_rule_count`).

### Implementation backlog (ranked, with concrete code targets)

This turns the findings into a small, ordered change list.

**P0 (fix correctness / remove “unknown”)**

- Orchestrator index unwrapping:
  - File: `.repo_studios/command_center/scripts/orchestrators/run_standards_integrity.py`
  - Where: `_execute_index()` and `_summarize_markdown()`
  - Change: treat index telemetry as an envelope and set `IndexOutcome.payload` to the producer payload:
    - load `telemetry.json`
    - set `payload = telemetry.get("payload")` (dict) and optionally keep `metrics = telemetry.get("metrics")`
    - ensure `index_status` reads from `payload["status"]` and `index_rule_count` from `payload["summary"]["rule_count"]`

**P1 (remove misleading metrics)**

- Summarizer markdown rule counting:
  - File: `.repo_studios/scripts/summarizers/summarize_standards.py`
  - Where: `_extract_markdown_rules()`
  - Change: count markdown rules by `category_ids` membership, not ID prefix.
  - Alternative: enforce ID convention and rename current metric to match what it measures.

**P1 (clarify prompt seed counts)**

- Prompt seed unique vs assignment reporting:
  - File: `.repo_studios/scripts/producers/seed_standards_prompts.py`
  - Where: `summarize_seed()` + `render_markdown_report()` + `render_log()`
  - Change:
    - compute `assignment_count = sum(category.rule_count)`
    - compute `unique_rule_count` using rule id only
    - report both counts and rename the displayed label from “Total Rules”.

**P2 (cross-platform stability)**

- Path normalization:
  - Files: `.repo_studios/scripts/producers/generate_standards_index.py` and any producer that writes paths into YAML/JSON.
  - Change: write repo-relative paths using `.as_posix()` so outputs are stable on Windows/Linux.

**P2 (agentic ergonomics)**

- Gap report additional machine output:
  - File: `.repo_studios/command_center/scripts/producers/analyze_standards_index_gaps.py`
  - Change: persist `render_tsv(report)` (or JSONL) as an extra artifact inside the run bundle for programmatic triage.

### How to use these artifacts agentically (today)

- Use the standards index as the canonical structured rules source:
  - `.repo_studios/scripts/repo_standards_index.yaml`
- Use gaps as the “backlog generator” for new structured rules:
  - start with the highest-count sources in the gaps summary
- Use prompt seeds as an LLM-friendly digest of high-severity rules:
  - treat `include_warn=false` as “only error/critical rules” unless configured otherwise

## Reference Prompts

- Run the pipeline:
  - `make studio-orchestrate-standards`
- Inspect the latest run:
  - Open the orchestrator bundle’s `summary.md`, then follow `manifest.json` links.

## Update Log

- 2026-01-21 — Initial review based on run `20260121-0026`.
- 2026-01-21 — Validated fixes against run `20260121-0202` (index telemetry unwrapped; markdown rule
  counting corrected; prompt seed unique vs assignment counts clarified).
- 2026-01-21 — Validated orchestrator prompt rollups against run `20260121-1132`.
- 2026-01-21 — Validated prompt seed telemetry.json JSON envelope against run `20260121-1138`.
