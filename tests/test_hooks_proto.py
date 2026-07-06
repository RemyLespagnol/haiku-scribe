from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from haiku_scribe.v1_2_hooks import render_nudge_hook_script


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


def run_hook(
    script_path: Path, payload: dict[str, object], extra_env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.update(extra_env or {})
    return subprocess.run(
        [sys.executable, str(script_path)],
        input=json.dumps(payload),
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def write_hook(tmp_path: Path) -> Path:
    hook_path = tmp_path / ".claude" / "hooks" / "haiku-scribe-v1-2-nudge.py"
    hook_path.parent.mkdir(parents=True)
    hook_path.write_text(render_nudge_hook_script(), encoding="utf-8")
    return hook_path


def write_file(tmp_path: Path, name: str, size: int) -> Path:
    file_path = tmp_path / name
    file_path.write_bytes(b"x" * size)
    return file_path


def read_pre_tool_use(session_id: str, file_path: Path) -> dict[str, object]:
    return {
        "hook_event_name": "PreToolUse",
        "session_id": session_id,
        "cwd": str(file_path.parent),
        "tool_name": "Read",
        "tool_input": {"file_path": str(file_path)},
    }


def nudges_log(tmp_path: Path) -> Path:
    return tmp_path / ".claude" / "haiku-scribe-nudges.jsonl"


def test_large_file_triggers_size_nudge(tmp_path: Path) -> None:
    hook_path = write_hook(tmp_path)
    big_file = write_file(tmp_path, "big.log", 300_000)

    result = run_hook(hook_path, read_pre_tool_use("s1", big_file))

    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["hookSpecificOutput"]["hookEventName"] == "PreToolUse"
    assert "haiku-scribe" in output["hookSpecificOutput"]["additionalContext"]
    log_lines = nudges_log(tmp_path).read_text(encoding="utf-8").splitlines()
    assert len(log_lines) == 1
    assert json.loads(log_lines[0])["decision"] == "size_nudge"


def test_small_file_stays_silent(tmp_path: Path) -> None:
    hook_path = write_hook(tmp_path)
    small_file = write_file(tmp_path, "small.py", 200)

    result = run_hook(hook_path, read_pre_tool_use("s1", small_file))

    assert result.returncode == 0
    assert result.stdout == ""
    assert not nudges_log(tmp_path).exists()


def test_dedup_same_file_same_session_nudges_once(tmp_path: Path) -> None:
    hook_path = write_hook(tmp_path)
    big_file = write_file(tmp_path, "big.log", 300_000)

    first = run_hook(hook_path, read_pre_tool_use("s1", big_file))
    second = run_hook(hook_path, read_pre_tool_use("s1", big_file))

    assert first.returncode == 0
    assert "haiku-scribe" in json.loads(first.stdout)["hookSpecificOutput"]["additionalContext"]
    assert second.returncode == 0
    assert second.stdout == ""
    log_lines = nudges_log(tmp_path).read_text(encoding="utf-8").splitlines()
    assert len(log_lines) == 1


def test_different_file_same_session_nudges_again(tmp_path: Path) -> None:
    hook_path = write_hook(tmp_path)
    first_file = write_file(tmp_path, "first.log", 300_000)
    second_file = write_file(tmp_path, "second.log", 300_000)

    first = run_hook(hook_path, read_pre_tool_use("s1", first_file))
    second = run_hook(hook_path, read_pre_tool_use("s1", second_file))

    assert first.returncode == 0
    assert "haiku-scribe" in json.loads(first.stdout)["hookSpecificOutput"]["additionalContext"]
    assert second.returncode == 0
    assert "haiku-scribe" in json.loads(second.stdout)["hookSpecificOutput"]["additionalContext"]
    log_lines = nudges_log(tmp_path).read_text(encoding="utf-8").splitlines()
    assert len(log_lines) == 2


def test_size_threshold_env_override_makes_small_file_nudgeable(tmp_path: Path) -> None:
    hook_path = write_hook(tmp_path)
    small_file = write_file(tmp_path, "small.py", 200)

    result = run_hook(hook_path, read_pre_tool_use("s1", small_file), {"HAIKU_SCRIBE_SIZE_THRESHOLD": "100"})

    assert result.returncode == 0
    assert "haiku-scribe" in json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]


def test_kill_switch_disables_nudge(tmp_path: Path) -> None:
    hook_path = write_hook(tmp_path)
    big_file = write_file(tmp_path, "big.log", 300_000)

    result = run_hook(hook_path, read_pre_tool_use("s1", big_file), {"HAIKU_SCRIBE_HOOKS": "off"})

    assert result.returncode == 0
    assert result.stdout == ""
    assert not nudges_log(tmp_path).exists()


def test_hook_ignores_haiku_scribe_agent_type_silently(tmp_path: Path) -> None:
    hook_path = write_hook(tmp_path)
    big_file = write_file(tmp_path, "big.log", 300_000)
    payload = read_pre_tool_use("s1", big_file)
    payload["agent_type"] = "haiku-scribe"

    result = run_hook(hook_path, payload)

    assert result.returncode == 0
    assert result.stdout == ""
    assert not nudges_log(tmp_path).exists()


def test_hook_ignores_sidechain_silently(tmp_path: Path) -> None:
    hook_path = write_hook(tmp_path)
    big_file = write_file(tmp_path, "big.log", 300_000)
    payload = read_pre_tool_use("s1", big_file)
    payload["is_sidechain"] = True

    result = run_hook(hook_path, payload)

    assert result.returncode == 0
    assert result.stdout == ""
    assert not nudges_log(tmp_path).exists()


def test_hook_ignores_subagent_transcript_silently(tmp_path: Path) -> None:
    hook_path = write_hook(tmp_path)
    big_file = write_file(tmp_path, "big.log", 300_000)
    payload = read_pre_tool_use("s1", big_file)
    payload["transcript_path"] = "/tmp/claude/subagents/haiku-scribe/session.jsonl"

    result = run_hook(hook_path, payload)

    assert result.returncode == 0
    assert result.stdout == ""
    assert not nudges_log(tmp_path).exists()


def test_non_read_tool_stays_silent(tmp_path: Path) -> None:
    hook_path = write_hook(tmp_path)

    result = run_hook(
        hook_path,
        {
            "hook_event_name": "PreToolUse",
            "session_id": "s1",
            "cwd": str(tmp_path),
            "tool_name": "Bash",
            "tool_input": {"command": "rg example"},
        },
    )

    assert result.returncode == 0
    assert result.stdout == ""


def test_user_prompt_submit_event_stays_silent(tmp_path: Path) -> None:
    hook_path = write_hook(tmp_path)

    result = run_hook(
        hook_path,
        {
            "hook_event_name": "UserPromptSubmit",
            "session_id": "s1",
            "cwd": str(tmp_path),
            "prompt": "scan the repo architecture",
        },
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert not nudges_log(tmp_path).exists()


def test_missing_file_stays_silent(tmp_path: Path) -> None:
    hook_path = write_hook(tmp_path)

    result = run_hook(hook_path, read_pre_tool_use("s1", tmp_path / "does-not-exist.log"))

    assert result.returncode == 0
    assert result.stdout == ""
    assert not nudges_log(tmp_path).exists()


def test_prototype_hooks_install_is_idempotent(tmp_path: Path) -> None:
    first = run_cli("prototype-hooks", "setup", "--home", str(tmp_path))
    second = run_cli("prototype-hooks", "setup", "--home", str(tmp_path))

    assert first.returncode == 0
    assert second.returncode == 0
    settings = json.loads((tmp_path / ".claude" / "settings.json").read_text(encoding="utf-8"))
    assert "UserPromptSubmit" not in settings["hooks"]
    pre_tool_groups = settings["hooks"]["PreToolUse"]
    assert len(pre_tool_groups) == 1
    assert pre_tool_groups[0]["matcher"] == "Read"
    assert pre_tool_groups[0]["hooks"][0]["command"].endswith("haiku-scribe-v1-2-nudge.py")
    assert (tmp_path / ".claude" / "hooks" / "haiku-scribe-v1-2-nudge.py").exists()


def test_prototype_hooks_uninstall_removes_only_owned_hook(tmp_path: Path) -> None:
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

    assert run_cli("prototype-hooks", "setup", "--home", str(tmp_path)).returncode == 0
    result = run_cli("prototype-hooks", "uninstall", "--home", str(tmp_path))

    assert result.returncode == 0
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    assert settings["hooks"]["UserPromptSubmit"] == [
        {"matcher": "", "hooks": [{"type": "command", "command": "echo keep"}]}
    ]
    assert "PreToolUse" not in settings["hooks"]
    assert not (tmp_path / ".claude" / "hooks" / "haiku-scribe-v1-2-nudge.py").exists()


def test_prototype_hooks_command_remains_compatible(tmp_path: Path) -> None:
    setup = run_cli("prototype-hooks", "setup", "--home", str(tmp_path))
    uninstall = run_cli("prototype-hooks", "uninstall", "--home", str(tmp_path))

    assert setup.returncode == 0
    assert uninstall.returncode == 0
    assert not (tmp_path / ".claude" / "hooks" / "haiku-scribe-v1-2-nudge.py").exists()


def test_setup_migrates_legacy_v1_2_layout(tmp_path: Path) -> None:
    settings_path = tmp_path / ".claude" / "settings.json"
    settings_path.parent.mkdir(parents=True)
    legacy_command = f"python3 {tmp_path / '.claude' / 'hooks' / 'haiku-scribe-v1-2-nudge.py'}"
    settings_path.write_text(
        json.dumps(
            {
                "hooks": {
                    "UserPromptSubmit": [
                        {
                            "matcher": "",
                            "hooks": [
                                {"type": "command", "command": "echo keep"},
                                {"type": "command", "command": legacy_command},
                            ],
                        }
                    ],
                    "PreToolUse": [
                        {
                            "matcher": "Read|Grep",
                            "hooks": [{"type": "command", "command": legacy_command}],
                        }
                    ],
                }
            }
        ),
        encoding="utf-8",
    )

    result = run_cli("setup", "--home", str(tmp_path))

    assert result.returncode == 0
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    prompt_groups = settings["hooks"]["UserPromptSubmit"]
    assert prompt_groups == [{"matcher": "", "hooks": [{"type": "command", "command": "echo keep"}]}]
    pre_tool_groups = settings["hooks"]["PreToolUse"]
    assert len(pre_tool_groups) == 1
    assert pre_tool_groups[0]["matcher"] == "Read"
