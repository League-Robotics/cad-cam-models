#!/usr/bin/env python3
"""Live model viewer for the headless SolidCraft MCP server on Buzzkill.

Serves viewer.html and the meshes in MODEL_DIR (STL, OBJ, 3MF). The page
polls /api/models and reloads whenever a file changes, so exporting from the
MCP server updates the browser.

    serve.py [MODEL_DIR] [--port 8765]
"""
import json
import os
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXTS = {".stl", ".obj", ".3mf"}

args = sys.argv[1:]
port = 8765
if "--port" in args:
    i = args.index("--port")
    port = int(args[i + 1])
    del args[i : i + 2]
model_dir = Path(args[0] if args else "~/designs/gears/view").expanduser().resolve()
model_dir.mkdir(parents=True, exist_ok=True)


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split("?")[0]
        if path in ("/", "/index.html"):
            return self.send_file(HERE / "viewer.html", "text/html")
        if path == "/api/models":
            models = [
                {"name": p.name, "mtime": p.stat().st_mtime, "size": p.stat().st_size}
                for p in model_dir.iterdir()
                if p.suffix.lower() in EXTS and p.is_file()
            ]
            models.sort(key=lambda m: m["mtime"], reverse=True)
            body = json.dumps(models).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if path.startswith("/models/"):
            f = (model_dir / os.path.basename(path)).resolve()
            if f.parent == model_dir and f.suffix.lower() in EXTS and f.is_file():
                return self.send_file(f, "application/octet-stream")
        self.send_error(404)

    def send_file(self, f, ctype):
        data = f.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *a):
        pass


print(f"viewer: http://0.0.0.0:{port}/  models from {model_dir}", flush=True)
ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
