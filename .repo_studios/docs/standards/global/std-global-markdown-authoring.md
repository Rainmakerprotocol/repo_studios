---
title: Markdown Authoring for AI, Agent, and Human Integration
audience:
  - coding_agent
  - human_developer
owners:
  - repo_studios_team@rainmakerprotocol.dev
status: approved
version: 1.1.0
updated: 2025-08-22
summary: >-
  Standardized Markdown authoring conventions to support Repo Studios automation, human comprehension, and agent ingestion.
tags:
  - markdown
  - standards
  - ai-ingestion
legacy_source: .repo_studios_legacy/repo_docs/copilot_standards_markdown.md
---

## 📘 Repo Studios Standards — Markdown Authoring for AI, Agent, and Human Integration

Audience: Repo Studios | Agents | Developers | All

This document outlines standardized Markdown authoring conventions for all `.md` files created or modified within Repo Studios workspaces. These files serve as:

- Developer notes for humans.
- Instructional overlays for scripting agents and LLM tools.
- Structured interfaces for autonomous agents to understand project logic.
- Modular, ingestible documents for orchestration, context loading, and persistent memory.

All Markdown files must be treated as first-class operational components — not just documentation.

## 🎯 Purpose of Markdown Files

Every `.md` file must support one or more of the following roles:

| Role | Description |
| --- | --- |
| ✅ Repo Notes | Instruct Repo Studios agents on how to behave, write, clean, or test code |
| ✅ Human-Readable | Document file or folder purposes, developer intentions, and architectural patterns |
| ✅ Agent Integration | Provide structured guidance so automation understands project logic |
| ✅ Agent Orchestration | Enable agents to trigger workflows, extract task definitions, or link files semantically |
| ✅ AI Ingestion | Format data in a way that is easily parseable, searchable, and structured for LLMs |

## ✅ Markdown Structure Guidelines

- Use top-level headings (`#`) to name the file purpose.
- Use second-level headings (`##`) for section groups (for example, `## Goals`, `## File Summary`, `## Agent Tasks`).
- Use third-level headings (`###`) only when subdividing known sections.
- Use bullet points or tables for enumerated items.
- Avoid overloading a single section with too many nested points — prefer separation.
- Use fenced code blocks with language markers (for example, md, python, json, bash) when instructing agents.

## 🔍 Required Sections (when relevant)

Every AI-integrated `.md` file must include at least two of the following:

- `## Goals` — Purpose of the file, logic, or module.
- `## Agent Instructions` — What the automation should do with the content.
- `## Human Notes` — Developer explanation or inline commentary.
- `## System Context` — Where the file lives in the architecture.
- `## Update Log` — Timestamped notes or changes made.
- `## Reference Prompts` — Instructive examples for future AI use.

## 🧠 AI Ingestibility Requirements

- Avoid ambiguous section headers like "Stuff", "Etc", or "Misc".
- Always clarify meaning with context: for example, `## Agent Instructions: Clean this file`, not just `## Instructions`.
- Make it clear who the audience is: agents, developers, both, or all.
- Prefer explicit formatting over implied meaning — avoid AI confusion.
- Ensure code examples are wrapped in triple backticks with proper language markers.

## 📚 Best Practices

- Use consistent Markdown heading hierarchy.
- Include timestamps in logs or examples.
- Use task lists (`- [ ]`) when describing multi-step behaviors for agents.
- Avoid raw HTML inside `.md` unless unavoidable.
- Reference relative file paths or folders when giving context (for example, `./backend/handler.py`).
- Prefer unique headings in plan/phase documents: apply domain + purpose prefixes (for example, "AI UI Phased Plan") to reduce duplicate anchor clusters. Preserve a single generic template (`docs/agents/step_template.md`) as canonical source of un-prefixed headings.

## 🔁 Self-Updating Instructions

- Repo Studios agents must scan Markdown files they create on re-entry into a folder.
- If a file is missing key sections or clarity, agents must correct it.
- Treat these files as primary sources of operational guidance and workflow visibility.
- Never delete `.md` files unless explicitly instructed.

## 🚫 Anti-Patterns to Avoid

- Vague notes like “to do later” without action steps.
- Markdown files with no context or headers.
- Empty sections with just headings.
- Inconsistent spacing, indentation, or formatting.
- Mixed intentions (for example, documentation + chat logs + code dump in one file).

## 📑 Metadata (YAML front matter)

