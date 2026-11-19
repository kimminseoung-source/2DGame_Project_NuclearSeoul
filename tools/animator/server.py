"""Our own skeleton animator, run locally (2026-11-19, user: "이 과정을 다 할 수 있게 사이트로 만들어").

    .venv\\Scripts\\python.exe tools/animator/server.py        -> http://localhost:8765

Serves tools/animator/index.html and the project's files read-only (sprites, Blender poses),
and saves what the page makes through POST /save, only inside assets/characters/ and only
PNG or JSON. Nothing else on the disk can be written. Standard library only.
"""

import base64
import json
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[2]
WRITABLE = ROOT / "assets" / "characters"
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8765


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kw):
        super().__init__(*args, directory=str(ROOT), **kw)

    def do_GET(self):
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            self.path = "/tools/animator/index.html"
        elif path == "/api/list":
            return self.send_json(self.listing())
        return super().do_GET()

    def listing(self):
        """Characters with 8-direction stills, and Blender pose files with their actions."""
        chars = sorted(p.parent.parent.parent.name for p in WRITABLE.glob("*/Idle/rotations/south.png"))
        poses = {}
        for f in sorted((ROOT / "assets" / "characters").glob("*/_passes/poses_*.json")):
            try:
                poses[f.relative_to(ROOT).as_posix()] = sorted(json.loads(f.read_text(encoding="utf-8")))
            except (OSError, ValueError):
                pass
        return {"characters": chars, "poses": poses}

    def do_POST(self):
        if urlparse(self.path).path != "/save":
            return self.send_error(404)
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        target = (ROOT / unquote(body.get("path", ""))).resolve()
        if WRITABLE.resolve() not in target.parents or target.suffix not in (".png", ".json"):
            return self.send_error(403, "only PNG/JSON inside assets/characters")
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.suffix == ".png":
            data = body.get("data", "")
            target.write_bytes(base64.b64decode(data.split(",", 1)[-1]))
        else:
            target.write_text(json.dumps(body.get("json"), ensure_ascii=False, indent=1), encoding="utf-8")
        self.send_json({"saved": target.relative_to(ROOT).as_posix()})

    def send_json(self, obj):
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt, *args):
        pass


if __name__ == "__main__":
    print(f"animator: http://localhost:{PORT}  (root {ROOT})")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
