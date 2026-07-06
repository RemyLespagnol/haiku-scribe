# Haiku Scribe V1 Guidance Routing Design

Date: 2026-07-06
Status: Implemented, revised after local trials
Parent roadmap: `docs/superpowers/specs/2026-07-04-haiku-scribe-roadmap-design.md`

## Objective

Make the installed `CLAUDE.md` guidance and `haiku-scribe` agent listing more effective at causing the main Claude session to invoke `haiku-scribe` before broad raw-context gathering.

The observed failure mode is that guidance which says to "use" Haiku Scribe in bulk-reading cases can still be treated as optional. Local trials also showed that tool-specific wording such as `CodeGraph` versus `Read/Grep` creates priority conflicts. The revised guidance should classify the remaining work by shape, not by tool brand.

## Scope

In scope:
- Update the guidance block rendered by `haiku-scribe setup`.
- Update the short `haiku-scribe` agent description rendered by setup, because that description appears in the agent listing when Claude chooses subagents.
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

The product should keep V1 boring: setup writes a static guidance block to the user's Claude guidance file and a stronger short description to the `haiku-scribe` agent frontmatter. The improvement is copy and structure, not runtime machinery.

The new block should use tool-agnostic routing language:
- classify remaining work before loading raw repository context;
- allow compact discovery tools first when they return metadata, symbols, call paths, or file candidates instead of raw file contents;
- allow direct main-session reads only for a small focused read;
- route broad context gathering to `haiku-scribe`;
- keep final judgment, edits, commits, and user-facing conclusions in the main session.

The block should be organized into these sections:
- Context routing.
- Small focused read criteria.
- Broad context gathering criteria.
- Workflow.
- What Haiku Scribe may and may not do.
- Fallback if unavailable.

This shape avoids tool-specific precedence arguments. `CodeGraph`, Token Optimizer checkpoints, project memory, grep, or future discovery tools are all just compact discovery if they do not load broad raw repository context.

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
## Cost-aware Context Routing

Before loading raw repository context, classify the remaining work.

Compact discovery tools may be used first if they return metadata, symbols, call paths, or file candidates instead of raw file contents.

Use the main session directly only when the remaining work is a small focused read:
- 3 or fewer small files;
- no directory reads;
- no shell search over many files;
- no logs, bundles, generated output, transcripts, or large docs;
- no architecture, flow, or cross-layer mapping.

Use `haiku-scribe` when the remaining work is broad context gathering:
- 4+ files;
- large files;
- directory or repository survey;
- logs, bundles, generated output, transcripts, or large docs;
- architecture review, flow mapping, pattern audit, unfamiliar-area exploration;
- evidence extraction before broad reasoning.

Workflow:
1. Use compact discovery if available.
2. Classify the remaining work as small focused read or broad context gathering.
3. If small, main session reads directly.
4. If broad, call `haiku-scribe` before raw Read, Grep, or shell exploration.
5. Main Claude performs focused direct reads on the highest-value locations.
6. Main Claude makes final decisions, edits, commits, and user-facing conclusions.
```

The agent frontmatter description should carry the same compact boundary because the agent listing is a high-salience decision point:

```md
Use when remaining work is broad context gathering: 4+ files, large files, directory/repo survey, logs, generated output, transcripts, architecture review, flow mapping, pattern audit, unfamiliar-area exploration, or evidence extraction before broad reasoning. Skip for small focused reads: 3 or fewer small files with no directory reads, shell search, logs, generated output, or cross-layer mapping.
```

## Testing

Tests should assert:
- `render_guidance_block()` contains context classification language.
- The rendered guidance defines small focused reads.
- The rendered guidance defines broad context gathering.
- The rendered guidance clarifies evidence gathering versus final judgment.
- `render_agent_markdown()` carries the broad-versus-small routing boundary in its frontmatter description.
- Existing setup tests still pass without changing file ownership boundaries.
- Existing doctor and uninstall tests still pass.

## Acceptance Criteria

This change is done when:
- `haiku-scribe setup` installs stronger guidance into the owned block.
- `haiku-scribe setup` installs the stronger agent description.
- Existing user guidance outside the owned block is preserved.
- Re-running setup remains idempotent.
- Uninstall still removes only Haiku Scribe-owned configuration.
- Doctor still validates the installation.
- Tests cover the stronger guidance contract.

## Non-Goals And Risks

This design intentionally does not solve every missed invocation. Static guidance can still be ignored by an agent. Local trials confirmed this limit: even when global guidance loaded and the agent listing included stronger copy, Claude still sometimes used compact discovery, then crossed into broad raw reads without calling `haiku-scribe`.

The main risk is over-broad wording that causes Haiku Scribe to be invoked for tiny obvious edits. The routing language should stay tied to bulk reading, large artifacts, directory surveys, flow mapping, pattern audits, and evidence gathering.

## V1.1 Decision Note

The original roadmap placed full audit-only instrumentation in v1.1 before prompt nudges. The local trials already produced enough evidence to justify a smaller next step:

- global guidance stacks correctly;
- the agent listing description is visible;
- Token Optimizer checkpoints can bypass routing, but they are not the only cause;
- repeated failures follow the same pattern: broad task, compact discovery, then raw direct reads without `haiku-scribe`.

Therefore, defer the full v1.1 audit/report product. The next useful phase should be a v1.2-lite prompt nudge with micro-audit:

- detect likely broad context gathering after compact discovery;
- nudge before or immediately after raw reads/searches cross the broad threshold;
- log only minimal local events needed to measure false positives and spam;
- avoid blocking behavior.
