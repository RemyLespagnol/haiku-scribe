# Design: haiku-scribe as a Claude Code plugin

Date: 2026-07-09
Status: approved (implements `docs/superpowers/plans/2026-07-08-plugin-pivot-plan.md`)

## Goal

Replace the Python CLI installer with a native Claude Code **plugin**. The
product stops being a program that generates config and becomes the config
itself: static files a user installs via `/plugin`. The core mechanism — an
always-on, read-only, Haiku-powered context-compression subagent invoked
implicitly via the native Task tool — is correct and stays. Everything built to
*prove and enforce* implicit delegation (installer, ownership tracking, backups,
`doctor`, deny rules, V1.2 nudge hooks, JSONL logging, `gain`/`replay`) is cut.

See the pivot plan for the full strategic argument (subscription-seat / no-API-key
moat, the KPI reframe, the double-read caveat). This spec covers only the
concrete implementation shape.

## KPI (from the plan, restated for scope)

Optimize for both **main-context headroom** (context tokens saved, every tier)
and **seat-usage / cap-stretch** (Pro/Max weekly cap conservation by offloading
broad reads to Haiku). Load-bearing caveat: both hold only if the main model does
**not** re-read the source after delegating. The output contract exists to
prevent that double-read; it is the make-or-break of the design.

## Repo disposition

**This repo becomes the plugin.** Plugin files live at the repo root. `src/` is
deleted. `bench/` and `docs/` remain in the repo but are **not loaded** by Claude
Code (it reads only `agents/`, `hooks/`, `commands/`, `skills/`) — they sit in the
cloned plugin directory as harmless, unshipped clutter. No subdirectory, no second
repo. git history is kept — this is subtraction, not a rewrite.

## File layout

```
.claude-plugin/
  plugin.json         # plugin manifest
  marketplace.json    # single-entry marketplace so `/plugin marketplace add <git-url>`
                      #   then `/plugin install haiku-scribe` works from this one repo
agents/
  haiku-scribe.md     # static; the current render_agent_markdown() output, frozen
hooks/
  hooks.json          # UserPromptSubmit; inline shell; marker-gated once-ever nudge
README.md             # install, KPI, @haiku-scribe fallback, optional snippet, headroom number
test_contract.py      # the one runnable check
bench/  docs/          # remain in repo, unloaded, private (not shipped as product)
```

The exact field names / schema of `plugin.json` and `marketplace.json` are pinned
against current Claude Code plugin docs at implementation time (writing-plans
step), not guessed here. A single repo acting as both marketplace and the plugin
it lists is a supported pattern: `marketplace.json` references one plugin whose
source is the repo root (where `plugin.json` lives).

## Surface 1 — the subagent (the always-on carrier)

`agents/haiku-scribe.md` is the current `render_agent_markdown()` output
(`src/haiku_scribe/contracts.py`) **frozen as a static file**, with one added
clause. It already carries both load-bearing carriers the plan names:

- **Frontmatter `description` = the routing carrier.** Claude selects a subagent
  by reading its `description`, so the when-to-delegate trigger lives there:
  *"Use proactively before broad exploration: 4+ files, directory/repository
  surveys, large files, logs, transcripts, generated output, or flow mapping in
  unfamiliar code. Skip for ≤3 known files and when exact line-level detail is
  needed immediately."* This is the single most important field. It also enables
  explicit `@haiku-scribe` invocation. **Unchanged from current.**
