# .repo_studios Library Naming Training Guide

> Canonical source: `que_for_integration/refactor_library/phase_1/naming_conventions.md`

**Purpose:** Define strict naming rules for the composable code library to ensure 100% AI discoverability and autonomous navigation.

**Philosophy:** Names should answer "what does this do?" not "how does it work?"

> **Audience:** AI copilots, automation agents, and developers onboarding to the shared library.
>
> **Canonical Source:** `que_for_integration/refactor_library/phase_1/naming_conventions.md`

This guide trains agents on how to interpret, enforce, and validate naming conventions inside `.repo_studios/library`. Use it as an operational playbook, not just a reference.

---

## 1. Mission & Outcomes

- **Mission:** Every path in `.repo_studios/library` must tell an AI _exactly_ what the code does.
- **Outcomes:**
  - Agents can infer purpose from directory + module names without reading code.
  - Naming violations are detected automatically and remediated using the decision tree in §4.
  - New modules join the library with zero manual rework.

---

## 2. Core Principles

1. **Answer "what", never "how".** Names describe capability, not implementation.
2. **Be maximally specific.** Longer, precise names beat vague shorthand.
3. **Keep depth ≤ 3 levels.** Domain → Purpose → Module.
4. **Primary function mirrors filename.** (`module_name.py` exports `module_name()`)
5. **No junk-drawer terms.** `utils`, `helpers`, `common`, `misc`, `stuff`, etc. are banned at every level.

> ❗ When in doubt, rename to remove ambiguity _before_ committing code.

---

## 3. Directory Structure Rules

### 3.1 Level 1 — Domain Folder (noun)

- **Goal:** Name the technical domain or lifecycle the code operates on.
- **Examples:** `filesystem/`, `artifact_lifecycle/`, `time_handling/`, `logging_setup/`, `cli_patterns/`
- **Violations:** `utils/`, `core/`, `misc/`, `common/`

### 3.2 Level 2 — Purpose Subfolder (noun or gerund_noun)

- **Goal:** Describe the specific category of work.
- **Examples:** `path_operations/`, `directory_management/`, `versioning/`, `structured_output/`, `parsing/`
- **Violations:** `other/`, `tmp/`, `stuff/`, `helpers/`

### 3.3 Level 3 — Module File (verb_noun.py)

- **Goal:** Single action + target.
- **Examples:** `compute_relative_path.py`, `create_latest_link.py`, `parse_iso_timestamp_utc.py`, `write_json_artifact.py`
- **Violations:** `path_utils.py`, `helpers.py`, `common.py`, `base.py`

---

## 4. Enforcement Decision Tree

```mermaid
START → Review path components (domain/purpose/module)
    ↓
Is any component vague (utils/helpers/etc.)?
    → YES → Rename to concrete noun/verb-noun. Document change in checklist.
    → NO → Continue

Does module name match its primary function (verb_noun)?
    → NO → Rename file or function so they align.
    → YES → Continue

Is hierarchy deeper than 3 levels?
    → YES → Consolidate by promoting purpose folder or splitting module.
    → NO → Continue

Is there a single module in a purpose folder?
    → YES → Evaluate: promote module up or add roadmap for additional modules.
    → NO → Pass

END → Update inventory + notify library owners of adjustments.
```

---

## 5. AI Agent Playbook

### 5.1 New Module Checklist

- [ ] Validate domain folder exists; create if missing with noun naming.
- [ ] Pick purpose folder; ensure at least 3 peer modules justify its existence.
- [ ] Name module `verb_noun.py`; implement `verb_noun()` as primary export.
- [ ] Add module docstring with one-line capability summary.
- [ ] Update function inventory (`.repo_studios/scripts/producers/generate_function_inventory.py`).
- [ ] Log addition in `.repo_studios/library_integration/checklists/YYYY-MM-DD.md`.

### 5.2 Refactor Checklist

- [ ] Run enforcement decision tree (§4) against candidate modules.
- [ ] For each rename, update imports across repo using search-and-replace.
- [ ] Regenerate inventories + reports.
- [ ] Capture before/after paths in run report.
- [ ] Notify owning team with rationale.

---

