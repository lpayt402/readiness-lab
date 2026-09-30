"""Local-only browser surface for the synthetic Readiness Lab demo."""

from __future__ import annotations

import argparse
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from readiness_lab import analyze, mock_proposals, record_review, validate_proposal

ROOT = Path(__file__).resolve().parent
STATIC_FILES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
    "/styles.css": ("styles.css", "text/css; charset=utf-8"),
}
MAX_REQUEST_BYTES = 8192


def create_demo_state() -> tuple[dict, dict]:
    pack = json.loads((ROOT / "fixtures" / "gizmo_cloud.json").read_text(encoding="utf-8"))
    state = analyze(pack)
    state["proposal_mode"] = "synthetic-mock; no provider calls"
    state["proposals"] = mock_proposals(state, pack)
    state["proposal_validation"] = [validate_proposal(proposal, state, pack) for proposal in state["proposals"]]
    return pack, state


def state_payload(pack: dict, state: dict) -> dict:
    return {
        "service": state["service"],
        "as_of": state["as_of"],
        "ruleset_version": state["ruleset_version"],
        "source_pack_sha256": state["source_pack_sha256"],
        "items": state["items"],
        "evidence": pack["evidence"],
        "proposals": state.get("proposals", []),
        "proposal_validation": state.get("proposal_validation", []),
        "human_decisions": state.get("human_decisions", []),
        "proposal_mode": state["proposal_mode"],
    }


class DemoServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, address, handler=BaseHTTPRequestHandler):
        super().__init__(address, handler)
        self.pack, self.state = create_demo_state()
        self.state_lock = threading.RLock()


class DemoHandler(BaseHTTPRequestHandler):
    server: DemoServer

    def log_message(self, format, *args):
        return

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data:; base-uri 'none'; form-action 'self'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, status: int, value: dict) -> None:
        self._send(status, json.dumps(value).encode("utf-8"), "application/json; charset=utf-8")

    def _local_request(self) -> bool:
        expected = {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}
        host = self.headers.get("Host", "")
        origin = self.headers.get("Origin")
        return host in expected and (origin is None or origin in {f"http://{entry}" for entry in expected})

    def do_GET(self):
        if not self._local_request():
            self._send_json(403, {"error": "Local requests only."})
            return
        if self.path == "/api/state":
            with self.server.state_lock:
                payload = state_payload(self.server.pack, self.server.state)
            self._send_json(200, payload)
            return
        asset = STATIC_FILES.get(self.path)
        if asset is None:
            self._send_json(404, {"error": "Not found."})
            return
        filename, content_type = asset
        content = (ROOT / "web" / filename).read_bytes()
        self._send(200, content, content_type)

    def do_POST(self):
        if not self._local_request():
            self._send_json(403, {"error": "Local requests only."})
            return
        if self.path != "/api/review":
            self._send_json(404, {"error": "Not found."})
            return
        if self.headers.get_content_type() != "application/json":
            self._send_json(415, {"error": "Send a JSON review decision."})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._send_json(400, {"error": "Invalid request length."})
            return
        if length < 1 or length > MAX_REQUEST_BYTES:
            self._send_json(413, {"error": "Review request is empty or too large."})
            return
        try:
            payload = json.loads(self.rfile.read(length))
            if not isinstance(payload, dict) or set(payload) - {"item_id", "action", "rationale", "reviewer", "value"}:
                raise ValueError("Unexpected review fields.")
            item_id = payload.get("item_id")
            if not isinstance(item_id, str):
                raise ValueError("Choose a work item.")
            rationale = payload.get("rationale")
            reviewer = payload.get("reviewer")
            action = payload.get("action")
            value = payload.get("value")
            if not isinstance(action, str) or action not in {"accept", "edit", "reject", "unresolved"}:
                raise ValueError("Choose accept, edit, reject, or unresolved.")
            if not isinstance(rationale, str) or len(rationale) > 1000:
                raise ValueError("Add a rationale under 1,000 characters.")
            if not isinstance(reviewer, str) or len(reviewer) > 120:
                raise ValueError("Enter a reviewer label under 120 characters.")
            if value is not None and (not isinstance(value, str) or len(value) > 500):
                raise ValueError("Edited value must be under 500 characters.")
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            self._send_json(400, {"error": str(exc)})
            return

        with self.server.state_lock:
            proposal = next((item for item in self.server.state.get("proposals", []) if item.get("item_id") == item_id), None)
            if proposal is None:
                self._send_json(404, {"error": "No cited suggestion is available for that item."})
                return
            try:
                self.server.state = record_review(
                    self.server.state,
                    proposal,
                    action,
                    rationale,
                    reviewer,
                    value,
                    pack=self.server.pack,
                )
            except ValueError as exc:
                self._send_json(400, {"error": str(exc)})
                return
            result = state_payload(self.server.pack, self.server.state)
        self._send_json(200, result)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the Readiness Lab browser demo on this computer")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args(argv)
    if not 1024 <= args.port <= 65535:
        parser.error("--port must be between 1024 and 65535")
    server = DemoServer(("127.0.0.1", args.port), DemoHandler)
    print(f"Readiness Lab local demo: http://127.0.0.1:{args.port}")
    print("Synthetic data only. No login, durable audit service, or live model calls.")
    print("Stop with Ctrl+C. Decisions reset when the server stops.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

