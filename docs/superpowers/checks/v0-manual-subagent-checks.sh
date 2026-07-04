#!/usr/bin/env bash
set -euo pipefail

agent=".claude/agents/haiku-scribe.md"
spec="docs/superpowers/specs/2026-07-04-v0-manual-subagent-design.md"
worksheet="docs/superpowers/evaluations/2026-07-04-v0-manual-workflow-trials.md"

for path in "$agent" "$spec" "$worksheet"; do
  if [[ ! -f "$path" ]]; then
    echo "missing required V0 file: $path" >&2
    exit 1
  fi
done

grep -q '^name: haiku-scribe$' "$agent"
grep -q '^model: haiku$' "$agent"
grep -q '^tools: Read, Glob, Grep$' "$agent"

grep -q 'Edit files' "$agent"
grep -q 'Write files' "$agent"
grep -q 'Run shell commands' "$agent"
grep -q 'Use web access' "$agent"
grep -q 'Use MCP tools' "$agent"
grep -q 'Invoke other agents' "$agent"

grep -q 'Do not open V1 while any of these remain true:' "$spec"
grep -q 'V1 may open: No' "$worksheet"

if grep -RInE '(^|[^A-Za-z])(setup|doctor|uninstall|hooks?|reports?|nudges?|enforcement|plugin packaging|enterprise-managed|MCP|Codegraph)([^A-Za-z]|$)' .claude docs/superpowers/specs/2026-07-04-v0-manual-subagent-design.md docs/superpowers/evaluations/2026-07-04-v0-manual-workflow-trials.md \
  | grep -Ev 'Out of Scope|excludes|must not|Do not open V1|V1 Handoff Conditions|after V0 passes|No|not installed|not evaluated|without making any implementation recommendations|Do not make|permits setup|excluded from V0|Forbidden Work|Refusal Rules|Use MCP tools|Codegraph integration|plugin|enterprise|hooks|reports|nudges|enforcement|setup|doctor|uninstall|direct user confirmation|refuse that part|refuse part|- MCP\.|agent needs shell, write, web, MCP'; then
  echo "found possible V1+ product surface in V0 files" >&2
  exit 1
fi

echo "V0 manual subagent checks passed"
