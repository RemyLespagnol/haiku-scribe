from __future__ import annotations

import json
from pathlib import Path

from haiku_scribe.gain import build_report, format_report


def _write_log(path: Path, events: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8")


def test_report_counts_and_compliance(tmp_path: Path) -> None:
    log = tmp_path / "nudges.jsonl"
    _write_log(
        log,
        [
            {"decision": "nudge"},
            {"decision": "nudge"},
            {"decision": "nudge"},
            {"decision": "nudge"},
            {"decision": "size_nudge", "size_bytes": 300_000},
            {"decision": "size_nudge", "size_bytes": 700_000},
            {"decision": "pre_tool_followup"},  # 1 of 4 prompts ignored -> 75%
            {"decision": "other"},
            "not json",
        ],
    )
    report = build_report(log)
    assert report.prompts_flagged == 4
    assert report.large_reads_flagged == 2
    assert report.bytes_flagged == 1_000_000
    assert report.followups == 1
    assert report.compliance == 0.75

    text = format_report(report)
    assert "1000 KB deferrable" in text
    assert "75%" in text
    assert "Verdict: nudges are mostly followed (proxy signal)" in text


def test_missing_log_reports_no_activity(tmp_path: Path) -> None:
    report = build_report(tmp_path / "absent.jsonl")
    assert report == report.__class__(0, 0, 0, 0)
    assert report.compliance is None
    assert "no activity logged yet" in format_report(report)


def test_verdict_needs_enough_signal(tmp_path: Path) -> None:
    log = tmp_path / "nudges.jsonl"
    _write_log(log, [{"decision": "nudge"}, {"decision": "size_nudge", "size_bytes": 1}])
    assert "not enough signal yet" in format_report(build_report(log))


def test_verdict_flags_ignored_nudges_as_audit_only(tmp_path: Path) -> None:
    log = tmp_path / "nudges.jsonl"
    events = [{"decision": "nudge"}] * 5 + [{"decision": "pre_tool_followup"}] * 4
    _write_log(log, events)
    text = format_report(build_report(log))
    assert "audit-only" in text
