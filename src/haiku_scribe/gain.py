"""Read the nudge log and report Haiku Scribe usage + double-read rate.

The V1.2 hook logs every decision to ``~/.claude/haiku-scribe-nudges.jsonl``
but nothing reads it back, so cost optimization is invisible. This turns that
log into an honest scoreboard:

- how often broad reconnaissance was flagged,
- how much large-file context was deferrable away from the main window,
- how often a nudge was ignored (a raw Read/Grep after the nudge) — the
  ``pre_tool_followup`` event, which is the "raw_into_main" double-read
  signal the break-even eval calls the primary KPI.

It measures what the log can prove (nudge activity), not token dollars: the
hook never sees whether the scout actually ran, so "deferrable" is potential,
and the ignored-nudge count is the realized-loss signal.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class GainReport:
    prompts_flagged: int  # UserPromptSubmit "nudge" events
    large_reads_flagged: int  # size-gated "size_nudge" events
    bytes_flagged: int  # sum of size_bytes across size_nudge events
    followups: int  # "pre_tool_followup": nudge ignored, raw read anyway

    @property
    def compliance(self) -> float | None:
        """Fraction of flagged prompts NOT followed by a raw read (0..1)."""
        if self.prompts_flagged == 0:
            return None
        return max(0.0, 1 - self.followups / self.prompts_flagged)


def build_report(log_path: Path) -> GainReport:
    prompts = large = followups = 0
    total_bytes = 0
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
            if decision == "nudge":
                prompts += 1
            elif decision == "size_nudge":
                large += 1
                try:
                    total_bytes += int(event.get("size_bytes") or 0)
                except (TypeError, ValueError):
                    pass
            elif decision == "pre_tool_followup":
                followups += 1
    return GainReport(prompts, large, total_bytes, followups)


def format_report(report: GainReport) -> str:
    lines = [
        "Haiku Scribe gain report",
        f"  Broad prompts flagged:      {report.prompts_flagged}",
        f"  Large-file reads flagged:   {report.large_reads_flagged}"
        f" ({report.bytes_flagged // 1000} KB deferrable from main context)",
        f"  Nudges ignored (raw read):  {report.followups}",
    ]
    if report.compliance is not None:
        lines.append(f"  Nudge compliance:           {report.compliance * 100:.0f}%")
    if report.prompts_flagged == 0 and report.large_reads_flagged == 0:
        lines.append("  No activity logged yet — enable hooks with `setup --hooks on`.")
    return "\n".join(lines)
