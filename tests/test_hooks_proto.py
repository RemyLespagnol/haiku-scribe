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


def read_pre_tool_use(session_id: str, file_path: Path, prompt_id: str | None = "p1") -> dict[str, object]:
    payload: dict[str, object] = {
        "hook_event_name": "PreToolUse",
        "session_id": session_id,
        "cwd": str(file_path.parent),
        "tool_name": "Read",
        "tool_input": {"file_path": str(file_path)},
    }
    if prompt_id is not None:
        payload["prompt_id"] = prompt_id
    return payload


def grep_pre_tool_use(session_id: str, cwd: Path, prompt_id: str | None = "p1") -> dict[str, object]:
    payload: dict[str, object] = {
        "hook_event_name": "PreToolUse",
        "session_id": session_id,
        "cwd": str(cwd),
        "tool_name": "Grep",
        "tool_input": {"pattern": "example"},
    }
    if prompt_id is not None:
        payload["prompt_id"] = prompt_id
    return payload


def prompt_submit(prompt: str, prompt_id: str | None = "p1") -> dict[str, object]:
    payload: dict[str, object] = {
        "hook_event_name": "UserPromptSubmit",
        "session_id": "s1",
        "cwd": "/tmp/project",
        "prompt": prompt,
    }
    if prompt_id is not None:
        payload["prompt_id"] = prompt_id
    return payload


def nudges_log(tmp_path: Path) -> Path:
    return tmp_path / ".claude" / "haiku-scribe-nudges.jsonl"


def test_user_prompt_submit_injects_context_for_broad_prompt(tmp_path: Path) -> None:
    hook_path = write_hook(tmp_path)

    result = run_hook(hook_path, prompt_submit("scan the repo architecture"))

    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"
    assert "haiku-scribe" in output["hookSpecificOutput"]["additionalContext"]
    log_lines = nudges_log(tmp_path).read_text(encoding="utf-8").splitlines()
    assert len(log_lines) == 1
    assert json.loads(log_lines[0])["decision"] == "nudge"


def test_removed_markers_do_not_trigger_by_themselves(tmp_path: Path) -> None:
    hook_path = write_hook(tmp_path)

    for marker in ("log", "repo", "flow", "map", "summarize", "unfamiliar"):
        result = run_hook(hook_path, prompt_submit(marker, prompt_id=f"prompt-{marker}"))
        assert result.returncode == 0
        assert result.stdout == ""

    assert not nudges_log(tmp_path).exists()


def test_specific_markers_trigger_nudge(tmp_path: Path) -> None:
    hook_path = write_hook(tmp_path)

    for marker in (
        "scan the repo",
        "explore the repo",
        "map the flow",
        "data flow",
        "plusieurs fichiers",
        "where is retry implemented",
        "where does auth happen",
        "search the codebase",
        "find all callers",
        "compress the log file",
        "summarize the logs",
        "trace the request path",
    ):
        result = run_hook(hook_path, prompt_submit(marker, prompt_id=f"prompt-{marker}"))
        assert result.returncode == 0
        assert "haiku-scribe" in json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]


def test_pre_tool_hook_reinforces_prompt_nudge_once_for_read_or_grep(tmp_path: Path) -> None:
    hook_path = write_hook(tmp_path)
    small_file = write_file(tmp_path, "small.py", 200)

    assert run_hook(hook_path, prompt_submit("scan the repo architecture")).returncode == 0
    first = run_hook(hook_path, read_pre_tool_use("s1", small_file))
    second = run_hook(hook_path, grep_pre_tool_use("s1", tmp_path))

    assert first.returncode == 0
    assert "haiku-scribe" in json.loads(first.stdout)["hookSpecificOutput"]["additionalContext"]
    assert second.returncode == 0
    assert second.stdout == ""
    decisions = [json.loads(line)["decision"] for line in nudges_log(tmp_path).read_text(encoding="utf-8").splitlines()]
    assert decisions == ["nudge", "pre_tool_followup"]


def test_followup_is_per_prompt_when_prompt_id_present(tmp_path: Path) -> None:
    hook_path = write_hook(tmp_path)
    small_file = write_file(tmp_path, "small.py", 200)

    assert run_hook(hook_path, prompt_submit("scan the repo architecture", prompt_id="p1")).returncode == 0
    assert "haiku-scribe" in json.loads(run_hook(hook_path, read_pre_tool_use("s1", small_file, prompt_id="p1")).stdout)["hookSpecificOutput"]["additionalContext"]
    assert run_hook(hook_path, prompt_submit("trace the request path", prompt_id="p2")).returncode == 0
    second = run_hook(hook_path, read_pre_tool_use("s1", small_file, prompt_id="p2"))

    assert "haiku-scribe" in json.loads(second.stdout)["hookSpecificOutput"]["additionalContext"]
    decisions = [json.loads(line)["decision"] for line in nudges_log(tmp_path).read_text(encoding="utf-8").splitlines()]
    assert decisions == ["nudge", "pre_tool_followup", "nudge", "pre_tool_followup"]


