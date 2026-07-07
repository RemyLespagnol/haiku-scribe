# Haiku Scribe V1.2 Default Hooks Design

Date: 2026-07-06
Status: Draft for review
Parent roadmap: `docs/superpowers/specs/2026-07-04-haiku-scribe-roadmap-design.md`
Previous design: `docs/superpowers/specs/2026-07-06-v1-guidance-routing-design.md`

## Objective

Promote the V1.2 prompt nudge hook from an experimental `prototype-hooks` path into the normal Haiku Scribe personal setup flow.

V1.2 should make broad context-routing nudges useful by default without creating recursive nudges, repeated interruptions, or over-broad trigger matches. The installed `haiku-scribe` agent must remain a bounded read-only context compression worker.

## Scope

In scope:

- Install V1.2 hooks by default during `haiku-scribe setup`.
- Remove V1.2 hooks during normal `haiku-scribe uninstall`.
- Extend `haiku-scribe doctor` to validate the installed hook script and settings entries.
- Keep setup idempotent and preserve existing user-owned Claude Code settings.
- Add anti-self-nudge behavior for `haiku-scribe` subagent runs.
- Limit `PreToolUse` nudges to one follow-up per user prompt.
- Tighten broad prompt trigger markers.
- Keep the `haiku-scribe` agent tools limited to `Read`, `Glob`, and `Grep`.
- Add an explicit exploration budget to the installed agent contract.
- Re-run the benchmark and compare cost, cache, subagent, and read metrics.

Out of scope:

- Hard-blocking direct reads.
- Adding runtime configuration flags for trigger lists or budgets.
- Adding MCP, CodeGraph, Bash, Agent, or edit access to `haiku-scribe`.
- Team or project-wide rollout.
- Claude Code plugin packaging.
- Enterprise-managed controls.

## Product Decision

V1.2 hooks are installed by default by `haiku-scribe setup`.

The experimental `prototype-hooks` command may stay temporarily as a compatibility alias, but it is no longer the primary product path or the documented way to install V1.2. The source code can reuse internal helpers from the prototype as long as normal setup, doctor, and uninstall own the resulting behavior.

## Installation Design

Normal setup installs four managed surfaces:

- `~/.claude/agents/haiku-scribe.md`
- the Haiku Scribe block in `~/.claude/CLAUDE.md`
- Haiku Scribe-owned read deny rules in `~/.claude/settings.json`
- `~/.claude/hooks/haiku-scribe-v1-2-nudge.py`

Setup also merges two hook groups into `~/.claude/settings.json`:

- `UserPromptSubmit` with an empty matcher.
- `PreToolUse` with matcher `Read|Grep`.

The hook command is tracked in Haiku Scribe ownership metadata so uninstall can remove only the hook entries it owns. Existing user hook groups and other settings must remain intact. Setup remains idempotent: running it twice must not duplicate hook groups, deny rules, guidance blocks, or agent files.

## Doctor And Uninstall

`haiku-scribe doctor` validates the normal V1.2 installation:

- agent file exists and matches the expected safe contract;
- guidance block exists;
- owned deny rules are present;
- hook script exists at the managed path;
- `UserPromptSubmit` contains the managed hook command;
- `PreToolUse` contains the managed hook command with matcher `Read|Grep`;
- ownership metadata points to the managed hook command.

`haiku-scribe uninstall` removes:

- the managed agent file;
- the managed guidance block;
- Haiku Scribe-owned deny rules;
- the managed hook entries;
- the managed hook script;
- empty Haiku Scribe ownership metadata created only for these managed resources.

Uninstall must not remove user hooks or unrelated settings.

## Hook Behavior

The hook handles `UserPromptSubmit` and `PreToolUse`.

### Anti-Self-Nudge

The hook returns `0` with no output and no log entry when any of these are true:

- `agent_type == "haiku-scribe"`;
- `is_sidechain == true`;
- `transcript_path` contains `/subagents/`.

This behavior is intentionally silent. The goal is to avoid recursive nudges and extra transcript noise inside the worker agent.

### Prompt Nudge

On `UserPromptSubmit`, the hook lowercases the prompt and checks it against a tightened list of broad-context markers. If no marker matches, it returns silently.

If a marker matches, it appends one JSONL event to `haiku-scribe-nudges.jsonl` with:

- timestamp;
- `decision: "nudge"`;
- reason;
- matched markers;
- session id;
- prompt id;
- cwd.

It then emits `additionalContext` telling the main session to consider `haiku-scribe` before raw repository reads or searches.

### Pre-Tool Follow-Up

On `PreToolUse`, the hook only considers `Read` and `Grep`. `Bash` is no longer part of the matcher or message.

For the same `session_id` and `prompt_id`, the hook emits `PRE_TOOL_NUDGE` only if:

- a prior `decision: "nudge"` event exists; and
- no prior `decision: "pre_tool_followup"` event exists.

After emitting the follow-up, it appends `decision: "pre_tool_followup"` to the JSONL log. Later `Read` or `Grep` calls for the same prompt return silently.

The JSONL log is both audit trail and de-duplication memory.

## Trigger Design

Remove broad ambiguous markers:

