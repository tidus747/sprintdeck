# Changelog

## Unreleased

- Added the supplied SprintDeck logo to the controller, all presentation scenes, Welcome, website navigation, homepage, footer, and browser icons.
- Consolidated the brand artwork into one canonical application asset, copied into the static website build.

- Aligned the documentation website with SprintDeck's blue, navy, white, and gray palette, replacing the earlier green website theme.
- Made repeated documentation builds tolerate copied read-only asset directories on Windows.

- Added a public documentation homepage explaining the facilitation workflow, searchable guides, and a six-scene screenshot gallery.
- Added a static GitHub Pages build/deploy workflow and an optional pinned documentation-only Markdown dependency.
- Added repeatable screenshots from temporary fictional sessions, with clearly labeled illustrative board and roadmap content.

- Added a Welcome scene with a large sprint title, starting-soon message, goal, dates, team count, and planning status.
- Added a Roadmap Review scene for a large external roadmap capture, matching Board Discussion.
- Changed every capture aperture to an exact 16:9 rectangle for uniformly scaled 1920 x 1080 sources, with unobstructed video corners.
- Added six selectable milestone colors in the controller and Overview, defaulting older milestones to blue.
- Added a local date/time clock with timezone in the footer of all six overlays.
- Expanded browser checks for capture aspect ratio, scene bounds, milestone colors, welcome synchronization, and local clock updates.

## 0.2.0 - 2026-11-08

- Added private session notes and a Save session & download recap action for Markdown meeting minutes.
- Added full-month sprint calendars with blue sprint dates, red weekends and configured holidays, and planned time-off indicators.
- Added manual holiday and team time-off editing, with a presentation summary of sprint absences.
- Added a fourth Board Discussion overlay with a nearly full-canvas transparent application capture.
- Made objectives, deliverables, dependencies, risks, review notes, and pending decisions shared across members.
- Removed the capacity model, editing controls, calculations, and panels. Use the captured planning application for capacity.
- Added validated migration of version 1 sessions, preserving written content, IDs, and timers.
- Added recap, migration, calendar, and browser integration checks and updated OBS documentation.

## 0.1.0 - 2026-11-08

- Added a local Python HTTP server, validated JSON state, atomic persistence, and revision checks.
- Added a facilitator dashboard with sprint editing, member ordering, individual reviews, capacity, and timers.
- Added synchronized Overview, Individual Planning, and Commitment & Wrap-up presentation overlays.
- Added roadmap, scope, risks, decisions, follow-up actions, and final ceremony checks.
- Added confirmed session import, export, reset, checklist configuration, and a fictional demo.
- Added deterministic state and timer tests, HTTP API tests, repository style checks, and CI.
- Documented local operation, privacy, state schema, and OBS transparency setup.
- Preserved the existing GPL-3.0 license.
