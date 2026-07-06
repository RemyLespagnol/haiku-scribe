# Haiku Scribe V1.2 Default Hooks Benchmark

Date: 2026-07-06
Setup path: `haiku-scribe setup`
Model: Sonnet 5 for all sessions

Compared sessions:
- Haiku Scribe uninstalled baseline: `4285e825-2bfb-4688-9bf3-530002b0d5b8`
- Earlier Haiku Scribe uninstalled run: `896e7357-1192-49bb-856e-f0da49965981`
- V1.2 default hooks run A: `2eb989db-e0c8-4ef5-bcc8-743e7e860f4f`
- V1.2 default hooks run B: `92d6eebc-b94c-4cd2-bfd8-4b0a13f9a641`
- Historical benchmark context: `docs/superpowers/evaluations/2026-07-05-codegraph-agent-bench.md`

## Results

| Metric | Uninstalled Baseline | V1.2 Hooks Run A | V1.2 Hooks Run B |
| --- | --- | --- | --- |
| Session ID | `4285e825-2bfb-4688-9bf3-530002b0d5b8` | `2eb989db-e0c8-4ef5-bcc8-743e7e860f4f` | `92d6eebc-b94c-4cd2-bfd8-4b0a13f9a641` |
| First `cache_creation_input_tokens` | 34,081 | 35,086 | 44,453 |
| Total `cache_creation_input_tokens` | 146,500 from `/cost` | 329,071 | 254,612 |
| Total `cache_read_input_tokens` | 390,300 from `/cost` | 786,252 | 491,476 |
| Output tokens | 3,200 from `/cost` | 7,856 | 4,526 |
| Main assistant usage messages | 10 | 20 | 12 |
| Main-session tool calls | 3 `codegraph_explore`; 5 `Bash`; 5 `Read` | 2 `codegraph_explore`; 4 `Bash`; 1 `AskUserQuestion`; 3 `Read`; 1 `Agent` | 3 `codegraph_explore`; 2 `Bash`; 5 `Read`; 1 `Agent` |
| Subagent messages | none | 1 `Agent`; 22 assistant messages in `haiku-scribe` | 1 `Agent`; 33 assistant messages in `haiku-scribe` |
| Direct reads | 5 main-session `Read`; 0 subagent `Read` | 3 main-session `Read`; 10 subagent `Read` | 5 main-session `Read`; 13 subagent `Read` |
| Subagent extra exploration tools | none | 5 `Glob` | 6 `Grep`; 2 `Glob` |
| Final subagent response size | n/a | 567 words; 6,878 chars | 277 words; 3,408 chars |
| Official `/cost` output | $1.04 | not captured | not captured |
| Estimated API cost | $1.04 from `/cost` | $2.748415 | $2.057721 |
| Estimated cost breakdown | $1.04 official total | $2.328262 main Sonnet + $0.420153 subagent Haiku | $1.743077 main Sonnet + $0.314644 subagent Haiku |

## Cost Method

The baseline session has official Claude `/cost` output:

```text
Total cost:            $1.04
Usage by model:
     claude-sonnet-5:  18 input, 3.2k output, 390.3k cache read, 146.5k cache write ($1.04)
```

That official output matches the standard Sonnet-family price shape:

- input: $3 / MTok
- 1-hour cache write: $6 / MTok
- cache hit: $0.30 / MTok
- output: $15 / MTok

The V1.2 sessions do not have captured `/cost` output. Their main-session cost estimates use the same effective Sonnet 5 rate as the baseline `/cost` output:

`(input_tokens * 3 + ephemeral_1h_cache_write_tokens * 6 + cache_read_input_tokens * 0.30 + output_tokens * 15) / 1_000_000`

The V1.2 subagent transcripts use `claude-haiku-4-5-20251001`, so subagent cost is estimated with Haiku 4.5 rates:

