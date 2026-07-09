# Discoverability & Top-of-Fold Pass — Design

Date: 2026-07-09
Status: approved (brainstorming)

## Problem

The repo is well-built (README, CI, demo GIF, logo, contract test) but
**invisible to discovery**: GitHub `description`, `topics`, and `homepageUrl` are
all empty, and the social preview is GitHub's default (renders as a bare repo
card when a link is shared). A visitor who does arrive lands on a good-but-dense
first screen with no one-line hook under the title.

Scope chosen: **metadata + README top-of-fold**. Explicitly out of scope (YAGNI):
comparison-vs-alternatives table, "who is this for" section, awesome-list
submissions.

## Changes

### 1. GitHub repository metadata

Set via `gh` CLI / API on `RemyLespagnol/haiku-scribe`:

- **Description** (verbatim):
  > Claude Code plugin: a read-only Haiku subagent that compresses broad context (surveys, logs, transcripts) into a compact brief — sparing your main model's context.
- **Topics** (10): `claude-code`, `claude-code-plugin`, `anthropic`, `claude`,
  `ai-agents`, `subagent`, `context-management`, `llm`, `developer-tools`,
  `haiku`.
- **Homepage**: leave empty (low value; no dedicated page exists).

### 2. Social preview image

- Produce a 1280×640 PNG at `assets/social-preview.png` from the existing
  `assets/logo.png` plus the tagline text.
- **Manual step (documented, not automatable):** GitHub exposes no API to upload
  a social preview. The user uploads it via *Settings → Social preview* in the
  browser (~30s). The spec/plan must surface this as an explicit hand-off, not a
  silent gap.

### 3. README top-of-fold

- Insert a one-line tagline (italic) directly under the `# haiku-scribe` H1,
  above the badges:
  > *Offload broad reading to a cheap Haiku scout — keep your main model's context for thinking.*
- No other README changes. The "Why" section and body stay as-is.

### 4. Hygiene rider

- Untrack `assets/.DS_Store` (macOS cruft in a public repo). Add `.DS_Store` to
  `.gitignore` if not already covered.

## Acceptance

- `gh repo view --json description,repositoryTopics,homepageUrl` shows the
  description and all 10 topics populated.
- `assets/social-preview.png` exists at 1280×640; user has the upload
  instruction.
- README renders the tagline under the H1; `python3 test_contract.py` still
  passes (no agent-contract change, so this is a no-op guard).
- `git ls-files` no longer lists `assets/.DS_Store`; `.gitignore` covers it.

## Non-goals

Adoption on-ramps (comparison, personas, external list submissions), any change
to the shipped agent contract or hook, benchmark/credibility work.
