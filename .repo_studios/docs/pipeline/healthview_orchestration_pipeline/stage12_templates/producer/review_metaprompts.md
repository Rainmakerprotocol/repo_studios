---
title: "Producer Review Metaprompts (Redirect)"
tier: metaprompt
audience:
  - coding_agent
  - human_operator
status: redirect
version: 1.1.0
updated_at: 2026-02-02
redirect_to: ../common/review_metaprompts.md
---

# ⚠️ REDIRECT NOTICE

**This file has moved.**

The review metaprompts are now shared across all script classes.

**New location:**
`.repo_studios/docs/pipeline/healthview_orchestration_pipeline/stage12_templates/common/review_metaprompts.md`

**Why:**
The 8 review prompts (PROMPT-01-SETUP through PROMPT-910-CLOSE) are class-agnostic — they
apply equally to producers, consumers, aggregators, summarizers, utilities, orchestrators,
and promotion scripts. Maintaining a single file ensures consistency and eliminates sync issues.

**What's class-specific:**
- `{CLASS}/build_template.md` — The output template (copied during BOOTSTRAP)
- `{CLASS}/QUICK_START.md` — Class-specific quick reference (optional, producer only for now)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.1.0 | 2026-02-02 | Converted to redirect; content moved to `common/review_metaprompts.md` |
| 1.0.1 | 2026-02-02 | Fixed path conflict: Pre-Flight now uses `tier2_roster/working_docs/stage_{STAGE}/` |
| 1.0.0 | 2026-02-01 | Initial release with 8 prompts aligned to template v3.4.0 |
