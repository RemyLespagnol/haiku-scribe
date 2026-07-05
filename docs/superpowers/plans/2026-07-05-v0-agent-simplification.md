# V0 Agent Simplification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Simplify the V0 `haiku-scribe` agent prompt and evaluation gate so V0 validates useful cheap context compression instead of strict formatter compliance.

**Architecture:** Keep the product surface unchanged: one manual Claude Code subagent, V0 docs, and a shell check. Replace the compliance-heavy prompt with a short pragmatic contract, then align the V0 spec, trial gate, and check script with workflow usefulness.

**Tech Stack:** Markdown, Claude Code custom subagent frontmatter, Bash shell checks, Git.

## Global Constraints

- Keep `haiku-scribe` read-only with `tools: Read, Glob, Grep`.
- Do not add setup, doctor, uninstall, hooks, reports, prompt nudges, enforcement, MCP, Codegraph, plugin packaging, or team rollout.
- The agent must not edit, write, run shell commands, browse, use MCP, call agents, or make final decisions.
- V0 evaluates workflow usefulness, not machine-parseable output stability.
- Prefix shell commands with `rtk`, except raw commands used only to debug command-output filtering.
- Use `git add -f` for ignored files under `.claude/` and `docs/`.

---

## File Structure

- Modify: `.claude/agents/haiku-scribe.md`
  - Owns the manual project-local Claude Code subagent contract.
  - Replace the compliance-heavy prompt with a concise read-only context-compression prompt.
- Modify: `docs/superpowers/specs/2026-07-04-v0-manual-subagent-design.md`
  - Owns the V0 source-of-truth spec.
  - Align response-shape and gate language with the simplified agent.
- Modify: `docs/superpowers/evaluations/2026-07-04-v0-manual-workflow-trials.md`
  - Owns manual trial outcomes and the V0 gate decision.
  - Reclassify transcript/log formatting instability as a known limitation unless it damages workflow usefulness or creates false confidence.
- Modify: `docs/superpowers/checks/v0-manual-subagent-checks.sh`
  - Owns fast repository validation for V0 boundaries.
  - Check the simplified safety contract and reject removed strict-format prompt language.

## Task 1: Simplify The Agent Prompt

**Files:**
- Modify: `.claude/agents/haiku-scribe.md`
- Test: `docs/superpowers/checks/v0-manual-subagent-checks.sh`

**Interfaces:**
- Consumes: existing Claude Code custom subagent frontmatter.
- Produces: a shorter prompt with sections `Role`, `Boundaries`, `How To Read`, and `Response Shape`.

- [ ] **Step 1: Inspect the current agent prompt**

Run:

```bash
rtk read .claude/agents/haiku-scribe.md
```

Expected: output includes `## Transcript Or Log Preflight`, exact heading-count rules, and transcript/log-specific citation rules.

- [ ] **Step 2: Replace the agent file**

Replace `.claude/agents/haiku-scribe.md` with this complete content:

````markdown
---
name: haiku-scribe
description: Read-only context compression worker for bulk file reading, large-file orientation, log or transcript summarization, generated output summarization, cross-file flow mapping, and evidence extraction. Use before loading broad raw context. Do not use for final reasoning, edits, security conclusions, architecture decisions, commits, or public summaries.
model: haiku
tools: Read, Glob, Grep
---

# Haiku Scribe

## Role

You are a read-only context-compression worker for Claude Code.

Read only the context needed for the request and return a compact brief so the main Claude session can reason without loading excessive raw files, logs, transcripts, or generated output.

## Boundaries

You may:

- Read files requested by the main Claude session.
- Search repository text with exact patterns.
- List files with glob patterns.
- Summarize large files, logs, transcripts, generated output, or related files.
- Extract evidence with file paths and line numbers when available.
- Identify uncertainty and recommend focused direct reads.

You must not:

