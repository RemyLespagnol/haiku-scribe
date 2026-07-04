# Haiku Scribe V0 Manual Workflow Trials

Date: 2026-07-04
Agent under test: `.claude/agents/haiku-scribe.md`
Spec: `docs/superpowers/specs/2026-07-04-v0-manual-subagent-design.md`
Status: Not evaluated

## Trial Instructions

Use the `haiku-scribe` subagent manually in realistic Claude Code sessions. The main Claude session must keep final reasoning, edits, security conclusions, architecture conclusions, commit decisions, and public summaries.

For each trial, record whether Haiku Scribe reduced raw context loading pressure without making the workflow feel worse.

## Trial 1: Multi-File Repository Orientation

User request:

```text
Use haiku-scribe to map the documents and identify which files define the product direction, rollout sequence, and V0 scope. Return evidence and suggested direct reads.
```

Delegation reason:

- This requires reading three or more files for orientation.

Expected useful result:

- Summary identifies the roadmap, PRD, and skill PRD roles.
- Evidence points to exact files and lines when available.
- Suggested direct reads are limited to the most important roadmap and V0 sections.

Result:

- Outcome: Not run
- Raw context avoided: Not measured
- Evidence quality: Not measured
- Suggested direct reads quality: Not measured
- Main workflow impact: Not measured
- Notes: Not run yet

## Trial 2: Large Single-File Summarization

User request:

```text
Use haiku-scribe to summarize the roadmap document's version sequence, gates, and non-passage conditions without making any implementation recommendations.
```

Delegation reason:

- This asks for broad summarization of one large document.

Expected useful result:

- Summary captures each version's purpose.
- Evidence distinguishes V0 from later versions.
- Unknowns identify any ambiguous roadmap text.

Result:

- Outcome: Not run
- Raw context avoided: Not measured
- Evidence quality: Not measured
- Suggested direct reads quality: Not measured
- Main workflow impact: Not measured
- Notes: Not run yet

## Trial 3: Log Or Transcript Compression

User request:

```text
Use haiku-scribe to compress a noisy Claude Code transcript or command log into key decisions, open questions, and evidence. Do not make final conclusions.
```

Delegation reason:

- Noisy transcripts and logs are explicitly in scope for context compression.

Expected useful result:

- Summary removes noisy tool output.
- Evidence references transcript locations or message boundaries when available.
- Unknowns state where the log is incomplete.

Result:

- Outcome: Not run
- Raw context avoided: Not measured
- Evidence quality: Not measured
- Suggested direct reads quality: Not measured
- Main workflow impact: Not measured
- Notes: Not run yet

## Trial 4: Cross-File Flow Mapping

User request:

```text
Use haiku-scribe to map where the product says bulk reading starts, how evidence must be returned, and when the main model must take over. Provide only an evidence map.
```

Delegation reason:

- This requires connecting related rules across multiple documents before main-model reasoning.

Expected useful result:

- Summary maps the flow from delegation trigger to subagent output to main-model verification.
- Evidence references all relevant documents.
- Suggested direct reads identify exact rule sections for the main Claude session.

Result:

- Outcome: Not run
- Raw context avoided: Not measured
- Evidence quality: Not measured
- Suggested direct reads quality: Not measured
- Main workflow impact: Not measured
- Notes: Not run yet

## Trial 5: Evidence Extraction Before Debugging Or Design Reasoning

User request:

```text
Use haiku-scribe to extract evidence for whether V0 permits setup, doctor, uninstall, hooks, reports, nudges, enforcement, MCP, or Codegraph. Do not make the final scope decision.
```

Delegation reason:

- The main Claude session needs focused evidence before making a scope decision.

Expected useful result:

- Summary lists which capabilities are excluded from V0.
- Evidence points to the roadmap and V0 spec.
- Suggested direct reads let the main Claude session verify scope before writing a plan.

Result:

- Outcome: Not run
- Raw context avoided: Not measured
- Evidence quality: Not measured
- Suggested direct reads quality: Not measured
- Main workflow impact: Not measured
- Notes: Not run yet

## Final V0 Gate Decision

Product or usage gate:

- Status: Not evaluated
- Evidence: Run all five trials before setting this to pass or fail.

Technical or security gate:

- Status: Not evaluated
- Evidence: Review the subagent contract, forbidden capabilities, response shape, and manual trial behavior before setting this to pass or fail.

Decision:

- V0 status: Not evaluated
- V1 may open: No
- Reason: Manual trials have not been completed.
