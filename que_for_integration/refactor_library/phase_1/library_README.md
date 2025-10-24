# .repo_studios/library/

**The Composable Code Library for Repo Studios**

## Purpose

This library contains **reusable, tested, single-responsibility functions** extracted from duplicate code across Repo Studios scripts. It serves as the central "store" of code utilities that AI agents and developers can reference instead of recreating common patterns.

---

## Philosophy

### Design Principles

1. **AI-First Navigation** - Folder and file names are optimized for autonomous AI discovery
2. **Single Responsibility** - Each module does ONE thing well
3. **Zero Duplication** - If code appears in 2+ places, it belongs here
4. **Test Coverage** - Every library function has corresponding pytest tests
5. **Pure Functions Preferred** - Minimize side effects; maximize composability

### Key Concepts

- **Technical Domain** (Level 1) - What the code operates on
- **Functional Purpose** (Level 2) - What the code achieves
- **Specific Implementation** (Level 3) - The actual function

---

## Directory Structure

```
.repo_studios/library/
│
├── filesystem/                          # File & directory operations
│   ├── path_operations/                 # Path manipulation
│   │   ├── compute_relative_path.py     # Convert absolute → repo-relative
│   │   └── resolve_absolute_path.py     # Convert relative → absolute
│   └── directory_management/            # Directory lifecycle
│       ├── ensure_directory.py          # Create dir with parents
│       └── create_timestamped_dir.py    # Create run dirs with timestamp
│
├── artifact_lifecycle/                  # Report/output management
│   ├── versioning/                      # Artifact version control
│   │   ├── create_latest_link.py        # Hardlink/copy "latest" artifacts
│   │   └── prune_old_runs.py            # Delete old timestamped dirs
│   ├── structured_output/               # Multi-format report generation
│   │   ├── write_json_artifact.py       # JSON with indent/sort
│   │   ├── write_markdown_artifact.py   # Markdown reports
│   │   ├── write_log_artifact.py        # key=value logs
│   │   └── write_tsv_artifact.py        # TSV tables
│   └── schemas/                         # Common report structures
│       └── base_report_schema.py        # schema_version, generated_utc, etc.
│
├── time_handling/                       # Timestamp operations
│   ├── parsing/                         # Input normalization
│   │   └── parse_iso_timestamp_utc.py   # ISO string → UTC datetime
│   └── formatting/                      # Output formatting
│       └── format_run_timestamp.py      # datetime → %Y%m%d_%H%M%S
│
├── logging_setup/                       # Logging configuration
│   └── configuration/                   # Logger initialization
│       └── configure_basic_logging.py   # Setup level & format
│
└── cli_patterns/                        # CLI argument handling
    └── common_args/                     # Reusable arg definitions
        ├── repo_root_arg.py             # --repo-root
        ├── output_dir_arg.py            # --output-dir
        ├── timestamp_arg.py             # --timestamp
        └── artifacts_to_keep_arg.py     # --artifacts-to-keep
```

---

## Usage Guidelines

### For Developers

#### Before Writing a New Utility Function

1. **Search the library first:**
   ```bash
   find .repo_studios/library -name "*.py" | xargs grep "def your_function_name"
   ```

2. **Check naming conventions:**
   - Read: `.repo_studios/naming_conventions.md`

3. **If function exists:**
   - Import it: `from .repo_studios.library.domain.purpose import function_name`

4. **If function doesn't exist:**
   - Is it truly reusable (used in 2+ places)?
   - Does it have a clear single responsibility?
   - Can you name it following conventions?
   - If YES to all → Extract to library
   - If NO → Keep it local to your script

#### Extracting to Library

**Manual Process (Phase 3):**
1. Choose appropriate domain/purpose folders
2. Create module file with clear verb_noun name
3. Write function with type hints and docstring
4. Create pytest test in `.repo_studios/tests/tests_library/`
5. Replace duplicates with import statements
6. Run tests to confirm no regressions

**Automated Process (Phase 4+):**
1. Run: `make studio-detect-duplicates`
2. Review: `.repo_studios/reports/duplicate_detection_report.json`
3. Run: `make studio-refactor-duplicates`
4. System automatically extracts, tests, and replaces

### For AI Agents (GitHub Copilot, Claude, etc.)

#### When Generating Code

**Priority Order:**
1. **Check library first** - Search `.repo_studios/library/` for existing utilities
2. **Import if exists** - Never duplicate code that's already in library
3. **Suggest extraction** - If writing duplicate code, suggest moving to library
4. **Follow conventions** - New library modules must follow naming conventions

#### Navigation Instructions

**Query Pattern:** "I need to [ACTION] a [THING]"

**Navigation Logic:**
1. Identify THING → Find Level 1 folder (technical domain)
2. Identify ACTION → Find Level 2 folder (functional purpose)  
3. Look for `[ACTION]_[THING].py` module

