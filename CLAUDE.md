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
python3 test_contract.py         # the one test: asserts the agent contract keeps its required clauses
python3 -m pytest -q             # same test via pytest
ruff check                       # lint
claude plugin validate .         # validate the plugin/marketplace manifests
claude --plugin-dir . -p "..."   # load the plugin locally without installing
```

## Architecture — the three shipped surfaces

Claude Code loads only `agents/`, `hooks/`, and the manifests in `.claude-plugin/`.
Everything else in the repo (`bench/`, `docs/`) is a private dev workspace, present
but never loaded.

1. **The subagent** — `agents/haiku-scribe.md`. A static markdown file: frontmatter
   (`model: haiku`, `tools: Read, Glob, Grep`, and the load-bearing `description`)
   plus the body contract. Two fields are load-bearing:
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

2. **The onboarding nudge** — `hooks/hooks.json`. A single `UserPromptSubmit` hook
   with an inline shell command, gated by a marker file
   (`~/.claude/.haiku-scribe-onboarded`) so it fires exactly once ever. Emits the
   note, then writes the marker (`printf` before `touch` = fire at-least-once rather
   than silently-never). No breadth detection, no PreToolUse, no logging — human
   discovery only.

3. **README** — install steps, the `@haiku-scribe` manual-invocation fallback, the
   optional CLAUDE.md routing snippet (a *booster*, not a carrier — the two carriers
   above already ship the load-bearing copy), the KPI, and the no-API-key moat.

## Notes

- `test_contract.py` is the spec of a healthy contract: it asserts the required
  clauses (read-only tools, routing trigger, coverage statement, read-restraint) are
  present in `agents/haiku-scribe.md`. Keep it in sync when changing the contract.
- `pyproject.toml` exists only for the one test + lint; `testpaths` is scoped to
  `test_contract.py` on purpose (root-wide collection breaks on the `bench/` sample
  fixture package).
- `bench/` is a private, semi-manual CodeGraph/headroom evaluation workspace. Its
  harness (`run_headless.py`) referenced the old Python package and is not runnable
  as-is after the plugin pivot — treat it as historical unless revived.
- `docs/superpowers/` holds the design specs and plans behind each version. Read the
  relevant spec before changing behavior; the plugin pivot is
  `docs/superpowers/specs/2026-07-09-plugin-pivot-design.md`.
