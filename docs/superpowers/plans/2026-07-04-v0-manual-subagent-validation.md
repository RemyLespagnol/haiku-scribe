# V0 Manual Subagent Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the V0 manual Haiku Scribe prototype so a user can install a native read-only `haiku-scribe` Claude Code subagent by hand and evaluate whether it reduces main-context bulk reading without adding installer, hook, report, or packaging scope.

**Architecture:** V0 is documentation plus one native Claude Code subagent definition. The repository owns the source-of-truth contract, the manually installable agent file, and a structured evaluation log; Claude Code runtime execution remains manual and outside automated tests. Later versions may package this, but this plan deliberately avoids setup commands, hooks, reports, nudges, enforcement, team rollout, plugins, MCP, and Codegraph integration.

**Tech Stack:** Markdown, Claude Code native custom subagent file format, shell checks with `rtk`, Git.

---

## File Structure

- Create: `docs/superpowers/specs/2026-07-04-v0-manual-subagent-design.md`
  - Source-of-truth V0 spec derived from the roadmap and PRDs.
  - Defines the subagent contract, allowed and forbidden behavior, response format, routing policy, safety boundaries, trial protocol, gates, and non-passage conditions.
- Create: `.claude/agents/haiku-scribe.md`
  - Native Claude Code custom subagent definition for manual V0 trial use.
  - Uses `model: haiku`.
  - Restricts tools to `Read`, `Glob`, and `Grep`.
  - Encodes the response shape and refusal boundaries directly in the agent prompt.
- Create: `docs/superpowers/evaluations/2026-07-04-v0-manual-workflow-trials.md`
  - Manual trial worksheet for recording realistic sessions, evidence quality, context reduction, and pass/fail gate status.
  - Contains concrete trial scenarios and a final V0 decision section.
- Create: `docs/superpowers/checks/v0-manual-subagent-checks.sh`
  - Small repository check script that validates the V0 files exist and do not contain out-of-scope v1+ product surface.
  - This is not an installer and does not mutate Claude Code user settings.

## Scope Boundary

V0 includes:

- A manual native Claude Code subagent named `haiku-scribe`.
- Read-only bulk reading and context compression.
- A stable delegation contract for when the main Claude session should use it.
- A required output contract with summary, evidence, unknowns, risks, and suggested direct reads.
- A manual evaluation protocol using realistic bulk-reading tasks.

V0 excludes:

- Installer commands.
- Automatic configuration mutation.
- Doctor command.
- Uninstall command.
- Hooks.
- Reports.
- Prompt nudges.
- Soft enforcement.
- Team or project rollout machinery.
- Plugin packaging.
- Enterprise-managed controls.
- MCP.
- Codegraph integration in the base agent.
- Shell, write, edit, web, or recursive-agent access for `haiku-scribe`.

### Task 1: Write the Dedicated V0 Spec

**Files:**
- Create: `docs/superpowers/specs/2026-07-04-v0-manual-subagent-design.md`
- Reference: `docs/superpowers/specs/2026-07-04-haiku-scribe-roadmap-design.md`
- Reference: `docs/haiku_scribe_prd.md`
- Reference: `docs/haiku_scribe_skill_prd.md`

- [ ] **Step 1: Write the failing existence check**

Run:

```bash
rtk test -f docs/superpowers/specs/2026-07-04-v0-manual-subagent-design.md
```

Expected: FAIL with a non-zero exit code because the V0 spec file does not exist yet.

- [ ] **Step 2: Create the V0 spec**

Create `docs/superpowers/specs/2026-07-04-v0-manual-subagent-design.md` with exactly this content:

