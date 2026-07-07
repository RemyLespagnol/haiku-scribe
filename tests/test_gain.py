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


def test_all_prompt_id_events_report_high_confidence(tmp_path: Path) -> None:
    log = tmp_path / "nudges.jsonl"
    _write_log(
        log,
        [
            {"decision": "nudge", "identity": "prompt_id", "prompt_id": "p1"},
            {"decision": "nudge", "prompt_id": "p2"},  # older hook: no identity field
            {"decision": "pre_tool_followup", "identity": "prompt_id", "prompt_id": "p1"},
        ],
    )
    report = build_report(log)
    assert report.prompt_id_events == 3
    assert report.fallback_events == 0
    assert report.high_confidence
    text = format_report(report)
    assert "3 with prompt_id / 0 fallback" in text
    assert "Confidence: high" in text


def test_fallback_events_report_proxy_only_confidence(tmp_path: Path) -> None:
    log = tmp_path / "nudges.jsonl"
    _write_log(
        log,
        [
            {"decision": "nudge", "identity": "prompt_id", "prompt_id": "p1"},
            {"decision": "nudge", "identity": "fallback", "prompt_key": "fb-abc123"},
            {"decision": "nudge", "prompt_id": None},  # older hook, missing prompt_id
            {"decision": "pre_tool_followup", "identity": "fallback", "prompt_key": "fb-abc123"},
        ],
    )
    report = build_report(log)
    assert report.prompt_id_events == 1
    assert report.fallback_events == 3
    assert not report.high_confidence
    text = format_report(report)
    assert "1 with prompt_id / 3 fallback" in text
    assert "Confidence: proxy-only" in text
    assert "over- or under-counted" in text


def test_delegation_and_suppression_reporting(tmp_path: Path) -> None:
    log = tmp_path / "nudges.jsonl"
    _write_log(
        log,
        [
            {"decision": "nudge", "session_id": "s1", "prompt_id": "p1"},
            {"decision": "nudge", "session_id": "s1", "prompt_id": "p2"},
            {"decision": "delegation", "session_id": "s1", "prompt_id": "p1"},
            {"decision": "delegation", "session_id": "s2", "prompt_id": "px"},  # organic, unflagged
            {"decision": "suppressed"},
        ],
    )
    report = build_report(log)
    assert report.delegations == 2
    assert report.nudges_delegated == 1
    assert report.suppressed == 1

    text = format_report(report)
    assert "Scout delegations observed: 2 (direct signal)" in text
    assert "Flagged prompts delegated:  1 of 2" in text
    assert "audit-only" in text


def test_verdict_prefers_direct_delegation_signal(tmp_path: Path) -> None:
    log = tmp_path / "nudges.jsonl"
    events = [{"decision": "nudge", "session_id": "s1", "prompt_id": f"p{i}"} for i in range(5)]
    events += [{"decision": "delegation", "session_id": "s1", "prompt_id": f"p{i}"} for i in range(3)]
    _write_log(log, events)

    report = build_report(log)
    assert report.nudges_delegated == 3
    assert "scout runs observed" in format_report(report)


def test_replay_classifies_transcript_prompts(tmp_path: Path) -> None:
    from haiku_scribe.gain import format_replay, replay_prompts

    project = tmp_path / "projects" / "proj"
    project.mkdir(parents=True)
    lines = [
        {"type": "user", "message": {"role": "user", "content": "scan the repo architecture"}},
        {
            "type": "user",
            "message": {
                "role": "user",
                "content": [{"type": "text", "text": "where is the check on line 42"}],
            },
        },
        {
            "type": "user",
            "message": {"role": "user", "content": [{"type": "tool_result", "content": "big dump"}]},
        },
        {"type": "user", "isSidechain": True, "message": {"role": "user", "content": "scan the repo"}},
        {"type": "user", "message": {"role": "user", "content": "<command-name>/gain</command-name>"}},
        {"type": "assistant", "message": {"role": "assistant", "content": "explore the repo"}},
        {"type": "user", "message": {"role": "user", "content": "fix the typo"}},
        "not json",
    ]
    (project / "t.jsonl").write_text(
        "\n".join(json.dumps(line) if isinstance(line, dict) else line for line in lines) + "\n",
        encoding="utf-8",
    )

    report = replay_prompts(tmp_path / "projects")
    assert report.files_scanned == 1
    assert report.prompts_seen == 3  # nudge candidate, suppressed, silent
    assert report.would_nudge == 1
    assert report.would_suppress == 1
    assert ("scan the repo", 1) in report.marker_counts

    text = format_replay(report)
    assert "Would have nudged:         1" in text
    assert "Would have suppressed:     1" in text
    assert "scan the repo" in text
    assert "Audit-only signal" in text


def test_replay_without_transcripts_reports_zero(tmp_path: Path) -> None:
    from haiku_scribe.gain import format_replay, replay_prompts

    report = replay_prompts(tmp_path / "projects")
    assert report.files_scanned == 0
    assert report.prompts_seen == 0
    assert "No transcripts found" in format_replay(report)
