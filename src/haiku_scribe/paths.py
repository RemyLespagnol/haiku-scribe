from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ClaudePaths:
    home: Path
    claude_dir: Path
    agents_dir: Path
    agent_path: Path
    guidance_path: Path
    settings_path: Path

    @classmethod
    def for_home(cls, home: Path) -> "ClaudePaths":
        claude_dir = home / ".claude"
        agents_dir = claude_dir / "agents"
        return cls(
            home=home,
            claude_dir=claude_dir,
            agents_dir=agents_dir,
            agent_path=agents_dir / "haiku-scribe.md",
            guidance_path=claude_dir / "CLAUDE.md",
            settings_path=claude_dir / "settings.json",
        )

