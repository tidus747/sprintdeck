# Architecture

SprintDeck has no runtime dependencies beyond Python 3.11+. `server.py` serves explicit static routes and an HTTP API through `ThreadingHTTPServer`. `state.py` owns mutations, migrations, timers, derived values, and persistence. `validation.py` validates stored and imported state. `recap.py` generates literal-text Markdown minutes. `static/control.js` builds facilitator forms; `static/overlay.js` renders six presentation scenes. Both share DOM helpers in `common.js` and month/time-off views in `calendar.js`.

## Data flow

The controller posts typed actions. The store takes a reentrant lock, verifies the expected revision, copies state, applies the action, validates the candidate, writes a temporary file, flushes and synchronizes it, and atomically replaces the session file. Only then does it publish the new in-memory state. Failed validation or persistence leaves the previous state intact.

All pages poll `GET /api/state` every 400 ms. Only changed revisions trigger a presentation rebuild; timers render between polls. Controller forms retain dirty drafts, focus, and open item editors across rebuilds. A successful form save clears that form's draft. The server is authoritative; localStorage is not used.

Multiple controllers share a revision. Stale actions return 409 without applying changes. Polling refreshes the revision; the facilitator can review and retry. This prevents silent stale writes but is not collaborative editing.

## State schema (version 2)

`examples/demo-session.json` is a validated example. Imports require this raw schema, not the enriched `/api/state` response. Use `/api/export` for reimportable JSON. Unknown object fields are rejected.

| Root field | Contents |
| --- | --- |
| `schema_version` | Integer 2 |
| `revision` | Nonnegative integer, incremented on successful actions |
| `session` | `title`, `created` (ISO date), `notes` (private minutes) |
| `planning` | Shared `objective`, `deliverables`, `dependencies`, `risks`, `notes`, `pending_decisions` |
| `sprint` | `current`, `next`, `start`, `end`, `goal`, `status`, `current_status`, `summary`, `carryover`, `commitment` |
| `timers` | `meeting` and `individual`, each with `duration`, `remaining`, `deadline` |
| `members` | Ordered list of members with stable IDs |
| `active_member` | Existing member ID, or null for an empty team |
| `roadmap` | Items: `id`, `title`, `date`, `description`, `status`, `color` |
| `scope` | Items: `id`, `title`, `confirmed` |
| `risks` | Items: `id`, `text`, `owner`, `next_action`, `status` |
| `decisions` | Items: `id`, `text`, `owner`, `status` |
| `actions` | Items: `id`, `text`, `owner`, `due`, `status` |
| `holidays` | Items: `id`, `title`, `date` |
| `time_off` | Items: `id`, `member_id`, `start`, `end`, `note` |
| `final_checks` | Checklist items: `id`, `label`, `checked` |

Members have `id`, `name`, `role`, `checks`, `review_override`, and `confirmed`. Checks use the final-check item shape. IDs are globally unique. New records receive UUIDs; ordering never identifies a record. Time off refers to a member by ID; removing that member also removes linked absences after confirmation. Planning context is shared rather than owned by a member. Capacity is not represented in version 2.

Dates use YYYY-MM-DD. Sprints span 1 to 43 inclusive calendar days. Time-off ranges are inclusive and require a nondecreasing start/end pair. Holiday dates are required; roadmap and follow-up dates are optional. Collection statuses are `Planned`, `Open`, `In progress`, `Confirmed`, or `Resolved`. There are at most 20 members, 60 entries per holiday/time-off collection, and 12 entries per other collection or checklist. Session notes allow 16,000 characters. Shared context allows 28,000 characters per field to preserve migrated member text. Strings are length-limited, finite numbers and booleans are type-checked, and Unicode U+2014 is rejected. Formatted JSON, including ASCII Unicode escapes, must fit a 240,000-byte storage budget so saved exports stay importable.

Read state adds `server_time`, timer `seconds_left`, member `completion` and `status`, and team `progress` and `ready`. These are calculated rather than persisted. The browser marks weekends, configured holidays, sprint dates, and distinct people away for each displayed date. No capacity or working-day calculation is performed.

Reviewed requires all member checks or the explicit facilitator override. Confirmed additionally requires explicit commitment confirmation. Selection alone only yields In review. Team progress averages actual checklist percentages, even with overrides. Ready requires a nonempty goal and scope, all scope confirmed, all members Confirmed, all final checks checked, and every risk Resolved. This is a checklist aid, not an independent assessment of planning quality.

