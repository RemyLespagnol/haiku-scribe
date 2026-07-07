# Haiku Scribe V0 Unblock Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Tighten the Haiku Scribe V0 contract and evaluation gate so transcript and log tasks must produce exact headings and reliable `path:line` evidence before `v1` can open.

**Architecture:** Keep the product surface unchanged. Strengthen the prompt contract in the committed subagent file, restore the V0 spec as the human-readable source of truth, and update the V0 evaluation to require clean reruns of the transcript-heavy trials before reopening `v1`.

**Tech Stack:** Markdown, Claude Code custom subagent contract, repository docs

## Global Constraints

- Do not expand scope beyond the approved V0 manual workflow.
- Keep Haiku Scribe read-only with `Read`, `Glob`, and `Grep` only.
- Do not add setup, doctor, uninstall, hooks, reports, nudges, enforcement, MCP, Codegraph, or packaging work to V0.
- Make transcript and log evidence requirements explicit enough to support verification-oriented follow-up.

---

### Task 1: Tighten The Subagent Contract
**Files:**
- Modify: `.claude/agents/haiku-scribe.md`

**Interfaces:**
- Consumes: existing Haiku Scribe V0 contract
- Produces: stricter response and evidence rules for transcript/log tasks

- [ ] **Step 1: Add exact transcript/log evidence requirements**
  Update the required response and evidence rules so each `## Evidence` bullet must use `full/path.ext:line` when the inspected output includes line numbers, and explicitly reject bare `L34`-style anchors.

- [ ] **Step 2: Add a transcript/log preflight checklist**
  Add a short pre-send checklist that forces the subagent to verify exact headings, no wrapper prose, and transcript/log anchors pointing to the inspected transcript file itself.

- [ ] **Step 3: Review the prompt for scope drift**
  Re-read the full file and confirm no new tools, no new product scope, and no ambiguity around allowed vs forbidden work.

### Task 2: Restore The V0 Spec As Source Of Truth
**Files:**
- Modify: `docs/superpowers/specs/2026-07-04-v0-manual-subagent-design.md`

**Interfaces:**
- Consumes: current V0 design and roadmap gate language
- Produces: readable spec text aligned with the committed subagent contract

- [ ] **Step 1: Repair the collapsed formatting**
  Rewrite the malformed sections after `## Evidence Rules` so the manual protocol, gate, non-passage conditions, and V1 handoff conditions are clean markdown again.

- [ ] **Step 2: Mirror the stricter transcript/log rules**
  Align the written spec with the updated subagent contract, including exact heading requirements and transcript/log citation rules.

- [ ] **Step 3: Re-read the gate language**
  Confirm the spec still says V1 opens only after V0 passes and that the blocker remains transcript/log citation reliability rather than broader product scope.

### Task 3: Tighten The Evaluation Gate
**Files:**
- Modify: `docs/superpowers/evaluations/2026-07-04-v0-manual-workflow-trials.md`

**Interfaces:**
- Consumes: current V0 trial findings and gate decision
- Produces: explicit rerun and reopen criteria for `v1`

- [ ] **Step 1: Clean up the evaluation markdown**
  Restore readable structure so each trial and the final gate decision are easy to review directly.

- [ ] **Step 2: Add explicit V1 reopen criteria**
  Record the minimal unblock rule: rerun Trial 3 and Trial 4, require exact `##` headings, require non-truncated `path:line` citations, and require `Evidence quality: Pass`.

- [ ] **Step 3: Keep the current decision closed until evidence changes**
  Leave `V1 may open: No` in place, but make the remaining work and success threshold unambiguous.

### Task 4: Verify The Changes
**Files:**
- Review: `.claude/agents/haiku-scribe.md`
- Review: `docs/superpowers/specs/2026-07-04-v0-manual-subagent-design.md`
- Review: `docs/superpowers/evaluations/2026-07-04-v0-manual-workflow-trials.md`

**Interfaces:**
- Consumes: patched markdown files
- Produces: fresh verification evidence for the user

- [ ] **Step 1: Inspect the final diff**
  Run `rtk git diff -- .claude/agents/haiku-scribe.md docs/superpowers/specs/2026-07-04-v0-manual-subagent-design.md docs/superpowers/evaluations/2026-07-04-v0-manual-workflow-trials.md docs/superpowers/plans/2026-07-05-haiku-scribe-v0-unblock.md`

- [ ] **Step 2: Re-read the changed files**
  Confirm the docs are internally consistent and the prompt contract matches the written V0 spec.

- [ ] **Step 3: Report exact remaining reruns**
  Tell the user which trials to rerun and what evidence must change before opening `v1`.