`(input_tokens * 1 + ephemeral_5m_cache_write_tokens * 1.25 + cache_read_input_tokens * 0.10 + output_tokens * 5) / 1_000_000`

The V1.2 main-session cache writes are `ephemeral_1h_input_tokens`. The V1.2 Haiku subagent cache writes are `ephemeral_5m_input_tokens`.

## Cost Comparison

| Metric | V1.2 Run A vs Baseline | V1.2 Run B vs Baseline |
| --- | --- | --- |
| Estimated cost delta | +$1.708415 (+164.3%) | +$1.017721 (+97.9%) |
| Total `cache_creation_input_tokens` delta | +182,571 (+124.6%) | +108,112 (+73.8%) |
| Total `cache_read_input_tokens` delta | +395,952 (+101.4%) | +101,176 (+25.9%) |
| Main assistant usage messages delta | +10 (+100.0%) | +2 (+20.0%) |
| Main-session `Read` calls delta | -2 | 0 |
| Subagent `Read` calls delta | +10 | +13 |

## Hook Observations

- Run A `PreToolUse` nudged once per prompt: yes. The nudge log has two prompt IDs and each has one `nudge` plus one `pre_tool_followup`.
- Run B `PreToolUse` showed duplicate follow-up for the first prompt: the nudge log has two `pre_tool_followup` events for prompt `0d2d3648-a62f-4390-bde2-721e1c9ac142`, both at `2026-07-06T13:16:53Z`, plus one follow-up for the second prompt. This suggests a duplicate hook invocation or concurrent event race.
- `haiku-scribe` avoided self-nudging in both V1.2 runs: no extra subagent nudge event was recorded.
- Run A stayed within intended exploration budget: 10 subagent `Read` calls and 5 `Glob` calls.
- Run B exceeded the stop-around-15 spirit if main and subagent reads are combined: 5 main-session `Read` calls plus 13 subagent `Read` calls. The subagent alone stayed under 15 reads.
- With Haiku Scribe uninstalled, no matching nudge events were recorded for session `4285e825-2bfb-4688-9bf3-530002b0d5b8`.

## Notes

The sessions are all Sonnet 5 sessions, but they are not identical executions. The uninstalled baseline used no subagent. Run A used `haiku-scribe` after hook nudges but included extra main-session discovery and verification (`Bash`, `AskUserQuestion`, direct `Read`). Run B was shorter than Run A in messages and final subagent response size, but still costlier than the uninstalled baseline by estimated API cost.

This comparison is useful as observed workflow evidence, not as a controlled A/B measurement of only hook overhead.

Metrics were extracted from:
- baseline main transcript: `~/.claude/projects/-Users-lespagnolremy-dev-formats/4285e825-2bfb-4688-9bf3-530002b0d5b8.jsonl`
- Run A main transcript: `~/.claude/projects/-Users-lespagnolremy-dev-formats/2eb989db-e0c8-4ef5-bcc8-743e7e860f4f.jsonl`
- Run A subagent transcript: `~/.claude/projects/-Users-lespagnolremy-dev-formats/2eb989db-e0c8-4ef5-bcc8-743e7e860f4f/subagents/agent-a3123f3b30757a4a6.jsonl`
- Run B main transcript: `~/.claude/projects/-Users-lespagnolremy-dev-formats/92d6eebc-b94c-4cd2-bfd8-4b0a13f9a641.jsonl`
- Run B subagent transcript: `~/.claude/projects/-Users-lespagnolremy-dev-formats/92d6eebc-b94c-4cd2-bfd8-4b0a13f9a641/subagents/agent-a99f7a4d7b1f83c12.jsonl`
- V1.2 nudge log: `~/.claude/haiku-scribe-nudges.jsonl`

Pricing source:
- Anthropic Claude Platform pricing, Sonnet 5 and Haiku 4.5 pricing plus prompt cache multipliers: `https://docs.anthropic.com/en/docs/about-claude/pricing`