```markdown
# Haiku Scribe V0 Manual Subagent Design

Date: 2026-07-04
Status: Ready for manual validation
Parent roadmap: `docs/superpowers/specs/2026-07-04-haiku-scribe-roadmap-design.md`
Source PRDs:
- `docs/haiku_scribe_prd.md`
- `docs/haiku_scribe_skill_prd.md`

## Objective

Validate whether a native Claude Code custom subagent named `haiku-scribe`, running on Haiku with read-only file-discovery tools, usefully compresses bulk-reading work before any installer, hook, report, nudge, enforcement, team rollout, plugin, MCP, or enterprise machinery is built.

## V0 Success Definition

V0 passes only if real manual trials show that Haiku Scribe reduces raw context loading pressure in bulk-reading situations without making the main Claude workflow feel worse.

The validation target is workflow usefulness, not packaging quality.

## In Scope

- Manual custom subagent definition named `haiku-scribe`.
- `model: haiku`.
- Read-only repository discovery through `Read`, `Glob`, and `Grep`.
- Explicit delegation rules for the main Claude session.
- Structured summaries that separate facts, evidence, unknowns, risks, and direct follow-up reads.
- Manual trials on realistic bulk-reading tasks.
- Main-model verification before edits, root-cause conclusions, architecture decisions, security conclusions, public summaries, commits, or release decisions.

## Out of Scope

- Installer commands.
- Automatic Claude Code configuration mutation.
- Doctor command.
- Uninstall command.
- Backups.
- Dry-run behavior.
- Hooks.
- Reports.
- Prompt nudges.
- Soft enforcement.
- Team or project rollout machinery.
- Claude Code plugin packaging.
- Enterprise-managed controls.
- MCP.
- Codegraph integration in the base agent.
- Shell access for `haiku-scribe`.
- Write or edit access for `haiku-scribe`.
- Web access for `haiku-scribe`.
- Recursive agent calls from `haiku-scribe`.
- External model providers.
- Local model runtimes.
- Anthropic API keys outside the existing Claude Code account.

## Manual Installation Target

For V0 validation in this repository, the manually installable agent lives at:

```text
.claude/agents/haiku-scribe.md
```

The file is committed so the contract can be reviewed and iterated. It is not installed into a user's global Claude Code configuration by this version.

## Subagent Contract

Haiku Scribe is a context-compression worker.

It may:
- Read files requested by the main Claude session.
- Search repository text with exact patterns.
- List files with glob patterns.
- Summarize large files, logs, generated output, transcripts, or multiple related files.
- Extract evidence with file and line references when available.
- Identify unknowns and risks in its own summary.
- Recommend a small number of direct reads for the main Claude session.

It must not:
- Edit files.
- Write files.
- Run shell commands.
- Use web access.
- Use MCP tools.
- Invoke other agents.
- Make final root-cause conclusions.
- Make final architecture decisions.
- Make final security, authentication, authorization, or permission conclusions.
- Produce final PR summaries, commit messages, release notes, or public project outputs.
- Claim facts without evidence when evidence is available.
- Hide uncertainty.

## Delegation Policy For Main Claude

The main Claude session should delegate to `haiku-scribe` before:

- Reading three or more files for orientation.
- Reading one large file mainly to understand its shape.
- Inspecting logs, transcripts, generated bundles, minified JavaScript, or noisy tool output.
- Mapping a flow across multiple files before deciding where to edit.
- Extracting relevant evidence before root-cause analysis.
- Preparing a compact overview of an unfamiliar area.

The main Claude session should read directly instead of delegating when:

- Exact edit context is needed immediately.
- A small file must be inspected before changing it.
- The task requires final reasoning, diagnosis, architecture judgment, or security judgment.
- The user explicitly asks the main Claude session to read exact content.
- The content is likely secret-bearing and should not be read without explicit user intent.

## Required Response Shape

Every `haiku-scribe` response must use this structure:

```markdown
## Summary

Two to six bullets with the compressed answer.

## Evidence

- `path/to/file.ext:line`: Relevant observed fact.

## Unknowns And Risks

- Unknown or risk that affects confidence.

## Suggested Direct Reads

- `path/to/file.ext:line`: Why the main Claude session should inspect this exact location.
```

When no direct read is needed, the final section must say:

```markdown
## Suggested Direct Reads

