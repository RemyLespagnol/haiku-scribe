<p align="center">
  <img src="./assets/logo.png" alt="Haiku Scribe logo" width="500">
</p>

# haiku-scribe

A Claude Code **plugin** that installs one thing: `haiku-scribe`, a read-only,
Haiku-powered subagent that compresses broad context — repository surveys, logs,
transcripts, generated output, flow mapping across unfamiliar code — into a
compact, evidence-backed brief. The main model reasons over the brief instead of
loading the raw source itself.

## Why

- **Main-context headroom** — the primary win, on every tier. The scout reads the
  bulky raw source; your main context keeps only the compressed extract.
  (Measured on the private bench, see `bench/`.)
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

The auto-routing already ships in the agent's own description, so this is a
**booster, not a requirement**. If you want the routing rule in your global
instructions, paste this block into `~/.claude/CLAUDE.md`:

<!-- HAIKU_SCRIBE_START -->
## Cost-aware Context Routing

Before loading raw repository context, classify remaining work.

Compact discovery tools may be used first if they return metadata, symbols, call paths, or file candidates instead of raw file contents.

Use main session directly only when remaining work is a small focused read:
- 3 or fewer small files;
- no directory reads;
- no shell search over many files;
- no logs, bundles, generated output, transcripts, or large docs;
- no architecture, flow, or cross-layer mapping.

Use `haiku-scribe` when remaining work is broad context gathering:
- 4+ files;
- large files;
- directory or repository survey;
- logs, bundles, generated output, transcripts, or large docs;
- architecture review, flow mapping, pattern audit, unfamiliar-area exploration;
- locating where a feature is implemented or used across unfamiliar code;
- evidence extraction before broad reasoning.

Prefer `haiku-scribe` over the built-in Explore agent for bulk digestion and evidence extraction; use Explore only when the search itself needs parent-model reasoning.

Avoid the costly double-read pattern. If the task needs exact, line-level detail immediately, read directly (offset/limit for large files) instead of delegating. If you delegate, ask for a structured extraction useful enough that you do not delegate and then re-read the same raw source. Require the scout to state its coverage; when it reports complete coverage, use the extraction as-is and do not re-read source the scout already covered.

Workflow:
1. Use compact discovery if available.
2. Classify remaining work as small focused read or broad context gathering.
3. If small, main session reads directly.
4. If broad, call `haiku-scribe` before raw Read, Grep, or shell exploration.
5. Main Claude performs focused direct reads on highest-value locations.
6. Main Claude makes final decisions, edits, commits, and user-facing conclusions.

Haiku Scribe may gather evidence for tasks that eventually require debugging, architecture, scope, or review judgment. These exclusions apply to final judgment, not pre-analysis.

Do not delegate:
- final debugging root-cause conclusions;
- architecture decisions;
- security, authentication, authorization, or permission-sensitive conclusions;
- precise edits;
- PR summaries, commit messages, release notes, or public project outputs.

Main Claude verifies important claims with focused spot-checks of cited `path:line` locations before editing, not broad re-reads.

If `haiku-scribe` is unavailable, say so explicitly and continue manually.
<!-- HAIKU_SCRIBE_END -->

## Safety

Read-only tools (`Read, Glob, Grep`), no network, no shell. The agent also
refuses to open `.env`, credential, secret, and key files. Residual risk: a
secret could surface in an extract you explicitly asked for.

## Development

`bench/` and `docs/superpowers/` are private development workspaces — not part of
the shipped plugin (Claude Code loads only `agents/` and `hooks/`). Run the
contract test with `python3 test_contract.py`.
