# DB Integration: Fault Run Analysis Utility

## Script Identity

- **Script**: `fault_run_analysis.py`
- **Path**: `.repo_studios/scripts/utilities/fault_run_analysis.py`
- **Category**: Utility (shared helpers)
- **Planned Stage**: 3.2

## Purpose

Shared helpers for faulthandler run analysis. Centralizes logic for parsing faulthandler stack dumps so both producer and consumer scripts can reuse the same data model.

## I/O Contract

This is a **library module**, not a standalone CLI script.

### Exports

| Export | Type | Description |
|--------|------|-------------|
| `FaultSignature` | Dataclass | Aggregated signature for a distinct stack fingerprint |
| `FaultAnalysisResult` | Dataclass | Structured payload from build_fault_report |
| `DEFAULT_TOP_N` | Constant | Default top-N value (10) |
| `THREAD_HEADER_RE` | Regex | Pattern for thread headers |
| `FRAME_RE` | Regex | Pattern for stack frames |
| `ensure_manifest` | Function | Ensure manifest exists |
| `read_stacks_text` | Function | Read stack dump text |
| `collect_signatures` | Function | Collect unique stack signatures |
| `build_fault_report` | Function | Build structured fault report |

### FaultSignature Dataclass

```python
@dataclass
class FaultSignature:
    signature_id: str
    count: int
    top_module: str
    top_func: str
    top_file: str
    top_line: int
    threads: list[str]
    first_seen_ts: str
    last_seen_ts: str
```

### FaultAnalysisResult Dataclass

```python
@dataclass
class FaultAnalysisResult:
    report: dict[str, object]
    signatures: list[FaultSignature]
    combined_text: str
```

## Consumers

- `generate_fault_artifacts.py` (consumer)
- `summarize_fault_diagnostics_overview.py` (summarizer)

## Notes

- Library module with no CLI interface
- Centralizes stack dump parsing logic
- Avoids divergent heuristics across producer/consumer scripts
- Planned for Stage 3.2 (not yet integrated into orchestrator)
