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

forbidden_work="$(awk '
  $0 == "You must not:" { in_block = 1; next }
  in_block && /^## / { exit }
  in_block { print }
' "$agent")"

grep -Fxq -- '- Edit files.' <<< "$forbidden_work"
grep -Fxq -- '- Write files.' <<< "$forbidden_work"
grep -Fxq -- '- Run shell commands.' <<< "$forbidden_work"
grep -Fxq -- '- Use web access.' <<< "$forbidden_work"
grep -Fxq -- '- Use MCP tools.' <<< "$forbidden_work"
grep -Fxq -- '- Invoke other agents.' <<< "$forbidden_work"

grep -q 'Do not open V1 while any of these remain true:' "$spec"
grep -q 'V1 may open: No' "$worksheet"

matches="$(grep -HnE '(^|[^A-Za-z])(setup|doctor|uninstall|installers?|automatic configuration mutation|automatic Claude Code configuration mutation|configuration mutation|backups?|dry-?run|hooks?|reports?|nudges?|enforcement|team rollout|project rollout|team or project rollout|team/project rollout|plugin|plugin packaging|enterprise|enterprise-managed|enterprise controls?|enterprise-managed controls?|MCP|Codegraph)([^A-Za-z]|$)' "$agent" "$spec" "$worksheet" || true)"

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
    *":- Installer commands." | \
    *":- Automatic Claude Code configuration mutation." | \
    *":- Doctor command." | \
    *":- Uninstall command." | \
    *":- Backups." | \
    *":- Dry-run behavior." | \
    *":- Hooks." | \
    *":- Reports." | \
    *":- Prompt nudges." | \
    *":- Soft enforcement." | \
    *":- Team or project rollout machinery." | \
    *":- Claude Code plugin packaging." | \
    *":- Enterprise-managed controls." | \
    *":- MCP." | \
    *":- \`setup\`." | \
    *":- \`doctor\`." | \
    *":- \`uninstall\`." | \
    *":- Backups." | \
    *":- Dry-run behavior." | \
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
