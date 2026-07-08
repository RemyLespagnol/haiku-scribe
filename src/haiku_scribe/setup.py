from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from haiku_scribe.backups import backup_existing
from haiku_scribe.contracts import DEFAULT_DENY_RULES, render_agent_markdown, render_guidance_block
from haiku_scribe.markdown_blocks import insert_or_replace_block
from haiku_scribe.paths import ClaudePaths
from haiku_scribe.settings import load_json_object, merge_deny_rules
from haiku_scribe.v1_2_hooks import (
    hook_command_for,
    hook_path_for,
    merge_v1_2_hook,
    owned_hook_command,
    remove_v1_2_hook,
    render_nudge_hook_script,
)


@dataclass(frozen=True)
class SetupResult:
    planned: list[str]
    written: list[Path]
    removed: list[Path] = field(default_factory=list)


def _write_text_if_changed(path: Path, text: str) -> bool:
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return False
    path.write_text(text, encoding="utf-8")
    return True


def setup_user(home: Path, dry_run: bool = False, install_hooks: bool = False) -> SetupResult:
    paths = ClaudePaths.for_home(home)
    hook_path = hook_path_for(paths)
    hook_command = hook_command_for(hook_path)

    existing_settings = load_json_object(paths.settings_path) if paths.settings_path.exists() else {}
    prior_hook_command = owned_hook_command(existing_settings)

    agent_text = render_agent_markdown()
    guidance_existing = paths.guidance_path.read_text(encoding="utf-8") if paths.guidance_path.exists() else ""
    guidance_text = insert_or_replace_block(guidance_existing, render_guidance_block())

    settings = merge_deny_rules(existing_settings, DEFAULT_DENY_RULES)
    if install_hooks:
        settings = merge_v1_2_hook(settings, hook_command)
    else:
        remove_v1_2_hook(settings, hook_command)
        if prior_hook_command and prior_hook_command != hook_command:
            remove_v1_2_hook(settings, prior_hook_command)

    settings_text = json.dumps(settings, indent=2, sort_keys=True) + "\n"
    current_settings = paths.settings_path.read_text(encoding="utf-8") if paths.settings_path.exists() else None
    hook_text = render_nudge_hook_script()
    current_hook_text = hook_path.read_text(encoding="utf-8") if hook_path.exists() else None

    # Plan only actual changes, so a second `setup --dry-run` truthfully
    # reports an already-installed state instead of re-listing every file.
    planned: list[str] = []
    if not paths.agent_path.exists() or paths.agent_path.read_text(encoding="utf-8") != agent_text:
        planned.append(f"Would write {paths.agent_path}")
    if guidance_existing != guidance_text:
        planned.append(f"Would update {paths.guidance_path}")
    if current_settings != settings_text:
        planned.append(f"Would update {paths.settings_path}")
    if install_hooks and current_hook_text != hook_text:
        planned.append(f"Would write {hook_path}")
    if not install_hooks and hook_path.exists():
        planned.append(f"Would remove {hook_path}")

    if dry_run:
        return SetupResult(planned=planned, written=[], removed=[])

    paths.agents_dir.mkdir(parents=True, exist_ok=True)
    paths.claude_dir.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []
    removed: list[Path] = []

    if paths.agent_path.exists() and paths.agent_path.read_text(encoding="utf-8") != agent_text:
        backup_existing(paths.agent_path, paths.claude_dir / "backups" / "haiku-scribe")
    if _write_text_if_changed(paths.agent_path, agent_text):
        written.append(paths.agent_path)

    if paths.guidance_path.exists() and guidance_existing != guidance_text:
        backup_existing(paths.guidance_path, paths.claude_dir / "backups" / "haiku-scribe")
    if _write_text_if_changed(paths.guidance_path, guidance_text):
        written.append(paths.guidance_path)

    if install_hooks:
        hook_text = render_nudge_hook_script()
        hook_path.parent.mkdir(parents=True, exist_ok=True)
        if hook_path.exists() and hook_path.read_text(encoding="utf-8") != hook_text:
            backup_existing(hook_path, paths.claude_dir / "backups" / "haiku-scribe")
        if _write_text_if_changed(hook_path, hook_text):
            written.append(hook_path)
    elif hook_path.exists():
        hook_path.unlink()
        removed.append(hook_path)

    current_settings = paths.settings_path.read_text(encoding="utf-8") if paths.settings_path.exists() else None
    if paths.settings_path.exists() and current_settings != settings_text:
        backup_existing(paths.settings_path, paths.claude_dir / "backups" / "haiku-scribe")
    if _write_text_if_changed(paths.settings_path, settings_text):
        written.append(paths.settings_path)

    return SetupResult(planned=planned, written=written, removed=removed)
