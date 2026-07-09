# Plugin Pivot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the Python CLI installer with a native Claude Code plugin (static subagent + once-ever nudge + README), then delete the `src/` package.

**Architecture:** This repo becomes the plugin. Plugin manifest and marketplace manifest live in `.claude-plugin/`; component dirs (`agents/`, `hooks/`) live at the repo root. The subagent is a static markdown file frozen from the current `render_agent_markdown()` output plus one read-restraint clause. Discovery is a single marker-gated `UserPromptSubmit` hook. All generation/installer machinery is deleted; `bench/` and `docs/` stay in-repo but are not loaded by Claude Code.

**Tech Stack:** Claude Code plugin format (JSON manifests + markdown agent + `hooks.json`), Python/pytest for the single contract test.

## Global Constraints

- Plugin name: `haiku-scribe` (kebab-case, used for `@haiku-scribe` and `/plugin install haiku-scribe`).
- Component directories (`agents/`, `hooks/`) MUST be at the repo root, NOT inside `.claude-plugin/`. Only `plugin.json` and `marketplace.json` go in `.claude-plugin/`.
- The agent file keeps `model: haiku` and `tools: Read, Glob, Grep` exactly.
- Read-only + no network is the only security boundary (deny rules cannot ship in a plugin); the agent's read-restraint clause is the replacement.
- Git remote: `https://github.com/RemyLespagnol/haiku-scribe.git`.
- Keep git history — this is subtraction, not a rewrite. Do NOT `rm -rf` history; use `git rm`.
- Do not add runtime dependencies. The only Python left is one test.

---

### Task 1: Freeze the agent contract + plugin manifest + contract test

**Files:**
- Create: `.claude-plugin/plugin.json`
- Create: `agents/haiku-scribe.md`
- Create: `test_contract.py`

**Interfaces:**
- Produces: `agents/haiku-scribe.md` (the always-on carrier), consumed by Task 2 (marketplace lists it) and Task 3 (nudge references `@haiku-scribe`). `test_contract.py::test_agent_contract_has_required_clauses` guards its content.

- [ ] **Step 1: Write the failing test**

Create `test_contract.py`:

```python
"""Guard the static agent contract: the product is this file, so the test is
that the file still says what it must. Runnable as `python3 test_contract.py`
or `python -m pytest test_contract.py`."""
from pathlib import Path

AGENT = Path(__file__).parent / "agents" / "haiku-scribe.md"

REQUIRED = [
    "model: haiku",
    "tools: Read, Glob, Grep",
    # routing carrier (description trigger)
    "Use proactively before broad exploration",
    "Skip for small focused reads (3 or fewer known files)",
    # don't-re-read carrier (coverage statement)
    "State coverage explicitly",
    "Never present a sample or partial scan as a total count",
    # read-restraint clause (deny-rule replacement)
    "never open `.env`",
]


def test_agent_contract_has_required_clauses():
    text = AGENT.read_text()
    missing = [c for c in REQUIRED if c not in text]
    assert not missing, f"agent contract missing required clauses: {missing}"


if __name__ == "__main__":
    test_agent_contract_has_required_clauses()
    print("ok")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 test_contract.py`
Expected: FAIL — `FileNotFoundError` (agents/haiku-scribe.md does not exist yet).

- [ ] **Step 3: Create the plugin manifest**

Create `.claude-plugin/plugin.json`:

```json
{
  "name": "haiku-scribe",
  "version": "2.0.0",
  "description": "Read-only Haiku scout subagent that compresses broad context (surveys, logs, transcripts, unfamiliar flow) into structured evidence, saving main-context headroom and stretching the Pro/Max cap.",
  "author": {
    "name": "Remy Lespagnol"
  },
  "homepage": "https://github.com/RemyLespagnol/haiku-scribe",
  "repository": "https://github.com/RemyLespagnol/haiku-scribe",
  "license": "MIT",
  "keywords": ["subagent", "context", "haiku", "token-efficiency"]
}
```

- [ ] **Step 4: Create the static agent contract**

Create `agents/haiku-scribe.md` with EXACTLY this content (frozen `render_agent_markdown()` output plus one added read-restraint bullet in "How To Read"):

