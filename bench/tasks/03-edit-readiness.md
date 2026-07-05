# Task 03: Deny Rule Edit Readiness

## Goal

Evaluate whether each mode can find the minimum context needed before editing deny-rule handling.

## Run Modes

- `baseline-agent`: use ordinary file listing/search/reads. Do not use CodeGraph.
- `agent-codegraph`: call CodeGraph first, then read only targeted files or lines.
- `simulated-haiku-codegraph`: first produce a compact graph-oriented evidence map, then let the main agent inspect only suggested files or lines.

## Prompt

In `bench/fixtures/sample-cli`, suppose we want to add `Read(**/*credential*)` to the default deny rules and ensure the merge remains idempotent. Identify the smallest set of files and exact sections the main agent should read before editing. Do not edit files.

## Record

Record whether the run found:

- where default deny rules are declared
- where deny rules are merged
- where settings are written
- where doctor validates missing deny rules
- the test that should change or be added

