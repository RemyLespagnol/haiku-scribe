from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any


OWNERSHIP_KEY = "haiku_scribe"
OWNED_DENY_RULES_KEY = "owned_deny_rules"


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
    previously_owned = _get_owned_deny_rules(merged)
    permissions = merged.setdefault("permissions", {})
    if not isinstance(permissions, dict):
        raise SettingsError("settings.permissions must be a JSON object")

    existing = permissions.get("deny", [])
    if not isinstance(existing, list):
        raise SettingsError("settings.permissions.deny must be a JSON array")

    deny = list(existing)
    added_rules: list[str] = []
    for rule in deny_rules:
        if rule not in deny:
            deny.append(rule)
            added_rules.append(rule)
    permissions["deny"] = deny
    _set_owned_deny_rules(merged, previously_owned + added_rules)
    return merged


def remove_owned_deny_rules(settings: dict[str, Any]) -> bool:
    permissions = settings.get("permissions")
    if permissions is None:
        return _clear_owned_deny_rules(settings)
    if not isinstance(permissions, dict):
        raise SettingsError("settings.permissions must be a JSON object")

    existing = permissions.get("deny", [])
    if not isinstance(existing, list):
        raise SettingsError("settings.permissions.deny must be a JSON array")

    owned_rules = _get_owned_deny_rules(settings)
    if not owned_rules:
        return _clear_owned_deny_rules(settings)

    updated = [rule for rule in existing if rule not in owned_rules]
    changed = updated != existing
    if changed:
        permissions["deny"] = updated

    metadata_changed = _clear_owned_deny_rules(settings)
    return changed or metadata_changed


def _get_owned_deny_rules(settings: dict[str, Any]) -> list[str]:
    ownership = settings.get(OWNERSHIP_KEY)
    if ownership is None:
        return []
    if not isinstance(ownership, dict):
        raise SettingsError(f"settings.{OWNERSHIP_KEY} must be a JSON object")

    owned_rules = ownership.get(OWNED_DENY_RULES_KEY, [])
    if not isinstance(owned_rules, list) or not all(isinstance(rule, str) for rule in owned_rules):
        raise SettingsError(f"settings.{OWNERSHIP_KEY}.{OWNED_DENY_RULES_KEY} must be a JSON array of strings")
    return list(owned_rules)


def _set_owned_deny_rules(settings: dict[str, Any], deny_rules: tuple[str, ...]) -> None:
    ownership = settings.setdefault(OWNERSHIP_KEY, {})
    if not isinstance(ownership, dict):
        raise SettingsError(f"settings.{OWNERSHIP_KEY} must be a JSON object")
    ownership[OWNED_DENY_RULES_KEY] = list(deny_rules)


def _clear_owned_deny_rules(settings: dict[str, Any]) -> bool:
    ownership = settings.get(OWNERSHIP_KEY)
    if ownership is None:
        return False
    if not isinstance(ownership, dict):
        raise SettingsError(f"settings.{OWNERSHIP_KEY} must be a JSON object")

    if OWNED_DENY_RULES_KEY not in ownership:
        return False

    del ownership[OWNED_DENY_RULES_KEY]
    if not ownership:
        del settings[OWNERSHIP_KEY]
    return True
