"""Shared state, derived values, deterministic timers, and atomic persistence."""

import copy
import json
import os
from pathlib import Path
import threading
import time
from datetime import date, timedelta
from uuid import uuid4

CHECKS = ["Sprint tasks are clearly defined", "Planned time off has been reviewed",
          "Dependencies have been identified", "Risks and blockers have been reviewed",
          "Sprint commitment has been confirmed"]
FINAL_CHECKS = ["Sprint goal agreed", "Calendar and time off reviewed", "Dependencies reviewed",
                "Risks recorded", "Individual commitments confirmed", "Next actions assigned"]
MEMBER_TEXT = ("name", "role")
PLANNING_TEXT = ("objective", "deliverables", "dependencies", "risks", "notes", "pending_decisions")
LEGACY_COLLECTIONS = ("roadmap", "scope", "risks", "decisions", "actions")
MILESTONE_COLORS = ("blue", "green", "purple", "orange", "red", "teal")
COLLECTIONS = {
    "roadmap": {"title", "date", "description", "status", "color"},
    "scope": {"title", "confirmed"},
    "risks": {"text", "owner", "next_action", "status"},
    "decisions": {"text", "owner", "status"},
    "actions": {"text", "owner", "due", "status"},
    "holidays": {"title", "date"},
    "time_off": {"member_id", "start", "end", "note"},
}


def collection_limit(name):
    return 60 if name in ("holidays", "time_off") else 12


class ValidationError(ValueError):
    """The request does not meet the state contract."""


def timer(duration):
    return {"duration": duration, "remaining": duration, "deadline": None}


def checklist(labels):
    return [{"id": str(uuid4()), "label": label, "checked": False} for label in labels]


def member(name):
    return {"id": str(uuid4()), **dict.fromkeys(MEMBER_TEXT, ""), "name": name,
            "checks": checklist(CHECKS),
            "review_override": False, "confirmed": False}


def initial_state(today=None):
    today = today or date.today()
    start = today + timedelta(days=(7 - today.weekday()) % 7)
    members = [member(f"Engineer {letter}") for letter in "ABCDE"]
    return {"schema_version": 2, "revision": 0,
            "session": {"title": "Sprint planning", "created": today.isoformat(), "notes": ""},
            "planning": dict.fromkeys(PLANNING_TEXT, ""),
            "sprint": {"current": "Sprint 01", "next": "Sprint 02", "start": start.isoformat(),
                       "end": (start + timedelta(days=13)).isoformat(), "goal": "",
                       "status": "Planning", "current_status": "In progress", "summary": "",
                       "carryover": "", "commitment": ""},
            "timers": {"meeting": timer(3600), "individual": timer(300)},
            "members": members, "active_member": members[0]["id"],
            **{key: [] for key in COLLECTIONS}, "final_checks": checklist(FINAL_CHECKS)}


def remaining(value, now):
    return max(0, value["deadline"] - now) if value["deadline"] is not None else value["remaining"]


def migrate_state(state):
    """Validate old sessions before upgrading shared context, preserving existing prose."""
    from .validation import validate_state
    validate_state(state)
    result = copy.deepcopy(state)
    for item in result["roadmap"]:
        item.setdefault("color", "blue")
    if result["schema_version"] == 2:
        return result
    result.update(schema_version=2, holidays=[], time_off=[])
    result["session"]["notes"] = ""
    result["planning"] = {}
    for key in PLANNING_TEXT:
        groups = {}
        for value in result["members"]:
            if value[key].strip():
                groups.setdefault(value[key], []).append(value["name"])
        # Identical former individual notes become one shared value. Different values keep attribution.
        result["planning"][key] = next(iter(groups)) if len(groups) == 1 else "\n\n".join(
            f"{', '.join(names)}:\n{value}" for value, names in groups.items())
    for value in result["members"]:
        for key in (*PLANNING_TEXT, "available", "assigned"):
            value.pop(key)
        for item in value["checks"]:
            if item["label"] == "Available capacity has been reviewed":
                item["label"] = CHECKS[1]
                item["checked"] = False
    for item in result["final_checks"]:
        if item["label"] == "Team capacity reviewed":
            item["label"] = FINAL_CHECKS[1]
            item["checked"] = False
    validate_state(result)
    return result


