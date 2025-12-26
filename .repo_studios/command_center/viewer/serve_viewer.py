#!/usr/bin/env python3
"""Simple HTTP server for the Command Center viewer with update support."""

from __future__ import annotations

import json
import http.server
import socketserver
from http import HTTPStatus
from pathlib import Path
import sys

from command_center.viewer.update_service import (
    UpdateAlreadyRunningError,
    UpdateProcessManager,
    UpdateValidationError,
    create_update_request,
)


_SCRIPT_PATH = Path(__file__).resolve()
REPO_ROOT = _SCRIPT_PATH.parent.parent.parent.parent

# Import the shared repo-root convention from the command_center scripts library.
LIBRARIES_ROOT = _SCRIPT_PATH.parent.parent / "scripts"
if str(LIBRARIES_ROOT) not in sys.path:
    sys.path.insert(0, str(LIBRARIES_ROOT))

from libraries.cli import resolve_repo_root  # noqa: E402
UPDATE_ENDPOINTS = {
    "/.repo_studios/command_center/viewer/update",
    "/command-center/viewer/update",
}
UPDATE_CANCEL_ENDPOINTS = {f"{path}/cancel" for path in UPDATE_ENDPOINTS}
UPDATE_MANAGER = UpdateProcessManager(REPO_ROOT)


class ViewerHTTPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """Threaded HTTP server that allows quick restarts."""

    daemon_threads = True
    allow_reuse_address = True


class ViewerHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP request handler with proper MIME type support for the viewer."""

    extensions_map = {
        ".html": "text/html",
        ".css": "text/css",
        ".js": "application/javascript",
        ".mjs": "application/javascript",
        ".json": "application/json",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".svg": "image/svg+xml",
        ".ico": "image/x-icon",
        ".woff": "font/woff",
        ".woff2": "font/woff2",
        ".ttf": "font/ttf",
        ".eot": "application/vnd.ms-fontobject",
        ".otf": "font/otf",
        "": "application/octet-stream",
    }

    def end_headers(self) -> None:
        """Add CORS headers for local development."""
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.send_header("Expires", "0")
        super().end_headers()

    def do_POST(self) -> None:  # noqa: N802 - align with HTTP handler API
        if self.path in UPDATE_ENDPOINTS:
            self._handle_update_request()
            return
        if self.path in UPDATE_CANCEL_ENDPOINTS:
            self._handle_update_cancel()
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Endpoint not found")

    def _handle_update_request(self) -> None:
        try:
            payload = self._read_json_body()
        except ValueError as exc:
            self._send_json({"status": "error", "message": str(exc)}, status=HTTPStatus.BAD_REQUEST)
            return

        try:
            request = create_update_request(
                REPO_ROOT,
                payload.get("target", ""),
                slug=payload.get("slug"),
                relative_path=payload.get("relative_path"),
                timestamp_iso=payload.get("timestamp_iso"),
            )
            result = UPDATE_MANAGER.start(request)
        except UpdateAlreadyRunningError as exc:
            self._send_json({"status": "conflict", "message": str(exc)}, status=HTTPStatus.CONFLICT)
            return
        except UpdateValidationError as exc:
            self._send_json({"status": "error", "message": str(exc)}, status=HTTPStatus.BAD_REQUEST)
            return
        except Exception as exc:  # pragma: no cover - defensive safeguard
            print(f"[viewer update] unexpected error: {exc}")
            self._send_json(
                {"status": "error", "message": f"Update failed: {exc}"}, status=HTTPStatus.INTERNAL_SERVER_ERROR
            )
            return

        payload = result.to_payload()
        self._send_json(payload, status=HTTPStatus.OK)

    def _handle_update_cancel(self) -> None:
        cancelled = UPDATE_MANAGER.cancel()
        status = "cancelled" if cancelled else "idle"
        self._send_json({"status": status}, status=HTTPStatus.OK)

    def _read_json_body(self) -> dict:
        length_header = self.headers.get("Content-Length", "0")
        try:
            length = int(length_header)
        except ValueError as exc:
            raise ValueError("Invalid Content-Length header") from exc

        raw = self.rfile.read(length) if length > 0 else b""
        if not raw:
            return {}
        try:
            payload = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError("Invalid JSON payload") from exc
        if not isinstance(payload, dict):
            raise ValueError("Update endpoint expects a JSON object payload")
        return payload

    def _send_json(self, payload: dict, *, status: HTTPStatus) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def serve_viewer(port: int = 8000, directory: str | None = None, serve_from_repo_root: bool = True) -> None:
    """
    Start HTTP server for the viewer.

    Args:
        port: Port to serve on (default: 8000)
        directory: Directory to serve from (default: repo root for reports access)
        serve_from_repo_root: If True, serve from repo root to access reports (default: True)
    """
    if directory is None:
        if serve_from_repo_root:
            # Serve from repo root so reports are accessible
            # viewer/serve_viewer.py -> viewer -> command_center -> .repo_studios -> repo_root
            directory = str(REPO_ROOT)
            print("Serving from repo root to enable reports access")
            print(f"Viewer URL: http://localhost:{port}/.repo_studios/command_center/viewer/ui/")
        else:
            # Serve from the ui directory only
            ui_dir = Path(__file__).parent / "ui"
            directory = str(ui_dir)
            print(f"Viewer URL: http://localhost:{port}/")

    print("Starting Command Center Viewer server...")
    print(f"Serving from: {directory}")
    print("Press Ctrl+C to stop the server")

    import os

    os.chdir(directory)

    with ViewerHTTPServer(("", port), ViewerHTTPRequestHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Serve the Command Center viewer")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Repository root (auto-discovered via .repo_studios marker when omitted)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to serve on (default: 8000)",
    )
    parser.add_argument(
        "--directory",
        type=str,
        default=None,
        help="Directory to serve from (default: repo root)",
    )
    parser.add_argument(
        "--ui-only",
        action="store_true",
        help="Serve only the UI directory (reports won't be accessible)",
    )

    args = parser.parse_args()

    # Allow the entrypoint to run from any CWD while consistently resolving the repo root.
    REPO_ROOT = resolve_repo_root(args.repo_root, origin=_SCRIPT_PATH)  # type: ignore[assignment]
    UPDATE_MANAGER = UpdateProcessManager(REPO_ROOT)  # type: ignore[assignment]

    serve_viewer(port=args.port, directory=args.directory, serve_from_repo_root=not args.ui_only)
