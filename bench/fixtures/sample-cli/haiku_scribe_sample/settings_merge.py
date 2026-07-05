from copy import deepcopy


def merge_deny_rules(settings: dict, deny_rules: list[str]) -> dict:
    merged = deepcopy(settings)
    permissions = merged.setdefault("permissions", {})
    existing = list(permissions.get("deny", []))
    for rule in deny_rules:
        if rule not in existing:
            existing.append(rule)
    permissions["deny"] = existing
    return merged
