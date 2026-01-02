# DB Integration: Test Log Analysis Library

## Script Identity

- **Script**: `test_log_analysis.py`
- **Path**: `.repo_studios/command_center/scripts/libraries/test_log_analysis.py`
- **Category**: Library (shared helpers)

## Purpose

Shared helpers for analyzing pytest log bundles. Provides data models and parsers for test health metrics, warnings, and slow test analysis.

## I/O Contract

This is a **library module**, not a standalone CLI script.

### Exports

| Export | Type | Description |
|--------|------|-------------|
| `TestHealth` | Dataclass | Test execution health metrics |
| `TestLogAnalysisResult` | Dataclass | Analysis result with report and markdown |
| `select_junit_artifact` | Function | Select JUnit XML artifact |
| `select_full_log` | Function | Select full log file |
| `build_test_log_report` | Function | Build structured test log report |
| `render_markdown` | Function | Render analysis to markdown |

### TestHealth Dataclass

```python
@dataclass
class TestHealth:
    total: int = 0
    passed: int = 0
    skipped: int = 0
    xfailed: int = 0
    failed: int = 0
    errors: int = 0
```

### TestLogAnalysisResult Dataclass

```python
@dataclass
class TestLogAnalysisResult:
    report: dict[str, Any]
    markdown: str
```

## Parsing Capabilities

### Warnings Extraction

Regex pattern: `^(?P<path>[^:]+):\d+:\s*(?P<type>[A-Za-z]+Warning):\s*(?P<msg>.*)$`

### Slow Tests Extraction

Regex pattern: `^(?P<secs>\d+\.\d+)s\s+call\s+(?P<node>\S+)\s*$`

### JUnit XML Parsing

Uses `defusedxml.ElementTree` when available, falls back to `xml.etree.ElementTree`.

Extracts:
- Total tests
- Failures
- Errors
- Skipped (including xfailed detection)

## Consumers

- `generate_test_log_health_report.py` (consumer)
- `summarize_test_execution_telemetry.py` (summarizer)

## Dependencies

- Optional: `defusedxml` (for safer XML parsing)

## Notes

- Library module with no CLI interface
- Centralizes pytest log analysis logic
- Supports JUnit XML and raw log parsing
