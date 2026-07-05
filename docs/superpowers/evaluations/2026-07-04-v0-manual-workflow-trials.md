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
Use haiku-scribe subagent to compress docs/superpowers/evaluations/fixtures/noisy-claude-session-sample.md into key decisions, open questions, evidence. Do not make final conclusions. Return exactly required Haiku Scribe response sections.
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
- Summary specificity: Useful; the response captured the V0 planning workflow, key design decisions, Trial 1 pass, Trial 2 failure, and remaining open questions.
- Raw context avoided: The main Claude session avoided reading the full noisy fixture directly and received a compact transcript summary instead.
- Evidence quality: Fail; the response used bare `L34`-style references instead of anchoring each claim to `docs/superpowers/evaluations/fixtures/noisy-claude-session-sample.md:<line>` citations, and several evidence bullets omitted the full source path entirely.
- Suggested direct reads quality: Pass; `None.` was a reasonable outcome because the fixture was self-contained for the requested compression task.
- Main workflow impact: Mixed. The compression was useful for orientation, but the evidence package was not reliable enough for transcript-based verification work.
- Notes: The remaining issue is no longer section presence. The response still failed the transcript citation contract because it did not use exact `path:line` anchors to the inspected fixture and did not render the exact required markdown headings in the returned output.

## Trial 4: Cross-File Flow Mapping

User request:

```text
Use haiku-scribe map where the product says bulk reading starts, how evidence must be returned, and when the main model must take over. Provide only an evidence map.
```

Delegation reason:

- This requires connecting related rules across multiple documents before main-model reasoning.

Expected useful result:

- Summary maps the flow from delegation trigger to subagent output to main-model verification.
- Evidence references all relevant documents.
- Suggested direct reads identify exact rule sections for the main Claude session.

Result:

- Trial pass/fail: Pass
- Files/artifact types inspected: `docs/haiku_scribe_prd.md`, `docs/superpowers/specs/2026-07-04-v0-manual-subagent-design.md`
- Summary specificity: Specific enough to map the bulk-reading threshold, required evidence format, and main-model takeover boundary.
- Raw context avoided: The main Claude session received a compact cross-file evidence map instead of manually tracing the flow across the PRD and V0 spec.
- Evidence quality: Mixed; the response named the right source areas and concepts, but some pasted line references were visibly garbled or truncated in the returned text.
- Suggested direct reads quality: Not requested in this trial prompt because the user asked for only an evidence map.
- Main workflow impact: Positive. The output was useful for orientation, but citation formatting needs scrutiny before relying on it for exact follow-up reads.
- Notes: Useful map of thresholds and handoff boundaries. The most important risk in this trial is citation cleanliness, not missing product understanding.

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

- Trial pass/fail: Pass
- Files/artifact types inspected: `docs/superpowers/specs/2026-07-04-v0-manual-subagent-design.md`, `docs/superpowers/specs/2026-07-04-haiku-scribe-roadmap-design.md`
- Summary specificity: Specific enough to identify that setup, doctor, uninstall, hooks, reports, nudges, enforcement, MCP, and Codegraph are all excluded from V0 and deferred to later roadmap phases.
- Raw context avoided: The main Claude session avoided rereading the entire spec set just to answer the scope question.
- Evidence quality: Pass; the response provided structured evidence with file paths and line references for both the V0 spec and the roadmap.
- Suggested direct reads quality: Pass; `None.` was appropriate because the evidence package was already sufficient for the scoped question.
- Main workflow impact: Positive. The answer stayed within the read-only evidence boundary and produced a usable verification package without drifting into a final scope decision.
- Notes: Trial passed after rerun with a properly structured evidence response and explicit roadmap citations.

## Final V0 Gate Decision

Product or usage gate:

- Status: Partial pass
- Evidence: Trials 1, 2, 4, and 5 show the subagent is useful for read-heavy orientation, roadmap summarization, cross-file flow mapping, and scoped evidence extraction. Trial 3 still shows a reliability gap for transcript compression because citations were not anchored cleanly enough to the inspected fixture.

Technical or security gate:

- Status: Partial pass
- Evidence: The project-local subagent is invokable, stayed read-only in observed trials, and the V0 contract is documented clearly. The main unresolved issue is transcript evidence quality: the agent can produce the required response shape in some cases, but transcript/log tasks still show weak citation anchoring and wrapper/heading drift.

Decision:

- V0 status: Useful but not yet ready to open V1
- V1 may open: No
- Reason: The manual workflow is clearly valuable, but transcript/log compression still does not produce citation-quality evidence reliably enough for verification-oriented follow-up. V0 should improve transcript evidence anchoring and exact output rendering before packaging work starts.
