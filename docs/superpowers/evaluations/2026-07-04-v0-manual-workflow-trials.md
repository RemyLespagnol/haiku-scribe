# Haiku Scribe V0 Manual Workflow Trials

Date: 2026-07-04
Agent under test: `.claude/agents/haiku-scribe.md`
Spec: `docs/superpowers/specs/2026-07-04-v0-manual-subagent-design.md`
Status: In evaluation

## Trial Instructions

Use the `haiku-scribe` subagent manually in realistic Claude Code sessions. The main Claude session must keep final reasoning, edits, security conclusions, architecture conclusions, commit decisions, and public summaries.

For each trial, record whether Haiku Scribe reduced raw context loading pressure without making the workflow feel worse.

## Trial 1: Claude Code Subagent Visibility Smoke Test

User request:

```text
Use the haiku-scribe subagent to summarize docs/haiku_scribe_skill_prd.md. Return only the required Haiku Scribe response sections.
```

Delegation reason:

- This verifies Claude Code can see and invoke the project-local `haiku-scribe` subagent.
- This asks for broad summarization of one PRD before main-model reasoning.

Expected useful result:

- Claude Code invokes `haiku-scribe`.
- Response uses only `Summary`, `Evidence`, `Unknowns And Risks`, and `Suggested Direct Reads`.
- The subagent summarizes without editing files or running shell commands.

Result:

- Trial pass/fail: Pass
- Files/artifact types inspected: `docs/haiku_scribe_skill_prd.md`
- Summary specificity: Specific enough to identify the product model, MVP exclusions, rollout sequence, output contract, and testing strategy.
- Raw context avoided: The main Claude session invoked `haiku-scribe` and did not directly load the full source document before receiving a compressed summary.
- Evidence quality: The response included concrete source references with line ranges.
- Suggested direct reads quality: The response recommended no direct reads because the PRD was complete and self-contained for the requested summary.
- Main workflow impact: Claude Code found and invoked `haiku-scribe` successfully; the response used the required four sections and did not edit files or run shell commands.
- Notes: Manual Claude Code visibility smoke test passed with `Done (1 tool use · 15.7k tokens · 17s)`.

## Trial 2: Large Single-File Summarization

User request:

```text
Use the haiku-scribe subagent to summarize docs/superpowers/specs/2026-07-04-haiku-scribe-roadmap-design.md.

Summarize only the version sequence, gates, and non-passage conditions. Do not make implementation recommendations. Return exactly the required Haiku Scribe response sections:
## Summary
## Evidence
## Unknowns And Risks
## Suggested Direct Reads
```

Delegation reason:

- This asks for broad summarization of one large roadmap document.

Expected useful result:

- Summary captures each version's purpose.
- Evidence distinguishes V0 from later versions.
- Unknowns identify any ambiguous roadmap text.

Result:

- Trial pass/fail: Pass
- Files/artifact types inspected: `docs/superpowers/specs/2026-07-04-haiku-scribe-roadmap-design.md`
- Summary specificity: Specific enough to capture the nine-version sequence, progression gates, and explicit non-passage conditions.
- Raw context avoided: The main Claude session delegated the roadmap read to `haiku-scribe` and received a compressed version/gate map instead of loading the whole roadmap directly.
- Evidence quality: Strong; the response cited line ranges for the version sequence and each version's gate/non-passage block.
- Suggested direct reads quality: Acceptable; the response recommended no direct reads because the requested roadmap summary was complete enough for the evaluation.
- Main workflow impact: Positive after rerun with explicit file path and required sections. The result was usable for roadmap orientation without implementation recommendations.
- Notes: Minor format issue: Claude Code wrapped the subagent output with `Here's the summary from haiku-scribe:` and headings were plain labels rather than markdown `##` headings, but the required section names and content were present.

## Trial 3: Log Or Transcript Compression

User request:

```text
Use the haiku-scribe subagent to compress docs/superpowers/evaluations/fixtures/noisy-claude-session-sample.md into key decisions, open questions, and evidence. Do not make final conclusions. Return exactly the required Haiku Scribe response sections.
```

Delegation reason:

- Noisy transcripts and logs are explicitly in scope for context compression.

Expected useful result:

- Summary removes noisy tool output.
- Evidence references transcript locations or message boundaries when available.
- Unknowns state where the log is incomplete.

Result:

- Trial pass/fail: Fail
- Files/artifact types inspected: `docs/superpowers/evaluations/fixtures/noisy-claude-session-sample.md`
- Summary specificity: Useful; it captured the V0 objective, completed artifacts, verification status, Trial 1 pass, and Trial 2 issue.
- Raw context avoided: The main Claude session avoided reading the full noisy fixture directly and received a compact decision/open-question summary.
- Evidence quality: Mixed; the response gave concrete references, but several references pointed to source files mentioned by the fixture rather than clearly anchoring every claim to fixture line locations.
- Suggested direct reads quality: Fail; the response omitted the required `Suggested Direct Reads` section.
- Main workflow impact: Mixed. The compression was useful, but the response did not obey the required output contract.
- Notes: The response used `Open Questions` instead of `Unknowns And Risks` and did not include `Suggested Direct Reads`. This is a contract-drift failure even though the summary itself was helpful.

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

- Trial pass/fail: Not evaluated
- Files/artifact types inspected: Not measured
- Summary specificity: Not measured
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

- Trial pass/fail: Not evaluated
- Files/artifact types inspected: Not measured
- Summary specificity: Not measured
- Raw context avoided: Not measured
- Evidence quality: Not measured
- Suggested direct reads quality: Not measured
- Main workflow impact: Not measured
- Notes: Not run yet

## Final V0 Gate Decision

Product or usage gate:

- Status: In evaluation
- Evidence: Trial 1 and Trial 2 passed. Trial 3 produced useful compression but failed the required response contract. Run Trials 4 and 5 before setting the overall gate to pass or fail.

Technical or security gate:

- Status: In evaluation
- Evidence: Claude Code can invoke the project-local subagent, and the subagent stayed read-only in observed trials. Trial 3 shows the response contract still needs validation pressure.

Decision:

- V0 status: In evaluation
- V1 may open: No
- Reason: Manual trials are not complete, and one completed trial showed response-format drift.
