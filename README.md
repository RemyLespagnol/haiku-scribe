<p align="center">
  <img src="./assets/logo.png" alt="Haiku Scribe logo">
</p>

# haiku-scribe

[![CI](https://github.com/RemyLespagnol/haiku-scribe/actions/workflows/ci.yml/badge.svg)](https://github.com/RemyLespagnol/haiku-scribe/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

A Claude Code **plugin** that installs one thing: `haiku-scribe`, a read-only,
Haiku-powered subagent that compresses broad context — repository surveys, logs,
transcripts, generated output, flow mapping across unfamiliar code — into a
compact, evidence-backed brief. The main model reasons over the brief instead of
loading the raw source itself.

## Why

- **Main-context headroom** — the primary win, on every tier. The scout reads the
  bulky raw source; your main context keeps only the compressed extract.
- **Pro/Max cap-stretch** — Haiku is weighted far below Opus, so offloading broad
  reads to the scout conserves the weekly cap.
- **Subscription-seat, no API key** — it runs as a native Task-tool subagent,
  billed to your seat by design. Works identically on Pro, Max, and Enterprise,
  where no-API-key is often mandatory. No `claude -p` side door, no external
  endpoint.

**One caveat that makes or breaks it:** don't re-read the source after the scout
returns. The scout states its coverage explicitly ("read A, B fully / skimmed C /
D not relevant / extraction complete"); when coverage is complete, use the extract
as-is. Delegating and then re-reading spends Haiku *and* Opus — strictly worse
than reading directly.

## Install

```
/plugin marketplace add https://github.com/RemyLespagnol/haiku-scribe.git
/plugin install haiku-scribe
```

Update: re-run `/plugin install haiku-scribe`. Remove: `/plugin uninstall haiku-scribe`.

## Use

The scout **auto-routes**: the main model delegates to it when a request means
broad reading (4+ files, directory/repo surveys, large files, logs, transcripts,
generated output, unfamiliar-flow mapping). To **force** it, invoke it manually:

```
@haiku-scribe survey the auth flow across src/ and list every entrypoint
```

Skip it for small focused reads (≤3 known files) and when you need exact
line-level detail immediately — read those directly.

## Optional: sharpen the reflex (power users)

The agent's own `description` already auto-routes this, so the block below is a
**booster, not a requirement** — it just makes the reflex stickier in your global
instructions. Copy it into `~/.claude/CLAUDE.md`:

```markdown
<!-- HAIKU_SCRIBE_START -->
## Cost-aware Context Routing

Classify remaining work before loading raw context.

Read directly when it's small: 3 or fewer small files, no directory reads, no
broad search, no logs or generated output, no flow mapping.

Delegate to `haiku-scribe` when it's broad: 4+ files, large files, directory or
repository surveys, logs, transcripts, generated output, flow or pattern mapping,
unfamiliar-area exploration.

Prefer `haiku-scribe` over the built-in Explore agent for bulk digestion. When it
reports complete coverage, trust the extract — don't re-read what it covered. Skip
it for exact line-level detail you need now. If it's unavailable, say so and
continue manually.
<!-- HAIKU_SCRIBE_END -->
```

## Safety

Read-only tools (`Read, Glob, Grep`), no network, no shell. The agent also
refuses to open `.env`, credential, secret, and key files. Residual risk: a
secret could surface in an extract you explicitly asked for.

## Development

`docs/superpowers/` is a private development workspace — not part of the shipped
plugin (Claude Code loads only `agents/` and `hooks/`). Run the contract test with
`python3 test_contract.py`.
