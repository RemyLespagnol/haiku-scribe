# Task 4 Report

## Summary

Replaced `docs/superpowers/checks/v0-manual-subagent-checks.sh` with a simplified V0 contract check that validates the landed agent, spec, and evaluation files, rejects the removed strict formatter language, and allows the current V0 wording rather than the normalized draft text.

## Verification

Confirmed the clean check passes:

```bash
rtk run docs/superpowers/checks/v0-manual-subagent-checks.sh
```

Output:

```text
V0 manual subagent checks passed
```

Confirmed the negative regression fails as expected when the removed strict formatter heading is appended to the agent:

```bash
rtk proxy bash -lc "cp .claude/agents/haiku-scribe.md /tmp/haiku-scribe-agent.bak && printf '\n## Transcript Or Log Preflight\n' >> .claude/agents/haiku-scribe.md && docs/superpowers/checks/v0-manual-subagent-checks.sh; status=\$?; mv /tmp/haiku-scribe-agent.bak .claude/agents/haiku-scribe.md; exit \$status"
```

Output:

```text
agent still contains removed strict-format language: Transcript Or Log Preflight
```

Re-ran the clean check after restoration and it still passed.

## Self-Review

The change is limited to the owned check script and the task report. The script now tracks the landed Task 1/2/3 contract wording, including the `## How Read` and `- Browse web.` drift noted during ambiguity resolution, and it still rejects the removed strict formatter markers.

## Notes

No remaining concerns.
