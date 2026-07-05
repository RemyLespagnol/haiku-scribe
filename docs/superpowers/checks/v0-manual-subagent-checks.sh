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

for forbidden in \
  '- Edit files.' \
  '- Write files.' \
  '- Run shell commands.' \
  '- Use web access.' \
  '- Use MCP tools.' \
  '- Invoke other agents.'
do
  grep -Fxq -- "$forbidden" "$agent"
done

grep -q 'Do not open V1 while any of these remain true:' "$spec"
grep -q 'V1 may open: No' "$worksheet"

matches="$(
  grep -RInE '(^|[^A-Za-z])(setup|doctor|uninstall|installers?|automatic configuration mutation|automatic Claude Code configuration mutation|configuration mutation|backups?|dry-?run|hooks?|reports?|nudges?|enforcement|team rollout|project rollout|team/project packaging|enterprise|enterprise-managed|enterprise controls?|enterprise-managed controls?|MCP|Codegraph)([^A-Za-z]|$)' \
    .claude \
    "$spec" \
    "$worksheet" \
    || true
)"

allowed_content=(
  'Validate whether a native Claude Code custom subagent named `haiku-scribe`, running on Haiku with read-only file-discovery tools, usefully compresses bulk-reading work before any installer, hook, report, nudge, enforcement, team rollout, plugin, MCP, or enterprise machinery is built.'
  '- Installer commands.'
  '- Automatic Claude Code configuration mutation.'
  '- Doctor command.'
  '- Uninstall command.'
  '- Backups.'
  '- Dry-run behavior.'
  '- Hooks.'
  '- Reports.'
  '- Prompt nudges.'
  '- Soft enforcement.'
  '- Team or project rollout machinery.'
  '- Claude Code plugin packaging.'
  '- Enterprise-managed controls.'
  '- MCP.'
  '- Codegraph integration in the base agent.'
  'When content appears secret-bearing, credential-like, or unrelated to the user request, stop and report that direct user confirmation is needed before inspecting it.'
  '- Use MCP tools.'
  'If asked edit, write, run shell commands, browse web, use MCP, call another agent, make final root-cause conclusions, make final architecture decisions, make final security conclusions, produce final public project outputs, refuse part provide only read-only evidence support fits this contract.'
  'Use haiku-scribe to extract evidence for whether V0 permits setup, doctor, uninstall, hooks, reports, nudges, enforcement, MCP, or Codegraph. Do not make the final scope decision.'
  '- The agent needs shell, write, web, MCP, recursive-agent, or Codegraph access to be useful for the base workflow.'
  '- `setup`.'
  '- `doctor`.'
  '- `uninstall`.'
  '- For evidence-extraction or scope-check tasks, do not answer without a populated `## Evidence` section using precise file references from the inspected context.'
)

remaining_matches=""
while IFS= read -r line; do
  [[ -z "$line" ]] && continue

  content="${line#*:}"
  content="${content#*:}"

  is_allowed=false
  for allowed in "${allowed_content[@]}"; do
    if [[ "$content" == "$allowed" ]]; then
      is_allowed=true
      break
    fi
  done

  if [[ "$is_allowed" == false ]]; then
    remaining_matches+="${line}"$'\n'
  fi
done <<< "$matches"

if [[ -n "$remaining_matches" ]]; then
  printf '%s' "$remaining_matches" >&2
  echo "found possible V1+ product surface in V0 files" >&2
  exit 1
fi

echo "V0 manual subagent checks passed"
