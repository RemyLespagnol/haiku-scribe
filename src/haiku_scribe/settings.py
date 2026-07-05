from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any


class SettingsError(ValueError):
    pass


def load_json_object(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SettingsError(f"{path} contains invalid JSON: {exc.msg}") from exc
    if not isinstance(value, dict):
        raise SettingsError(f"{path} must contain a JSON object")
    return value


def merge_deny_rules(settings: dict[str, Any], deny_rules: tuple[str, ...]) -> dict[str, Any]:
    merged = deepcopy(settings)
    permissions = merged.setdefault("permissions", {})
    if not isinstance(permissions, dict):
        raise SettingsError("settings.permissions must be a JSON object")

    existing = permissions.get("deny", [])
    if not isinstance(existing, list):
        raise SettingsError("settings.permissions.deny must be a JSON array")

    deny = list(existing)
    for rule in deny_rules:
        if rule not in deny:
            deny.append(rule)
    permissions["deny"] = deny
    return merged

