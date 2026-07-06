# Haiku Scribe V1 Guidance Routing Design

Date: 2026-07-06
Status: Approved for planning
Parent roadmap: `docs/superpowers/specs/2026-07-04-haiku-scribe-roadmap-design.md`

## Objective

Make the installed `CLAUDE.md` guidance more effective at causing the main Claude session to invoke `haiku-scribe` before broad code exploration.

The observed failure mode is that the current guidance says to "use" Haiku Scribe in bulk-reading cases, but an agent can treat that as optional and inspect files directly first. The revised guidance must express Haiku Scribe as a mandatory pre-exploration routing step for defined triggers.

## Scope

In scope:
- Update the guidance block rendered by `haiku-scribe setup`.
- Keep the change inside the existing owned `<!-- HAIKU_SCRIBE_START -->` / `<!-- HAIKU_SCRIBE_END -->` block.
- Preserve the installed subagent's read-only contract.
- Preserve setup idempotency, backups, doctor behavior, uninstall ownership, and settings merge behavior.
- Add tests that prove the stronger guidance is installed and remains bounded.

Out of scope:
- Hooks.
- Audit events or reports.
- Prompt nudges beyond static `CLAUDE.md` guidance.
- Soft enforcement.
- Blocking direct reads.
- Changes to the `haiku-scribe` subagent tools, model, or authority.
- Team or project rollout.
- CodeGraph or MCP access inside the base agent.

## Design

The product should keep V1 boring: setup writes a static guidance block to the user's Claude guidance file. The improvement is copy and structure, not runtime machinery.

The new block should use imperative routing language:
- "Before reading 3+ files, call `haiku-scribe` first."
- "Do not read files yourself first and then decide whether Haiku Scribe was needed."
- "Use Haiku Scribe for evidence gathering; main Claude keeps final judgment."

The block should be organized into these sections:
- Mandatory routing.
- Triggers.
- Workflow.
- What Haiku Scribe may and may not do.
- Red flags.
- Fallback if unavailable.

This shape mirrors the successful pattern from process skills: explicit `BEFORE` language, recognizable triggers, sequencing, and anti-rationalization red flags.

## Delegation Boundary

The revised guidance must not weaken the core safety model.

Haiku Scribe remains appropriate for:
- bulk file orientation;
- large-file structure summaries;
- log, transcript, bundle, or generated-output compression;
- cross-file flow mapping;
- evidence extraction before reasoning.

Haiku Scribe remains inappropriate for:
- final root-cause conclusions;
- final architecture decisions;
- final security, authentication, authorization, or permission conclusions;
- precise edits;
- commits;
- public PR summaries or release notes.

The important clarification is that these exclusions apply to final judgment, not to pre-analysis. For example, if a debugging task will eventually need root-cause analysis, Haiku Scribe may still gather evidence first. The main Claude session must then verify relevant evidence directly before deciding or editing.

## Expected Installed Guidance Shape

The exact copy may be refined during implementation, but it should preserve this behavior:

```md
## Cost-aware Scribe routing

Before broad code exploration, call `haiku-scribe` first.

Mandatory triggers:
- You are about to read 3+ files.
- You are about to read a file likely over 400 lines mainly for orientation.
- You need to map a flow across files.
- You need to summarize logs, transcripts, generated bundles, large docs, or noisy tool output.
- You need evidence before debugging, review, architecture, or scope reasoning.
- The user asks to review, analyze, explore, understand, audit, map, or find code across an unfamiliar area.

Workflow:
1. Haiku Scribe gathers compact evidence.
2. Main Claude performs focused direct reads on the highest-value locations.
3. Main Claude makes final decisions, edits, commits, and user-facing conclusions.

Do not read files yourself first and then decide whether Haiku Scribe was needed.
```

## Testing

Tests should assert:
- `render_guidance_block()` contains mandatory `BEFORE` or equivalent pre-exploration language.
- The rendered guidance includes the 3+ files trigger.
- The rendered guidance includes the "do not read files yourself first" rule.
- The rendered guidance clarifies evidence gathering versus final judgment.
- Existing setup tests still pass without changing file ownership boundaries.
- Existing doctor and uninstall tests still pass.

## Acceptance Criteria

This change is done when:
- `haiku-scribe setup` installs stronger guidance into the owned block.
- Existing user guidance outside the owned block is preserved.
- Re-running setup remains idempotent.
- Uninstall still removes only Haiku Scribe-owned configuration.
- Doctor still validates the installation.
- Tests cover the stronger guidance contract.

## Non-Goals And Risks

This design intentionally does not solve every missed invocation. Static guidance can still be ignored by an agent. That is acceptable for V1 because the roadmap reserves audit, nudges, and enforcement for later phases after the baseline is stable.

The main risk is over-broad wording that causes Haiku Scribe to be invoked for tiny obvious edits. The trigger language should stay tied to bulk reading, large artifacts, flow mapping, and evidence gathering.
