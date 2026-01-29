"""Documentation Index Producer.

Scans the entire repository (minus generated or vendor directories) to build a
structured inventory of Markdown documents. Each run produces a JSON payload and
an accompanying Markdown bundle that embeds JSON, YAML, and CSV renderings for
downstream automation while preserving a lightweight placeholder for a future
database sink.
"""

import argparse
import csv
import importlib.util
import json
import logging
import re
import sys
import textwrap
import types
from collections import Counter, OrderedDict
from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from io import StringIO
from pathlib import Path
from typing import Any, Iterable, Sequence

import yaml

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
CODE_FENCE_RE = re.compile(r"^(```|~~~)")

TOPIC_SLUG = "doc_index"
VIEWER_SLUG = "producer_reports"

CHECKBOX_REPORT_SCRIPT = Path(
  ".repo_studios/docs/pipeline/checkbox_report/checkbox_report.py"
)
TIER3_INDEX_SCRIPT = Path(
  ".repo_studios/docs/pipeline/tier3_index/generate_tier3_index.py"
)

EXCLUDED_DIR_NAMES = {
  ".git",
  ".hg",
  ".svn",
  "__pycache__",
  ".mypy_cache",
  ".pytest_cache",
  ".venv",
  ".tox",
  "node_modules",
  "build",
  "dist",
}

EXCLUDED_PATH_PREFIXES = [
  (".repo_studios", "reports"),
  (".repo_studios", "command_center", "reports"),
]

GENERIC_DESCRIPTION_WIDTH = 240

LIBRARIES_ROOT = Path(__file__).resolve().parents[3] / ".repo_studios" / "command_center" / "scripts"

try:  # pragma: no cover - import guard for standalone execution
  from libraries import (
    KeepSpec,
    OptionsConfig,
    PathsConfig,
    PathSpec,
    build_standard_options,
    build_standard_paths,
  )
  from libraries.database_integration import create_storage
  from libraries.prune_logs import prune_run_directories
  from libraries.report_paths import build_topic_path
  from libraries.retention_policy import get_keep
except ModuleNotFoundError:  # pragma: no cover - fallback when script is run directly
  import sys

  if str(LIBRARIES_ROOT) not in sys.path:
    sys.path.insert(0, str(LIBRARIES_ROOT))
  from libraries import (
    KeepSpec,
    OptionsConfig,
    PathsConfig,
    PathSpec,
    build_standard_options,
    build_standard_paths,
  )
  from libraries.database_integration import create_storage
  from libraries.prune_logs import prune_run_directories
  from libraries.report_paths import build_topic_path
  from libraries.retention_policy import get_keep

DEFAULT_ARTIFACTS_TO_KEEP = get_keep("generate_doc_index")
DEFAULT_OUTPUT_DIR = build_topic_path("producer", TOPIC_SLUG)


@dataclass(frozen=True)
class Paths:
  """Resolved filesystem paths for the doc index producer.

  Attributes:
    repo_root: Repository root directory.
    output_dir: Directory for output artifacts.
  """

  repo_root: Path
  output_dir: Path


@dataclass(frozen=True)
class Options:
  """Runtime options for the doc index producer.

  Attributes:
    artifacts_to_keep: Number of historical run directories to retain.
  """

  artifacts_to_keep: int


@dataclass(frozen=True)
class Heading:
  """Represents an H1 heading extracted from a Markdown document.

  Attributes:
    title: Raw heading text.
    slug: URL-friendly slug derived from title.
    line: 1-based line number where heading appears.
  """

  title: str
  slug: str
  line: int


@dataclass(frozen=True)
class SubHeading:
  """Represents an H2 heading extracted from a Markdown document.

  Attributes:
    title: Raw heading text.
    slug: URL-friendly slug derived from title.
    line: 1-based line number where heading appears.
    parent_title: Title of the parent H1 heading.
    parent_slug: Slug of the parent H1 heading.
  """

  title: str
  slug: str
  line: int
  parent_title: str
  parent_slug: str


@dataclass(frozen=True)
class DocumentRecord:
  """Metadata record for a single Markdown document.

  Attributes:
    folder: Parent folder path relative to repo root.
    filename: Full file path relative to repo root.
    slug: Document slug derived from first H1 or fallback.
    h1_headings: List of H1 headings in the document.
    h2_headings: List of H2 headings in the document.
    links: Unique link targets found in the document.
    description: Extracted first paragraph text, or None.
    size_bytes: File size in bytes.
    modified_utc: ISO 8601 timestamp of last modification.
    tags: Tags extracted from frontmatter.
    owners: Owner identifiers from frontmatter.
    status: Status field from frontmatter, or None.
    frontmatter: Sanitized frontmatter dictionary, or None.
    contains_placeholder: True if document contains placeholder text.
  """

  folder: str
  filename: str
  slug: str
  h1_headings: list[Heading]
  h2_headings: list[SubHeading]
  links: list[str]
  description: str | None
  size_bytes: int
  modified_utc: str
  tags: list[str]
  owners: list[str]
  status: str | None
  frontmatter: dict[str, Any] | None
  contains_placeholder: bool


