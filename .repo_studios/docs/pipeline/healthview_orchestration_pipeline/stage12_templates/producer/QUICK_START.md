---
title: "Producer Quick Start"
tier: quick-reference
audience:
  - coding_agent
  - human_developer
status: active
version: 1.0.0
updated_at: 2026-02-01
related_files:
  - ./build_template.md
---

# Producer Quick Start — Express Lane

> **Use this when:** Script is already mostly compliant and you need fast verification.
> **Use full template when:** Script has significant gaps, is new, or requires detailed documentation.
>
> **Time estimate:** 30 minutes (vs 2-3 hours for full template)

---

## Pre-Flight Check

Before starting, confirm:

- [ ] Script path known: `________________________`
- [ ] Record ID assigned: `________________________`
- [ ] Compliance Tier determined: `[ ] Tier A (HOP bundle)` / `[ ] Tier B (Utility)`

If any are missing, **STOP** and get assignment details first.

---

## Express Verification Checklist

### 1. Entry Point Contract (5 min)

| Check | Command | Pass? |
|-------|---------|-------|
| `run(argv)` exists | `grep -n "def run" <script>` | [ ] |
| Returns dict | Check return type annotation | [ ] |
| Has `status` key | Check return statement | [ ] |
| Has `exit_code` key | Check return statement | [ ] |
| No `sys.exit()` in run() | `grep -n "sys.exit" <script>` | [ ] |

### 2. CLI Flags (5 min)

| Check | Command | Pass? |
|-------|---------|-------|
| `--repo-root` supported | `python <script> --help` | [ ] |
| `--log-level` supported | `python <script> --help` | [ ] |
| `--artifacts-to-keep` (Tier A only) | `python <script> --help` | [ ] / N/A |

### 3. HOP Bundle (Tier A only) (5 min)

| Check | How to Verify | Pass? |
|-------|---------------|-------|
| Produces manifest.json | Run script, check output dir | [ ] |
| Produces summary.md | Run script, check output dir | [ ] |
| Produces telemetry.json | Run script, check output dir | [ ] |
| Uses `build_topic_path()` | `grep -n "build_topic_path" <script>` | [ ] |

**Skip this section if Tier B.**

### 4. Actually Run It (10 min)

```bash
# Run the script
python <script> --log-level DEBUG

# Verify output exists
ls -la <output_dir>

# Spot-check one claim in summary.md against reality
# Example: If summary says "5 violations found", manually count them
```

- [ ] Script ran without error
- [ ] Output files created
- [ ] One claim spot-checked and TRUE

### 5. Tier-3 YAML (5 min)

- [ ] YAML exists at `<script_dir>/<script_name>.tier3.yaml`
- [ ] `tool.id` matches script name
- [ ] `invocation.script_path` is correct

### 6. Final Sign-Off

| Item | Status |
|------|--------|
| All checks above pass | [ ] |
| No HIGH priority gaps found | [ ] |
| Ready for orchestrator integration | [ ] |

**Inspector:** `________________________`  
**Date:** `________________________`

---

## Found Gaps?

If any check above **FAILS**, switch to the [full build template](./build_template.md):

1. Create `{RECORD_ID}_{script_stem}_build.md`
2. Document the gap in Section 5
3. Fix and re-verify using full process

---

## Quick Reference Links

- [Full Build Template](./build_template.md)
- [Requirements Registry](./build_template.md#requirements-registry)
- [Status Values Legend](./build_template.md#status-values-legend)
- [Tier-3 YAML Template](./build_template.md#33-reference-tier-3-yaml-template)
