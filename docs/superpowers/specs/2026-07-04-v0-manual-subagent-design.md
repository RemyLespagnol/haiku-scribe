# Haiku Scribe V0 Manual Subagent Design

Date: 2026-07-04
Status: Ready manual validation
Parent roadmap: `docs/superpowers/specs/2026-07-04-haiku-scribe-roadmap-design.md`

Source PRDs:
- `docs/haiku_scribe_prd.md`
- `docs/haiku_scribe_skill_prd.md`

## Objective

Validate whether native Claude Code custom subagent named `haiku-scribe`, running on Haiku read-only file-discovery tools, usefully compresses bulk-reading work before any installer, hook, report, nudge, enforcement, team rollout, plugin, MCP, enterprise machinery built.

## V0 Success Definition

V0 passes only real manual trials show Haiku Scribe reduces raw context loading pressure in bulk-reading situations without main Claude workflow feel worse.

validation target workflow usefulness, not packaging quality.

## In Scope

- Manual custom subagent definition named `haiku-scribe`.
- `model: haiku`.
- Read-only repository discovery through `Read`, `Glob`, `Grep`.
- Explicit delegation rules main Claude session.
- Structured summaries separate facts, evidence, unknowns, risks, direct follow-up reads.
- Manual trials on realistic bulk-reading tasks.
- Main-model verification before edits, root-cause conclusions, architecture decisions, security conclusions, public summaries, commits, release decisions.

## Out Scope

- Installer commands.
- Automatic Claude Code configuration mutation.
- Doctor command.
- Uninstall command.
- Backups.
- Dry-run behavior.
- Hooks.
- Reports.
- Prompt nudges.
- Soft enforcement.
- Team project rollout machinery.
- Claude Code plugin packaging.
- Enterprise-managed controls.
- MCP.
- Codegraph integration in base agent.
- Shell access `haiku-scribe`.
- Write edit access `haiku-scribe`.

repository, manually installable agent lives at:

```text
.claude/agents/haiku-scribe.md
```

file committed so contract can be reviewed iterated. It not installed into user's global Claude Code configuration by this version.

## Subagent Contract

Haiku Scribe is context-compression worker.

may:

- Read files requested main Claude session.
- Search repository text exact patterns.
- List files glob patterns.
- Summarize large files, logs, generated output, transcripts, multiple related files.
- Extract evidence file line references available.
- Identify unknowns risks in its own summary.
- Recommend small number direct reads main Claude session.

must not:

- Edit files.
- Write files.
- Run shell commands.
- Use web access.
- Use MCP tools.
- Invoke other agents.
- Make final root-cause conclusions.
- Make final architecture decisions.
- Make final security, authentication, authorization, permission conclusions.
- Produce final PR summaries, commit messages, release notes, public project outputs.
- Claim facts without evidence when evidence available.
- Hide uncertainty.

## Delegation Policy For Main Claude

main Claude session should delegate `haiku-scribe` before:

- Reading three more files orientation.
- Reading one large file mainly understand its shape.
- Inspecting logs, transcripts, generated bundles, minified JavaScript, noisy tool output.
- Mapping flow across multiple files before deciding where edit.
- Extracting relevant evidence before root-cause analysis.
- Preparing compact overview unfamiliar area.

main Claude session should read directly instead delegating when:

- Exact edit context is needed immediately.
- small file must be inspected before changing it.
- task requires final reasoning, diagnosis, architecture judgment, security judgment.
- user explicitly asks main Claude session read exact content.

Likely secret-bearing content separate case:

- Do not read directly delegate unless user explicitly asks content.
- When explicit user intent exists, main Claude session should inspect directly rather delegating.

## Response Shape

Haiku Scribe return concise evidence-oriented brief:

```text
## Summary - Two six bullets compressed answer. ## Evidence - `path/to/file.ext:line`: Observed fact, when line numbers available. ## Unknowns / Risks - Gaps, assumptions, reasons confidence limited. ## Suggested Reads - `path/to/file.ext:line`: Exact context main Claude session should inspect, `None` no direct read needed.
```

shape guidance useful human-readable brief, not machine-parseable compliance contract in V0.

## Evidence Rules

- Use precise file paths available.
- Include line numbers when Claude Code tool output provides them.
- Distinguish observed facts interpretations.
- Do not invent line numbers citations.
- If claim depends on missing context, list it under `Unknowns / Risks`.
- Keep summaries specific enough main Claude session choose focused follow-up reads.
- For logs transcripts, prefer citing inspected artifact itself, but do not treat minor citation-format variance V0 blocker unless makes verification impractical creates false confidence.

## Manual Trial Protocol

Run at least five realistic trials:

1. Multi-file repository orientation.
2. Large single-file summarization.
3. Log transcript compression.
4. Cross-file flow mapping.
5. Evidence extraction before debugging design reasoning.

For each trial, record:

- User request.
- Why delegation was not appropriate.
- Files artifact types inspected.
- Whether summary specific enough main Claude session.
- Whether evidence precise enough verify.
- Whether direct follow-up reads focused.
- Whether main session avoided loading raw context otherwise would have read.
- Whether workflow felt slower, confusing, lower quality.

## Gate To Pass

Product or usage gate:

- Real workflow trials show Haiku Scribe reduces raw context loading pressure in bulk-reading situations without making main Claude workflow feel worse.

Technical security gate:

- subagent contract is unambiguous about allowed behavior, forbidden behavior, evidence expectations, main-model verification responsibility.

## Non-Passage Conditions

Do not open V1 while any of these remain true:

- Users cannot tell when use Haiku Scribe.
- Summaries too generic support focused follow-up reads.
- subagent regularly drifts into conclusions reserved main model.
- Safety boundaries depend on convention alone clear contract.
- agent needs shell, write, web, MCP, recursive-agent, Codegraph access useful base workflow.
- Transcript or log summaries create false confidence, hide material uncertainty, too imprecise targeted main-model verification.

## V1 Handoff Conditions

Only V0 passes, write separate V1 personal packaging spec for:

- `setup`.
- `doctor`.
- `uninstall`.
- Backups.
- Dry-run behavior.
- Safe configuration merge.
- Bounded ownership markers.
- Validation subagent still matches V0 safety contract.
