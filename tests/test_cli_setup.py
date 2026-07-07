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


def test_cli_help_lists_v1_commands() -> None:
    result = run_cli("--help")

    assert result.returncode == 0
    assert "setup" in result.stdout
    assert "doctor" in result.stdout
    assert "uninstall" in result.stdout


def test_setup_dry_run_command_exists(tmp_path: Path) -> None:
    result = run_cli("setup", "--dry-run", "--home", str(tmp_path))

    assert result.returncode == 0
    assert "Dry run" in result.stdout


def test_setup_dry_run_writes_nothing(tmp_path: Path) -> None:
    result = run_cli("setup", "--dry-run", "--hooks", "on", "--home", str(tmp_path))

    assert result.returncode == 0
    assert "Dry run" in result.stdout
    assert "Would write" in result.stdout
    assert "haiku-scribe-v1-2-nudge.py" in result.stdout
    assert not (tmp_path / ".claude").exists()


def test_setup_installs_agent_guidance_and_settings(tmp_path: Path) -> None:
    result = run_cli("setup", "--home", str(tmp_path))

    assert result.returncode == 0
    agent = tmp_path / ".claude" / "agents" / "haiku-scribe.md"
    guidance = tmp_path / ".claude" / "CLAUDE.md"
    settings = tmp_path / ".claude" / "settings.json"
    assert agent.exists()
    assert "model: haiku" in agent.read_text(encoding="utf-8")
    guidance_text = guidance.read_text(encoding="utf-8")
    assert "HAIKU_SCRIBE_START" in guidance_text
    assert "Use `haiku-scribe` when remaining work is broad context gathering" in guidance_text
    parsed = json.loads(settings.read_text(encoding="utf-8"))
    assert "Read(**/*credential*)" in parsed["permissions"]["deny"]


def test_setup_is_idempotent(tmp_path: Path) -> None:
    first = run_cli("setup", "--hooks", "on", "--home", str(tmp_path))
    second = run_cli("setup", "--hooks", "on", "--home", str(tmp_path))

    assert first.returncode == 0
    assert second.returncode == 0
    guidance = (tmp_path / ".claude" / "CLAUDE.md").read_text(encoding="utf-8")
    settings = json.loads((tmp_path / ".claude" / "settings.json").read_text(encoding="utf-8"))
    assert guidance.count("HAIKU_SCRIBE_START") == 1
    assert settings["permissions"]["deny"].count("Read(**/*credential*)") == 1
    assert len(settings["hooks"]["UserPromptSubmit"]) == 1
    assert len(settings["hooks"]["PreToolUse"]) == 1


def test_setup_installs_no_hooks_by_default(tmp_path: Path) -> None:
    result = run_cli("setup", "--home", str(tmp_path))

    assert result.returncode == 0
    hook_path = tmp_path / ".claude" / "hooks" / "haiku-scribe-v1-2-nudge.py"
    settings_path = tmp_path / ".claude" / "settings.json"
    assert not hook_path.exists()
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    assert "hooks" not in settings
    assert "owned_v1_2_nudge_hook_command" not in settings.get("haiku_scribe", {})


def test_setup_hooks_on_installs_v1_2_hooks(tmp_path: Path) -> None:
    result = run_cli("setup", "--hooks", "on", "--home", str(tmp_path))

    assert result.returncode == 0
    hook_path = tmp_path / ".claude" / "hooks" / "haiku-scribe-v1-2-nudge.py"
    settings_path = tmp_path / ".claude" / "settings.json"
    assert hook_path.exists()
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    command = settings["haiku_scribe"]["owned_v1_2_nudge_hook_command"]
    assert command.endswith("haiku-scribe-v1-2-nudge.py")
    assert settings["hooks"]["UserPromptSubmit"] == [
        {"matcher": "", "hooks": [{"type": "command", "command": command}]}
    ]
    assert settings["hooks"]["PreToolUse"] == [
        {"matcher": "Read|Grep", "hooks": [{"type": "command", "command": command}]}
    ]


def test_setup_default_removes_previously_owned_hooks(tmp_path: Path) -> None:
    run_cli("setup", "--hooks", "on", "--home", str(tmp_path))
    result = run_cli("setup", "--home", str(tmp_path))

    assert result.returncode == 0
    hook_path = tmp_path / ".claude" / "hooks" / "haiku-scribe-v1-2-nudge.py"
    settings_path = tmp_path / ".claude" / "settings.json"
    assert not hook_path.exists()
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    assert "hooks" not in settings
    assert "owned_v1_2_nudge_hook_command" not in settings.get("haiku_scribe", {})
    # deny rules survive the hook removal
    assert "Read(**/*credential*)" in settings["permissions"]["deny"]


