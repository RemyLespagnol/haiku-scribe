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


def run_hook(script_path: Path, payload: dict[str, object]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script_path)],
        input=json.dumps(payload),
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


def test_nudge_hook_injects_context_for_broad_prompt(tmp_path: Path) -> None:
    hook_path = write_hook(tmp_path)

    result = run_hook(
        hook_path,
        {
            "hook_event_name": "UserPromptSubmit",
            "session_id": "s1",
            "prompt_id": "p1",
            "cwd": str(tmp_path),
            "prompt": "Map the flow and review architecture",
        },
    )

    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"
    assert "haiku-scribe" in output["hookSpecificOutput"]["additionalContext"]
    log_lines = (tmp_path / ".claude" / "haiku-scribe-nudges.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(log_lines) == 1
    assert json.loads(log_lines[0])["decision"] == "nudge"


def test_nudge_hook_disabled_by_env_kill_switch(tmp_path: Path) -> None:
    hook_path = write_hook(tmp_path)

    env = os.environ.copy()
    env["HAIKU_SCRIBE_HOOKS"] = "off"
    result = subprocess.run(
        [sys.executable, str(hook_path)],
        input=json.dumps(
            {
                "hook_event_name": "UserPromptSubmit",
                "session_id": "s1",
                "prompt_id": "p1",
                "cwd": str(tmp_path),
                "prompt": "Map the flow and review architecture",
            }
        ),
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert not (tmp_path / ".claude" / "haiku-scribe-nudges.jsonl").exists()


def test_nudge_hook_stays_silent_for_small_prompt(tmp_path: Path) -> None:
    hook_path = write_hook(tmp_path)

    result = run_hook(
        hook_path,
        {
            "hook_event_name": "UserPromptSubmit",
            "session_id": "s1",
            "prompt_id": "p1",
            "cwd": str(tmp_path),
            "prompt": "Fix typo in README",
        },
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert not (tmp_path / ".claude" / "haiku-scribe-nudges.jsonl").exists()


def test_hook_ignores_haiku_scribe_agent_type_silently(tmp_path: Path) -> None:
    hook_path = write_hook(tmp_path)

    result = run_hook(
        hook_path,
        {
            "hook_event_name": "UserPromptSubmit",
            "session_id": "s1",
            "prompt_id": "p1",
            "cwd": str(tmp_path),
            "agent_type": "haiku-scribe",
            "prompt": "scan the repo architecture",
        },
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""
    assert not (tmp_path / ".claude" / "haiku-scribe-nudges.jsonl").exists()


def test_hook_ignores_sidechain_silently(tmp_path: Path) -> None:
    hook_path = write_hook(tmp_path)

    result = run_hook(
        hook_path,
        {
            "hook_event_name": "UserPromptSubmit",
            "session_id": "s1",
            "prompt_id": "p1",
            "cwd": str(tmp_path),
            "is_sidechain": True,
            "prompt": "scan the repo architecture",
        },
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""
    assert not (tmp_path / ".claude" / "haiku-scribe-nudges.jsonl").exists()


def test_hook_ignores_subagent_transcript_silently(tmp_path: Path) -> None:
    hook_path = write_hook(tmp_path)

    result = run_hook(
        hook_path,
        {
            "hook_event_name": "UserPromptSubmit",
            "session_id": "s1",
            "prompt_id": "p1",
            "cwd": str(tmp_path),
            "transcript_path": "/tmp/claude/subagents/haiku-scribe/session.jsonl",
            "prompt": "scan the repo architecture",
        },
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""
    assert not (tmp_path / ".claude" / "haiku-scribe-nudges.jsonl").exists()


def test_removed_markers_do_not_trigger_by_themselves(tmp_path: Path) -> None:
    hook_path = write_hook(tmp_path)

    for marker in ("log", "repo", "flow", "map", "summarize", "unfamiliar"):
        result = run_hook(
            hook_path,
            {
                "hook_event_name": "UserPromptSubmit",
                "session_id": "s1",
                "prompt_id": f"prompt-{marker}",
                "cwd": str(tmp_path),
                "prompt": marker,
            },
        )
        assert result.returncode == 0
        assert result.stdout == ""

    assert not (tmp_path / ".claude" / "haiku-scribe-nudges.jsonl").exists()


def test_specific_markers_trigger_nudge(tmp_path: Path) -> None:
    hook_path = write_hook(tmp_path)

    markers = (
        "architecture",
        "audit",
        "large file",
        "mapping",
        "transcript",
        "scan the repo",
        "explore the repo",
        "map the flow",
        "data flow",
        "plusieurs fichiers",
        "cartographie",
    )
    for index, marker in enumerate(markers):
        result = run_hook(
            hook_path,
            {
                "hook_event_name": "UserPromptSubmit",
                "session_id": "s1",
                "prompt_id": f"prompt-{index}",
                "cwd": str(tmp_path),
                "prompt": marker,
            },
        )
        assert result.returncode == 0
        assert "haiku-scribe" in json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]


def test_pre_tool_hook_reinforces_after_broad_prompt_nudge(tmp_path: Path) -> None:
    hook_path = write_hook(tmp_path)

    assert run_hook(
        hook_path,
        {
            "hook_event_name": "UserPromptSubmit",
            "session_id": "s1",
            "prompt_id": "p1",
            "cwd": str(tmp_path),
            "prompt": "scan the repo architecture",
        },
    ).returncode == 0

    result = run_hook(
        hook_path,
        {
            "hook_event_name": "PreToolUse",
            "session_id": "s1",
            "prompt_id": "p1",
            "cwd": str(tmp_path),
            "tool_name": "Read",
            "tool_input": {"file_path": "src/example.py"},
        },
    )

    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["hookSpecificOutput"]["hookEventName"] == "PreToolUse"
    assert "haiku-scribe" in output["hookSpecificOutput"]["additionalContext"]


def test_pre_tool_hook_reinforces_only_once_per_prompt(tmp_path: Path) -> None:
    hook_path = write_hook(tmp_path)

    assert run_hook(
        hook_path,
        {
            "hook_event_name": "UserPromptSubmit",
            "session_id": "s1",
            "prompt_id": "p1",
            "cwd": str(tmp_path),
            "prompt": "scan the repo architecture",
        },
    ).returncode == 0

    first = run_hook(
        hook_path,
        {
            "hook_event_name": "PreToolUse",
            "session_id": "s1",
            "prompt_id": "p1",
            "cwd": str(tmp_path),
            "tool_name": "Read",
            "tool_input": {"file_path": "src/example.py"},
        },
    )
    second = run_hook(
        hook_path,
        {
            "hook_event_name": "PreToolUse",
            "session_id": "s1",
            "prompt_id": "p1",
            "cwd": str(tmp_path),
            "tool_name": "Grep",
            "tool_input": {"pattern": "example"},
        },
    )

    assert first.returncode == 0
    assert "haiku-scribe" in json.loads(first.stdout)["hookSpecificOutput"]["additionalContext"]
    assert second.returncode == 0
    assert second.stdout == ""

    log_lines = (tmp_path / ".claude" / "haiku-scribe-nudges.jsonl").read_text(encoding="utf-8").splitlines()
    decisions = [json.loads(line)["decision"] for line in log_lines]
    assert decisions == ["nudge", "pre_tool_followup"]


def test_bash_does_not_trigger_pre_tool_followup(tmp_path: Path) -> None:
    hook_path = write_hook(tmp_path)

    assert run_hook(
        hook_path,
        {
            "hook_event_name": "UserPromptSubmit",
            "session_id": "s1",
            "prompt_id": "p1",
            "cwd": str(tmp_path),
            "prompt": "scan the repo architecture",
        },
    ).returncode == 0

    result = run_hook(
        hook_path,
        {
            "hook_event_name": "PreToolUse",
            "session_id": "s1",
            "prompt_id": "p1",
            "cwd": str(tmp_path),
            "tool_name": "Bash",
            "tool_input": {"command": "rg example"},
        },
    )

    assert result.returncode == 0
    assert result.stdout == ""


def test_prototype_hooks_install_is_idempotent(tmp_path: Path) -> None:
    first = run_cli("prototype-hooks", "setup", "--home", str(tmp_path))
    second = run_cli("prototype-hooks", "setup", "--home", str(tmp_path))

    assert first.returncode == 0
    assert second.returncode == 0
    settings = json.loads((tmp_path / ".claude" / "settings.json").read_text(encoding="utf-8"))
    prompt_groups = settings["hooks"]["UserPromptSubmit"]
    pre_tool_groups = settings["hooks"]["PreToolUse"]
    assert len(prompt_groups) == 1
    assert len(pre_tool_groups) == 1
    assert prompt_groups[0]["hooks"][0]["command"].endswith("haiku-scribe-v1-2-nudge.py")
    assert pre_tool_groups[0]["matcher"] == "Read|Grep"
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
