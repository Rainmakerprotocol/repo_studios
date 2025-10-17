# Typecheck Report Contract
# Typecheck Report Contract

Date: 2025-09-19

# Typecheck Report Contract
Status: Draft (Phase 1 — Contract Defined)

Phase/Step: Health Suite — Typecheck Integration

## Purpose

Define a stable, minimal contract for typecheck artifacts so they can be produced by a script,
consumed by the Health Suite summary composer, and archived consistently across runs.

## Outputs

Artifacts are written per-run under a timestamped directory:

* `.repo_studios/typecheck/<timestamp>/report.md` — Human-readable summary
* `.repo_studios/typecheck/<timestamp>/report.json` — Machine-friendly results
* `.repo_studios/typecheck/<timestamp>/raw.txt` — Raw mypy output (optional)

Notes

* `timestamp` follows the orchestrator format: `YYYY-MM-DD_HHMM`
* The producing script should never raise on failure; encode status in JSON/MD and exit 0
	(tolerant health-suite semantics)

## JSON Schema (Minimal + Stable)

This is the required baseline. Producers may include additional optional fields; consumers should
ignore unknown keys.

Required fields

* `status`: "OK" | "ERROR"
* `mypy_version`: string
* `checked_paths`: list[string]
* `total_errors`: int (>= 0)
* `files_with_issues`: int (>= 0)
* `error_samples`: list[ErrorSample] (up to N entries, e.g., 20–50)

ErrorSample

* `path`: string (file path, relative to repo root when possible)
* `line`: int (>= 1)
* `code`: string (mypy error code or category, for example, `arg-type`)
* `message`: string (single-line, trimmed)

Optional fields (recommended)

* `invocation`: list[string] — argv used for the run
* `timestamp`: string — run timestamp (`YYYY-MM-DD_HHMM`)
* `duration_sec`: number — wall time seconds
* `summary`: string — brief sentence summarizing the run

Authoritative schema

* See `report.schema.json` alongside this document for a JSON Schema (Draft 2020-12) representation.

## Markdown Report (report.md)

Content layout (exact wording can vary; structure should be stable):

1) Title + timestamp

* Example: `# Typecheck Report — 2025-09-19_1340`

2) Summary bullets

* mypy version
* total errors
* files with issues
* checked paths (compact list or first N)

3) Top issues (first 20 lines)

* Render a compact list from `error_samples` (truncate at 20 entries)
* Format: `- path:line — [code] message`

4) How to reproduce

* Either reference `make typecheck` or print the exact command used (argv) to re-run locally.

Example skeleton

```
# Typecheck Report — <timestamp>


## Top Issues (up to 20)
	variable has type "Y")
## Paths & Discovery

	by picking the lexicographically last folder name.

## Exit Codes & Tolerance
* Failures are signaled in `report.json` and reflected in `report.md`; this keeps the health-suite
	tolerant.

## Environment Overrides (for later phases)

* `TYPECHECK_TARGETS`: space-separated custom target paths (overrides defaults)
* `HEALTH_TYPECHECK_FAST=1`: enable a curated, fast target set
* `TYPECHECK_STRICT=1`: opt into stricter mypy flags

## Backwards Compatibility

* New optional fields can be added to `report.json`; consumers must ignore unknown keys.
* Required fields and their semantics are stable.

# Typecheck Report Contract
Date: 2025-09-19
Status: Draft (Phase 1 — Contract Defined)
Phase/Step: Health Suite — Typecheck Integration

## Purpose
Define a stable, minimal contract for typecheck artifacts so they can be produced by a script, consumed by the Health Suite summary composer, and archived consistently across runs.

## Outputs
Artifacts are written per-run under a timestamped directory:
- .repo_studios/typecheck/<timestamp>/report.md — Human-readable summary
- .repo_studios/typecheck/<timestamp>/report.json — Machine-friendly results
- .repo_studios/typecheck/<timestamp>/raw.txt — Raw mypy output (optional)

Notes
- <timestamp> follows the orchestrator format: YYYY-MM-DD_HHMM
- The producing script should never raise on failure; encode status in JSON/MD and exit 0 (tolerant health-suite semantics)

## JSON Schema (Minimal + Stable)
This is the required baseline. Producers may include additional optional fields; consumers should ignore unknown keys.

Required fields
- status: "OK" | "ERROR"
- mypy_version: string
- checked_paths: list[string]
- total_errors: int (>= 0)
- files_with_issues: int (>= 0)
- error_samples: list[ErrorSample] (up to N entries, e.g., 20–50)

ErrorSample
- path: string (file path, relative to repo root when possible)
- line: int (>= 1)
- code: string (mypy error code or category, e.g., "arg-type")
- message: string (single-line, trimmed)

Optional fields (recommended)
- invocation: list[string] — argv used for the run
- timestamp: string — run timestamp (YYYY-MM-DD_HHMM)
- duration_sec: number — wall time seconds
- summary: string — brief sentence summarizing the run

Authoritative schema
- See report.schema.json alongside this document for a JSON Schema (Draft 2020-12) representation.

## Markdown Report (report.md)
Content layout (exact wording can vary; structure should be stable):

1) Title + timestamp
- Example: "# Typecheck Report — 2025-09-19_1340"

2) Summary bullets
- mypy version
- total errors
- files with issues
- checked paths (compact list or first N)

3) Top issues (first 20 lines)
- Render a compact list from error_samples (truncate at 20 entries)
- Format: "- path:line — [code] message"

4) How to reproduce
- Either reference "make typecheck" or print the exact command used (argv) to re-run locally.

Example skeleton

# Typecheck Report — <timestamp>

- mypy: <mypy_version>
- total errors: <total_errors>
- files with issues: <files_with_issues>
- checked paths: <p1> <p2> ...

## Top Issues (up to 20)
- path/to/file.py:123 — [arg-type] Incompatible types in assignment (expression has type "X", variable has type "Y")
- ...

## How to Reproduce
- make typecheck
- or run: <invocation joined by spaces>

## Paths & Discovery
- The Health Suite Summary will discover the latest typecheck run from .repo_studios/typecheck/ by picking the lexicographically last folder name.
- If no report is present, the summary should display "(missing)" for the Typecheck section.

## Exit Codes & Tolerance
- The producing script must exit 0 even when errors are detected (status = "ERROR").
- Failures are signaled in report.json and reflected in report.md; this keeps the health-suite tolerant.

## Environment Overrides (for later phases)
- TYPECHECK_TARGETS: space-separated custom target paths (overrides defaults)
- HEALTH_TYPECHECK_FAST=1: enable a curated, fast target set
- TYPECHECK_STRICT=1: opt into stricter mypy flags

## Backwards Compatibility
- New optional fields can be added to report.json; consumers must ignore unknown keys.
- Required fields and their semantics are stable.
