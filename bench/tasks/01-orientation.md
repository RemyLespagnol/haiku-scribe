# Task 01: Setup Flow Orientation

## Goal

Trace the sample CLI setup flow from public entrypoint to generated agent file and merged settings.

## Run Modes

- `baseline-agent`: use ordinary file listing/search/reads. Do not use CodeGraph.
- `agent-codegraph`: call CodeGraph first, then read only targeted files or lines.
- `simulated-haiku-codegraph`: first produce a compact graph-oriented evidence map, then let the main agent inspect only suggested files or lines.

## Prompt

In `bench/fixtures/sample-cli`, trace how `install_config` writes the Haiku Scribe agent file and settings file. Return the smallest set of files and line ranges needed to understand the setup flow. Do not edit files.

## Record

Record whether the run found:

- `install_config`
- `default_agent_config`
- `render_agent_markdown`
- `merge_deny_rules`
- the final `InstallResult`