Version 1 sessions remain accepted by validation for migration only. After validating the original shape, migration preserves IDs, timers, sprint fields, and recorded lists, deduplicates identical individual context, and preserves differing text with member attribution in shared fields. It removes capacity fields and replaces former default capacity checks with unchecked time-off/calendar checks. Startup atomically saves the validated upgrade; imports use the ordinary atomic action transaction. Failure preserves the original file. Current mutations always operate on version 2.

Milestone `color` is an additive version 2 field. Older version 1/2 items without it validate and receive blue during migration. New item actions require color. Only six named values are accepted: blue, green, purple, orange, red, and teal. These map to predefined CSS classes, without inserting arbitrary user CSS. Color does not change milestone status or readiness.

## API

- `GET /health`: health and version.
- `GET /api/state`: synchronized state and calculated values.
- `GET /api/export`: raw importable JSON.
- `GET /api/recap`: UTF-8 Markdown attachment generated from one saved state snapshot, without changing session state.
- `POST /api/actions`: an object containing `type`, current integer `revision`, and action fields. Success returns enriched state.

| Action type | Additional fields |
| --- | --- |
| `update_sprint` | `values`: partial sprint object |
| `update_session` | `values`: partial `title` and/or private `notes` |
| `update_planning` | `values`: partial shared planning context |
| `select_member` | `member_id` |
| `navigate_member` | `direction`: -1 or 1, wraps around |
| `add_member` | `name` |
| `update_member` | `member_id`, `values`: editable member fields |
| `remove_member` | `member_id`, `confirm: true` |
| `move_member` | `member_id`, `direction`: -1 or 1 |
| `set_check` | `member_id`, `id`, `checked` |
| `configure_checks` | `labels`: 1 to 12 strings, `confirm: true` |
| `timer` | `timer`: meeting or individual; `operation`: start, resume, pause, reset; optional `duration` in seconds for reset |
| `set_final_check` | `id`, `checked` |
| `save_item` | `collection`, `id` (null for new), `values`: all editable collection fields |
| `remove_item` | `collection`, `id`, `confirm: true` |
| `import_session` | `state`: raw session, `confirm: true` |
| `reset_session` | `confirm: true` |

Errors use JSON `error`: invalid input 400, revision conflict 409, unknown route 404, incorrect content type 415, oversized request 413, and storage failure 503. Requests require JSON and Content-Length; bodies are limited to 256 KiB. Local Host headers are required. Mutations reject foreign Origins and cross-site fetches. There is no permissive CORS. A content security policy and text-node rendering reduce injection risk. Session content is not logged.

## Timers and persistence

All times use seconds. Running timers store absolute Unix `deadline` timestamps. `remaining` is the paused value or value at last start. While running, remaining time is `max(0, deadline - clock())`. Starting an already running timer is idempotent. Pause captures remaining time and clears the deadline; reset restores configured duration and clears the deadline. Member selection changes neither timer. Expired timers stay at zero until reset.

Browsers interpolate from `server_time` with `performance.now()` and catch up after throttled tabs. Polls and ticks never save state. After restart, deadlines remain unchanged: downtime counts for running timers; paused timers retain remaining time. Server clock adjustments can affect running timers, a tradeoff for simple restart-safe persistence.

The default file is `~/.sprintdeck/session.json`, outside the checkout. Invalid existing data fails startup rather than silently resetting. Atomic replacement is not a backup system; export before destructive changes. Run one process per file: locking protects threads, not multiple processes.

Polling avoids WebSocket complexity. There is no database, framework, external service, or build pipeline. Overlays scale a fixed 1920 x 1080 CSS canvas. Overview, Individual, Board Discussion, and Roadmap Review contain transparent capture slots. The largest fitting 16:9 aperture is centered in each slot using whole 16 x 9 pixel units. The outline sits outside the aperture; labels do not cover source pixels. Uniform scaling of a full 1920 x 1080 source preserves its content. Board Discussion and Roadmap Review use compact headers. Welcome is an opaque waiting screen with no application capture. Long presentation text is truncated; complete content remains editable and exportable.

Every overlay footer has a separate wall clock. It formats the viewing browser's local timezone with Intl.DateTimeFormat, including date, seconds, and timezone, and updates once per second without server writes. Meeting countdowns retain their server timestamp behavior.

The recap is generated deterministically from a deep-copied saved snapshot. It includes complete notes and explicit statuses without inferring agreements. User Markdown metacharacters and HTML are escaped. Save session & download recap first persists session notes through the normal API, then requests the attachment. Other unsaved form drafts block generation to avoid omission. Markdown is a report, not an import schema. Private notes are omitted from overlay rendering but are present in local shared state and the recap.