def test_setup_default_removes_orphaned_unowned_hooks(tmp_path: Path) -> None:
    # Legacy/manually-edited install: hook entries exist in settings.json and the
    # hook script exists on disk, but there is no haiku_scribe ownership key.
    run_cli("setup", "--hooks", "on", "--home", str(tmp_path))

    settings_path = tmp_path / ".claude" / "settings.json"
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    settings.get("haiku_scribe", {}).pop("owned_v1_2_nudge_hook_command", None)
    settings_path.write_text(json.dumps(settings), encoding="utf-8")

    hook_path = tmp_path / ".claude" / "hooks" / "haiku-scribe-v1-2-nudge.py"
    assert hook_path.exists()

    result = run_cli("setup", "--home", str(tmp_path))

    assert result.returncode == 0
    assert not hook_path.exists()
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    assert "hooks" not in settings


def test_setup_creates_backups_for_existing_files(tmp_path: Path) -> None:
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


def test_setup_backs_up_preexisting_same_name_agent(tmp_path: Path) -> None:
    agent_path = tmp_path / ".claude" / "agents" / "haiku-scribe.md"
    agent_path.parent.mkdir(parents=True)
    agent_path.write_text("user agent", encoding="utf-8")

    result = run_cli("setup", "--home", str(tmp_path))

    assert result.returncode == 0
    backups = sorted((tmp_path / ".claude" / "backups" / "haiku-scribe").glob("*haiku-scribe.md.bak"))
    assert len(backups) == 1
    assert backups[0].read_text(encoding="utf-8") == "user agent"


def test_full_v1_user_journey(tmp_path: Path) -> None:
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


def test_uninstall_removes_v1_2_hooks_but_preserves_user_hooks(tmp_path: Path) -> None:
    settings_path = tmp_path / ".claude" / "settings.json"
    settings_path.parent.mkdir(parents=True)
    settings_path.write_text(
        json.dumps(
            {
                "hooks": {
                    "UserPromptSubmit": [
                        {
                            "matcher": "",
                            "hooks": [{"type": "command", "command": "echo keep"}],
                        }
                    ]
                }
            }
        ),
        encoding="utf-8",
    )

    setup = run_cli("setup", "--home", str(tmp_path))
    uninstall = run_cli("uninstall", "--home", str(tmp_path))

    assert setup.returncode == 0
    assert uninstall.returncode == 0
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    assert settings["hooks"]["UserPromptSubmit"] == [
        {"matcher": "", "hooks": [{"type": "command", "command": "echo keep"}]}
    ]
    assert "PreToolUse" not in settings["hooks"]
    assert "owned_v1_2_nudge_hook_command" not in settings.get("haiku_scribe", {})
    assert not (tmp_path / ".claude" / "hooks" / "haiku-scribe-v1-2-nudge.py").exists()


def test_setup_preserves_user_prompt_submit_when_adding_owned_hook(tmp_path: Path) -> None:
    settings_path = tmp_path / ".claude" / "settings.json"
    settings_path.parent.mkdir(parents=True)
    settings_path.write_text(
        json.dumps(
            {
                "hooks": {
                    "UserPromptSubmit": [
                        {
                            "matcher": "",
                            "hooks": [{"type": "command", "command": "echo keep"}],
                        }
                    ]
                }
            }
        ),
        encoding="utf-8",
    )

    result = run_cli("setup", "--hooks", "on", "--home", str(tmp_path))

    assert result.returncode == 0
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    command = settings["haiku_scribe"]["owned_v1_2_nudge_hook_command"]
    assert settings["hooks"]["UserPromptSubmit"] == [
        {"matcher": "", "hooks": [{"type": "command", "command": "echo keep"}]},
        {"matcher": "", "hooks": [{"type": "command", "command": command}]},
    ]


def test_doctor_fails_when_v1_2_hook_script_missing(tmp_path: Path) -> None:
    assert run_cli("setup", "--hooks", "on", "--home", str(tmp_path)).returncode == 0
    (tmp_path / ".claude" / "hooks" / "haiku-scribe-v1-2-nudge.py").unlink()

    result = run_cli("doctor", "--home", str(tmp_path))

    assert result.returncode == 1
    assert "missing V1.2 hook script" in result.stdout


def test_doctor_fails_when_v1_2_pre_tool_matcher_wrong(tmp_path: Path) -> None:
    assert run_cli("setup", "--hooks", "on", "--home", str(tmp_path)).returncode == 0
    settings_path = tmp_path / ".claude" / "settings.json"
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    settings["hooks"]["PreToolUse"][0]["matcher"] = "Read"
    settings_path.write_text(json.dumps(settings), encoding="utf-8")

    result = run_cli("doctor", "--home", str(tmp_path))

    assert result.returncode == 1
    assert "missing V1.2 PreToolUse hook with matcher Read|Grep" in result.stdout


def test_doctor_fails_when_v1_2_hook_ownership_missing(tmp_path: Path) -> None:
    assert run_cli("setup", "--hooks", "on", "--home", str(tmp_path)).returncode == 0
    settings_path = tmp_path / ".claude" / "settings.json"
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    settings["haiku_scribe"].pop("owned_v1_2_nudge_hook_command")
    settings_path.write_text(json.dumps(settings), encoding="utf-8")

    result = run_cli("doctor", "--home", str(tmp_path))

    assert result.returncode == 1
    assert "missing V1.2 hook ownership metadata" in result.stdout
