"""Optional browser smoke check using an installed Chromium browser, no packages."""

import argparse
from http.server import ThreadingHTTPServer
from pathlib import Path
import subprocess
import sys
import tempfile
import threading

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sprintdeck.server import Handler  # noqa: E402
from sprintdeck.state import Store  # noqa: E402


class ProbeHandler(Handler):
    def send_header(self, keyword, value):
        # Allow same-origin probe frames in this temporary test server only.
        if keyword == "Content-Security-Policy":
            value = value.replace("frame-ancestors 'none'", "frame-ancestors 'self'")
        super().send_header(keyword, value)

    def do_GET(self):
        if self.path == "/probe" and self.trusted_host():
            self.respond(200, b'<!doctype html><html><head><script type="module" src="/probe.js"></script></head><body><pre id="result">RUNNING</pre><iframe id="control" src="/control" width="1280" height="900"></iframe><iframe id="overlay" src="/overlays/individual" width="1280" height="720"></iframe><iframe id="overview" src="/overlays/overview" width="1280" height="720"></iframe><iframe id="discussion" src="/overlays/discussion" width="1280" height="720"></iframe><iframe id="welcome" src="/overlays/welcome" width="1280" height="720"></iframe><iframe id="roadmap" src="/overlays/roadmap" width="1920" height="1080"></iframe><iframe id="wrapup" src="/overlays/wrapup" width="1280" height="720"></iframe></body></html>', "text/html")
        elif self.path == "/probe.js" and self.trusted_host():
            self.respond(200, (ROOT / "scripts/browser_probe.js").read_bytes(), "text/javascript")
        else:
            super().do_GET()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--browser", required=True, help="Path to Chrome, Chromium, or Edge executable")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="sprintdeck-browser-") as folder:
        server = ThreadingHTTPServer(("127.0.0.1", 0), ProbeHandler)
        server.store = Store(Path(folder) / "test.session.json")
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            try:
                result = subprocess.run([args.browser, "--headless=new", "--disable-gpu", "--no-first-run",
                                         "--disable-background-networking", "--disable-component-update", "--disable-sync",
                                         f"--user-data-dir={Path(folder) / 'profile'}", "--virtual-time-budget=25000",
                                         "--dump-dom", f"http://127.0.0.1:{server.server_port}/probe"],
                                        capture_output=True, text=True, timeout=45)
            except (OSError, subprocess.TimeoutExpired):
                print("Browser check could not finish. Verify the executable path and available headless browser support.")
                return 1
            if result.returncode == 0 and "BROWSER_CHECK_PASSED" in result.stdout:
                print("Browser check passed: 16:9 captures, welcome and roadmap scenes, milestone colors, local clocks, shared context, notes and Markdown download, calendar, time off, reviews, timers, and safe text.")
                return 0
            print("Browser check failed. Probe output:")
            print(result.stdout[:8000])
            return 1
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


if __name__ == "__main__":
    sys.exit(main())
