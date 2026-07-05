# CodeGraph Agent Bench Evaluation

Date: 2026-07-05
Status: Code-first runs complete

## Hypothesis

CodeGraph may reduce context usage and improve navigation precision when the task involves code symbols, call paths, or blast radius analysis.

The benchmark should include token usage, not only tool calls. Tool calls are a useful workflow proxy, but token usage better reflects cost pressure when the main model is expensive.

## Token Notes

The report now tracks:

- `gross_tokens`: input + output + cache creation + cache read tokens.
- `no_cache_tokens`: input + output tokens only.
- cache creation and cache read tokens separately.

These are local transcript metrics, not exact billing. Real pricing may weight cache creation and cache reads differently. The current test sessions appear to run on Haiku, so they do not fully model the intended Opus/Fable-main plus Haiku-scout economic split.

## Report Snapshot

| Task | Mode | Tool Calls | Direct Reads | Gross Tokens | No-Cache Tokens | Edit Ready |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| 01-orientation | baseline-agent | 5 | 3 | 174394 | 1517 | No |
| 01-orientation | agent-codegraph | 4 | 3 | 144554 | 1666 | No |
| 01-orientation | simulated-haiku-codegraph | 4 | 3 | 147744 | 2522 | No |
| 02-impact-analysis | baseline-agent | 10 | 6 | 339704 | 2569 | Yes |
| 02-impact-analysis | agent-codegraph | 9 | 5 | 225055 | 4318 | Yes |
| 02-impact-analysis | simulated-haiku-codegraph | 6 | 5 | 192449 | 4204 | Yes |
| 03-edit-readiness | baseline-agent | 4 | 3 | 108837 | 1479 | No |
| 03-edit-readiness | agent-codegraph | 1 | 0 | 72125 | 1160 | No |
| 03-edit-readiness | simulated-haiku-codegraph | 7 | 4 | 264949 | 4116 | Yes |
| 05-strict-scout | agent-codegraph | 7 | 4 | 261807 | 3429 | Yes |
| 05-strict-scout | simulated-haiku-codegraph-strict | 22 | 3 | 1044730 | 7632 | Yes |

## Observations

CodeGraph direct is consistently useful enough to keep in the main agent workflow. It reduces discovery friction, avoids irrelevant reads in some tasks, and can eliminate direct reads for narrow questions.

The strict scout protocol achieved the important safety boundary: zero direct reads in scout phase. However, the strict scout used too many CodeGraph calls. On task 05, it reduced main-model direct reads from 4 to 3, but gross tokens increased from 261807 to 1044730 and no-cache tokens increased from 3429 to 7632.

The economic argument for a future `haiku-codegraph` still exists if the main model is Opus/Fable and the scout is Haiku. But the current prompt is not efficient enough. The scout must be bounded.

## Decision

Use CodeGraph directly for now.

Do not add CodeGraph to the base `haiku-scribe` MVP.

Do not build a separate `haiku-codegraph` agent yet. The next experiment should cap the scout to at most 3 CodeGraph calls, zero direct reads, and a compact evidence map. Only revisit a real agent if that version reduces main-model reads without exploding total token usage.

