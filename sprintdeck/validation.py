"""Strict schema validation for persisted and imported sessions."""

from datetime import date
import json
import math

from .state import COLLECTIONS, LEGACY_COLLECTIONS, MEMBER_TEXT, PLANNING_TEXT, MILESTONE_COLORS, ValidationError, collection_limit


def require(condition, message):
    if not condition:
        raise ValidationError(message)


def text(value, limit=2000, nonempty=False):
    require(isinstance(value, str) and len(value) <= limit, f"Text must contain at most {limit} characters")
    require(not nonempty or bool(value.strip()), "Text must not be empty")
    require(chr(0x2014) not in value, "Use punctuation other than U+2014")
    return value


def number(value, low=0, high=10000):
    require(type(value) in (int, float) and math.isfinite(value) and low <= value <= high,
            f"Number must be finite and between {low} and {high}")


def fields(value, keys):
    require(isinstance(value, dict) and set(value) == set(keys), "Invalid object fields")


def boolean(value):
    require(type(value) is bool, "Expected a boolean")


def iso_date(value, optional=False):
    text(value, 10)
    if optional and not value:
        return
    try:
        require(date.fromisoformat(value).isoformat() == value, "Date must be YYYY-MM-DD")
    except ValueError as exc:
        raise ValidationError("Date must be YYYY-MM-DD") from exc


def validate_state(state):
    require(isinstance(state, dict), "Session must be an object")
    require(type(state.get("schema_version")) is int and state["schema_version"] in (1, 2), "Unsupported schema version")
    legacy = state["schema_version"] == 1
    collections = {key: COLLECTIONS[key] for key in LEGACY_COLLECTIONS} if legacy else COLLECTIONS
    fields(state, {"schema_version", "revision", "session", "sprint", "timers", "members",
                   "active_member", "final_checks", *collections, *([] if legacy else ["planning"])})
    require(type(state["revision"]) is int and state["revision"] >= 0, "Invalid revision")
    fields(state["session"], {"title", "created", *([] if legacy else ["notes"])})
    text(state["session"]["title"], 100, True)
    iso_date(state["session"]["created"])
    if not legacy:
        text(state["session"]["notes"], 16000)
        fields(state["planning"], PLANNING_TEXT)
        for value in state["planning"].values():
            text(value, 28000)
    sprint = state["sprint"]
    fields(sprint, {"current", "next", "start", "end", "goal", "status", "current_status", "summary", "carryover", "commitment"})
    for value in sprint.values():
        text(value)
    iso_date(sprint["start"])
    iso_date(sprint["end"])
    require(0 <= (date.fromisoformat(sprint["end"]) - date.fromisoformat(sprint["start"])).days <= 42,
            "Sprint must last between 1 and 43 calendar days")
    for key in ("current", "next", "status", "current_status"):
        text(sprint[key], 100, True)
    fields(state["timers"], {"meeting", "individual"})
    for value in state["timers"].values():
        fields(value, {"duration", "remaining", "deadline"})
        number(value["duration"], 1, 86400)
        number(value["remaining"], 0, value["duration"])
        if value["deadline"] is not None:
            number(value["deadline"], 0, 253402300799)

    ids = set()

    def unique(value):
        text(value, 100, True)
        require(value not in ids, "IDs must be unique across the session")
        ids.add(value)

    def checks(items):
        require(isinstance(items, list) and 1 <= len(items) <= 12, "Supply 1 to 12 checklist items")
        for item in items:
            fields(item, {"id", "label", "checked"})
            unique(item["id"])
            text(item["label"], 160, True)
            boolean(item["checked"])

    members = state["members"]
    require(isinstance(members, list) and len(members) <= 20, "At most 20 members are supported")
    for member in members:
        fields(member, {"id", *MEMBER_TEXT, "checks", "review_override", "confirmed",
                        *([*PLANNING_TEXT, "available", "assigned"] if legacy else [])})
        unique(member["id"])
        for key in MEMBER_TEXT:
            text(member[key], 100, key == "name")
        if legacy:
            for key in PLANNING_TEXT:
                text(member[key], 1200)
            number(member["available"], 0, 366)
            number(member["assigned"], 0, 366)
        boolean(member["review_override"])
        boolean(member["confirmed"])
        checks(member["checks"])
    require((not members and state["active_member"] is None)
            or any(m["id"] == state["active_member"] for m in members), "Active member must exist")
    checks(state["final_checks"])
    for name, keys in collections.items():
        items = state[name]
        require(isinstance(items, list) and len(items) <= collection_limit(name), f"At most {collection_limit(name)} items are supported in {name}")
        for item in items:
            item_keys = keys
            # Older sessions have no milestone color. Migration assigns blue after validation.
            if name == "roadmap" and (legacy or (isinstance(item, dict) and "color" not in item)):
                item_keys = keys - {"color"}
            fields(item, {"id", *item_keys})
            unique(item["id"])
            for key in item_keys:
                value = item[key]
                if key == "confirmed":
                    boolean(value)
                elif key in ("date", "due", "start", "end"):
                    iso_date(value, optional=name not in ("holidays", "time_off"))
                elif key == "member_id":
                    require(any(member["id"] == value for member in members), "Time off must refer to an existing member")
                elif key == "color":
                    require(isinstance(value, str) and value in MILESTONE_COLORS, "Choose a supported milestone color")
                else:
                    text(value, 400, key in ("title", "text"))
            if "status" in item:
                require(item["status"] in {"Planned", "In progress", "Confirmed", "Resolved", "Open"}, "Invalid item status")
            if name == "time_off":
                require(item["start"] <= item["end"], "Time off end must be on or after its start")
    require(len(json.dumps(state, indent=2, allow_nan=False).encode("utf-8")) <= 240000,
            "Session exceeds the 240,000-byte storage budget. Shorten notes or remove unused items before saving.")