- **Body: Response Shape + Structured Extraction + explicit coverage statement =
  the don't-re-read carrier.** The returned coverage statement ("read A, B fully /
  skimmed C / D not relevant; extraction complete") lands in the main model's
  context on every call and tells it the extract is complete — the enforcement
  lever that replaces deleted CLAUDE.md guidance. Output contract sizing (exact
  `path:line`, verbatim decision-bearing snippets, "never present a sample as a
  total count") is already present. **Unchanged from current.**
- **Read-restraint replacing the deleted deny rules.** The body already stops on
  secret-bearing / credential-like content. Add one explicit line to the
  Boundaries / How-To-Read section: *never open `.env`, credential, or secret
  files; note any skipped as skipped in the coverage statement.* Read-only tools
  (`Read, Glob, Grep`) + no network = no exfiltration path; residual risk is a
  secret surfacing in an extract the user explicitly asked for.

Net change to the frozen file: **freeze the existing string + one read-restraint
clause.** Not a rewrite.

`tools: Read, Glob, Grep`, `model: haiku` — unchanged.

## Surface 2 — the once-ever onboarding nudge (simple version)

`hooks/hooks.json` registers a single `UserPromptSubmit` hook whose stdout Claude
Code injects as additional context. Inline shell, **no separate script file**:

```
test -f ~/.claude/.haiku-scribe-onboarded || { printf '<one line: a read-only Haiku scout is installed — it auto-routes for broad reads, or invoke @haiku-scribe manually>'; touch ~/.claude/.haiku-scribe-onboarded; }
```

The marker file gates it to fire **exactly once, ever**, on the first user prompt
after install. Purpose is human discovery, not model policing. **No** breadth
detection (no file-count/size/keyword classifier), **no** PreToolUse follow-up,
**no** JSONL logging. If discovery later proves inadequate the nudge can grow; it
starts minimal.

## Surface 3 — README

Documents:
- Install: `/plugin marketplace add <git-url>` then `/plugin install haiku-scribe`.
- `@haiku-scribe` as the manual-invocation fallback when auto-routing doesn't fire.
- The optional CLAUDE.md snippet — the current `render_guidance_block()` output
  verbatim — for power users who want the routing reflex in their global
  instructions. **Booster, not a carrier**: the two carriers in Surface 1 already
  ship the load-bearing copy to everyone. Don't oversell it, don't depend on it.
- The KPI: main-context headroom + Pro/Max cap-stretch.
- The Enterprise / no-API-key moat, stated explicitly.
- The fresh headroom number from a private `bench/` run against the frozen contract.

## What gets deleted

- The entire `src/haiku_scribe/` package: `cli.py`, `setup.py`, `doctor.py`,
  `contracts.py`, `v1_2_hooks.py`, `gain.py`, `uninstall.py`, `backups.py`,
  `settings.py`, `paths.py`, `markdown_blocks.py`, `__main__.py`, `__init__.py`,
  and `src/haiku_scribe.egg-info/`.
- The CLI test suite (`tests/`) — replaced by `test_contract.py`.
- `DEFAULT_DENY_RULES` — a plugin can't ship deny rules; replaced by the
  read-restraint clause in Surface 1.
- V1.2 `PreToolUse` follow-up hooks, `haiku-scribe-nudges.jsonl` logging, `gain`,
  `replay`, and the `setup --hooks` machinery.
- `bench/` as a *shipped* product (the directory stays in-repo, private).

Before deleting `contracts.py`, copy its `render_agent_markdown()` and
`render_guidance_block()` strings out to `agents/haiku-scribe.md` and the README
snippet respectively. That is the only content that must survive the deletion.

### Private dev-only tools (kept, never shipped)

- **JSONL double-read probe** — kept locally, run on your own sessions to watch
  the double-read rate across contract edits. Instrument yourself, not users.
- **Headroom benchmark** — `bench/` run once against the frozen contract to
  capture the context-saved delta for the README. Private throwaway.

## Testing

The product is a static file, so the check is "the file still says what it must."
One runnable assert-style check, `test_contract.py`, asserting
`agents/haiku-scribe.md` contains its required clauses:
- frontmatter `tools: Read, Glob, Grep` and `model: haiku`;
- the coverage-statement language (the don't-re-read carrier);
- the read-restraint line (the deny-rule replacement);
- the routing trigger phrasing in `description`.

No frameworks beyond the existing pytest. If any required clause is edited out of
the static file, this test fails.

## Migration

None shipped. haiku-scribe is effectively personal. The plugin will not clean up
old Python-written artifacts under `~/.claude`, so: run the old `uninstall` on
your own machine before deleting `src/`, then message the handful of colleagues
directly. The bet is nobody else is on the old version, so no migration tooling.

## Execution order (for the plan step)

1. **Write the static agent contract** — `agents/haiku-scribe.md` (frozen output +
   read-restraint clause) and `.claude-plugin/plugin.json`. `test_contract.py`
   asserting the required clauses. Highest-leverage; prerequisite for everything.
2. **Add `.claude-plugin/marketplace.json`** so the repo is installable.
3. **Add the once-ever nudge** — `hooks/hooks.json` inline marker-gated shell.
4. **Write the README** — install, `@haiku-scribe` fallback, optional snippet, KPI,
   moat, headroom number.
5. **Cut over and subtract** — run old `uninstall` locally, Slack colleagues, then
   delete `src/` and its tests. Keep `bench/` private.

## Open items deferred to implementation (not design unknowns)

- Exact `plugin.json` / `marketplace.json` field names and schema.
- The precise one-line nudge copy.
- The headroom number (produced by the private bench run).