```markdown
---
name: haiku-scribe
description: Read-only Haiku scout that compresses broad context into structured evidence and exact extractions. Use proactively before broad exploration: 4+ files, directory or repository surveys, large files, logs, transcripts, generated output, or flow mapping in unfamiliar code. Skip for small focused reads (3 or fewer known files) and when exact line-level detail is needed immediately. Not for edits, final debugging/architecture/security conclusions, or user-facing summaries.
model: haiku
tools: Read, Glob, Grep
---

# Haiku Scribe

## Role

You are a read-only context-compression worker for Claude Code. Read only the context needed for the request and return a compact, evidence-backed brief so the main Claude session can reason without loading excessive raw files, logs, transcripts, or generated output.

## Exploration Budget

When the main session names an explicit scope — specific files, a directory, "all the specs", a whole survey — cover it completely in one pass. Treat a named scope like a named-files request: do not cut it off at an arbitrary file count.
For open-ended exploration with no named scope, budget by volume read rather than file count — many small files are cheap, large files are not. Keep the total you read modest and sample structure from big files instead of reading them whole.
Either way, never stop silently mid-scope. If you cannot finish, return what you did cover and list the exact paths still unread, so the main session can decide rather than guess whether coverage was complete.
For a single large file, summarize structure first and read only the regions needed to answer unless the main session explicitly requests exact extraction. Do not read it in full across offset/limit slices unless exact extraction demands it.

## Boundaries

You may:
- Read files requested by the main Claude session.
- Search repository text with exact patterns.
- List files with glob patterns.
- Summarize large files, logs, transcripts, generated output, and related files.
- Extract evidence file paths and line numbers when available.
- Identify uncertainty and recommend focused direct reads.

You must not:
- Edit files.
- Write files.
- Run shell commands.
- Browse web.
- Use MCP tools.
- Invoke other agents.
- Make final root-cause conclusions.
- Make final architecture decisions.
- Make final security, authentication, authorization, or permission conclusions.
- Produce final PR summaries, commit messages, release notes, or public project outputs.

## How To Read

- Prefer compact evidence over exhaustive dumping.
- When specific files are named, prioritize those files.
- When an exact, verbatim extraction is requested, read enough offset/limit slices to return the requested exact data; for explicitly requested extractions, completeness takes priority over the read budget.
- Avoid forcing the main session to delegate and then re-read the same raw source. If exact line-level detail is the real task, say direct reading may be cheaper and safer.
- If content appears secret-bearing, credential-like, or unrelated to the request, stop and say direct user confirmation is needed before inspecting it.
- Read-only always: never open `.env`, credential, secret, or key files even when they fall inside a requested scope. Skip them and note each as skipped in the coverage statement.
- Do not invent evidence line numbers.

## Response Shape

### Summary
Two to six bullets with the compressed answer.

### Evidence
`path/to/file.ext:line`: Relevant observed fact.

### Unknowns And Risks
Unknown or risk that affects confidence.

### Suggested Direct Reads
`path/to/file.ext:line`: Why the main Claude session should inspect the exact location.

### Structured Extraction
When the request asks for exact stats, counts, ordered occurrences, or correlations, return complete and exact data — tables, ordered `path:line` lists, short verbatim excerpts — not a generic summary. The main session should not need to re-read broad raw context to use the extraction.

State coverage explicitly: which files and line ranges you read, and whether the extraction is complete. If you could not cover the full requested range, name exactly what is missing instead of returning data that looks complete. Never present a sample or partial scan as a total count.
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python3 test_contract.py`
Expected: prints `ok`.

Also run: `python -m pytest test_contract.py -v`
Expected: 1 passed.

- [ ] **Step 6: Validate the plugin manifest**

Run: `claude plugin validate .`
Expected: reports the plugin as valid (name `haiku-scribe`, one agent found). If `claude plugin validate` is unavailable in this environment, skip and rely on the load test in Task 2.

- [ ] **Step 7: Commit**

```bash
git add .claude-plugin/plugin.json agents/haiku-scribe.md test_contract.py
git commit -m "feat(plugin): static haiku-scribe agent contract + manifest + contract test"
```

---

### Task 2: Add the marketplace manifest and verify installability

**Files:**
- Create: `.claude-plugin/marketplace.json`

**Interfaces:**
- Consumes: `.claude-plugin/plugin.json` and `agents/haiku-scribe.md` from Task 1.
- Produces: a same-repo marketplace so `/plugin marketplace add <git-url>` + `/plugin install haiku-scribe` works.

