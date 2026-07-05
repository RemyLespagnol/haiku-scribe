# Haiku CodeGraph Scout Design

Date: 2026-07-05
Status: Evaluation-only proposal

## Goal

Evaluate a future separate `haiku-codegraph` agent that uses Haiku plus CodeGraph to produce compact code-navigation evidence maps before the main model reads or edits files.

This is not part of the base `haiku-scribe` MVP. The base `haiku-scribe` agent remains a simple read-only context compression worker with no MCP and no CodeGraph.

## Problem

Direct CodeGraph use by the main agent reduces some discovery cost, but any direct file reads still happen in the main model context. If the main model is Opus, Fable, or another expensive model, large reads remain expensive.

A separate Haiku scout could move code exploration and targeted evidence extraction to a cheaper model, returning only compact findings to the main model.

## Proposed Agent Boundary

`haiku-codegraph` is a graph scout, not a coding agent.

It may:

- use CodeGraph to identify symbols, files, callers, callees, and blast radius;
- return compact evidence maps;
- recommend exact direct reads for the main model;
- list unknowns and verification risks.

It must not:

- edit files;
- write files;
- run shell commands;
- browse the web;
- make final debugging conclusions;
- make final architecture or security decisions;
- produce final PR summaries;
- replace main-model verification.

## Strict Scout Protocol

The first protocol to benchmark is intentionally strict:

```text
Use CodeGraph only.
Do not use Read, Grep, Glob, Bash, or other tools.
Do not make final conclusions.
Return only candidate symbols, files, line ranges, call relationships, unknowns, and suggested direct reads.
```

The main model then reads only the suggested files or line ranges if needed.

## Output Contract

```md
## Evidence Map
- `path/to/file.py:line-line` — symbol or relationship

## Call / Impact Notes
- Caller/callee or blast-radius facts from CodeGraph.

## Unknowns
- Things the main model must verify by direct read.

## Suggested Direct Reads
- 1-5 targeted files or line ranges.
```

## Bench Decision Criteria

Treat `haiku-codegraph` as worth designing further only if strict-scout runs show:

- zero direct file reads in the scout phase;
- useful candidate files and symbols;
- fewer main-model direct reads than baseline;
- no unsupported final conclusions;
- fewer false claims than direct CodeGraph use by the main model.

Defer the agent if direct CodeGraph use by the main model captures most of the benefit with less ceremony.

## Current Bench Reading

The first code-first bench suggests:

- CodeGraph direct is already useful for code navigation.
- Simulated `haiku-codegraph` can improve edit-readiness, but the scout phase was not disciplined enough and read files too early.
- The next experiment should test the strict scout protocol on edit-readiness tasks.

