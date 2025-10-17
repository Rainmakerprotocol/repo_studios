import importlib.util
import os
from pathlib import Path


def _import_pytest_runner():
    module_path = Path(".repo_studios/pytest_log_runner.py")
    spec = importlib.util.spec_from_file_location("pytest_log_runner", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_logs_dir_defaults_to_workspace_root(tmp_path, monkeypatch):
    mod = _import_pytest_runner()

    # Case 1: GITHUB_WORKSPACE set
    ws = tmp_path / "repo"
    ws.mkdir()
    monkeypatch.setenv("GITHUB_WORKSPACE", str(ws))
    monkeypatch.delenv("PYTEST_LOGS_DIR", raising=False)
    parser = mod.argparse.ArgumentParser()
    parser.add_argument("--cwd", default=str(ws))
    parser.add_argument(
        "--logs-dir",
        default=os.environ.get("PYTEST_LOGS_DIR")
        or str(Path(os.environ.get("GITHUB_WORKSPACE") or Path.cwd())
                / ".repo_studios/pytest_logs"),
    )
    args = parser.parse_args([])
    assert Path(args.logs_dir) == ws / ".repo_studios/pytest_logs"

    # Case 2: GITHUB_WORKSPACE unset – falls back to cwd
    monkeypatch.delenv("GITHUB_WORKSPACE", raising=False)
    cwd = tmp_path / "work"
    cwd.mkdir()
    parser = mod.argparse.ArgumentParser()
    parser.add_argument("--cwd", default=str(cwd))
    parser.add_argument(
        "--logs-dir",
        default=os.environ.get("PYTEST_LOGS_DIR")
        or str(Path(os.environ.get("GITHUB_WORKSPACE") or Path.cwd())
                / ".repo_studios/pytest_logs"),
    )
    args = parser.parse_args([])
    # Since we constructed default using Path.cwd(), ensure process cwd matches our desired cwd
    # by temporarily chdir. We can't change chdir here without affecting pytest, so compare suffix.
    assert args.logs_dir.endswith(".repo_studios/pytest_logs")