Add a YAML front matter block at the top of AI-operational Markdown files to standardize parsing by agents and CI.

Required keys (baseline): `title`, `audience`, `status`, `version`, `updated`.

Required keys for memory indexing (memory-ready): `tags`, `related_files`, `role`.

Optional: `owners` (preferred), any additional fields useful for retrieval.

```yaml
---
title: <file title>
audience: [Repo Studios, Agents, Developer]
role: [Standards, Operational-Doc]
owners: ["@owner"]
status: approved
version: 1.0.0
updated: 2025-08-22
tags: [markdown, standards]
related_files:
  - ../README.md
---
```

### Memory-ready template (use for RAG-targeted docs)

```yaml
---
title: <concise title>
audience: [Repo Studios, Agents, Developer]
role: [Operational-Doc, Memory-Source]
owners: ["@owner"]
status: approved
version: 1.0.0
updated: 2025-08-27
tags: [agents, memory, api]
related_files:
  - mrp/training_docs/<related>.md
  - mrp/vector_db/index.json
---
```

## 📐 Canonical Section Order

For AI-focused docs, prefer this order for predictability:

1. H1 Title.
2. Goals.
3. System Context.
4. Agent Instructions.
5. Human Notes.
6. Reference Prompts.
7. Update Log.

## 🤖 Agent Block (machine-readable)

Delimit an agent-consumable block and include actionable tasks. Keep it YAML for easy parsing.

````markdown
<!-- agents:begin:agent_instructions -->
```yaml
agents:
  section: agent_instructions
  tasks:
    - id: md-001
      title: Ensure required sections exist
      steps:
        - check: ["## Goals", "## Agent Instructions", "## Update Log"]
        - add_if_missing: true
      severity: warn
  rules:
    heading_hierarchy: strict
    code_fences_language_required: true
```
<!-- agents:end:agent_instructions -->
````

## 🧼 Lint and CI Rules

This section enumerates enforceable Markdown lint and structural rules. Each discrete rule is encoded as a machine-extraction marker block so automated standards harvesting (via `ENABLE_STANDARDS_EXTRACTION=1`) can propose or merge them.

### Summary (Human Overview)

Ordered focus (top = most structurally critical):

1. Heading structure & first heading (MD001 / MD002 / MD025 / MD041).
2. Empty / duplicate heading prevention (MD042 / MD043).
3. Required spacing & blank line hygiene (MD022 / MD032 / MD004).
4. Code fence quality (MD040) and trailing whitespace (MD008).
5. Accessibility & link clarity (MD034) and language tags (MD040).
6. Formatting consistency (MD010 tabs, MD013 line length, MD047 final newline).
7. Section completeness (MD058 – no empty content shells).

### Extraction Rule Blocks

<!-- standards:rule
id: markdown-heading-first-h1
categories: markdown
severity: error
applies_to: **/*.md
summary: Documents must begin with a single top-level heading (or YAML front matter then heading)
rationale: A canonical first heading enables stable anchors, navigation, and deterministic indexing.
-->
<!-- /standards:rule -->

<!-- standards:rule
id: markdown-heading-hierarchy
categories: markdown
severity: warn
applies_to: **/*.md
summary: Maintain proper heading level progression without skipping levels
rationale: Predictable hierarchy improves automated TOC generation and agent context slicing.
-->
<!-- /standards:rule -->

<!-- standards:rule
id: markdown-no-empty-headings
categories: markdown
severity: warn
applies_to: **/*.md
summary: Prohibit empty headings without accompanying descriptive content
rationale: Empty headings create noise and degrade retrieval precision.
-->
<!-- /standards:rule -->

<!-- standards:rule
id: markdown-no-duplicate-headings
categories: markdown
severity: warn
applies_to: **/*.md
summary: Avoid duplicate same-level headings within a document
rationale: Duplicate slugs fragment inbound links and reduce anchor uniqueness.
-->
<!-- /standards:rule -->

<!-- standards:rule
id: markdown-blank-line-spacing
categories: markdown
severity: info
applies_to: **/*.md
summary: Surround headings and lists with required blank lines
rationale: Consistent spacing ensures parser stability and diff readability.
-->
<!-- /standards:rule -->

<!-- standards:rule
id: markdown-lists-blank-line-separation
categories: markdown
severity: info
applies_to: **/*.md
summary: Lists must be preceded and followed by a blank line unless at file start/end
rationale: Blank line separation prevents unintended list merging and aids visual scanning.
-->
<!-- /standards:rule -->

