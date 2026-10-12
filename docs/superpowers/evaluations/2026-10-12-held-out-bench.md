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
- Context shrinks on every multi-file case (÷2 to ÷6). Cost falls clearly only on the
  broadest one (`unittest-flow`, 13 files: −35% Sonnet, −41% Opus); `logging-flow`
  (3 large files) costs +12–15%, inside the spread below.
- **Between-batch spread, free.** The four one-file cases never triggered the hook, so on
  and off ran identical code, yet their medians differ by up to +43% (Sonnet `big-log`)
  and ±12% (Opus). This is not only sampling noise: on and off ran as separate
  sequential batches, the Sonnet `big-log` cost ranges do not overlap (on 0.074–0.079,
  off 0.053–0.055), and all three on-runs issued the same 13 KB command that no off-run
  did. Read any cost delta inside that spread as unproven; next time, interleave the
  arms in one job list.

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
Main context: −33% to −90% on every case but Sonnet `email-headers` (+35%). Cost: a clear
fall on `email-survey` (−49% Sonnet, −17% Opus); every other change, from +36% (Sonnet
`email-headers`) to −22%, is inside the between-batch spread above. Latency is the cost:
+6 to +78 s per broad question.

## Summary table (medians, cost min-max; `python3 bench/summary.py <tags>`)

`bench/runs/` is untracked, so this table is the lasting record. `pass` counts against
`expect`: off arms fail cases that expect a scout by design.

```
tag        case                    scout  pass     cost       min-max  haiku     raw  brief tools  secs badcite
h0         big-edit                0/3    3/3     0.034  0.033-0.034   0.000     250      0   2.0    18 0/0
h0         big-log                 0/3    3/3     0.078  0.074-0.079   0.000   16763      0   3.0    37 0/0
h0         configparser-explain    0/3    3/3     0.090  0.079-0.091   0.000   19942      0   6.0    31 0/0
h0         configparser-signatures 0/3    3/3     0.067  0.058-0.069   0.000    7263      0   4.0   275 0/0
h0         logging-flow            3/3    3/3     0.075  0.062-0.082   0.014    5443   4170   3.0    61 0/39
h0         unittest-flow           3/3    3/3     0.073  0.072-0.076   0.006    5682   3331   2.0    52 1/83
h0-opus    big-edit                0/3    3/3     0.070  0.068-0.070   0.000     230      0   2.0    13 0/0
h0-opus    big-log                 0/3    3/3     0.156  0.135-0.163   0.000    7707      0   4.0    41 0/0
h0-opus    configparser-explain    0/3    3/3     0.200  0.176-0.213   0.000   25581      0   3.0    41 0/0
h0-opus    configparser-signatures 0/3    3/3     0.127  0.123-0.200   0.000    5850      0   4.0    31 0/0
h0-opus    logging-flow            2/3    3/3     0.182  0.134-0.218   0.006    5843   3903   3.0    44 0/28
h0-opus    unittest-flow           3/3    3/3     0.174  0.156-0.187   0.008    6506   4165   3.0    84 0/113
h0off      big-edit                0/3    3/3     0.034  0.034-0.039   0.000     250      0   2.0    19 0/0
h0off      big-log                 0/3    3/3     0.055  0.053-0.055   0.000    4789      0   3.0    33 0/0
h0off      configparser-explain    0/3    3/3     0.084  0.079-0.098   0.000   19579      0   5.0    34 0/0
h0off      configparser-signatures 0/3    3/3     0.051  0.044-0.068   0.000    3887      0   3.0    25 0/0
h0off      logging-flow            0/3    3/3     0.065  0.060-0.069   0.000   12330      0   3.0    23 0/0
h0off      unittest-flow           0/3    0/3     0.111  0.104-0.127   0.000   31428      0   5.0    40 0/0
h0off-opus big-edit                0/3    3/3     0.071  0.067-0.076   0.000     248      0   2.0    12 0/0
h0off-opus big-log                 0/3    3/3     0.155  0.144-0.186   0.000    7859      0   5.0    38 0/0
h0off-opus configparser-explain    0/3    3/3     0.227  0.195-0.229   0.000   37105      0   4.0    42 0/0
h0off-opus configparser-signatures 0/3    3/3     0.121  0.111-0.128   0.000    7070      0   3.0    29 0/0
h0off-opus logging-flow            0/3    3/3     0.163  0.156-0.178   0.000   15505      0   4.0    37 0/0
h0off-opus unittest-flow           0/3    0/3     0.293  0.271-0.323   0.000   39351      0   6.0    53 0/0
r3         email-headers           3/3    3/3     0.069  0.066-0.071   0.005    5411   3373   3.0    42 0/22
r3         email-survey            3/3    3/3     0.078  0.078-0.079   0.009    5641   3924   2.0    64 1/75
r3         json-flow               3/3    3/3     0.071  0.069-0.071   0.003    5093   3376   2.0    36 0/74
r3         specs-history           3/3    3/3     0.071  0.069-0.073   0.014    5701   3984   2.0    82 0/14
r3-opus    email-headers           3/3    3/3     0.122  0.118-0.147   0.007    7032   5083   2.0    62 0/29
r3-opus    email-survey            3/3    3/3     0.200  0.191-0.214   0.010   14108   6508   4.0    95 0/111
r3-opus    json-flow               2/3    3/3     0.200  0.199-0.203   0.003   14748   4093   4.0    58 0/39
r3-opus    specs-history           3/3    3/3     0.210  0.195-0.214   0.013   18695   6743   5.0   119 1/24
r3off      email-headers           0/3    0/3     0.051  0.049-0.057   0.000    4024      0   3.0    21 0/0
r3off      email-survey            0/3    0/3     0.154  0.124-0.175   0.000   53788      0   8.0    42 0/0
r3off      json-flow               0/3    3/3     0.090  0.069-0.094   0.000   15462      0   5.0    30 0/0
r3off      specs-history           0/3    0/3     0.078  0.076-0.078   0.000   13915      0   3.0    28 0/0
r3off-opus email-headers           0/3    0/3     0.136  0.134-0.162   0.000   10448      0   4.0    32 0/0
r3off-opus email-survey            0/3    0/3     0.242  0.239-0.269   0.000   34610      0   5.0    48 0/0
r3off-opus json-flow               0/3    3/3     0.195  0.193-0.201   0.000   23793      0   4.0    39 0/0
r3off-opus specs-history           0/3    0/3     0.250  0.249-0.314   0.000   39687      0   5.0    41 0/0
```

