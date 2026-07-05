# CodeGraph Agent Bench

This is a semi-manual benchmark for evaluating whether CodeGraph helps an agent reduce context usage and improve navigation precision.

The bench is code-first. The primary target is `bench/fixtures/sample-cli`, a small Python fixture with real symbols and call paths. `bench/tasks/04-docs-control.md` is only a control for documentation-heavy lookup.

## Modes

- `baseline-agent`: use ordinary exploration tools without CodeGraph.
- `agent-codegraph`: call CodeGraph before direct file reads or search.
- `simulated-haiku-codegraph`: simulate a separate graph-oriented worker by first producing a compact evidence map, then reading only the suggested files or lines.
- `simulated-haiku-codegraph-strict`: scout uses CodeGraph only and must not call Read, Grep, Glob, Bash, or other tools before handing an evidence map to the main agent.

## Recording Runs

Create JSONL files under `bench/runs/`. One line equals one run:

```json
{"task_id":"01-orientation","mode":"agent-codegraph","date":"2026-07-05","tool_calls":4,"direct_file_reads":1,"large_outputs":0,"files_surfaced":["bench/fixtures/sample-cli/haiku_scribe_sample/installer.py"],"line_evidence_count":3,"found_right_area":true,"edit_ready":false,"estimated_context_cost":"low","accuracy_notes":"Found setup flow with one targeted read.","friction_notes":"CodeGraph query was precise."}
```

Use `estimated_context_cost` values `low`, `medium`, or `high`. These are context proxies, not exact token counts.

## Report

Generate a report:

```bash
python3 bench/report.py
```

The report aggregates by task and mode:

- average tool calls;
- average direct file reads;
- average large outputs;
- average line evidence count;
- found-right-area pass rate;
- edit-ready pass rate;
- context-cost distribution.
- average gross tokens;
- average no-cache tokens;
- average input, output, cache-creation, and cache-read tokens.

Token fields are optional but recommended when runs come from Claude transcript IDs. Use:

- `input_tokens`
- `output_tokens`
- `cache_creation_tokens`
- `cache_read_tokens`
- `gross_tokens`
- `no_cache_tokens`

`gross_tokens` is a workload/context proxy. `no_cache_tokens` is `input_tokens + output_tokens` and intentionally excludes cache reads and cache writes. Real billing may weight cache creation and cache reads differently, so do not treat either column as exact cost.

## Decision Rule

CodeGraph is promising if `agent-codegraph` or `simulated-haiku-codegraph` consistently reduces direct file reads or large outputs while preserving or improving navigation quality.

Defer a separate `haiku-codegraph` agent if direct CodeGraph use by the main agent captures most of the benefit with less ceremony.

Use `bench/tasks/05-strict-scout.md` before designing a real `haiku-codegraph` agent. The strict scout must show useful evidence maps with zero direct file reads in the scout phase.
