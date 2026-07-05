import tempfile
import unittest
from pathlib import Path

from haiku_scribe_sample.agent_config import default_agent_config, render_agent_markdown
from haiku_scribe_sample.doctor import doctor_report
from haiku_scribe_sample.installer import install_config
from haiku_scribe_sample.settings_merge import merge_deny_rules


class SampleCliTests(unittest.TestCase):
    def test_render_agent_markdown_includes_read_only_contract(self):
        markdown = render_agent_markdown(default_agent_config())

        self.assertIn("name: haiku-scribe", markdown)
        self.assertIn("model: haiku", markdown)
        self.assertIn("tools: Read, Glob, Grep", markdown)
        self.assertIn("Write", markdown)
        self.assertIn("Bash", markdown)

    def test_merge_deny_rules_preserves_existing_settings(self):
        settings = {"permissions": {"allow": ["Read(src/**)"], "deny": ["Read(.env)"]}}

        merged = merge_deny_rules(settings, ["Read(.env)", "Read(**/*.pem)"])

        self.assertEqual(merged["permissions"]["allow"], ["Read(src/**)"])
        self.assertEqual(merged["permissions"]["deny"], ["Read(.env)", "Read(**/*.pem)"])

    def test_install_config_writes_agent_and_settings(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            result = install_config(home)

            self.assertEqual(result.agent_path, home / ".claude" / "agents" / "haiku-scribe.md")
            self.assertEqual(result.settings_path, home / ".claude" / "settings.json")
            self.assertTrue(result.agent_path.exists())
            self.assertTrue(result.settings_path.exists())

    def test_doctor_report_detects_safe_install(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            install_config(home)

            report = doctor_report(home)

            self.assertTrue(report.ok)
            self.assertEqual(report.failures, [])


if __name__ == "__main__":
    unittest.main()
