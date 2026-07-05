# CodeGraph Agent Bench Design

Date: 2026-07-05
Status: Proposed

## Goal

Create a minimal benchmark harness to evaluate whether CodeGraph helps this agent reduce token/context usage and improve navigation precision while working on Haiku Scribe code.

The benchmark is not part of the Haiku Scribe MVP product. It is an evaluation scaffold for deciding whether a future separate `haiku-codegraph` agent is worth designing. The base `haiku-scribe` MVP remains read-only and does not gain MCP or CodeGraph access.

The bench must be code-first. CodeGraph is strongest when it can inspect symbols, call paths, and blast radius. A docs-only benchmark would mostly measure document search and would understate CodeGraph's real value.

## Modes Compared

The bench compares three workflow modes:

- `baseline-agent`: the main agent uses ordinary repository exploration tools without CodeGraph.
- `agent-codegraph`: the main agent calls CodeGraph before direct file reading or search.
- `simulated-haiku-codegraph`: the main agent follows a simulated delegation protocol where a graph-oriented worker first returns relevant symbols, files, and line evidence, then the main agent reads only targeted context.

## Benchmark Shape

Use a semi-manual bench. Each task is a markdown prompt that can be replayed in each mode. Each run is recorded as one JSONL object with measured and observed fields.

This avoids pretending we can reliably capture exact Claude token usage from inside the repo. Instead, it records stable proxies:

- number of direct file reads or large outputs;
- number of tool calls;
- files and line ranges surfaced;
- whether the first pass found the right area;
- whether the result was ready for editing;
- notes about false positives, reruns, and workflow friction.

The harness includes a small Python fixture codebase under `bench/fixtures/sample-cli/`. The fixture models a minimal Haiku Scribe-style installer with setup, doctor, uninstall, settings merge, agent markdown generation, and deny-rule validation. It exists only to give CodeGraph real code structure to index.

## Files

Create:

- `bench/tasks/01-orientation.md`
- `bench/tasks/02-impact-analysis.md`
- `bench/tasks/03-edit-readiness.md`
- `bench/fixtures/sample-cli/haiku_scribe_sample/__init__.py`
- `bench/fixtures/sample-cli/haiku_scribe_sample/agent_config.py`
- `bench/fixtures/sample-cli/haiku_scribe_sample/settings_merge.py`
- `bench/fixtures/sample-cli/haiku_scribe_sample/installer.py`
- `bench/fixtures/sample-cli/haiku_scribe_sample/doctor.py`
- `bench/fixtures/sample-cli/tests/test_sample_cli.py`
- `bench/runs/.gitkeep`
- `bench/report.py`
- `bench/README.md`
- `docs/superpowers/evaluations/2026-07-05-codegraph-agent-bench.md`

## Run Format

Each run in `bench/runs/*.jsonl` should use this shape:

```json
{
  "task_id": "01-orientation",
  "mode": "agent-codegraph",
  "date": "2026-07-05",
  "tool_calls": 4,
  "direct_file_reads": 1,
  "large_outputs": 0,
  "files_surfaced": ["docs/haiku_scribe_prd.md"],
  "line_evidence_count": 3,
  "found_right_area": true,
  "edit_ready": false,
  "estimated_context_cost": "low",
  "accuracy_notes": "Found the correct roadmap and MVP boundary.",
  "friction_notes": "CodeGraph query needed one retry because docs-only repo has little indexed code."
}
```

## Scoring

The report script aggregates runs by task and mode. It should produce a markdown table with:

- average tool calls;
- average direct file reads;
- average large outputs;
- average line evidence count;
- found-right-area pass rate;
- edit-ready pass rate;
- context-cost distribution.

The report should not claim exact token savings. It should frame results as context-usage proxies.

## Initial Tasks

Task 1, orientation:

Trace the sample CLI setup flow from the public setup entrypoint to agent file generation and settings merge. Return the smallest set of files and line ranges needed to understand it.

Task 2, impact analysis:

Identify the blast radius of changing the agent configuration shape, especially allowed tools, disallowed tools, model name, and generated markdown.

Task 3, edit readiness:

Given a proposed change to deny-rule handling, identify the smallest set of files and exact sections the main agent should inspect before editing.

Optional control task:

Use the existing docs to answer whether CodeGraph belongs in the base Haiku Scribe MVP. This task is useful as a docs-search control, not as the primary CodeGraph value test.

## Success Criteria

The bench is useful if it lets us compare at least five real code-oriented runs without changing product scope.

CodeGraph is considered promising if `agent-codegraph` or `simulated-haiku-codegraph` consistently reduces direct file reads or large outputs while preserving or improving navigation quality.

The separate `haiku-codegraph` idea should be rejected or deferred if the main agent using CodeGraph directly already captures most of the benefit with less ceremony.

## Non-Goals

- No automatic Claude transcript parsing.
- No exact token accounting.
- No MCP or CodeGraph access in the base `haiku-scribe` MVP.
- No autonomous benchmark runner that invokes Claude.
- No implementation of a real `haiku-codegraph` agent yet.
