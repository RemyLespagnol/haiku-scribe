# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`haiku-scribe` is a **Claude Code plugin** (not a program). It ships one thing: a
read-only, Haiku-powered "context compression" subagent. The product is a small
set of **static files** a user installs via `/plugin` — there is no build step, no
runtime code, no generated config. Editing behavior means editing these files
directly.

This repo is simultaneously the plugin and its own single-entry marketplace, so
`/plugin marketplace add <git-url>` + `/plugin install haiku-scribe` works from
this one repo.

## Commands

```bash
python3 test_contract.py         # asserts the agent contract keeps its required clauses
python3 test_route.py            # routing hook: broad-call classifier, deny-once, disarm rules
python3 -m pytest -q             # both tests via pytest
python3 bench/route_eval.py -n 2 # paid routing eval (claude -p, clean env); summary: bench/summary.py
ruff check                       # lint
claude plugin validate .         # validate the plugin/marketplace manifests
claude --plugin-dir . -p "..."   # load the plugin locally without installing
```

## Architecture — the shipped surfaces

Claude Code loads only `agents/`, `hooks/`, and the manifests in `.claude-plugin/`.
Everything else in the repo (`docs/`) is a private dev workspace, present
but never loaded.

1. **The subagent** — `agents/haiku-scribe.md`. A static markdown file: frontmatter
   (`model: haiku`, `effort: medium`, `tools: Read, Glob, Grep`, and the load-bearing
   `description`) plus the body contract. Two fields are load-bearing:
   - **`description` = the routing carrier.** Claude picks a subagent by reading its
     `description`, so the when-to-delegate trigger (4+ files, logs, transcripts,
     surveys, unfamiliar flow; skip for ≤3 known files) lives there. It must stay
     YAML-quoted — the value contains `": "` which is a mapping indicator unquoted.
   - **The body's Response Shape / coverage statement = the don't-re-read carrier.**
     The scout states coverage explicitly so the main model trusts the extract and
     does not re-read the raw source (the double-read is strictly worse — it spends
     Haiku *and* Opus). See `docs/superpowers/specs/2026-07-06-v1-2-size-gated-nudge.md`
     for the break-even lesson behind this wording.
   - **Read-restraint** (`never open .env`/credential/secret files) replaces the
     deny rules a plugin cannot ship; read-only tools + no network is the only other
     boundary.
   - **`effort: medium` = the cost pin.** Without it the scout inherits the main
     session's effort; at `xhigh` Haiku 5.5 thinks 3–9x more for the same brief.
     `low` is cheaper but cut a named scope short (4 of 13 files). Haiku 4.5
     (Bedrock/Vertex) accepts the field without error. Evidence:
     `docs/superpowers/evaluations/2026-10-09-haiku-5-5-effort-pin.md`.

2. **The routing hook** — `hooks/route` + `hooks/broad-bash` (POSIX sh + awk, no `jq`),
   wired in `hooks/hooks.json`. The description alone never got an unprompted
   delegation in a clean env (0/8 Sonnet, 0/3 Opus): the model always opens with its
   own `ls`/`find`/`grep`. The hook judges the model's *tool call*, never the prompt
   wording (a keyword classifier was tried and missed broad prompts without the words).
   - `PreToolUse` on the main thread: the first broad read of a turn is denied once
     with a pointer to `haiku-scribe:haiku-scribe`. Broad = a recursive/wildcard
     `find`/`grep -r`/`rg`/`ls -R`/`tree`, a command or loop over 3+ files or a glob,
     a `Glob` with `**`, a `Grep` on a directory, or a 4th distinct file `Read` this turn.
     A retry goes through, so a misjudged call costs one turn.
   - Disarmed for the rest of the turn by a scout call or any edit; subagent calls
     (`agent_id`) and other agent types are never touched.
   - State: per-session files in `$XDG_RUNTIME_DIR` (else `$TMPDIR`, else `/tmp`).
     `UserPromptSubmit` only resets them (not on `<task-notification>` turns). The
     denial is claimed atomically (`set -C`), so parallel calls get one deny, and an
     unwritable state dir never denies. `HAIKU_SCRIBE_ROUTE=off` disables it.
   - Must stay portable: macOS `/bin/sh` + BSD awk and Debian dash + mawk (no `{n,}`
     regex intervals). `test_route.py` passes on both.
   - Evidence: `docs/superpowers/evaluations/2026-10-10-route-hook.md`.
   The onboarding note (inline command, same `UserPromptSubmit` block) fires once per
   marker; the marker is `~/.claude/.haiku-scribe-onboarded-route` so pre-hook users
   see the new note.

3. **README** — install steps, the `@haiku-scribe` manual-invocation fallback, the
   optional CLAUDE.md routing snippet (a *booster*, not a carrier — the two carriers
   above already ship the load-bearing copy), the KPI, and the no-API-key moat.

## Notes

- `test_contract.py` is the spec of a healthy contract: it asserts the required
  clauses (read-only tools, routing trigger, coverage statement, read-restraint) are
  present in `agents/haiku-scribe.md`. Keep it in sync when changing the contract.
- `test_route.py` pins the hook's behavior, including the broad/targeted command
  examples. Keep it in sync when changing `hooks/route` or `hooks/broad-bash`.
- `pyproject.toml` exists only for the tests + lint; `testpaths` is scoped to the two
  test files on purpose (`bench/` is paid and never runs in CI).
- `docs/superpowers/` holds the design specs and plans behind each version. Read the
  relevant spec before changing behavior; the plugin pivot is
  `docs/superpowers/specs/2026-07-09-plugin-pivot-design.md`.
