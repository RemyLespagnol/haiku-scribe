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


def test_cli_help_lists_v1_commands():
    result = run_cli("--help")

    assert result.returncode == 0
    assert "setup" in result.stdout
    assert "doctor" in result.stdout
    assert "uninstall" in result.stdout


def test_setup_dry_run_command_exists(tmp_path):
    result = run_cli("setup", "--dry-run", "--home", str(tmp_path))

    assert result.returncode == 0
    assert "Dry run" in result.stdout


def test_setup_dry_run_writes_nothing(tmp_path):
    result = run_cli("setup", "--dry-run", "--home", str(tmp_path))

    assert result.returncode == 0
    assert "Dry run" in result.stdout
    assert "Would write" in result.stdout
    assert not (tmp_path / ".claude").exists()


def test_setup_installs_agent_guidance_and_settings(tmp_path):
    result = run_cli("setup", "--home", str(tmp_path))

    assert result.returncode == 0
    agent = tmp_path / ".claude" / "agents" / "haiku-scribe.md"
    guidance = tmp_path / ".claude" / "CLAUDE.md"
    settings = tmp_path / ".claude" / "settings.json"
    assert agent.exists()
    assert "model: haiku" in agent.read_text(encoding="utf-8")
    assert "HAIKU_SCRIBE_START" in guidance.read_text(encoding="utf-8")
    parsed = json.loads(settings.read_text(encoding="utf-8"))
    assert "Read(**/*credential*)" in parsed["permissions"]["deny"]


def test_setup_is_idempotent(tmp_path):
    first = run_cli("setup", "--home", str(tmp_path))
    second = run_cli("setup", "--home", str(tmp_path))

    assert first.returncode == 0
    assert second.returncode == 0
    guidance = (tmp_path / ".claude" / "CLAUDE.md").read_text(encoding="utf-8")
    settings = json.loads((tmp_path / ".claude" / "settings.json").read_text(encoding="utf-8"))
    assert guidance.count("HAIKU_SCRIBE_START") == 1
    assert settings["permissions"]["deny"].count("Read(**/*credential*)") == 1


def test_setup_creates_backups_for_existing_files(tmp_path):
    claude = tmp_path / ".claude"
    (claude / "agents").mkdir(parents=True)
    (claude / "CLAUDE.md").write_text("# User guidance\n", encoding="utf-8")
    (claude / "settings.json").write_text('{"permissions":{"deny":["Read(./private)"]}}', encoding="utf-8")

    result = run_cli("setup", "--home", str(tmp_path))

    assert result.returncode == 0
    backups = sorted((claude / "backups" / "haiku-scribe").glob("*"))
    assert len(backups) == 2
    assert any(path.name.endswith("CLAUDE.md.bak") for path in backups)
    assert any(path.name.endswith("settings.json.bak") for path in backups)


def test_full_v1_user_journey(tmp_path):
    dry = run_cli("setup", "--dry-run", "--home", str(tmp_path))
    setup = run_cli("setup", "--home", str(tmp_path))
    doctor_ok = run_cli("doctor", "--home", str(tmp_path))
    uninstall = run_cli("uninstall", "--home", str(tmp_path))
    doctor_missing = run_cli("doctor", "--home", str(tmp_path))

    assert dry.returncode == 0
    assert setup.returncode == 0
    assert doctor_ok.returncode == 0
    assert uninstall.returncode == 0
    assert doctor_missing.returncode == 1
    assert "missing agent file" in doctor_missing.stdout