- Edit files.
- Write files.
- Run shell commands.
- Browse the web.
- Use MCP tools.
- Invoke other agents.
- Make final root-cause conclusions.
- Make final architecture decisions.
- Make final security, authentication, authorization, or permission conclusions.
- Produce final PR summaries, commit messages, release notes, or public project outputs.

## How To Read

- Prefer compact evidence over exhaustive dumping.
- When specific files are named, inspect those files first.
- For broad orientation, use `Glob` and `Grep` to find relevant files before reading.
- For large files, summarize structure and read only regions needed to answer.
- If content appears secret-bearing, credential-like, or unrelated to the request, stop and say direct user confirmation is needed before inspecting it.
- Do not invent evidence. If a claim depends on missing context, list it as uncertainty.

## Response Shape

Use this shape as a concise brief:

```text
## Summary
- Two to six bullets with the compressed answer.

## Evidence
- `path/to/file.ext:line`: Observed fact, when line numbers are available.

## Unknowns / Risks
- Gaps, assumptions, or reasons confidence is limited.

## Suggested Reads
- `path/to/file.ext:line`: Exact context the main Claude session should inspect, or `None` if no direct read is needed.
```

The main Claude session owns final reasoning, verification, edits, and user-facing decisions.
````

- [ ] **Step 3: Verify removed over-strict language is gone**

Run:

```bash
rtk grep "Transcript Or Log Preflight|exactly four|full/path.ext|bare `L34`|## None|None identified from inspected context" .claude/agents/haiku-scribe.md
```

Expected: command exits non-zero with no matches.

- [ ] **Step 4: Verify core safety contract remains**

Run:

```bash
rtk grep "^name: haiku-scribe$|^model: haiku$|^tools: Read, Glob, Grep$|Edit files|Write files|Run shell commands|Use MCP tools|Invoke other agents|final root-cause|final architecture|final security" .claude/agents/haiku-scribe.md
```

Expected: output contains the three frontmatter lines and all forbidden-work lines.

- [ ] **Step 5: Commit the simplified agent**

Run:

```bash
rtk git add -f .claude/agents/haiku-scribe.md
rtk git commit -m "docs: simplify v0 haiku scribe agent"
```

Expected: commit succeeds.

## Task 2: Align The V0 Spec With The Pragmatic Agent

**Files:**
- Modify: `docs/superpowers/specs/2026-07-04-v0-manual-subagent-design.md`
- Reference: `docs/superpowers/specs/2026-07-05-v0-agent-simplification-design.md`

**Interfaces:**
- Consumes: simplified agent contract from Task 1.
- Produces: V0 spec language that treats response shape as guidance and workflow usefulness as the gate.

- [ ] **Step 1: Inspect current strict sections**

Run:

```bash
rtk grep "Required Response Shape|Transcript Or Log Preflight|Non-Passage Conditions|V1 Handoff Conditions|exactly four|bare `L34`" docs/superpowers/specs/2026-07-04-v0-manual-subagent-design.md
```

Expected: output shows the response-shape, transcript/log preflight, and strict formatting language that will be simplified.

- [ ] **Step 2: Replace strict response rules**

In `docs/superpowers/specs/2026-07-04-v0-manual-subagent-design.md`, replace the `## Required Response Shape`, `## Evidence Rules`, and `## Transcript Or Log Preflight` sections with:

````markdown
## Response Shape

Haiku Scribe should return a concise evidence-oriented brief:

```text
## Summary
- Two to six bullets with the compressed answer.

## Evidence
- `path/to/file.ext:line`: Observed fact, when line numbers are available.

## Unknowns / Risks
- Gaps, assumptions, or reasons confidence is limited.

## Suggested Reads
- `path/to/file.ext:line`: Exact context the main Claude session should inspect, or `None` if no direct read is needed.
```

This shape is guidance for a useful human-readable brief, not a machine-parseable compliance contract in V0.

## Evidence Rules

