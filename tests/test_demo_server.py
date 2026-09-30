import json
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from demo_server import DemoHandler, DemoServer


class DemoServerTests(unittest.TestCase):
    def setUp(self):
        self.server = DemoServer(("127.0.0.1", 0), DemoHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def get_state(self):
        with urlopen(f"{self.base}/api/state") as response:
            return json.loads(response.read())

    def post_review(self, payload):
        request = Request(f"{self.base}/api/review", data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"}, method="POST")
        return urlopen(request)

    def test_local_page_and_state_serve_the_existing_core_results(self):
        with urlopen(self.base) as response:
            html = response.read().decode()
            self.assertEqual(response.status, 200)
            self.assertIn("Fictional working paper", html)
            self.assertEqual(response.headers["Content-Security-Policy"].split(";")[0], "default-src 'self'")
        state = self.get_state()
        self.assertEqual(len(state["items"]), 10)
        self.assertEqual(state["proposals"][0]["source"], "synthetic-mock")
        self.assertTrue(state["proposal_validation"][0]["valid"])

    def test_human_decision_is_cited_and_does_not_change_deterministic_state(self):
        before = self.get_state()
        result = json.loads(self.post_review({"item_id": "WI-002", "action": "edit", "value": "Security Team (provisional)", "rationale": "Confirm alias with service owner.", "reviewer": "Local reviewer"}).read())
        self.assertEqual(result["items"], before["items"])
        decision = result["human_decisions"][-1]
        self.assertEqual(decision["citation"], {"evidence_id": "EV-002", "locator": "row:2", "revision": "r1"})
        self.assertEqual(decision["action"], "edit")

    def test_unknown_fields_and_missing_rationale_cannot_submit_decisions(self):
        for payload in (
            {"item_id": "WI-002", "action": "accept", "rationale": "Checked", "reviewer": "Local", "state": "complete"},
            {"item_id": "WI-002", "action": "accept", "reviewer": "Local"},
            {"item_id": "WI-002", "action": [], "rationale": "Checked", "reviewer": "Local"},
        ):
            with self.assertRaises(HTTPError) as rejected:
                self.post_review(payload)
            self.assertEqual(rejected.exception.code, 400)
        self.assertEqual(self.get_state()["human_decisions"], [])


if __name__ == "__main__":
    unittest.main()

