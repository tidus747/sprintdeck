# OBS setup

SprintDeck uses standard OBS Browser Sources. No plugin, Jira authentication, Jira API, or OBS WebSocket is needed. Keep the local server running.

## Prepare the canvas

1. Run `python -m sprintdeck`. Copy printed URLs if a fallback port is selected.
2. Open http://127.0.0.1:8765/control. Load the fictional demo in Settings or configure a session.
3. In OBS Settings, Video, set Base (Canvas) Resolution to 1920 x 1080. Output can be 1920 x 1080 or 1280 x 720. Keep 16:9.
4. Create scenes `00 | Welcome`, `01 | Overview`, `02 | Individual Planning`, `03 | Commitment & Wrap-up`, `04 | Board Discussion`, and `05 | Roadmap Review`.

## Add the browser sources

| Scene | URL |
| --- | --- |
| 00 Welcome | http://127.0.0.1:8765/overlays/welcome |
| 01 Overview | http://127.0.0.1:8765/overlays/overview |
| 02 Individual Planning | http://127.0.0.1:8765/overlays/individual |
| 03 Commitment & Wrap-up | http://127.0.0.1:8765/overlays/wrapup |
| 04 Board Discussion | http://127.0.0.1:8765/overlays/discussion |
| 05 Roadmap Review | http://127.0.0.1:8765/overlays/roadmap |

Add a Browser Source to each scene with the corresponding URL, width 1920, height 1080. Fit it to the canvas and lock the transform. Retain OBS's transparent default browser background or leave custom CSS empty. Do not add CSS that sets the page background to white. Disabling Shutdown source when not visible reduces scene-switch loading; timer correctness does not depend on it.

For a native 1280 x 720 base canvas, use Browser Source dimensions 1280 x 720. SprintDeck scales its full canvas. Multiply the capture coordinates below by 2/3.

## Compose captured content

Open Jira or another planning application separately. Configure its captured output to 1920 x 1080, then add Window Capture below the Browser Source. If using Display Capture, select just the intended 1920 x 1080 application region. Verify the source's native dimensions before scaling. Do not include unrelated windows or private navigation.

Recommended source order, top to bottom:

1. SprintDeck Browser Source.
2. Uniformly scaled 1920 x 1080 application capture (Overview, Individual, Board Discussion, and Roadmap Review).
3. White Color Source or chosen background.

Panels, header, and footer are opaque. Capture apertures and their surrounding layout stay transparent. A white Color Source gives the intended surrounding appearance. Welcome is an opaque starting screen, and Wrap-up uses panels without an application capture. Do not add captured application sources to Welcome or Wrap-up.

Every aperture is exactly 16:9 and centered inside its available slot. A full 1920 x 1080 image fits without cropping or distortion, leaving margins where needed. The outline is outside the aperture; no labels cover source pixels. Default aperture coordinates and uniform source scale at a 1920 x 1080 canvas are:

| Scene | Left | Top | Width | Height | Source scale |
| --- | --- | --- | --- | --- | --- |
| Overview | 153 | 610 | 672 | 378 | 0.35 |
| Individual Planning | 32.4 | 214.5 | 1296 | 729 | 0.675 |
| Board Discussion | 160 | 114 | 1600 | 900 | 0.833333 |
| Roadmap Review | 160 | 114 | 1600 | 900 | 0.833333 |

The dashed outline is 2 px outside the source bounds. In OBS Edit Transform, use top-left source alignment and enter the position and size above, or apply the same scale to both axes. For example, a 1920 x 1080 source at scale 0.675 becomes 1296 x 729 in Individual Planning. Do not stretch one axis independently or crop the source to fill a wider slot. Scale is rounded in the table for Board Discussion and Roadmap Review; the listed 1600 x 900 bounds are exact.

The individual slot occupies about 70% of useful width, adjustable through `--capture-share` in app.css. Its aperture fits a complete 1080p image within that slot. Board Discussion and Roadmap Review remove the sidebar and use compact headers, giving the source a larger 1600 x 900 presentation. Use a board capture for general discussion and a roadmap application capture in Roadmap Review. Colored milestones are configured separately in the controller for Overview. Capacity stays in the captured application. These scenes do not change member selection or timers.

Right-click the captured source, Transform, Edit Transform to position it. Keep the complete 1920 x 1080 source visible and preserve aspect ratio. If a larger display must first be cropped to isolate the application, produce a 1920 x 1080 source region before applying these transforms. Lock the capture and Browser Source once aligned. Changing CSS proportions changes aperture positions, so update source transforms afterward.

Without a capture, use the white background and outlined space for discussion. All planning fields remain useful and independent of Jira.

Welcome shows the upcoming sprint in large type, goal, dates, team count, planning status, and a starting-soon message. It reads existing controller fields; it does not start the meeting automatically. All six scenes show date/time in the footer using the presenting browser's local timezone, refreshed every second. Check the computer's timezone if that clock is incorrect.

## Verify before a meeting

1. Temporarily place a bright colored Color Source directly below the Browser Source. The capture region must show the color while cards and header remain white. If the page is opaque, remove white background overrides in browser custom CSS. Remove the test color afterward.
2. In Individual Planning, select Engineer B. Confirm that name and checklist change while the shared objective, deliverables, dependencies, and review notes remain unchanged. Check an item, navigate away, and return to verify isolation.
3. Start, pause, and resume the individual timer. Switch scenes and tabs; confirm consistent time. Member navigation must not reset it.
4. Add a fictional holiday and time-off range. Check the full-month calendar, blue sprint dates, red holiday/weekend numbers, away count, and planned absences. If the sprint crosses a month boundary, verify both full months.
5. Check goal, colored milestones, and team status in Overview. Enter a decision and scope item and inspect Wrap-up. Open Welcome before starting, then check Board Discussion and Roadmap Review. Selection must not automatically confirm members. Verify the local footer clock.
6. Test 1080p and 720p. Show all four corners of a 1920 x 1080 source and verify none are hidden. A circle in the captured application should remain circular. Check readable text, no scrollbars, and capture outlines. Keep projection notes concise: long text and lists are truncated, with complete values in the controller.
7. Export a backup, restart with the same data file, and verify persistence. Running timers include downtime; paused timers retain remaining time.
8. Add private session notes and save a Markdown recap. Confirm the notes are in the report and absent from presentation overlays. Shared review notes are intentionally visible.

## Share the output

Start OBS Virtual Camera and select it as your meeting application's camera, or open an OBS Windowed Projector for Program and share that projector window. Availability and permissions vary by OS and meeting application. Check legibility with another participant. Share Program output, not the facilitator dashboard or the whole desktop. SprintDeck plays no audio; configure meeting audio separately.

## Troubleshooting

- Blank source: check the server and exact printed URL in a browser, then refresh the OBS source cache. A fallback port requires updating all URLs.
- Disconnected banner: the last state stays visible while polling retries. Restart at the same URL or update source ports.
- Hidden board: check source order, custom CSS, and the bright-color transparency test. Check source dimensions and uniform scaling; do not crop the Browser Source or stretch the application to fit a non-16:9 slot.
- Clipping: use 16:9 dimensions, verify transforms, and shorten notes. Larger teams and long lists exceed compact panels; review them in the controller.
- Frozen capture: check the chosen application window and OBS capture method. This is independent of polling.
- Zero timer: reset it before starting a new timebox.

Programmatic OBS scene switching through OBS WebSocket remains a future enhancement.
