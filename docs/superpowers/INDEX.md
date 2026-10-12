# docs/superpowers index

Which docs still describe the shipped plugin. Everything dated before 2026-07-09
describes the pre-plugin Python CLI (`src/`, `setup`, `doctor`, `gain`, nudge hooks)
that the plugin pivot (#5) deleted: read those for the lessons, not the design.
Plan checkboxes were never ticked; this index and git history are the record.

## Current

| Doc | Status |
|-----|--------|
| `specs/2026-07-09-plugin-pivot-design.md` | Shipped (#5). Still the architecture, except it cut `PreToolUse` hooks: routing is now one (`hooks/route`). |
| `plans/2026-07-08-plugin-pivot-plan.md`, `plans/2026-07-09-plugin-pivot.md` | Shipped (#5). |
| `specs/` + `plans/2026-07-09-credibility-adoption-pass*` | Shipped (v0.2.0). |
| `specs/` + `plans/2026-07-09-discoverability-top-of-fold*` | Shipped (82670a6). |
| `evaluations/2026-10-09-haiku-5-5-effort-pin.md` | Shipped (#6): `effort: medium`. |
| `evaluations/2026-10-10-route-hook.md` | Shipped (#7): the routing hook. Superseded numbers: see 2026-10-12. |
| `evaluations/2026-10-12-held-out-bench.md`, `plans/2026-10-12-held-out-bench-and-large-read.md` | Latest numbers: held-out cases, n=3 medians, field audit. Large-file Read gate not shipped: no model ever read a large file whole. |
| `evaluations/2026-07-06-v1-2-break-even-sweep.md` | Holds: the loss case (large file + detail task → main re-reads → +50%) behind the coverage statement. Re-run on the current contract in `evaluations/2026-10-12-held-out-bench.md` (`configparser-signatures`): never reached, no one-file task delegates. |
| `evaluations/2026-07-07-clean-win-qa-extraction.md` | Holds: the win case, counterpart of the sweep. |

## Superseded

| Doc | Superseded by |
|-----|---------------|
| `specs/2026-07-04-haiku-scribe-roadmap-design.md` | The plugin pivot; its "next specs" list is stale. |
| `specs/2026-07-06-v1-2-size-gated-nudge.md` | Never shipped. The pivot dropped size classifiers; `hooks/route` judges the tool call instead. |
| `specs/2026-07-06-haiku-scribe-v1-2-default-hooks-design.md`, `plans/2026-07-06-haiku-scribe-v1-2-default-hooks.md`, `plans/2026-07-07-v1-2-opt-in-hooks-and-bench-fixes.md`, `evaluations/2026-07-06-v1-2-default-hooks-bench.md` | Nudge hooks shipped opt-in (#4), deleted by the pivot, replaced by `hooks/route`. |
| `specs/2026-07-06-v1-guidance-routing-design.md`, `plans/2026-07-06-v1-guidance-routing.md` | CLAUDE.md routing copy, now the optional README booster; the hook carries routing. |
| `plans/2026-07-07-make-it-usable-plan.md` | The plugin pivot. Its FR/EN trigger list is rejected: routing never keys on prompt words. |
| `plans/2026-07-05-haiku-scribe-v1-personal-cli.md` | The CLI it built was deleted by the pivot. |
| `specs/2026-07-06-haiku-scribe-v1-2-benchmark-target.md` | Partly run (500/5k/10k lines, n=1); `bench/route_eval.py` is the current driver. |

## Historical

- v0 agent contract and its manual trials: `specs/2026-07-04-v0-manual-subagent-design.md`,
  `plans/2026-07-04-v0-manual-subagent-validation.md`, `evaluations/2026-07-04-v0-manual-workflow-trials.md`,
  `checks/v0-manual-subagent-checks.sh`, `specs/` + `plans/2026-07-05-v0-agent-simplification*`,
  `plans/2026-07-05-haiku-scribe-v0-unblock.md`. `test_contract.py` now guards the contract.
- CodeGraph-backed scout, evaluated and not pursued (the agent keeps `Read, Glob, Grep`):
  `specs/2026-07-05-codegraph-agent-bench-design.md`, `specs/2026-07-05-haiku-codegraph-scout-design.md`,
  `plans/2026-07-05-codegraph-agent-bench-bootstrap.md`, `evaluations/2026-07-05-codegraph-agent-bench.md`.

## Stale references

- `bench/cost.py` and `bench/run_headless.py`, cited by the July evaluations, were removed in f8093b6.
- `feat/read-gate`, cited by the effort-pin and route-hook evaluations, merged as #7; its driver is `bench/route_eval.py`.
