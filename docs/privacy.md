# Privacy

SprintDeck is local-first. It has no telemetry, analytics, external scripts, fonts, accounts, project management APIs, or automatic updates. Runtime pages request only local server resources. SprintDeck sends no meeting data to external services.

The server listens on 127.0.0.1. Its unauthenticated API is available to local processes. Host validation, JSON requests, Origin checks, and no permissive CORS help prevent browser cross-site mutations. These are not authentication or protection against malicious local software. Do not expose the server through a tunnel or public reverse proxy. The controller is private by intended local use, not by an account boundary.

The session file contains sprint details, names, checklists, shared objectives and context, private session notes, holidays, time-off dates, risks, decisions, actions, and timers. Capacity is managed in the captured application instead. Data defaults to `~/.sprintdeck/session.json`, outside the checkout, unless overridden with `--data`. SprintDeck does not encrypt it; OS permissions and device access determine who can read it.

`.session/`, `sessions/`, `imports/`, `exports/`, `*.session.json`, and root-level `sprintdeck-recap*.md` downloads are ignored by Git. Keep imports and exports there. Arbitrary JSON or Markdown filenames elsewhere are not automatically ignored. Never commit real company, employee, customer, project, or meeting data, credentials, or private configuration. The tracked example is fictional only.

JSON exports and Markdown recaps can disclose all entered meeting information, including vacation dates and private notes. Review before sharing. Session notes are not rendered on presentation overlays, but local pages share the same unauthenticated server; this is not an access-control boundary. Shared review notes are intentionally presented. OBS recordings, screenshots, and screen sharing may reveal shared context and captured application content. Keep the controller off the shared screen.

To delete data, stop SprintDeck, delete the configured session file, and remove backups and exports you created. Next startup creates a blank session. Reset in Settings replaces saved state but does not erase backups or recordings. Deletion does not guarantee forensic erasure from storage, backups, or synchronized folders.
