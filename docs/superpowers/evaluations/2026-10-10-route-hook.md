# Route hook: getting Sonnet and Opus to delegate unprompted

Date: 2026-10-10 · Claude Code 2.1.296 · Max subscription · driver `bench/route_eval.py`,
summary `bench/summary.py` (raw transcripts in `bench/runs/`, untracked).

Clean environment: `--setting-sources project,local` drops the user's global
`CLAUDE.md`, plugins and hooks. That confound sat under every earlier round
(`feat/read-gate`, rounds 1–6). Main session `--effort medium`, with the parent's
`CLAUDE_EFFORT` scrubbed. That variable was `xhigh` in the driving session and would
otherwise leak into the child runs. "raw" counts tool output entering the main
context, including a backgrounded scout's brief. Cost is list price (Max bills
usage, not dollars).

## Arms

| arm | mechanism |
|---|---|
| base | v0.2.0: description + onboarding note only |
| P | UserPromptSubmit keyword classifier → `additionalContext` hint |
| G | P + PreToolUse: on a keyword-flagged turn, deny the first exploratory call once |
| B (shipped) | no prompt classifier. PreToolUse judges the tool call: deny the first *broad* read of a turn once (recursive/wildcard search, 3+ files or a glob, `Glob **`, `Grep` on a directory, 4th distinct `Read`). An edit or scout call disarms the turn |

## Results: unprompted scout use

| arm | model | broad questions delegated | one-file tasks delegated |
|---|---|---|---|
| base | Sonnet | 0/4 | 0/2 |
| P | Sonnet | 1/4 | 0/2 |
| G (n=1–2) | Sonnet | 8/11 | 0/7 |
| G | Sonnet, user's real setup | 2/2 | 0/2 |
| G | broad prompt with no keyword (`email-headers`) | 0/1 | — |
| **B** (n=2) | **Sonnet** | **8/8** | **0/6** |
| base | Opus | 0/3 | 0/4 |
| **B** | **Opus** | **4/4** | **0/2** |

All runs answered correctly (keyword grade). `argparse-tour` (one 2.6k-line file;
a class/def grep answers it as cheaply as a scout) is scored either way and is left
out of the table.

## Cost, context, latency (B vs base, per question)

| case | model | cost | main raw chars | seconds |
|---|---|---|---|---|
| email-survey | Sonnet | 0.119 → 0.095 | 37,427 → 11,179 | 44 → 70 |
| specs-history | Sonnet | 0.083 → 0.074 | 16,031 → 8,442 | 42 → 56 |
| json-flow | Sonnet | 0.064 → 0.078 | 5,633 → 7,643 | 35 → 40 |
| email-survey | Opus | 0.223 → 0.212 | 29,578 → 15,791 | 48 → 97 |
| specs-history | Opus | 0.272 → 0.177 | 46,476 → 13,485 | 60 → 145 |
| json-flow | Opus | 0.199 → 0.181 | 23,483 → 14,750 | 50 → 66 |

- **Cost**: −5% to −35% when the material is broad. json-flow on Sonnet is the
  exception (+22%, more raw): the answer sits in two files, and Sonnet reading
  them directly was already frugal.
- **Context**: −37% to −71% on the broad cases. Opus still runs one targeted
  verification read after the brief (3–7k chars), despite the "do not re-read"
  instruction. Briefs ran 6–10k chars: the main model's delegation prompt asks for
  detail, and that overrides the scout's 1.5–3k budget.
- **Brief ceiling (B2)**: the agent body now caps the reply at ~2,500 chars (hard
  4,000) and states that "exact / line numbers / details" requests do not lift it.
  Briefs dropped from 5–10k to 3.5–6.7k chars. Main raw chars fell again (Sonnet
  email-survey 11.2k → 7.6k, specs 8.4k → 5.7k; Opus json-flow 14.8k → 9.8k,
  specs 13.5k → 10.9k), with cost flat or lower and delegation unchanged
  (Sonnet 7/8, the miss on json-flow which scores either way; Opus 3/3).
- **Latency**: +5 to +85 s per broad question. The scout's sequential tool turns
  are the main cost. The agent body now asks it to batch independent reads.

## Why behavior, not keywords

The keyword classifier (P/G) works on the prompts it was written for and misses the
rest. `email-headers` ("Which files in email/ deal with header parsing or folding,
and what does each one depend on?") has none of the words, so G stayed silent and
the model read everything itself. B fired on the same prompt 3/3, because the
model's own first move (`find . -name '*.py' | xargs wc -l`, `grep -rn`) is the
breadth signal. Replaying B's Bash classifier over the first Bash call of all 60
earlier transcripts: 0 false positives on the 19 one-file runs, 23/28 hits on broad
runs. The misses were a plain `ls -la specs/`, which is cheap and gets caught at
the next call.

## Review fixes (before the final run)

A code review of the two scripts found false "broad" calls on redirections and
pipes (`cat package.json 2>/dev/null | head`), multi-line commands that were never
split, quadratic awk time on huge heredocs (now skipped above 20k chars), repeated
denials under parallel tool calls (now an atomic `set -C` claim), and a deny that
could never disarm with an unwritable state dir (now fails open). All of these are
pinned in `test_route.py`, which passes on macOS sh/BSD awk and Debian dash/mawk.
Replaying the classifier over the first Bash call of 91 saved transcripts gave 1
false positive in 27 one-file runs (`grep -rn "def total" <dir>`, which costs one
retry) and 43/64 on broad runs.

## Final run (shipped files, n=1, all 8 cases)

| case | Sonnet base → final: cost / raw | Opus base → final: cost / raw |
|---|---|---|
| email-survey | 0.119 / 37.4k → 0.084 / 7.5k | 0.223 / 29.6k → 0.209 / 15.5k |
| specs-history | 0.083 / 16.0k → 0.069 / 5.9k | 0.272 / 46.5k → 0.191 / 12.6k |
| json-flow | 0.064 / 5.6k → 0.067 / 5.9k | 0.199 / 23.5k → 0.176 / 10.0k |
| email-headers | 0.059 / 4.2k → 0.067 / 6.0k | — → 0.138 / 9.7k |

Scout on 4/4 broad questions and 0/3 one-file tasks for both models, all answers
correct. Across B, B2 and final: Sonnet delegated on 19 of 20 broad questions and
Opus on 11 of 11, against 0 of 7 without the hook. Neither delegated on any of the
14 one-file runs. Where Sonnet already answers a broad-sounding question from a
couple of grepped slices (json-flow, email-headers), delegating costs about the
same or slightly more. The gains are on genuinely broad material, and on Opus
across the board. 111 sessions in total, $9.91 at list price.

## Limits

- n=1–2 per cell; the routing result (0/12 → 12/12 across both models) is far
  outside that noise, but the cost and latency deltas are not.
- Coding turns: a 4th distinct `Read` before any edit is denied once. Not measured
  on a multi-turn implementation task. The deny text tells the model to retry when
  it needs files verbatim, and the first edit disarms the turn.
- One-shot `-p` runs only. Interactive sessions reset state on each user prompt.