- Use precise file paths when available.
- Include line numbers when Claude Code tool output provides them.
- Distinguish observed facts from interpretations.
- Do not invent line numbers or citations.
- If a claim depends on missing context, list it under `Unknowns / Risks`.
- Keep summaries specific enough that the main Claude session can choose focused follow-up reads.
- For logs and transcripts, prefer citing the inspected artifact itself, but do not treat minor citation-format variance as a V0 blocker unless it makes verification impractical or creates false confidence.
````

- [ ] **Step 3: Revise non-passage conditions**

In the same file, update `## Non-Passage Conditions` to:

````markdown
## Non-Passage Conditions

Do not open V1 while any of these remain true:

- Users cannot tell when to use Haiku Scribe.
- Summaries are too generic to support focused follow-up reads.
- The subagent regularly drifts into conclusions reserved for the main model.
- Safety boundaries depend on convention alone rather than a clear contract.
- The agent needs shell, write, web, MCP, recursive-agent, or Codegraph access to be useful for the base workflow.
- Transcript or log summaries create false confidence, hide material uncertainty, or are too imprecise for targeted main-model verification.
````

- [ ] **Step 4: Verify the spec reflects the new boundary**

Run:

```bash
rtk grep "machine-parseable compliance contract|minor citation-format variance|creates false confidence|Do not open V1 while any of these remain true" docs/superpowers/specs/2026-07-04-v0-manual-subagent-design.md
```

Expected: output contains all four phrases.

- [ ] **Step 5: Verify removed strict preflight language is gone**

Run:

```bash
rtk grep "Transcript Or Log Preflight|exactly four `##` headings|bare `L34`|## None|None identified from inspected context" docs/superpowers/specs/2026-07-04-v0-manual-subagent-design.md
```

Expected: command exits non-zero with no matches.

- [ ] **Step 6: Commit the aligned V0 spec**

Run:

```bash
rtk git add -f docs/superpowers/specs/2026-07-04-v0-manual-subagent-design.md
rtk git commit -m "docs: align v0 spec with simplified agent"
```

Expected: commit succeeds.

## Task 3: Reframe The Trial Gate Around Workflow Usefulness

**Files:**
- Modify: `docs/superpowers/evaluations/2026-07-04-v0-manual-workflow-trials.md`
- Reference: `docs/superpowers/specs/2026-07-05-v0-agent-simplification-design.md`

**Interfaces:**
- Consumes: revised V0 spec from Task 2.
- Produces: trial log that records Trial 3 formatting instability as a limitation, not an automatic V1 blocker.

- [ ] **Step 1: Inspect current gate language**

Run:

```bash
rtk grep "Final V0 Gate Decision|V1 may open|Minimal Unblock|Trial 3 rerun|exact `##` headings|Evidence quality" docs/superpowers/evaluations/2026-07-04-v0-manual-workflow-trials.md
```

Expected: output shows the current gate still blocks V1 on exact formatting and reruns.

- [ ] **Step 2: Replace the final gate decision**

In `docs/superpowers/evaluations/2026-07-04-v0-manual-workflow-trials.md`, replace the `## Final V0 Gate Decision` and `## Minimal Unblock For Opening V1` sections with:

````markdown
## Final V0 Gate Decision

Product or usage gate:

- Status: Pass with known limitation
- Evidence: Trials 1, 2, 4, and 5 show useful context compression for document orientation, large single-file summarization, cross-file evidence mapping, and scoped evidence extraction. Trial 3 produced useful transcript orientation but exposed output-format instability.

Technical or security gate:

- Status: Pass with known limitation
- Evidence: The project-local subagent was invokable, stayed read-only in observed trials, and maintained the main-model ownership boundary. The remaining issue is not safety or usefulness; it is strict output-shape stability for transcript/log compression.

Decision:

- V0 status: Pass with known limitation
- V1 may open: Yes, if V1 keeps formatting validation outside the agent prompt and does not add enforcement before packaging proves useful.
- Reason: V0 validated the core workflow value. Transcript/log formatting variance should be tracked as a limitation, not used to keep expanding the Haiku prompt.

