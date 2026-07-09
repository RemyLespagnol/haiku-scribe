# v0.2 Credibility & Adoption Pass Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the existing haiku-scribe plugin land and be believed via a docs + packaging pass (illustrative walkthrough, VHS demo GIF, badges, CI) with no change to the three shipped surfaces.

**Architecture:** Docs-only + a GitHub Actions workflow. The README gains a "proof by explanation" walkthrough and a VHS-generated demo GIF; a minimal CI workflow runs the existing Python contract test + ruff and validates the manifests, powering a CI badge. The subagent contract, hook, and manifests are untouched.

**Tech Stack:** Markdown, GitHub Actions, charmbracelet/vhs (`.tape` → GIF), Python 3 (existing test), ruff.

## Global Constraints

- No change to shipped-surface behavior: `agents/haiku-scribe.md`, `hooks/hooks.json`, `.claude-plugin/*.json` stay behaviorally identical. `test_contract.py` and its required clauses stay green.
- Proof is *explanation only*: any numbers in the walkthrough are labeled illustrative, never presented as measured. No reproducible benchmark.
- No new runtime/build machinery in the repo: the demo asset is a text `.tape` + a committed `.gif`; VHS is an external tool, not a repo dependency. No Node/package.json.
- Do not fabricate a "recorded" GIF. If VHS is unavailable to render, commit the `.tape` source and leave the GIF to be generated, with the README referencing it.
- Out of scope: external discoverability (awesome-lists, directories, topics).
- Target release: `v0.2`. Keep existing README voice/structure; add, don't rewrite.

---

### Task 1: CI workflow + badge

**Files:**
- Create: `.github/workflows/ci.yml`
- Modify: `README.md` (add CI + license badges under the title, around line 5-6)

**Interfaces:**
- Produces: a workflow named `CI` on branch `main` whose status badge URL is `https://github.com/RemyLespagnol/haiku-scribe/actions/workflows/ci.yml/badge.svg`. Task 4 references this badge already being present.

- [ ] **Step 1: Write the workflow**

Create `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install ruff
        run: pip install ruff
      - name: Contract test
        run: python3 test_contract.py
      - name: Lint
        run: ruff check
      - name: Validate manifests (JSON well-formed)
        run: |
          python3 -c "import json,sys; [json.load(open(p)) for p in ('.claude-plugin/plugin.json', '.claude-plugin/marketplace.json', 'hooks/hooks.json')]; print('manifests OK')"
```

Rationale: `claude plugin validate .` needs the Claude Code CLI, which is not cleanly installable/authable in a stock runner. Per spec, fall back to a JSON well-formedness check so the badge reflects a real green signal without a flaky CLI dependency.

- [ ] **Step 2: Validate the workflow YAML locally**

Run: `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml')); print('yaml OK')"`
Expected: `yaml OK` (if PyYAML missing, `pip install pyyaml` first, or skip — GitHub will parse it on push).

- [ ] **Step 3: Reproduce the CI steps locally**

Run: `python3 test_contract.py && ruff check && python3 -c "import json; [json.load(open(p)) for p in ('.claude-plugin/plugin.json','.claude-plugin/marketplace.json','hooks/hooks.json')]; print('manifests OK')"`
Expected: `ok` then ruff clean output then `manifests OK`.

- [ ] **Step 4: Add badges to README**

In `README.md`, immediately after the `# haiku-scribe` title line, add a badge line:

```markdown
[![CI](https://github.com/RemyLespagnol/haiku-scribe/actions/workflows/ci.yml/badge.svg)](https://github.com/RemyLespagnol/haiku-scribe/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
```

Verify a `LICENSE` file exists at repo root; if it does not, point the license badge at the `license` field context in `plugin.json` or add a standard MIT `LICENSE` (author: Remy Lespagnol) — the manifests already declare MIT.

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/ci.yml README.md LICENSE 2>/dev/null; git add .github/workflows/ci.yml README.md
git commit -m "ci: add contract+lint+manifest workflow and README badges"
```

---

### Task 2: Illustrative walkthrough in README

**Files:**
- Modify: `README.md` (new section between the `## Why` block and `## Install`)

