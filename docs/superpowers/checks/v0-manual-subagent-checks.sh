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

for required in \
  '## Role' \
  '## Boundaries' \
  '## How Read' \
  '## Response Shape'
do
  grep -Fxq -- "$required" "$agent"
done

must_not_block="$(
  awk '
    /^You must not:$/ { capture = 1; next }
    /^## / && capture { capture = 0 }
    capture { print }
  ' "$agent"
)"

if [[ -z "$must_not_block" ]]; then
  echo "agent is missing the You must not block" >&2
  exit 1
fi

for forbidden in \
  '- Edit files.' \
  '- Write files.' \
  '- Run shell commands.' \
  '- Browse web.' \
  '- Use MCP tools.' \
  '- Invoke other agents.' \
  '- Make final root-cause conclusions.' \
  '- Make final architecture decisions.' \
  '- Make final security, authentication, authorization, permission conclusions.'
do
  grep -Fxq -- "$forbidden" <<< "$must_not_block"
done

for removed in \
  'Transcript Or Log Preflight' \
  'exactly four `##` headings' \
  'bare `L34`' \
  '## None.' \
  'None identified from inspected context'
do
  if grep -Fq -- "$removed" "$agent"; then
    echo "agent still contains removed strict-format language: $removed" >&2
    exit 1
  fi
done

grep -q 'shape guidance useful human-readable brief, not machine-parseable compliance contract in V0.' "$spec"
grep -q 'Do not open V1 while any of these remain true:' "$spec"
grep -q 'V1 may open: Yes, if V1 keeps formatting validation outside agent prompt not add enforcement before packaging proves useful.' "$worksheet"
grep -q 'Known Limitation For V1' "$worksheet"

matches="$(
  grep -RInE '(^|[^A-Za-z])(setup|doctor|uninstall|installers?|automatic configuration mutation|automatic Claude Code configuration mutation|configuration mutation|backups?|dry-?run|hooks?|reports?|nudges?|enforcement|team rollout|project rollout|team/project packaging|enterprise|enterprise-managed|enterprise controls?|enterprise-managed controls?|MCP|Codegraph)([^A-Za-z]|$)' \
    .claude \
    "$spec" \
    "$worksheet" \
    || true
)"

allowed_content=(
  'Validate whether native Claude Code custom subagent named `haiku-scribe`, running on Haiku read-only file-discovery tools, usefully compresses bulk-reading work before any installer, hook, report, nudge, enforcement, team rollout, plugin, MCP, enterprise machinery built.'
  '- Automatic Claude Code configuration mutation.'
  '- Backups.'
  '- Dry-run behavior.'
  '- Hooks.'
  '- Reports.'
  '- Prompt nudges.'
  '- Soft enforcement.'
  '- Team project rollout machinery.'
  '- Claude Code plugin packaging.'
  '- Enterprise-managed controls.'
  '- MCP.'
  '- Codegraph integration in base agent.'
  '- Use MCP tools.'
  '- agent needs shell, write, web, MCP, recursive-agent, Codegraph access useful base workflow.'
  '- `setup`.'
  '- `doctor`.'
  '- `uninstall`.'
  'Use haiku-scribe to extract evidence for whether V0 permits setup, doctor, uninstall, hooks, reports, nudges, enforcement, MCP, or Codegraph. Do not make the final scope decision.'
  '- Summary specificity: Specific enough to identify that setup, doctor, uninstall, hooks, reports, nudges, enforcement, MCP, and Codegraph are all excluded from V0 and deferred to later roadmap phases.'
  '- V1 may open: Yes, if V1 keeps formatting validation outside agent prompt not add enforcement before packaging proves useful.'
  'Transcript log compression can produce useful orientation while varying heading names, citation style, `None` wording. V1 must not solve making agent prompt substantially larger. strict structure needed, handle it through external validation, transcript extraction, report tooling, golden tests in later spec.'
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
