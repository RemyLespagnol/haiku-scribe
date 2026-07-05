from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from haiku_scribe.markdown_blocks import remove_owned_block
from haiku_scribe.paths import ClaudePaths


@dataclass(frozen=True)
class UninstallResult:
    planned: list[str]
    removed: list[Path]


def uninstall_user(home: Path, dry_run: bool = False) -> UninstallResult:
    paths = ClaudePaths.for_home(home)
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

    if dry_run:
        return UninstallResult(planned=planned, removed=[])

    if paths.agent_path.exists():
        paths.agent_path.unlink()
        removed.append(paths.agent_path)

    if guidance_changed:
        paths.guidance_path.write_text(remove_owned_block(guidance_text), encoding="utf-8")
        removed.append(paths.guidance_path)

    return UninstallResult(planned=planned, removed=removed)