PATH_SPECS: dict[str, PathSpec] = {
  "output_dir": PathSpec(
    field="output_dir",
    default=DEFAULT_OUTPUT_DIR,
    ensure_dir=True,
    within_repo=False,
  ),
}

PATH_CONFIG = PathsConfig(
  dataclass_type=Paths,
  path_specs=PATH_SPECS,
  repo_root_depth=4,
)

KEEP_SPECS: dict[str, KeepSpec] = {
  "artifacts_to_keep": KeepSpec(field="artifacts_to_keep", minimum=1),
}

OPTIONS_CONFIG = OptionsConfig(dataclass_type=Options, keep_specs=KEEP_SPECS)


def slugify(raw: str) -> str:
  """Convert raw text into a URL-friendly slug.

  Args:
    raw: Raw heading or title text.

  Returns:
    Lowercase slug with only alphanumeric characters and dashes.
  """
  text = raw.strip().lower()
  text = re.sub(r"`+", "", text)
  text = re.sub(r"[^a-z0-9\- ]", "", text)
  text = re.sub(r"\s+", "-", text)
  text = re.sub(r"-+", "-", text)
  return text.strip("-")


def _should_skip(relative_parts: Sequence[str]) -> bool:
  """Check if a path should be excluded from scanning.

  Args:
    relative_parts: Path components relative to repo root.

  Returns:
    True if the path matches any exclusion rule.
  """
  lowered = [part.lower() for part in relative_parts]
  excluded_names = {name.lower() for name in EXCLUDED_DIR_NAMES}
  if any(name in excluded_names for name in lowered):
    return True
  for prefix in EXCLUDED_PATH_PREFIXES:
    candidate = tuple(lowered[: len(prefix)])
    if candidate == tuple(part.lower() for part in prefix):
      return True
  return False


def iter_markdown_files(root: Path) -> Iterable[Path]:
  """Iterate over all Markdown files in the repository.

  Args:
    root: Repository root directory.

  Yields:
    Paths to Markdown files, excluding vendor and generated directories.
  """
  for path in sorted(root.rglob("*.md")):
    try:
      relative = path.relative_to(root)
    except ValueError:  # pragma: no cover - defensive
      continue
    if _should_skip(relative.parts):
      continue
    yield path


def _extract_description(lines: list[str], start_index: int) -> str | None:
  """Extract the first prose paragraph following a heading.

  Args:
    lines: Document lines.
    start_index: Line index to start scanning from.

  Returns:
    Truncated paragraph text, or None if no prose found.
  """
  in_code_block = False
  snippet: list[str] = []
  for raw in lines[start_index:]:
    stripped = raw.strip()
    if CODE_FENCE_RE.match(stripped):
      in_code_block = not in_code_block
      continue
    if in_code_block:
      continue
    if not stripped:
      if snippet:
        break
      continue
    if stripped.startswith(("#", "-", "*", "+", ">", "|", "<")):
      if snippet:
        break
      continue
    if stripped.startswith("!"):
      if snippet:
        break
      continue
    snippet.append(stripped)
  if not snippet:
    return None
  paragraph = " ".join(snippet)
  return textwrap.shorten(paragraph, width=GENERIC_DESCRIPTION_WIDTH, placeholder="…")


def _collect_links(text: str) -> list[str]:
  """Collect unique link targets from Markdown text.

  Args:
    text: Full document text.

  Returns:
    List of unique link targets in order of first appearance.
  """
  ordered: "OrderedDict[str, None]" = OrderedDict()
  for match in LINK_RE.finditer(text):
    target = match.group(1).strip()
    if target and target not in ordered:
      ordered[target] = None
  return list(ordered.keys())


def _fallback_slug(relative_str: str) -> str:
  """Generate a fallback slug when no H1 heading is present.

  Args:
    relative_str: Relative file path as a string.

  Returns:
    Slug derived from filename stem or path hash.
  """
  simplified = slugify(Path(relative_str).stem)
  if simplified:
    return simplified
  simplified = slugify(relative_str.replace("/", "-"))
  if simplified:
    return simplified
  return f"doc-{abs(hash(relative_str)) & 0xFFFFFFFF:08x}"


def _extract_frontmatter(lines: list[str]) -> tuple[dict[str, Any] | None, int]:
  """Parse YAML frontmatter from document lines.

  Args:
    lines: Document lines.

  Returns:
    Tuple of (parsed frontmatter dict or None, end line index).
  """
  if not lines or lines[0].strip() != "---":
    return None, 0
  buffer: list[str] = []
  end_index = 0
  for idx, line in enumerate(lines[1:], start=1):
    if line.strip() == "---":
      end_index = idx
      break
    buffer.append(line)
  if end_index == 0:
    return None, 0
  try:
    parsed = yaml.safe_load("\n".join(buffer))
  except yaml.YAMLError:
    return None, end_index
  return parsed if isinstance(parsed, dict) else None, end_index


