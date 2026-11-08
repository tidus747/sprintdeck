# Session notes and recap

The recap records what the facilitator entered. It does not infer decisions, summarize with AI, or automatically turn pending items into agreements.

## During the meeting

1. Record shared objectives, deliverables, dependencies, risks, review notes, and pending decisions in Overview. These are visible in the individual overlay.
2. Record explicit scope, risks, decisions, owners, and follow-up actions in Commitment.
3. Use Session notes & recap for private meeting minutes. Save notes persists the title and notes on the local server. These notes are not rendered on audience overlays.

## Save the recap

Save edited sections first, then select **Save session & download recap (.md)**. SprintDeck saves the notes and downloads `sprintdeck-recap.md`. If another form contains an unsaved draft, the controller blocks the download so that it cannot silently omit that draft. The notes and session are retained after download.

The report includes the goal, commitment, full notes, shared context, scope confirmation, risks, decisions, owners, next actions, due dates, roadmap, team review states, holidays, time off, and final checks. It preserves pending statuses and complete text even when presentation panels truncate it.

## Keep a restorable backup

Markdown is a readable meeting record. JSON is the restorable session format. Use Settings, Export session JSON to download `sprintdeck.session.json`, and import that file to restore a session later. See [configuration](configuration.md) for limits and migration behavior.

## Share deliberately

Recaps include private notes and may include names, vacation dates, and sensitive discussions. Review the file before sharing and keep real exports out of this public repository. The default recap filename is ignored by Git, as are `exports/` and `*.session.json`. See [privacy](privacy.md).
