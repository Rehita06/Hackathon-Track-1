#!/usr/bin/env python3
"""Yojana Saathi - zero-dependency HTTP server (Python 3.8+)."""
import json
import mimetypes
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from engine import assistant, eligibility, llm

STATIC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
MAX_BODY = 64 * 1024


class Handler(BaseHTTPRequestHandler):
    def _json(self, obj, code=200):
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/api/health":
            return self._json({"ok": True, "ai": llm.available(), "schemes": len(assistant.SCHEMES)})
        if path == "/api/schemes":
            return self._json(assistant.SCHEMES)
        rel = "index.html" if path == "/" else path.lstrip("/")
        full = os.path.realpath(os.path.join(STATIC, rel))
        if not full.startswith(os.path.realpath(STATIC)) or not os.path.isfile(full):
            return self._json({"error": "not found"}, 404)
        with open(full, "rb") as f:
            data = f.read()
        self.send_response(200)
        self.send_header("Content-Type", (mimetypes.guess_type(full)[0] or "application/octet-stream") + "; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        try:
            n = int(self.headers.get("Content-Length", 0))
            if n > MAX_BODY:
                return self._json({"error": "too large"}, 413)
            body = json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            return self._json({"error": "invalid json"}, 400)
        lang = body.get("lang", "en") if body.get("lang") in llm.LANG_NAMES else "en"
        if self.path == "/api/eligibility":
            return self._json(eligibility.evaluate(body.get("profile"), lang=lang))
        if self.path == "/api/ask":
            q = str(body.get("question", ""))[:500].strip()
            if not q:
                return self._json({"error": "empty question"}, 400)
            return self._json(assistant.ask(q, lang, body.get("profile")))
        if self.path == "/api/explain":
            t = str(body.get("text", ""))[:8000].strip()
            if len(t) < 20:
                return self._json({"error": "text too short"}, 400)
            return self._json(assistant.explain_notice(t, lang))
        self._json({"error": "not found"}, 404)

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    print(f"Yojana Saathi on http://localhost:{port}  (AI mode: {'ON' if llm.available() else 'offline'})")
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
