# Haiku Scribe V0 Agent Simplification Design

Date: 2026-07-05
Status: Draft for review
Related docs:
- `docs/superpowers/specs/2026-07-04-v0-manual-subagent-design.md`
- `docs/superpowers/evaluations/2026-07-04-v0-manual-workflow-trials.md`
- `.claude/agents/haiku-scribe.md`

## Objective

Simplify the V0 `haiku-scribe` agent prompt so it fits the product goal: cheap read-only context compression before main-model reasoning.

The current V0 agent became too focused on output-shape compliance, transcript-specific rules, and self-validation. That makes the agent larger, more expensive to invoke, and harder to reason about. V0 should validate whether Haiku Scribe is useful as a workflow primitive, not whether a Haiku subagent can reliably behave like a deterministic formatter.

## Product Fit

Haiku Scribe should remain a small worker with this contract:

```text
Haiku Scribe reads cheaply.
Haiku Scribe returns a compact, evidence-oriented brief.
Main Claude verifies important claims before decisions or edits.
Later tooling can validate, report, or enforce formatting if needed.
```

The agent prompt should optimize for:

- low prompt overhead;
- clear read-only boundaries;
- useful summaries with citations when available;
- explicit uncertainty;
- focused direct-read recommendations for the main Claude session.

It should not optimize for machine-parseable output in V0.

## Diagnosis

The manual trials show that Haiku Scribe is useful for broad reading tasks:

- large document summarization;
- product and roadmap orientation;
- cross-file evidence mapping;
- scope evidence extraction.

The main failure mode is transcript/log output stability. The current response was to add more prompt rules, including exact heading checks, transcript-specific citation rules, and preflight validation. That solves the wrong problem at the wrong layer.

A subagent prompt is a weak place to enforce deterministic structure. If strict validation becomes important, it should move into V1+ tooling such as `doctor`, `extract`, golden tests, or a lightweight output checker. V0 should keep the agent small and measure whether the workflow saves useful context.

## Proposed Agent Contract

Rewrite `.claude/agents/haiku-scribe.md` around four short sections:

1. Role
2. Boundaries
3. How to read
4. Response shape

The agent should keep only these requirements:

- It is read-only context compression.
- It may use only `Read`, `Glob`, and `Grep`.
- It must not edit, write, run shell commands, browse, use MCP, call agents, or make final decisions.
- It should summarize only the requested context.
- It should cite file paths and line numbers when available.
- It should separate observations from uncertainty.
- It should suggest a few direct reads only when the main Claude session needs exact context.

The response shape should be guidance, not a hard compliance engine:

```markdown
## Summary

## Evidence

## Unknowns / Risks

## Suggested Reads
```

The prompt should not include transcript/log-specific rules, exact heading-count checks, `## None.` templates, or a pre-send checklist.

## Evaluation Change

V0 should pass or fail on workflow usefulness:

- Did the main session avoid loading raw context it otherwise would have read?
- Was the returned brief specific enough to guide next action?
- Were citations or file references good enough for targeted verification?
- Did the workflow feel cheaper and clearer than direct reading?
- Did Haiku Scribe avoid forbidden work and final authority?

Transcript/log compression can remain a known limitation if it produces useful orientation but unstable formatting. It should not block V1 packaging by itself unless it makes the workflow worse or creates false confidence.

## Out Of Scope

This simplification does not add:

- setup;
- doctor;
- uninstall;
- hooks;
- reports;
- prompt nudges;
- enforcement;
- MCP;
- Codegraph;
- plugin packaging;
- team rollout.

It also does not create a parser, validator, or transcript extraction tool. Those belong in later specs if V0 validates the product value.

## Success Criteria

The simplification succeeds if:

- the agent prompt is materially shorter and easier to inspect;
- the V0 safety boundaries remain explicit;
- the agent still returns compact evidence-oriented summaries;
- evaluation language measures product usefulness instead of perfect format stability;
- V1 can be considered when the manual workflow is useful despite minor formatting variance.

## Recommended Next Step

After this design is approved, write an implementation plan that:

1. Replaces the current agent prompt with the simplified pragmatic contract.
2. Updates the V0 design doc to remove strict transcript/log compliance as a V1 blocker.
3. Updates the trial log gate language to evaluate workflow usefulness first.
4. Runs the existing V0 checks and adjusts them only where they enforce the old over-strict contract.
