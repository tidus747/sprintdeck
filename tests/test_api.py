from http.client import HTTPConnection
import json
from pathlib import Path
import tempfile
import threading
import unittest

from sprintdeck.server import MAX_BODY, Server
from sprintdeck.state import Store


class APITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.store = Store(Path(cls.temp.name) / "session.json")
        cls.server = Server(("127.0.0.1", 0), cls.store)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()
        cls.temp.cleanup()

    def request(self, method, path, body=None, headers=None):
        connection = HTTPConnection("127.0.0.1", self.server.server_port, timeout=3)
        connection.request(method, path, body, headers or {})
        response = connection.getresponse()
        data = response.read()
        result = response.status, dict(response.getheaders()), data
        connection.close()
        return result

    def post(self, action):
        return self.request("POST", "/api/actions", json.dumps(action), {"Content-Type": "application/json"})

    def test_health_and_presentation_routes(self):
        for route in ("/health", "/control", "/overlays/welcome", "/overlays/roadmap", "/overlays/overview", "/overlays/individual", "/overlays/wrapup", "/overlays/discussion", "/static/app.css", "/static/control.js", "/static/overlay.js", "/static/common.js", "/static/calendar.js", "/static/demo-session.json"):
            with self.subTest(route=route):
                status, headers, body = self.request("GET", route)
                self.assertEqual(status, 200)
                self.assertTrue(body)
                self.assertIn("Content-Security-Policy", headers)
                self.assertNotIn("Access-Control-Allow-Origin", headers)

    def test_shared_state_changes_and_export(self):
        value = self.store.export()
        selected = value["members"][1]["id"]
        status, _, data = self.post({"type": "select_member", "member_id": selected, "revision": value["revision"]})
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(data)["active_member"], selected)
        status, _, data = self.request("GET", "/api/state")
        self.assertEqual(json.loads(data)["active_member"], selected)
        status, _, data = self.request("GET", "/api/export")
        exported = json.loads(data)
        self.assertNotIn("server_time", exported)
        self.assertNotIn("status", exported["members"][0])

    def test_invalid_json_and_actions(self):
        for body in ("{", "null", "[]", '{"type": "unknown"}', '{"revision": {}}'):
            status, _, data = self.request("POST", "/api/actions", body, {"Content-Type": "application/json"})
            self.assertIn(status, (400, 409))
            self.assertIn("error", json.loads(data))
        status, _, _ = self.post({"type": "unknown", "revision": self.store.state["revision"]})
        self.assertEqual(status, 400)

    def test_conflict(self):
        status, _, _ = self.post({"type": "reset_session", "revision": -1, "confirm": True})
        self.assertEqual(status, 409)

    def test_markdown_recap_is_a_private_local_download(self):
        action = {"type": "update_session", "values": {"notes": "Agreed to prioritize automated testing."}, "revision": self.store.state["revision"]}
        self.assertEqual(self.post(action)[0], 200)
        status, headers, content = self.request("GET", "/api/recap")
        self.assertEqual(status, 200)
        self.assertIn("text/markdown", headers["Content-Type"])
        self.assertIn('filename="sprintdeck-recap.md"', headers["Content-Disposition"])
        self.assertIn("Agreed to prioritize automated testing.", content.decode("utf-8"))
        self.assertEqual(self.request("GET", "/api/recap", headers={"Host": "example.invalid"})[0], 403)

    def test_oversized_request(self):
        status, _, _ = self.request("POST", "/api/actions", "x" * (MAX_BODY + 1), {"Content-Type": "application/json"})
        self.assertEqual(status, 413)
        status, _, _ = self.request("POST", "/api/actions", b"", {"Content-Type": "application/json", "Content-Length": str(MAX_BODY * 100)})
        self.assertEqual(status, 413)

    def test_content_type_origin_host_and_routes(self):
        self.assertEqual(self.request("POST", "/api/actions", "{}")[0], 415)
        self.assertEqual(self.request("POST", "/api/actions", "{}", {"Content-Type": "application/json", "Origin": "https://example.invalid"})[0], 403)
        self.assertEqual(self.request("POST", "/api/actions", "{}", {"Content-Type": "application/json", "Sec-Fetch-Site": "cross-site"})[0], 403)
        self.assertEqual(self.request("GET", "/api/state", headers={"Host": "example.invalid"})[0], 403)
        self.assertEqual(self.request("GET", "/static/../../LICENSE")[0], 404)
        self.assertEqual(self.request("POST", "/api/unknown", "{}")[0], 404)
        self.assertEqual(self.request("GET", "/")[0], 302)

    def test_two_controllers_do_not_silently_overwrite(self):
        revision = self.store.state["revision"]
        action = {"type": "update_sprint", "values": {"goal": "Technical validation"}, "revision": revision}
        self.assertEqual(self.post(action)[0], 200)
        self.assertEqual(self.post(action)[0], 409)


if __name__ == '__main__':
    unittest.main()
