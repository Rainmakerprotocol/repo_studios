# generate_doc_index.py

**Status:** Live (database sink placeholder logged; no writes yet)

## Purpose

`generate_doc_index.py` emits a repo-wide inventory of Markdown documents so AI
agents and operators can locate content, follow cross-links, and understand
section structure without rescanning the filesystem. The producer normalises
H1/H2 headings, parses YAML front matter, gathers inline links, and captures a
short descriptive snippet for each document, packaging the results in JSON, a
Markdown bundle, and a standalone CSV export with mirrored data.

## Output Contract

- Timestamped run directories under `.repo_studios/reports/producer_reports/doc_index/`.
- Each run contains:
      - `doc_index.json` – canonical JSON payload.
      - `doc_index_bundle.md` – Markdown bundle with metadata frontmatter plus
            fenced JSON, YAML, and CSV sections. The file begins with
            `<!-- markdownlint-disable MD013 -->` and closes with
            `<!-- markdownlint-enable MD013 -->` so long descriptions and CSV rows
            can exceed standard line-length without failing lint.
      - `doc_index.csv` – flattened export containing the expanded metadata
            columns described below.
- Latest pointers (`latest_doc_index.json`, `latest_doc_index_bundle.md`,
      `latest_doc_index.csv`) live
      alongside the run directories.
- Retention defaults to one run; older directories are pruned automatically
      (`--artifacts-to-keep` honours higher values when explicitly provided).
- When `--db-target` is supplied the run records a placeholder block describing
      the requested sink; no database writes are attempted.

## Data Shape

Each document entry includes:

- `folder`: directory relative to repo root (`.` for top-level files).
- `filename`: POSIX-style relative path to the Markdown file.
- `slug`: stable identifier derived from the lead H1 or the path.
- `h1_headings`: list of objects with `title`, `slug`, and `line` (1-based).
- `h2_headings`: list of objects with `title`, `slug`, `line`, `parent_title`,
      and `parent_slug` to preserve hierarchy.
- `links`: ordered, de-duplicated list of Markdown link targets discovered in
      the file (image links excluded by design).
- `description`: first qualifying paragraph after the lead H1 (trimmed to ~240
      characters, optional when no prose is available).
- `size_bytes`: file size at crawl time (integer).
- `modified_utc`: ISO 8601 timestamp for the last modification.
- `tags`: normalised list extracted from front matter (`tags` scalar or list).
- `owners`: normalised list extracted from common owner front matter keys.
- `status`: optional status string from front matter.
- `frontmatter`: sanitised dict preserving serialisable values (dates rendered
      as ISO strings, other unsupported types coerced to string).
- `contains_placeholder`: `true` when the document text includes the word
      “placeholder”.

CSV output columns are `folder`, `filename`, `level`, `heading`, `slug`,
`parent_slug`, `description`, `size_bytes`, `modified_utc`, `tags`, `owners`,
`status`, `contains_placeholder`, and `links`; each row repeats the document’s
link targets (semicolon-separated) so spreadsheet tooling can pivot on
cross-document references without reprocessing the JSON payload.

Payload metadata exposes summary counts, derived metrics (link density, missing
description totals, duplicate slug counts, directory distributions), advisory
previews (recent files missing descriptions/headings, placeholder hits, files
outside the docs tree), scanner exclusions, and an `outputs` block describing
file artifacts; the optional `outputs.database` node records placeholder sink
details when requested.

## CLI Reference

- `--repo-root`: override repository root discovery (defaults to script
      location depth traversal).
- `--output-dir`: alternate artifact directory (default:
      `.repo_studios/reports/producer_reports/doc_index`).
- `--artifacts-to-keep`: retention count (defaults to `1`).
- `--timestamp`: ISO-8601 timestamp override for deterministic tests.
- `--db-target`: optional database sink identifier. The script logs a warning
      and records placeholder metadata; integration will arrive in a future
      iteration.
- `--log-level`: standard logging verbosity flag.

## Implementation Summary

- Uses `build_standard_paths` / `build_standard_options` to resolve paths and
      retention counts.
- Traverses the repository while excluding generated/vendor directories such as
      `.venv/`, `node_modules/`, `dist/`, and `.repo_studios/reports/`.
- Normalises slugs via the shared `slugify` helper, captures heading line
      numbers, deduplicates inline links, and converts front matter into
      serialisable metadata (tags, owners, status, preserved dict snapshot).
- Generates JSON, YAML, and CSV renderings, embedding them in the Markdown
      bundle with frontmatter and guidance for agent consumers.
- Delegates artifact management to `write_report_artifacts`, maintaining latest
      pointers and pruning stale runs.
- Provides pytest coverage in
      `.repo_studios/tests/tests_producers/test_generate_doc_index.py` for crawling,
      extraction, retention pruning, and the database placeholder pathway.

## Notes for AI Consumers

- Prefer `doc_index.json` (or the JSON section in the bundle) for structured
      ingestion; YAML and CSV panels mirror the same dataset for human review or
      spreadsheet tooling.
- Use `slug` values to construct anchor-safe URLs and to join H2 rows with
      their parent headings.
- `outputs.database` advertises the requested target and explicitly states that
      no records were persisted when the sink is still a placeholder.
- Scanner metadata exposes the excluded directory names and prefixes so agents
      can mirror the same traversal rules when enriching the index downstream.