<!-- standards:rule
id: markdown-no-consecutive-blank-lines
categories: markdown
severity: info
applies_to: **/*.md
summary: Disallow runs of consecutive blank lines
rationale: Excess vertical whitespace obscures structure and inflates diffs.
-->
<!-- /standards:rule -->

<!-- standards:rule
id: markdown-fenced-code-language
categories: markdown
severity: error
applies_to: **/*.md
summary: All fenced code blocks must declare a language
rationale: Language tags enable syntax highlighting, accurate tokenization, and security scanning.
-->
<!-- /standards:rule -->

<!-- standards:rule
id: markdown-no-inline-html
categories: markdown
severity: warn
applies_to: **/*.md
summary: Avoid raw inline HTML except sanctioned automation comments
rationale: Raw HTML complicates rendering portability and increases parsing variance.
-->
<!-- /standards:rule -->

<!-- standards:rule
id: markdown-no-hard-tabs
categories: markdown
severity: warn
applies_to: **/*.md
summary: Disallow hard tab characters; use spaces for indentation
rationale: Tabs render inconsistently across viewers and break alignment heuristics.
-->
<!-- /standards:rule -->

<!-- standards:rule
id: markdown-no-bare-urls
categories: markdown
severity: warn
applies_to: **/*.md
summary: Replace bare URLs with descriptive link text
rationale: Descriptive anchors improve accessibility and retrieval context scoring.
-->
<!-- /standards:rule -->

<!-- standards:rule
id: markdown-prefer-soft-wrap-100
categories: markdown
severity: info
applies_to: **/*.md
summary: Prefer soft wraps at roughly 100 characters
rationale: Moderate line length optimizes diff clarity without forcing unnatural hard breaks.
-->
<!-- /standards:rule -->

<!-- standards:rule
id: markdown-final-newline
categories: markdown
severity: info
applies_to: **/*.md
summary: Ensure file ends with a single trailing newline
rationale: Final newline prevents concatenation issues and normalizes POSIX tooling behavior.
-->
<!-- /standards:rule -->

<!-- standards:rule
id: markdown-no-trailing-spaces
categories: markdown
severity: info
applies_to: **/*.md
summary: Strip trailing spaces at line ends
rationale: Trailing whitespace causes noisy diffs and accidental semantic changes in some processors.
-->
<!-- /standards:rule -->

<!-- standards:rule
id: markdown-section-not-empty
categories: markdown
severity: warn
applies_to: **/*.md
summary: Sections introduced by a heading must contain substantive content
rationale: Placeholder sections reduce document signal-to-noise and mislead agents about coverage.
-->
<!-- /standards:rule -->

### Conventions (Non-Rule Guidance)

- Keep lines near 100 characters (do not hard-wrap mid-sentence if it harms readability).
- Prefer consistent table alignment (one space padding around pipes) for stable diffs.
- Use comment markers for automation instead of raw HTML blocks when possible.
- Treat lint violations as governance debt; stage fixes incrementally in focused commits.

> The above marker blocks will be ignored when extraction is disabled and skipped for any rule IDs already present in the seed index.

## 🧭 File Naming and Cross-References

- Use lowercase, kebab-case names (for example, `metrics-ui-standards.md`).
- Maintain one canonical `README.md` per folder; link to specialized docs.
- Use relative links and stable anchors.

### Anchor Health Governance (Automated)

Anchor slug duplication is continuously monitored and reported. The automation writes timestamped artifacts and a rolling latest pointer that both humans and agents can consume to decide when to rename headings or tighten the baseline.

Artifacts (per run via `make anchor-health`):

- JSON report: `.repo_studios/anchor_health/anchor_health-<ts>/anchor_report.json` — metrics & clusters.
- Markdown summary: `.repo_studios/anchor_health/anchor_health-<ts>/anchor_report.md` — cluster overview.
- Clusters TSV: `.repo_studios/anchor_health/anchor_health-<ts>/clusters.tsv` — slug/count/files list.
- Latest summary pointer: `.repo_studios/anchor_health/anchor_report_latest.json` — stable pointer for automation.
- Runs log: `.repo_studios/anchor_health/runs.log` — run history (timestamp, counts, delta).

Key fields (JSON): `strict_duplicate_count`, `baseline_cross_file_duplicates`.