def test_missing_prompt_id_still_allows_one_followup_per_flagged_prompt(tmp_path: Path) -> None:
    hook_path = write_hook(tmp_path)
    small_file = write_file(tmp_path, "small.py", 200)

    assert run_hook(hook_path, prompt_submit("scan the repo architecture", prompt_id=None)).returncode == 0
    first = run_hook(hook_path, read_pre_tool_use("s1", small_file, prompt_id=None))
    repeat = run_hook(hook_path, read_pre_tool_use("s1", small_file, prompt_id=None))
    assert run_hook(hook_path, prompt_submit("trace the request path", prompt_id=None)).returncode == 0
    second = run_hook(hook_path, read_pre_tool_use("s1", small_file, prompt_id=None))

    assert "haiku-scribe" in json.loads(first.stdout)["hookSpecificOutput"]["additionalContext"]
    assert repeat.stdout == ""  # same flagged prompt: still deduped
    assert "haiku-scribe" in json.loads(second.stdout)["hookSpecificOutput"]["additionalContext"]
    decisions = [json.loads(line)["decision"] for line in nudges_log(tmp_path).read_text(encoding="utf-8").splitlines()]
    assert decisions == ["nudge", "pre_tool_followup", "nudge", "pre_tool_followup"]


def test_missing_prompt_id_events_use_fallback_hash_not_raw_prompt(tmp_path: Path) -> None:
    hook_path = write_hook(tmp_path)
    small_file = write_file(tmp_path, "small.py", 200)
    secret_prompt = "scan the repo for SECRET_TOKEN_XYZ"

    assert run_hook(hook_path, prompt_submit(secret_prompt, prompt_id=None)).returncode == 0
    assert run_hook(hook_path, read_pre_tool_use("s1", small_file, prompt_id=None)).returncode == 0

    log_text = nudges_log(tmp_path).read_text(encoding="utf-8")
    assert "SECRET_TOKEN_XYZ" not in log_text
    events = [json.loads(line) for line in log_text.splitlines()]
    assert [e["identity"] for e in events] == ["fallback", "fallback"]
    assert all(str(e["prompt_key"]).startswith("fb-") for e in events)
    assert events[0]["prompt_key"] == events[1]["prompt_key"]


def test_missing_prompt_id_does_not_lock_out_size_nudge(tmp_path: Path) -> None:
    hook_path = write_hook(tmp_path)
    small_file = write_file(tmp_path, "small.py", 200)
    big_file = write_file(tmp_path, "big.log", 300_000)

    assert run_hook(hook_path, prompt_submit("scan the repo architecture", prompt_id=None)).returncode == 0
    assert run_hook(hook_path, read_pre_tool_use("s1", small_file, prompt_id=None)).returncode == 0

    result = run_hook(hook_path, read_pre_tool_use("s1", big_file, prompt_id=None))

    assert result.returncode == 0
    assert "KB" in json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
    decisions = [json.loads(line)["decision"] for line in nudges_log(tmp_path).read_text(encoding="utf-8").splitlines()]
    assert decisions == ["nudge", "pre_tool_followup", "size_nudge"]


def test_size_nudge_still_fires_after_prompt_nudge_and_followup(tmp_path: Path) -> None:
    hook_path = write_hook(tmp_path)
    small_file = write_file(tmp_path, "small.py", 200)
    big_file = write_file(tmp_path, "big.log", 300_000)

    assert run_hook(hook_path, prompt_submit("scan the repo architecture")).returncode == 0
    followup = run_hook(hook_path, read_pre_tool_use("s1", small_file))
    assert "haiku-scribe" in json.loads(followup.stdout)["hookSpecificOutput"]["additionalContext"]

    result = run_hook(hook_path, read_pre_tool_use("s1", big_file))

    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert "KB" in output["hookSpecificOutput"]["additionalContext"]
    decisions = [json.loads(line)["decision"] for line in nudges_log(tmp_path).read_text(encoding="utf-8").splitlines()]
    assert decisions == ["nudge", "pre_tool_followup", "size_nudge"]


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
    assert len(settings["hooks"]["UserPromptSubmit"]) == 1
    pre_tool_groups = settings["hooks"]["PreToolUse"]
    assert len(pre_tool_groups) == 1
    assert pre_tool_groups[0]["matcher"] == "Read|Grep|Task|Agent"
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

    result = run_cli("setup", "--hooks", "on", "--home", str(tmp_path))

    assert result.returncode == 0
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    prompt_groups = settings["hooks"]["UserPromptSubmit"]
    assert prompt_groups == [
        {"matcher": "", "hooks": [{"type": "command", "command": "echo keep"}]},
        {"matcher": "", "hooks": [{"type": "command", "command": legacy_command}]},
    ]
    pre_tool_groups = settings["hooks"]["PreToolUse"]
    assert len(pre_tool_groups) == 1
    assert pre_tool_groups[0]["matcher"] == "Read|Grep|Task|Agent"


