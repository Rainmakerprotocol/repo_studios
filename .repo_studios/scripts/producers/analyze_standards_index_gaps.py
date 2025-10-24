#!/usr/bin/env python
"""Identify potential standards directives present in source markdown files but absent from the index.

Artifacts (default):
    - `.repo_studios/reports/producer_reports/standards_gap_reports/`
        - `standards_index_gap-<timestamp>/report.json`
        - `standards_index_gap-<timestamp>/report.md`
        - `standards_index_gap-<timestamp>/candidates.tsv`
        - `latest_report.(json|md|tsv)` pointers for quick review

Exit codes:
    0 success (gaps may or may not exist)
    2 parse / IO error (missing YAML inputs etc.)

Limitations:
    - Only scans bullet and numbered list imperatives; tables remain unsupported.
    - De-duplication is lexical and may surface similar directives across files.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INDEX_PATH = ROOT / "repo_standards_index.yaml"
DEFAULT_CATEGORIES_PATH = ROOT / ".repo_studios" / "standards_categories.yaml"
DEFAULT_OUTPUT_DIR = Path(
    ".repo_studios/reports/producer_reports/standards_gap_reports"
)
RUN_PREFIX = "standards_index_gap"

IMP_VERBS = re.compile(
    r"^(?:[-*]\s*|\d+\.\s*)?(?:avoid|ensure|prefer|use|never|do not|limit|prohibit|enforce|document|pin)\b",
    re.IGNORECASE,
)
STRIP_PREFIX = re.compile(r"^[-*]\s*|^\d+\.\s*")


@dataclass
class GapCandidate:
    line: int
    text: str

    def to_dict(self) -> dict[str, Any]:
        return {"line": self.line, "text": self.text}


def load_index(path: Path) -> dict[str, Any]:
    if not path.exists():
        logging.error("index file missing: %s", path)
        raise SystemExit(2)
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception as exc:  # pragma: no cover
        logging.exception("failed to parse index: %s", exc)
        raise SystemExit(2)
    if not isinstance(data, dict):
        logging.error("index payload must be a mapping: %s", path)
        raise SystemExit(2)
    return data


def load_sources(categories_path: Path) -> list[Path]:
    if not categories_path.exists():
        logging.error("categories file missing: %s", categories_path)
        raise SystemExit(2)
    try:
        data = yaml.safe_load(categories_path.read_text(encoding="utf-8")) or {}
    except Exception as exc:  # pragma: no cover
        logging.exception("failed to parse categories: %s", exc)
        raise SystemExit(2)
    sources: list[Path] = []
    for src in data.get("sources", []) or []:
        raw_path = src.get("path", "")
        if not raw_path:
            continue
        candidate = Path(raw_path)
        if not candidate.is_absolute():
            candidate = (ROOT / candidate).resolve()
        if candidate.exists():
            sources.append(candidate)
        else:
            logging.warning("source file listed but missing: %s", candidate)
    return sources


def build_existing_tokens(index: dict[str, Any]) -> set[str]:
    tokens: set[str] = set()
    for rule in index.get("rules", []) or []:
        summary = str(rule.get("summary", "")).lower()
        for word in re.findall(r"[a-zA-Z]{4,}", summary):
            tokens.add(word)
        rule_id = rule.get("id")
        if rule_id:
            tokens.add(str(rule_id).lower())
    return tokens


def scan_file(path: Path, existing_tokens: set[str]) -> list[GapCandidate]:
    results: list[GapCandidate] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except Exception as exc:  # pragma: no cover
        logging.warning("failed to read %s: %s", path, exc)
        return results
    for idx, raw in enumerate(lines, start=1):
        text = raw.strip()
        if not text or text.startswith("#"):
            continue
        if not IMP_VERBS.match(text):
            continue
        core = STRIP_PREFIX.sub("", text).lower()
        words = [w for w in re.findall(r"[a-zA-Z]{4,}", core) if w]
        if words and sum(1 for w in words if w in existing_tokens) / len(words) > 0.6:
            continue
        results.append(GapCandidate(line=idx, text=raw))
    return results


def run_gap_detection(index_path: Path, categories_path: Path) -> dict[str, list[GapCandidate]]:
    index = load_index(index_path)
    existing_tokens = build_existing_tokens(index)
    sources = load_sources(categories_path)
    gaps: dict[str, list[GapCandidate]] = {}
    for src in sources:
        candidates = scan_file(src, existing_tokens)
        if candidates:
            try:
                rel = str(src.relative_to(ROOT))
            except ValueError:
                rel = str(src)
            gaps[rel] = candidates
    return gaps


def build_report(
    *,
    gaps: dict[str, list[GapCandidate]],
    generated_ts: datetime,
    index_path: Path,
    categories_path: Path,
) -> dict[str, Any]:
    total_candidates = sum(len(items) for items in gaps.values())
    top_source_count = max((len(items) for items in gaps.values()), default=0)
    sorted_sources = {
        path: [cand.to_dict() for cand in items]
        for path, items in sorted(gaps.items())
    }
    summary = {
        "sources_with_candidates": len(gaps),
        "top_source_candidates": top_source_count,
        "total_candidates": total_candidates,
    }
    top_sources = [
        {"path": path, "candidate_count": len(items)}
        for path, items in sorted(
            gaps.items(), key=lambda item: (-len(item[1]), item[0])
        )
    ][:10]
    return {
        "schema_version": 1,
        "generated_utc": generated_ts.isoformat(),
        "index_path": str(index_path),
        "categories_path": str(categories_path),
        "summary": summary,
        "sources": sorted_sources,
        "top_sources": top_sources,
        "total_candidates": total_candidates,
    }


def write_markdown(report: dict[str, Any]) -> str:
    lines: list[str] = [
        "# Standards Index Gap Report",
        "",
        f"Generated (UTC): {report['generated_utc']}",
        f"Index Path: {report['index_path']}",
        f"Categories Path: {report['categories_path']}",
        "",
        "## Summary",
        "",
        f"* total candidates: {report['summary']['total_candidates']}",
        f"* sources with candidates: {report['summary']['sources_with_candidates']}",
        f"* top source candidate count: {report['summary']['top_source_candidates']}",
        "",
        "## Sources With Candidates",
        "",
    ]
    sources = report.get("sources", {})
    if not sources:
        lines.append("- (none)")
    else:
        for path, items in sources.items():
            lines.append(f"- **{path}** — {len(items)} candidate(s)")
            for candidate in items[:5]:
                snippet = (
                    candidate["text"]
                    .strip()
                    .replace("`", "'")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
                )
                lines.append(f"  - L{candidate['line']}: {snippet}")
            if len(items) > 5:
                lines.append(f"  - ... (+{len(items) - 5} more)")
    lines.append("")
    return "\n".join(lines) + "\n"


def write_candidates_tsv(report: dict[str, Any]) -> str:
    rows = ["source\tline\ttext"]
    for path, items in report.get("sources", {}).items():
        for candidate in items:
            text = candidate["text"].replace("\t", " ").replace("\n", " ")
            rows.append(f"{path}\t{candidate['line']}\t{text}")
    return "\n".join(rows) + "\n"


def write_artifacts(report: dict[str, Any], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    generated_ts = datetime.fromisoformat(report["generated_utc"])
    run_dir = output_dir / f"{RUN_PREFIX}-{generated_ts.strftime('%Y%m%d_%H%M%S')}"
    run_dir.mkdir(parents=True, exist_ok=True)

    json_path = run_dir / "report.json"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    md_path = run_dir / "report.md"
    md_path.write_text(write_markdown(report), encoding="utf-8")

    tsv_path = run_dir / "candidates.tsv"
    tsv_path.write_text(write_candidates_tsv(report), encoding="utf-8")

    latest_pairs = [
        (json_path, output_dir / "latest_report.json"),
        (md_path, output_dir / "latest_report.md"),
        (tsv_path, output_dir / "latest_candidates.tsv"),
    ]
    for src, dest in latest_pairs:
        try:
            if dest.exists():
                dest.unlink()
            dest.hardlink_to(src)
        except OSError:
            dest.write_bytes(src.read_bytes())
    return run_dir


def prune_old_runs(output_dir: Path, *, keep: int, current_run: Path) -> list[Path]:
    keep = max(keep, 1)
    if not output_dir.exists():
        return []
    candidates = [
        path
        for path in output_dir.iterdir()
        if path.is_dir() and path.name.startswith(f"{RUN_PREFIX}-")
    ]
    candidates.sort(key=lambda p: p.name, reverse=True)
    removed: list[Path] = []
    for idx, path in enumerate(candidates):
        if idx < keep or path == current_run:
            continue
        removed.append(path)
        for child in path.iterdir():
            if child.is_file():
                child.unlink(missing_ok=True)  # type: ignore[attr-defined]
        path.rmdir()
    return removed


def emit_runtime_log(logger: logging.Logger, report: dict[str, Any], *, max_show: int) -> None:
    sources = report.get("sources", {})
    if not sources:
        logger.info("No candidate gaps detected")
        return
    for path, items in sources.items():
        logger.info("%s: %d candidates", path, len(items))
        for item in items[:max_show]:
            logger.info("  L%4d | %s", item["line"], item["text"].strip())
        if len(items) > max_show:
            logger.info("  ... (+%d more)", len(items) - max_show)
    logger.info("Total candidate directives: %d", report.get("total_candidates", 0))


def _parse_timestamp(raw: str | None) -> datetime:
    if raw is None:
        return datetime.now(timezone.utc)
    try:
        return datetime.fromisoformat(raw)
    except ValueError as exc:  # pragma: no cover
        raise SystemExit(f"Invalid --timestamp value: {exc}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="standards_index_gap",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description=__doc__,
    )
    parser.add_argument("--json", dest="json_out", help="Write legacy JSON payload to this path")
    parser.add_argument(
        "--max",
        dest="max_show",
        type=int,
        default=8,
        help="Max candidates to display per source in console output",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory to store structured artifact runs",
    )
    parser.add_argument(
        "--artifacts-to-keep",
        type=int,
        default=10,
        help="Maximum number of timestamped runs to retain",
    )
    parser.add_argument(
        "--timestamp",
        help="Override run timestamp (ISO 8601) for reproducible tests",
    )
    parser.add_argument(
        "--index-path",
        type=Path,
        default=DEFAULT_INDEX_PATH,
        help="Override standards index path",
    )
    parser.add_argument(
        "--categories-path",
        type=Path,
        default=DEFAULT_CATEGORIES_PATH,
        help="Override standards categories mapping path",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO), format="%(levelname)s %(message)s")
    log = logging.getLogger("standards_index_gap")

    generated_ts = _parse_timestamp(args.timestamp)
    index_path = args.index_path.resolve()
    categories_path = args.categories_path.resolve()
    gaps = run_gap_detection(index_path, categories_path)
    report = build_report(
        gaps=gaps,
        generated_ts=generated_ts,
        index_path=index_path,
        categories_path=categories_path,
    )

    output_dir = args.output_dir.resolve()
    run_dir = write_artifacts(report, output_dir)
    pruned = prune_old_runs(output_dir, keep=args.artifacts_to_keep, current_run=run_dir)
    if pruned:
        log.info("Pruned %d old run(s)", len(pruned))

    emit_runtime_log(log, report, max_show=args.max_show)

    if args.json_out:
        Path(args.json_out).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        log.info("Wrote legacy JSON payload: %s", args.json_out)

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