def review_status(value, active):
    complete = all(c["checked"] for c in value["checks"]) or value["review_override"]
    if complete and value["confirmed"]:
        return "Confirmed"
    if complete:
        return "Reviewed"
    return "In review" if value["id"] == active else "Pending"


def derived(state, now):
    result = copy.deepcopy(state)
    for value in result["timers"].values():
        value["seconds_left"] = remaining(value, now)
    for value in result["members"]:
        value["completion"] = round(sum(c["checked"] for c in value["checks"]) / len(value["checks"]) * 100)
        value["status"] = review_status(value, result["active_member"])
    result["progress"] = round(sum(m["completion"] for m in result["members"]) / len(result["members"])) if result["members"] else 0
    result["ready"] = bool(result["members"] and result["sprint"]["goal"].strip() and result["scope"]
                           and all(m["status"] == "Confirmed" for m in result["members"])
                           and all(c["checked"] for c in result["final_checks"])
                           and all(s["confirmed"] for s in result["scope"])
                           and not any(r["status"] != "Resolved" for r in result["risks"]))
    result["server_time"] = now
    return result


class Store:
    def __init__(self, path, clock=time.time):
        self.path = Path(path)
        self.clock = clock
        self.lock = threading.RLock()
        if self.path.exists():
            try:
                state = json.loads(self.path.read_text(encoding="utf-8"))
            except (ValueError, UnicodeError) as exc:
                raise ValidationError("Session file is not valid JSON. Restore a backup or choose another --data path.") from exc
            self.state = migrate_state(state)
            if self.state != state:
                self._persist(self.state)
        else:
            self.state = initial_state()
            self._persist(self.state)

    def _persist(self, state):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        try:
            with temporary.open("w", encoding="utf-8") as stream:
                json.dump(state, stream, indent=2, allow_nan=False)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
        finally:
            temporary.unlink(missing_ok=True)

    def snapshot(self):
        with self.lock:
            return derived(self.state, self.clock())

    def export(self):
        with self.lock:
            return copy.deepcopy(self.state)

    def apply(self, action):
        from .validation import validate_state, require, text, number
        with self.lock:
            require(isinstance(action, dict), "Action must be an object")
            require(type(action.get("revision")) is int and action["revision"] == self.state["revision"],
                    "Session changed. Refresh and try again.")
            state = copy.deepcopy(self.state)
            kind = action.get("type")
            target = next((m for m in state["members"] if m["id"] == action.get("member_id")), None)
            if kind == "update_sprint":
                patch = action.get("values")
                require(isinstance(patch, dict) and set(patch) <= set(state["sprint"]), "Unknown sprint field")
                state["sprint"].update(patch)
            elif kind in ("update_planning", "update_session"):
                section = "planning" if kind == "update_planning" else "session"
                patch = action.get("values")
                allowed = set(PLANNING_TEXT) if section == "planning" else {"title", "notes"}
                require(isinstance(patch, dict) and set(patch) <= allowed, "Unknown session or planning field")
                state[section].update(patch)
            elif kind == "select_member":
                require(target is not None, "Member does not exist")
                state["active_member"] = target["id"]
            elif kind == "navigate_member":
                require(action.get("direction") in (-1, 1), "Direction must be -1 or 1")
                ids = [m["id"] for m in state["members"]]
                require(bool(ids), "Add a member first")
                state["active_member"] = ids[(ids.index(state["active_member"]) + action["direction"]) % len(ids)]
            elif kind == "add_member":
                new_member = member(text(action.get("name"), 100, nonempty=True))
                if state["members"]:
                    new_member["checks"] = checklist([c["label"] for c in state["members"][0]["checks"]])
                state["members"].append(new_member)
                state["active_member"] = state["active_member"] or state["members"][-1]["id"]
            elif kind in ("update_member", "remove_member", "move_member", "set_check"):
                require(target is not None, "Member does not exist")
                if kind == "update_member":
                    patch = action.get("values")
                    require(isinstance(patch, dict) and set(patch) <= set(MEMBER_TEXT) | {"review_override", "confirmed"}, "Unknown member field")
                    target.update(patch)
                elif kind == "remove_member":
                    require(action.get("confirm") is True, "Removal needs confirmation")
                    state["members"].remove(target)
                    state["time_off"] = [item for item in state["time_off"] if item["member_id"] != target["id"]]
                    if state["active_member"] == target["id"]:
                        state["active_member"] = state["members"][0]["id"] if state["members"] else None
                elif kind == "move_member":
                    require(action.get("direction") in (-1, 1), "Direction must be -1 or 1")
                    index = state["members"].index(target)
                    new_index = max(0, min(len(state["members"]) - 1, index + action["direction"]))
                    state["members"].insert(new_index, state["members"].pop(index))
                else:
                    item = next((c for c in target["checks"] if c["id"] == action.get("id")), None)
                    require(item is not None, "Checklist item does not exist")
                    item["checked"] = action.get("checked")
            elif kind == "configure_checks":
                labels = action.get("labels")
                require(isinstance(labels, list) and 1 <= len(labels) <= 12, "Supply 1 to 12 checklist labels")
                for label in labels:
                    text(label, 160, nonempty=True)
                require(action.get("confirm") is True, "Replacing checklists needs confirmation")
                for value in state["members"]:
                    value.update(checks=checklist(labels), review_override=False, confirmed=False)
            elif kind == "timer":
                require(action.get("timer") in state["timers"], "Unknown timer")
                value = state["timers"][action["timer"]]
                operation = action.get("operation")
                if operation in ("start", "resume"):
                    if value["deadline"] is None:
                        value["deadline"] = self.clock() + value["remaining"]
                elif operation == "pause":
                    value["remaining"] = remaining(value, self.clock())
                    value["deadline"] = None
                elif operation == "reset":
                    duration = action.get("duration", value["duration"])
                    number(duration, 1, 86400)
                    value.update(timer(duration))
                else:
                    raise ValidationError("Unsupported timer operation")
            elif kind == "set_final_check":
                item = next((c for c in state["final_checks"] if c["id"] == action.get("id")), None)
                require(item is not None, "Checklist item does not exist")
                item["checked"] = action.get("checked")
            elif kind in ("save_item", "remove_item"):
                collection = action.get("collection")
                require(collection in COLLECTIONS, "Unknown collection")
                items = state[collection]
                item = next((i for i in items if i["id"] == action.get("id")), None)
                if kind == "remove_item":
                    require(item is not None and action.get("confirm") is True, "Removal needs an existing item and confirmation")
                    items.remove(item)
                else:
                    values = action.get("values")
                    require(isinstance(values, dict) and set(values) == COLLECTIONS[collection], "Supply all collection fields")
                    if item is None:
                        require(action.get("id") is None, "Item does not exist")
                        items.append({"id": str(uuid4()), **values})
                    else:
                        item.update(values)
            elif kind == "import_session":
                require(action.get("confirm") is True, "Import needs confirmation")
                state = migrate_state(action.get("state"))
            elif kind == "reset_session":
                require(action.get("confirm") is True, "Reset needs confirmation")
                state = initial_state()
            else:
                raise ValidationError("Unsupported action")
            state["revision"] = self.state["revision"] + 1
            validate_state(state)
            self._persist(state)
            self.state = state
            return derived(state, self.clock())