**Interfaces:**
- Consumes: the scout's `Response Shape` structure from `agents/haiku-scribe.md:53-70` (Summary / Evidence / Unknowns And Risks / Suggested Direct Reads) — reproduce it faithfully in the sample brief.
- Produces: a `## How it feels` (or `## Walkthrough`) section that Task 3's GIF sits above or beside.

- [ ] **Step 1: Write the walkthrough section**

Add to `README.md` between `## Why` and `## Install`. Use this content (adjust prose to match README voice; keep the "illustrative" labeling verbatim):

````markdown
## How it feels

Say you ask the main model to *map how auth flows across the ~8 files that touch
login*. Two ways that goes:

**Without haiku-scribe** — the main model opens all 8 files itself. Every line of
raw source now sits in the main context for the rest of the task (illustratively,
several thousand tokens of code you'll never look at again).

**With haiku-scribe** — the main model delegates the survey. The Haiku scout
reads the 8 files and hands back a compact brief; the main context holds only
this, not the raw files:

```
### Summary
- Login enters at routes/auth.py:42, delegates to services/session.py.
- Password check is services/session.py:88 (bcrypt); tokens minted at :140.
- Two callers bypass the service and hit the model directly — see below.

### Evidence
routes/auth.py:42: `login()` — validates form, calls `Session.start()`.
services/session.py:88: bcrypt compare against `User.pw_hash`.
services/session.py:140: JWT minted, 24h expiry.

### Unknowns And Risks
- Refresh-token path not covered in these files; likely in middleware/.

### Suggested Direct Reads
services/session.py:140: inspect exact claim set before changing token shape.
```

The numbers above are illustrative, not a benchmark — the point is the *shape*:
the main context keeps ~40 lines of structured evidence instead of 8 files of
source. **One caveat still holds:** when the scout says coverage is complete,
use the brief as-is; re-reading the same files spends Haiku *and* the main model.
````

- [ ] **Step 2: Verify the sample brief matches the real contract**

Run: `grep -n "Suggested Direct Reads\|Unknowns And Risks\|### Evidence\|### Summary" agents/haiku-scribe.md`
Expected: all four headings exist in the agent's Response Shape, confirming the sample uses real section names.

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: add illustrative without/with walkthrough to README"
```

---

### Task 3: VHS demo asset

**Files:**
- Create: `assets/demo.tape`
- Create: `assets/demo.gif` (generated by VHS, if available)
- Modify: `README.md` (embed the GIF near the top, under the badges/intro)

**Interfaces:**
- Consumes: the walkthrough framing from Task 2 (same auth-survey scenario, kept consistent).
- Produces: `assets/demo.gif` referenced by README.

- [ ] **Step 1: Write the VHS tape**

Create `assets/demo.tape`. Keep it a short, honest terminal reenactment of the auto-route → brief flow (a Claude Code session prompt, the delegation line, the returned brief). Example:

```tape
# Regenerate with: vhs assets/demo.tape  (needs charmbracelet/vhs installed)
Output assets/demo.gif
Set FontSize 20
Set Width 1100
Set Height 640
Set Theme "Catppuccin Mocha"
Set TypingSpeed 40ms
Set PlaybackSpeed 1.0

Type "> map how auth flows across the files that touch login"
Enter
Sleep 700ms
Type "· Delegating the survey to haiku-scribe (read-only Haiku scout)…"
Enter
Sleep 900ms
Type "✓ Brief returned — 8 files read, coverage complete"
Enter
Sleep 500ms
Type "  Summary: login → routes/auth.py:42 → services/session.py"
Enter
Type "  bcrypt check :88 · JWT minted :140 · 2 callers bypass the service"
Enter
Sleep 2500ms
```

- [ ] **Step 2: Render the GIF (best-effort)**

Run: `command -v vhs && vhs assets/demo.tape && echo "gif rendered" || echo "vhs not installed — commit tape only, generate gif later"`
Expected: either `gif rendered` (with `assets/demo.gif` created) or the fallback message. Do NOT fabricate a GIF if VHS is absent.

- [ ] **Step 3: Embed the GIF in README**

In `README.md`, under the intro/badges (after the logo block, before or right after `## Why`), add:

```markdown
<p align="center">
  <img src="./assets/demo.gif" alt="haiku-scribe auto-routing a survey to the Haiku scout" width="700">
</p>
```

If the GIF was not rendered in Step 2, still add this line — it resolves once the GIF is generated and committed — and note in the PR/commit that the GIF is pending render.

- [ ] **Step 4: Document regeneration**

In `README.md` `## Development` section, add one line:

```markdown
- Demo GIF: edit `assets/demo.tape`, regenerate with `vhs assets/demo.tape` ([charmbracelet/vhs](https://github.com/charmbracelet/vhs)).
```

- [ ] **Step 5: Commit**

```bash
git add assets/demo.tape assets/demo.gif README.md 2>/dev/null; git add assets/demo.tape README.md
git commit -m "docs: add VHS demo tape and embed demo GIF in README"
```

---

### Task 4: Install-friction cleanup + release bump

**Files:**
- Modify: `README.md` (`## Install` / `## Use` sections)
- Modify: `.claude-plugin/plugin.json` (version bump to `0.2.0`)

**Interfaces:**
- Consumes: badges from Task 1 (present), walkthrough from Task 2, GIF from Task 3 (README already coherent).

- [ ] **Step 1: Verify the install command names**

Run: `claude plugin --help 2>/dev/null || echo "claude CLI not present — verify command names against current Claude Code docs manually"`
Expected: confirm `marketplace add`, `install`, `uninstall` (and whether `update` is a distinct command or a re-`install`). Fix README wording only if the current CLI disagrees with `README.md:30-37`.

- [ ] **Step 2: Tighten the Install/Use copy**

In `README.md`, ensure the Install block clearly lists, as distinct steps: add marketplace → install → update (re-run install) → remove (`/plugin uninstall haiku-scribe`). Fix any garbled or dropped words in the current `## Use` section (lines ~39-56) so the auto-route trigger and the `@haiku-scribe` manual fallback read as clean sentences. Do not change meaning.

- [ ] **Step 3: Bump plugin version**

In `.claude-plugin/plugin.json`, change `"version": "0.1.0"` to `"version": "0.2.0"`.

- [ ] **Step 4: Run the contract test + lint**

Run: `python3 test_contract.py && ruff check`
Expected: `ok` then clean.

- [ ] **Step 5: Commit**

```bash
git add README.md .claude-plugin/plugin.json
git commit -m "docs: clarify install/update/remove flow; bump to v0.2.0"
```

---

## Self-Review

**Spec coverage:**
- Illustrative walkthrough → Task 2. ✓
- VHS demo asset (`.tape` → GIF, VHS-over-Remotion rationale, no faked GIF) → Task 3. ✓
- Badges + install friction → Task 1 (badges) + Task 4 (friction, version). ✓
- CI workflow with `claude plugin validate` fallback to JSON check → Task 1. ✓
- Non-goals (no bench, no external discoverability, shipped surfaces untouched) → Global Constraints. ✓
- Verification (contract test, ruff, CI green, README renders, install sanity) → distributed across Task 1 Step 3, Task 4 Step 4, and badge/GIF embed steps. ✓

**Placeholder scan:** No TBD/TODO left in-plan. The one deliberate conditional — GIF may not render if VHS absent — is spec-sanctioned and handled explicitly (commit tape, embed reference, note pending), not a placeholder.

**Type consistency:** Badge URL in Task 1 (`ci.yml/badge.svg`) matches the workflow filename created in Task 1. Sample brief section names in Task 2 match `agents/haiku-scribe.md` Response Shape headings (verified by Task 2 Step 2). GIF path `assets/demo.gif` consistent across Task 3 Steps 1/3/5. Version `0.2.0` consistent with target release.
