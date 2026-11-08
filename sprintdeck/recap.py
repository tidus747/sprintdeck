"""Portable Markdown minutes generated from one saved session snapshot."""

import html
import re

from .state import derived


def escape(value):
    """Keep user text literal, including HTML and Markdown-looking meeting notes."""
    return re.sub(r"([\\`*_{}\[\]()#+\-!|>])", r"\\\1", html.escape(str(value), quote=False))


def render_recap(state):
    computed = derived(state, 0)
    sprint = state["sprint"]
    lines = [f"# {escape(state['session']['title'])}: {escape(sprint['next'])}", "",
             f"Session created: {state['session']['created']}",
             f"Sprint dates: {sprint['start']} to {sprint['end']}",
             f"Planning status: {escape(sprint['status'])}",
             f"Ceremony review: {'Ready for commitment' if computed['ready'] else 'Review still required'}", ""]

    def section(title, content):
        lines.extend([f"## {title}", "", escape(content) if content.strip() else "Not recorded.", ""])

    section("Sprint goal", sprint["goal"])
    section("Agreed commitment", sprint["commitment"])
    section("Session notes", state["session"]["notes"])
    for key, label in (("objective", "Shared sprint objective"), ("deliverables", "Expected deliverables"),
                       ("dependencies", "Dependencies"), ("risks", "Shared risks"),
                       ("notes", "Shared review notes"), ("pending_decisions", "Pending decisions")):
        section(label, state["planning"][key])

    for name, title in (("scope", "Committed scope"), ("risks", "Risks and attention points"),
                        ("decisions", "Decisions"), ("actions", "Next steps"), ("roadmap", "Roadmap")):
        lines.extend([f"## {title}", ""])
        for item in state[name]:
            marker = f"[{'x' if item['confirmed'] else ' '}] " if name == "scope" else ""
            details = [item.get("status"), f"Owner: {item['owner']}" if item.get("owner") else "",
                       f"Next action: {item['next_action']}" if item.get("next_action") else "",
                       f"Due: {item['due']}" if item.get("due") else "", item.get("date"), item.get("description")]
            suffix = " | ".join(escape(value) for value in details if value)
            text = escape(item.get("title", item.get("text", ""))).replace("\n", "\n  ")
            lines.append(f"- {marker}{text}" + (f" ({suffix.replace(chr(10), ' ')})" if suffix else ""))
        if not state[name]:
            lines.append("No items recorded.")
        lines.append("")

    lines.extend(["## Team review", ""])
    for value in computed["members"]:
        lines.extend([f"### {escape(value['name'])}", "", f"Status: {value['status']} | Checklist: {value['completion']}%", ""])
        if value["review_override"]:
            lines.extend(["Review completion overridden by facilitator.", ""])
        lines.extend(f"- [{'x' if item['checked'] else ' '}] {escape(item['label'])}" for item in value["checks"])
        lines.append("")
    if not computed["members"]:
        lines.extend(["No members configured.", ""])
    lines.extend(["## Holidays", ""])
    lines.extend(f"- {item['date']}: {escape(item['title'])}" for item in sorted(state["holidays"], key=lambda item: item["date"]))
    if not state["holidays"]:
        lines.append("No holidays configured.")
    lines.extend(["", "## Planned time off", ""])
    names = {value["id"]: value["name"] for value in state["members"]}
    for item in sorted(state["time_off"], key=lambda item: item["start"]):
        lines.append(f"- {escape(names[item['member_id']])}: {item['start']} to {item['end']}" +
                     (f" ({escape(item['note']).replace(chr(10), ' ')})" if item["note"] else ""))
    if not state["time_off"]:
        lines.append("No time off configured.")
    lines.extend(["", "## Final ceremony checklist", ""])
    lines.extend(f"- [{'x' if item['checked'] else ' '}] {escape(item['label'])}" for item in state["final_checks"])
    lines.append("")
    section("Current sprint summary", sprint["summary"])
    section("Carry-over work", sprint["carryover"])
    lines.extend(["Generated locally by SprintDeck from saved session data. Review before sharing.", ""])
    return "\n".join(lines)
