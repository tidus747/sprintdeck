"""Optional headless QA for the built GitHub Pages website."""

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import subprocess
import tempfile
import threading

ROOT = Path(__file__).resolve().parents[1]


class SiteHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        if self.path == "/probe":
            content = b'<!doctype html><html><head><script type="module" src="/probe.js"></script></head><body><pre id="result">RUNNING</pre><iframe id="home" src="/sprintdeck/" width="1440" height="1000"></iframe><iframe id="docs" src="/sprintdeck/docs/configuration/" width="1280" height="900"></iframe><iframe id="mobile" src="/sprintdeck/" width="390" height="844"></iframe></body></html>'
        elif self.path == "/mobile-preview":
            # Headless browser windows can enforce a minimum width; an iframe gives an exact mobile viewport.
            content = b'<!doctype html><html><body style="margin:0"><iframe title="390 pixel mobile preview" src="/sprintdeck/" style="position:absolute;inset:0;width:390px;height:844px;border:0"></iframe></body></html>'
        elif self.path == "/probe.js":
            content = (ROOT / "scripts/site_browser_probe.js").read_bytes()
        else:
            if self.path.startswith("/sprintdeck/"):
                self.path = self.path.removeprefix("/sprintdeck")
            return super().do_GET()
        self.send_response(200)
        self.send_header("Content-Type", "text/javascript" if self.path.endswith(".js") else "text/html")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers(); self.wfile.write(content)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--browser", required=True)
    parser.add_argument("--site", type=Path, default=ROOT / "_site")
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(SiteHandler, directory=str(args.site.resolve())))
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    try:
        with tempfile.TemporaryDirectory(prefix="sprintdeck-site-browser-") as folder:
            result = subprocess.run([args.browser, "--headless=new", "--disable-gpu", "--no-first-run", "--disable-background-networking", "--disable-component-update", "--disable-sync", "--force-device-scale-factor=1", f"--user-data-dir={folder}", "--virtual-time-budget=15000", "--dump-dom", f"http://127.0.0.1:{server.server_port}/probe"], capture_output=True, text=True, timeout=40)
            if result.returncode == 0 and "SITE_BROWSER_PASSED" in result.stdout:
                print("Website browser check passed: homepage images, scene gallery, local search, documentation paths, and mobile layout.")
                return 0
            print(result.stdout[:5000]); return 1
    finally:
        server.shutdown(); server.server_close(); thread.join()


if __name__ == "__main__":
    raise SystemExit(main())
