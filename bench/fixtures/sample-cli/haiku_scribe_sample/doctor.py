import json
from dataclasses import dataclass
from pathlib import Path

from .agent_config import default_agent_config


@dataclass(frozen=True)
class DoctorReport:
    ok: bool
    failures: list[str]


def doctor_report(home: Path) -> DoctorReport:
    config = default_agent_config()
    agent_path = home / ".claude" / "agents" / "haiku-scribe.md"
    settings_path = home / ".claude" / "settings.json"
    failures: list[str] = []

    if not agent_path.exists():
        failures.append("missing agent file")
    else:
        agent_text = agent_path.read_text()
        if f"model: {config.model}" not in agent_text:
            failures.append("agent model is not haiku")
        if "Bash" not in agent_text:
            failures.append("agent does not disallow Bash")

    if not settings_path.exists():
        failures.append("missing settings file")
    else:
        settings = json.loads(settings_path.read_text())
        deny = settings.get("permissions", {}).get("deny", [])
        missing = [rule for rule in config.deny_rules if rule not in deny]
        if missing:
            failures.append(f"missing deny rules: {', '.join(missing)}")

    return DoctorReport(ok=not failures, failures=failures)