def _sanitize_frontmatter(value: Any) -> Any:
  """Recursively sanitize frontmatter values for JSON serialization.

  Args:
    value: Frontmatter value (dict, list, or scalar).

  Returns:
    Sanitized value with dates converted to ISO format.
  """
  if isinstance(value, dict):
    return {str(key): _sanitize_frontmatter(val) for key, val in value.items()}
  if isinstance(value, list):
    return [_sanitize_frontmatter(item) for item in value]
  if isinstance(value, tuple):
    return [_sanitize_frontmatter(item) for item in value]
  if isinstance(value, (datetime, date)):
    return value.isoformat()
  if isinstance(value, (str, int, float, bool)) or value is None:
    return value
  return str(value)


def _normalize_tags(raw: Any) -> list[str]:
  """Normalize tags from frontmatter into a list of strings.

  Args:
    raw: Raw tags value from frontmatter.

  Returns:
    List of non-empty tag strings.
  """
  if raw is None:
    return []
  if isinstance(raw, str):
    value = raw.strip()
    return [value] if value else []
  if isinstance(raw, (list, tuple, set)):
    return [str(item).strip() for item in raw if str(item).strip()]
  return []


def _normalize_owners(frontmatter: dict[str, Any] | None) -> list[str]:
  """Extract owner identifiers from frontmatter.

  Args:
    frontmatter: Parsed frontmatter dictionary.

  Returns:
    List of owner strings from owners/maintainers fields.
  """
  if not frontmatter:
    return []
  for key in ("owners", "owner", "maintainers", "maintainer"):
    if key in frontmatter:
      value = frontmatter[key]
      if isinstance(value, str):
        stripped = value.strip()
        return [stripped] if stripped else []
      if isinstance(value, (list, tuple, set)):
        return [str(item).strip() for item in value if str(item).strip()]
  return []


def _normalize_status(frontmatter: dict[str, Any] | None) -> str | None:
  """Normalize the status field from frontmatter.

  Extract and strip the status value from document frontmatter.

  Args:
    frontmatter: Parsed frontmatter dictionary, or None.

  Returns:
    The stripped status string, or None if missing or empty.
  """
  if not frontmatter:
    return None
  value = frontmatter.get("status")
  if value is None:
    return None
  stripped = str(value).strip()
  return stripped or None


def parse_markdown_document(path: Path, repo_root: Path) -> DocumentRecord:
  """Parse a markdown file into a structured document record.

  Extract headings, frontmatter, links, and metadata from a markdown
  file and assemble a DocumentRecord with normalized fields.

  Args:
    path: Absolute path to the markdown file.
    repo_root: Repository root for computing relative paths.

  Returns:
    A DocumentRecord containing parsed structure and metadata.
  """
  text = path.read_text(encoding="utf-8", errors="replace")
  lines = text.splitlines()
  frontmatter, frontmatter_end = _extract_frontmatter(lines)
  frontmatter_dict = frontmatter if isinstance(frontmatter, dict) else None
  sanitized_frontmatter = _sanitize_frontmatter(frontmatter_dict) if frontmatter_dict else None
  h1_headings: list[Heading] = []
  h2_headings: list[SubHeading] = []
  in_code_block = False
  current_h1: tuple[str, str] | None = None
  description: str | None = None

  for index, raw_line in enumerate(lines):
    stripped = raw_line.strip()
    if CODE_FENCE_RE.match(stripped):
      in_code_block = not in_code_block
      continue
    if in_code_block:
      continue
    if frontmatter_end and index <= frontmatter_end:
      continue
    match = HEADING_RE.match(stripped)
    if not match:
      continue
    level = len(match.group(1))
    title = match.group(2).strip()
    if not title:
      continue
    slug = slugify(title)
    if level == 1:
      heading = Heading(title=title, slug=slug, line=index + 1)
      h1_headings.append(heading)
      current_h1 = (title, slug)
      if description is None:
        description = _extract_description(lines, index + 1)
    elif level == 2:
      parent_title, parent_slug = (current_h1 if current_h1 else ("", ""))
      sub_heading = SubHeading(
        title=title,
        slug=slug,
        line=index + 1,
        parent_title=parent_title,
        parent_slug=parent_slug,
      )
      h2_headings.append(sub_heading)

  relative_path = path.relative_to(repo_root)
  relative_str = relative_path.as_posix()
  folder = relative_path.parent.as_posix() if relative_path.parent.as_posix() else "."
  doc_slug = h1_headings[0].slug if h1_headings else _fallback_slug(relative_str)
  links = _collect_links(text)
  stat = path.stat()
  modified = datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat()
  tags = _normalize_tags(frontmatter_dict.get("tags") if frontmatter_dict else None)
  owners = _normalize_owners(frontmatter_dict)
  status = _normalize_status(frontmatter_dict)
  contains_placeholder = "placeholder" in text.lower()

  return DocumentRecord(
    folder=folder,
    filename=relative_str,
    slug=doc_slug,
    h1_headings=h1_headings,
    h2_headings=h2_headings,
    links=links,
    description=description,
    size_bytes=stat.st_size,
    modified_utc=modified,
    tags=tags,
    owners=owners,
    status=status,
    frontmatter=sanitized_frontmatter,
    contains_placeholder=contains_placeholder,
  )