## 6. Examples for Navigation Queries

| Query | Expected Path | Rationale |
| --- | --- | --- |
| "Convert absolute path to relative" | `filesystem/path_operations/compute_relative_path.py` | Domain filesystem → purpose path ops → module action |
| "Prune old report directories" | `artifact_lifecycle/versioning/prune_old_runs.py` | Lifecycle management of artifacts |
| "Parse ISO timestamp" | `time_handling/parsing/parse_iso_timestamp_utc.py` | Time handling domain + parsing purpose |

---

## 7. Forbidden Patterns Cheat Sheet

- Folder names: `utils/`, `helpers/`, `common/`, `misc/`, `other/`, `stuff/`
- Module names: `*_utils.py`, `helpers.py`, `common.py`, `base.py`, `main.py`
- Abbreviations: `fs_ops/` instead of `filesystem/`
- Mixed concerns: `path_and_logging_utils.py`
- Deep nesting: `library/a/b/c/d/e.py`

Agents encountering these must schedule remediation immediately.

---

## 8. Validation & Automation Hooks

- **Lint Gate:** Extend inventory generator to flag banned tokens (TODO tracked in checklist §Phase 1).
- **Runbooks:** `docs/checklists/*.md` capture remediation tasks + outcomes.
- **Reporting:** Store diffs in `.repo_studios/library_integration/reports/` for each run, including renamed paths and justification.

---

## 9. Escalation Protocol

1. If naming ambiguity persists after applying rules, capture context + blockers in checklist.
2. Tag library maintainers (`#library-owners` channel) with proposal using the domain/purpose/action format.
3. Do not merge code until naming passes review.

---

## 10. Success Criteria (Definition of Done)

- [ ] Zero banned tokens in directory or file names.
- [ ] Every module’s primary function matches filename.
- [ ] Inventory and documentation synchronized after changes.
- [ ] Checklist updated with actions taken and issues raised.

> ✅ When all boxes are checked, the naming change is ready for integration.

- ✅ `directory_management/` - manages directories
- ✅ `versioning/` - handles version control of artifacts
- ✅ `structured_output/` - generates formatted outputs
- ✅ `parsing/` - converts input formats
- ✅ `formatting/` - converts to output formats

**Anti-patterns:**

- ❌ `misc/` - catch-all is forbidden
- ❌ `other/` - unclear purpose
- ❌ `stuff/` - unprofessional and vague

### Level 3: Module Files

**Format:** `verb_noun.py` describing the specific action

**Examples:**

- ✅ `compute_relative_path.py` - clear action + target
- ✅ `create_latest_link.py` - verb + noun
- ✅ `parse_iso_timestamp_utc.py` - action + format + constraint
- ✅ `write_json_artifact.py` - action + format + target

**Anti-patterns:**

- ❌ `path_utils.py` - "utils" is meaningless
- ❌ `helpers.py` - what kind of help?
- ❌ `common.py` - common to what?
- ❌ `base.py` - base of what?

---

## 🐍 Python Naming Within Modules

### Function Names

**Format:** `verb_noun` matching the filename (usually same as module name without `.py`)

**Rule:** The primary function in a module should match the module filename.

**Example:**

```python
# File: create_latest_link.py
def create_latest_link(source: Path, destination: Path) -> None:
    """Create hardlink with fallback to file copy."""
    pass
```

**Anti-patterns:**

```python
# ❌ BAD - doesn't match filename
# File: create_latest_link.py
def make_link(source, dest):  # Wrong name
    pass

# ❌ BAD - unclear prefix
# File: create_latest_link.py
def _internal_create_latest_link(source, dest):  # Don't hide primary function
    pass
```

### Private Helpers

**Format:** Prefix with single underscore `_verb_noun`

**Rule:** Only use for implementation details not meant for external import.

**Example:**

```python
# File: prune_old_runs.py
def prune_old_runs(output_dir: Path, *, keep: int) -> list[Path]:
    """Public API - prune old timestamped directories."""
    candidates = _collect_pruneable_dirs(output_dir)
    return _delete_oldest(candidates, keep)


def _collect_pruneable_dirs(output_dir: Path) -> list[Path]:
    """Private helper - not exported."""
    pass


def _delete_oldest(dirs: list[Path], keep: int) -> list[Path]:
    """Private helper - not exported."""
    pass
```

