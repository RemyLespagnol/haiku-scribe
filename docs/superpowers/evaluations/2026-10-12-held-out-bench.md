# Held-out bench, n=3 headline re-run, field audit, and the large-file Read gate

Date: 2026-10-12 · Claude Code 2.1.296 · Max subscription · plugin v0.3.4 (unchanged
`hooks/route`, `agents/haiku-scribe.md`) · driver `bench/route_eval.py`, summary
`bench/summary.py`, field audit `bench/field_audit.py` (raw transcripts in `bench/runs/`,
untracked). Clean env (`--setting-sources project,local`), medium effort, n=3 per cell,
**medians** (cost range in `bench/summary.py`). "Off" = the same plugin with
`HAIKU_SCRIBE_ROUTE=off`: the agent is still installed, only the hook is silent. Cost is
list price. 120 runs, $15.06.

Why: the earlier numbers came from n=1–2 means on 8 cases written while tuning the hook.
A competitor review (2026-10-12) found none with a with/without delegation eval, and
one headline (subagent-bouncer, −63%) that a single outlier run produced.

## Held-out cases (never used to tune the hook or the contract)

Stdlib packages never used in development (`logging`, `unittest`, `configparser.py`), a
generated 48 KB log, and a generated 51 KB module with a bug. All 72 answers correct.

| case | model | scout | cost off → on | main raw off → on | secs off → on |
|---|---|---|---|---|---|
| unittest-flow (13 files) | Sonnet | 3/3 | 0.111 → 0.073 (−35%) | 31.4k → 5.7k | 40 → 52 |
| unittest-flow | Opus | 3/3 | 0.293 → 0.174 (−41%) | 39.4k → 6.5k | 53 → 84 |
| logging-flow (3 large files) | Sonnet | 3/3 | 0.065 → 0.075 (+15%) | 12.3k → 5.4k | 23 → 61 |
| logging-flow | Opus | 2/3 | 0.163 → 0.182 (+12%) | 15.5k → 5.8k | 37 → 44 |
| big-log, big-edit, configparser-explain, configparser-signatures | both | 0/24 | hook never fired | — | — |

- Routing generalizes: the hook fired once on every multi-file run (12/12) and on none
  of the 24 one-file runs, including the bug fix in a 51 KB module (`big-edit`).
- The saving tracks real breadth. 13 files: −35% to −41% cost, context ÷5–6.
  3 files: +12–15% cost for context ÷2–3. Same shape as `json-flow` / `email-headers`
  before: when a few greps already answer it, delegating costs a little more.
- **Null control, free.** The four one-file cases never triggered the hook, so on and
  off ran identical code. Their spread is pure sampling noise: up to +43% (Sonnet
  `big-log`) and ±12% (Opus) between identical arms at n=3. Read any Sonnet cost delta
  under ~40% at n=3 as noise.

## Headline re-run at n=3 (the README cases)

| case | model | scout | cost off → on | main raw off → on | secs off → on |
|---|---|---|---|---|---|
| email-survey | Sonnet | 3/3 | 0.154 → 0.078 (−49%) | 53.8k → 5.6k | 42 → 64 |
| json-flow | Sonnet | 3/3 | 0.090 → 0.071 (−22%) | 15.5k → 5.1k | 30 → 36 |
| specs-history | Sonnet | 3/3 | 0.078 → 0.071 (−9%) | 13.9k → 5.7k | 28 → 82 |
| email-headers | Sonnet | 3/3 | 0.051 → 0.069 (+36%) | 4.0k → 5.4k | 21 → 42 |
| email-survey | Opus | 3/3 | 0.242 → 0.200 (−17%) | 34.6k → 14.1k | 48 → 95 |
| json-flow | Opus | 2/3 | 0.195 → 0.200 (+2%) | 23.8k → 14.7k | 39 → 58 |
| specs-history | Opus | 3/3 | 0.250 → 0.210 (−16%) | 39.7k → 18.7k | 41 → 119 |
| email-headers | Opus | 3/3 | 0.136 → 0.122 (−11%) | 10.4k → 7.0k | 32 → 62 |

All 48 answers correct. Delegation on broad prompts: 23/24 with the hook, 0/24 without.
Main context: −33% to −90% on every case but Sonnet `email-headers`. Latency is the
cost: +6 to +78 s per broad question.

## Scout citations

`route_eval` now checks every `path:line` in a brief against the fixture. 3 bad out of
651, all ranges running past end of file by 4–21 lines (`suite.py:375-400` on a
379-line file). No invented file. The first pass flagged 22 more: the scout writes
`v1-2-size-gated-nudge.md:18` for `2026-07-06-v1-2-size-gated-nudge.md`, which the
checker now resolves.

## Field audit (real sessions, free)

`python3 bench/field_audit.py --since 2026-10-10`, the author's own sessions with the
plugin installed, bench runs excluded:

```
sessions 20, turns 78
denials 11: scout 1, retry 2, other 8, ended 0
scout briefs 5: median 3655 chars; no read after the brief in 5/5, median 0 reads
```

- Delegation after a denial is rare in real work (1 scout, 2 exact retries, 8 other).
  Most "other" were a reworded retry of the same search; 2 turns reached the scout later.
  Replaying the 11 denied commands through the current `broad-bash`: 10 still flagged,
  the heredoc false positive is gone since v0.3.1.
- No re-read after any brief (0 reads after 5/5): the coverage statement holds in the field.
- Token buckets by role and model are in the full output. The scout's cache writes are
  all 5-minute, the main thread's all 1-hour.

## Large-file Read gate: not built

Competitors gate a whole-file `Read` of a large file (token-economy-kit around 10k
tokens, cheap-llm-router at 200 lines). The plan built that gate only if the main
model actually does it. Across all 72 held-out runs (4 cases built around one 48–54 KB file, plus
`logging`'s 83 KB `__init__.py`), neither Sonnet nor Opus ever read a large file whole. They grep, `sed -n`, or page
with `offset`/`limit` (Sonnet `configparser-explain`: 11 ranged Reads, never the whole
file). A whole-file gate has nothing to catch, so `hooks/route` is unchanged.

This also answers the open question from the 2026-07-06 break-even sweep (large file +
detail task → delegate, then re-read, +50%). On the current hook that shape is never
reached: no one-file run delegated (0/24, including `configparser-signatures`), so
nothing gets read twice.

## Bench fixes found by this run

- **Grader read the wrong turn.** A model that launches `find /` gets it backgrounded;
  `claude -p` then re-opens the session and the last `result` is only "the background
  search finished". The grader now accepts any `result` turn (`route_eval.correct`).
  `configparser-signatures` went 0/3 → 3/3, with the same answers. Its 275 s on-arm median
  is that wait, not the hook.
- **`unittest-flow` must-string.** Correct answers say `loader.py` / `self.testLoader`,
  never the class name `TestLoader`; the grader now checks `loader.py`.
- **Audit excluded bench runs.** `route_eval`'s own `claude -p` runs share the transcript
  store (237 `hs-route-*` dirs against 101 real ones) and had swamped the field numbers.

## Limits

- n=3 per cell. Routing (delegation, no delegation on one-file tasks) is far outside
  the noise; cost deltas under ~40% (Sonnet) or ~12% (Opus) are not.
- Stdlib fixtures come from one Python (3.12.6). Everything is Python or Markdown.
- `-p` one-shot runs only. The field audit covers interactive use, but 20 sessions by one
  user.
