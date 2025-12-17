#!/usr/bin/env python3
"""Detect functions and classes lacking docstrings across repo automation code."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence
import ast

SCRIPTS_ROOT = Path(__file__).resolve().parents[1]
if str(SCRIPTS_ROOT) not in sys.path:  # pragma: no cover - import path bootstrap
    sys.path.insert(0, str(SCRIPTS_ROOT))

from utilities.anchor_inventory_loader import load_anchor_inventory  # noqa: E402

logger = logging.getLogger(__name__)

DEFAULT_OUTPUT_DIR = Path(
    ".repo_studios/reports/producer_reports/undocumented_logic_reports"
)
DEFAULT_ARTIFACTS_TO_KEEP = 5
RUN_PREFIX = "undocumented_logic"

LIBRARIES_ROOT = Path(__file__).resolve().parents[3] / ".repo_studios" / "command_center" / "scripts"

try:  # pragma: no cover - import guard when executed via package
    from libraries import (
        KeepSpec,
        OptionsConfig,
        PathSpec,
        PathsConfig,
        ReportArtifact,
        build_standard_options,
        build_standard_paths,
        write_report_artifacts,
    )
except ModuleNotFoundError:  # pragma: no cover - fallback for direct execution
    import sys

    if str(LIBRARIES_ROOT) not in sys.path:
        sys.path.insert(0, str(LIBRARIES_ROOT))
    from libraries import (  # type: ignore
        KeepSpec,
        OptionsConfig,
        PathSpec,
        PathsConfig,
        ReportArtifact,
        build_standard_options,
        build_standard_paths,
        write_report_artifacts,
    )


@dataclass(frozen=True)
class Paths:
    repo_root: Path
    output_dir: Path
    doc_index: Path
    anchor_inventory: Path
    allowlist: Path


@dataclass(frozen=True)
class Options:
    artifacts_to_keep: int


PATH_CONFIG = PathsConfig(
    dataclass_type=Paths,
    path_specs={
        "output_dir": PathSpec(
            field="output_dir",
            default=DEFAULT_OUTPUT_DIR,
            ensure_dir=True,
            within_repo=True,
        ),
        "doc_index": PathSpec(
            field="doc_index",
            default=Path(
                ".repo_studios/reports/producer_reports/healthview/doc_index"
            ),
            ensure_dir=False,
            within_repo=True,
        ),
        "anchor_inventory": PathSpec(
            field="anchor_inventory",
            default=Path(
                ".repo_studios/reports/producer_reports/healthview/anchor_inventory"
            ),
            ensure_dir=False,
            within_repo=True,
        ),
        "allowlist": PathSpec(
            field="allowlist",
            default=Path(
                ".repo_studios/config/undocumented_logic_allowlist.txt"
            ),
            ensure_dir=False,
            within_repo=True,
        ),
    },
    repo_root_depth=4,
)

OPTIONS_CONFIG = OptionsConfig(
    dataclass_type=Options,
    keep_specs={"artifacts_to_keep": KeepSpec(field="artifacts_to_keep", minimum=1)},
)


@dataclass
class EntityFinding:
    kind: str
    name: str
    qualified_name: str
    line: int
    reason: str


@dataclass
class ModuleScan:
    module_path: str
    module_name: str
    total_entities: int
    findings: list[EntityFinding] = field(default_factory=list)

    def coverage(self) -> float | None:
        if self.total_entities == 0:
            return None
        documented = self.total_entities - len(self.findings)
        return documented / self.total_entities * 100.0


Allowlist = dict[str, set[str]]


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__ or "")
    parser.add_argument("--repo-root", help="Repository root override")
    parser.add_argument("--output-dir", help="Directory for report artifacts")
    parser.add_argument("--doc-index", help="Path to latest doc index JSON")
    parser.add_argument(
        "--anchor-inventory",
        help="Path to anchor inventory input (canonical topic/bundle dir or legacy report.json)",
    )
    parser.add_argument("--allowlist", help="File listing modules or entities to skip")
    parser.add_argument(
        "--code-root",
        action="append",
        help="Code root to scan. Can be supplied multiple times.",
    )
    parser.add_argument(
        "--include-command-center",
        action="store_true",
        help="Scan .repo_studios/command_center/scripts in addition to other roots.",
    )
    parser.add_argument(
        "--artifacts-to-keep",
        type=int,
        default=DEFAULT_ARTIFACTS_TO_KEEP,
        help="Retention count for timestamped runs",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    )
    return parser.parse_args(argv)


def _configure_logging(level: str) -> None:
    logging.basicConfig(level=getattr(logging, level.upper()), format="%(levelname)s %(message)s")


def _read_allowlist(path: Path) -> Allowlist:
    if not path.exists():
        return {}
    entries: Allowlist = {}
    text = path.read_text(encoding="utf-8", errors="ignore")
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        if "::" in line:
            module_key, entity_key = line.split("::", 1)
        else:
            module_key, entity_key = line, "*"
        entities = entries.setdefault(module_key.strip(), set())
        entities.add(entity_key.strip() or "*")
    return entries


def _is_private(name: str) -> bool:
    return name.startswith("_") and not name.startswith("__init__")


def _should_skip(module_key: str, qualified_name: str, allowlist: Allowlist) -> bool:
    module_entries = allowlist.get(module_key)
    if module_entries and ("*" in module_entries or qualified_name in module_entries):
        return True
    return False


def _iter_code_files(code_roots: list[Path]) -> Iterable[Path]:
    seen: set[Path] = set()
    for root in code_roots:
        if not root.exists():
            continue
        for path in root.rglob("*.py"):
            if any(part == "__pycache__" for part in path.parts):
                continue
            if path in seen:
                continue
            seen.add(path)
            yield path


def _module_key(path: Path, repo_root: Path) -> str:
    return path.relative_to(repo_root).as_posix()


def _module_name(path: Path, repo_root: Path) -> str:
    relative = path.relative_to(repo_root).with_suffix("")
    return ".".join(part for part in relative.parts if part)


def _get_docstring(node: ast.AST) -> str | None:
    doc = ast.get_docstring(node, clean=False)
    if doc is None:
        return None
    stripped = doc.strip()
    return stripped if stripped else None


def _scan_ast(path: Path, repo_root: Path, allowlist: Allowlist) -> ModuleScan | None:
    try:
        source = path.read_text(encoding="utf-8")
    except OSError:
        logging.warning("Failed to read %s", path)
        return None
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        logging.warning("Failed to parse %s: %s", path, exc)
        return None

    module_key = _module_key(path, repo_root)
    module_name = _module_name(path, repo_root)
    findings: list[EntityFinding] = []
    total_entities = 0

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if _is_private(node.name):
                continue
            total_entities += 1
            qualified = f"{module_name}.{node.name}" if module_name else node.name
            if _should_skip(module_key, qualified, allowlist):
                continue
            if _get_docstring(node) is None:
                findings.append(
                    EntityFinding(
                        kind="function",
                        name=node.name,
                        qualified_name=qualified,
                        line=getattr(node, "lineno", 0),
                        reason="missing docstring",
                    )
                )
        elif isinstance(node, ast.ClassDef):
            if _is_private(node.name):
                continue
            total_entities += 1
            class_qualified = f"{module_name}.{node.name}" if module_name else node.name
            if _should_skip(module_key, class_qualified, allowlist):
                continue
            if _get_docstring(node) is None:
                findings.append(
                    EntityFinding(
                        kind="class",
                        name=node.name,
                        qualified_name=class_qualified,
                        line=getattr(node, "lineno", 0),
                        reason="missing docstring",
                    )
                )
            for body_item in node.body:
                if isinstance(body_item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if _is_private(body_item.name):
                        continue
                    total_entities += 1
                    method_qualified = f"{class_qualified}.{body_item.name}"
                    if _should_skip(module_key, method_qualified, allowlist):
                        continue
                    if _get_docstring(body_item) is None:
                        findings.append(
                            EntityFinding(
                                kind="method",
                                name=f"{node.name}.{body_item.name}",
                                qualified_name=method_qualified,
                                line=getattr(body_item, "lineno", 0),
                                reason="missing docstring",
                            )
                        )

    return ModuleScan(
        module_path=module_key,
        module_name=module_name,
        total_entities=total_entities,
        findings=findings,
    )


def _latest_run_dir(topic_dir: Path) -> Path | None:
    if not topic_dir.exists() or not topic_dir.is_dir():
        return None
    runs = [node for node in topic_dir.iterdir() if node.is_dir()]
    if not runs:
        return None
    runs.sort(key=lambda node: (node.name, node.stat().st_mtime), reverse=True)
    return runs[0]


def _load_json(path: Path) -> Any | None:
    if not path.exists():
        return None

    candidate = path
    if candidate.is_dir():
        latest = _latest_run_dir(candidate)
        if latest is None:
            return None
        telemetry_path = latest / "telemetry.json"
        if not telemetry_path.exists():
            return None
        candidate = telemetry_path

    try:
        data = json.loads(candidate.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        logging.warning("Failed to parse JSON from %s: %s", candidate, exc)
        return None

    if isinstance(data, dict) and "payload" in data:
        return data.get("payload")
    return data


def _build_doc_lookup(doc_index: Any) -> list[dict[str, Any]]:
    if not isinstance(doc_index, dict):
        return []
    docs = doc_index.get("documents")
    if not isinstance(docs, list):
        return []
    filtered: list[dict[str, Any]] = []
    for doc in docs:
        if isinstance(doc, dict):
            filtered.append(doc)
    return filtered


def _normalize_doc_path(path: str) -> str:
    return Path(path).as_posix()


def _build_anchor_lookup(anchor_inventory: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(anchor_inventory, dict):
        return {}
    docs = anchor_inventory.get("documents")
    if not isinstance(docs, list):
        return {}
    lookup: dict[str, dict[str, Any]] = {}
    for entry in docs:
        if not isinstance(entry, dict):
            continue
        path = entry.get("path")
        if not isinstance(path, str):
            continue
        lookup[_normalize_doc_path(path)] = entry
    return lookup


def _score_doc_candidate(module_base: str, doc: dict[str, Any]) -> tuple[int, str]:
    filename = str(doc.get("filename") or doc.get("path") or "")
    slug = str(doc.get("slug") or "")
    name_score = 2
    if filename:
        stem = Path(filename).stem
        if stem == module_base:
            name_score = 0
        elif module_base in stem:
            name_score = 1
    slug_score = 0 if module_base.replace("_", "-") in slug else 1
    return name_score + slug_score, filename


def _doc_candidates_for_module(
    module_path: str,
    doc_index: list[dict[str, Any]],
    anchor_lookup: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    module_base = Path(module_path).stem
    matches: list[tuple[int, dict[str, Any]]] = []
    for doc in doc_index:
        score, _ = _score_doc_candidate(module_base, doc)
        if score <= 3:
            matches.append((score, doc))
    matches.sort(key=lambda item: item[0])
    results: list[dict[str, Any]] = []
    for score, doc in matches[:5]:
        path_value = _normalize_doc_path(str(doc.get("filename") or doc.get("path") or ""))
        anchors = anchor_lookup.get(path_value, {})
        results.append(
            {
                "path": path_value,
                "owners": doc.get("owners", []),
                "score": score,
                "slug": doc.get("slug"),
                "anchor_count": len((anchors.get("slug_counts") or {}).keys()),
            }
        )
    return results


def _summarize(scans: list[ModuleScan]) -> dict[str, Any]:
    modules_scanned = len(scans)
    modules_with_findings = sum(1 for scan in scans if scan.findings)
    total_entities = sum(scan.total_entities for scan in scans)
    findings_count = sum(len(scan.findings) for scan in scans)
    if total_entities:
        coverage = (total_entities - findings_count) / total_entities * 100.0
    else:
        coverage = None
    return {
        "modules_scanned": modules_scanned,
        "modules_with_findings": modules_with_findings,
        "entities_scanned": total_entities,
        "entities_missing_docs": findings_count,
        "docstring_coverage_percent": round(coverage, 2) if coverage is not None else None,
    }


def _build_report(
    *,
    scans: list[ModuleScan],
    doc_index: list[dict[str, Any]],
    anchor_lookup: dict[str, dict[str, Any]],
    repo_root: Path,
    generated_ts: datetime,
    doc_index_path: Path,
    anchor_inventory_path: Path,
    code_roots: list[Path],
) -> dict[str, Any]:
    summary = _summarize(scans)
    modules_payload: list[dict[str, Any]] = []
    for scan in scans:
        coverage = scan.coverage()
        modules_payload.append(
            {
                "module_path": scan.module_path,
                "module_name": scan.module_name,
                "total_entities": scan.total_entities,
                "findings": [finding.__dict__ for finding in scan.findings],
                "coverage_percent": round(coverage, 2) if coverage is not None else None,
                "doc_candidates": _doc_candidates_for_module(
                    scan.module_path, doc_index, anchor_lookup
                ),
            }
        )
    modules_payload.sort(key=lambda item: (-len(item["findings"]), item["module_path"]))
    return {
        "schema_version": 1,
        "generated_utc": generated_ts.isoformat(),
        "repo_root": str(repo_root),
        "summary": summary,
        "modules": modules_payload,
        "doc_index_path": str(doc_index_path) if doc_index_path.exists() else None,
        "anchor_inventory_path": str(anchor_inventory_path) if anchor_inventory_path.exists() else None,
        "code_roots": [str(root) for root in code_roots],
    }


def _render_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary", {})
    lines = ["# Undocumented Logic Report", ""]
    lines.append("## Summary")
    lines.append("")
    lines.append(
        f"- Modules scanned: {summary.get('modules_scanned', 0)}"
    )
    lines.append(
        f"- Modules with findings: {summary.get('modules_with_findings', 0)}"
    )
    lines.append(
        f"- Entities scanned: {summary.get('entities_scanned', 0)}"
    )
    lines.append(
        f"- Entities missing docs: {summary.get('entities_missing_docs', 0)}"
    )
    coverage = summary.get("docstring_coverage_percent")
    coverage_str = f"{coverage:.2f}%" if isinstance(coverage, (int, float)) else "n/a"
    lines.append(f"- Docstring coverage: {coverage_str}")
    lines.append("")

    modules = report.get("modules", [])
    if not modules:
        lines.append("No undocumented logic detected.")
        return "\n".join(lines) + "\n"

    lines.append("## Modules With Undocumented Logic")
    lines.append("")
    lines.append("<!-- markdownlint-disable MD013 -->")
    for module in modules:
        findings = module.get("findings", [])
        if not findings:
            continue
        coverage_val = module.get("coverage_percent")
        coverage_display = (
            f"{coverage_val:.2f}%" if isinstance(coverage_val, (int, float)) else "n/a"
        )
        lines.append(
            f"- `{module['module_path']}` — missing {len(findings)} of {module.get('total_entities', 0)}"
            f" entities (coverage {coverage_display})."
        )
        candidates = module.get("doc_candidates", [])
        if candidates:
            lines.append("  - Doc candidates:")
            for candidate in candidates:
                owners = candidate.get("owners") or []
                owners_display = ", ".join(owners) if owners else "(unassigned)"
                slug_display = candidate.get("slug") or "n/a"
                lines.append(
                    f"    - `{candidate.get('path')}` (slug: {slug_display}, anchors: {candidate.get('anchor_count')}, owners: {owners_display})"
                )
        for finding in findings:
            lines.append(
                f"  - {finding['kind']} `{finding['qualified_name']}` line {finding['line']}"
                f" — {finding['reason']}"
            )
    lines.append("<!-- markdownlint-enable MD013 -->")
    return "\n".join(lines) + "\n"


def _render_tsv(modules: list[dict[str, Any]]) -> str:
    rows = ["module\tentity_type\tqualified_name\tline\treason"]
    for module in modules:
        for finding in module.get("findings", []):
            rows.append(
                "\t".join(
                    [
                        module.get("module_path", ""),
                        finding.get("kind", ""),
                        finding.get("qualified_name", ""),
                        str(finding.get("line", "")),
                        finding.get("reason", ""),
                    ]
                )
            )
    return "\n".join(rows)


def _bundle_summary(report: dict[str, Any]) -> dict[str, Any]:
    summary = report.get("summary", {})
    return {
        "modules_scanned": summary.get("modules_scanned", 0),
        "modules_with_findings": summary.get("modules_with_findings", 0),
        "entities_missing_docs": summary.get("entities_missing_docs", 0),
        "docstring_coverage_percent": summary.get("docstring_coverage_percent"),
    }


def run(argv: Sequence[str] | None = None) -> dict[str, Any]:
    args = parse_args(argv)
    _configure_logging(args.log_level)

    paths = build_standard_paths(args, PATH_CONFIG, origin=Path(__file__))
    options = build_standard_options(args, OPTIONS_CONFIG)

    allowlist = _read_allowlist(paths.allowlist)

    code_roots: list[Path] = []
    default_root = paths.repo_root / ".repo_studios" / "scripts"
    code_roots.append(default_root)
    if args.include_command_center:
        code_roots.append(paths.repo_root / ".repo_studios" / "command_center" / "scripts")
    if args.code_root:
        for raw in args.code_root:
            candidate = Path(raw)
            if not candidate.is_absolute():
                candidate = (paths.repo_root / raw).resolve()
            code_roots.append(candidate)
    # Deduplicate while preserving order
    seen: set[str] = set()
    normalized_roots: list[Path] = []
    for root in code_roots:
        key = str(root.resolve())
        if key in seen:
            continue
        seen.add(key)
        normalized_roots.append(root)
    code_roots = normalized_roots

    scans: list[ModuleScan] = []
    for path in _iter_code_files(code_roots):
        scan = _scan_ast(path, paths.repo_root, allowlist)
        if scan is None:
            continue
        scans.append(scan)

    doc_index_raw = _load_json(paths.doc_index)
    anchor_inventory_raw, anchor_inventory_path = load_anchor_inventory(paths.anchor_inventory, logger=logger)
    if anchor_inventory_raw is None:
        anchor_inventory_raw = {}
    doc_index = _build_doc_lookup(doc_index_raw)
    anchor_lookup = _build_anchor_lookup(anchor_inventory_raw)

    generated_ts = datetime.now(timezone.utc)
    report = _build_report(
        scans=scans,
        doc_index=doc_index,
        anchor_lookup=anchor_lookup,
        repo_root=paths.repo_root,
        generated_ts=generated_ts,
        doc_index_path=paths.doc_index,
        anchor_inventory_path=anchor_inventory_path or paths.anchor_inventory,
        code_roots=code_roots,
    )

    markdown = _render_markdown(report)
    tsv = _render_tsv(report.get("modules", [])) + "\n"
    bundle_summary = json.dumps(_bundle_summary(report), indent=2, sort_keys=True) + "\n"

    artifacts = [
        ReportArtifact(
            filename="report.json",
            pointer="latest_report.json",
            kind="json",
            content=report,
        ),
        ReportArtifact(
            filename="report.md",
            pointer="latest_report.md",
            kind="text",
            content=markdown,
        ),
        ReportArtifact(
            filename="undocumented.tsv",
            pointer="latest_undocumented.tsv",
            kind="text",
            content=tsv,
        ),
        ReportArtifact(
            filename="bundle_summary.json",
            pointer="latest_bundle_summary.json",
            kind="text",
            content=bundle_summary,
        ),
    ]

    write_result = write_report_artifacts(
        stem=RUN_PREFIX,
        timestamp=generated_ts,
        output_dir=paths.output_dir,
        artifacts=artifacts,
        keep=options.artifacts_to_keep,
    )

    summary = report.get("summary", {})
    logging.info(
        "Modules with undocumented logic: %s", summary.get("modules_with_findings", 0)
    )

    return {
        "run_dir": str(write_result.run_dir),
        "artifacts": {name: str(path) for name, path in write_result.artifacts.items()},
        "summary": summary,
    }


def main(argv: Sequence[str] | None = None) -> int:
    run(argv)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
