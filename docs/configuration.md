# Configuration

## Startup

Run `python -m sprintdeck` from the repository root using Python 3.11+ (`py -3.11` on Windows or `python3` on Linux where needed).

```sh
python -m sprintdeck --port 8765 --data .session/session.json
python -m sprintdeck --port 0
```

The default file is `~/.sprintdeck/session.json`. Startup prints the URLs. An occupied default port falls back to a free port; explicit occupied ports fail. The host is always 127.0.0.1. Use one server process per data file.

## Sprint and members

Overview contains sprint identifiers, dates, goal, planning status, current status, summary, carry-over, and roadmap. Blank sessions start at the next Monday (including today when Monday) and end 13 days later. Dates may span 1 to 43 inclusive calendar days.

Milestones support blue, green, purple, orange, red, or teal accents. Choose Milestone color in the expandable roadmap item editor and save. Overview uses the selected tint and accent independently of milestone status. Older milestones without a color receive blue on load or import; existing titles, dates, descriptions, statuses, and IDs are retained.

Team controls add, remove, reorder, and select members. Removal requires confirmation and deletes review data and linked time-off entries. Previous and next navigation wraps. Selection never resets the timer or confirms a commitment.

Individual review edits each member's name, role, checklist, and commitment confirmation. Overview contains shared objectives, deliverables, dependencies, risks, review notes, and pending decisions. Shared context stays the same when changing members. Capacity is left to Jira or another captured planning application; SprintDeck does not calculate it.

## Calendar and time off

Calendar & time off shows a full month, with previous/next navigation and a Sprint month shortcut. The Overview overlay shows every full month touched by the sprint, including month and year boundaries. Blue backgrounds mark sprint dates. Red day numbers mark weekends and manually configured holidays, including holidays during the sprint. Today has an outline.

Holidays require a name and date. They are team-wide entries, not an automatic regional holiday service. Time off requires a team member and inclusive first/last dates, plus an optional note. Dates can span months or years; the end cannot precede the start. Calendar cells show how many distinct people are away. Overview and Wrap-up list planned absences that overlap the sprint. No working-day or capacity calculation is performed. Add a team member before entering time off.

Checks save immediately and remain separate for each member. Reviewed requires all checks or the labeled facilitator override. Confirmed also requires explicit commitment confirmation. Unchecking a review item removes completion status unless overridden. Team progress always uses actual checks. Replacing checklist labels in Settings clears checks, overrides, and confirmations after confirmation. New members inherit the first member's template, or defaults when the roster is empty.

## Timers

Timers are independent. Start/resume and pause save immediately. Reset requires confirmation. Set duration accepts minutes and resets that timer, paused. The maximum is 24 hours; defaults are 60 and five minutes.

Running timers continue across tabs, scenes, and restarts; downtime counts. Paused timers remain paused. At 60 seconds or less the display turns orange; at zero it reports Time complete. No sound plays. Reset expired timers before starting another timebox.

## Commitment and limits

Scope, roadmap, risks, decisions, next steps, holidays, and time off use expandable editors with explicit save and remove controls. Final checks save immediately. Limits are 20 members, 60 holidays and time-off entries each, and 12 items per other list. Projection works best with five members and short text. Long text and lists are truncated in overlays; use the controller or recap for complete content.

Ready requires goal and scope, confirmed scope and members, all final checks, and all risks Resolved. Final checks remain facilitator assertions to review with the team.

## Session notes and Markdown recap

Session notes & recap contains the session title and private session notes (up to 16,000 characters). Save notes persists these fields. They are not displayed on overlays. Shared review notes in Overview are separate and intentionally visible to the audience.

Save session & download recap (.md) saves the session title and notes, then downloads `sprintdeck-recap.md`. Save other edited sections first: the action blocks download if other forms contain unsaved drafts, including member drafts retained during navigation. It does not clear or reset the session. The download is a snapshot of saved data at the time the server generates it.

The Markdown report includes the sprint goal, commitment, complete session notes and shared context, confirmed and pending scope, risks, decisions, owners, next actions, due dates, roadmap, member review statuses, holidays, planned time off, and final checks. It keeps pending items visibly pending and does not invent agreements or summarize with AI. User content is escaped as literal text. It includes the session creation date, which is retained until reset. Review the file before sharing. The browser chooses the download location. Markdown is not a restorable session format; export JSON for backups.

## Import and export

Settings exports raw JSON as `sprintdeck.session.json`. Import accepts version 1 or 2 files up to 250,000 bytes and replaces state only after confirmation and server validation. A 240,000-byte formatted storage budget keeps valid saved sessions within import limits, including Unicode escaping. Shorten notes if this budget is reached. Use an export or `examples/demo-session.json`, not `/api/state` output. Export a backup before importing or resetting.

Load fictional demo replaces the session with Engineer A through Engineer E and generic notes dated April 2030. Reset entire session restores a blank five-member team with relative dates. Both require confirmation.

Form drafts stay in the browser until saved or the page closes. They are not persisted or broadcast. Immediate actions preserve unrelated drafts. Disconnected pages warn and reconnect automatically. If another tab saves first, stale actions fail; review the updated session and retry.

## Existing sessions

Version 1 files are validated and upgraded to version 2 on startup or import. Shared context is built from former individual text: identical entries are deduplicated; differing entries retain member attribution. Member/checklist IDs, custom checklist labels, confirmations, dates, recorded agreements, and timers are preserved. Capacity fields are removed. The old default capacity checks are replaced by unchecked time-off/calendar review checks, so previous capacity review does not imply that the new calendar has been reviewed.

Export a JSON backup before upgrading. Restart the server and refresh browser sources after updating the code. Invalid files are not silently reset. If validation or the storage budget prevents conversion, the existing file remains intact and startup reports the error.

## Layout

`sprintdeck/static/app.css` defines design tokens and `--capture-share: 70%`. Adjust that variable for the individual capture slot width. The sidebar uses the remaining space with a 22 px gap. Inside each slot, the largest fitting exact 16:9 aperture is centered, using whole 16 x 9 pixel units. A 1920 x 1080 source can be scaled uniformly to that aperture without cropping. Test 1920 x 1080 and 1280 x 720 and update OBS source transforms after changing proportions. The outline sits outside the video; no labels overlap it.

Board Discussion at `/overlays/discussion` and Roadmap Review at `/overlays/roadmap` offer large capture slots with a compact header and no sidebar. They are separate scenes for external board and roadmap application captures. The manually configured colored milestones remain in Overview. Both scenes share the meeting timer and never change member selection.

Welcome at `/overlays/welcome` is an opaque starting screen with a large upcoming sprint identifier, session title, starting-soon message, sprint goal, dates, team count, and planning status. These values come from existing session/sprint fields. It does not automatically start the timer or declare the sprint ready.

All six overlay footers show local date and time, including seconds and timezone, refreshed once per second without a session write. The clock uses the viewing browser's device timezone, English labels, and 24-hour time. It is separate from the meeting countdown. If OBS displays the wrong timezone, check the presenting computer's system timezone.