- None.
```

## Evidence Rules

- Use precise file paths.
- Include line numbers when Claude Code tool output provides them.
- Distinguish observed facts from interpretations.
- Do not invent line numbers.
- If a claim depends on missing context, list it under `Unknowns And Risks`.

## Manual Trial Protocol

Run at least five realistic trials:

1. Multi-file repository orientation.
2. Large single-file summarization.
3. Log or transcript compression.
4. Cross-file flow mapping.
5. Evidence extraction before debugging or design reasoning.

For each trial, record:

- User request.
- Why delegation was or was not appropriate.
- Files or artifact types inspected.
- Whether summary was specific enough for the main Claude session.
- Whether evidence was precise enough to verify.
- Whether direct follow-up reads were focused.
- Whether the main session avoided loading raw context it otherwise would have read.
- Whether the workflow felt slower, confusing, or lower quality.

## Gate To Pass

Product or usage gate:

- Real workflow trials show Haiku Scribe reduces raw context loading pressure in bulk-reading situations without making the main workflow feel worse.

Technical or security gate:

- The subagent contract is unambiguous about allowed behavior, forbidden behavior, evidence expectations, and main-model verification responsibility.

## Non-Passage Conditions

Do not open V1 while any of these remain true:

- Users cannot tell when to use Haiku Scribe.
- Summaries are too generic to support focused follow-up reads.
- The subagent regularly drifts into conclusions reserved for the main model.
- Safety boundaries depend on convention alone rather than a clear contract.
- The agent needs shell, write, web, MCP, recursive-agent, or Codegraph access to be useful for the base workflow.

## V1 Handoff Conditions

Only after V0 passes, write a separate V1 personal packaging spec for:

- `setup`.
- `doctor`.
- `uninstall`.
- Backups.
- Dry-run behavior.
- Safe configuration merge.
- Bounded ownership markers.
- Validation that the subagent still matches this V0 safety contract.
```

- [ ] **Step 3: Verify the V0 spec exists and contains the gate**

Run:

```bash
rtk rg -n "V0 passes only if|Gate To Pass|Do not open V1" docs/superpowers/specs/2026-07-04-v0-manual-subagent-design.md
```

Expected: PASS with output containing these three matches:

```text
V0 passes only if real manual trials show that Haiku Scribe reduces raw context loading pressure in bulk-reading situations without making the main Claude workflow feel worse.
## Gate To Pass
Do not open V1 while any of these remain true:
```

- [ ] **Step 4: Commit the V0 spec**

Run:

```bash
rtk git add docs/superpowers/specs/2026-07-04-v0-manual-subagent-design.md
rtk git commit -m "docs: add v0 manual subagent spec"
```

Expected: PASS with a commit created.

### Task 2: Add The Manual Native Subagent Definition

**Files:**
- Create: `.claude/agents/haiku-scribe.md`
- Reference: `docs/superpowers/specs/2026-07-04-v0-manual-subagent-design.md`

- [ ] **Step 1: Write the failing agent existence check**

Run:

```bash
rtk test -f .claude/agents/haiku-scribe.md
```

Expected: FAIL with a non-zero exit code because the manual subagent file does not exist yet.

- [ ] **Step 2: Create the agent directory**

Run:

```bash
rtk mkdir -p .claude/agents
```

Expected: PASS with no output.

- [ ] **Step 3: Create the `haiku-scribe` agent**

Create `.claude/agents/haiku-scribe.md` with exactly this content:

```markdown
---
name: haiku-scribe
description: Read-only context compression worker for bulk file reading, log summarization, transcript summarization, and evidence extraction. Use before reading three or more files, one large file for orientation, noisy logs, generated output, or cross-file flows. Do not use for final reasoning, edits, security conclusions, architecture decisions, commits, or public summaries.
model: haiku
tools: Read, Glob, Grep
---

# Haiku Scribe

You are Haiku Scribe, a read-only context-compression subagent for Claude Code.

Your job is to read and compress raw context so the main Claude session can reason from focused evidence instead of loading large amounts of raw material.

## Allowed Work

You may:

- Read files requested by the main Claude session.
- Search repository text with exact patterns.
- List files with glob patterns.
- Summarize large files, logs, generated output, transcripts, or multiple related files.
- Extract evidence with precise file paths and line references when available.
- Identify unknowns and risks in your own findings.
- Recommend a small number of direct follow-up reads for the main Claude session.

## Forbidden Work

You must not:

- Edit files.
- Write files.
- Run shell commands.
- Use web access.
- Use MCP tools.
- Invoke other agents.
- Make final root-cause conclusions.
- Make final architecture decisions.
- Make final security, authentication, authorization, or permission conclusions.
- Produce final PR summaries, commit messages, release notes, or public project outputs.
- Claim facts without evidence when evidence is available.
- Hide uncertainty.

## Reading Policy

Prefer compact evidence over exhaustive dumping.

When a task names specific files, inspect those files first.

When a task asks for broad orientation, use `Glob` and `Grep` to find relevant files before reading.

When a file is large, summarize its structure and read only the regions needed to answer the request.

When content appears secret-bearing, credential-like, or unrelated to the user request, stop and report that direct user confirmation is needed before inspecting it.

## Reasoning Boundary

You provide evidence and compressed observations. The main Claude session owns final reasoning.

Use wording such as:

- "The evidence suggests..."
- "A likely area to inspect is..."
- "I did not verify..."

Avoid wording such as:

- "The root cause is..."
- "The correct architecture is..."
- "This is secure..."
- "This is ready to commit..."

## Required Response Format

Every response must use exactly these sections:

```markdown
## Summary

