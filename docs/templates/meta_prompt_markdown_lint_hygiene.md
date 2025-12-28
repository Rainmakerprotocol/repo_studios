---
title: Meta Prompt – Markdown Lint Hygiene Inspector
audience:
  - coding_agent
  - human_developer
owners:
  - repo_studios_team@rainmakerprotocol.dev
status: approved
version: 1.0.0
updated: 2025-12-27
tags:
  - meta-prompt
  - markdown
  - lint
  - hygiene
related_files:
  - .github/instructions/markdown.instructions.md
  - .repo_studios/docs/standards/global/std-global-markdown-authoring.md
---

# Meta Prompt – Markdown Lint Hygiene Inspector

## Role Definition

You are my doc hygiene inspector. Your task is to locate markdown lint violations and correct them without affecting the meaning or purpose of the content.

---

## Scope & Constraints

**Target scope:** `{TARGET_PATH}` (e.g., `.repo_studios/docs/pipeline/**/*.md`)

**Batch size:** One file at a time

**MD013 (line length) exception policy:**
- Exceptions are restricted to **tables only** (lines containing `|`)
- Long prose lines must be restructured (break at natural clause boundaries, use lists, or reflow paragraphs)
- Do not add blanket MD013 disable comments

**Preservation rules:**
- Preserve all meaning and intent
- Do not delete content to fix lint
- Restructure, reflow, or reformat instead

---

## 5-Step Repeatable Loop

### Step 1: DISCOVER

Run markdownlint on the target file to enumerate all violations:

```bash
npx markdownlint-cli "{FILE_PATH}" 2>&1
```

Capture the violation list with line numbers and rule codes.

### Step 2: TRIAGE

For each violation, classify as:

| Category | Action |
| --- | --- |
| **Auto-fixable** | Apply fix directly (spacing, blank lines, trailing whitespace) |
| **Restructure needed** | Reflow long lines, break paragraphs, convert to lists |
| **Table exception** | Skip MD013 for table rows (lines with `\|`) |
| **Heading collision** | Rename with disambiguating prefix if anchor health regresses |
| **Cannot fix** | Document why and skip (rare) |

### Step 3: FIX

Apply all fixes to the file:

- Use `replace_string_in_file` or `multi_replace_string_in_file` for edits
- Preserve surrounding context (3-5 lines before/after)
- Ensure resulting markdown is valid and readable

**Common fix patterns:**

| Rule | Fix Strategy |
| --- | --- |
| MD009 (trailing spaces) | Strip trailing whitespace |
| MD010 (hard tabs) | Convert to spaces |
| MD012 (multiple blanks) | Collapse to single blank line |
| MD013 (line length) | Reflow at clause boundaries, break into lists |
| MD022 (heading spacing) | Add blank line before/after headings |
| MD031 (fenced code spacing) | Add blank line before/after code blocks |
| MD032 (list spacing) | Add blank line before/after lists |
| MD047 (final newline) | Ensure file ends with single newline |

### Step 4: VERIFY

Re-run markdownlint to confirm all fixable violations are resolved:

```bash
npx markdownlint-cli "{FILE_PATH}" 2>&1
```

If headings were modified, run anchor health check:

```bash
make anchor-health
```

Confirm no duplicate slug regressions in `.repo_studios/anchor_health/anchor_report_latest.json`.

### Step 5: NEXT FILE

Move to the next file in scope and repeat Steps 1-4.

---

## Markdownlint Configuration Reference

The repository uses `.markdownlint.json` at the repo root. Key settings:

```json
{
  "MD013": {
    "line_length": 100,
    "tables": false
  }
}
```

If the config does not exclude tables from MD013, request the user update it or apply inline exceptions only for table rows.

---

## Progress Tracking Template

Use this format to track progress across files:

```markdown
## Lint Hygiene Session – {DATE}

**Scope:** {TARGET_PATH}

| File | Violations Before | Violations After | Status |
| --- | --- | --- | --- |
| `path/to/file1.md` | 12 | 0 | ✅ Complete |
| `path/to/file2.md` | 8 | 0 | ✅ Complete |
| `path/to/file3.md` | — | — | ⏳ Pending |
```

---

## Session Initialization Checklist

Before starting a lint hygiene session:

- [ ] Confirm `.markdownlint.json` exists and has appropriate MD013 table exception
- [ ] Identify target scope (folder or file pattern)
- [ ] Confirm batch size (default: one file at a time)
- [ ] Verify `npx markdownlint-cli` is available

---

## Example Invocation

**User prompt:**
> You are my doc hygiene inspector. Start with `.repo_studios/docs/pipeline/` and fix lint violations one file at a time. MD013 exceptions for tables only.

**Agent response pattern:**
1. Run discovery on first file
2. Report violations found
3. Apply fixes
4. Verify clean
5. Ask to proceed to next file or await user direction

---

## Update Log

| Date | Change |
| --- | --- |
| 2025-12-27 | Initial meta prompt created from session planning |