def collect_documents(repo_root: Path) -> list[DocumentRecord]:
  """Collect and parse all markdown documents in the repository.

  Iterate through all markdown files, parse each into a DocumentRecord,
  and return the sorted collection.

  Args:
    repo_root: Repository root directory to scan.

  Returns:
    A list of DocumentRecord objects sorted by filename.
  """
  records: list[DocumentRecord] = []
  for path in iter_markdown_files(repo_root):
    records.append(parse_markdown_document(path, repo_root))
  records.sort(key=lambda record: record.filename)
  return records


def build_metrics(documents: Sequence[DocumentRecord]) -> tuple[dict[str, Any], dict[str, Any]]:
  """Compute health metrics and advisories from document records.

  Analyze the document collection to produce counts, densities, and
  advisory lists for missing descriptions, headings, duplicates, etc.

  Args:
    documents: Sequence of parsed DocumentRecord objects.

  Returns:
    A tuple of (metrics_dict, advisories_dict) with computed statistics.
  """
  total_documents = len(documents)
  counts_by_dir = Counter(doc.folder for doc in documents)
  top_directories = [
    {"directory": directory, "count": count}
    for directory, count in counts_by_dir.most_common(20)
  ]

  missing_description = sorted(doc.filename for doc in documents if not doc.description)
  missing_h1 = sorted(doc.filename for doc in documents if not doc.h1_headings)
  missing_h2 = sorted(
    doc.filename for doc in documents if doc.h1_headings and not doc.h2_headings
  )
  placeholder_docs = sorted(doc.filename for doc in documents if doc.contains_placeholder)
  outside_docs_tree = sorted(
    doc.filename
    for doc in documents
    if not (doc.filename.startswith("docs/") or doc.filename.startswith(".repo_studios/docs/"))
  )

  slug_map: dict[str, list[str]] = {}
  for doc in documents:
    slug_map.setdefault(doc.slug, []).append(doc.filename)
  duplicate_slugs = {slug: sorted(files) for slug, files in slug_map.items() if len(files) > 1}

  total_links = sum(len(doc.links) for doc in documents)
  link_density = total_links / total_documents if total_documents else 0.0

  metrics = {
    "documents_per_directory": top_directories,
    "documents_missing_description_count": len(missing_description),
    "documents_without_h1_count": len(missing_h1),
    "documents_without_h2_count": len(missing_h2),
    "placeholder_documents_count": len(placeholder_docs),
    "duplicate_slug_count": len(duplicate_slugs),
    "documents_outside_docs_tree_count": len(outside_docs_tree),
    "link_density": link_density,
  }

  advisories = {
    "documents_missing_description": missing_description[:25],
    "documents_without_h1": missing_h1[:25],
    "documents_without_h2": missing_h2[:25],
    "placeholder_documents": placeholder_docs[:25],
    "documents_outside_docs_tree": outside_docs_tree[:25],
    "duplicate_slugs": {slug: files[:10] for slug, files in list(duplicate_slugs.items())[:10]},
  }

  return metrics, advisories


def build_database_placeholder(target: str) -> dict[str, Any]:
  """Build a placeholder record for database output.

  Create a stub dictionary indicating that database persistence was
  requested but not yet implemented.

  Args:
    target: The database target identifier.

  Returns:
    A dictionary with placeholder status and target information.
  """
  return {
    "target": target,
    "status": "pending",
    "implemented": False,
    "note": "Database sink placeholder; no data persisted during this run.",
  }