## Scout citations

`route_eval` now checks every `path:line` in a brief against the fixture. 3 bad out of
651, all ranges running past end of file by 1–21 lines (`suite.py:375-400` on a
379-line file). No invented file. The first pass flagged 22 more: the scout writes
`v1-2-size-gated-nudge.md:18` for `2026-07-06-v1-2-size-gated-nudge.md`, which the
checker now resolves.

## Field audit (real sessions, free)

`python3 bench/field_audit.py --since 2026-10-10`, the author's own sessions with the
plugin installed, bench runs excluded:

```
sessions 20, turns 82
denials 11: scout 1, retry 5, other 5, ended 0
scout briefs 5: median 3655 chars; no read after the brief in 2/5, median 2 reads
```

- Delegation after a denial is rare in real work: 1 scout, 5 retries of the same call
  (3 of them only reworded the Bash description), 5 other; 2 turns reached the scout later.
  Replaying the 11 denied commands through the current `broad-bash`: 10 still flagged,
  the heredoc false positive is gone since v0.3.1.
- Reads after a brief (Read/Grep/Glob, and Bash `cat`/`sed`/`grep`/…): 3 of 5 briefs were
  followed by the same 2 Bash reads, of `hooks/route` and `hooks/hooks.json`, outside the
  competitor repos the scouts covered (checked by hand). No covered file was re-read.
- Token buckets by role and model are in the full output. The scout's cache writes are
  all 5-minute, the main thread's all 1-hour.

## Large-file Read gate: not built

Competitors gate a whole-file `Read` of a large file (token-economy-kit around 10k
tokens, cheap-llm-router at 200 lines). The plan built that gate only if the main
model actually does it. Across all 72 held-out runs (4 cases built around one 48–54 KB file, plus
`logging`'s 83 KB `__init__.py`), neither Sonnet nor Opus read a large file whole. The
author's real sessions agree: since 2026-09-01, 157 sessions made 274 whole-file Reads
(no `offset`/`limit`) and 1 returned more than 40k characters. They grep, `sed -n`, or page
with `offset`/`limit` (Sonnet `configparser-explain`: 11 ranged Reads, never the whole
file). In these runs and sessions a whole-file gate has almost nothing to catch, so
`hooks/route` is unchanged.

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
