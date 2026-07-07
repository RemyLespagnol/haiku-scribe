# TODO

## Fait le 2026-07-07 (branche `feat/v1-2-default-hooks`)

Plan `docs/superpowers/plans/2026-07-07-v1-2-opt-in-hooks-and-bench-fixes.md`, commits `5ecb617..892f595` :

- Décision default-on tranchée : **hooks opt-in** (`setup --hooks on`, off par défaut ; `setup` retire tout hook possédé, y compris legacy).
- `bench/report.py` réparé (ignore les records étrangers sans `task_id`).
- Dev deps `pytest`/`ruff` déclarées dans `pyproject.toml` (`ruff check` runnable depuis l'env).
- Hooks partiellement gouvernables : `--hooks on|off` + retrait des hooks possédés à l'opt-out ; kill-switch `HAIKU_SCRIBE_HOOKS=off` déjà présent. Reste ouvert : le mode `auto` et les décisions nommées loggées.

## Ordre de reprise proposé (2026-07-07)

Séquence recommandée à travers les items P0/P1 ci-dessous, sans les dupliquer :

1. Réparer `python3 bench/report.py` (schéma `task` vs `task_id`) — voir "Fix benchmark reporting". Prérequis à toute décision data-driven.
2. Déclarer les dev deps `pytest`/`ruff` dans `pyproject.toml` — voir "Declare dev dependencies".
3. Triggers FR/EN réalistes + tests positifs/négatifs — voir "Define the real V1.2 trigger policy" et "Add multilingual trigger tests".
4. Sortie scout substituable (extractions structurées : stats, comptages, occurrences ordonnées, paths + lignes) — voir "Make scout output substitutable". C'est la vraie correction du +50% mesuré au sweep.
5. Hooks gouvernables (`setup --hooks on|off|auto`, décisions nommées loggées, fail-open) — voir la section "Hook Strategy Inspired By CodeGraph".
6. Trancher default-on vs opt-in, avec le bench réparé et une arme `HAIKU_SCRIBE_HOOKS=off` — voir "Decide whether V1.2 nudges should stay default-on". Pas de blocage dur `PreToolUse` avant ces données.

This file tracks what is missing before Haiku Scribe can be considered product-ready against the original goal:

> A Claude Code Enterprise-safe Haiku subagent for cheap read-only context compression, with no external API key, no local model setup, no MCP dependency, and progressive governance.

## P0 - Product Correctness

- [x] Decide whether V1.2 nudges should stay default-on. — **Decided: opt-in.** `setup --hooks on` to enable; default off. Rationale: `docs/superpowers/evaluations/2026-07-06-v1-2-break-even-sweep.md` (default-on often raises cost).
  - Current evidence shows that delegation can increase cost when the main session delegates and then re-reads the same raw material.
  - Use `docs/superpowers/evaluations/2026-07-06-v1-2-break-even-sweep.md` as the decision input.
  - Exit criteria: documented decision to keep default-on, gate by task/size, or make V1.2 opt-in.

- [ ] Make scout output substitutable for supported tasks.
  - Strengthen prompts/contracts so `haiku-scribe` returns exact structured extraction when the task needs stats, counts, ordered occurrences, or correlations.
  - The main session should not need broad raw re-reads after the scout returns.
  - Exit criteria: benchmark shows lower raw tokens into main session without correctness loss.

- [ ] Define the real V1.2 trigger policy.
  - Current triggers miss broad French prompts such as project-state audits.
  - Prefer conservative triggers, but add realistic product-language cases: `etat du projet`, `ce qu'il manque`, `bloque`, `audit projet`, `cartographie`, `plusieurs fichiers`.
  - Exit criteria: tests cover both false positives and real broad prompts in English/French.

## P0 - Hook Strategy Inspired By CodeGraph

- [x] Make hook installation explicitly governable. — **Partial:** `setup --hooks on|off` added (default off); `off`/plain `setup` removes owned + legacy hook entries; `HAIKU_SCRIBE_HOOKS=off` kill-switch present. Still open: `auto` mode.
  - CodeGraph's useful pattern is: installer-owned hook, default-on only when the user accepts/defaults, cleanly removable on opt-out, and runtime kill-switch for experiments.
  - Replace the implicit always-on behavior with a clear setup option such as `haiku-scribe setup --hooks on|off|auto`.
  - `--hooks off` should remove any Haiku Scribe-owned hook entry instead of merely skipping writes.
  - Keep `HAIKU_SCRIBE_HOOKS=off` as a runtime escape hatch for A/B runs and emergency disablement.
  - Exit criteria: install, reinstall, opt-out, uninstall, and kill-switch behavior are covered by tests.

- [ ] Split hook behavior into named gate decisions.
  - Record whether the hook chose `silent`, `prompt_nudge`, `followup_nudge`, `large_file_nudge`, or `disabled`.
  - Avoid logging prompt contents; only store fixed decision names, matched trigger IDs, sizes, and coarse metadata needed for reporting.
  - Exit criteria: `haiku-scribe report` can show hook usefulness without reading private prompt text.

- [ ] Treat the hook as additive and degradable, not enforcing.
  - If parsing stdin, reading state, or checking files fails, the hook should exit `0` silently.
  - Non-broad prompts, exact edit requests, unrecognized tools, and subagent runs should remain no-ops.
  - Exit criteria: tests prove malformed payloads and unsupported events never block Claude Code.

- [ ] Add multilingual trigger tests before broadening triggers.
  - Cover French prompts that match our real usage: `regarde l'etat actuel du projet`, `ce qu'il manque`, `qu'est-ce qui bloque`, `audit du projet`, `cartographie du code`.
  - Keep negative controls: typo fixes, small exact-file edits, README/license updates, and direct edit requests.
  - Exit criteria: trigger changes are justified by tests, not ad hoc keyword additions.

- [ ] Make benchmark arms isolate the hook effect.
  - Add a bench mode where both arms have the same agent/guidance installation, but one arm disables hooks with `HAIKU_SCRIBE_HOOKS=off`.
  - Keep a separate raw baseline where Haiku Scribe is fully uninstalled.
  - Do not let an ambient user-level hook contaminate the control arm.
  - Exit criteria: benchmark output separates "guidance caused delegation" from "hook caused delegation".

- [ ] Do not ship hard `PreToolUse` blocking yet.
  - CodeGraph keeps hard read-redirection in evaluation scripts, not as the primary product surface.
  - Haiku Scribe should stay non-blocking until report data proves where enforcement helps and where it harms.
  - Exit criteria: any future blocking design requires a separate spec, override story, and A/B evidence.

## P0 - Measurement And Reporting

- [ ] Implement `haiku-scribe report`.
  - Aggregate local hook/transcript data.
  - Show direct reads, large reads, Haiku Scribe invocations, suspected missed delegations, top files/projects, and estimated context saved.
  - Use a Triss-style local JSONL usage log: one best-effort record per hook decision or scout invocation, with timestamp, fixed event type, model/agent label, token counts when available, cwd/project, and no prompt text.
  - Support `--since 24h|7d|30d`, `--by-project`, `--by-decision`, `--json`, and `--reset`.
  - Keep tracking disableable with an environment switch such as `HAIKU_SCRIBE_USAGE_LOG=0`.
  - Exit criteria: CLI command exists, has tests, and README documents it.

- [ ] Add audit-only event logging if report needs more data than the V1.2 nudge log.
  - Original V1.1 called for `PostToolUse` logging of `Read`, `Grep`, `Glob`, and `Agent`.
  - Follow Triss/Scribe's safety posture: logging must be best-effort, bounded by rotation, and never fail the real Claude Code action.
  - Exit criteria: reporting can distinguish direct raw reads from delegated scout work.

- [ ] Add usage-log rotation and privacy controls.
  - Rotate the active JSONL log when it crosses a fixed size, keeping at most one archive by default.
  - Allow cwd/project logging to be disabled independently, for users who sync logs across machines.
  - Exit criteria: tests cover malformed log lines, rotation, disabled logging, and aggregation with missing fields.

- [x] Fix benchmark reporting. — **Done:** `load_runs` skips foreign records without `task_id`; `python3 bench/report.py` runs on checked-in data.
  - `python3 bench/report.py` currently crashes on `bench/runs/sweep.jsonl` because the current sweep schema uses `task`, not `task_id`.
  - Exit criteria: documented benchmark command runs successfully on current checked-in data.

## P1 - CLI Scope

- [ ] Implement `haiku-scribe extract`.
  - Parse Claude Code JSONL transcripts into readable conversation artifacts.
  - Borrow the robust `lmsgo` / `claude-coworker-model` shape: support both common Claude JSONL formats, skip system/tool/thinking blocks, handle string content and text block arrays, tolerate malformed lines, and avoid loading huge lines unsafely.
  - Support `--last N`, `-o/--output`, secret redaction, and noisy tool-output exclusion.
  - Print a small stderr summary when writing a file: number of exchanges, lines, and characters.
  - Exit criteria: command exists with parser tests and fixture coverage.

- [ ] Add `haiku-scribe agent-help`.
  - Install only a tiny always-loaded guidance block, then expose the full routing cookbook through an on-demand CLI command, inspired by Triss.
  - The installed block should state when to delegate, when not to delegate, and point to `haiku-scribe agent-help` for full examples.
  - Exit criteria: setup writes a small marker-owned block, `agent-help` prints the full reference, and tests prove reinstall is idempotent.

- [ ] Tighten the scout prompt contract for cache-friendly delegation.
  - Build worker/scout prompts with stable corpus first and the specific question last, like `ask-kimi` and `scribe-mcp`.
  - Require structured bullets, file paths, and line references when available; forbid broad prose that forces the main agent to reread everything.
  - Exit criteria: prompt fixture tests prove the corpus/question order and required output contract.

- [ ] Decide whether `prototype-hooks` should remain public.
  - It is now a compatibility alias, while normal `setup` installs V1.2 hooks.
  - Exit criteria: hide, deprecate, or clearly document it.

- [ ] Decide on project/team scope timing.
  - `--scope project` is in the PRD but not implemented.
  - Exit criteria: either schedule V2 explicitly or remove project-scope commands from near-term docs.

## P1 - Installer And Uninstall UX

- [ ] Make `setup --dry-run` truthful after installation.
  - It currently lists all planned writes even when a real second `setup` would write nothing.
  - Match the useful `lmsgo setup --dry-run` behavior: preview actual env/rules/hook changes without touching files.
  - Exit criteria: dry-run reports only actual changes or clearly says it is a static plan.

- [ ] Improve uninstall output wording.
  - `uninstall` can print `Removed CLAUDE.md/settings.json` even when it only removed owned content and left the files present.
  - Exit criteria: output distinguishes deleted files from updated files.

- [x] Add optional no-hooks install path if V1.2 remains controversial. — **Done:** no-hooks is now the default; hooks are opt-in via `setup --hooks on`.
  - Candidate flag: `haiku-scribe setup --no-hooks`.
  - Exit criteria: users can install the safe agent/guidance/deny rules without nudges.

- [ ] Keep marker-owned setup blocks tiny and replaceable.
  - Use explicit start/end markers for every installed block.
  - Reinstall should replace only the owned block, append when no block exists, and preserve all user-authored content.
  - Exit criteria: tests cover create, append, replace, global/local target, and uninstall cleanup.

## P1 - Test And Dev Reproducibility

- [x] Declare dev dependencies. — **Done:** `[project.optional-dependencies] dev = ["pytest>=8", "ruff>=0.6"]`; `pip install -e ".[dev]"` enables the documented commands.
  - `pytest` and `ruff` are not declared in `pyproject.toml`.
  - Exit criteria: a fresh checkout can run the documented test/lint commands.

- [x] Add a lint command to project metadata. — **Done:** `ruff` is declared in the `dev` extra, so `ruff check` runs from the project environment.
  - Current `ruff check` cannot run unless ruff is installed externally.
  - Exit criteria: documented command works from the project environment.

- [ ] Fix `pytest bench` collection.
  - `bench/fixtures/sample-cli/tests/test_sample_cli.py` needs its fixture package on `PYTHONPATH` or should be excluded from default bench collection.
  - Exit criteria: either `python3 -m pytest bench` passes or docs specify the supported targeted bench test command.

## P2 - Packaging And Distribution

- [ ] Add a `LICENSE`.
  - README currently says this is required before wider reuse or distribution.
  - Exit criteria: repository includes a chosen license file and package metadata references it.

- [ ] Add package metadata for maintainability.
  - Consider authors, readme, license, classifiers, and optional dependency groups.
  - Exit criteria: editable install and package build metadata are complete enough for personal distribution.

- [ ] Add changelog or release notes before tagging.
  - Current package version is `0.1.0`.
  - Exit criteria: release notes explain V1/V1.2 behavior and known limitations.

## P2 - Documentation

- [ ] Update README status to match reality.
  - Make clear which parts are implemented now and which remain roadmap.
  - Include the V1.2 measurement caveat: nudges are not guaranteed savings.
  - Exit criteria: README does not imply `report`, `extract`, or project scope exist.

- [ ] Document the anti-double-read rule prominently.
  - Delegation only helps when the scout replaces broad raw reading.
  - Use explicit positive and negative routing rules from the coworker repos:
    delegate broad reading, summarisation, multi-file search, transcript extraction, and large-file reconnaissance;
    do not delegate architecture decisions, root-cause debugging, safety-critical code, exact line edits, or tasks under roughly 2k tokens.
  - Exit criteria: README and generated guidance both warn against delegate-then-reread workflows.

- [ ] Defer MCP and write-capable tools until the CLI proves value.
  - `scribe-mcp` is useful as a future MCP reference, especially `alwaysLoad` and tool-schema routing, but Haiku Scribe's original product constraint is no MCP dependency.
  - `kimi-write`, `write_docs`, and `write_boilerplate` are intentionally out of MVP scope because Haiku Scribe should stay read-only and Enterprise-safe.
  - Exit criteria: roadmap states MCP/write tools are future optional surfaces, not current requirements.

- [ ] Add a manual smoke test checklist.
  - Automated tests cannot verify real Claude Code model invocation.
  - Exit criteria: docs include setup, doctor, visible agent, nudge behavior, and uninstall checks.

## Reference Patterns Reviewed

- [x] `colbymchenry/codegraph`: optional additive hooks, runtime kill switch, multilingual trigger tests, and isolated A/B hook benchmarks.
- [x] `imkunal007219/claude-coworker-model`: simple corpus-first/question-last prompt shape, transcript extraction, and stderr token/cache reporting.
- [x] `cicoub13/scribe-mcp`: MCP routing guidance, `alwaysLoad` tradeoff, safe bulk read limits, skipped-file handling, workspace root guard, and meta footer.
- [x] `payfacto/lmsgo`: stdlib-style `extract`, `--last`, dry-run setup, sentinel-owned installed snippets.
- [x] `ayleen/triss-coworker`: nano agent rules plus `agent-help`, local JSONL usage report, marker-owned init, path safety for MCP mode, and opt-outable tracking.

## Current Verification Baseline

Last local checks from audit:

```bash
python3 -m pytest tests bench/test_cost.py bench/test_report.py
# 68 passed

python3 -m compileall -q src tests bench
# passed
```

Known unsupported or failing commands:

```bash
python3 -m ruff check
# fails unless ruff is installed externally

python3 bench/report.py
# currently fails on current sweep data schema

python3 -m pytest bench
# currently collects a fixture package without the needed PYTHONPATH
```
