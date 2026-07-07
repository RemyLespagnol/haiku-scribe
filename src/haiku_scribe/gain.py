"""Read the nudge log and report Haiku Scribe usage + double-read rate.

The V1.2 hook logs every decision to ``~/.claude/haiku-scribe-nudges.jsonl``
but nothing reads it back, so cost optimization is invisible. This turns that
log into an honest scoreboard:

- how often broad reconnaissance was flagged,
- how much large-file context was deferrable away from the main window,
- how often a nudge was ignored (a raw Read/Grep after the nudge) — the
  ``pre_tool_followup`` event, which is the "raw_into_main" double-read
  signal the break-even eval calls the primary KPI.

It measures what the log can prove (nudge activity), not token dollars.
"Deferrable" is potential, the ignored-nudge count is the realized-loss
signal, and "delegation" events (the Task matcher observing a haiku-scribe
spawn) are the direct followed-signal — observed scout runs, still not
proven token savings.
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class GainReport:
    prompts_flagged: int  # UserPromptSubmit "nudge" events
    large_reads_flagged: int  # size-gated "size_nudge" events
    bytes_flagged: int  # sum of size_bytes across size_nudge events
    followups: int  # "pre_tool_followup": nudge ignored, raw read anyway
    prompt_id_events: int = 0  # nudge/followup events keyed by a real prompt_id
    fallback_events: int = 0  # nudge/followup events keyed by a fallback hash
    delegations: int = 0  # "delegation": haiku-scribe scout spawn observed
    nudges_delegated: int = 0  # flagged prompts with an observed scout run
    suppressed: int = 0  # nudges suppressed by negative patterns (audit-only)

    @property
    def compliance(self) -> float | None:
        """Fraction of flagged prompts NOT followed by a raw read (0..1)."""
        if self.prompts_flagged == 0:
            return None
        return max(0.0, 1 - self.followups / self.prompts_flagged)

    @property
    def high_confidence(self) -> bool:
        """True when every nudge/followup event carried a real prompt_id.
        Fallback keys attribute follow-ups to the latest flagged prompt, so
        compliance may be over- or under-counted."""
        return self.fallback_events == 0


def build_report(log_path: Path) -> GainReport:
    prompts = large = followups = 0
    total_bytes = 0
    prompt_id_events = fallback_events = 0
    delegations = suppressed = 0
    nudge_keys: set[tuple[object, object]] = set()
    delegation_keys: set[tuple[object, object]] = set()
    if log_path.exists():
        text = log_path.read_text(encoding="utf-8", errors="replace")
        for line in text.splitlines():
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(event, dict):
                continue
            decision = event.get("decision")
            key = (event.get("session_id"), event.get("prompt_key") or event.get("prompt_id"))
            if decision == "nudge":
                prompts += 1
                if key[1] is not None:
                    nudge_keys.add(key)
            elif decision == "delegation":
                delegations += 1
                if key[1] is not None:
                    delegation_keys.add(key)
            elif decision == "suppressed":
                suppressed += 1
            elif decision == "size_nudge":
                large += 1
                try:
                    total_bytes += int(event.get("size_bytes") or 0)
                except (TypeError, ValueError):
                    pass
            elif decision == "pre_tool_followup":
                followups += 1
            if decision in ("nudge", "pre_tool_followup"):
                # Older hook versions have no "identity" field; classify by
                # whether they carried a prompt_id at all.
                identity = event.get("identity")
                if identity == "prompt_id" or (identity is None and event.get("prompt_id")):
                    prompt_id_events += 1
                else:
                    fallback_events += 1
    return GainReport(
        prompts,
        large,
        total_bytes,
        followups,
        prompt_id_events,
        fallback_events,
        delegations,
        len(nudge_keys & delegation_keys),
        suppressed,
    )


def format_report(report: GainReport) -> str:
    lines = [
        "Haiku Scribe gain report",
        f"  Broad prompts flagged:      {report.prompts_flagged}",
        f"  Large-file reads flagged:   {report.large_reads_flagged}"
        f" ({report.bytes_flagged // 1000} KB deferrable from main context)",
        f"  Nudges ignored (raw read):  {report.followups}",
        f"  Scout delegations observed: {report.delegations} (direct signal)",
    ]
    if report.prompts_flagged:
        lines.append(
            f"  Flagged prompts delegated:  {report.nudges_delegated} of {report.prompts_flagged}"
        )
    if report.suppressed:
        lines.append(
            f"  Nudges suppressed:          {report.suppressed}"
            " (negative patterns; likely false positives avoided — audit-only)"
        )
    if report.compliance is not None:
        lines.append(f"  Nudge compliance:           {report.compliance * 100:.0f}%")
    if report.prompt_id_events or report.fallback_events:
        lines.append(
            f"  Prompt identity:            {report.prompt_id_events} with prompt_id"
            f" / {report.fallback_events} fallback"
        )
        if report.high_confidence:
            lines.append("  Confidence: high — every nudge event carried a prompt_id.")
        else:
            lines.append(
                "  Confidence: proxy-only — some events lacked prompt_id; fallback keys"
                " attribute follow-ups to the latest flagged prompt, so compliance may"
                " be over- or under-counted."
            )
    lines.append(f"  Verdict: {_verdict(report)}")
    return "\n".join(lines)


@dataclass(frozen=True)
class ReplayReport:
    files_scanned: int
    prompts_seen: int
    would_nudge: int
    would_suppress: int
    marker_counts: tuple[tuple[str, int], ...]


def _hook_classifier():
    """Execute the generated hook script and return its classify_prompt, so
    replay uses exactly what an installed hook would do — no duplicated lists."""
    from haiku_scribe.v1_2_hooks import render_nudge_hook_script

    namespace: dict[str, object] = {"__name__": "haiku_scribe_hook_replay"}
    exec(compile(render_nudge_hook_script(), "<haiku-scribe-hook>", "exec"), namespace)
    return namespace["classify_prompt"]


def _user_prompt_text(event: dict) -> str | None:
    if event.get("type") != "user" or event.get("isSidechain") or event.get("isMeta"):
        return None
    message = event.get("message")
    if not isinstance(message, dict):
        return None
    content = message.get("content")
    if isinstance(content, list):
        texts = []
        for block in content:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "tool_result":
                return None  # tool output echoed back, not a typed prompt
            if block.get("type") == "text":
                texts.append(str(block.get("text", "")))
        content = "\n".join(texts)
    if not isinstance(content, str) or not content.strip():
        return None
    if content.lstrip().startswith("<"):
        return None  # slash-command wrappers and injected system content
    return content


def replay_prompts(projects_dir: Path) -> ReplayReport:
    classify = _hook_classifier()
    files = sorted(projects_dir.rglob("*.jsonl")) if projects_dir.is_dir() else []
    prompts = nudges = suppressed = 0
    marker_counts: Counter[str] = Counter()
    for path in files:
        try:
            with path.open(encoding="utf-8", errors="replace") as handle:
                for line in handle:
                    try:
                        event = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if not isinstance(event, dict):
                        continue
                    text = _user_prompt_text(event)
                    if text is None:
                        continue
                    prompts += 1
                    matched, negative = classify(text.lower())
                    if not matched:
                        continue
                    if negative is not None:
                        suppressed += 1
                    else:
                        nudges += 1
                        marker_counts.update(matched)
        except OSError:
            continue
    ranked = tuple(sorted(marker_counts.items(), key=lambda item: (-item[1], item[0])))
    return ReplayReport(len(files), prompts, nudges, suppressed, ranked)


def format_replay(report: ReplayReport) -> str:
    lines = [
        "Haiku Scribe replay — what would the current markers have done?",
        f"  Transcript files scanned:  {report.files_scanned}",
        f"  User prompts seen:         {report.prompts_seen}",
        f"  Would have nudged:         {report.would_nudge}",
        f"  Would have suppressed:     {report.would_suppress} (negative patterns)",
    ]
    if report.files_scanned == 0:
        lines.append("  No transcripts found under ~/.claude/projects.")
    if report.marker_counts:
        lines.append("  Top markers:")
        for marker, count in report.marker_counts[:10]:
            lines.append(f"    {marker:<20} {count}")
    lines.append(
        "  Audit-only signal: replays current marker lists over past prompts;"
        " says nothing about whether delegation would have saved tokens."
    )
    return "\n".join(lines)


def _verdict(report: GainReport) -> str:
    """One honest, decision-useful line. All figures are proxy signals —
    the log proves nudge activity, never actual token savings."""
    total = report.prompts_flagged + report.large_reads_flagged
    if total == 0:
        return "no activity logged yet — enable hooks with `setup --hooks on`."
    if total < 5:
        return "not enough signal yet — keep hooks on and re-check after more sessions."
    if report.prompts_flagged and report.nudges_delegated / report.prompts_flagged >= 0.5:
        return "nudges are being followed — scout runs observed after flagged prompts; keep hooks on."
    if report.compliance is None or report.compliance >= 0.5:
        return "nudges are mostly followed (proxy signal) — keep hooks on."
    return (
        "most nudges are ignored — hooks are audit-only right now; "
        "keep them for measurement or remove with plain `setup`."
    )
