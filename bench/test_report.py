import tempfile
import unittest
from pathlib import Path

from report import build_markdown_report, load_runs


class ReportTests(unittest.TestCase):
    def test_load_runs_reads_jsonl_files(self):
        with tempfile.TemporaryDirectory() as directory:
            runs_dir = Path(directory) / "runs"
            runs_dir.mkdir()
            (runs_dir / "sample.jsonl").write_text(
                '{"task_id":"01-orientation","mode":"agent-codegraph","tool_calls":2,'
                '"direct_file_reads":1,"large_outputs":0,"line_evidence_count":3,'
                '"found_right_area":true,"edit_ready":false,"estimated_context_cost":"low",'
                '"input_tokens":10,"output_tokens":20,"cache_creation_tokens":30,'
                '"cache_read_tokens":40,"gross_tokens":100,"no_cache_tokens":30}\n'
            )

            runs = load_runs(runs_dir)

            self.assertEqual(len(runs), 1)
            self.assertEqual(runs[0]["mode"], "agent-codegraph")

    def test_build_markdown_report_groups_by_task_and_mode(self):
        runs = [
            {
                "task_id": "01-orientation",
                "mode": "agent-codegraph",
                "tool_calls": 2,
                "direct_file_reads": 1,
                "large_outputs": 0,
                "line_evidence_count": 3,
                "found_right_area": True,
                "edit_ready": False,
                "estimated_context_cost": "low",
                "input_tokens": 10,
                "output_tokens": 20,
                "cache_creation_tokens": 30,
                "cache_read_tokens": 40,
                "gross_tokens": 100,
                "no_cache_tokens": 30,
            },
            {
                "task_id": "01-orientation",
                "mode": "agent-codegraph",
                "tool_calls": 4,
                "direct_file_reads": 1,
                "large_outputs": 0,
                "line_evidence_count": 1,
                "found_right_area": False,
                "edit_ready": True,
                "estimated_context_cost": "medium",
                "input_tokens": 20,
                "output_tokens": 30,
                "cache_creation_tokens": 40,
                "cache_read_tokens": 50,
                "gross_tokens": 140,
                "no_cache_tokens": 50,
            },
        ]

        markdown = build_markdown_report(runs)

        self.assertIn(
            "| 01-orientation | agent-codegraph | 2 | 3.0 | 1.0 | 0.0 | 2.0 | 50% | 50% | low:1, medium:1 | 120.0 | 40.0 | 15.0 | 25.0 | 35.0 | 45.0 |",
            markdown,
        )


if __name__ == "__main__":
    unittest.main()