- [ ] **Step 1: Create the marketplace manifest**

Create `.claude-plugin/marketplace.json`. `source: "./"` points at the repo root, where `plugin.json` lives:

```json
{
  "name": "haiku-scribe",
  "owner": {
    "name": "Remy Lespagnol"
  },
  "description": "Haiku Scribe: a read-only Haiku context-compression subagent.",
  "plugins": [
    {
      "name": "haiku-scribe",
      "source": "./",
      "description": "Read-only Haiku scout that compresses broad context into structured evidence, saving main-context headroom and stretching the Pro/Max cap.",
      "category": "productivity"
    }
  ]
}
```

- [ ] **Step 2: Validate the marketplace manifest**

Run: `claude plugin validate .`
Expected: both manifests valid, one plugin listed. If unavailable, proceed to Step 3.

- [ ] **Step 3: Load the plugin locally to confirm the agent registers**

Run: `claude --plugin-dir . -p "List your available subagents" 2>&1 | grep -i haiku-scribe`
Expected: output mentions `haiku-scribe`. (This loads the plugin from the current directory without a full install.)

If `--plugin-dir` is not available in this Claude version, instead run `/plugin marketplace add .` then `/plugin install haiku-scribe` inside an interactive session and confirm `@haiku-scribe` autocompletes.

- [ ] **Step 4: Commit**

```bash
git add .claude-plugin/marketplace.json
git commit -m "feat(plugin): same-repo marketplace manifest for /plugin install"
```

---

### Task 3: Add the once-ever onboarding nudge

**Files:**
- Create: `hooks/hooks.json`

**Interfaces:**
- Consumes: nothing (self-contained hook).
- Produces: a marker-gated `UserPromptSubmit` hook that fires exactly once per machine.

**Note on the mechanism:** For `UserPromptSubmit`, a hook that exits 0 with stdout has that stdout added to the model's context (this and `SessionStart` are the two events with this behavior). The marker file `~/.claude/.haiku-scribe-onboarded` gates it to a single lifetime firing. Inline shell only — no separate script file.

- [ ] **Step 1: Create the hook config**

