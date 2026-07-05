from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from haiku_scribe.backups import backup_existing
from haiku_scribe.contracts import DEFAULT_DENY_RULES, render_agent_markdown, render_guidance_block
from haiku_scribe.markdown_blocks import insert_or_replace_block
from haiku_scribe.paths import ClaudePaths
from haiku_scribe.settings import load_json_object, merge_deny_rules


@dataclass(frozen=True)
class SetupResult:
    planned: list[str]
    written: list[Path]


def _write_text_if_changed(path: Path, text: str) -> bool:
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return False
    path.write_text(text, encoding="utf-8")
    return True


def setup_user(home: Path, dry_run: bool = False) -> SetupResult:
    paths = ClaudePaths.for_home(home)
    planned = [
        f"Would write {paths.agent_path}",
        f"Would update {paths.guidance_path}",
        f"Would merge deny rules into {paths.settings_path}",
    ]
    if dry_run:
        return SetupResult(planned=planned, written=[])

    paths.agents_dir.mkdir(parents=True, exist_ok=True)
    paths.claude_dir.mkdir(parents=True, exist_ok=True)

    agent_text = render_agent_markdown()
    guidance_existing = paths.guidance_path.read_text(encoding="utf-8") if paths.guidance_path.exists() else ""
    guidance_text = insert_or_replace_block(guidance_existing, render_guidance_block())
    settings = merge_deny_rules(load_json_object(paths.settings_path), DEFAULT_DENY_RULES)
    settings_text = json.dumps(settings, indent=2, sort_keys=True) + "\n"

    written: list[Path] = []
    if _write_text_if_changed(paths.agent_path, agent_text):
        written.append(paths.agent_path)

    if paths.guidance_path.exists() and guidance_existing != guidance_text:
        backup_existing(paths.guidance_path, paths.claude_dir / "backups" / "haiku-scribe")
    if _write_text_if_changed(paths.guidance_path, guidance_text):
        written.append(paths.guidance_path)

    current_settings = paths.settings_path.read_text(encoding="utf-8") if paths.settings_path.exists() else None
    if paths.settings_path.exists() and current_settings != settings_text:
        backup_existing(paths.settings_path, paths.claude_dir / "backups" / "haiku-scribe")
    if _write_text_if_changed(paths.settings_path, settings_text):
        written.append(paths.settings_path)

    return SetupResult(planned=planned, written=written)

