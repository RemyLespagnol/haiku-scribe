# Task 02: Agent Config Impact Analysis

## Goal

Measure how well each mode identifies the blast radius of changing the agent configuration shape.

## Run Modes

- `baseline-agent`: use ordinary file listing/search/reads. Do not use CodeGraph.
- `agent-codegraph`: call CodeGraph first, then read only targeted files or lines.
- `simulated-haiku-codegraph`: first produce a compact graph-oriented evidence map, then let the main agent inspect only suggested files or lines.

## Prompt

In `bench/fixtures/sample-cli`, identify what would be affected if `AgentConfig` changed the representation of `tools`, `disallowed_tools`, `model`, or `deny_rules`. Return callers, generated outputs, tests, and exact files or line ranges to inspect before editing. Do not edit files.

## Record

Record whether the run found:

- `AgentConfig`
- `default_agent_config`
- `render_agent_markdown`
- `install_config`
- `doctor_report`
- `tests/test_sample_cli.py`

