# Task 05: Strict CodeGraph Scout

## Goal

Test whether a future `haiku-codegraph` scout can stay compact and avoid direct file reads while still giving the main agent enough evidence to prepare an edit.

This task exists because task 03 showed a useful answer but a flawed protocol: the simulated scout read files too early.

## Run Modes

- `agent-codegraph`: main agent uses CodeGraph directly before any direct reads.
- `simulated-haiku-codegraph-strict`: scout uses CodeGraph only, then main agent reads only suggested direct reads if needed.

## Prompt: agent-codegraph

```text
Use CodeGraph first before any direct file reads.

In `bench/fixtures/sample-cli`, suppose we want to add `Read(**/*credential*)` to the default deny rules and ensure the merge remains idempotent. Identify the smallest set of files and exact sections the main agent should read before editing. Do not edit files.
```

## Prompt: simulated-haiku-codegraph-strict Step 1

```text
Act as a future `haiku-codegraph` strict scout.

Use CodeGraph only. Do not use Read, Grep, Glob, Bash, or any non-CodeGraph tool.
Do not make final conclusions.

Return only:
## Evidence Map
## Call / Impact Notes
## Unknowns
## Suggested Direct Reads

Task: In `bench/fixtures/sample-cli`, suppose we want to add `Read(**/*credential*)` to the default deny rules and ensure the merge remains idempotent.
```

## Prompt: simulated-haiku-codegraph-strict Step 2

```text
Using only the strict scout evidence map above, inspect the minimum necessary files or line ranges and answer the task. Do not broaden the search unless the evidence map is insufficient. Do not edit files.
```

## Record

Record whether the strict scout:

- used zero direct file reads;
- avoided Bash, Grep, Glob, and non-CodeGraph tools;
- identified `default_agent_config`;
- identified `merge_deny_rules`;
- identified the test surface in `test_sample_cli.py`;
- separated unknowns from facts;
- avoided final conclusions before direct verification.

Record whether the step 2 answer:

- required fewer main-model direct reads than baseline task 03;
- corrected or avoided the direct CodeGraph false claim about idempotency;
- was edit-ready.