def test_log_scan_is_capped_to_recent_tail(tmp_path: Path) -> None:
    hook_path = write_hook(tmp_path)
    big_file = write_file(tmp_path, "big.log", 300_000)
    log_path = nudges_log(tmp_path)
    old_dedup = json.dumps({"decision": "size_nudge", "session_id": "s1", "file_path": str(big_file)})
    filler = json.dumps({"decision": "size_nudge", "session_id": "old-session", "file_path": "/other.log"})
    # The dedup entry sits before >1MB of filler, so a tail-capped scan must not see it.
    log_path.write_text(old_dedup + "\n" + (filler + "\n") * 20_000, encoding="utf-8")

    result = run_hook(hook_path, read_pre_tool_use("s1", big_file))

    assert result.returncode == 0
    assert "haiku-scribe" in json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]


def task_pre_tool_use(session_id: str, subagent: str, prompt_id: str | None = "p1") -> dict[str, object]:
    payload: dict[str, object] = {
        "hook_event_name": "PreToolUse",
        "session_id": session_id,
        "cwd": "/tmp/project",
        "tool_name": "Task",
        "tool_input": {"subagent_type": subagent, "prompt": "scout the repo"},
    }
    if prompt_id is not None:
        payload["prompt_id"] = prompt_id
    return payload


def test_weak_markers_alone_do_not_trigger(tmp_path: Path) -> None:
    hook_path = write_hook(tmp_path)

    for prompt in (
        "check the architecture",
        "audit this function",
        "i implemented the fix",
        "keyboard mapping is broken",
        "investigate please",
        "how does this work",
    ):
        result = run_hook(hook_path, prompt_submit(prompt, prompt_id=f"prompt-{prompt}"))
        assert result.returncode == 0
        assert result.stdout == ""

    assert not nudges_log(tmp_path).exists()


def test_two_weak_markers_trigger_nudge(tmp_path: Path) -> None:
    hook_path = write_hook(tmp_path)

    result = run_hook(hook_path, prompt_submit("audit the architecture of this service"))

    assert result.returncode == 0
    assert "haiku-scribe" in json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]


def test_negative_patterns_suppress_nudge_and_log_it(tmp_path: Path) -> None:
    hook_path = write_hook(tmp_path)

    for i, prompt in enumerate(
        (
            "where is the bug in this snippet ```py\nx = 1\n```",
            "trace the failure at gain.py:42",
            "where is the check on line 42",
        )
    ):
        result = run_hook(hook_path, prompt_submit(prompt, prompt_id=f"p{i}"))
        assert result.returncode == 0
        assert result.stdout == ""

    events = [json.loads(line) for line in nudges_log(tmp_path).read_text(encoding="utf-8").splitlines()]
    assert [e["decision"] for e in events] == ["suppressed"] * 3
    assert all(e["reason"] == "negative_prompt_pattern" for e in events)


def test_haiku_scribe_delegation_is_logged_and_suppresses_followup(tmp_path: Path) -> None:
    hook_path = write_hook(tmp_path)
    small_file = write_file(tmp_path, "small.txt", 10)

    assert run_hook(hook_path, prompt_submit("scan the repo architecture", prompt_id="p1")).returncode == 0
    task_result = run_hook(hook_path, task_pre_tool_use("s1", "haiku-scribe", prompt_id="p1"))
    assert task_result.returncode == 0
    assert task_result.stdout == ""

    read_result = run_hook(hook_path, read_pre_tool_use("s1", small_file, prompt_id="p1"))
    assert read_result.returncode == 0
    assert read_result.stdout == ""

    decisions = [
        json.loads(line)["decision"]
        for line in nudges_log(tmp_path).read_text(encoding="utf-8").splitlines()
    ]
    assert decisions == ["nudge", "delegation"]


def test_other_subagent_task_is_not_logged(tmp_path: Path) -> None:
    hook_path = write_hook(tmp_path)

    result = run_hook(hook_path, task_pre_tool_use("s1", "explore"))

    assert result.returncode == 0
    assert result.stdout == ""
    assert not nudges_log(tmp_path).exists()
