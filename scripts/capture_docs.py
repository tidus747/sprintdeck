"""Capture only a fictional temporary SprintDeck session, never the user's OBS screen."""

import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
from http.server import ThreadingHTTPServer

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from sprintdeck.server import Handler
from sprintdeck.state import Store

SCENES = ("welcome", "overview", "individual", "discussion", "roadmap", "wrapup")


class DemoHandler(Handler):
    def send_header(self, keyword, value):
        if keyword == "Content-Security-Policy":
            value = value.replace("frame-ancestors 'none'", "frame-ancestors 'self'")
        super().send_header(keyword, value)

    def do_GET(self):
        if not self.trusted_host():
            return super().do_GET()
        if self.path.startswith("/showcase/") and self.path.split("/")[-1] in SCENES:
            self.respond(200, (ROOT / "website/demo/composition.html").read_bytes(), "text/html")
        elif self.path in ("/demo/board.css", "/demo/compose.js"):
            self.respond(200, (ROOT / "website/demo" / self.path.split("/")[-1]).read_bytes(),
                         "text/css" if self.path.endswith("css") else "text/javascript")
        else:
            super().do_GET()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--browser", required=True, help="Installed Chrome, Chromium, or Edge executable")
    args = parser.parse_args()
    output = ROOT / "website/assets/screenshots"
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="sprintdeck-public-demo-") as folder:
        store = Store(Path(folder) / "demo.session.json")
        demo = json.loads((ROOT / "examples/demo-session.json").read_text(encoding="utf-8"))
        demo["members"][0]["checks"][0]["checked"] = True
        demo["members"][0]["checks"][1]["checked"] = True
        demo["roadmap"].extend([
            {"id": "docs-testing-milestone", "title": "Automated testing", "date": "2030-04-08", "description": "Review the test coverage", "status": "In progress", "color": "green"},
            {"id": "docs-documentation-milestone", "title": "Documentation improvements", "date": "2030-04-10", "description": "Prepare the review notes", "status": "Planned", "color": "blue"},
        ])
        store.apply({"type": "import_session", "revision": store.state["revision"], "state": demo, "confirm": True})
        server = ThreadingHTTPServer(("127.0.0.1", 0), DemoHandler); server.store = store
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        try:
            for index, scene in enumerate(SCENES):
                command = [args.browser, "--headless=new", "--disable-gpu", "--no-first-run", "--disable-background-networking", "--disable-component-update", "--disable-sync", "--hide-scrollbars", "--force-device-scale-factor=1", "--window-size=1920,1080", "--virtual-time-budget=2500", "--dump-dom", f"--user-data-dir={Path(folder) / ('profile-' + str(index))}", f"--screenshot={output / (scene + '.png')}", f"http://127.0.0.1:{server.server_port}/showcase/{scene}"]
                completed = subprocess.run(command, capture_output=True, timeout=40)
                if completed.returncode:
                    raise RuntimeError(f"Screenshot failed for {scene}")
                if scene not in ("welcome", "wrapup") and b'data-alignment="verified"' not in completed.stdout:
                    raise RuntimeError(f"Fictional capture did not align for {scene}")
                print(f"Captured fictional demo: {scene}.png", flush=True)
        finally:
            server.shutdown(); server.server_close(); thread.join()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