def build_payload(
  *,
  documents: Sequence[DocumentRecord],
  generated_ts: datetime,
  repo_root: Path,
  database_placeholder: dict[str, Any] | None,
) -> dict[str, Any]:
  """Build the complete JSON payload for the documentation index.

  Assemble documents, metrics, advisories, and scanner configuration
  into a structured payload suitable for serialization.

  Args:
    documents: Parsed document records to include.
    generated_ts: Timestamp when the index was generated.
    repo_root: Repository root directory.
    database_placeholder: Optional database placeholder record.

  Returns:
    A dictionary containing the full index payload.
  """
  doc_dicts = [asdict(doc) for doc in documents]
  total_h1 = sum(len(doc.h1_headings) for doc in documents)
  total_h2 = sum(len(doc.h2_headings) for doc in documents)
  total_links = sum(len(doc.links) for doc in documents)
  metrics, advisories = build_metrics(documents)
  summary = {
    "total_documents": len(documents),
    "total_h1": total_h1,
    "total_h2": total_h2,
    "total_headings": total_h1 + total_h2,
    "total_links": total_links,
  }
  payload: dict[str, Any] = {
    "schema_version": 1,
    "generated_utc": generated_ts.isoformat(),
    "repo_root": str(repo_root),
    "summary": summary,
    "metrics": metrics,
    "advisories": advisories,
    "documents": doc_dicts,
    "outputs": {
      "files": {
        "manifest": "manifest.json",
        "summary": "summary.md",
        "telemetry": "telemetry.json",
        "csv": "doc_index.csv",
      }
    },
    "scanner": {
      "excluded_names": sorted(EXCLUDED_DIR_NAMES),
      "excluded_prefixes": ["/".join(prefix) for prefix in EXCLUDED_PATH_PREFIXES],
    },
  }
  if database_placeholder is not None:
    payload["outputs"]["database"] = database_placeholder
  return payload


def build_csv(documents: Sequence[DocumentRecord]) -> str:
  """Build a CSV representation of document headings.

  Create a CSV string with one row per heading, including metadata
  such as folder, level, slug, and description.

  Args:
    documents: Sequence of parsed DocumentRecord objects.

  Returns:
    A CSV-formatted string with header row and data rows.
  """
  buffer = StringIO()
  writer = csv.writer(buffer, lineterminator="\n")
  writer.writerow([
    "folder",
    "filename",
    "level",
    "heading",
    "slug",
    "parent_slug",
    "description",
    "size_bytes",
    "modified_utc",
    "tags",
    "owners",
    "status",
    "contains_placeholder",
    "links",
  ])
  for doc in documents:
    description = doc.description or ""
    links_value = ";".join(doc.links)
    tags_value = ";".join(doc.tags)
    owners_value = ";".join(doc.owners)
    status_value = doc.status or ""
    placeholder_value = "yes" if doc.contains_placeholder else "no"
    if doc.h1_headings or doc.h2_headings:
      for heading in doc.h1_headings:
        writer.writerow(
          [
            doc.folder,
            doc.filename,
            "h1",
            heading.title,
            heading.slug,
            "",
            description,
            doc.size_bytes,
            doc.modified_utc,
            tags_value,
            owners_value,
            status_value,
            placeholder_value,
            links_value,
          ]
        )
      for sub_heading in doc.h2_headings:
        writer.writerow(
          [
            doc.folder,
            doc.filename,
            "h2",
            sub_heading.title,
            sub_heading.slug,
            sub_heading.parent_slug,
            description,
            doc.size_bytes,
            doc.modified_utc,
            tags_value,
            owners_value,
            status_value,
            placeholder_value,
            links_value,
          ]
        )
    else:
      writer.writerow([
        doc.folder,
        doc.filename,
        "document",
        "",
        doc.slug,
        "",
        description,
        doc.size_bytes,
        doc.modified_utc,
        tags_value,
        owners_value,
        status_value,
        placeholder_value,
        links_value,
      ])
  return buffer.getvalue().strip()


