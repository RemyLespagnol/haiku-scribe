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
        (
            '{"theme":"dark","permissions":{"allow":["Edit"],"deny":['
            '"Read(./private)","Read(./.env)","Read(**/*.pem)"]},"profile":{"name":"me"}}'
        ),
        encoding="utf-8",
    )
    backup_root = claude / "backups" / "haiku-scribe"
    backup_root.mkdir(parents=True)
    (backup_root / "20240101T000000Z-settings.json.bak").write_text("backup", encoding="utf-8")

    assert run_cli("setup", "--home", str(tmp_path)).returncode == 0

    result = run_cli("uninstall", "--home", str(tmp_path))

    assert result.returncode == 0
    assert not (claude / "agents" / "haiku-scribe.md").exists()
    guidance = (claude / "CLAUDE.md").read_text(encoding="utf-8")
    settings = json.loads((claude / "settings.json").read_text(encoding="utf-8"))
    assert "# My guidance" in guidance
    assert "HAIKU_SCRIBE_START" not in guidance
    assert settings["theme"] == "dark"
    assert settings["profile"]["name"] == "me"
    assert settings["permissions"]["allow"] == ["Edit"]
    assert "Read(./private)" in settings["permissions"]["deny"]
    assert "Read(./.env)" not in settings["permissions"]["deny"]
    assert "Read(**/*.pem)" not in settings["permissions"]["deny"]
    assert not backup_root.exists()


def test_uninstall_keeps_matching_deny_rules_without_ownership_metadata(tmp_path: Path) -> None:
    assert run_cli("setup", "--home", str(tmp_path)).returncode == 0

    settings_path = tmp_path / ".claude" / "settings.json"
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    settings["permissions"]["deny"] = ["Read(./.env)", "Read(**/*.pem)", "Read(./private)"]
    settings.pop("haiku_scribe", None)
    settings_path.write_text(json.dumps(settings, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    result = run_cli("uninstall", "--home", str(tmp_path))

    assert result.returncode == 0
    updated = json.loads(settings_path.read_text(encoding="utf-8"))
    assert updated["permissions"]["deny"] == ["Read(./.env)", "Read(**/*.pem)", "Read(./private)"]


def test_uninstall_ignores_malformed_settings_but_removes_other_owned_files(tmp_path: Path) -> None:
    assert run_cli("setup", "--home", str(tmp_path)).returncode == 0

    claude = tmp_path / ".claude"
    settings_path = claude / "settings.json"
    settings_path.write_text("{broken", encoding="utf-8")
    backup_root = claude / "backups" / "haiku-scribe"

    result = run_cli("uninstall", "--home", str(tmp_path))

    assert result.returncode == 0
    assert "Traceback" not in result.stderr
    assert not (claude / "agents" / "haiku-scribe.md").exists()
    assert "HAIKU_SCRIBE_START" not in (claude / "CLAUDE.md").read_text(encoding="utf-8")
    assert not backup_root.exists()
    assert settings_path.read_text(encoding="utf-8") == "{broken"


def test_uninstall_is_idempotent(tmp_path: Path) -> None:
    assert run_cli("setup", "--home", str(tmp_path)).returncode == 0

    first = run_cli("uninstall", "--home", str(tmp_path))
    second = run_cli("uninstall", "--home", str(tmp_path))

    assert first.returncode == 0
    assert second.returncode == 0
    assert "Nothing to remove" in second.stdout
