import json
from dataclasses import dataclass
from pathlib import Path

from .agent_config import default_agent_config, render_agent_markdown
from .settings_merge import merge_deny_rules


@dataclass(frozen=True)
class InstallResult:
    agent_path: Path
    settings_path: Path


def install_config(home: Path) -> InstallResult:
    config = default_agent_config()
    claude_dir = home / ".claude"
    agent_dir = claude_dir / "agents"
    agent_dir.mkdir(parents=True, exist_ok=True)

    agent_path = agent_dir / "haiku-scribe.md"
    settings_path = claude_dir / "settings.json"

    existing_settings = {}
    if settings_path.exists():
        existing_settings = json.loads(settings_path.read_text())

    agent_path.write_text(render_agent_markdown(config))
    settings = merge_deny_rules(existing_settings, list(config.deny_rules))
    settings_path.write_text(json.dumps(settings, indent=2, sort_keys=True))

    return InstallResult(agent_path=agent_path, settings_path=settings_path)
