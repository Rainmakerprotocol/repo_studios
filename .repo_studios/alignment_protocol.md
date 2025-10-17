# Alignment Protocol: AI & Developer Collaboration

_Last updated: 2025-10-17_

This document captures the working blueprint for collaborative cycles between the coding agent (GitHub Copilot) and the human developer. It is meant to stay lightweight, evolve over time, and provide repeatable guardrails for future projects that adopt Repo Studios tooling.

## 1. Purpose & Principles
- Maintain a shared understanding of goals, constraints, and context before any implementation work begins.
- Keep the collaboration asynchronous-friendly: every important decision or question should be documented where agents can ingest it quickly.
- Treat alignment as an iterative process; revisit assumptions as new information surfaces.
- Preserve provenance for major actions so future agents and developers can audit decisions and reasoning chains.

## 2. Roles
- **Coding Agent (GitHub Copilot)**: researches the repository state, proposes questions, synthesizes responses, plans changes, and implements code/doc updates once explicitly approved.
- **Developer**: supplies domain context, answers alignment questions, reviews proposals, and decides when to advance to execution steps.

## 3. Collaboration Phases
1. **Scope & Discovery**
   - Agent inventories the repo, highlights unknowns, and drafts an alignment worksheet (e.g., `alignment_notes_temp.md`).
   - Developer reviews and fills in answers; agent responds to each answer to confirm understanding.
2. **Question Rounds**
   - Agent batches follow-up questions in numbered rounds to avoid overwhelming the developer.
   - Developer answers inline; agent acknowledges and refines the plan with each pass.
3. **Blueprint & Plan**
   - Agent distills decisions into actionable plans (e.g., inventory schema, folder layout strategy, automation phases).
   - Any prerequisites (e.g., environment setup, dependencies) are clarified before code work begins.
4. **Implementation & Logging**
   - With alignment confirmed, the agent executes agreed tasks, logging significant actions in `agent_notes/description_YYYY-MM-DD_hhmmss.txt`.
   - For multi-step efforts, the agent may create interim checklists to keep progress transparent.
5. **Review & Handoff**
   - Agent summarizes changes, test results, and next-step suggestions.
   - Developer reviews, approves, or requests adjustments; alignment doc is updated if scope shifts.

## 4. Artifacts & Record Keeping
- **Alignment worksheet**: Temporary scratch pad (e.g., `alignment_notes_temp.md`) capturing questions, answers, and agent responses.
- **Agent notes**: Timestamped text files under `agent_notes/` logging significant actions, decisions, or blockers.
- **Protocols & Standards**: Living documents (like this one) that encode the collaboration playbook and standards for reuse.
- **Automation Indexes**: Inventories and manifests that agents can query for roles, dependencies, and ownership.

## 5. Decision Logging Patterns
- Prefix all major questions with numbered headings to create a clear thread.
- When answers prompt new actions, the agent should confirm next steps directly beneath the developer’s response.
- Significant deviations from the plan are logged in `agent_notes/` with context, rationale, and follow-up items.

## 6. Extending the Protocol
- As new collaboration techniques emerge (e.g., automated diff reviews, governance checklists), append them here with dates and owning agents.
- Encourage future projects to clone this protocol and customize the phases/artefacts to their needs while retaining the core principles.

## 7. Open Items
- Define the governance checklist for project maturity phases (scaffold → growth → mature).
- Establish standard metadata format for alignment worksheets (project name, phase, participants).
- Integrate notifications or summaries for newly added `agent_notes/` entries if required.

_This protocol is intentionally iterative. Update it whenever alignment practices evolve so every Repo Studios project benefits from the collective learning._
