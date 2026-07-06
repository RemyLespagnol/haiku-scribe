# V1.2 Break-Even Sweep — automated, real-cost

Date: 2026-07-06
Method spec: `docs/superpowers/specs/2026-07-06-haiku-scribe-v1-2-benchmark-target.md`
Driver: `bench/run_headless.py` (headless `claude -p`, real transcripts, costs via `bench/cost.py` which reproduces official `/cost` to the cent). Raw data: `bench/runs/sweep.jsonl`.

## Design (after two invalidated attempts)

Two arms, flipped by (un)installing haiku-scribe against the real `~/.claude`:

- **raw** — uninstalled: no agent, no guidance, and `Task/Agent/Bash/Grep/Glob` hard-denied (`--disallowedTools`), so the main model must `Read` the file into its own context.
- **scout** — full v1.2 installed: main may delegate; shell/grep still denied.

Task: whole-file comprehension of a deterministic log fixture (level distribution, busiest component, ordered NEEDLE incidents, WARN correlation). Correctness auto-checked (all 5 `NEEDLE_TOKEN_i` must appear in the answer).

Two earlier designs were discarded as invalid, and the reasons matter:

1. **hook-on vs hook-off is not a delegation A/B.** With v1.2 installed, the CLAUDE.md guidance alone triggers delegation even with the nudge hooks disabled — both arms delegate, no baseline exists.
2. **A needle-hunt task never loads the file.** The model answers it with one `grep` at O(1) context regardless of size; measured costs were pure cache-order noise around the ~$0.28/session floor. Deny the shell and demand whole-file comprehension, or you measure nothing.

## Results (main model = Sonnet, then Sonnet 1M for the bracket)

Sonnet 200k, 5000 lines (smoke, n=1, raw ran cold):

| mode | real $ | raw→main | main reads | subagent | correct |
| --- | ---: | ---: | ---: | --- | --- |
| raw | 3.58 | 549k | 10 | none | yes |
| scout | 2.65 | 275k | 3 | 3× haiku-scribe ($0.38 haiku) | yes |

Sonnet **1M**, order-balanced bracket (n=1 per cell):

| size | mode | real $ | raw→main | main reads | subagent reads | correct |
| ---: | --- | ---: | ---: | ---: | ---: | --- |
| 500 | raw | 0.77 | 76k | 1 | 0 | yes |
| 500 | scout | **0.48** | 69k | 0 | 1 | yes |
| 10000 | scout | 3.68 | 420k | **9** | 24 | yes |
| 10000 | raw | **2.45** | **328k** | 10 | 0 | yes |

Delegation is proven per-run by `cost_by_model` (haiku cost present ⇔ the haiku-scribe subagent did the work; a general-purpose agent would bill sonnet).

## Findings

1. **At 10000 lines the v1.0 substitution failure returned.** The main delegated (24 scout reads) *and then re-read the whole file itself* (9 reads): +50% cost, +28% context vs raw. Structural cause: the task demands exact full-file statistics that a summary cannot guarantee, so the main does not trust the scout's answer and re-reads. Delegation without substitution is strictly worse than either alternative.
2. **The 5000-line scout "win" was the compaction tax, not scout efficiency.** raw@5000 on 200k-window Sonnet cost $3.58 (auto-compaction fired); raw@10000 on Sonnet 1M cost $2.45 — no compaction, and direct reading became cheaper than delegating again.
3. **At 500 lines the arms are within cache-order noise.** Neither dominates on small files.

## Verdict

v1.2 pays only inside a narrow window: the file must overflow the main model's context window (so raw pays the compaction tax) *and* the task must tolerate summary-level fidelity (so the main actually substitutes). Outside that window it is neutral (small files) or actively harmful (large files + detail-demanding tasks: double work). 1M-context main models shrink the window further.

All cells were `correct` — quality never degraded; the KPIs that move are $ and context.

## Limitations

n=1 per cell; sequential sessions share prompt cache, so $ comparisons carry order bias (the bracket alternates arm order to balance it; `raw_into_main` is order-invariant and is the primary KPI). `cost.py` does not model the >200k long-context premium; official `cli_cost` is recorded per run as cross-check and matched within cents everywhere.

## Open product question (not decided here)

Given the narrow win window, default-on nudging is hard to justify as-is. Options to evaluate next: gate the nudge on estimated material size vs main-model window; strengthen the agent contract so its output is *substitutable* for detail-demanding tasks (exact structured stats, per-section extracts); or demote v1.2 to opt-in. The `HAIKU_SCRIBE_HOOKS=off` kill-switch (added this session) covers the opt-out half regardless.
