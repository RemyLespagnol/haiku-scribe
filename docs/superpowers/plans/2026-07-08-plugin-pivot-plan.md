# Plan: Pivot to a Claude Code plugin, shed the enforcement stack

Date: 2026-07-08
Status: proposed (supersedes the V1.2 → V1.3 → V2 sequence)

## Why (the strategic conclusion)

haiku-scribe is the **only** design in its inspiration set (`scribe-mcp`,
`triss-coworker`, `lmsgo`, `claude-coworker-model`) that runs under a
subscription seat with **no API key**. All four inspirations reach their cheap
worker through an external/local endpoint (DeepSeek / Kimi / MiniMax / LM
Studio) — *free* tokens off the Claude bill. That door is closed to us.

The two subscription-safe ways to run Haiku with no API key are **not** equal:

- `claude -p --model haiku` — enables explicit tool/CLI delegation like the
  inspirations, **but** it bills through a Pro/Max side door Anthropic can
  meter or close at any time. Fragile foundation.
- **Native Haiku subagent (Task tool)** — first-class, sanctioned, bills the
  seat by design, works identically on Pro/Max/Enterprise, no API key, no
  `claude -p`. This is what haiku-scribe already uses.

There is **no** way for an out-of-process MCP server to spawn a *native*
subagent. So "explicit delegation" forces the fragile path and "durable
delegation" forces the native subagent. Implicit-but-sanctioned beats
explicit-but-fragile. **The core mechanism is correct and stays.** The
over-build was never the core — the machinery grew up to *prove* and *enforce*
implicit delegation. We now accept the bet on structural grounds, so the
machinery is cut.

### KPI

Optimize for **both**:

1. **Main-context headroom** — the primary felt win, on every tier. Measured in
   context tokens saved, not dollars.
2. **Seat-usage / cap-stretch** — on Pro/Max the weekly cap is real, and
   offloading broad reads to Haiku (weighted far below Opus) stretches it.

The dollar-only break-even framing and the "double-read sign-flip" are
retired: on a flat seat there is no per-token dollar cost to the user, and on a
cap the relevant question is cap conservation, not dollars.

**Load-bearing caveat:** both KPIs only hold if the main model does **not**
re-read the source after delegating. A double-read spends Haiku cap *plus* Opus
cap — strictly worse than reading directly in Opus. The output contract exists
to prevent this; it is the make-or-break of the whole design.

## What the plugin ships (three surfaces, down from four)

Constraint discovered during planning: a Claude Code **plugin cannot ship a
CLAUDE.md guidance block, cannot ship permission `deny` rules**, and its
`settings.json` supports only `agent` / `subagentStatusLine`. It *can* ship a
subagent (with `model`/`tools`), and hooks via `hooks/hooks.json`. The design
below routes every surface through what a plugin can actually deliver.

