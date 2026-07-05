import json

import pytest

from haiku_scribe.contracts import DEFAULT_DENY_RULES
from haiku_scribe.settings import SettingsError, load_json_object, merge_deny_rules


def test_merge_deny_rules_preserves_existing_settings():
    settings = {
        "theme": "dark",
        "permissions": {"allow": ["Read(./docs/**)"], "deny": ["Read(./private)"]},
    }

    merged = merge_deny_rules(settings, DEFAULT_DENY_RULES)

    assert merged["theme"] == "dark"
    assert merged["permissions"]["allow"] == ["Read(./docs/**)"]
    assert merged["permissions"]["deny"].count("Read(./private)") == 1
    assert merged["permissions"]["deny"].count("Read(**/*credential*)") == 1


def test_merge_deny_rules_is_idempotent():
    once = merge_deny_rules({}, DEFAULT_DENY_RULES)
    twice = merge_deny_rules(once, DEFAULT_DENY_RULES)

    assert twice == once


def test_load_json_object_reports_invalid_json(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text("{broken", encoding="utf-8")

    with pytest.raises(SettingsError, match="invalid JSON"):
        load_json_object(path)


def test_load_json_object_rejects_json_array(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text(json.dumps([]), encoding="utf-8")

    with pytest.raises(SettingsError, match="must contain a JSON object"):
        load_json_object(path)
