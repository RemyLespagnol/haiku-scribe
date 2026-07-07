from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from haiku_scribe.backups import backup_existing
from haiku_scribe.paths import ClaudePaths
from haiku_scribe.settings import load_json_object


HOOK_SCRIPT_NAME = "haiku-scribe-v1-2-nudge.py"
OWNED_HOOK_COMMAND_KEY = "owned_v1_2_nudge_hook_command"


@dataclass(frozen=True)
class PrototypeHooksResult:
    planned: list[str]
    written: list[Path]
    removed: list[Path]


def render_nudge_hook_script() -> str:
    return '''from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


BROAD_PROMPT_MARKERS = (
    "architecture",
    "audit",
    "cartographie",
    "data flow",
    "explore the repo",
    "large file",
    "map the flow",
    "mapping",
    "plusieurs fichiers",
    "scan the repo",
    "transcript",
)

NUDGE = (
    "Haiku Scribe nudge: this prompt looks like broad context gathering. "
    "Before raw repository reads/searches, consider delegating reconnaissance "
    "to the `haiku-scribe` subagent. Ask it for an extraction useful enough "
    "to avoid rereading everything, then verify only focused evidence directly."
)

PRE_TOOL_NUDGE = (
    "Haiku Scribe follow-up: this prompt was already flagged as broad context "
    "gathering. Before continuing with direct Read/Grep exploration, use "
    "the `haiku-scribe` subagent for reconnaissance unless this is now a small "
    "focused read. Avoid delegating and then rereading the same raw source."
)

DEFAULT_SIZE_THRESHOLD_BYTES = 256_000
MAX_LOG_SCAN_BYTES = 1_000_000

NUDGE_TEMPLATE = (
    "Haiku Scribe nudge: {path} is about {kb} KB and may dominate or overflow "
    "the main context window. If a structured extraction is enough to finish "
    "the task, delegate this file to the `haiku-scribe` subagent. If the task "
    "needs exact line-level detail, read it directly with offset/limit - do "
    "not delegate and then re-read."
)


def should_skip_payload(payload: dict) -> bool:
    if payload.get("agent_type") == "haiku-scribe":
        return True
    if payload.get("is_sidechain") is True:
        return True
    transcript_path = str(payload.get("transcript_path", ""))
    return "/subagents/" in transcript_path


def append_event(log_path: Path, event: dict) -> None:
    with log_path.open("a", encoding="utf-8") as log:
        log.write(json.dumps(event, sort_keys=True) + "\\n")


def iter_events(log_path: Path):
    # ponytail: tail-scan cap keeps per-call cost bounded; dedup memory is
    # limited to the last ~1MB of events, which is fine for advisory nudges.
    if not log_path.exists():
        return
    size = log_path.stat().st_size
    with log_path.open("rb") as fh:
        if size > MAX_LOG_SCAN_BYTES:
            fh.seek(size - MAX_LOG_SCAN_BYTES)
            fh.readline()
        text = fh.read().decode("utf-8", errors="replace")
    for line in text.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict):
            yield event


def size_threshold_bytes() -> int:
    try:
        return int(os.environ.get("HAIKU_SCRIBE_SIZE_THRESHOLD", ""))
    except ValueError:
        return DEFAULT_SIZE_THRESHOLD_BYTES


def already_nudged(events: list[dict], session_id: object, file_path: str) -> bool:
    return any(
        event.get("session_id") == session_id
        and event.get("file_path") == file_path
        and event.get("decision") == "size_nudge"
        for event in events
    )


def has_followup(events: list[dict], session_id: object, prompt_id: object) -> bool:
    return any(
        event.get("session_id") == session_id
        and event.get("prompt_id") == prompt_id
        and event.get("decision") == "pre_tool_followup"
        for event in events
    )


def has_initial_nudge(events: list[dict], session_id: object, prompt_id: object) -> bool:
    return any(
        event.get("session_id") == session_id
        and event.get("prompt_id") == prompt_id
        and event.get("decision") == "nudge"
        for event in events
    )


def main() -> int:
    if os.environ.get("HAIKU_SCRIBE_HOOKS") == "off":
        return 0
    payload = json.load(sys.stdin)
    if should_skip_payload(payload):
        return 0
    event_name = payload.get("hook_event_name")
    if event_name == "PreToolUse":
        return handle_pre_tool_use(payload)
    if event_name == "UserPromptSubmit":
        return handle_user_prompt_submit(payload)
    return 0


def handle_user_prompt_submit(payload: dict) -> int:
    prompt = str(payload.get("prompt", "")).lower()
    matched = [marker for marker in BROAD_PROMPT_MARKERS if marker in prompt]
    if not matched:
        return 0

    claude_dir = Path(__file__).resolve().parents[1]
    log_path = claude_dir / "haiku-scribe-nudges.jsonl"
    append_event(
        log_path,
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "decision": "nudge",
            "reason": "broad_prompt_marker",
            "matched": matched,
            "session_id": payload.get("session_id"),
            "prompt_id": payload.get("prompt_id"),
            "cwd": payload.get("cwd"),
        },
    )
    print(
        json.dumps(
            {
                "suppressOutput": True,
                "hookSpecificOutput": {
                    "hookEventName": "UserPromptSubmit",
                    "additionalContext": NUDGE,
                },
            }
        )
    )
    return 0


def handle_pre_tool_use(payload: dict) -> int:
    tool_name = payload.get("tool_name")
    claude_dir = Path(__file__).resolve().parents[1]
    log_path = claude_dir / "haiku-scribe-nudges.jsonl"
    events = list(iter_events(log_path))
    session_id = payload.get("session_id")
    prompt_id = payload.get("prompt_id")

    if has_initial_nudge(events, session_id, prompt_id):
        if tool_name in {"Read", "Grep"} and not has_followup(events, session_id, prompt_id):
            append_event(
                log_path,
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "decision": "pre_tool_followup",
                    "reason": "direct_tool_after_nudge",
                    "session_id": session_id,
                    "prompt_id": prompt_id,
                    "cwd": payload.get("cwd"),
                    "tool_name": tool_name,
                },
            )
            print(
                json.dumps(
                    {
                        "suppressOutput": True,
                        "hookSpecificOutput": {
                            "hookEventName": "PreToolUse",
                            "additionalContext": PRE_TOOL_NUDGE,
                        },
                    }
                )
            )
        return 0

    if tool_name != "Read":
        return 0

    tool_input = payload.get("tool_input")
    file_path = str(tool_input.get("file_path") or "") if isinstance(tool_input, dict) else ""
    if not file_path:
        return 0
    try:
        size = Path(file_path).stat().st_size
    except OSError:
        return 0
    threshold = size_threshold_bytes()
    if size <= threshold:
        return 0

    if already_nudged(events, session_id, file_path):
        return 0

    append_event(
        log_path,
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "decision": "size_nudge",
            "reason": "file_exceeds_size_threshold",
            "file_path": file_path,
            "size_bytes": size,
            "threshold_bytes": threshold,
            "session_id": session_id,
            "cwd": payload.get("cwd"),
        },
    )
    print(
        json.dumps(
            {
                "suppressOutput": True,
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "additionalContext": NUDGE_TEMPLATE.format(path=file_path, kb=size // 1000),
                },
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def hook_path_for(paths: ClaudePaths) -> Path:
    return paths.claude_dir / "hooks" / HOOK_SCRIPT_NAME


def hook_command_for(hook_path: Path) -> str:
    return f"python3 {hook_path}"


def setup_prototype_hooks(home: Path, dry_run: bool = False) -> PrototypeHooksResult:
    paths = ClaudePaths.for_home(home)
    hook_path = hook_path_for(paths)
    command = hook_command_for(hook_path)
    planned = [
        f"Would write {hook_path}",
        f"Would merge UserPromptSubmit and PreToolUse nudge hooks into {paths.settings_path}",
    ]
    if dry_run:
        return PrototypeHooksResult(planned=planned, written=[], removed=[])

    paths.claude_dir.mkdir(parents=True, exist_ok=True)
    hook_path.parent.mkdir(parents=True, exist_ok=True)

    settings = load_json_object(paths.settings_path)
    updated_settings = merge_v1_2_hook(settings, command)
    settings_text = json.dumps(updated_settings, indent=2, sort_keys=True) + "\n"
    hook_text = render_nudge_hook_script()

    written: list[Path] = []
    if hook_path.exists() and hook_path.read_text(encoding="utf-8") != hook_text:
        backup_existing(hook_path, paths.claude_dir / "backups" / "haiku-scribe")
    if _write_text_if_changed(hook_path, hook_text):
        written.append(hook_path)

    current_settings = paths.settings_path.read_text(encoding="utf-8") if paths.settings_path.exists() else None
    if paths.settings_path.exists() and current_settings != settings_text:
        backup_existing(paths.settings_path, paths.claude_dir / "backups" / "haiku-scribe")
    if _write_text_if_changed(paths.settings_path, settings_text):
        written.append(paths.settings_path)

    return PrototypeHooksResult(planned=planned, written=written, removed=[])


def uninstall_prototype_hooks(home: Path, dry_run: bool = False) -> PrototypeHooksResult:
    paths = ClaudePaths.for_home(home)
    hook_path = hook_path_for(paths)
    planned: list[str] = []
    removed: list[Path] = []

    settings = load_json_object(paths.settings_path) if paths.settings_path.exists() else {}
    command = _owned_hook_command(settings) or hook_command_for(hook_path)
    settings_changed = remove_v1_2_hook(settings, command)
    if settings_changed:
        planned.append(f"Would remove haiku-scribe nudge hooks from {paths.settings_path}")
    if hook_path.exists():
        planned.append(f"Would remove {hook_path}")
    if dry_run:
        return PrototypeHooksResult(planned=planned, written=[], removed=[])

    if settings_changed:
        paths.settings_path.write_text(json.dumps(settings, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        removed.append(paths.settings_path)
    if hook_path.exists():
        hook_path.unlink()
        removed.append(hook_path)
    return PrototypeHooksResult(planned=planned, written=[], removed=removed)


def merge_v1_2_hook(settings: dict[str, Any], command: str) -> dict[str, Any]:
    merged = json.loads(json.dumps(settings))
    hooks = merged.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise ValueError("settings.hooks must be a JSON object")

    # Migrate any prior registration of this command before re-adding the
    # current V1.2 layout.
    for event_name in ("UserPromptSubmit", "PreToolUse"):
        groups = hooks.get(event_name)
        if isinstance(groups, list):
            updated_groups = [
                group
                for group in (_remove_command_from_group(g, command) for g in groups)
                if group is not None
            ]
            if updated_groups:
                hooks[event_name] = updated_groups
            else:
                hooks.pop(event_name, None)

    prompt_groups = hooks.setdefault("UserPromptSubmit", [])
    if not isinstance(prompt_groups, list):
        raise ValueError("settings.hooks.UserPromptSubmit must be a JSON array")
    _append_group_once(
        prompt_groups,
        {
            "matcher": "",
            "hooks": [{"type": "command", "command": command}],
        },
    )

    pre_tool_groups = hooks.setdefault("PreToolUse", [])
    if not isinstance(pre_tool_groups, list):
        raise ValueError("settings.hooks.PreToolUse must be a JSON array")
    _append_group_once(
        pre_tool_groups,
        {
            "matcher": "Read|Grep",
            "hooks": [{"type": "command", "command": command}],
        },
    )

    ownership = merged.setdefault("haiku_scribe", {})
    if not isinstance(ownership, dict):
        raise ValueError("settings.haiku_scribe must be a JSON object")
    ownership[OWNED_HOOK_COMMAND_KEY] = command
    return merged


def remove_v1_2_hook(settings: dict[str, Any], command: str) -> bool:
    changed = False
    hooks = settings.get("hooks")
    if isinstance(hooks, dict):
        for event_name in ("UserPromptSubmit", "PreToolUse"):
            groups = hooks.get(event_name)
            if isinstance(groups, list):
                updated_groups = [_remove_command_from_group(group, command) for group in groups]
                updated_groups = [group for group in updated_groups if group is not None]
                if updated_groups != groups:
                    changed = True
                    if updated_groups:
                        hooks[event_name] = updated_groups
                    else:
                        hooks.pop(event_name, None)
        if not hooks:
            settings.pop("hooks", None)

    ownership = settings.get("haiku_scribe")
    if isinstance(ownership, dict) and ownership.get(OWNED_HOOK_COMMAND_KEY) == command:
        ownership.pop(OWNED_HOOK_COMMAND_KEY)
        changed = True
        if not ownership:
            settings.pop("haiku_scribe", None)
    return changed


merge_prototype_hook = merge_v1_2_hook
remove_prototype_hook = remove_v1_2_hook


def _remove_command_from_group(group: object, command: str) -> object | None:
    if not isinstance(group, dict):
        return group
    handlers = group.get("hooks")
    if not isinstance(handlers, list):
        return group
    updated_handlers = [
        handler
        for handler in handlers
        if not (isinstance(handler, dict) and handler.get("type") == "command" and handler.get("command") == command)
    ]
    if not updated_handlers:
        return None
    updated_group = dict(group)
    updated_group["hooks"] = updated_handlers
    return updated_group


def _append_group_once(groups: list[Any], group: dict[str, Any]) -> None:
    if group not in groups:
        groups.append(group)


def _hook_path(paths: ClaudePaths) -> Path:
    return hook_path_for(paths)


def _hook_command(hook_path: Path) -> str:
    return hook_command_for(hook_path)


def _owned_hook_command(settings: dict[str, Any]) -> str | None:
    ownership = settings.get("haiku_scribe")
    if not isinstance(ownership, dict):
        return None
    command = ownership.get(OWNED_HOOK_COMMAND_KEY)
    return command if isinstance(command, str) else None


def _write_text_if_changed(path: Path, text: str) -> bool:
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return False
    path.write_text(text, encoding="utf-8")
    return True
