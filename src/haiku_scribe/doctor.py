from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from haiku_scribe.contracts import (
    DEFAULT_DENY_RULES,
    GUIDANCE_END,
    GUIDANCE_START,
    render_agent_markdown,
    render_guidance_block,
)
from haiku_scribe.paths import ClaudePaths
from haiku_scribe.settings import SettingsError, load_json_object
from haiku_scribe.v1_2_hooks import (
    PRE_TOOL_MATCHER,
    hook_command_for,
    hook_path_for,
    render_nudge_hook_script,
)


@dataclass(frozen=True)
class DoctorResult:
    ok: bool
    failures: list[str]


def _check_agent_file(agent_path: Path) -> list[str]:
    if not agent_path.exists():
        return ["missing agent file"]

    agent = agent_path.read_text(encoding="utf-8")
    failures: list[str] = []
    required_fragments = (
        ("agent name is not haiku-scribe", "name: haiku-scribe"),
        ("agent model is not haiku", "model: haiku"),
        ("agent tools are not read-only", "tools: Read, Glob, Grep"),
        ("agent does not forbid web access", "Browse web."),
        ("agent does not forbid file edits", "Edit files"),
        ("agent does not forbid file writes", "Write files"),
        ("agent does not forbid shell execution", "Run shell commands"),
        ("agent does not forbid MCP tools", "Use MCP tools"),
        ("agent does not forbid recursive agents", "Invoke other agents"),
    )
    for failure, fragment in required_fragments:
        if fragment not in agent:
            failures.append(failure)
    if agent != render_agent_markdown():
        failures.append("agent file drifted from current contract (run setup to restore)")
    return failures


def _check_guidance_file(guidance_path: Path) -> list[str]:
    if not guidance_path.exists():
        return ["missing CLAUDE.md guidance block"]

    guidance = guidance_path.read_text(encoding="utf-8")
    start = guidance.find(GUIDANCE_START)
    end = guidance.find(GUIDANCE_END)
    if start == -1 or end == -1 or end < start:
        return ["missing CLAUDE.md guidance block"]

    installed_block = guidance[start : end + len(GUIDANCE_END)]
    rendered = render_guidance_block()
    expected_block = rendered[rendered.find(GUIDANCE_START) : rendered.find(GUIDANCE_END) + len(GUIDANCE_END)]
    if installed_block != expected_block:
        return ["CLAUDE.md guidance block drifted from current contract (run setup to restore)"]
    return []


def _group_has_command(groups: Any, matcher: str, command: str) -> bool:
    if not isinstance(groups, list):
        return False
    expected = {"type": "command", "command": command}
    for group in groups:
        if not isinstance(group, dict):
            continue
        if group.get("matcher") != matcher:
            continue
        hooks = group.get("hooks")
        if isinstance(hooks, list) and expected in hooks:
            return True
    return False


def _check_v1_2_hook(paths: ClaudePaths, settings: dict[str, Any]) -> list[str]:
    hook_path = hook_path_for(paths)
    command = hook_command_for(hook_path)
    failures: list[str] = []
    if not hook_path.exists():
        failures.append("missing V1.2 hook script")
    elif hook_path.read_text(encoding="utf-8") != render_nudge_hook_script():
        failures.append("hook script drifted from current contract (run setup to restore)")

    ownership = settings.get("haiku_scribe")
    if not isinstance(ownership, dict) or ownership.get("owned_v1_2_nudge_hook_command") != command:
        failures.append("missing V1.2 hook ownership metadata")

    hooks = settings.get("hooks")
    if not isinstance(hooks, dict):
        failures.append("settings hooks must be JSON object")
        return failures

    if not _group_has_command(hooks.get("UserPromptSubmit"), "", command):
        failures.append("missing V1.2 UserPromptSubmit hook")
    if not _group_has_command(hooks.get("PreToolUse"), PRE_TOOL_MATCHER, command):
        failures.append(f"missing V1.2 PreToolUse hook with matcher {PRE_TOOL_MATCHER}")
    return failures


def _hooks_present(paths: ClaudePaths, settings: dict[str, Any]) -> bool:
    if hook_path_for(paths).exists():
        return True
    ownership = settings.get("haiku_scribe")
    if isinstance(ownership, dict) and ownership.get("owned_v1_2_nudge_hook_command"):
        return True
    command = hook_command_for(hook_path_for(paths))
    hooks = settings.get("hooks")
    if isinstance(hooks, dict):
        if _group_has_command(hooks.get("UserPromptSubmit"), "", command):
            return True
        # "Read|Grep" is the pre-Task-matcher layout; still counts as an
        # install so doctor reports the drift instead of skipping the checks.
        for matcher in (PRE_TOOL_MATCHER, "Read|Grep"):
            if _group_has_command(hooks.get("PreToolUse"), matcher, command):
                return True
    return False


def _check_settings_file(paths: ClaudePaths) -> list[str]:
    settings_path = paths.settings_path
    if not settings_path.exists():
        return ["missing settings file"]

    try:
        settings = load_json_object(settings_path)
    except SettingsError as exc:
        return [str(exc)]

    permissions = settings.get("permissions", {})
    if not isinstance(permissions, dict):
        return ["settings permissions must be a JSON object"]

    deny = permissions.get("deny", [])
    if not isinstance(deny, list):
        return ["settings permissions.deny not array"]

    failures: list[str] = []
    for rule in DEFAULT_DENY_RULES:
        if rule not in deny:
            failures.append(f"missing deny rule: {rule}")
    if _hooks_present(paths, settings):
        failures.extend(_check_v1_2_hook(paths, settings))
    return failures


def doctor_user(home: Path) -> DoctorResult:
    paths = ClaudePaths.for_home(home)
    failures = []
    failures.extend(_check_agent_file(paths.agent_path))
    failures.extend(_check_guidance_file(paths.guidance_path))
    failures.extend(_check_settings_file(paths))
    return DoctorResult(ok=not failures, failures=failures)
