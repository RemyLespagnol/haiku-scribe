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

matches="$(grep -RInE '(^|[^A-Za-z])(setup|doctor|uninstall|hooks?|reports?|nudges?|enforcement|plugin packaging|enterprise-managed|MCP|Codegraph)([^A-Za-z]|$)' .claude docs/superpowers/specs/2026-07-04-v0-manual-subagent-design.md docs/superpowers/evaluations/2026-07-04-v0-manual-workflow-trials.md || true)"

remaining_matches=""
while IFS= read -r line; do
  [[ -z "$line" ]] && continue

  case "$line" in
    *"Out of Scope"* | \
    *"before any installer, hook, report, nudge, enforcement, team rollout, plugin, MCP, or enterprise machinery is built"* | \
    *"excludes setup, doctor, uninstall, hooks, reports, nudges, enforcement, plugin packaging, enterprise-managed controls, MCP, and Codegraph integration"* | \
    *"Do not open V1 while any of these remain true:"* | \
    *"V1 Handoff Conditions"* | \
    *"Only after V0 passes"* | \
    *":- Doctor command." | \
    *":- Uninstall command." | \
    *":- Hooks." | \
    *":- Reports." | \
    *":- Prompt nudges." | \
    *":- Soft enforcement." | \
    *":- Claude Code plugin packaging." | \
    *":- Enterprise-managed controls." | \
    *":- MCP." | \
    *":- \`setup\`." | \
    *":- \`doctor\`." | \
    *":- \`uninstall\`." | \
    *"V1 may open: No"* | \
    *"not installed into a user's global Claude Code configuration"* | \
    *"without making any implementation recommendations"* | \
    *"Do not make the final scope decision"* | \
    *"Use MCP tools"* | \
    *"Codegraph integration in the base agent"* | \
    *"direct user confirmation is needed before inspecting it"* | \
    *"If asked to edit, write, run shell commands, browse the web, use MCP, call another agent"* | \
    *"The agent needs shell, write, web, MCP, recursive-agent, or Codegraph access to be useful for the base workflow"*)
      continue
      ;;
  esac

  remaining_matches+="${line}"$'\n'
done <<< "$matches"

if [[ -n "$remaining_matches" ]]; then
  printf '%s' "$remaining_matches" >&2
  echo "found possible V1+ product surface in V0 files" >&2
  exit 1
fi

echo "V0 manual subagent checks passed"
