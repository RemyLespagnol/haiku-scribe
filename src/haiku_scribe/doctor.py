from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from haiku_scribe.contracts import DEFAULT_DENY_RULES, GUIDANCE_END, GUIDANCE_START
from haiku_scribe.paths import ClaudePaths
from haiku_scribe.settings import SettingsError, load_json_object


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
    return failures


def _check_guidance_file(guidance_path: Path) -> list[str]:
    if not guidance_path.exists():
        return ["missing CLAUDE.md guidance block"]

    guidance = guidance_path.read_text(encoding="utf-8")
    if GUIDANCE_START not in guidance or GUIDANCE_END not in guidance:
        return ["missing CLAUDE.md guidance block"]
    return []


def _check_settings_file(settings_path: Path) -> list[str]:
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
    return failures


def doctor_user(home: Path) -> DoctorResult:
    paths = ClaudePaths.for_home(home)
    failures = []
    failures.extend(_check_agent_file(paths.agent_path))
    failures.extend(_check_guidance_file(paths.guidance_path))
    failures.extend(_check_settings_file(paths.settings_path))
    return DoctorResult(ok=not failures, failures=failures)
