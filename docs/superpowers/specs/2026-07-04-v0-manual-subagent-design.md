# Haiku Scribe V0 Manual Subagent Design

Date: 2026-07-04
Status: Ready for manual validation
Parent roadmap: `docs/superpowers/specs/2026-07-04-haiku-scribe-roadmap-design.md`
Source PRDs:
- `docs/haiku_scribe_prd.md`
- `docs/haiku_scribe_skill_prd.md`

## Objective

Validate whether a native Claude Code custom subagent named `haiku-scribe`, running on Haiku with read-only file-discovery tools, usefully compresses bulk-reading work before any installer, hook, report, nudge, enforcement, team rollout, plugin, MCP, or enterprise machinery is built.

## V0 Success Definition

V0 passes only if real manual trials show that Haiku Scribe reduces raw context loading pressure in bulk-reading situations without making the main Claude workflow feel worse.

The validation target is workflow usefulness, not packaging quality.

## In Scope

- Manual custom subagent definition named `haiku-scribe`.
- `model: haiku`.
- Read-only repository discovery through `Read`, `Glob`, and `Grep`.
- Explicit delegation rules for the main Claude session.
- Structured summaries that separate facts, evidence, unknowns, risks, and direct follow-up reads.
- Manual trials on realistic bulk-reading tasks.
- Main-model verification before edits, root-cause conclusions, architecture decisions, security conclusions, public summaries, commits, or release decisions.

## Out of Scope

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
- Team or project rollout machinery.
- Claude Code plugin packaging.
- Enterprise-managed controls.
- MCP.
- Codegraph integration in the base agent.
- Shell access for `haiku-scribe`.
- Write or edit access for `haiku-scribe`.
- Web access for `haiku-scribe`.
- Recursive agent calls from `haiku-scribe`.
- External model providers.
- Local model runtimes.
- Anthropic API keys outside the existing Claude Code account.

## Manual Installation Target

For V0 validation in this repository, the manually installable agent lives at:

```text
.claude/agents/haiku-scribe.md
```

The file is committed so the contract can be reviewed and iterated. It is not installed into a user's global Claude Code configuration by this version.

## Subagent Contract

Haiku Scribe is a context-compression worker.

It may:
- Read files requested by the main Claude session.
- Search repository text with exact patterns.
- List files with glob patterns.
- Summarize large files, logs, generated output, transcripts, or multiple related files.
- Extract evidence with file and line references when available.
- Identify unknowns and risks in its own summary.
- Recommend a small number of direct reads for the main Claude session.

It must not:
- Edit files.
- Write files.
- Run shell commands.
- Use web access.
- Use MCP tools.
- Invoke other agents.
- Make final root-cause conclusions.
- Make final architecture decisions.
- Make final security, authentication, authorization, or permission conclusions.
- Produce final PR summaries, commit messages, release notes, or public project outputs.
- Claim facts without evidence when evidence is available.
- Hide uncertainty.

## Delegation Policy For Main Claude

The main Claude session should delegate to `haiku-scribe` before:

- Reading three or more files for orientation.
- Reading one large file mainly to understand its shape.
- Inspecting logs, transcripts, generated bundles, minified JavaScript, or noisy tool output.
- Mapping a flow across multiple files before deciding where to edit.
- Extracting relevant evidence before root-cause analysis.
- Preparing a compact overview of an unfamiliar area.

The main Claude session should read directly instead of delegating when:

- Exact edit context is needed immediately.
- A small file must be inspected before changing it.
- The task requires final reasoning, diagnosis, architecture judgment, or security judgment.
- The user explicitly asks the main Claude session to read exact content.
- The content is likely secret-bearing and should not be read without explicit user intent.

## Required Response Shape

Every `haiku-scribe` response must use this structure:

```markdown
## Summary

Two to six bullets with the compressed answer.

## Evidence

- `path/to/file.ext:line`: Relevant observed fact.

## Unknowns And Risks

- Unknown or risk that affects confidence.

## Suggested Direct Reads

- `path/to/file.ext:line`: Why the main Claude session should inspect this exact location.
```

When no direct read is needed, the final section must say:

```markdown
## Suggested Direct Reads

- None.
```

## Evidence Rules

- Use precise file paths.
- Include line numbers when Claude Code tool output provides them.
- Distinguish observed facts from interpretations.
- Do not invent line numbers.
- If a claim depends on missing context, list it under `Unknowns And Risks`.

## Manual Trial Protocol

Run at least five realistic trials:

1. Multi-file repository orientation.
2. Large single-file summarization.
3. Log or transcript compression.
4. Cross-file flow mapping.
5. Evidence extraction before debugging or design reasoning.

For each trial, record:

- User request.
- Why delegation was or was not appropriate.
- Files or artifact types inspected.
- Whether summary was specific enough for the main Claude session.
- Whether evidence was precise enough to verify.
- Whether direct follow-up reads were focused.
- Whether the main session avoided loading raw context it otherwise would have read.
- Whether the workflow felt slower, confusing, or lower quality.

## Gate To Pass

Product or usage gate:

- Real workflow trials show Haiku Scribe reduces raw context loading pressure in bulk-reading situations without making the main workflow feel worse.

Technical or security gate:

- The subagent contract is unambiguous about allowed behavior, forbidden behavior, evidence expectations, and main-model verification responsibility.

## Non-Passage Conditions

Do not open V1 while any of these remain true:

- Users cannot tell when to use Haiku Scribe.
- Summaries are too generic to support focused follow-up reads.
- The subagent regularly drifts into conclusions reserved for the main model.
- Safety boundaries depend on convention alone rather than a clear contract.
- The agent needs shell, write, web, MCP, recursive-agent, or Codegraph access to be useful for the base workflow.

## V1 Handoff Conditions

Only after V0 passes, write a separate V1 personal packaging spec for:

- `setup`.
- `doctor`.
- `uninstall`.
- Backups.
- Dry-run behavior.
- Safe configuration merge.
- Bounded ownership markers.
- Validation that the subagent still matches this V0 safety contract.
