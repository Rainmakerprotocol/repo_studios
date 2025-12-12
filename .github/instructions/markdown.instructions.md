---
description: Primary Markdown instruction set for Repo_Studios contributors and agents
applyTo: '**/*.md'
---
# Markdown Instruction Set — Repo_Studios Repo

Use this document whenever you create or edit Markdown inside the repo. It consolidates the actionable recommendations from the latest doc-index refresh and links you to the deeper standards so every file stays ingestible by humans, Copilot, and autonomous agents.

## Why this file exists
- Protect doc-index stability by keeping headings, links, and front matter predictable.
- Give a single entry point that forwards authors to the specialized standards under `.repo_studios/docs/standards/global/`.
- Attach machine-readable standard labels so CI and autonomous agents can enforce them.

## Authoring workflow (always follow order)
1. **Plan**: Identify the doc audience (Copilot, Agents, Developer) and choose whether the file must be "memory ready." 
2. **Frame**: Start with YAML front matter (title, audience, role, owners, status, version, updated_at, tags, related_files).
3. **Structure**: Apply the canonical section order — H1 title, Goals, System Context, Agent Instructions, Human Notes, Reference Prompts, Update Log.
4. **Link**: Use relative links and explicitly named anchors; avoid bare URLs and newline-contaminated link targets.
5. **Lint**: Run doc-index generator (`python .repo_studios/scripts/producers/generate_doc_index.py --repo-root .`) after meaningful doc work so artifacts stay up to date.
6. **Publish**: Reference this instruction set inside new Markdown files via a short note ("See `.github/instructions/markdown.instructions.md` for repo-wide rules").

## Recommendations snapshot
- Front matter is **not optional** for AI-operational docs. Memory-ready docs must include `tags`, `related_files`, and `role` arrays.
- Keep headings unique repo-wide; prefix plan docs with functional scopes (e.g., `Command Center Plan — ...`).
- Always wrap agent automation data between `<!-- agents:begin -->` / `<!-- agents:end -->` blocks with YAML payloads.
- Limit link targets to <2 KB and strip newline characters before committing.

## Standards by label (human summary)
| Label | Enforced Behavior | Notes |
| --- | --- | --- |
| `MD-L1` | File must begin with YAML front matter followed by a single H1 | Mirrors markdown-heading-first-h1 standard |
| `MD-L2` | Canonical section order + required sections present | Ensures doc-index slices behave predictably |
| `MD-L3` | Links must be descriptive, relative, <2 KB, no newlines | Prevents ingestion crashes and CSV export issues |
| `MD-L4` | Code fences always specify language; agent blocks use YAML | Supports syntax highlighting + automation |
| `MD-L5` | References to other standards must be relative and dated | Keeps navigation within repo and preserves provenance |

## Standards by label (machine readable)
<!-- standards:rule
id: md-l1-frontmatter-h1
label: MD-L1
categories: markdown
severity: error
applies_to: '**/*.md'
summary: Start every AI-operational Markdown file with YAML front matter followed by a single H1
rationale: Stable identity metadata and first heading anchors allow doc-index ingestion and agent routing.
-->
<!-- /standards:rule -->

<!-- standards:rule
id: md-l2-section-order
label: MD-L2
categories: markdown
severity: warn
applies_to: '**/*.md'
summary: Preserve canonical section order and ensure Goals + Agent Instructions + Update Log exist when relevant
rationale: Normalized sections let agents and doc-index CSVs map intent rapidly.
-->
<!-- /standards:rule -->

<!-- standards:rule
id: md-l3-link-hygiene
label: MD-L3
categories: markdown
severity: warn
applies_to: '**/*.md'
summary: Links must be relative, descriptive, newline-free, and shorter than 2048 characters
rationale: Mirrors doc-index guardrails to avoid ingestion crashes from malformed URLs.
-->
<!-- /standards:rule -->

<!-- standards:rule
id: md-l4-code-fence-language
label: MD-L4
categories: markdown
severity: error
applies_to: '**/*.md'
summary: All fenced code blocks and agent instruction blocks must specify their language (usually yaml)
rationale: Syntax-aware highlighting and automation parsing require explicit language tags.
-->
<!-- /standards:rule -->

<!-- standards:rule
id: md-l5-standards-linking
label: MD-L5
categories: markdown
severity: info
applies_to: '**/*.md'
summary: Cross-reference other markdown standards by relative path and include the last reviewed date
rationale: Creates a navigable standards graph and prevents orphaned guidance.
-->
<!-- /standards:rule -->

## Where to go next (linked standards directory)
| Scope | File | Why it matters |
| --- | --- | --- |
| Repo-wide Markdown details | [`.repo_studios/docs/standards/global/std-global-markdown-authoring.md`](../../.repo_studios/docs/standards/global/std-global-markdown-authoring.md) | Deep dive on structure, lint rules, automation blocks |
| Project-wide engineering customs | [`.repo_studios/docs/standards/project/std-project-operating-standard.md`](../../.repo_studios/docs/standards/project/std-project-operating-standard.md) | Shared conventions impacting doc-writing, naming, and lint |
| Python-specific guidance | [`.repo_studios/docs/standards/global/std-global-python-engineering.md`](../../.repo_studios/docs/standards/global/std-global-python-engineering.md) | Ensure embedded code snippets mirror runtime expectations |
| HTML and template nuances | [`.repo_studios/docs/standards/global/std-global-html-coding.md`](../../.repo_studios/docs/standards/global/std-global-html-coding.md) | Use when authoring embedded HTML fragments |
| Code cleanup standards | [`.repo_studios/docs/standards/global/std-global-code-cleanup.md`](../../.repo_studios/docs/standards/global/std-global-code-cleanup.md) | Technical debt reduction and refactoring guidelines |

## Agent callout block
````md
<!-- agents:begin:markdown_enforcement -->
```yaml
audience: [Copilot, Agents]
tasks:
  - id: md-check-001
    title: Verify YAML front matter + H1
    severity: error
  - id: md-check-002
    title: Ensure Goals + Agent Instructions + Update Log sections exist
    severity: warn
  - id: md-check-003
    title: Scan links for newline characters or >2048 length
    severity: warn
  - id: md-check-004
    title: Confirm all fenced blocks declare language
    severity: error
```
<!-- agents:end:markdown_enforcement -->
````

## Update log
- 2025-12-11 — Adapted for Repo_Studios, removed Jarvis2-specific references, updated paths to .repo_studios/ locations.
- 2025-11-28 — Initial instruction set authored post doc-index hardening.
