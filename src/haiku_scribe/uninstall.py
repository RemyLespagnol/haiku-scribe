from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path

from haiku_scribe.markdown_blocks import remove_owned_block
from haiku_scribe.paths import ClaudePaths
from haiku_scribe.settings import SettingsError, load_json_object, remove_owned_deny_rules
from haiku_scribe.v1_2_hooks import hook_command_for, hook_path_for, remove_v1_2_hook


@dataclass(frozen=True)
class UninstallResult:
    planned: list[str]
    removed: list[Path]


def uninstall_user(home: Path, dry_run: bool = False) -> UninstallResult:
    paths = ClaudePaths.for_home(home)
    hook_path = hook_path_for(paths)
    hook_command = hook_command_for(hook_path)
    planned: list[str] = []
    removed: list[Path] = []

    if paths.agent_path.exists():
        planned.append(f"Would remove {paths.agent_path}")

    guidance_text = ""
    guidance_changed = False
    if paths.guidance_path.exists():
        guidance_text = paths.guidance_path.read_text(encoding="utf-8")
        updated_guidance = remove_owned_block(guidance_text)
        guidance_changed = updated_guidance != guidance_text
        if guidance_changed:
            planned.append(f"Would remove owned block from {paths.guidance_path}")

    settings = None
    settings_changed = False
    if paths.settings_path.exists():
        try:
            settings = load_json_object(paths.settings_path)
            deny_changed = remove_owned_deny_rules(settings)
            hook_changed = remove_v1_2_hook(settings, hook_command)
            settings_changed = deny_changed or hook_changed
        except SettingsError:
            settings = None
            settings_changed = False
        else:
            if deny_changed:
                planned.append(f"Would remove owned deny rules from {paths.settings_path}")
            if hook_changed:
                planned.append(f"Would remove owned V1.2 hooks from {paths.settings_path}")

    if hook_path.exists():
        planned.append(f"Would remove {hook_path}")

    backup_root = paths.claude_dir / "backups" / "haiku-scribe"
    if backup_root.exists():
        planned.append(f"Would remove {backup_root}")

    if dry_run:
        return UninstallResult(planned=planned, removed=[])

    if paths.agent_path.exists():
        paths.agent_path.unlink()
        removed.append(paths.agent_path)

    if guidance_changed:
        paths.guidance_path.write_text(remove_owned_block(guidance_text), encoding="utf-8")
        removed.append(paths.guidance_path)

    if settings_changed and settings is not None:
        paths.settings_path.write_text(json.dumps(settings, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        removed.append(paths.settings_path)

    if hook_path.exists():
        hook_path.unlink()
        removed.append(hook_path)

    if backup_root.exists():
        if backup_root.is_dir():
            shutil.rmtree(backup_root)
        else:
            backup_root.unlink()
        removed.append(backup_root)

    return UninstallResult(planned=planned, removed=removed)