- `log`
- `repo`
- `flow`
- `map`
- `summarize`
- `unfamiliar`

Keep or add markers that more clearly indicate broad context gathering:

- `architecture`
- `audit`
- `large file`
- `mapping`
- `transcript`
- `scan the repo`
- `explore the repo`
- `map the flow`
- `data flow`
- `plusieurs fichiers`
- `cartographie`

The trigger list should prefer false negatives over false positives. The hook should nudge when the prompt clearly asks for repository exploration, flow mapping, architecture review, large artifact compression, or multi-file context gathering. It should stay silent for small edits, exact-file requests, and ordinary words that can appear in focused work.

## Agent Contract

The installed agent frontmatter remains:

```yaml
name: haiku-scribe
model: haiku
tools: Read, Glob, Grep
```

The contract must explicitly continue to forbid:

- editing files;
- writing files;
- running shell commands;
- browsing the web;
- using MCP tools;
- invoking other agents;
- making final root-cause conclusions;
- making final architecture decisions;
- making final security, authentication, authorization, or permission conclusions;
- producing final PR summaries, commit messages, release notes, or public project outputs.

The `How To Read` section adds an exploration budget:

- keep the response short;
- use `Glob` and `Grep` to localize before reading;
- target about 12 file reads;
- stop around 15 file reads unless the main session explicitly named the files to inspect;
- do not run open-ended exploration loops;
- stop once the brief has enough evidence, unknowns, and suggested direct reads.

This budget is guidance for the agent, not a hard runtime enforcement mechanism.

## Data Flow

1. User submits a prompt.
2. `UserPromptSubmit` hook classifies the prompt.
3. If broad and not a subagent run, the hook writes a `nudge` event and injects context.
4. Main Claude may call `haiku-scribe` before raw reads.
5. If main Claude instead uses direct `Read` or `Grep`, `PreToolUse` checks the log.
6. If this is the first direct read/search for the prompt, the hook injects one follow-up and writes `pre_tool_followup`.
7. Future direct reads/searches for the same prompt stay silent.
8. `haiku-scribe` itself is ignored by the hook.

## Error Handling

Hook failures should not block Claude Code usage. Malformed JSONL lines are skipped. Missing nudge log means no `PreToolUse` follow-up. The hook returns `0` for unsupported events and unsupported tools.

Setup and doctor should fail clearly on malformed settings shapes that prevent safe hook merging. Uninstall should remove managed files and entries when it can do so safely, while preserving unrelated user content.

## Testing

Automated tests should cover:

- setup installs V1.2 hooks by default;
- setup remains idempotent;
- doctor succeeds for a complete V1.2 install;
- doctor fails when the hook script is missing;
- doctor fails when hook entries are missing or have the wrong matcher;
- uninstall removes only managed hook entries and the managed hook script;
- hook ignores `agent_type == "haiku-scribe"` silently;
- hook ignores `is_sidechain == true` silently;
- hook ignores transcript paths containing `/subagents/` silently;
- `PreToolUse` emits only one follow-up per `session_id` and `prompt_id`;
- `Bash` does not trigger `PreToolUse`;
- removed markers do not match by themselves;
- specific markers such as `scan the repo`, `explore the repo`, `map the flow`, `data flow`, `plusieurs fichiers`, and `cartographie` do match;
- installed agent frontmatter remains `tools: Read, Glob, Grep`;
- installed agent contract mentions the exploration budget.

Existing setup, doctor, uninstall, settings merge, backup, and CLI tests must continue to pass.

## Benchmark

After implementation, re-run the same benchmark used for the previous V1.2 evaluation with hooks installed through normal setup.

Record:

- first `cache_creation_input_tokens`;
- total `cache_creation_input_tokens`;
- total `cache_read_input_tokens`;
- number of subagent messages;
- number of direct reads;
- final cost;
- whether `PreToolUse` nudged only once;
- whether `haiku-scribe` avoided self-nudging;
- whether the `haiku-scribe` response stayed short and within the intended exploration budget.

The benchmark result should be written under `docs/superpowers/evaluations/` and compared against the prior run.

## Acceptance Criteria

V1.2 is complete when:

- `haiku-scribe setup` installs the agent, guidance, deny rules, and V1.2 hooks by default;
- `haiku-scribe doctor` validates the V1.2 hooks as part of the normal installation;
- `haiku-scribe uninstall` removes the V1.2 hook artifacts without removing user-owned hooks;
- the hook does not nudge `haiku-scribe` itself;
- `PreToolUse` nudges at most once per user prompt;
- triggers are narrower and tested;
- the agent contract remains read-only and includes the exploration budget;
- the automated test suite passes;
- the V1.2 benchmark has been re-run and documented.

## Risks

Static and hook-injected guidance can still be ignored by the main model. V1.2 is a nudge system, not enforcement.

Tighter triggers will miss some broad prompts. This is acceptable for V1.2 because repeated false positives would train users and agents to ignore the hook.

The JSONL log is simple local state. It is adequate for prompt-level de-duplication, but it is not a durable analytics database.

Keeping `prototype-hooks` as a compatibility alias may create documentation confusion. Public docs should point to normal `setup`; the alias should be treated as temporary.