Create `hooks/hooks.json`:

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "f=\"$HOME/.claude/.haiku-scribe-onboarded\"; [ -f \"$f\" ] || { mkdir -p \"$HOME/.claude\"; touch \"$f\"; printf '%s' 'haiku-scribe is installed: a read-only Haiku scout that compresses broad reads (4+ files, logs, transcripts, surveys, unfamiliar flow) into structured evidence. It auto-routes for those; invoke @haiku-scribe to force it. This note fires once.'; }"
          }
        ]
      }
    ]
  }
}
```

- [ ] **Step 2: Verify the gating logic in isolation**

Run (simulates two firings against a temp marker):

```bash
rm -f /tmp/hs-marker-test
CMD='f="/tmp/hs-marker-test"; [ -f "$f" ] || { touch "$f"; printf "%s" "NUDGE"; }'
echo "first: [$(sh -c "$CMD")]"
echo "second: [$(sh -c "$CMD")]"
rm -f /tmp/hs-marker-test
```

Expected:
```
first: [NUDGE]
second: []
```
(Fires once, silent thereafter.)

- [ ] **Step 3: Validate the plugin still loads with hooks**

Run: `claude plugin validate .`
Expected: valid, hooks recognized. If unavailable, load via `claude --plugin-dir . -p "hi"` and confirm no error.

- [ ] **Step 4: Commit**

```bash
git add hooks/hooks.json
git commit -m "feat(plugin): once-ever marker-gated onboarding nudge"
```

---

### Task 4: Write the README

**Files:**
- Modify: `README.md` (replace installer-era content with plugin content)

**Interfaces:**
- Consumes: the agent from Task 1, marketplace from Task 2.
- Produces: user-facing install + usage docs; the optional CLAUDE.md snippet (booster only).

- [ ] **Step 1: Get the current headroom number**

Run the private benchmark once against the frozen contract to produce the context-saved figure:

Run: `python3 bench/report.py`
Expected: prints a report including a context-saved / headroom figure. Note the number; substitute it for `<HEADROOM_NUMBER>` below. If the bench cannot run cleanly, write the README with the phrase "measured on the private bench (see `bench/`)" and leave the specific number out rather than inventing one.

- [ ] **Step 2: Write README.md**

Replace `README.md` with:

````markdown
# haiku-scribe

A Claude Code **plugin** that installs one thing: `haiku-scribe`, a read-only,
Haiku-powered subagent that compresses broad context — repository surveys, logs,
transcripts, generated output, flow mapping across unfamiliar code — into a
compact, evidence-backed brief. The main model reasons over the brief instead of
loading the raw source itself.

## Why

- **Main-context headroom** — the primary win, on every tier. The scout reads the
  bulky raw source; your main context keeps only the compressed extract.
  (Measured delta: `<HEADROOM_NUMBER>`.)
- **Pro/Max cap-stretch** — Haiku is weighted far below Opus, so offloading broad
  reads to the scout conserves the weekly cap.
- **Subscription-seat, no API key** — it runs as a native Task-tool subagent,
  billed to your seat by design. Works identically on Pro, Max, and Enterprise,
  where no-API-key is often mandatory. No `claude -p` side door, no external
  endpoint.

**One caveat that makes or breaks it:** don't re-read the source after the scout
returns. The scout states its coverage explicitly ("read A, B fully / skimmed C /
D not relevant / extraction complete"); when coverage is complete, use the extract
as-is. Delegating and then re-reading spends Haiku *and* Opus — strictly worse
than reading directly.

## Install

```
/plugin marketplace add https://github.com/RemyLespagnol/haiku-scribe.git
/plugin install haiku-scribe
```

Update: re-run `/plugin install haiku-scribe`. Remove: `/plugin uninstall haiku-scribe`.

## Use

The scout **auto-routes**: the main model delegates to it when a request means
broad reading (4+ files, directory/repo surveys, large files, logs, transcripts,
generated output, unfamiliar-flow mapping). To **force** it, invoke it manually:

```
@haiku-scribe survey the auth flow across src/ and list every entrypoint
```

Skip it for small focused reads (≤3 known files) and when you need exact
line-level detail immediately — read those directly.

## Optional: sharpen the reflex (power users)

The auto-routing already ships in the agent's own description, so this is a
**booster, not a requirement**. If you want the routing rule in your global
instructions, paste this block into `~/.claude/CLAUDE.md`:

<!-- HAIKU_SCRIBE_START -->
## Cost-aware Context Routing

Before loading raw repository context, classify remaining work.

Compact discovery tools may be used first if they return metadata, symbols, call paths, or file candidates instead of raw file contents.

Use main session directly only when remaining work is a small focused read:
- 3 or fewer small files;
- no directory reads;
- no shell search over many files;
- no logs, bundles, generated output, transcripts, or large docs;
- no architecture, flow, or cross-layer mapping.

Use `haiku-scribe` when remaining work is broad context gathering:
- 4+ files;
- large files;
- directory or repository survey;
- logs, bundles, generated output, transcripts, or large docs;
- architecture review, flow mapping, pattern audit, unfamiliar-area exploration;
- locating where a feature is implemented or used across unfamiliar code;
- evidence extraction before broad reasoning.

Prefer `haiku-scribe` over the built-in Explore agent for bulk digestion and evidence extraction; use Explore only when the search itself needs parent-model reasoning.

Avoid the costly double-read pattern. If the task needs exact, line-level detail immediately, read directly (offset/limit for large files) instead of delegating. If you delegate, ask for a structured extraction useful enough that you do not delegate and then re-read the same raw source. Require the scout to state its coverage; when it reports complete coverage, use the extraction as-is and do not re-read source the scout already covered.

Workflow:
1. Use compact discovery if available.
2. Classify remaining work as small focused read or broad context gathering.
3. If small, main session reads directly.
4. If broad, call `haiku-scribe` before raw Read, Grep, or shell exploration.
5. Main Claude performs focused direct reads on highest-value locations.
6. Main Claude makes final decisions, edits, commits, and user-facing conclusions.

Haiku Scribe may gather evidence for tasks that eventually require debugging, architecture, scope, or review judgment. These exclusions apply to final judgment, not pre-analysis.

Do not delegate:
- final debugging root-cause conclusions;
- architecture decisions;
- security, authentication, authorization, or permission-sensitive conclusions;
- precise edits;
- PR summaries, commit messages, release notes, or public project outputs.

Main Claude verifies important claims with focused spot-checks of cited `path:line` locations before editing, not broad re-reads.

If `haiku-scribe` is unavailable, say so explicitly and continue manually.
<!-- HAIKU_SCRIBE_END -->

## Safety

Read-only tools (`Read, Glob, Grep`), no network, no shell. The agent also
refuses to open `.env`, credential, secret, and key files. Residual risk: a
secret could surface in an extract you explicitly asked for.

## Development

`bench/` and `docs/superpowers/` are private development workspaces — not part of
the shipped plugin (Claude Code loads only `agents/` and `hooks/`). Run the
contract test with `python3 test_contract.py`.
````

- [ ] **Step 3: Verify the README snippet matches the agent's routing rule**

Run: `grep -c "haiku-scribe" README.md`
Expected: a positive count (sanity check the file wrote).

- [ ] **Step 4: Commit**

```bash
git add README.md
git commit -m "docs: plugin README — install, usage, KPI, optional snippet"
```

---

### Task 5: Subtract the Python installer

**Files:**
- Delete: `src/` (entire tree, incl. `src/haiku_scribe/` and `src/haiku_scribe.egg-info/`)
- Delete: `tests/` (entire CLI test suite)
- Modify: `pyproject.toml`

**Interfaces:**
- Consumes: nothing new — Tasks 1–4 already reproduced all shipped content as static files.
- Produces: a repo whose only Python is `test_contract.py`.

**Precondition:** Before deleting, run the old uninstaller on your own machine so no orphaned installer artifacts remain under `~/.claude`:

Run: `PYTHONPATH=src python3 -m haiku_scribe uninstall --dry-run` then, if it looks right, `PYTHONPATH=src python3 -m haiku_scribe uninstall`
Expected: removes the old agent file, guidance block, deny rules, and V1.2 hooks it owns.

- [ ] **Step 1: Confirm no shipped content is lost**

Run: `grep -q "never open" agents/haiku-scribe.md && echo "agent ok"; grep -q "Cost-aware Context Routing" README.md && echo "snippet ok"`
Expected: prints `agent ok` and `snippet ok` — the two pieces of content that had to survive the deletion (the read-restraint clause in the agent, the routing snippet in the README) are present in the static files.

- [ ] **Step 2: Delete the package and its tests**

```bash
git rm -r src tests
```

- [ ] **Step 3: Simplify pyproject.toml for the one remaining test**

Replace `pyproject.toml` with:

```toml
[project]
name = "haiku-scribe"
version = "2.0.0"
description = "Claude Code plugin: a read-only Haiku context-compression subagent"
requires-python = ">=3.11"
dependencies = []

