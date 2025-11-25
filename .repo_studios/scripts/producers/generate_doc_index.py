"""Documentation Index Producer.

Scans the entire repository (minus generated or vendor directories) to build a
structured inventory of Markdown documents. Each run produces a JSON payload and
an accompanying Markdown bundle that embeds JSON, YAML, and CSV renderings for
downstream automation while preserving a lightweight placeholder for a future
database sink.
"""

import argparse
import csv
import json
import logging
import re
import textwrap
from collections import OrderedDict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
from typing import Any, Iterable, Sequence

import yaml

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
CODE_FENCE_RE = re.compile(r"^(```|~~~)")

DEFAULT_OUTPUT_DIR = Path(".repo_studios/reports/producer_reports/doc_index")
RUN_PREFIX = "doc_index"
DEFAULT_ARTIFACTS_TO_KEEP = 1

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
  from libraries import (  # type: ignore import
    KeepSpec,
    OptionsConfig,
    PathSpec,
    PathsConfig,
    build_standard_options,
    build_standard_paths,
  )
  from libraries.artifacts import ReportArtifact, write_report_artifacts  # type: ignore import
except ModuleNotFoundError:  # pragma: no cover - fallback when script is run directly
  import sys

  if str(LIBRARIES_ROOT) not in sys.path:
    sys.path.insert(0, str(LIBRARIES_ROOT))
  from libraries import (  # type: ignore import
    KeepSpec,
    OptionsConfig,
    PathSpec,
    PathsConfig,
    build_standard_options,
    build_standard_paths,
  )
  from libraries.artifacts import ReportArtifact, write_report_artifacts  # type: ignore import


@dataclass(frozen=True)
class Paths:
  repo_root: Path
  output_dir: Path


@dataclass(frozen=True)
class Options:
  artifacts_to_keep: int


@dataclass(frozen=True)
class Heading:
  title: str
  slug: str
  line: int


@dataclass(frozen=True)
class SubHeading:
  title: str
  slug: str
  line: int
  parent_title: str
  parent_slug: str


@dataclass(frozen=True)
class DocumentRecord:
  folder: str
  filename: str
  slug: str
  h1_headings: list[Heading]
  h2_headings: list[SubHeading]
  links: list[str]
  description: str | None


