---
title: Global Prompt Engineering Standard
status: draft
version: 2025-12-07
last_updated: 2025-12-07
owner: repo_studios_ai
tags:
	- prompt-engineering
	- ai
	- evaluation
---

<!-- markdownlint-disable MD013 -->

# Global Prompt Engineering Standard

This standard describes how Repo Studios designs, evaluates, and governs prompts used by automation agents
and customer-facing assistants.

## Evaluation Cases

- Pair every material prompt change with evaluation cases that demonstrate expected success criteria and known failure modes.
- Store evaluation artifacts alongside the prompt (for example JSON or markdown fixtures) so reviewers can replay them quickly.
- Automate regression checks where feasible, and document manual review steps when automation is not yet available.

## Design Principles

- Anchor each prompt with an explicit task statement, guardrails, and output format to minimise ambiguity.
- Compose prompts using reusable snippets (persona, policies, response schema) maintained in version control
	to keep behaviour consistent across surfaces.
- Include negative instructions that prohibit unsafe behaviours and reference escalation guidelines for edge
	cases.

## Deployment Workflow

- Record prompt revisions in the prompt catalog with links to evaluation results and release notes.
- Secure reviewer approval before promoting a prompt to production; reviewers confirm policy alignment and
	evaluation coverage.
- Monitor live metrics (quality ratings, deflection rates, incident counts) after release; roll back promptly
	if degradation is detected.

## Data Stewardship

- Mask personal or regulated data in evaluation corpora and prompts stored in the repository; rely on the
	secure fixture store for sensitive examples.
- Document data provenance and consent status when incorporating third-party content.
- Remove evaluation artifacts when they exceed retention policies and record the purge in the governance
	register.

<!-- markdownlint-enable MD013 -->