[project.optional-dependencies]
dev = ["pytest>=8", "ruff>=0.6"]

[tool.pytest.ini_options]
testpaths = ["."]
```

(Removed: the `[build-system]`/setuptools packaging, the `haiku-scribe = ...` console entry point pointing at the deleted `cli.py`, and the `pythonpath = ["src"]` / `testpaths = ["tests"]` config.)

- [ ] **Step 4: Verify the repo still tests and lints clean**

Run: `python -m pytest -q`
Expected: 1 passed (only `test_contract.py`).

Run: `ruff check`
Expected: no errors (or "All checks passed"). If ruff flags the now-empty former package paths, they no longer exist, so no action needed.

- [ ] **Step 5: Confirm the plugin still validates after subtraction**

Run: `claude plugin validate .`
Expected: valid — the plugin is entirely static files, untouched by the deletion.

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "refactor: delete Python installer — plugin ships static files only"
```

- [ ] **Step 7: Cut over (manual, outside the repo)**

Notify the handful of colleagues on the old version to run the old `uninstall` and `/plugin install haiku-scribe`. No migration tooling is shipped — the bet is nobody else is on the old version. This step is a message, not code.

---

## Notes for the implementer

- **`bench/` and `docs/` are intentionally kept** in the repo after Task 5. They are private dev workspaces, not shipped product; Claude Code ignores them.
- **If `claude plugin validate` / `--plugin-dir` are unavailable**, fall back to the interactive `/plugin marketplace add .` + `/plugin install haiku-scribe` flow described in Task 2 Step 3 for every "validate" step.
- **If plain `UserPromptSubmit` stdout is not injected** in the target Claude version (behavior differs across versions), change the hook's `printf '%s' '...'` to emit the documented JSON form instead:
  `printf '%s' '{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":"<same text>"}}'`
  Both are marker-gated identically; only the output encoding changes.
