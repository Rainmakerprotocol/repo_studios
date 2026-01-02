# DB Integration: Monkey Patch Risk Utility

## Script Identity

- **Script**: `monkey_patch_risk.py`
- **Path**: `.repo_studios/scripts/utilities/monkey_patch_risk.py`
- **Category**: Utility (shared helper module)
- **Standard Reference**: `docs/standards/global/std-global-monkey-patching.md`

## Purpose

Shared monkey patch risk classification helpers used by consumers and aggregators to emit consistent severity tiers for scanner findings.

## I/O Contract

This is a **library module**, not a standalone CLI script.

### Exports

| Export | Type | Description |
|--------|------|-------------|
| `RiskLevel` | Type alias | Literal type: `"HIGH"`, `"MODERATE"`, `"SAFE"` |
| `FindingSignals` | Dataclass | Signals required to classify a finding |
| `classify_monkey_patch` | Function | Returns risk level for given signals |

### FindingSignals Dataclass

```python
@dataclass(frozen=True)
class FindingSignals:
    category: str      # Finding category from scanner
    is_test: bool      # Whether finding is in test code
    is_module_scope: bool  # Whether finding is at module scope
```

## Risk Classification Rules

| Category | Condition | Risk Level |
|----------|-----------|------------|
| `global_env_mutation` | Non-test + module scope | HIGH |
| `global_env_mutation` | Other | MODERATE |
| `sys_modules_assignment` | Non-test | HIGH |
| `sys_modules_assignment` | Test | MODERATE |
| `import_time_side_effect` | Non-test | HIGH |
| `import_time_side_effect` | Test | MODERATE |
| `builtins_mutation` | Non-test | HIGH |
| `builtins_mutation` | Test | MODERATE |
| `singleton_rebind` | Non-test | HIGH |
| `singleton_rebind` | Test | MODERATE |
| `attribute_reassignment_on_import` | Non-test | MODERATE |
| `attribute_reassignment_on_import` | Test | SAFE |
| `setattr_on_import_or_class` | Non-test | MODERATE |
| `setattr_on_import_or_class` | Test | SAFE |
| `test_patch_misuse` | Any | MODERATE |
| Other | Any | SAFE |

## Usage Pattern

```python
from utilities.monkey_patch_risk import (
    FindingSignals,
    classify_monkey_patch,
)

signals = FindingSignals(
    category="sys_modules_assignment",
    is_test=False,
    is_module_scope=True,
)
risk = classify_monkey_patch(signals)  # Returns "HIGH"
```

## Consumers

- `classify_monkey_patches.py` (consumer)
- `analyze_monkey_patch_trends.py` (aggregator)

## Notes

- Library module with no CLI interface
- Rules align with governance standard `std-global-monkey-patching.md`
- Part of the Monkey Patch Oversight pipeline (Stage 5.1)
