---
title: repo Standards — Markdown Authoring for AI, Agent, and Human Integration
audience: [repo, Jarvis2, Developer]
role: [Standards, Operational-Doc]
owners: ["@docs-owners"]
status: approved
version: 1.1.0
updated_at: 2025-08-22
tags: [markdown, standards, ai-ingestion, agents]
related_files:
  - ./repo_standards_project.md
  - ../README.md
---

## 📘 repo Standards — Markdown Authoring for AI, Agent, and Human Integration

Audience: repo | Jarvis2 | Developer | All

This document outlines standardized Markdown authoring conventions for all `.md`
files created or modified by GitHub repo. These files serve as:

* Developer notes for humans
* Instructional overlays for repo and LLM tools
* Structured interfaces for AI agents (for example, Jarvis2)
* Modular, ingestible documents for orchestration, context loading,
  and persistent memory

All Markdown files must be treated as first-class operational components —
not just documentation.

## 🎯 Purpose of Markdown Files

Every `.md` file must support one or more of the following roles:

| Role                  | Description                                      |
| --------------------- | ------------------------------------------------ |
| ✅ repo Notes       | Instruct repo on how to behave, write, clean, |
|                       | or test code                                     |
| ✅ Human-Readable      | Document file or folder purposes, developer      |
|                       | intentions, and architectural patterns           |
| ✅ Agent Integration   | Provide structured guidance for Jarvis2 or       |
|                       | autonomous agents to understand project logic    |
| ✅ Agent Orchestration | Enable agents to trigger workflows, extract task |
|                       | definitions, or link files semantically          |
| ✅ AI Ingestion        | Format data in a way that is easily parseable,   |
|                       | searchable, and structured for LLMs              |

## ✅ Markdown Structure Guidelines

* Use top-level headings (`#`) to name the file purpose.
* Use second-level headings (`##`) for section groups (for example, `## Goals`,
  `## File Summary`, `## Agent Tasks`).
* Use third-level headings (`###`) only when subdividing known sections.
* Use bullet points or tables for enumerated items.
* Never overload a single section with too many nested points — prefer separation.
* Use fenced code blocks with language markers (for example, md, python, json,
  bash) when instructing agents or repo directly.

## 🔍 Required Sections (when relevant)

Every AI-integrated `.md` file must include at least two of the following:

* `## Goals` — Purpose of the file, logic, or module
* `## Agent Instructions` — What Jarvis2 or repo should do with the content
* `## Human Notes` — Developer explanation or inline commentary
* `## System Context` — Where the file lives in the architecture
* `## Update Log` — Timestamped notes or changes made
* `## Reference Prompts` — Instructive examples for future AI use

## 🧠 AI Ingestibility Requirements

* Avoid ambiguous section headers like "Stuff", "Etc", or "Misc".
* Always clarify meaning with context: for example.
  `## Agent Instructions: Clean this file`, not just `## Instructions`.
* Make it clear who the audience is: repo, Jarvis2, Developer, or All.
* Prefer explicit formatting over implied meaning — avoid AI confusion.
* Ensure code examples are wrapped in triple backticks with proper language markers.

## 📚 Best Practices

* Use consistent Markdown heading hierarchy.
* Include timestamps in logs or examples.
* Use task lists (`* [ ]`) when describing multi-step behaviors for agents.
* Avoid raw HTML inside `.md` unless unavoidable.
* Reference relative file paths or folders when giving context (for example, `./backend/handler.py`).
* Prefer AI-first unique headings in plan/phase documents: apply domain + purpose prefixes
  (e.g., "AI UI Phased Plan") to reduce duplicate anchor clusters.
  Preserve a single generic template (`docs/agents/step_template.md`) as canonical source of
  un-prefixed headings.

## 🔁 Self-Updating Instructions

* repo must scan Markdown files it creates on re-entry into a folder.
* If a file is missing key sections or clarity, repo must correct it.
* Jarvis2 and agents should use these files as primary sources of operational
  guidance and workflow visibility.
* repo should never delete `.md` files unless explicitly instructed.

## 🚫 Anti-Patterns to Avoid

* Vague notes like “to do later” without action steps.
* Markdown files with no context or headers.
* Empty sections with just headings.
* Inconsistent spacing, indentation, or formatting.
* Mixed intentions (for example, documentation + chat logs + code dump in one file).

## 📑 Metadata (YAML front matter)

Add a YAML front matter block at the top of AI-operational Markdown files to
standardize parsing by agents and CI.

Required keys (baseline): `title`, `audience`, `status`, `version`, `updated_at`.

Required keys for memory indexing (memory-ready): `tags`, `related_files`, `role`.