def render_bundle(
  *,
  payload: dict[str, Any],
  json_text: str,
  yaml_text: str,
  csv_text: str,
) -> str:
  """Render the complete markdown bundle from index artifacts.

  Combine JSON, YAML, and CSV representations with summary metrics
  and advisories into a single markdown document.

  Args:
    payload: The full index payload dictionary.
    json_text: Serialized JSON representation.
    yaml_text: Serialized YAML representation.
    csv_text: CSV-formatted heading data.

  Returns:
    A markdown string containing the complete documentation bundle.
  """
  summary = payload.get("summary", {})
  metrics = payload.get("metrics", {})
  advisories = payload.get("advisories", {})

  def preview_list(values: Sequence[str]) -> str:
    if not values:
      return "none"
    limited = list(values[:5])
    text = ", ".join(limited)
    if len(values) > 5:
      text += ", …"
    return text

  bundle_lines: list[str] = [
    "---",
    f"schema_version: {payload['schema_version']}",
    f"generated_utc: {payload['generated_utc']}",
    f"total_documents: {summary.get('total_documents', 0)}",
    f"total_headings: {summary.get('total_headings', 0)}",
    f"total_links: {summary.get('total_links', 0)}",
    "---",
    "",
    "<!-- markdownlint-disable MD013 -->",
    "# Documentation Index Bundle",
    "",
    "## Guidance",
    "",
    "- Prefer the JSON section for machine ingestion; YAML mirrors the same payload for readability.",
    "- The CSV section lists every heading row for spreadsheet-style analyses.",
  ]
  if "database" in payload.get("outputs", {}):
    bundle_lines.append(
      "- A database target was requested; this run recorded a placeholder only (no records persisted)."
    )
  bundle_lines.extend(
    [
      "",
      "## Summary",
      "",
      f"- documents: {summary.get('total_documents', 0)}",
      f"- h1 headings: {summary.get('total_h1', 0)}",
      f"- h2 headings: {summary.get('total_h2', 0)}",
      f"- links: {summary.get('total_links', 0)}",
      "",
      "## Metrics",
      "",
      f"- link density: {metrics.get('link_density', 0):.3f}",
      f"- duplicate slug groups: {metrics.get('duplicate_slug_count', 0)}",
      f"- placeholder documents: {metrics.get('placeholder_documents_count', 0)}",
      f"- documents outside docs tree: {metrics.get('documents_outside_docs_tree_count', 0)}",
    ]
  )
  top_directories = metrics.get("documents_per_directory", [])
  if top_directories:
    preview = ", ".join(f"{entry['directory']} ({entry['count']})" for entry in top_directories[:5])
    bundle_lines.append(f"- top directories: {preview}")
  bundle_lines.extend(
    [
      "- see JSON section for full metric payload.",
      "",
      "## Advisories",
      "",
      f"- documents missing description: {preview_list(advisories.get('documents_missing_description', []))}",
      f"- documents without h1: {preview_list(advisories.get('documents_without_h1', []))}",
      f"- documents without h2: {preview_list(advisories.get('documents_without_h2', []))}",
      f"- placeholder documents: {preview_list(advisories.get('placeholder_documents', []))}",
      f"- documents outside docs tree: {preview_list(advisories.get('documents_outside_docs_tree', []))}",
    ]
  )
  duplicate_preview = advisories.get("duplicate_slugs", {})
  if isinstance(duplicate_preview, dict):
    duplicate_count = len(duplicate_preview)
    samples = list(duplicate_preview.items())[:3]
    if samples:
      rendered = "; ".join(f"{slug} ({len(files)} files)" for slug, files in samples)
      bundle_lines.append(f"- duplicate slugs: {duplicate_count} groups; examples: {rendered}")
    else:
      bundle_lines.append("- duplicate slugs: none detected")
  bundle_lines.extend(
    [
      "- see JSON section for full advisory payload.",
      "",
      "## JSON",
      "",
      "```json",
      json_text.strip(),
      "```",
      "",
      "## YAML",
      "",
      "```yaml",
      yaml_text.strip(),
      "```",
      "",
      "## CSV",
      "",
      "```csv",
      csv_text.strip(),
      "```",
      "",
    ]
  )
  bundle_lines.append("<!-- markdownlint-enable MD013 -->")
  return "\n".join(bundle_lines).rstrip() + "\n"


def _parse_timestamp(raw: str | None) -> datetime:
  """Parse a timestamp string or return current UTC time.

  Convert an ISO 8601 timestamp string to a datetime object, or
  return the current UTC time if no value is provided.

  Args:
    raw: ISO 8601 timestamp string, or None.

  Returns:
    A timezone-aware datetime object.

  Raises:
    SystemExit: If the timestamp string is malformed.
  """
  if raw is None:
    return datetime.now(timezone.utc)
  try:
    return datetime.fromisoformat(raw)
  except ValueError as exc:  # pragma: no cover - validated via CLI
    raise SystemExit(f"Invalid --timestamp value: {exc}") from None


def handle_database_placeholder(target: str, logger: logging.Logger) -> None:
  """Log a warning that database integration is not yet implemented.

  Emit a warning message indicating the database output was requested
  but the sink integration is pending.

  Args:
    target: The database target identifier.
    logger: Logger instance for emitting the warning.
  """
  logger.warning(
    "Database output target requested (%s) but sink integration is not yet implemented. Skipping.",
    target,
  )


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
  """Parse command-line arguments for the documentation index generator.

  Configure and parse CLI arguments including repo root, output directory,
  artifact retention, timestamp override, and database target options.

  Args:
    argv: Command-line arguments to parse, or None for sys.argv.

  Returns:
    A Namespace object with parsed argument values.
  """
  parser = argparse.ArgumentParser(description="Generate documentation index artifacts")
  parser.add_argument("--repo-root", help="Repository root override (defaults to script-relative resolution)")
  parser.add_argument(
    "--output-dir",
    type=Path,
    default=DEFAULT_OUTPUT_DIR,
    help="Base reports directory for positional bundles",
  )
  parser.add_argument("--artifacts-to-keep", type=int, default=DEFAULT_ARTIFACTS_TO_KEEP)
  parser.add_argument("--timestamp", help="Override run timestamp (ISO 8601)")
  parser.add_argument(
    "--db-target",
    type=str,
    default=None,
    help="Optional database sink identifier (placeholder only; no writes performed)",
  )
  parser.add_argument(
    "--refresh-checkbox-report",
    action="store_true",
    help="Regenerate docs/pipeline checkbox report artifacts before indexing",
  )
  parser.add_argument(
    "--refresh-tier3-index",
    action="store_true",
    help="Regenerate docs/pipeline tier3 scripts index before indexing",
  )
  parser.add_argument(
    "--log-level",
    default="INFO",
    choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
  )
  return parser.parse_args(argv)