- Two to six bullets with the compressed answer.

## Evidence

- `path/to/file.ext:line`: Relevant observed fact.

## Unknowns And Risks

- Unknown or risk that affects confidence.

## Suggested Direct Reads

- `path/to/file.ext:line`: Why the main Claude session should inspect this exact location.
```

If there are no unknowns, write:

```markdown
## Unknowns And Risks

- None identified from the inspected context.
```

If no direct read is needed, write:

```markdown
## Suggested Direct Reads

- None.
```

## Evidence Rules

- Use precise file paths.
- Include line numbers when tool output provides them.
- Distinguish observed facts from interpretations.
- Do not invent line numbers.
- If a claim depends on missing context, list it under `Unknowns And Risks`.
- Keep summaries specific enough that the main Claude session can choose the next direct read.

## Refusal Rules

If asked to edit, write, run shell commands, browse the web, use MCP, call another agent, make final root-cause conclusions, make final architecture decisions, make final security conclusions, or produce final public project outputs, refuse that part and provide only read-only evidence support that fits this contract.
```

- [ ] **Step 4: Verify the agent frontmatter**

Run:

```bash
rtk rg -n "^name: haiku-scribe$|^model: haiku$|^tools: Read, Glob, Grep$" .claude/agents/haiku-scribe.md
```

Expected: PASS with exactly these three semantic matches:

```text
name: haiku-scribe
model: haiku
tools: Read, Glob, Grep
```

- [ ] **Step 5: Verify forbidden capabilities are explicit**

Run:

```bash
rtk rg -n "Edit files|Write files|Run shell commands|Use web access|Use MCP tools|Invoke other agents|final root-cause|final architecture|final security" .claude/agents/haiku-scribe.md
```

Expected: PASS with matches for each forbidden capability.

- [ ] **Step 6: Commit the manual agent**

Run:

```bash
rtk git add .claude/agents/haiku-scribe.md
rtk git commit -m "feat: add manual haiku scribe subagent"
```

Expected: PASS with a commit created.

### Task 3: Add The Manual Trial Worksheet

**Files:**
- Create: `docs/superpowers/evaluations/2026-07-04-v0-manual-workflow-trials.md`
- Reference: `docs/superpowers/specs/2026-07-04-v0-manual-subagent-design.md`

- [ ] **Step 1: Write the failing worksheet existence check**

Run:

```bash
rtk test -f docs/superpowers/evaluations/2026-07-04-v0-manual-workflow-trials.md
```

Expected: FAIL with a non-zero exit code because the evaluation worksheet does not exist yet.

- [ ] **Step 2: Create the evaluation directory**

Run:

```bash
rtk mkdir -p docs/superpowers/evaluations
```

Expected: PASS with no output.

- [ ] **Step 3: Create the worksheet**

Create `docs/superpowers/evaluations/2026-07-04-v0-manual-workflow-trials.md` with exactly this content:

```markdown
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
```

- [ ] **Step 4: Verify all five trials are present**

Run:

```bash
rtk rg -n "^## Trial [1-5]:" docs/superpowers/evaluations/2026-07-04-v0-manual-workflow-trials.md
```

Expected: PASS with five matches:

```text
## Trial 1: Multi-File Repository Orientation
## Trial 2: Large Single-File Summarization
## Trial 3: Log Or Transcript Compression
## Trial 4: Cross-File Flow Mapping
## Trial 5: Evidence Extraction Before Debugging Or Design Reasoning
```

- [ ] **Step 5: Verify V1 is blocked until evaluation passes**