## Known Limitation For V1

Transcript and log compression can produce useful orientation while varying heading names, citation style, or `None` wording. V1 must not solve that by making the agent prompt substantially larger. If strict structure is needed, handle it through external validation, transcript extraction, report tooling, or golden tests in a later spec.
````

- [ ] **Step 3: Verify the new gate language**

Run:

```bash
rtk grep "Pass with known limitation|V1 may open: Yes|formatting validation outside the agent prompt|Known Limitation For V1" docs/superpowers/evaluations/2026-07-04-v0-manual-workflow-trials.md
```

Expected: output contains all four phrases.

- [ ] **Step 4: Verify old unblock checklist is gone**

Run:

```bash
rtk grep "Minimal Unblock For Opening V1|Trial 3 rerun recorded `Pass`|exact `##` headings|JSONL verification rerun" docs/superpowers/evaluations/2026-07-04-v0-manual-workflow-trials.md
```

Expected: command exits non-zero with no matches.

- [ ] **Step 5: Commit the reframed evaluation**

Run:

```bash
rtk git add -f docs/superpowers/evaluations/2026-07-04-v0-manual-workflow-trials.md
rtk git commit -m "docs: reframe v0 gate around workflow value"
```

Expected: commit succeeds.

## Task 4: Update V0 Checks For The Simplified Contract

**Files:**
- Modify: `docs/superpowers/checks/v0-manual-subagent-checks.sh`
- Review: `.claude/agents/haiku-scribe.md`
- Review: `docs/superpowers/specs/2026-07-04-v0-manual-subagent-design.md`
- Review: `docs/superpowers/evaluations/2026-07-04-v0-manual-workflow-trials.md`

**Interfaces:**
- Consumes: simplified agent, revised V0 spec, and reframed trial gate.
- Produces: shell check that enforces V0 safety boundaries without requiring the old strict formatter prompt.

- [ ] **Step 1: Replace the check script**

Replace `docs/superpowers/checks/v0-manual-subagent-checks.sh` with:

````bash
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
  '## How To Read' \
  '## Response Shape' \
  '- Edit files.' \
  '- Write files.' \
  '- Run shell commands.' \
  '- Browse the web.' \
  '- Use MCP tools.' \
  '- Invoke other agents.' \
  '- Make final root-cause conclusions.' \
  '- Make final architecture decisions.' \
  '- Make final security, authentication, authorization, or permission conclusions.'
do
  grep -Fxq -- "$required" "$agent"
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

grep -q 'This shape is guidance for a useful human-readable brief, not a machine-parseable compliance contract in V0.' "$spec"
grep -q 'Do not open V1 while any of these remain true:' "$spec"
grep -q 'V1 may open: Yes' "$worksheet"
grep -q 'Known Limitation For V1' "$worksheet"

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
  '- Use MCP tools.'
  '- The agent needs shell, write, web, MCP, recursive-agent, or Codegraph access to be useful for the base workflow.'
  '- `setup`.'
  '- `doctor`.'
  '- `uninstall`.'
  '- V1 may open: Yes, if V1 keeps formatting validation outside the agent prompt and does not add enforcement before packaging proves useful.'
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
````

- [ ] **Step 2: Ensure the script is executable**

Run:

```bash
rtk chmod +x docs/superpowers/checks/v0-manual-subagent-checks.sh
```

Expected: command succeeds with no output.

- [ ] **Step 3: Run the V0 check script**

Run:

```bash
rtk docs/superpowers/checks/v0-manual-subagent-checks.sh
```

Expected: output contains `V0 manual subagent checks passed`.

- [ ] **Step 4: Run a negative check for removed strict prompt language**

Run:

```bash
rtk proxy bash -lc "cp .claude/agents/haiku-scribe.md /tmp/haiku-scribe-agent.bak && printf '\n## Transcript Or Log Preflight\n' >> .claude/agents/haiku-scribe.md && docs/superpowers/checks/v0-manual-subagent-checks.sh; status=\$?; mv /tmp/haiku-scribe-agent.bak .claude/agents/haiku-scribe.md; exit \$status"
```

Expected: command exits non-zero and output includes `agent still contains removed strict-format language: Transcript Or Log Preflight`.

- [ ] **Step 5: Verify the restored agent is clean**

Run:

```bash
rtk docs/superpowers/checks/v0-manual-subagent-checks.sh
```

Expected: output contains `V0 manual subagent checks passed`.

- [ ] **Step 6: Commit the updated checks**

Run:

```bash
rtk git add -f docs/superpowers/checks/v0-manual-subagent-checks.sh
rtk git commit -m "test: update v0 checks for simplified agent"
```

Expected: commit succeeds.

## Task 5: Final Verification And Handoff

**Files:**
- Review: `.claude/agents/haiku-scribe.md`
- Review: `docs/superpowers/specs/2026-07-04-v0-manual-subagent-design.md`
- Review: `docs/superpowers/evaluations/2026-07-04-v0-manual-workflow-trials.md`
- Review: `docs/superpowers/checks/v0-manual-subagent-checks.sh`

**Interfaces:**
- Consumes: all commits from Tasks 1-4.
- Produces: verified implementation ready for manual Claude Code trial reruns.

- [ ] **Step 1: Run the V0 check script**

Run:

```bash
rtk docs/superpowers/checks/v0-manual-subagent-checks.sh
```

Expected: output contains `V0 manual subagent checks passed`.

- [ ] **Step 2: Verify no unwanted strict language remains**

Run:

```bash
rtk grep "Transcript Or Log Preflight|exactly four|bare `L34`|None identified from inspected context|## None" .claude/agents/haiku-scribe.md docs/superpowers/specs/2026-07-04-v0-manual-subagent-design.md
```

Expected: command exits non-zero with no matches.

- [ ] **Step 3: Verify V0 did not add V1 implementation files**

Run each command:

```bash
rtk find setup
rtk find doctor
rtk find uninstall
rtk find hooks
rtk find report
```

Expected: no output for each command.

- [ ] **Step 4: Inspect final repository status**

Run:

```bash
rtk git status --short
```

Expected: no output.

- [ ] **Step 5: Recommend one manual rerun**

In the final execution response, ask the user to rerun:

```text
Use the haiku-scribe subagent to summarize docs/superpowers/specs/2026-07-04-haiku-scribe-roadmap-design.md. Return a compact evidence brief.
```

Expected observation: the new agent should produce a shorter, less compliance-heavy response while preserving read-only evidence-oriented behavior.

## Self-Review

Spec coverage:

- Simplifies `.claude/agents/haiku-scribe.md`: Task 1.
- Keeps safety boundaries explicit: Task 1 and Task 4.
- Removes transcript/log-specific compliance machinery: Task 1, Task 2, and Task 5.
- Reframes V0 around workflow usefulness: Task 2 and Task 3.
- Keeps V1+ surfaces out of V0: Global Constraints and Task 4.
- Runs checks and reports manual rerun: Task 4 and Task 5.

Placeholder scan:

- No `TBD`, `TODO`, `implement later`, or open-ended “add appropriate” instructions remain.
- Every edit step includes exact replacement text or exact verification commands.

Type and name consistency:

- Agent name remains `haiku-scribe`.
- Agent path remains `.claude/agents/haiku-scribe.md`.
- V0 spec path remains `docs/superpowers/specs/2026-07-04-v0-manual-subagent-design.md`.
- Evaluation path remains `docs/superpowers/evaluations/2026-07-04-v0-manual-workflow-trials.md`.
- Check script path remains `docs/superpowers/checks/v0-manual-subagent-checks.sh`.
