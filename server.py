"""
Local HTTP API Server for Chrome Extension Communication
==========================================================
Runs on http://127.0.0.1:8765 in a background thread inside app.py.
Allows the SI AOC-4 Pro Chrome Extension to fetch approved AOC-4 filing JSON data.

Endpoints:
  GET /status           -> Check server & desktop app connection
  GET /api/aoc4-data    -> Return approved AOC-4 JSON data
"""

import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
from typing import Dict, Any, Optional

HOST = "127.0.0.1"
PORT = 8765

_app_state_ref = {"parsed_result": None, "license_valid": True}

def set_app_data(parsed_result: Optional[Dict[str, Any]], license_valid: bool = True):
    """Set current approved AOC-4 data from the desktop GUI."""
    _app_state_ref["parsed_result"] = parsed_result
    _app_state_ref["license_valid"] = license_valid


class AOC4RequestHandler(BaseHTTPRequestHandler):
    """HTTP Request Handler serving CORS-enabled JSON API endpoints."""

    def _set_headers(self, status=200, content_type="application/json"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(200)

    def do_GET(self):
        path = self.path.split("?")[0]

        if path == "/status":
            self._set_headers(200)
            res = {
                "status": "online",
                "app": "SI Filings Pro",
                "version": "1.0",
                "has_data": _app_state_ref["parsed_result"] is not None,
                "is_approved": _app_state_ref["parsed_result"].get("approved", False) if _app_state_ref["parsed_result"] else False,
            }
            self.wfile.write(json.dumps(res).encode("utf-8"))

        elif path == "/api/aoc4-data":
            if not _app_state_ref["parsed_result"]:
                self._set_headers(404)
                res = {"error": "No AOC-4 data loaded. Upload and approve a financial statement in the desktop app first."}
                self.wfile.write(json.dumps(res).encode("utf-8"))
            else:
                self._set_headers(200)
                self.wfile.write(json.dumps(_app_state_ref["parsed_result"]).encode("utf-8"))

        else:
            self._set_headers(404)
            res = {"error": "Endpoint not found"}
            self.wfile.write(json.dumps(res).encode("utf-8"))

    def do_POST(self):
        path = self.path.split("?")[0]
        if path == "/api/log-report":
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            try:
                log_json = json.loads(post_data.decode('utf-8'))
                log_file_path = r"c:\RIYAS\Sharp INtell\SI Filings\autofill_audit.log"
                with open(log_file_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(log_json, indent=2) + "\n" + "="*50 + "\n")
                self._set_headers(200)
                self.wfile.write(json.dumps({"status": "saved", "path": log_file_path}).encode("utf-8"))
            except Exception as e:
                self._set_headers(500)
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
        else:
            self._set_headers(404)

    def log_message(self, format, *args):
        """Suppress default stdout HTTP logging."""
        pass


def start_local_api_server() -> HTTPServer:
    """Start HTTP API server in a background thread."""
    server = HTTPServer((HOST, PORT), AOC4RequestHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    print(f"SI Filings Pro Local API Server running on http://{HOST}:{PORT}")
    return server
