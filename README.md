# SprintDeck

An open-source visual control room for better planning meetings.

SprintDeck gives a facilitator a local dashboard and six synchronized OBS presentation overlays. Manage shared sprint context, individual reviews, calendars, time off, timers, and commitments, then download the session recap as Markdown. No project management integration is required.

[Documentation website](https://tidus747.github.io/sprintdeck/) · [Scene gallery](docs/scenes.md) · [OBS setup](docs/obs-setup.md) · [Session recap](docs/session-recap.md)

## Run locally

Requires Python 3.11 or newer and a modern browser. No Python packages, Node installation, build step, external accounts, or OBS plugins are required. Clone this repository, enter its directory, and run:

```sh
python -m sprintdeck
```

On Windows with the Python launcher, use `py -3.11 -m sprintdeck`. On Linux, use `python3 -m sprintdeck` if that is the name of your Python 3.11+ interpreter.

| Interface | Default URL |
| --- | --- |
| Facilitator dashboard | http://127.0.0.1:8765/control |
| Welcome / starting soon | http://127.0.0.1:8765/overlays/welcome |
| Overview | http://127.0.0.1:8765/overlays/overview |
| Individual planning | http://127.0.0.1:8765/overlays/individual |
| Commitment and wrap-up | http://127.0.0.1:8765/overlays/wrapup |
| Board discussion (large capture) | http://127.0.0.1:8765/overlays/discussion |
| Roadmap review (large capture) | http://127.0.0.1:8765/overlays/roadmap |

The server prints the actual URLs. If port 8765 is occupied, it chooses a free port. Use `--port 9000` to select another port, or `--port 0` to request any free port. Press Ctrl+C to stop.

## Use during planning

1. In Settings choose **Load fictional demo**, or start with the blank five-member team. The demo uses fictional dates in April 2030; adjust them in Overview.
2. Set sprint identifiers, dates, goal, current sprint summary, and roadmap in Overview. Each milestone has a selectable color. Open Welcome before the ceremony for a large sprint title and starting-soon message.
3. Enter shared objectives, deliverables, dependencies, risks, review notes, and pending decisions in Overview. These remain common when selecting another member.
4. Configure holidays and vacation dates in Calendar & time off. Full-month calendars show sprint days in blue, weekends and holidays in red, and planned absences. Holidays are entered manually.
5. Add and reorder members in Team. Individual review manages each member's checklist and commitment confirmation. Capacity stays in your captured planning application.
6. Control meeting and individual timers. Selecting another member preserves the timer and review.
7. Record scope, risks, decisions, next actions, and final checks in Commitment.
8. Use Session notes & recap for private minutes. Save other edited sections, then choose **Save session & download recap (.md)**. The file includes saved agreements, pending items, owners, due dates, and the complete notes. Session notes stay off the overlays.
9. Export session JSON in Settings for a reimportable backup. Markdown is a readable report, not an import format. Forms save on submission; checklists and timers save immediately.

The controller is separate from presentation-only overlays. All pages use one server state, polling every 400 ms. Default timers are 60 minutes for the meeting and five minutes for an individual review. Running timers count elapsed wall time through server restarts; paused timers remain paused.

## OBS setup

Create a 1920 x 1080 canvas and six scenes with the overlay URLs as Browser Sources. Put your 1920 x 1080 Jira or other application capture below the browser source. Every capture aperture is exactly 16:9, so the full source scales uniformly without cropping or distortion. Overview and Individual Planning have smaller apertures; Board Discussion and Roadmap Review have large ones. Welcome is an opaque starting screen; Wrap-up is a panel-based summary. All overlays show local date/time with timezone in the footer.

See the [OBS setup tutorial](docs/obs-setup.md) for scene names, capture coordinates, source order, transparency verification, and meeting software setup. SprintDeck does not embed or synchronize with Jira.

## Design and local data

The application uses Python's standard library, HTML, CSS, and vanilla JavaScript. JSON writes are atomic, mutations are locked, and revisions prevent silent overwrites from multiple controllers. Examples use generic fictional identities and data.

The private session defaults to `~/.sprintdeck/session.json`, outside the checkout. For an ignored repository-local path:

```sh
python -m sprintdeck --data .session/session.json
```

The server binds only to `127.0.0.1`. It is unauthenticated and intended for one trusted local facilitator. Exports can contain private meeting content; keep them out of source control. See [privacy](docs/privacy.md), [configuration](docs/configuration.md), and [architecture and schema](docs/architecture.md).

## Checks

```sh
python -m unittest discover -s tests -v
python scripts/check_style.py
```

Optional JavaScript syntax checks, with Node installed:

```sh
node --check sprintdeck/static/common.js
node --check sprintdeck/static/calendar.js
node --check sprintdeck/static/control.js
node --check sprintdeck/static/overlay.js
node --check scripts/browser_probe.js
```

With an installed Chromium browser, optionally run `python scripts/check_browser.py --browser "PATH_TO_BROWSER_EXECUTABLE"`. This uses an isolated temporary session and browser profile to check controller interactions and overlay synchronization. It requires no browser automation package and is separate from CI.

Application CI runs Python tests on Windows and Linux with Python 3.11 and 3.14, repository text checks, and JavaScript syntax checks. A separate, explicitly configured Pages workflow builds and deploys the static documentation on approved changes to `main`. It never deploys the local server or session files. See [website development](docs/website.md) for the optional Markdown build dependency, screenshot generation, and Pages setup.

## Limits and next versions

Version 0.2 supports one active session and one server process per file, up to 20 members, 60 holidays and time-off entries each, and 12 items per other collection or checklist. Overlays prioritize a five-member, two-week sprint at 1920 x 1080, scaling to 1280 x 720. Long presentation text and lists are truncated; the controller, JSON exports, and Markdown recaps retain complete values.

Existing version 1 session files and JSON imports migrate automatically to version 2. Previous individual context becomes shared content, preserving member attribution when values differ. The capacity fields are removed; the former default capacity checks become unchecked calendar/time-off checks. Export a backup before upgrading, restart the server, and refresh the browser sources. See [configuration](docs/configuration.md).

No integrations, accounts, telemetry, automatic updates, or remote access are included. The local server is not a production hosting service. Templates and scene configuration are planned next, followed by reusable meeting types and optional OBS scene control. See the [roadmap](docs/roadmap.md).

## Contribute and license

Read [CONTRIBUTING.md](CONTRIBUTING.md) and [AGENTS.md](AGENTS.md). The existing GNU GPL version 3 license is preserved; see [LICENSE](LICENSE). AI assistance is disclosed in [CONTRIBUTORS.md](CONTRIBUTORS.md). Contributions require human review and maintenance. OpenAI does not sponsor, maintain, or endorse SprintDeck.