Optional: `owners` (preferred), any additional fields useful for retrieval.

```yaml
---
title: <file title>
audience: [repo, Jarvis2, Developer]
role: [Standards, Operational-Doc]
owners: ["@owner"]
status: approved
version: 1.0.0
updated_at: 2025-08-22
tags: [markdown, standards]
related_files:
  - ../README.md
---
```

### Memory-ready template (use for RAG-targeted docs)

```yaml
---
title: <concise title>
audience: [repo, Jarvis2, Developer]
role: [Operational-Doc, Memory-Source]
owners: ["@owner"]
status: approved
version: 1.0.0
updated_at: 2025-08-27
tags: [agents, memory, api]  # specific, retrieval-friendly
related_files:
  - mrp/training_docs/<related>.md
  - mrp/vector_db/index.json
---
```

## 📐 Canonical Section Order

For AI-focused docs, prefer this order for predictability:

1. H1 Title
2. Goals
3. System Context
4. Agent Instructions
5. Human Notes
6. Reference Prompts
7. Update Log

## 🤖 Agent Block (machine-readable)

Delimit an agent-consumable block and include actionable tasks.
Keep it YAML for easy parsing.

````md
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

This section enumerates enforceable Markdown lint and structural rules. Each discrete
rule is encoded as a machine‑extraction marker block so automated standards
harvesting (via `ENABLE_STANDARDS_EXTRACTION=1`) can propose or merge them.

### Summary (Human Overview)

Ordered focus (top = most structurally critical):
1. Heading structure & first heading (MD001 / MD002 / MD025 / MD041)
2. Empty / duplicate heading prevention (MD042 / MD043)
3. Required spacing & blank line hygiene (MD022 / MD032 / MD004)
4. Code fence quality (MD040) and trailing whitespace (MD008)
5. Accessibility & link clarity (MD034) and language tags (MD040)
6. Formatting consistency (MD010 tabs, MD013 line length, MD047 final newline)
7. Section completeness (MD058 – no empty content shells)

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

### Conventions (Non‑Rule Guidance)

* Keep lines near 100 chars (do not hard‑wrap mid‑sentence if it harms readability).
* Prefer consistent table alignment (one space padding around pipes) for stable diffs.
* Use comment markers for automation instead of raw HTML blocks when possible.
* Treat lint violations as governance debt; stage fixes incrementally in focused commits.

> The above marker blocks will be ignored when extraction is disabled and skipped
> for any rule ids already present in the seed index.

## 🧭 File naming and cross-references

* Use lowercase, kebab-case names (for example, `metrics-ui-standards.md`).

* One canonical `README.md` per folder; link to specialized docs.

* Use relative links and stable anchors.

* Anchor Uniqueness Governance (2025-09-28): Second-wave heading normalization introduced
  AI-prefixed headings (for example, `AI Domain Concept`) across step plan docs. New plan
  docs must follow this pattern to prevent reintroduction of duplicate slug clusters
  detected by `tests/docs/test_global_anchors.py`.

### Anchor Health Governance (automated)

Anchor slug duplication is now continuously monitored and reported. The automation writes
timestamped artifacts and a rolling latest pointer that both humans and agents can
consume to decide when to rename headings or ratchet the baseline.

Artifacts (per run via `make anchor-health`):

* JSON report:
  `.repo_studios/anchor_health/anchor_health-<ts>/anchor_report.json` — metrics & clusters.
* Markdown summary:
  `.repo_studios/anchor_health/anchor_health-<ts>/anchor_report.md` — cluster overview.
* Clusters TSV:
  `.repo_studios/anchor_health/anchor_health-<ts>/clusters.tsv` — slug/count/files list.
* Latest summary pointer:
  `.repo_studios/anchor_health/anchor_report_latest.json` — stable pointer for automation.
* Runs log:
  `.repo_studios/anchor_health/runs.log` — run history (timestamp, counts, delta).

Key fields (JSON):

`strict_duplicate_count`, `baseline_cross_file_duplicates`,
`delta_vs_baseline`, `clusters[]` (each cluster includes `slug`, `file_count`, `files`).

Enforcement:

* Test: `tests/docs/test_global_anchors.py` fails when disallowed duplicates persist
  or when strict duplicates exceed baseline (`tests/docs/anchor_slug_baseline.json`).

* Ratchet: After sustained reduction (strict << baseline) update the baseline file in
  the same commit as heading renames.

* Non-allowed duplicates must be eliminated before ratcheting; partial cluster edits
  do not reduce the cluster until all but one canonical heading remains.

Workflow:

1. Run `make anchor-health` (optionally set `FAIL_ON_DUPES=1` / `RUN_ANCHOR_TEST=1`).

