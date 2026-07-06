# V1 Guidance Routing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement plan task-by-task.

**Goal:** Strengthen the `haiku-scribe setup` guidance block so Claude treats Haiku Scribe as a mandatory pre-exploration routing step for bulk reading.

**Architecture:** The feature remains a static guidance-rendering change in `src/haiku_scribe/contracts.py`. Tests assert the guidance contract directly and through the existing setup path; no runtime hooks, nudges, enforcement, or subagent authority changes are introduced.

**Tech Stack:** Python 3.11+, setuptools package, pytest, Markdown guidance blocks installed into Claude configuration.

## Global Constraints

- Keep the change inside the existing owned `<!-- HAIKU_SCRIBE_START -->` / `<!-- HAIKU_SCRIBE_END -->` block.
- Preserve the installed `haiku-scribe` subagent's read-only contract.
- Do not add hooks, audit events, prompt nudges beyond static `CLAUDE.md` guidance, soft enforcement, or blocking behavior.
- Do not change the `haiku-scribe` subagent tools, model, or authority.
- Preserve setup idempotency, backups, doctor behavior, uninstall ownership, and settings merge behavior.
- Use TDD: write failing tests before implementation.

---

### Task 1: Strengthen Installed Guidance Routing

**Files:**
- Create: `tests/test_contracts.py`
- Modify: `src/haiku_scribe/contracts.py`
- Verify: `tests/test_cli_setup.py`, `tests/test_doctor.py`, `tests/test_uninstall.py`

**Interfaces:**
- Consumes: `haiku_scribe.contracts.render_guidance_block() -> str`
- Produces: A stronger guidance block returned by `render_guidance_block()` and installed unchanged by existing setup code.

- [ ] **Step 1: Write failing guidance contract tests**

Create `tests/test_contracts.py`:

```python
from __future__ import annotations

from haiku_scribe.contracts import GUIDANCE_END, GUIDANCE_START, render_guidance_block


def test_guidance_requires_scribe_before_bulk_exploration() -> None:
    guidance = render_guidance_block()

    assert GUIDANCE_START in guidance
    assert GUIDANCE_END in guidance
    assert "Before broad code exploration, call `haiku-scribe` first." in guidance
    assert "You are about to read 3+ files." in guidance
    assert "Do not read files yourself first" in guidance


def test_guidance_separates_evidence_gathering_from_final_judgment() -> None:
    guidance = render_guidance_block()

    assert "Haiku Scribe gathers compact evidence." in guidance
    assert "Main Claude performs focused direct reads" in guidance
    assert "Main Claude makes final decisions, edits, commits, and user-facing conclusions." in guidance
    assert "These exclusions apply to final judgment, not pre-analysis." in guidance


def test_guidance_stays_static_and_non_enforcing() -> None:
    guidance = render_guidance_block()

    assert "hooks" not in guidance.lower()
    assert "soft enforcement" not in guidance.lower()
    assert "block direct reads" not in guidance.lower()
```

- [ ] **Step 2: Run the new tests and verify they fail**

Run:

```bash
rtk pytest tests/test_contracts.py -q
```

Expected: FAIL because the current guidance block does not include the mandatory pre-exploration wording or final-judgment clarification.

- [ ] **Step 3: Update the rendered guidance block**

Modify only `render_guidance_block()` in `src/haiku_scribe/contracts.py`. Replace the body between `{GUIDANCE_START}` and `{GUIDANCE_END}` with:

```python
def render_guidance_block() -> str:
    return f"""{GUIDANCE_START}
## Cost-aware Scribe routing

Before broad code exploration, call `haiku-scribe` first.

Mandatory triggers:
- You are about to read 3+ files.
- You are about to read a file likely over 400 lines mainly for orientation.
- You need to map a flow across files.
- You need to summarize logs, transcripts, generated bundles, large docs, or noisy tool output.
- You need evidence before debugging, review, architecture, or scope reasoning.
- The user asks to review, analyze, explore, understand, audit, map, or find code across an unfamiliar area.

Workflow:
1. Haiku Scribe gathers compact evidence.
2. Main Claude performs focused direct reads on the highest-value locations.
3. Main Claude makes final decisions, edits, commits, and user-facing conclusions.

Haiku Scribe may gather evidence for tasks that eventually require debugging, architecture, scope, or review judgment. These exclusions apply to final judgment, not pre-analysis.

Do not delegate:
- final debugging root-cause conclusions;
- architecture decisions;
- security, authentication, authorization, or permission-sensitive conclusions;
- precise edits;
- final PR summaries;
- commits.

Red flags:
- "I will just inspect a few files first" means call `haiku-scribe`.
- "I need context first" means call `haiku-scribe`.
- "This probably only needs a quick grep" is not a reason to skip `haiku-scribe` when a mandatory trigger applies.

Do not read files yourself first and then decide whether Haiku Scribe was needed.

If `haiku-scribe` is unavailable, say so explicitly and continue manually.

Main Claude must verify important claims before editing.
{GUIDANCE_END}

"""
```

- [ ] **Step 4: Run the new tests and verify they pass**

Run:

```bash
rtk pytest tests/test_contracts.py -q
```

Expected: PASS.

- [ ] **Step 5: Run existing setup, doctor, and uninstall regression tests**

Run:

```bash
rtk pytest tests/test_cli_setup.py tests/test_doctor.py tests/test_uninstall.py -q
```

Expected: PASS.

- [ ] **Step 6: Run the full test suite**

Run:

```bash
rtk pytest -q
```

Expected: PASS.

- [ ] **Step 7: Review the diff for scope boundaries**

Run:

```bash
rtk git diff -- tests/test_contracts.py src/haiku_scribe/contracts.py
```

Confirm:
- No changes to `render_agent_markdown()`.
- No changes to deny rules.
- No hooks, audit, nudges, enforcement, or blocking behavior.
- The stronger wording remains inside the owned guidance block only.

- [ ] **Step 8: Commit the implementation**

Run:

```bash
rtk git add tests/test_contracts.py src/haiku_scribe/contracts.py
rtk git commit -m "fix: strengthen haiku scribe guidance routing"
```

Expected: one implementation commit containing only the guidance renderer and focused tests.
