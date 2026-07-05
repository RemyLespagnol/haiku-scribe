from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = str(PROJECT_ROOT / "src")


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = SRC_DIR if not pythonpath else f"{SRC_DIR}{os.pathsep}{pythonpath}"
    return subprocess.run(
        [sys.executable, "-m", "haiku_scribe", *args],
        cwd=PROJECT_ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_uninstall_dry_run_writes_nothing(tmp_path: Path) -> None:
    assert run_cli("setup", "--home", str(tmp_path)).returncode == 0

    result = run_cli("uninstall", "--dry-run", "--home", str(tmp_path))

    assert result.returncode == 0
    assert "Dry run" in result.stdout
    assert (tmp_path / ".claude" / "agents" / "haiku-scribe.md").exists()


def test_uninstall_removes_agent_and_guidance_but_keeps_settings_and_user_content(tmp_path: Path) -> None:
    claude = tmp_path / ".claude"
    claude.mkdir()
    (claude / "CLAUDE.md").write_text("# My guidance\n", encoding="utf-8")
    (claude / "settings.json").write_text(
        '{"theme":"dark","permissions":{"deny":["Read(./private)"]}}',
        encoding="utf-8",
    )

    assert run_cli("setup", "--home", str(tmp_path)).returncode == 0

    result = run_cli("uninstall", "--home", str(tmp_path))

    assert result.returncode == 0
    assert not (claude / "agents" / "haiku-scribe.md").exists()
    guidance = (claude / "CLAUDE.md").read_text(encoding="utf-8")
    settings = json.loads((claude / "settings.json").read_text(encoding="utf-8"))
    assert "# My guidance" in guidance
    assert "HAIKU_SCRIBE_START" not in guidance
    assert settings["theme"] == "dark"
    assert "Read(./private)" in settings["permissions"]["deny"]


def test_uninstall_is_idempotent(tmp_path: Path) -> None:
    assert run_cli("setup", "--home", str(tmp_path)).returncode == 0

    first = run_cli("uninstall", "--home", str(tmp_path))
    second = run_cli("uninstall", "--home", str(tmp_path))

    assert first.returncode == 0
    assert second.returncode == 0
    assert "Nothing to remove" in second.stdout
