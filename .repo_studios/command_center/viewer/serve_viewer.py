#!/usr/bin/env python3
"""Simple HTTP server for the Command Center viewer with proper MIME types."""

from __future__ import annotations

import http.server
import socketserver
from pathlib import Path


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
            repo_root = Path(__file__).parent.parent.parent.parent
            directory = str(repo_root)
            print(f"Serving from repo root to enable reports access")
            print(f"Viewer URL: http://localhost:{port}/.repo_studios/command_center/viewer/ui/")
        else:
            # Serve from the ui directory only
            ui_dir = Path(__file__).parent / "ui"
            directory = str(ui_dir)
            print(f"Viewer URL: http://localhost:{port}/")

    print(f"Starting Command Center Viewer server...")
    print(f"Serving from: {directory}")
    print(f"Press Ctrl+C to stop the server")

    import os
    os.chdir(directory)

    with socketserver.TCPServer(("", port), ViewerHTTPRequestHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Serve the Command Center viewer")
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
    serve_viewer(
        port=args.port, 
        directory=args.directory,
        serve_from_repo_root=not args.ui_only
    )