def _load_module_from_path(path: Path, module_name: str) -> types.ModuleType:
  """Dynamically load a Python module from a file path.

  Import a module by its file path, registering it in sys.modules
  under the specified name.

  Args:
    path: Absolute path to the Python file.
    module_name: Name to assign the module in sys.modules.

  Returns:
    The loaded module object.

  Raises:
    RuntimeError: If the module specification cannot be loaded.
  """
  spec = importlib.util.spec_from_file_location(module_name, path)
  if spec is None or spec.loader is None:
    raise RuntimeError(f"Unable to load module spec for {path}")
  module = importlib.util.module_from_spec(spec)
  sys.modules[module_name] = module
  spec.loader.exec_module(module)
  return module


def _refresh_checkbox_report(repo_root: Path, logger: logging.Logger) -> None:
  """Regenerate the checkbox report before indexing.

  Dynamically load and execute the checkbox_report script to ensure
  the pipeline checkbox artifacts are current.

  Args:
    repo_root: Repository root directory.
    logger: Logger instance for status messages.

  Raises:
    RuntimeError: If the script is missing or lacks a main entrypoint.
  """
  script_path = repo_root / CHECKBOX_REPORT_SCRIPT
  if not script_path.exists():
    raise RuntimeError(f"checkbox_report.py not found at {script_path}")

  module = _load_module_from_path(script_path, "repo_studios_checkbox_report")
  if not hasattr(module, "main"):
    raise RuntimeError("checkbox_report.py missing main(argv) entrypoint")

  output_dir = repo_root / ".repo_studios/docs/pipeline/checkbox_report/outputs"
  search_dir = repo_root / ".repo_studios/docs/pipeline"

  logger.info("Refreshing checkbox report: %s", output_dir)
  module.main(
    [
      "--repo-root",
      str(repo_root),
      "--output-dir",
      str(output_dir),
      "--search-dir",
      str(search_dir),
    ]
  )


def _refresh_tier3_index(repo_root: Path, logger: logging.Logger, log_level: str) -> None:
  """Regenerate the tier-3 scripts index before indexing.

  Dynamically load and execute the generate_tier3_index script to
  ensure the scripts index is current.

  Args:
    repo_root: Repository root directory.
    logger: Logger instance for status messages.
    log_level: Log level to pass to the child script.

  Raises:
    RuntimeError: If the script is missing, lacks a run entrypoint,
      or returns a non-zero exit code.
  """
  script_path = repo_root / TIER3_INDEX_SCRIPT
  if not script_path.exists():
    raise RuntimeError(f"generate_tier3_index.py not found at {script_path}")

  module = _load_module_from_path(script_path, "repo_studios_generate_tier3_index")
  if not hasattr(module, "run"):
    raise RuntimeError("generate_tier3_index.py missing run(argv) entrypoint")

  logger.info("Refreshing tier3 scripts index")
  exit_code = module.run(
    [
      "--repo-root",
      str(repo_root),
      "--log-level",
      log_level,
    ]
  )
  if exit_code != 0:
    raise RuntimeError(f"generate_tier3_index returned exit code {exit_code}")