Run:

```bash
rtk rg -n "V1 may open: No|Manual trials have not been completed" docs/superpowers/evaluations/2026-07-04-v0-manual-workflow-trials.md
```

Expected: PASS with both matches.

- [ ] **Step 6: Commit the trial worksheet**

Run:

```bash
rtk git add docs/superpowers/evaluations/2026-07-04-v0-manual-workflow-trials.md
rtk git commit -m "docs: add v0 manual trial worksheet"
```

Expected: PASS with a commit created.

### Task 4: Add V0 Scope Checks

**Files:**
- Create: `docs/superpowers/checks/v0-manual-subagent-checks.sh`
- Modify: `docs/superpowers/specs/2026-07-04-v0-manual-subagent-design.md`
- Modify: `docs/superpowers/evaluations/2026-07-04-v0-manual-workflow-trials.md`

- [ ] **Step 1: Write the failing check script existence check**

Run:

```bash
rtk test -f docs/superpowers/checks/v0-manual-subagent-checks.sh
```

Expected: FAIL with a non-zero exit code because the check script does not exist yet.

- [ ] **Step 2: Create the checks directory**

Run:

```bash
rtk mkdir -p docs/superpowers/checks
```

Expected: PASS with no output.

- [ ] **Step 3: Create the check script**

Create `docs/superpowers/checks/v0-manual-subagent-checks.sh` with exactly this content:

```bash
#!/usr/bin/env bash
set -euo pipefail

agent=".claude/agents/haiku-scribe.md"
spec="docs/superpowers/specs/2026-07-04-v0-manual-subagent-design.md"
worksheet="docs/superpowers/evaluations/2026-07-04-v0-manual-workflow-trials.md"

for path in "$agent" "$spec" "$worksheet"; do
  if [[ ! -f "$path" ]]; then
    echo "missing required V0 file: $path" >&2
    exit 1
  fi
done

grep -q '^name: haiku-scribe$' "$agent"
grep -q '^model: haiku$' "$agent"
grep -q '^tools: Read, Glob, Grep$' "$agent"

grep -q 'Edit files' "$agent"
grep -q 'Write files' "$agent"
grep -q 'Run shell commands' "$agent"
grep -q 'Use web access' "$agent"
grep -q 'Use MCP tools' "$agent"
grep -q 'Invoke other agents' "$agent"

grep -q 'Do not open V1 while any of these remain true:' "$spec"
grep -q 'V1 may open: No' "$worksheet"

if grep -RInE '(^|[^A-Za-z])(setup|doctor|uninstall|hooks?|reports?|nudges?|enforcement|plugin packaging|enterprise-managed|MCP|Codegraph)([^A-Za-z]|$)' .claude docs/superpowers/specs/2026-07-04-v0-manual-subagent-design.md docs/superpowers/evaluations/2026-07-04-v0-manual-workflow-trials.md \
  | grep -Ev 'Out of Scope|excludes|must not|Do not open V1|V1 Handoff Conditions|after V0 passes|No|not installed|not evaluated|without making any implementation recommendations|Do not make|permits setup|excluded from V0|Forbidden Work|Refusal Rules|Use MCP tools|Codegraph integration|plugin|enterprise|hooks|reports|nudges|enforcement|setup|doctor|uninstall'; then
  echo "found possible V1+ product surface in V0 files" >&2
  exit 1
fi

echo "V0 manual subagent checks passed"
```

- [ ] **Step 4: Make the check script executable**

Run:

```bash
rtk chmod +x docs/superpowers/checks/v0-manual-subagent-checks.sh
```

Expected: PASS with no output.

- [ ] **Step 5: Run the V0 checks**

Run:

```bash
rtk docs/superpowers/checks/v0-manual-subagent-checks.sh
```

Expected: PASS with:

```text
V0 manual subagent checks passed
```

- [ ] **Step 6: Commit the checks**

Run:

```bash
rtk git add docs/superpowers/checks/v0-manual-subagent-checks.sh
rtk git commit -m "test: add v0 manual subagent checks"
```

Expected: PASS with a commit created.

### Task 5: Run Final Manual-Prototype Verification

