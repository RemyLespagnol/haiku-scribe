# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`haiku-scribe` is a personal installer (a Python CLI, no runtime dependencies) that provisions a read-only, Haiku-powered "context compression" subagent into a user's Claude Code config under `~/.claude`. It writes an agent file, a managed `CLAUDE.md` guidance block, safety deny rules, and V1.2 nudge hooks. It is **not** a runtime library — the "product" is the generated config, not imported code.

## Commands

```bash
python -m pytest                    # run all tests
python -m pytest tests/test_cli_setup.py -k merge   # single test / filter
ruff check                          # lint

python -m haiku_scribe setup --dry-run   # preview install (also: haiku-scribe setup)
python -m haiku_scribe setup
python -m haiku_scribe doctor            # validate an install
python -m haiku_scribe uninstall --dry-run
python3 bench/report.py                  # regenerate the CodeGraph benchmark report
```

Always run `setup`/`uninstall` with `--dry-run` first when testing against a real home. Tests and internal callers pass a `--home` path (hidden flag) to install into a temp dir instead of `~`.

## Architecture

The CLI (`cli.py`) dispatches four commands to one module each; each returns a frozen dataclass of `planned`/`written`/`removed` paths that `cli.py` prints. The install target is modeled once in `paths.py` (`ClaudePaths.for_home`) — everything else takes a `home: Path` and derives paths from it.

Two ideas govern everything:

1. **Idempotent, backup-before-mutate writes.** Every file write goes through `_write_text_if_changed` (skip if identical) and calls `backup_existing` into `~/.claude/backups/haiku-scribe/` before overwriting user content. `setup.py` and `v1_2_hooks.py` each have their own copy of `_write_text_if_changed`.

2. **Ownership tracking so uninstall only removes what we added.** The installer never blindly overwrites shared files. It records what it owns under a `haiku_scribe` key in `settings.json` (`owned_deny_rules`, `owned_v1_2_nudge_hook_command`), then uninstall removes only those tracked entries and leaves surrounding user content intact. The managed `CLAUDE.md` block is bounded by `HAIKU_SCRIBE_START`/`_END` markers (see `markdown_blocks.py`) for the same reason.

### The four surfaces it manages

- **Agent file** `~/.claude/agents/haiku-scribe.md` — generated verbatim by `render_agent_markdown()` in `contracts.py`. The read-only contract (`tools: Read, Glob, Grep`, `model: haiku`, forbid edit/write/shell/web/MCP) lives here as a string literal.
- **Guidance block** in `~/.claude/CLAUDE.md` — `render_guidance_block()` in `contracts.py`, inserted/replaced via marker comments.
- **Deny rules** in `~/.claude/settings.json` — `DEFAULT_DENY_RULES` (secrets/creds globs), merged by `settings.py::merge_deny_rules`.
- **V1.2 nudge hooks** — `v1_2_hooks.py` writes a standalone hook script (`render_nudge_hook_script()`, emitted as a string literal) and registers it as a `UserPromptSubmit` hook plus a `PreToolUse` hook (matcher `Read|Grep`) in `settings.json`. The script detects broad-context prompts by keyword and prints a delegation nudge; it logs decisions to `~/.claude/haiku-scribe-nudges.jsonl` and self-suppresses inside subagent transcripts.

`doctor.py` re-derives all of the above and reports missing/invalid entries — it is the spec of what a healthy install looks like; keep it in sync when changing any generated content.

### Generated content is source-of-truth as string literals

The agent markdown, guidance block, and hook script are Python strings in `contracts.py` / `v1_2_hooks.py`. Editing installed behavior means editing those literals (and the matching `doctor.py` checks + tests), not the files under `~/.claude`.

## Notes

- `contracts.py` and the guidance block contain intentional-looking duplicated/terse sentences — that is the current authored wording, not accidental. Don't "clean it up" without checking `docs/superpowers/specs/` for intent.
- `bench/` is a semi-manual CodeGraph evaluation workspace; the base agent is deliberately kept MCP/CodeGraph-free until benchmark data justifies otherwise.
- `docs/superpowers/` holds the design specs and plans behind each version (V0–V5 roadmap in README). Read the relevant spec before changing behavior.