PATH_SPECS: dict[str, PathSpec] = {
  "output_dir": PathSpec(
    field="output_dir",
    default=DEFAULT_OUTPUT_DIR,
    ensure_dir=False,
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
  text = raw.strip().lower()
  text = re.sub(r"`+", "", text)
  text = re.sub(r"[^a-z0-9\- ]", "", text)
  text = re.sub(r"\s+", "-", text)
  text = re.sub(r"-+", "-", text)
  return text.strip("-")


def _should_skip(relative_parts: Sequence[str]) -> bool:
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
  for path in sorted(root.rglob("*.md")):
    try:
      relative = path.relative_to(root)
    except ValueError:  # pragma: no cover - defensive
      continue
    if _should_skip(relative.parts):
      continue
    yield path


def _extract_description(lines: list[str], start_index: int) -> str | None:
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
  ordered = OrderedDict()
  for match in LINK_RE.finditer(text):
    target = match.group(1).strip()
    if target and target not in ordered:
      ordered[target] = None
  return list(ordered.keys())


def _fallback_slug(relative_str: str) -> str:
  simplified = slugify(Path(relative_str).stem)
  if simplified:
    return simplified
  simplified = slugify(relative_str.replace("/", "-"))
  if simplified:
    return simplified
  return f"doc-{abs(hash(relative_str)) & 0xFFFFFFFF:08x}"


def parse_markdown_document(path: Path, repo_root: Path) -> DocumentRecord:
  text = path.read_text(encoding="utf-8", errors="replace")
  lines = text.splitlines()
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

  return DocumentRecord(
    folder=folder,
    filename=relative_str,
    slug=doc_slug,
    h1_headings=h1_headings,
    h2_headings=h2_headings,
    links=links,
    description=description,
  )


def collect_documents(repo_root: Path) -> list[DocumentRecord]:
  records: list[DocumentRecord] = []
  for path in iter_markdown_files(repo_root):
    records.append(parse_markdown_document(path, repo_root))
  records.sort(key=lambda record: record.filename)
  return records


def build_database_placeholder(target: str) -> dict[str, Any]:
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
  doc_dicts = [asdict(doc) for doc in documents]
  total_h1 = sum(len(doc.h1_headings) for doc in documents)
  total_h2 = sum(len(doc.h2_headings) for doc in documents)
  total_links = sum(len(doc.links) for doc in documents)
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
    "documents": doc_dicts,
    "outputs": {
      "files": {
        "bundle": "doc_index_bundle.md",
        "json": "doc_index.json",
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
  buffer = StringIO()
  writer = csv.writer(buffer)
  writer.writerow(["folder", "filename", "level", "heading", "slug", "parent_slug", "description"])
  for doc in documents:
    description = doc.description or ""
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
          ]
        )
      for heading in doc.h2_headings:
        writer.writerow(
          [
            doc.folder,
            doc.filename,
            "h2",
            heading.title,
            heading.slug,
            heading.parent_slug,
            description,
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
      ])
  return buffer.getvalue().strip()


def render_bundle(
  *,
  payload: dict[str, Any],
  json_text: str,
  yaml_text: str,
  csv_text: str,
) -> str:
  summary = payload.get("summary", {})
  bundle_lines: list[str] = [
    "---",
    f"schema_version: {payload['schema_version']}",
    f"generated_utc: {payload['generated_utc']}",
    f"total_documents: {summary.get('total_documents', 0)}",
    f"total_headings: {summary.get('total_headings', 0)}",
    f"total_links: {summary.get('total_links', 0)}",
    "---",
    "",
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
  return "\n".join(bundle_lines).rstrip() + "\n"


def _parse_timestamp(raw: str | None) -> datetime:
  if raw is None:
    return datetime.now(timezone.utc)
  try:
    return datetime.fromisoformat(raw)
  except ValueError as exc:  # pragma: no cover - validated via CLI
    raise SystemExit(f"Invalid --timestamp value: {exc}")


def handle_database_placeholder(target: str, logger: logging.Logger) -> None:
  logger.warning(
    "Database output target requested (%s) but sink integration is not yet implemented. Skipping.",
    target,
  )


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
  parser = argparse.ArgumentParser(description="Generate documentation index artifacts")
  parser.add_argument("--repo-root", help="Repository root override (defaults to script-relative resolution)")
  parser.add_argument(
    "--output-dir",
    type=Path,
    default=DEFAULT_OUTPUT_DIR,
    help="Directory for documentation index artifacts",
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
    "--log-level",
    default="INFO",
    choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
  )
  return parser.parse_args(argv)


def run(argv: Sequence[str] | None = None) -> dict[str, Any]:
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

  artifacts = [
    ReportArtifact(
      filename="doc_index.json",
      pointer="latest_doc_index.json",
      kind="json",
      content=payload,
      sort_keys=False,
    ),
    ReportArtifact(
      filename="doc_index_bundle.md",
      pointer="latest_doc_index_bundle.md",
      kind="text",
      content=bundle_text,
    ),
  ]

  result = write_report_artifacts(
    stem=RUN_PREFIX,
    timestamp=generated_ts,
    output_dir=paths.output_dir,
    artifacts=artifacts,
    keep=options.artifacts_to_keep,
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
    "run_dir": str(result.run_dir),
    "slug": result.slug,
    "artifacts": {name: str(path) for name, path in result.artifacts.items()},
    "documents": summary["total_documents"],
    "headings": summary["total_headings"],
    "links": summary["total_links"],
    "database_placeholder": database_placeholder,
  }


def main(argv: Sequence[str] | None = None) -> int:
  run(argv)
  return 0


if __name__ == "__main__":  # pragma: no cover
  raise SystemExit(main())
