---
description: Google-style docstring requirements for Python code
applyTo: '**/*.py'
---

# Google-Style Docstring Standard

## Overview

All Python code in this repository follows **Google-style docstrings** as defined in the
[Google Python Style Guide](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings).

## Required Coverage

| Element | Requirement |
|---------|-------------|
| Module | Required — describe purpose, key exports, usage context |
| Public class | Required — describe purpose, key attributes |
| Public function/method | Required — describe behavior, args, returns, raises |
| Private function/method | Recommended for non-trivial logic |
| Dataclass/NamedTuple | Required — describe purpose; field docs via inline comments or Args section |

## Module Docstring Template

```python
"""One-line summary of module purpose.

Extended description explaining the module's role in the system,
key exports, and typical usage patterns. Keep to 2-3 sentences.

Example:
    >>> from module import main_function
    >>> result = main_function(arg)
"""
```

## Function/Method Docstring Template

```python
def function_name(param1: str, param2: int, optional: bool = False) -> dict[str, Any]:
    """One-line summary of function behavior.

    Extended description if the one-liner is insufficient. Explain
    algorithm, side effects, or important behavioral notes.

    Args:
        param1: Description of first parameter.
        param2: Description of second parameter.
        optional: Description of optional parameter. Defaults to False.

    Returns:
        Description of return value. For complex types, describe structure:
        - key1: Description of key1 value
        - key2: Description of key2 value

    Raises:
        ValueError: When param1 is empty.
        FileNotFoundError: When referenced path does not exist.

    Example:
        >>> result = function_name("test", 42)
        >>> result["status"]
        'success'
    """
```

## Class Docstring Template

```python
class ClassName:
    """One-line summary of class purpose.

    Extended description explaining the class's role, lifecycle,
    and key behavioral contracts.

    Attributes:
        attr1: Description of public attribute.
        attr2: Description of another public attribute.

    Example:
        >>> obj = ClassName(config)
        >>> obj.process()
    """

    def __init__(self, config: Config) -> None:
        """Initialize the ClassName instance.

        Args:
            config: Configuration object for initialization.
        """
```

## Dataclass Docstring Template

```python
@dataclass
class DataClassName:
    """One-line summary of dataclass purpose.

    Extended description if needed.

    Attributes:
        field1: Description of field1.
        field2: Description of field2.
    """

    field1: str
    field2: int
```

## Section Order

When multiple sections are present, use this order:

1. One-line summary (required)
2. Extended description (optional)
3. `Args:` (if parameters exist)
4. `Returns:` (if non-None return)
5. `Yields:` (for generators)
6. `Raises:` (if exceptions raised)
7. `Example:` or `Examples:` (recommended for public APIs)
8. `Note:` or `Notes:` (optional)
9. `See Also:` (optional)
10. `Todo:` (optional, for known gaps)

## Formatting Rules

1. **First line**: Imperative mood, ends with period, fits on one line
2. **Blank line**: Separate summary from extended description and sections
3. **Args indentation**: 4 spaces for continuation lines
4. **Type hints**: In signature, not duplicated in docstring
5. **Line length**: Follow project standard (88 chars for Black compatibility)

## Anti-Patterns to Avoid

| Anti-Pattern | Correct Approach |
|--------------|------------------|
| `"""Gets the value."""` | `"""Return the cached value."""` (imperative) |
| Duplicating type hints in Args | Types in signature only |
| `"""This function does..."""` | Start with verb directly |
| Empty docstrings `""""""` | Omit or write meaningful content |
| Sphinx/reST `:param:` syntax | Use `Args:` section |

## Validation

Docstring compliance is checked via:

- `pydocstyle --convention=google` (CI integration planned)
- `generate_undocumented_logic_report.py` for coverage metrics

## References

- [Google Python Style Guide - Docstrings](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings)
- [PEP 257 - Docstring Conventions](https://peps.python.org/pep-0257/)
