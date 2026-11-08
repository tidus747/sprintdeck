"""Run the local SprintDeck server."""

import argparse
import errno
from pathlib import Path
import sys

from .server import Server
from .state import Store, ValidationError


def main():
    parser = argparse.ArgumentParser(description="SprintDeck local planning controller")
    parser.add_argument("--port", type=int, default=8765, help="Local port, 0 selects a free port")
    parser.add_argument("--data", type=Path, default=Path.home() / ".sprintdeck" / "session.json",
                        help="Local session JSON path (default: ~/.sprintdeck/session.json)")
    args = parser.parse_args()
    if not 0 <= args.port <= 65535:
        parser.error("Port must be between 0 and 65535")
    try:
        store = Store(args.data)
        try:
            server = Server(("127.0.0.1", args.port), store)
        except OSError as exc:
            if exc.errno not in (errno.EADDRINUSE, 10048) or args.port != 8765:
                raise
            server = Server(("127.0.0.1", 0), store)
    except (OSError, ValidationError) as exc:
        print(f"SprintDeck could not start: {exc}", file=sys.stderr)
        return 1
    base = f"http://127.0.0.1:{server.server_port}"
    print("SprintDeck 0.2.0 | Local session only", flush=True)
    for route in ("control", "overlays/welcome", "overlays/overview", "overlays/individual", "overlays/wrapup", "overlays/discussion", "overlays/roadmap"):
        print(f"  {base}/{route}", flush=True)
    print("Press Ctrl+C to stop. Running timers continue through a restart.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