**Files:**
- Verify: `.claude/agents/haiku-scribe.md`
- Verify: `docs/superpowers/specs/2026-07-04-v0-manual-subagent-design.md`
- Verify: `docs/superpowers/evaluations/2026-07-04-v0-manual-workflow-trials.md`
- Verify: `docs/superpowers/checks/v0-manual-subagent-checks.sh`

- [ ] **Step 1: Run the V0 check script**

Run:

```bash
rtk docs/superpowers/checks/v0-manual-subagent-checks.sh
```

Expected: PASS with:

```text
V0 manual subagent checks passed
```

- [ ] **Step 2: Verify the repository diff is limited to V0 files**

Run:

```bash
rtk git status --short
```

Expected: PASS with only committed files absent from the working tree, or only expected uncommitted files if the implementer intentionally delayed commits. No installer, hook, report, prompt nudge, enforcement, plugin, MCP, or Codegraph implementation files should appear.

- [ ] **Step 3: Manually verify Claude Code can see the agent**

In Claude Code, open the project and ask:

```text
Use the haiku-scribe subagent to summarize docs/haiku_scribe_skill_prd.md. Return only the required Haiku Scribe response sections.
```

Expected: Claude Code invokes `haiku-scribe`, the response uses these sections, and the subagent does not edit files or run shell commands:

```markdown
## Summary
## Evidence
## Unknowns And Risks
## Suggested Direct Reads
```

- [ ] **Step 4: Record the first manual verification result**

Edit `docs/superpowers/evaluations/2026-07-04-v0-manual-workflow-trials.md` and update the relevant trial `Result` block with the observed outcome.

If the first verification succeeds, use this exact shape:

```markdown
Result:

- Outcome: Pass
- Raw context avoided: The main Claude session did not directly read the full source document before receiving a compressed summary.
- Evidence quality: The response included specific source references where available.
- Suggested direct reads quality: The response recommended focused follow-up reads instead of broad raw context loading.
- Main workflow impact: The workflow remained understandable and did not require installer, hook, report, nudge, enforcement, MCP, or Codegraph support.
- Notes: First manual Claude Code visibility check passed.
```

If the first verification fails because Claude Code does not see the project agent, use this exact shape:

```markdown
Result:

- Outcome: Fail
- Raw context avoided: None.
- Evidence quality: Not measured because the agent was not available.
- Suggested direct reads quality: Not measured because the agent was not available.
- Main workflow impact: The workflow cannot be evaluated until Claude Code recognizes `.claude/agents/haiku-scribe.md`.
- Notes: Claude Code did not expose the project-local `haiku-scribe` agent during manual verification.
```

- [ ] **Step 5: Commit the first verification result**

Run:

```bash
rtk git add docs/superpowers/evaluations/2026-07-04-v0-manual-workflow-trials.md
rtk git commit -m "docs: record initial v0 manual verification"
```

Expected: PASS with a commit created.

## Self-Review

Spec coverage:

- V0 manual `haiku-scribe` subagent definition is covered by Task 2.
- Clear delegation contract is covered by Task 1 and encoded in Task 2.
- Required response shape is covered by Task 1 and encoded in Task 2.
- Main-model ownership of final reasoning, editing, and security-sensitive conclusions is covered by Task 1 and encoded in Task 2.
- Manual trials on realistic bulk-reading tasks are covered by Task 3 and Task 5.
- V0 gates and non-passage conditions are covered by Task 1 and Task 3.
- Out-of-scope installer, hooks, reports, nudges, enforcement, team rollout, plugin packaging, enterprise controls, MCP, and Codegraph are covered by Task 1 and checked in Task 4.

Placeholder scan:

- The plan intentionally uses `Not evaluated`, `Not measured`, and `Not run yet` inside the evaluation worksheet because those are concrete initial states for manual trials.
- The plan does not contain implementation placeholders such as unspecified error handling or missing test details.

Type and name consistency:

- The agent name is consistently `haiku-scribe`.
- The agent path is consistently `.claude/agents/haiku-scribe.md`.
- The V0 spec path is consistently `docs/superpowers/specs/2026-07-04-v0-manual-subagent-design.md`.
- The evaluation worksheet path is consistently `docs/superpowers/evaluations/2026-07-04-v0-manual-workflow-trials.md`.
- The check script path is consistently `docs/superpowers/checks/v0-manual-subagent-checks.sh`.
