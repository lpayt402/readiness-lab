import copy
import json
import tempfile
import unittest
from pathlib import Path

from readiness_lab import analyze, record_review, render_report, validate_proposal


ROOT = Path(__file__).parents[1]


class ReadinessLabTests(unittest.TestCase):
    def setUp(self):
        self.pack = json.loads((ROOT / "fixtures" / "gizmo_cloud.json").read_text())

    def test_fixture_has_ten_illustrative_items_and_synthetic_boundary(self):
        self.assertEqual(len(self.pack["items"]), 10)
        self.assertTrue(self.pack["synthetic_only"])
        self.assertIn("fictional", self.pack["service"]["name"].lower())

    def test_analysis_flags_missing_owner_stale_duplicate_conflict_and_unknown(self):
        result = analyze(self.pack, today="2026-09-30")
        codes = {finding["code"] for item in result["items"] for finding in item["findings"]}
        self.assertTrue({"missing_owner", "stale_evidence", "possible_duplicate", "conflicting_claims", "unknown_state"} <= codes)
        inventory = next(item for item in result["items"] if item["id"] == "WI-003")
        self.assertEqual(sum(f["code"] == "possible_duplicate" for f in inventory["findings"]), 1)

    def test_prompt_injection_in_evidence_is_retained_as_data(self):
        note = next(e for e in self.pack["evidence"] if e["id"] == "EV-010")
        self.assertIn("ignore previous instructions", note["text"].lower())
        result = analyze(self.pack, today="2026-09-30")
        self.assertTrue(any(f["code"] == "instruction_like_text" for i in result["items"] for f in i["findings"]))
        self.assertEqual(result["human_decisions"], [])

    def test_malformed_pack_is_rejected_before_analysis(self):
        malformed = copy.deepcopy(self.pack)
        malformed["items"][0]["id"] = ""
        with self.assertRaisesRegex(ValueError, "item id"):
            analyze(malformed, today="2026-09-30")

    def test_malformed_item_shape_is_rejected_with_domain_error(self):
        malformed = copy.deepcopy(self.pack)
        malformed["items"][0] = "not-an-object"
        with self.assertRaisesRegex(ValueError, "item must be an object"):
            analyze(malformed, today="2026-09-30")

    def test_unknown_item_state_is_not_coerced_to_open_or_closed(self):
        malformed = copy.deepcopy(self.pack)
        malformed["items"][0]["state"] = "approved-by-model"
        with self.assertRaisesRegex(ValueError, "unknown state"):
            analyze(malformed, today="2026-09-30")

    def test_invalid_dates_and_non_string_states_are_rejected(self):
        malformed = copy.deepcopy(self.pack)
        malformed["items"][0]["due_date"] = "soon"
        with self.assertRaisesRegex(ValueError, "invalid due_date"):
            analyze(malformed, today="2026-09-30")
        malformed = copy.deepcopy(self.pack)
        malformed["items"][0]["state"] = []
        with self.assertRaisesRegex(ValueError, "unknown state"):
            analyze(malformed, today="2026-09-30")

    def test_proposal_requires_exact_locator_and_revision(self):
        result = analyze(self.pack, today="2026-09-30")
        valid = {"item_id": "WI-002", "suggestion": "Security Team", "citation": {"evidence_id": "EV-002", "locator": "row:2", "revision": "r1"}, "confidence": 0.42, "source": "synthetic-mock"}
        self.assertTrue(validate_proposal(valid, result, self.pack)["valid"])
        invented = copy.deepcopy(valid)
        invented["citation"]["evidence_id"] = "EV-999"
        self.assertFalse(validate_proposal(invented, result, self.pack)["valid"])
        mismatch = copy.deepcopy(valid)
        mismatch["citation"]["revision"] = "r0"
        self.assertFalse(validate_proposal(mismatch, result, self.pack)["valid"])

    def test_human_review_is_explicit_and_provenance_bearing(self):
        result = analyze(self.pack, today="2026-09-30")
        proposal = {"item_id": "WI-002", "suggestion": "Security Team", "citation": {"evidence_id": "EV-002", "locator": "row:2", "revision": "r1"}, "confidence": 0.42, "source": "synthetic-mock"}
        updated = record_review(result, proposal, pack=self.pack, action="edit", rationale="Owner alias is plausible; confirm with service owner.", reviewer="demo-reviewer", accepted_value="Security Team (provisional)")
        self.assertEqual(updated["human_decisions"][0]["action"], "edit")
        self.assertEqual(updated["human_decisions"][0]["proposal_source"], "synthetic-mock")
        self.assertEqual(updated["human_decisions"][0]["rationale"], "Owner alias is plausible; confirm with service owner.")
        self.assertEqual(updated["items"], result["items"])
        output = render_report(updated, self.pack)
        self.assertIn("SYNTHETIC WORKING PAPER", output)
        self.assertIn("not an assessment", output.lower())
        self.assertIn("EV-002@r1#row:2", output)

    def test_mock_suggestion_is_visible_in_review_output_with_its_citation(self):
        result = analyze(self.pack, today="2026-09-30")
        proposal = {"item_id": "WI-002", "suggestion": "Security Team (candidate alias)", "citation": {"evidence_id": "EV-002", "locator": "row:2", "revision": "r1"}, "confidence": 0.42, "source": "synthetic-mock", "uncertainty": "Illustrative fixture only; confirm with a human."}
        result["proposals"] = [proposal]
        result["proposal_validation"] = [validate_proposal(proposal, result, self.pack)]
        output = render_report(result, self.pack)
        self.assertIn("PENDING HUMAN REVIEW", output)
        self.assertIn("Security Team (candidate alias)", output)
        self.assertIn("synthetic-mock", output)
        self.assertIn("EV-002@r1#row:2", output)

    def test_unknown_human_action_is_rejected(self):
        result = analyze(self.pack, today="2026-09-30")
        proposal = {"item_id": "WI-002", "suggestion": "candidate", "citation": {"evidence_id": "EV-002", "locator": "row:2", "revision": "r1"}, "confidence": 0.42, "source": "synthetic-mock"}
        with self.assertRaisesRegex(ValueError, "action must be"):
            record_review(result, proposal, pack=self.pack, action="approve_everything", rationale="No", reviewer="reviewer")

    def test_direct_review_rejects_invented_citation_and_changed_source(self):
        result = analyze(self.pack, today="2026-09-30")
        proposal = {"item_id": "WI-002", "suggestion": "candidate", "citation": {"evidence_id": "EV-999", "locator": "row:2", "revision": "r1"}, "confidence": 0.42, "source": "synthetic-mock"}
        with self.assertRaisesRegex(ValueError, "proposal citation"):
            record_review(result, proposal, pack=self.pack, action="accept", rationale="Checked", reviewer="reviewer")
        self.assertEqual(result["human_decisions"], [])
        changed = copy.deepcopy(self.pack)
        changed["evidence"][1]["text"] += " Revised text without a revision bump."
        proposal["citation"]["evidence_id"] = "EV-002"
        with self.assertRaisesRegex(ValueError, "source pack changed"):
            record_review(result, proposal, pack=changed, action="accept", rationale="Checked", reviewer="reviewer")
        tampered = copy.deepcopy(result)
        tampered["items"][1]["state"] = "complete"
        with self.assertRaisesRegex(ValueError, "analysis state"):
            record_review(tampered, proposal, pack=self.pack, action="accept", rationale="Checked", reviewer="reviewer")


if __name__ == "__main__":
    unittest.main()