2. Inspect `anchor_report_latest.json` or the most recent timestamped directory.

3. Choose a canonical file per duplicate cluster; rename headings in all others
  (prefer AI-prefixed contextual headings).

4. Re-run the target until `strict_duplicate_count <= baseline_cross_file_duplicates`
  and no non-allowed duplicates remain.

5. When stable, lower `cross_file_duplicates` in `anchor_slug_baseline.json` (single PR
  with supporting renames + test pass).

Authoring Rules (additions):

* Prefer disambiguating prefixes early; do not wait for collisions to appear in the
  report.

* When creating a new phased/plan doc, scan the latest report to avoid resurrecting retired generic headings (purpose, scope, troubleshooting, future-work, changelog, etc.).

* Do not increase the allowlist unless governance explicitly approves; favor renaming instead.

Agent Guidance:

* Agents generating or modifying docs must read `anchor_report_latest.json` if present; if a touched heading appears in a multi-file cluster, proactively rename unless it is the canonical file.

* During multi-file refactors, run the anchor health target before finalizing to avoid introducing new collisions.

Quality Gate Integration:

* The health suite orchestrator ingests `anchor_report_latest.json` and surfaces metrics (strict duplicates, delta vs baseline, top clusters) in the consolidated health summary.

* CI can enforce failure on regression by exporting `FAIL_ON_DUPES=1 make anchor-health`.

Future Enhancements (planned):

* Prometheus-style counters (`doc_anchor_duplicates`) for trend dashboards.

* Auto-suggest canonical candidate based on earliest commit or size heuristics.

* Optional PR comment bot summarizing new/removed clusters.

By embedding automated anchor health, documentation remains navigable, retrievable, and low-friction for AI ingestion.

## ♿ Accessibility & Inclusive Authoring

Accessibility is a first-class requirement for any Markdown consumed by humans or transformed into UI components.

### Accessibility Checklist

* Provide descriptive link text (avoid “here”, “this”).
* Use meaningful table headers; never rely on color alone to convey meaning.
* Prefer sentence case for readability; keep heading capitalization consistent.
* Use lists for procedural steps; avoid burying steps in paragraphs.
* Avoid ASCII art that impairs screen reader flow.
* Provide alt context when embedding images (see Image Guidance). If an image is purely decorative, omit or mark with empty alt.

### Image Guidance

* Use relative paths: `![Architecture Overview](../diagrams/arch_overview.png)`.
* Keep file names lowercase, hyphenated, semantic: `agent-state-flow.png`.
* Prefer SVG for diagrams (text remains selectable and searchable) unless raster-only.
* Include an accompanying textual summary under a heading: `#### Diagram Summary` for complex diagrams to aid RAG ingestion.

## 🧾 Tables & Structured Data

Tables should be used for compact, relational data. For procedural or stepwise instructions, prefer ordered lists.

Table Rules:
* Always include a header row.
* Align delimiter pipes with a single space padding for diff stability.
* Keep cells concise; move verbose explanations below the table in a `Notes` subsection.
* Avoid embedding large code blocks inside tables—link or reference instead.

Example:

| Field          | Required | Notes                               |
| -------------- | -------- | ----------------------------------- |
| `title`        | Yes      | YAML front matter; human friendly   |
| `updated_at`   | Yes      | ISO8601 UTC                         |
| `related_files`| Conditional | Only if cross-linking dependencies |

## 💬 Admonitions & Callouts

While raw GitHub Markdown lacks native admonitions, we standardize a comment + heading pattern to enable future transformation.

Pattern:
````md
<!-- admonition:warning title="Deprecation Pending" -->
**Deprecation Notice:** This section will be superseded by `markdown-extended-layout`.
<!-- /admonition -->
````

Rules:
* Supported kinds: `note`, `tip`, `warning`, `important`.
* Title attribute optional; defaults to capitalized kind.
* Never nest admonitions.

Extraction Hint: Tools may treat these as structured blocks keyed by kind for enrichment.

## 🧪 Code Block Conventions

| Aspect        | Rule                                                      |
| ------------- | --------------------------------------------------------- |
| Language Tag  | Always specify (python, bash, json, md, yaml, text)       |
| Line Length   | Keep sample lines <= 100 chars where possible             |
| Sensitive Data| Redact tokens (`sk-***`) and credentials                  |
| Prompts       | Use `md` or `text` fence; avoid triple nesting            |
| Diff Examples | Use `diff` fence only for illustrative unified diffs      |

Inline Guidance:
```python
def example(value: str) -> str:
  """Return processed value.

  NOTE: Example kept intentionally small for docs; real implementation may validate input.
  """
  return value.strip()
```

## 🔗 Link Policy

