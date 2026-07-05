# Task 04: Docs Control

## Goal

Keep one control task that measures document search rather than code navigation.

This task should not drive the CodeGraph decision. It exists to show whether CodeGraph helps or struggles when the repository question is mostly documentation-oriented.

## Run Modes

- `baseline-agent`: use ordinary file listing/search/reads. Do not use CodeGraph.
- `agent-codegraph`: call CodeGraph first, then read only targeted files or lines.
- `simulated-haiku-codegraph`: first produce a compact graph-oriented evidence map, then let the main agent inspect only suggested files or lines.

## Prompt

Using the Haiku Scribe docs in this repo, answer whether CodeGraph belongs in the base Haiku Scribe MVP or should remain a separate future agent. Return evidence paths and line ranges. Do not edit files.

## Record

Record whether the run found:

- the MVP exclusion of MCP and CodeGraph
- the future `haiku-codegraph` idea
- the distinction between `haiku-scribe` and `haiku-codegraph`
- any signs that docs-only lookup caused unnecessary reads

