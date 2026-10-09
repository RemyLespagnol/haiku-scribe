# Haiku 5.5 — scout effort pin

Date: 2026-10-09 · Claude Code 2.1.295 · Max subscription · n=2 per cell. Driver:
`bench/route_eval.py` from the unmerged `feat/read-gate` branch (not on `main`);
raw transcripts stay untracked.

`model: haiku` now resolves to `claude-haiku-5-5` ($0.10 / $0.50 per MTok up to 100K
prompt, vs $1 / $5 for Haiku 4.5). The Haiku 4.5 arm sets
`ANTHROPIC_DEFAULT_HAIKU_MODEL=claude-haiku-4-5`, the model Bedrock and Vertex still
serve. Two questions: explain `json.dumps` across the stdlib `json/` package
(`json-flow`), and trace a position across 13 design specs (`specs-history`).
`direct` is the main model told to read the files itself; scout arms tell it to
delegate. "effort" is the main session's (`--effort`) unless the frontmatter pins it.

Main model Sonnet 5.5:

| arm | case | total $ | Haiku $ | Haiku thinking tok | main raw chars | spec files read |
|---|---|--:|--:|--:|--:|---|
| direct | json-flow | 0.198 | — | — | 26,028 | — |
| Haiku 4.5 | json-flow | 0.202 | 0.045 | 1,044 | 7,203 | — |
| 5.5, session medium | json-flow | 0.166 | 0.0065 | 2,374 | 9,138 | — |
| 5.5, session xhigh | json-flow | 0.195 | 0.019 | 22,094 | 11,266 | — |
| 5.5, pinned low | json-flow | 0.163 | 0.0057 | 1,158 | 7,471 | — |
| 5.5, pinned medium, session xhigh | json-flow | 0.174 | 0.0069 | 2,244 | 9,358 | — |
| direct | specs-history | 0.220 | — | — | 36,926 | 4/4 |
| Haiku 4.5 | specs-history | 0.244 | 0.092 | 2,124 | 6,510 | 13/13 |
| 5.5, session medium | specs-history | 0.185 | 0.024 | 22,022 | 13,310 | 13/13 |
| 5.5, session xhigh | specs-history | 0.267 | 0.090 | 64,648 | 15,582 | 13/13 |
| 5.5, pinned low | specs-history | 0.172 | 0.012 | 7,966 | 8,938 | 13/4 |
| 5.5, pinned medium, session xhigh | specs-history | 0.177 | 0.020 | 16,486 | 11,156 | 13/13 |

Main model Opus 5.5 (session medium, pinned agent):

| arm | case | total $ | Haiku $ | main raw chars | spec files read |
|---|---|--:|--:|--:|---|
| direct | json-flow | 0.403 | — | 29,198 | — |
| scout | json-flow | 0.358 | 0.0069 | 12,015 | — |
| direct | specs-history | 0.445 | — | 40,288 | 4/3 |
| scout | specs-history | 0.319 | 0.022 | 12,536 | 13/13 |

All 33 runs answered correctly (keyword grade).

- **Without a pin, the scout inherits the session's effort.** At `xhigh` Haiku 5.5
  thinks 9x (json) and 3x (specs) more, the Haiku bill triples to quadruples, and
  specs-history costs more than reading directly ($0.267 vs $0.220). Haiku 4.5 has no
  effort levels, so this was not a lever before.
- **`low` cut a named scope short.** One of two specs runs read 4 of 13 files after a
  grep and listed the other 9 as unread. The coverage statement was honest, but a
  partial extract invites the main model to re-read. `medium` read 13/13 every time.
- **Decision: `effort: medium` in the frontmatter.** Under an `xhigh` session, Haiku
  thinking matches session-medium levels. With `haiku` resolved to Haiku 4.5 the
  field is accepted without error (one run, PASS).
- **With the pin, delegating is cheaper than reading directly**: -16% under Sonnet
  5.5, -11% and -28% under Opus 5.5, with main raw content down ~60–70%. Haiku 4.5
  stays at +2% and +11%.
- Measurement note: Claude Code now backgrounds some Agent calls. The `tool_result`
  is then a ~1.1k-char launch stub and the brief arrives in a `task_notification`
  event; "main raw chars" counts that brief.
