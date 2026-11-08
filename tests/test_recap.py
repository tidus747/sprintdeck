import copy
import unittest

from sprintdeck.recap import render_recap
from sprintdeck.state import initial_state


class RecapTests(unittest.TestCase):
    def test_full_notes_agreements_and_follow_ups_without_mutation(self):
        value = initial_state()
        value["session"]["notes"] = "Discussed validation.\nAgreed on testing.\n" + "Detailed note. " * 500
        value["planning"]["dependencies"] = "Platform integration"
        value["sprint"].update(goal="Release readiness", commitment="Prioritize automated testing")
        value["scope"] = [{"id": "scope", "title": "Testing", "confirmed": False}]
        value["decisions"] = [{"id": "decision", "text": "Review documentation", "owner": "Engineer A", "status": "Confirmed"}]
        value["risks"] = [{"id": "risk", "text": "Validation pending", "owner": "Engineer B", "next_action": "Review the plan", "status": "Open"}]
        value["actions"] = [{"id": "action", "text": "Follow up", "owner": "Engineer C", "due": "2030-04-05", "status": "Open"}]
        value["holidays"] = [{"id": "holiday", "date": "2030-04-05", "title": "Example holiday"}]
        value["time_off"] = [{"id": "leave", "member_id": value["members"][0]["id"], "start": "2030-04-01", "end": "2030-04-02", "note": "Planned leave"}]
        before = copy.deepcopy(value)
        report = render_recap(value)
        for text in (value["session"]["notes"], "Platform integration", "Release readiness", "Prioritize automated testing", "[ ] Testing", "Review documentation", "Owner: Engineer A", "Next action: Review the plan", "Due: 2030", "Example holiday", "Planned leave", "Review still required"):
            self.assertIn(text, report)
        self.assertEqual(value, before)
        self.assertEqual(report, render_recap(value))
        self.assertNotIn("capacity", report.lower())

    def test_empty_and_hostile_text_remains_literal(self):
        value = initial_state()
        value["session"]["notes"] = '<script>alert(1)</script>\n## Fake agreement\n[x] Confirmed'
        report = render_recap(value)
        self.assertNotIn("<script>", report)
        self.assertNotIn("\n## Fake agreement", report)
        self.assertIn("&lt;script&gt;", report)
        self.assertIn("No items recorded.", report)
        self.assertIn("Review still required", report)