def run(argv: Sequence[str] | None = None) -> dict[str, Any]:
  """Execute the documentation index generator.

  Parse arguments, collect documents, compute metrics, and write
  index artifacts including manifest, summary, and telemetry files.

  Args:
    argv: Command-line arguments to parse, or None for sys.argv.

  Returns:
    A dictionary with run metadata including output directory, slug,
    artifact paths, and document counts.

  Raises:
    SystemExit: If the repository root does not exist.
  """
  args = parse_args(argv)
  logging.basicConfig(
    level=getattr(logging, args.log_level.upper(), logging.INFO),
    format="%(levelname)s %(message)s",
    force=True,
  )
  logger = logging.getLogger("doc_index")

  paths = build_standard_paths(args, PATH_CONFIG, origin=Path(__file__))
  options = build_standard_options(args, OPTIONS_CONFIG)

  repo_root = paths.repo_root
  if not repo_root.exists():
    raise SystemExit(f"repo root not found: {repo_root}")

  if args.refresh_checkbox_report:
    _refresh_checkbox_report(repo_root, logger)
  if args.refresh_tier3_index:
    _refresh_tier3_index(repo_root, logger, args.log_level)

  records = collect_documents(repo_root)
  generated_ts = _parse_timestamp(args.timestamp)

  database_placeholder = build_database_placeholder(args.db_target) if args.db_target else None

  payload = build_payload(
    documents=records,
    generated_ts=generated_ts,
    repo_root=repo_root,
    database_placeholder=database_placeholder,
  )

  json_text = json.dumps(payload, indent=2, sort_keys=True)
  yaml_text = yaml.safe_dump(payload, sort_keys=False)
  csv_text = build_csv(records)
  bundle_text = render_bundle(payload=payload, json_text=json_text, yaml_text=yaml_text, csv_text=csv_text)

  timestamp_slug = generated_ts.strftime("%Y%m%d-%H%M")

  manifest = {
    "schema_version": 1,
    "viewer_slug": "producer_reports",
    "topic": TOPIC_SLUG,
    "run_timestamp": timestamp_slug,
    "generated_utc": generated_ts.isoformat(),
    "status": "ok",
    "catalog": ["scripts.docs.generate_doc_index"],
    "inputs": {
      "repo_root": str(repo_root),
      "output_dir": str(paths.output_dir),
      "artifacts_to_keep": options.artifacts_to_keep,
      "db_target": args.db_target,
      "excluded_names": sorted(EXCLUDED_DIR_NAMES),
      "excluded_prefixes": ["/".join(prefix) for prefix in EXCLUDED_PATH_PREFIXES],
      "description_width": GENERIC_DESCRIPTION_WIDTH,
    },
    "artifacts": [
      {"name": "manifest.json", "role": "manifest"},
      {"name": "summary.md", "role": "summary"},
      {"name": "telemetry.json", "role": "telemetry"},
      {"name": "doc_index.csv", "role": "csv"},
    ],
  }

  summary = payload.get("summary", {})
  metrics_block = payload.get("metrics", {})
  telemetry = {
    "schema_version": 1,
    "viewer_slug": "producer_reports",
    "topic": TOPIC_SLUG,
    "run_timestamp": timestamp_slug,
    "generated_utc": payload.get("generated_utc"),
    "status": "ok",
    "metrics": {
      "total_documents": summary.get("total_documents"),
      "total_headings": summary.get("total_headings"),
      "total_links": summary.get("total_links"),
      "duplicate_slug_count": metrics_block.get("duplicate_slug_count"),
      "documents_missing_description_count": metrics_block.get("documents_missing_description_count"),
      "placeholder_documents_count": metrics_block.get("placeholder_documents_count"),
      "link_density": metrics_block.get("link_density"),
    },
    "payload": payload,
  }

  storage = create_storage(
    output_dir=paths.output_dir,
    viewer_slug="",  # output_dir already contains full topic path
    topic="",  # output_dir already contains full topic path
    timestamp=timestamp_slug,
  )

  # DB_INTEGRATION_MARKER: write manifest.json (report_runs)
  storage.write_manifest(manifest)
  # DB_INTEGRATION_MARKER: write summary.md (report_summaries)
  storage.write_summary({"markdown": bundle_text}, format="markdown")
  # DB_INTEGRATION_MARKER: write telemetry.json + extracted metrics (test_metrics)
  storage.write_telemetry(telemetry)

  # Human-facing artifact: doc_index.csv (no DB integration required).
  csv_path = storage.file_storage.bundle_dir / "doc_index.csv"
  csv_path.write_text(csv_text.rstrip("\n") + "\n", encoding="utf-8")

  run_dir = storage.file_storage.bundle_dir
  # output_dir already contains full topic path - prune directly from it
  prune_result = prune_run_directories(
    paths.output_dir,
    keep=options.artifacts_to_keep,
    current_run=run_dir,
    logger=logger,
  )
  logger.debug(
    "Pruned doc index bundles: kept=%s removed=%s protected=%s failures=%s",
    len(prune_result.kept),
    len(prune_result.removed),
    len(prune_result.protected),
    len(prune_result.failures),
  )

  if database_placeholder is not None:
    handle_database_placeholder(args.db_target, logger)

  summary = payload["summary"]
  logger.info(
    "Indexed %d documents (%d headings, %d links)",
    summary["total_documents"],
    summary["total_headings"],
    summary["total_links"],
  )

  return {
    "status": "ok",
    "exit_code": 0,
    "run_dir": str(run_dir),
    "output_dir": str(paths.output_dir),
    "run_id": timestamp_slug,
    "slug": timestamp_slug,  # Alias for backward compatibility
    "manifest": manifest,
    "telemetry": telemetry,
    "summary": {
      "total_documents": summary["total_documents"],
      "total_headings": summary["total_headings"],
      "total_links": summary["total_links"],
    },
    "artifacts": {
      "manifest.json": str(run_dir / "manifest.json"),
      "summary.md": str(run_dir / "summary.md"),
      "telemetry.json": str(run_dir / "telemetry.json"),
      "doc_index.csv": str(run_dir / "doc_index.csv"),
    },
    "documents": summary["total_documents"],
    "headings": summary["total_headings"],
    "links": summary["total_links"],
    "database_placeholder": database_placeholder,
  }


def main(argv: Sequence[str] | None = None) -> int:
  """CLI entrypoint for the documentation index generator.

  Execute the documentation index workflow and return an exit code.

  Args:
    argv: Command-line arguments to parse, or None for sys.argv.

  Returns:
    Exit code 0 on success.
  """
  run(argv)
  return 0


if __name__ == "__main__":  # pragma: no cover
  raise SystemExit(main())
