# Haiku Scribe V1.2 — Benchmark Target & Break-Even Sweep

Date: 2026-07-06
Branch: `feat/v1-2-default-hooks`
Status: spec (supersedes the ad-hoc measurement in `docs/superpowers/evaluations/2026-07-06-v1-2-default-hooks-bench.md`)

## Why this exists

The existing V1.2 measurement is not trustworthy:

- It compares **different conversations of different lengths** (baseline 10 assistant
  messages vs Run A 20), so it measures conversation length, not the hooks.
- The only real number is the baseline `$1.04` (official `/cost`). The V1.2 costs
  (`$2.75`, `$2.06`) are **hand estimates** — `/cost` was never captured for those runs.
- The fixture (`bench/fixtures/sample-cli`, ~6 tiny files) is a scenario where a
  read-only Haiku scout can **never** pay off: delegation overhead is fixed, and there
  is no heavy context to amortize it against.

Conclusion: we do not currently know whether V1.2 saves anything. This spec defines a
falsifiable target and a controlled sweep to find the break-even point ("spot point").

## Target: what V1.2 must achieve

V1.2 should help on **heavy-context** tasks:

- large repo survey (locate a feature / grasp architecture in a repo you don't know);
- large logs / stack traces / CI output;
- large generated files (bundles, schemas, migrations, big JSON/CSV, transcripts);
- large multi-file review.

**"Win" = all three at once (speed is not a goal):**

1. **Real $ saved** — lower total session cost, measured on real `/cost`.
2. **Context preserved** — fewer raw tokens injected into the main session's window.
3. **Quality maintained** — same correctness as reading everything directly.

A V1.2 variant is good only if, on these tasks, it lowers cost **and** lightens the main
window **without** degrading quality. Miss any one → the variant fails.

## The real lever is substitution, not economics

Analytically, if a scout's summary is ~10% of the source, delegating the read to Haiku is
almost always cheaper — **provided the main session then stops reading the raw material.**

The current measurement shows the opposite: the main session saved 0–2 reads, i.e. it read
the raw material *plus* the summary (additive, not substitutive). So the two levers that
decide break-even are:

1. **Context size N** of the material being read.
2. **Substitution rate** — does the main session skip the raw read once it has the summary?

The current guidance nudges delegation but never says *"do not re-read what the scout
covered."* That, not raw Haiku price, is the suspected root cause.

## Metrics — measure per run

| Metric | Source | KPI it serves |
| --- | --- | --- |
| Real cost ($) | sum of transcript `usage` fields × calibrated price formula | $ saved |
| Raw tokens into main | main-session `cache_creation_input_tokens` | context preserved |
| Correct answer (pass/fail) | manual judgment on the deliverable | quality |
| Substitution rate | main reads on the raw material *after* the summary returns | diagnostic |

Price formula (calibrated: reproduces the official baseline `$1.04`):

- Sonnet 5 main: `(input*3 + cache_write_1h*6 + cache_read*0.30 + output*15) / 1e6`
- Haiku 4.5 subagent: `(input*1 + cache_write_5m*1.25 + cache_read*0.10 + output*5) / 1e6`

Cost is the **sum of main + subagent** transcripts. No estimation of missing `/cost` —
every run's cost comes from summing that run's real `usage` records.

## The sweep — start on the single-large-file axis

Of the four scenarios, a **single large file** (log or generated) is the cleanest place to
find the spot point: it is the only one where N varies cleanly and in isolation.

- Fixture: one generated file at increasing sizes — **~500 / 2k / 5k / 10k lines**.
- Task: a fixed question answerable from that file (e.g. "find the N occurrences of X and
  summarize the surrounding context").
- Arms: **hook-on** (delegate to `haiku-scribe`) vs **hook-off** (main reads directly).
- Repetition: 3 runs per (size × arm); report the **median** to damp non-determinism.
- Output: a curve of real cost vs N per arm → the crossover N is the spot point.
- Alongside cost, record raw-tokens-into-main and the pass/fail correctness, and the
  substitution rate, so the curve is explained, not just observed.

Only once the single-file threshold is known do we extend to repo survey, multi-file
review, and log debugging — those have too much variance to isolate a threshold first.

## Tooling to build (in order)

1. **Cost extractor** — reads a session `.jsonl`, sums real `usage` per model, applies the
   calibrated formula, returns real $ and raw-tokens-into-main. Kills the hand-estimation
   error. (~40 lines; the one piece of real tooling that matters.)
2. **Fixture generator** — emits the large file at the target sizes, deterministically.
3. **Sweep runner / recorder** — records one JSONL line per run (reuse the existing
   `bench/report.py` format; add the real-cost fields from the extractor).

## Non-goals

- No automated launching of Claude Code sessions — runs stay operator-driven; only the
  measurement is automated (removes the manual `/cost` transcription error).
- No trigger/nudge/budget tuning until the sweep shows where and whether delegation wins.
- Default-on stays **out of scope** here: this spec decides *whether* V1.2 earns default-on,
  it does not assume it.
