import json
import tempfile
import unittest
from pathlib import Path

from cost import message_cost, session_cost


class CostTests(unittest.TestCase):
    def test_message_cost_uses_calibrated_rates(self):
        usage = {
            "input_tokens": 100,
            "output_tokens": 200,
            "cache_read_input_tokens": 1000,
            "cache_creation": {"ephemeral_1h_input_tokens": 5000, "ephemeral_5m_input_tokens": 0},
        }
        # (100*3 + 200*15 + 1000*0.30 + 5000*6) / 1e6
        self.assertAlmostEqual(message_cost("claude-sonnet-5", usage), 0.0336)

    def test_1h_fallback_when_split_absent(self):
        usage = {"cache_creation_input_tokens": 5000}  # no nested split
        self.assertAlmostEqual(message_cost("claude-sonnet-5", usage), 5000 * 6 / 1e6)

    def test_session_dedupes_repeated_message_id(self):
        with tempfile.TemporaryDirectory() as d:
            projects = Path(d)
            (projects / "proj").mkdir()
            row = {
                "message": {
                    "id": "msg_dup",
                    "model": "claude-sonnet-5",
                    "usage": {"cache_creation_input_tokens": 5000,
                              "cache_creation": {"ephemeral_1h_input_tokens": 5000}},
                }
            }
            # Same message id written twice -> counted once.
            (projects / "proj" / "sess.jsonl").write_text(
                json.dumps(row) + "\n" + json.dumps(row) + "\n"
            )
            result = session_cost("sess", projects)
            self.assertAlmostEqual(result["total_cost"], 5000 * 6 / 1e6)
            self.assertEqual(result["raw_into_main"], 5000)


if __name__ == "__main__":
    unittest.main()