1. **The subagent** — static `agents/haiku-scribe.md`, `model: haiku`,
   `tools: Read, Glob, Grep`. This is the **always-on carrier**. A plugin has
   exactly **two durable main-model carriers**, and everything load-bearing
   must ride them:
   - **Frontmatter `description` = the routing carrier.** Claude selects a
     subagent by reading its `description`, not its body; the body only
     configures the agent *after* it's picked. So the *when-to-delegate* trigger
     ("delegate when you want an answer/extract you won't need the raw source
     for"; broad-context markers: logs, transcripts, surveys, 4+ files) lives in
     `description`, not in the body. This is the single most important field in
     the plugin — treat it as the star, not a detail. It also enables explicit
     `@haiku-scribe` invocation as a manual fallback.
   - **The returned coverage statement = the don't-re-read carrier.** "Don't
     re-read after delegating" is a *main-model* instruction, and the agent body
     can't reach the main model at all. The one per-invocation surface that
     does is the scout's own output. So the coverage statement ("read A, B
     fully / skimmed C / D not relevant") is not just documentation — it is the
     enforcement lever, landing in the main model's context on every call and
     telling it the extract is complete. Size the output contract (exact
     `path:line`, verbatim *decision-bearing* snippets) so that statement is
     credible and the main model provably never needs to re-read what was
     covered.
   - **Soft read-restraint** replacing the deleted deny rules: read-only, never
     open `.env` / credential / secret files; note them as skipped in coverage.

2. **Optional CLAUDE.md snippet** — documented in the README, the same routing
   guidance for power users who want the reflex in their global instructions.
   Reinforcement only — a **booster, not a carrier**. The two carriers in
   surface #1 (the `description` and the returned coverage statement) already
   ship the load-bearing copy to everyone; the snippet only sharpens the reflex
   for power users. Don't oversell it and don't depend on it.

3. **Once-ever onboarding nudge** — `hooks/hooks.json` fires on the **literal
   first user prompt** after install, injects one dismissible "a Haiku scout is
   available" note, writes a marker (`~/.claude/.haiku-scribe-onboarded`), and
   never fires again. **No breadth detection** (no file-count/size/keyword
   classifier — that was the wrong proxy), no PreToolUse follow-up, no JSONL.
   Purpose is human discovery, not model policing.

### Substitutability verdict

The **main model decides upfront** via the routing trigger; the scout just
extracts and reports coverage, it does not return a verdict. Accepted residual:
on rare dense/interdependent source the main model will occasionally delegate
something that can't compress and then re-read. The broad-context trigger
(logs, transcripts, surveys, 4+ files) steers away from that minority case.

## What gets deleted

The pivot dissolves the "generated content as string literals" architecture —
a plugin renders nothing, so every artifact becomes a **static file**. Delete:

- The entire `src/haiku_scribe/` Python package — installer, `doctor`,
  ownership tracking, backups, `contracts.py` generators, `v1_2_hooks.py`,
  `cli.py`. The agent `.md`, hook script, and snippet are hand-authored static
  files, not generated.
- `DEFAULT_DENY_RULES` — a plugin can't ship deny rules; replaced by the soft
  read-restraint clause in the agent description. Read-only tools + no network
  = no exfiltration path. Residual risk: a secret could surface in an extract
  you explicitly asked for.
- V1.2 `PreToolUse` follow-up hooks and JSONL logging
  (`haiku-scribe-nudges.jsonl`), `gain`, `replay`.
- `bench/` as a *shipped* product.

Keep git history — this is subtraction, not a rewrite.

### Private dev-only tools (never shipped)

- The **JSONL double-read probe** — kept locally, run on your own sessions to
  watch the double-read rate across contract edits. Instrument yourself, not
  users.
- The **headroom benchmark** — run once against the sharpened contract to
  capture the context-saved delta; that number goes in the README. Kept in
  `bench/` as a private throwaway.

## Execution steps

1. **Write the static agent contract** — `agents/haiku-scribe.md` with the
   substitutable output contract, routing guidance, and read-restraint clause.
   Add `plugin.json`. One runnable assert-style check that the contract text
   contains its required clauses. *(Highest-leverage change; prerequisite for
   everything else — do it first.)*
2. **Add the onboarding nudge** — `hooks/hooks.json` + a marker-gated script
   that fires once on the first post-install prompt.
3. **README** — install via `/plugin`; the `@haiku-scribe` manual-invocation
   fallback for forcing the scout when auto-routing doesn't fire; the optional
   guidance snippet; the KPI (headroom + Pro/Max cap-stretch); the
   Enterprise-no-API-key moat stated explicitly; the fresh headroom number from
   the private benchmark.
4. **Cut over and subtract** — uninstall your own old Python install, Slack the
   handful of colleagues (no migration tooling shipped — bet is nobody else is
   on the old version), then delete `src/`. Keep `bench/` private.

## Migration

None shipped. haiku-scribe is effectively personal; the plugin won't clean up
old Python-written artifacts, so you run the old `uninstall` on your own
machine before deleting the code and message colleagues directly.

## Resolved planning questions

- Plugin format confirmed: subagent with `model: haiku` ✅, `hooks.json` ✅,
  clean `/plugin install|uninstall` ✅; **no** CLAUDE.md block, **no** deny
  rules, `settings.json` limited to `agent`/`subagentStatusLine`.
- Guidance block → agent `description` frontmatter (routing carrier, ships) +
  returned coverage statement (don't-re-read carrier) + optional snippet
  (booster only). `@haiku-scribe` documented as manual fallback.
- Deny rules → dropped, replaced by soft read-restraint.
- Nudge → once-ever, literal-first-prompt, marker-gated, human-facing.
- Measurement → two private dev tools; nothing user-facing logs.
