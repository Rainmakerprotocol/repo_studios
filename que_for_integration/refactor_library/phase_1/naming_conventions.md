# Naming Conventions for .repo_studios/library/

**Purpose:** Define strict naming rules for the composable code library to ensure 100% AI discoverability and autonomous navigation.

**Philosophy:** Names should answer "what does this do?" not "how does it work?"

---

## 📁 Folder Naming Rules

### Level 1: Technical Domain (Top-Level)
**Format:** `noun` describing what the code operates on

**Examples:**
- ✅ `filesystem/` - operates on files and directories
- ✅ `artifact_lifecycle/` - manages artifact generation and versioning
- ✅ `time_handling/` - works with timestamps and dates
- ✅ `logging_setup/` - configures logging behavior
- ✅ `cli_patterns/` - command-line interface utilities

**Anti-patterns:**
- ❌ `utils/` - too vague
- ❌ `core/` - meaningless
- ❌ `helpers/` - ambiguous
- ❌ `common/` - doesn't describe what it contains

### Level 2: Functional Purpose (Subdirectory)
**Format:** `noun` or `gerund_noun` describing the specific purpose

**Examples:**
- ✅ `path_operations/` - manipulates paths
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

### Never Use These Names:
- `utils/`, `helpers/`, `common/`, `misc/`, `other/`, `stuff/`
- `base.py`, `core.py`, `main.py` (in library - too vague)
- Abbreviations: `fs_ops/` instead of `filesystem/`
- Technical jargon without context: `dag/`, `etl/` (unless domain-specific)

### Never Use These Structures:
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
