import copy
from datetime import date
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from sprintdeck.state import Store, ValidationError, initial_state, migrate_state, PLANNING_TEXT
from sprintdeck.validation import validate_state


class StateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "session.json"
        self.now = 1000
        self.store = Store(self.path, clock=lambda: self.now)
        self.first, self.second = [m["id"] for m in self.store.state["members"][:2]]

    def act(self, kind, **values):
        return self.store.apply({"type": kind, "revision": self.store.state["revision"], **values})

    def test_initial_state_dates_and_serialization(self):
        value = initial_state(date(2032, 12, 29))
        self.assertEqual(value["sprint"]["start"], "2033-01-03")
        self.assertEqual(value["sprint"]["end"], "2033-01-16")
        self.assertEqual(len(value["members"]), 5)
        self.assertEqual(json.loads(json.dumps(value)), value)
        validate_state(value)

    def test_demo_load_and_persistence(self):
        demo = json.loads((Path(__file__).resolve().parents[1] / "examples/demo-session.json").read_text())
        self.act("import_session", state=demo, confirm=True)
        restored = Store(self.path, clock=lambda: self.now)
        self.assertEqual(restored.export(), self.store.export())
        self.assertTrue(restored.snapshot()["sprint"]["goal"])

    def test_corrupt_file_is_preserved(self):
        self.path.write_text("not json")
        with self.assertRaises(ValidationError):
            Store(self.path)
        self.assertEqual(self.path.read_text(), "not json")

    def test_unknown_action_and_stale_revision(self):
        with self.assertRaises(ValidationError):
            self.act("unsupported")
        with self.assertRaises(ValidationError):
            self.store.apply({"type": "reset_session", "revision": -1, "confirm": True})
        with self.assertRaises(ValidationError):
            self.store.apply([])

    def test_navigation_add_reorder_remove(self):
        self.assertEqual(self.act("navigate_member", direction=1)["active_member"], self.second)
        self.assertEqual(self.act("navigate_member", direction=-1)["active_member"], self.first)
        self.assertEqual(self.act("select_member", member_id=self.second)["active_member"], self.second)
        value = self.act("add_member", name="Engineer F")
        new_id = value["members"][-1]["id"]
        self.act("move_member", member_id=new_id, direction=-1)
        self.assertEqual(self.store.state["members"][-2]["id"], new_id)
        self.act("remove_member", member_id=self.second, confirm=True)
        self.assertEqual(self.store.state["active_member"], self.first)

    def test_empty_team_safe(self):
        for item in list(self.store.state["members"]):
            self.act("remove_member", member_id=item["id"], confirm=True)
        value = self.store.snapshot()
        self.assertIsNone(value["active_member"])
        self.assertEqual(value["progress"], 0)
        self.assertFalse(value["ready"])
        value = self.act("add_member", name="Engineer A")
        self.assertEqual(value["active_member"], value["members"][0]["id"])

    def test_checklist_isolation_and_completion(self):
        checks = self.store.state["members"][0]["checks"]
        self.act("set_check", member_id=self.first, id=checks[0]["id"], checked=True)
        self.act("select_member", member_id=self.second)
        value = self.act("select_member", member_id=self.first)
        self.assertEqual(value["members"][0]["completion"], 20)
        self.assertEqual(value["members"][1]["completion"], 0)
        for item in checks:
            value = self.act("set_check", member_id=self.first, id=item["id"], checked=True)
        self.assertEqual(value["members"][0]["status"], "Reviewed")
        self.assertEqual(value["members"][0]["completion"], 100)
        value = self.act("update_member", member_id=self.first, values={"confirmed": True})
        self.assertEqual(value["members"][0]["status"], "Confirmed")
        value = self.act("set_check", member_id=self.first, id=checks[0]["id"], checked=False)
        self.assertNotEqual(value["members"][0]["status"], "Confirmed")

    def test_explicit_override_and_template(self):
        value = self.act("update_member", member_id=self.first, values={"confirmed": True})
        self.assertNotEqual(value["members"][0]["status"], "Confirmed")
        value = self.act("update_member", member_id=self.first, values={"review_override": True})
        self.assertEqual(value["members"][0]["status"], "Confirmed")
        self.act("configure_checks", labels=["Tasks reviewed", "Capacity reviewed"], confirm=True)
        value = self.act("add_member", name="Engineer F")
        self.assertEqual([c["label"] for c in value["members"][-1]["checks"]], ["Tasks reviewed", "Capacity reviewed"])
        self.assertFalse(value["members"][0]["confirmed"])

    def test_capacity_is_removed_from_state_and_actions(self):
        value = self.store.snapshot()
        self.assertNotIn("capacity", value)
        self.assertNotIn("capacity", value["members"][0])
        self.assertNotIn("available", value["members"][0])
        with self.assertRaises(ValidationError):
            self.act("update_member", member_id=self.first, values={"available": 10})

    def test_shared_context_and_private_session_notes_survive_navigation_and_reload(self):
        self.act("update_planning", values={"objective": "Release readiness", "dependencies": "Technical validation"})
        self.act("update_session", values={"notes": "Agreed to prioritize testing.\nFollow up on validation."})
        self.act("select_member", member_id=self.second)
        restored = Store(self.path).snapshot()
        self.assertEqual(restored["planning"]["objective"], "Release readiness")
        self.assertIn("Follow up", restored["session"]["notes"])
        self.assertEqual(restored["active_member"], self.second)

    def test_validation_rollback(self):
        before = self.store.export()
        for values in ({"available": -1}, {"assigned": float('nan')}, {"name": ""}, {"confirmed": "yes"}, {"unknown": 1}):
            with self.subTest(values=values), self.assertRaises(ValidationError):
                self.act("update_member", member_id=self.first, values=values)
            self.assertEqual(before, self.store.export())
        with self.assertRaises(ValidationError):
            self.act("update_sprint", values={"end": "1900-01-01"})
        with self.assertRaises(ValidationError):
            self.act("set_check", member_id=self.first, id=self.store.state["members"][0]["checks"][0]["id"], checked="true")

    def test_import_schema_rejects_unknown_duplicate_and_derived_fields(self):
        for mutate in [lambda s: s.update(unknown=1),
                       lambda s: s["members"][1].update(id=s["members"][0]["id"]),
                       lambda s: s.update(members="invalid"),
                       lambda s: s.update(schema_version=3),
                       lambda s: s["members"][0].update(capacity={})]:
            bad = self.store.export(); mutate(bad)
            with self.assertRaises(ValidationError):
                self.act("import_session", state=bad, confirm=True)

    def test_atomic_save_failure_does_not_change_memory_or_file(self):
        before = self.path.read_bytes()
        state = self.store.export()
        with patch('sprintdeck.state.os.replace', side_effect=OSError('write failed')):
            with self.assertRaises(OSError):
                self.act("update_sprint", values={"goal": "New goal"})
        self.assertEqual(self.store.export(), state)
        self.assertEqual(self.path.read_bytes(), before)

    def test_session_budget_keeps_exports_importable(self):
        large = self.store.export()
        large["planning"].update(notes=chr(0x6F22) * 28000, deliverables=chr(0x6F22) * 28000)
        with self.assertRaisesRegex(ValidationError, "storage budget"):
            self.act("import_session", state=large, confirm=True)

    def test_reset_requires_confirmation(self):
        self.act("update_sprint", values={"goal": "Example goal"})
        with self.assertRaises(ValidationError):
            self.act("reset_session")
        value = self.act("reset_session", confirm=True)
        self.assertEqual(value["sprint"]["goal"], "")
        self.assertEqual(len(value["members"]), 5)

    def test_collection_create_update_delete(self):
        value = self.act("save_item", collection="risks", values={"text": "Technical validation", "owner": "Engineer A", "next_action": "Review", "status": "Open"})
        item = value["risks"][0]
        self.act("save_item", collection="risks", id=item["id"], values={k: v if k != "status" else "Resolved" for k, v in item.items() if k != "id"})
        self.assertEqual(self.store.state["risks"][0]["status"], "Resolved")
        self.act("remove_item", collection="risks", id=item["id"], confirm=True)
        self.assertEqual(self.store.state["risks"], [])

    def test_milestone_colors_persist_and_reject_unsafe_values(self):
        fields = {"title": "Release readiness", "date": "2030-04-12", "description": "Technical validation", "status": "Planned", "color": "purple"}
        value = self.act("save_item", collection="roadmap", values=fields)
        item_id = value["roadmap"][0]["id"]
        self.assertEqual(Store(self.path).export()["roadmap"][0]["color"], "purple")
        value = self.act("save_item", collection="roadmap", id=item_id, values={**fields, "color": "teal"})
        self.assertEqual(value["roadmap"][0]["color"], "teal")
        before = self.store.export()
        for color in ("url(example.invalid)", "#ffffff", [], None):
            with self.subTest(color=color), self.assertRaises(ValidationError):
                self.act("save_item", collection="roadmap", id=item_id, values={**fields, "color": color})
            self.assertEqual(self.store.export(), before)

    def test_old_milestones_receive_a_default_without_losing_content(self):
        for version in (1, 2):
            old = self.legacy_state() if version == 1 else self.store.export()
            old["roadmap"] = [{"id": "old-milestone", "title": "Testing", "date": "2030-04-12", "description": "Keep this description", "status": "In progress"}]
            converted = migrate_state(old)
            self.assertEqual(converted["roadmap"][0], {**old["roadmap"][0], "color": "blue"})
            self.path.write_text(json.dumps(old), encoding="utf-8")
            self.assertEqual(Store(self.path).export()["roadmap"][0]["color"], "blue")

    def test_ready_requires_actual_commitments_scope_goal_and_checks(self):
        for item in self.store.export()["final_checks"]:
            self.act("set_final_check", id=item["id"], checked=True)
        self.assertFalse(self.store.snapshot()["ready"])
        for item in self.store.export()["members"]:
            for check in item["checks"]:
                self.act("set_check", member_id=item["id"], id=check["id"], checked=True)
            self.act("update_member", member_id=item["id"], values={"confirmed": True})
        self.act("update_sprint", values={"goal": "Release readiness"})
        self.act("save_item", collection="scope", values={"title": "Automated testing", "confirmed": True})
        self.assertTrue(self.store.snapshot()["ready"])
        self.act("save_item", collection="risks", values={"text": "Validation needed", "owner": "", "next_action": "", "status": "Open"})
        self.assertFalse(self.store.snapshot()["ready"])

    def legacy_state(self):
        legacy = self.store.export()
        legacy["schema_version"] = 1
        for key in ("planning", "holidays", "time_off"):
            legacy.pop(key)
        legacy["session"].pop("notes")
        for value in legacy["members"]:
            value.update(dict.fromkeys(PLANNING_TEXT, "Shared example"))
            value.update(available=10, assigned=2)
            value["checks"][1].update(label="Available capacity has been reviewed", checked=True)
        legacy["final_checks"][1].update(label="Team capacity reviewed", checked=True)
        return legacy

    def test_legacy_import_preserves_text_ids_and_timer(self):
        legacy = self.legacy_state()
        legacy["members"][0]["objective"] = "Automated testing"
        legacy["timers"]["individual"].update(deadline=1300)
        original = copy.deepcopy(legacy)
        value = self.act("import_session", state=legacy, confirm=True)
        self.assertEqual(value["schema_version"], 2)
        self.assertEqual(value["members"][0]["id"], self.first)
        self.assertIn("Engineer A:\nAutomated testing", value["planning"]["objective"])
        self.assertEqual(value["planning"]["dependencies"], "Shared example")
        self.assertEqual(value["timers"]["individual"]["deadline"], 1300)
        self.assertFalse(value["members"][0]["checks"][1]["checked"])
        self.assertFalse(value["final_checks"][1]["checked"])
        self.assertEqual(legacy, original)

    def test_legacy_file_is_upgraded_and_remains_reloadable(self):
        self.path.write_text(json.dumps(self.legacy_state()), encoding="utf-8")
        upgraded = Store(self.path).export()
        self.assertEqual(upgraded["schema_version"], 2)
        self.assertEqual(Store(self.path).export(), upgraded)
        self.assertEqual(json.loads(self.path.read_text())["schema_version"], 2)
        bad = self.legacy_state()
        bad["members"][0]["available"] = "bad"
        with self.assertRaises(ValidationError):
            migrate_state(bad)

    def test_holidays_and_time_off_validation_and_removal(self):
        self.act("save_item", collection="holidays", values={"title": "Example holiday", "date": "2032-02-29"})
        self.act("save_item", collection="time_off", values={"member_id": self.first, "start": "2032-02-28", "end": "2032-03-02", "note": "Planned leave"})
        restored = Store(self.path).export()
        self.assertEqual(restored["time_off"][0]["member_id"], self.first)
        for values in ({"member_id": "missing", "start": "2032-02-28", "end": "2032-03-02", "note": ""},
                       {"member_id": self.first, "start": "2032-03-02", "end": "2032-03-01", "note": ""},
                       {"member_id": self.first, "start": "invalid", "end": "2032-03-01", "note": ""}):
            with self.assertRaises(ValidationError):
                self.act("save_item", collection="time_off", values=values)
        with self.assertRaises(ValidationError):
            self.act("save_item", collection="holidays", values={"title": "Example holiday", "date": "2031-02-29"})
        self.act("remove_member", member_id=self.first, confirm=True)
        self.assertEqual(self.store.export()["time_off"], [])


if __name__ == '__main__':
    unittest.main()
