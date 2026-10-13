<p align="center">
  <img src="./assets/logo.png" alt="Haiku Scribe logo">
</p>

# haiku-scribe

> _Offload broad reading to a cheap Haiku scout — keep your main model's context for thinking._

[![CI](https://github.com/RemyLespagnol/haiku-scribe/actions/workflows/ci.yml/badge.svg)](https://github.com/RemyLespagnol/haiku-scribe/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

<p align="center">
  <img src="./assets/demo.gif" alt="haiku-scribe auto-routing a survey to the Haiku scout" width="700">
</p>

A Claude Code **plugin** that installs one thing: `haiku-scribe`, a read-only,
Haiku-powered subagent that compresses broad context — repository surveys, logs,
transcripts, generated output, flow mapping across unfamiliar code — into a
compact, evidence-backed brief. The main model reasons over the brief instead of
loading the raw source itself.

## Results

| | without the plugin | with haiku-scribe |
|---|---|---|
| Broad prompts handed to the scout | 0 / 36 | **34 / 36** |
| One-file tasks wrongly delegated | 0 / 24 | **0 / 24** |
| Raw tool output in the main context (broad prompts) | baseline | **−33% to −90%** on 11 of 12 |
| Cost on the broadest reads | baseline | **−17% to −49%** |
| Correct answers | 60 / 60 | **60 / 60** |

Raw tool output loaded into the main context, in characters:

```
Sonnet · architecture overview of the `email` package   cost −49%
  without  ██████████████████████████████  53.8k
  with     ███                              5.6k  −90%

Opus · trace `python -m unittest` across 13 files       cost −41%
  without  ██████████████████████          39.4k
  with     ████                             6.5k  −84%

Sonnet · trace `python -m unittest` across 13 files     cost −35%
  without  █████████████████               31.4k
  with     ███                              5.7k  −82%
```

120 `claude -p` runs in a clean environment (no user `CLAUDE.md`), Sonnet 5.5 and Opus
5.5, 3 runs per case, medians, 6 of the 10 cases held out from tuning. What it costs you:
each delegation adds 6–80 s, and on smaller surveys the cost change stays within the
spread between identical runs. Every case, with ranges:
[the bench](./docs/superpowers/evaluations/2026-10-12-held-out-bench.md).

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

## How it feels

Say you ask the main model to *map how auth flows across the ~8 files that touch
login*. Two ways that goes:

**Without haiku-scribe** — the main model opens all 8 files itself. Every line of
raw source now sits in the main context for the rest of the task (illustratively,
several thousand tokens of code you'll never look at again).

**With haiku-scribe** — the main model delegates the survey. The Haiku scout
reads the 8 files and hands back a compact brief; the main context holds only
this, not the raw files:

````markdown
### Summary
- Login enters at routes/auth.py:42, delegates to services/session.py.
- Password check is services/session.py:88 (bcrypt); tokens minted at :140.
- Two callers bypass the service and hit the model directly — see below.

### Evidence
routes/auth.py:42: `login()` — validates form, calls `Session.start()`.
services/session.py:88: bcrypt compare against `User.pw_hash`.
services/session.py:140: JWT minted, 24h expiry.

### Unknowns And Risks
- Refresh-token path not covered in these files; likely in middleware/.

### Suggested Direct Reads
services/session.py:140: inspect exact claim set before changing token shape.
````

The numbers above are illustrative (measured ones are in [Results](#results)) — the point is the *shape*:
the main context keeps ~40 lines of structured evidence instead of 8 files of
source. **One caveat still holds:** when the scout says coverage is complete,
use the brief as-is; re-reading the same files spends Haiku *and* the main model.

## Install

```
/plugin install haiku-scribe --marketplace RemyLespagnol/haiku-scribe
```

On Claude Code older than 2.1.275, add the marketplace first:

```
/plugin marketplace add https://github.com/RemyLespagnol/haiku-scribe.git
/plugin install haiku-scribe
```

Third-party marketplaces don't auto-update by default, and a marketplace can't turn
it on for you. To get new versions automatically: `/plugin` → **Marketplaces** →
`haiku-scribe` → **Enable auto-update** (it applies on the next launch, or now with
`/reload-plugins`). Without it, update by hand: `/plugin update haiku-scribe`, then
`/reload-plugins`. Remove: `/plugin uninstall haiku-scribe`.

## Use

The scout **auto-routes**. A subagent description alone almost never wins: left
to itself, the main model starts with its own `ls`/`grep` and never delegates. So
the plugin ships a small routing hook that watches what the main model is about to
do, not what you typed. When it starts a broad read (a recursive `find`/`grep -r`,
a command over many files or a glob, a 4th file in the same turn), the hook
declines that call once and points it at the scout. If the model really needs
those files verbatim (to edit them, or one or two are enough), it retries and the
retry goes through, so a misjudged call costs one turn. Any edit, or a scout call,
turns the hook off until your next prompt. In the bench ([Results](#results)) it never
fired on a one-file task, a bug fix in a 51 KB file included.

Turn routing off with `HAIKU_SCRIBE_ROUTE=off`. To **force** the scout, invoke it manually:

```
@haiku-scribe survey the auth flow across src/ and list every entrypoint
```

Skip it for small focused reads (≤3 known files) and when you need exact
line-level detail immediately — read those directly.

The scout runs at `effort: medium` whatever your session's effort: inheriting
`xhigh` made Haiku 5.5 think 3–9x more for the same brief.

## Optional: sharpen the reflex (power users)

The routing hook already does the routing, so the block below is a **booster, not
a requirement**. It nudges delegation before the first read rather than at it. Copy it into `~/.claude/CLAUDE.md`:

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
plugin (Claude Code loads only `agents/` and `hooks/`); `docs/superpowers/INDEX.md`
says which of those docs still hold.

- Checks (the same as CI): `python3 test_contract.py && python3 test_route.py && python3 test_bench.py && ruff check && claude plugin validate .`
- Routing eval (paid: runs `claude -p` on your account, never in CI): `python3 bench/route_eval.py -n 2`, then `python3 bench/summary.py`.
- Field audit (free, reads your local transcripts): `python3 bench/field_audit.py --since YYYY-MM-DD`.
- Demo GIF: edit `assets/demo.tape`, regenerate with `vhs assets/demo.tape` ([charmbracelet/vhs](https://github.com/charmbracelet/vhs)).