---

## 📦 Import Statement Patterns

### Standard Import Format

```python
# From scripts/producers/
from .repo_studios.library.artifact_lifecycle.versioning import create_latest_link
from .repo_studios.library.time_handling.parsing import parse_iso_timestamp_utc
```

### Group Imports by Domain

```python
# Stdlib first
import json
from pathlib import Path
from datetime import datetime

# Third-party second
import yaml

# Library imports third (grouped by domain)
from .repo_studios.library.filesystem.path_operations import compute_relative_path
from .repo_studios.library.filesystem.directory_management import ensure_directory

from .repo_studios.library.artifact_lifecycle.versioning import create_latest_link
from .repo_studios.library.artifact_lifecycle.versioning import prune_old_runs

from .repo_studios.library.time_handling.parsing import parse_iso_timestamp_utc

# Local imports last
from .local_module import helper_function
```

---

## 🤖 AI Navigation Examples

### Example 1: Finding Path Utilities

**AI Query:** "Where do I find functions for converting absolute paths to relative?"

**Navigation Path:**

1. `filesystem/` ← works with file system paths
2. `path_operations/` ← manipulates paths
3. `compute_relative_path.py` ← verb "compute" + noun "relative_path"

### Example 2: Finding Timestamp Parsers

**AI Query:** "I need to parse ISO timestamps into UTC datetime objects"

**Navigation Path:**

1. `time_handling/` ← deals with time/dates
2. `parsing/` ← converts input formats to structured data
3. `parse_iso_timestamp_utc.py` ← exact match!

### Example 3: Finding Artifact Pruning

**AI Query:** "How do I delete old timestamped report directories?"

**Navigation Path:**

1. `artifact_lifecycle/` ← manages generated artifacts
2. `versioning/` ← handles retention of artifact versions
3. `prune_old_runs.py` ← verb "prune" indicates deletion

---

## 🚫 Forbidden Patterns

### Never Use These Names

- `utils/`, `helpers/`, `common/`, `misc/`, `other/`, `stuff/`
- `base.py`, `core.py`, `main.py` (in library - too vague)
- Abbreviations: `fs_ops/` instead of `filesystem/`
- Technical jargon without context: `dag/`, `etl/` (unless domain-specific)

### Never Use These Structures

- Flat library with no hierarchy: `library/everything.py` ❌
- Deep nesting (>3 levels): `library/a/b/c/d/e.py` ❌
- Mixed concerns in one file: `path_and_logging_utils.py` ❌

---

## 📊 Validation Checklist

Before adding any new library module, ask:

- [ ] Does the folder name describe WHAT (not HOW)?
- [ ] Does the filename start with a VERB?
- [ ] Can an AI infer the purpose from the path alone?
- [ ] Is the hierarchy maximum 3 levels deep?
- [ ] Does the primary function name match the filename?
- [ ] Are there no "utils/helpers/common" anti-patterns?
- [ ] Would a junior developer (or AI) find this intuitively?

---

## 🔄 Evolution Rules

### When to Create a New Module

✅ Create new module when:

- Function has single clear purpose
- Function will be reused across 2+ scripts
- Function has no side effects or minimal controlled side effects

❌ Don't create module when:

- Function is script-specific business logic
- Function has heavy external dependencies
- Function's purpose is unclear or mixed

### When to Create a New Folder

✅ Create new folder when:

- You have 3+ related modules that share a theme
- The theme is distinct from existing folders
- The theme can be named with a clear noun

❌ Don't create folder when:

- Only 1-2 modules would live there
- Purpose overlaps heavily with existing folder
- You're tempted to name it "misc" or "other"

---

## 🎯 Summary

**Golden Rule:** If you can't explain what a module does from its path alone, rename it.

**Test:** Show path to someone unfamiliar with the code. Can they guess what it does?

- ✅ `artifact_lifecycle/versioning/prune_old_runs.py` - YES
- ❌ `core/utils/helpers.py` - NO

**When in doubt:** More specific is better than more general.