**Examples:**
- "Parse ISO timestamps" → `time_handling/parsing/parse_iso_timestamp_utc.py`
- "Create directory safely" → `filesystem/directory_management/ensure_directory.py`
- "Prune old artifacts" → `artifact_lifecycle/versioning/prune_old_runs.py`

#### Code Generation Template

When AI needs to use a library function:

```python
# Step 1: Import from library
from .repo_studios.library.{domain}.{purpose} import {function_name}

# Step 2: Use the function
result = function_name(args)

# Step 3: NO need to reimplement!
```

When AI doesn't find the function in library:

```python
# TODO: This function is a candidate for library extraction
# Target: .repo_studios/library/{domain}/{purpose}/{function_name}.py
def temporary_function():
    """Will be extracted to library after duplicate detection."""
    pass
```

---

## Testing

### Running Library Tests

```bash
# Test entire library
pytest .repo_studios/tests/tests_library/

# Test specific domain
pytest .repo_studios/tests/tests_library/test_filesystem/

# Test specific module
pytest .repo_studios/tests/tests_library/test_artifact_lifecycle/test_create_latest_link.py
```

### Test Organization

Tests mirror the library structure:

```
.repo_studios/tests/tests_library/
├── test_filesystem/
│   ├── test_path_operations/
│   │   └── test_compute_relative_path.py
│   └── test_directory_management/
│       └── test_ensure_directory.py
├── test_artifact_lifecycle/
│   ├── test_versioning/
│   │   ├── test_create_latest_link.py
│   │   └── test_prune_old_runs.py
│   └── test_structured_output/
│       └── test_write_json_artifact.py
└── ...
```

---

## Current Status

**Phase:** Foundation Setup (Phase 1 Complete)

**Modules Implemented:** 0 / 14 placeholders

**Next Steps:**
1. Run duplicate detection: `scan_code_duplicates.py`
2. Review extraction candidates
3. Begin manual extraction validation (Phase 3)

---

## Maintenance

### Adding New Modules

1. Ensure module follows naming conventions
2. Place in appropriate domain/purpose folder
3. Create corresponding test file
4. Update this README if adding new domain/purpose
5. Run full test suite to confirm no conflicts

### Modifying Existing Modules

1. **Never modify without tests** - Update tests first
2. Check reverse dependencies - Who imports this?
3. Consider backwards compatibility
4. Document breaking changes in commit message

### Deprecating Modules

1. Mark as deprecated in docstring
2. Add deprecation warning
3. Provide migration path to replacement
4. Remove after 2 release cycles minimum

---

## Anti-Patterns to Avoid

### ❌ Don't Do This

```python
# BAD - Creating "god object" utility file
from .repo_studios.library.utils import everything

# BAD - Bypassing library with local duplicate
def _my_local_copy_of_library_function():
    pass

# BAD - Importing entire module
from .repo_studios.library.filesystem.path_operations import *

# BAD - Circular imports
# library function importing from scripts
```

### ✅ Do This Instead

```python
# GOOD - Specific imports
from .repo_studios.library.filesystem.path_operations import compute_relative_path
from .repo_studios.library.artifact_lifecycle.versioning import create_latest_link

# GOOD - Using library as single source of truth
result = create_latest_link(src, dest)

# GOOD - Keeping library self-contained
# Library modules only import from stdlib or other library modules
```

---

## FAQ

**Q: When should I add code to the library?**  
A: When you find yourself copy-pasting the same function into a 2nd script.

**Q: Can library functions call other library functions?**  
A: Yes! Compose small functions into larger ones. Just avoid circular imports.

**Q: What if I need to modify a library function for my specific use case?**  
A: Don't modify the library function. Instead:
1. Add optional parameters to make it more flexible, OR
2. Create a new specialized function that calls the library function

**Q: How do I know if my code belongs in the library?**  
A: Ask: "Would this be useful to 2+ other scripts?" If YES → library. If NO → keep local.

**Q: Can I import library functions in tests?**  
A: Absolutely! In fact, please do. Library functions are the *preferred* way to handle common operations.

---

## Resources

- **Naming Conventions:** `.repo_studios/naming_conventions.md`
- **Duplicate Detection:** `.repo_studios/scripts/producers/scan_code_duplicates.py`
- **Auto Refactoring:** `.repo_studios/scripts/orchestrators/refactor_from_report.py`
- **Test Templates:** `.repo_studios/tests/tests_library/`

---

## Contributing

This library is **automatically curated** by the duplicate detection pipeline. Manual additions are allowed but must:

1. Follow naming conventions strictly
2. Include comprehensive tests
3. Have clear docstrings with examples
4. Pass all existing tests without modification

**Questions?** Check the naming conventions doc or run duplicate detection to see examples of proper structure.
