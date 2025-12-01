from __future__ import annotations

import json
from pathlib import Path

from command_center.scripts.orchestrators import run_standards_integrity as orchestrator


def _arg_value(argv: list[str], option: str, default: Path) -> Path:
    if option in argv:
        try:
            return Path(argv[argv.index(option) + 1])
        except (ValueError, IndexError):  # pragma: no cover - defensive fallback
            return default
    return default


def test_orchestrator_emits_healthview_bundle(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[4]

    index_output_dir = tmp_path / "index"
    gap_output_dir = tmp_path / "gap"
    diff_output_dir = tmp_path / "diff"
    prompt_output_dir = tmp_path / "prompts"
    healthview_root = tmp_path / "healthview"
    pending_path = tmp_path / "pending.yaml"
    pending_path.write_text("- item: test\n", encoding="utf-8")

    categories_path = (
        repo_root / ".repo_studios/scripts/.repo_studios/standards_categories.yaml"
    )

    original_loader = orchestrator._load_callable

    def _fake_loader(script_path: Path, module_name: str, attribute: str):
        resolved = script_path.resolve()

        if resolved == (repo_root / orchestrator.GENERATE_SCRIPT).resolve():
            def _fake_generate(argv: list[str] | None = None) -> int:
                argv = argv or []
                output_dir = _arg_value(argv, "--output-dir", index_output_dir)
                index_path = _arg_value(argv, "--index-path", index_output_dir / "latest_index.yaml")
                output_dir.mkdir(parents=True, exist_ok=True)
                slug = "20240102_120000"
                run_dir = output_dir / f"{orchestrator.INDEX_RUN_PREFIX}{slug}"
                run_dir.mkdir(parents=True, exist_ok=True)
                (run_dir / "report.json").write_text(
                    json.dumps({"summary": {"rule_count": 123}, "status": "ok"}),
                    encoding="utf-8",
                )
                latest_payload = {
                    "timestamp": slug,
                    "status": "ok",
                    "summary": {"rule_count": 123},
                    "integrity_hash": "hash-123",
                }
                (output_dir / "latest_report.json").write_text(
                    json.dumps(latest_payload),
                    encoding="utf-8",
                )
                index_path.parent.mkdir(parents=True, exist_ok=True)
                index_path.write_text("rules: []\n", encoding="utf-8")
                return 0

            return _fake_generate

        if resolved == (repo_root / orchestrator.GAP_SCRIPT).resolve():
            def _fake_gap(argv: list[str] | None = None) -> dict[str, object]:
                argv = argv or []
                output_dir = _arg_value(argv, "--output-dir", gap_output_dir)
                output_dir.mkdir(parents=True, exist_ok=True)
                run_dir = output_dir / "standards_gap-20240102_120000"
                run_dir.mkdir(parents=True, exist_ok=True)
                report_path = run_dir / "report.json"
                report_path.write_text(json.dumps({"summary": {"total_candidates": 3}}), encoding="utf-8")
                bundle_summary = run_dir / "bundle_summary.json"
                bundle_summary.write_text(json.dumps({"sources_with_candidates": 2}), encoding="utf-8")
                return {
                    "run_dir": str(run_dir),
                    "report_json": str(report_path),
                    "bundle_summary": str(bundle_summary),
                    "summary": {"total_candidates": 3, "sources_with_candidates": 2},
                }

            return _fake_gap

        if resolved == (repo_root / orchestrator.PROMPT_SCRIPT).resolve():
            def _fake_prompt(argv: list[str] | None = None) -> dict[str, object]:
                argv = argv or []
                output_dir = _arg_value(argv, "--output-dir", prompt_output_dir)
                output_dir.mkdir(parents=True, exist_ok=True)
                run_dir = output_dir / "standards_prompt_seed-20240102_1200"
                run_dir.mkdir(parents=True, exist_ok=True)
                return {
                    "run_id": run_dir.name,
                    "status": "ok",
                    "summary": {"total_rules": 5, "category_count": 2},
                }

            return _fake_prompt

        if resolved == (repo_root / orchestrator.SUMMARY_SCRIPT).resolve():
            def _fake_summarize(*_args, **_kwargs) -> int:
                return 0

            return _fake_summarize

        return original_loader(script_path, module_name, attribute)

    orchestrator._load_callable = _fake_loader

    try:
        exit_code = orchestrator.run(
            [
                "--repo-root",
                str(repo_root),
                "--index-output-dir",
                str(index_output_dir),
                "--index-path",
                str(tmp_path / "index" / "latest_index.yaml"),
                "--categories-path",
                str(categories_path),
                "--gap-output-dir",
                str(gap_output_dir),
                "--diff-output-dir",
                str(diff_output_dir),
                "--prompt-output-dir",
                str(prompt_output_dir),
                "--pending-path",
                str(pending_path),
                "--healthview-root",
                str(healthview_root),
                "--artifacts-to-keep",
                "2",
                "--index-artifacts-to-keep",
                "2",
                "--gap-artifacts-to-keep",
                "2",
                "--prompt-artifacts-to-keep",
                "2",
                "--timestamp",
                "2024-01-02T12:00:00+00:00",
                "--log-level",
                "DEBUG",
            ]
        )
    finally:
        orchestrator._load_callable = original_loader

    assert exit_code == 0

    manifest_paths = list(healthview_root.glob("healthview/standards_integrity/*/manifest.json"))
    assert manifest_paths
    manifest_path = manifest_paths[0]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["viewer"] == "healthview"
    assert manifest["topic"] == "standards_integrity"

    telemetry_steps = {step["name"]: step for step in manifest["telemetry"]["steps"]}
    assert telemetry_steps["index"]["status"] == "success"
    assert telemetry_steps["gap"]["status"] == "success"
    assert telemetry_steps["diff"]["status"] == "skipped"
    assert telemetry_steps["prompts"]["status"] == "success"
    assert telemetry_steps["summary"]["status"] == "success"

    summary_path = manifest_path.with_name("summary.md")
    assert summary_path.exists()
    summary_content = summary_path.read_text(encoding="utf-8")
    assert "# Standards Integrity Summary" in summary_content
    assert "pipeline_status" in summary_content

    telemetry_path = manifest_path.with_name("telemetry.json")
    assert telemetry_path.exists()

    artifacts_section = manifest["artifacts"]
    assert artifacts_section["index_report"].endswith("report.json")
    assert artifacts_section["gap_report"].endswith("report.json")
    assert artifacts_section["gap_summary"].endswith("bundle_summary.json")
    assert artifacts_section["prompt_run"].endswith("standards_prompt_seed-20240102_1200")