* Prefer relative links within repository.
* External links must use descriptive anchor text and (optionally) a trailing reference tag if cited repeatedly.
* Avoid bare URLs; wrap with `[Descriptive Text](https://example.com)`.
* Dead link prevention: run link validation target (`make docs-link-check`) pre-commit when touching many docs.

## 🗃️ Deprecation Annotations (Planned Schema v1.1)

Upcoming fields to support lifecycle management:

Deprecation Fields:

* `status`: lifecycle state (`active`, `deprecated`, `superseded`). Example: `deprecated`.
* `replaced_by`: successor rule id or doc anchor. Example: `markdown-structure-v2`.
* `sunset_at`: planned removal date (ISO8601 UTC). Example: `2025-12-31`.

Authoring Interim:
* Use an admonition callout when marking future deprecations until schema update lands.
* Avoid removing deprecated guidance before migration instructions exist.

## 🛠 Extraction Anchors (Machine Markers)

Extraction tooling may rely on comment delimiters. When introducing new structured sections, optionally wrap them:

````md
<!-- standards:begin:markdown:accessibility -->
## ♿ Accessibility & Inclusive Authoring
...section content...
<!-- standards:end:markdown:accessibility -->
````

Rules:
* Use `standards:begin:<category>:<slug>` and matching `end` marker.
* Slug must be lowercase kebab-case.
* Avoid overlapping or nested begin/end markers.

Existing content can be retrofitted incrementally—do not churn entire file solely to add markers.

## 📈 Expansion Roadmap (Markdown Standards)

1. Add automated extraction of admonition blocks into structured rule candidates.
2. Integrate accessibility lint (alt text, heading clarity) into standards gap report.
3. Enrich rule seed with `status` + lifecycle metadata (deprecation pipeline).
4. Surface per-category coverage ratios in metrics exposition.
5. Introduce doc complexity scoring (sections, words, code block balance) for governance dashboards.

## 🧾 Change Log (Local to This File)

* 2025-09-28: Added accessibility, tables, admonitions, code, link, deprecation, extraction anchors, roadmap sections.
* 2025-08-22: Initial version 1.1.0.

### Heading Naming Priority Weights

Weighting applied when choosing headings (optimize in this order):

1. AI (60%): Disambiguation, retrieval clarity, low collision probability.
2. Author (30%): Human scan readability and concise intent signaling.
3. Dev Team (10%): Internal convention alignment and historical continuity.

Pattern: `AI <Domain> <Primary Concept> <Optional Qualifier>` (<= 65 chars).
Examples:
`AI Data Collection Phased Plan`,
`AI Framework Acceptance Criteria`,
`AI Model Onboarding Session Results`.

## 🧩 Memory-ready docs checklist

Use this checklist for any doc intended for retrieval (RAG):

* [ ] YAML front matter includes required memory fields: `tags`, `updated_at`, `related_files`, `role`
* [ ] `tags` are specific (e.g., `agents`, `ui`, `api`, `standards`) and minimal
* [ ] `updated_at` reflects last substantive change (UTC ISO8601 preferred)
* [ ] `related_files` points to source paths and key indices (e.g., `mrp/training_docs/*`, `mrp/vector_db/index.json`)
* [ ] Headings and sections are clear and stable; avoid ambiguous labels
* [ ] Citations or file paths included where applicable to aid provenance
* [ ] Large code or data blocks are scoped and labeled with language fences
* [ ] Optional agent block is delimited with `<!-- agents:begin:... -->` markers if tasks are present

## 🔒 Security and compliance

* Do not include secrets or PII. Redact examples (for example, `sk-***`).
* Sanitize tokens/URLs; mark examples as sample-only.

## 🧩 Template Skeleton

````md
## <Title: concise and specific>

Audience: repo | Jarvis2 | Developer | All

## Goals
 
* What this file enables (for humans and agents)

## System Context
 
* Where it lives (paths, modules)
* Dependencies or consumers

## Agent Instructions
 
* [ ] [TASK:<id>] Actionable steps for agents
<!-- agents:begin:agent_instructions -->
```yaml
agents:
  tasks:
    - id: <id>
      title: <task>
      steps: [<step1>, <step2>]
```
<!-- agents:end:agent_instructions -->

## Human Notes
 
* Rationale, caveats, trade-offs

## Reference Prompts
```md
You are maintaining the docs...
```

## Update Log
 
* 2025-08-22: Init (owner: @owner)
````

By following this Markdown standard, repo and AI agents will produce files
that are:

* Human readable
* Machine parseable
* Agent-operable
* Architecturally meaningful

These `.md` files are not documentation. They are living protocols for the
intelligence layer of the codebase.
