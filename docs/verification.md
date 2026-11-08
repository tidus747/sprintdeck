# Verification

## Documentation website

- Built the homepage and 15 documentation pages from repository Markdown with the GitHub Pages `/sprintdeck` base path.
- Ran 46 tests with the optional Markdown build dependency installed. Application tests remain runnable without it; the five documentation-specific tests skip when it is absent.
- Verified documentation completeness, local links and anchors, screenshot assets, repeatable output, search index generation, protection of unrelated output directories, and exclusion of session/profile data from the generated artifact.
- Passed a real Chrome website check covering the scene gallery, image loading, local search, documentation paths, and a 390 px mobile iframe without horizontal overflow.
- Inspected the homepage and documentation layout in browser screenshots. Reviewed all six public demo images. They show actual overlays with fictional content and clearly identified illustrative captures, not the user's OBS window.
- GitHub Pages publication must be confirmed separately by the remote workflow and live site response. Repository writes do not establish that Pages is enabled.
- Remote GitHub Actions checks passed on Windows and Linux with Python 3.11 and 3.14. The documentation build, including the five website checks and Pages artifact upload, also passed. Pages requires the repository publishing source to be enabled separately before deployment can succeed.

## Current scene refinements

- `py -3.11 -m unittest discover -s tests -v`: 41 tests passed, including milestone palette validation, persistence, default-color migration, and all six overlay routes.
- `py -3.11 scripts/check_browser.py --browser "PATH_TO_CHROME_EXECUTABLE"`: passed. Checks covered exact 16:9 capture aspect ratios, complete unobstructed apertures within scene bounds at 1080p and 720p, Welcome content and goal synchronization, visible milestone color, and ticking local date/time clocks across all six overlays, alongside existing session checks.
- Inspected screenshots: Welcome at 1920 x 1080 and 1280 x 720; Roadmap Review and Overview at 1920 x 1080; Individual Planning at 1280 x 720. Welcome had large sprint text and critical context. Colored milestones and local clocks were visible. A colored background remained visible through capture apertures. No clipping was seen in these fictional demo screenshots.
- Actual OBS source alignment and video playback remain manual checks. The guide now lists exact aperture dimensions and scale factors for full 1920 x 1080 captures. These dimensions differ from the older full-slot outlines.

## v0.2 checks

Executed on Windows with Python 3.11.9, Node 20.10.0, and an isolated Chrome profile:

- `py -3.11 -m unittest discover -s tests -v`: 39 tests passed, including shared context and private notes, Markdown completeness and escaping, attachment responses, valid/invalid holiday and time-off dates, linked absence removal, version 1 file/import migration, capacity removal, existing timer/review behavior, and upload rejection.
- `py -3.11 scripts/check_browser.py --browser "PATH_TO_CHROME_EXECUTABLE"`: passed. Actual browser interactions verified note saving and the Markdown download trigger/content, blocking recap generation when other drafts are unsaved, shared context across member changes, full-month rendering, holiday styling, time-off editing, privacy of notes in overlays, timers, safe DOM rendering, and a large transparent discussion region.
- JavaScript files were syntax-checked through Node's module-mode stdin check. No new runtime dependencies were installed.
- Headless screenshots were inspected for Overview, Individual Planning, and Board Discussion at 1920 x 1080, plus a two-month Overview at 1280 x 720. A colored browser background remained visible through the capture regions. Monthly sprint highlighting, red weekend/holiday numbers, vacation summaries, and shared-context panels were visible.

The remaining OBS, meeting-software, keyboard/screen-reader, Linux, and larger-team checks listed below still require manual validation. Browser transparency checks do not replace actual OBS composition testing.

## v0.1 historical checks

Executed on Windows with Python 3.11.9, Node 20.10.0, and an installed Chrome browser.

### Automated checks

- `py -3.11 -m unittest discover -s tests -v`: state initialization, demo import, serialization, persistence, failed-write rollback, validation, members, isolated checklists, completion, readiness, capacity, deterministic timers, restart behavior, reset, HTTP routes, request limits, Origin/Host rejection, revision conflicts, CLI port behavior, and repository style.
- `python scripts/check_style.py`: rejects U+2014 in repository UTF-8 text, including untracked new files and excluding ignored local data.
- Each JavaScript file was syntax-checked with `node --input-type=module --check` using source piped through stdin because the execution sandbox restricted Node's filesystem path resolution. The equivalent filename-based commands are in README.md and CI.
- `py -3.11 scripts/check_browser.py --browser "PATH_TO_CHROME_EXECUTABLE"`: successful real-browser checks of controller rendering, form saves, safe text, draft preservation through saves and member navigation, selection propagation, checklist isolation, capacity warnings, timer start/pause, and computed transparent body/capture backgrounds.
- A real `py -3.11 -m sprintdeck --port 0 --data TEMPORARY_SESSION_PATH` process started and returned HTTP 200 for health, controller, and all three overlay URLs. It was stopped after the check.
- `git diff --check`: no whitespace errors. License content was preserved. Added content was reviewed for credentials, real identities, company data, and dependencies on other repositories.

### Visual inspection

Headless Chrome screenshots were captured and inspected for Individual Planning at 1920 x 1080 and 1280 x 720, Overview and Wrap-up at 1920 x 1080, and the controller at 1440 x 1080. The 720p Individual screenshot used a colored browser background, visible through the capture area and surrounding transparent canvas while cards remained white.

The fictional five-member scene layouts fit the canvas without unexpected clipping in these screenshots. Projection readability still depends on the viewer's display and meeting setup. Long text and larger lists are deliberately truncated and remain fully available in the controller and exports.

An additional narrow controller screenshot attempt timed out, so narrow-screen appearance was not visually verified. Browser QA uses only a new temporary profile; it does not read an existing user profile. Screenshots and test session files are ignored local artifacts.

## Still requires manual validation

- OBS Browser Source alpha compositing, actual Window Capture crop/alignment, and source ordering.
- Live meeting software virtual camera/projector output and audience readability.
- Keyboard-only navigation and a screen reader pass.
- Interactive Linux browser and OBS use. The Windows/Linux Python test matrix has passed remotely; this does not replace desktop presentation testing.
- Larger teams and maximum-length text in actual meeting presentation conditions.

Use the practical checklist in [obs-setup.md](obs-setup.md) before presenting. This verification does not claim an OBS session or public release was performed.
