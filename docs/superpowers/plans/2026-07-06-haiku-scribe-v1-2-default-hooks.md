# Haiku Scribe V1.2 Default Hooks Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Promote V1.2 prompt nudges into the normal `haiku-scribe setup` flow with bounded hooks, stricter triggers, doctor validation, uninstall cleanup, and benchmark evidence.

**Architecture:** Keep the hook rendering and hook settings merge logic in `src/haiku_scribe/v1_2_hooks.py`. Normal setup/uninstall/doctor call those helpers instead of duplicating hook knowledge. The installed agent remains read-only through `contracts.py`; hooks nudge the main session but never block tools.

**Tech Stack:** Python 3.11+, standard library only, `pytest`, Claude Code settings JSON under `~/.claude/settings.json`.

## Global Constraints

- V1.2 hooks are installed by default during `haiku-scribe setup`.
- `PreToolUse` matcher is exactly `Read|Grep`.
- `Bash`, `Agent`, MCP tools, and file editing stay unavailable to `haiku-scribe`.
- Hook anti-self-nudge returns `0` silently for `agent_type == "haiku-scribe"`, `is_sidechain == true`, or `transcript_path` containing `/subagents/`.
- `PreToolUse` nudges at most once per `session_id` and `prompt_id`.
- Removed trigger markers do not match by themselves: `log`, `repo`, `flow`, `map`, `summarize`, `unfamiliar`.
- Specific trigger markers match: `architecture`, `audit`, `large file`, `mapping`, `transcript`, `scan the repo`, `explore the repo`, `map the flow`, `data flow`, `plusieurs fichiers`, `cartographie`.
- The installed agent frontmatter remains `tools: Read, Glob, Grep`.
- The agent contract includes a target of about 12 file reads and stopping around 15 file reads unless named files were explicitly requested.
- Hook failures must not block Claude Code usage.
- Existing user-owned settings, hooks, and guidance outside Haiku Scribe-owned regions must be preserved.

---

## File Structure

- Modify `src/haiku_scribe/v1_2_hooks.py`: Own V1.2 hook script rendering, hook path/command helpers, settings merge/removal helpers, and compatibility wrappers for `prototype-hooks`.
- Modify `src/haiku_scribe/contracts.py`: Add the exploration budget to the generated agent markdown while keeping the read-only tool contract.
- Modify `src/haiku_scribe/setup.py`: Install V1.2 hooks by default as part of normal setup.
- Modify `src/haiku_scribe/uninstall.py`: Remove V1.2 hooks by default as part of normal uninstall.
- Modify `src/haiku_scribe/doctor.py`: Validate V1.2 hook files, settings entries, matcher, and ownership metadata.
- Modify `src/haiku_scribe/cli.py`: Keep `prototype-hooks` as a temporary compatibility path; normal commands should now handle hooks.
- Modify `tests/test_hooks_proto.py`: Convert prototype hook tests into V1.2 behavior tests while retaining CLI compatibility coverage.
- Modify `tests/test_cli_setup.py`: Assert normal setup installs hooks and normal uninstall removes them.
- Modify or add `tests/test_contracts.py`: Assert the agent contract includes the exploration budget and keeps read-only tools.
- Add `docs/superpowers/evaluations/2026-07-06-v1-2-default-hooks-bench.md`: Record the rerun benchmark metrics after implementation.

---

### Task 1: Harden The V1.2 Hook Script And Settings Helpers

**Files:**
- Modify: `src/haiku_scribe/v1_2_hooks.py`
- Modify: `tests/test_hooks_proto.py`

**Interfaces:**
- Produces: `render_nudge_hook_script() -> str`
- Produces: `merge_v1_2_hook(settings: dict[str, Any], command: str) -> dict[str, Any]`
- Produces: `remove_v1_2_hook(settings: dict[str, Any], command: str) -> bool`
- Produces: `hook_path_for(paths: ClaudePaths) -> Path`
- Produces: `hook_command_for(hook_path: Path) -> str`
- Produces: compatibility aliases `merge_prototype_hook = merge_v1_2_hook` and `remove_prototype_hook = remove_v1_2_hook`
- Consumes: `ClaudePaths.for_home(home: Path) -> ClaudePaths`

- [ ] **Step 1: Write failing tests for self-nudge silence**

Add these tests to `tests/test_hooks_proto.py`:

```python
def test_hook_ignores_haiku_scribe_agent_type_silently(tmp_path: Path) -> None:
    hook_path = tmp_path / ".claude" / "hooks" / "haiku-scribe-v1-2-nudge.py"
    hook_path.parent.mkdir(parents=True)
    hook_path.write_text(render_nudge_hook_script(), encoding="utf-8")

    result = run_hook(
        hook_path,
        {
            "hook_event_name": "UserPromptSubmit",
            "session_id": "s1",
            "prompt_id": "p1",
            "cwd": str(tmp_path),
            "agent_type": "haiku-scribe",
            "prompt": "scan the repo architecture",
        },
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""
    assert not (tmp_path / ".claude" / "haiku-scribe-nudges.jsonl").exists()


def test_hook_ignores_sidechain_silently(tmp_path: Path) -> None:
    hook_path = tmp_path / ".claude" / "hooks" / "haiku-scribe-v1-2-nudge.py"
    hook_path.parent.mkdir(parents=True)
    hook_path.write_text(render_nudge_hook_script(), encoding="utf-8")

    result = run_hook(
        hook_path,
        {
            "hook_event_name": "UserPromptSubmit",
            "session_id": "s1",
            "prompt_id": "p1",
            "cwd": str(tmp_path),
            "is_sidechain": True,
            "prompt": "scan the repo architecture",
        },
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""
    assert not (tmp_path / ".claude" / "haiku-scribe-nudges.jsonl").exists()


def test_hook_ignores_subagent_transcript_silently(tmp_path: Path) -> None:
    hook_path = tmp_path / ".claude" / "hooks" / "haiku-scribe-v1-2-nudge.py"
    hook_path.parent.mkdir(parents=True)
    hook_path.write_text(render_nudge_hook_script(), encoding="utf-8")

    result = run_hook(
        hook_path,
        {
            "hook_event_name": "UserPromptSubmit",
            "session_id": "s1",
            "prompt_id": "p1",
            "cwd": str(tmp_path),
            "transcript_path": "/tmp/claude/subagents/haiku-scribe/session.jsonl",
            "prompt": "scan the repo architecture",
        },
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""
    assert not (tmp_path / ".claude" / "haiku-scribe-nudges.jsonl").exists()
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
rtk python -m pytest tests/test_hooks_proto.py::test_hook_ignores_haiku_scribe_agent_type_silently tests/test_hooks_proto.py::test_hook_ignores_sidechain_silently tests/test_hooks_proto.py::test_hook_ignores_subagent_transcript_silently -v
```

Expected: FAIL because the current hook nudges broad prompts even when the payload identifies a subagent run.

- [ ] **Step 3: Write failing tests for trigger tightening and one follow-up**

Add these tests to `tests/test_hooks_proto.py`:

```python
def test_removed_markers_do_not_trigger_by_themselves(tmp_path: Path) -> None:
    hook_path = tmp_path / ".claude" / "hooks" / "haiku-scribe-v1-2-nudge.py"
    hook_path.parent.mkdir(parents=True)
    hook_path.write_text(render_nudge_hook_script(), encoding="utf-8")

    for marker in ("log", "repo", "flow", "map", "summarize", "unfamiliar"):
        result = run_hook(
            hook_path,
            {
                "hook_event_name": "UserPromptSubmit",
                "session_id": "s1",
                "prompt_id": f"prompt-{marker}",
                "cwd": str(tmp_path),
                "prompt": marker,
            },
        )
        assert result.returncode == 0
        assert result.stdout == ""

    assert not (tmp_path / ".claude" / "haiku-scribe-nudges.jsonl").exists()


def test_specific_markers_trigger_nudge(tmp_path: Path) -> None:
    hook_path = tmp_path / ".claude" / "hooks" / "haiku-scribe-v1-2-nudge.py"
    hook_path.parent.mkdir(parents=True)
    hook_path.write_text(render_nudge_hook_script(), encoding="utf-8")

    markers = (
        "architecture",
        "audit",
        "large file",
        "mapping",
        "transcript",
        "scan the repo",
        "explore the repo",
        "map the flow",
        "data flow",
        "plusieurs fichiers",
        "cartographie",
    )
    for index, marker in enumerate(markers):
        result = run_hook(
            hook_path,
            {
                "hook_event_name": "UserPromptSubmit",
                "session_id": "s1",
                "prompt_id": f"prompt-{index}",
                "cwd": str(tmp_path),
                "prompt": marker,
            },
        )
        assert result.returncode == 0
        assert "haiku-scribe" in json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]


def test_pre_tool_hook_reinforces_only_once_per_prompt(tmp_path: Path) -> None:
    hook_path = tmp_path / ".claude" / "hooks" / "haiku-scribe-v1-2-nudge.py"
    hook_path.parent.mkdir(parents=True)
    hook_path.write_text(render_nudge_hook_script(), encoding="utf-8")

    assert run_hook(
        hook_path,
        {
            "hook_event_name": "UserPromptSubmit",
            "session_id": "s1",
            "prompt_id": "p1",
            "cwd": str(tmp_path),
            "prompt": "scan the repo architecture",
        },
    ).returncode == 0

    first = run_hook(
        hook_path,
        {
            "hook_event_name": "PreToolUse",
            "session_id": "s1",
            "prompt_id": "p1",
            "cwd": str(tmp_path),
            "tool_name": "Read",
            "tool_input": {"file_path": "src/example.py"},
        },
    )
    second = run_hook(
        hook_path,
        {
            "hook_event_name": "PreToolUse",
            "session_id": "s1",
            "prompt_id": "p1",
            "cwd": str(tmp_path),
            "tool_name": "Grep",
            "tool_input": {"pattern": "example"},
        },
    )

    assert first.returncode == 0
    assert "haiku-scribe" in json.loads(first.stdout)["hookSpecificOutput"]["additionalContext"]
    assert second.returncode == 0
    assert second.stdout == ""

    log_lines = (tmp_path / ".claude" / "haiku-scribe-nudges.jsonl").read_text(encoding="utf-8").splitlines()
    decisions = [json.loads(line)["decision"] for line in log_lines]
    assert decisions == ["nudge", "pre_tool_followup"]


def test_bash_does_not_trigger_pre_tool_followup(tmp_path: Path) -> None:
    hook_path = tmp_path / ".claude" / "hooks" / "haiku-scribe-v1-2-nudge.py"
    hook_path.parent.mkdir(parents=True)
    hook_path.write_text(render_nudge_hook_script(), encoding="utf-8")

    assert run_hook(
        hook_path,
        {
            "hook_event_name": "UserPromptSubmit",
            "session_id": "s1",
            "prompt_id": "p1",
            "cwd": str(tmp_path),
            "prompt": "scan the repo architecture",
        },
    ).returncode == 0

    result = run_hook(
        hook_path,
        {
            "hook_event_name": "PreToolUse",
            "session_id": "s1",
            "prompt_id": "p1",
            "cwd": str(tmp_path),
            "tool_name": "Bash",
            "tool_input": {"command": "rg example"},
        },
    )

    assert result.returncode == 0
    assert result.stdout == ""
```

- [ ] **Step 4: Run tests to verify they fail**

Run:

```bash
rtk python -m pytest tests/test_hooks_proto.py -v
```

Expected: FAIL on removed trigger markers, repeated `PreToolUse`, `Bash`, and matcher expectations.

- [ ] **Step 5: Implement the hook script changes**

In `src/haiku_scribe/v1_2_hooks.py`, update `render_nudge_hook_script()` so the rendered script contains these helper functions and constants:

```python
BROAD_PROMPT_MARKERS = (
    "architecture",
    "audit",
    "cartographie",
    "data flow",
    "explore the repo",
    "large file",
    "map the flow",
    "mapping",
    "plusieurs fichiers",
    "scan the repo",
    "transcript",
)

NUDGE = (
    "Haiku Scribe nudge: this prompt looks like broad context gathering. "
    "Before raw repository reads/searches, consider delegating reconnaissance "
    "to the `haiku-scribe` subagent, then verify focused evidence directly."
)

PRE_TOOL_NUDGE = (
    "Haiku Scribe follow-up: this prompt was already flagged as broad context "
    "gathering. Before continuing with direct Read/Grep exploration, use "
    "the `haiku-scribe` subagent for reconnaissance unless this is now a small "
    "focused read."
)


def should_skip_payload(payload: dict) -> bool:
    if payload.get("agent_type") == "haiku-scribe":
        return True
    if payload.get("is_sidechain") is True:
        return True
    transcript_path = str(payload.get("transcript_path", ""))
    return "/subagents/" in transcript_path


def append_event(log_path: Path, event: dict) -> None:
    with log_path.open("a", encoding="utf-8") as log:
        log.write(json.dumps(event, sort_keys=True) + "\\n")


def iter_events(log_path: Path):
    if not log_path.exists():
        return
    for line in log_path.read_text(encoding="utf-8").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict):
            yield event


def has_followup(events: list[dict], session_id: object, prompt_id: object) -> bool:
    return any(
        event.get("session_id") == session_id
        and event.get("prompt_id") == prompt_id
        and event.get("decision") == "pre_tool_followup"
        for event in events
    )


def has_initial_nudge(events: list[dict], session_id: object, prompt_id: object) -> bool:
    return any(
        event.get("session_id") == session_id
        and event.get("prompt_id") == prompt_id
        and event.get("decision") == "nudge"
        for event in events
    )
```

Then update the rendered `main()`, `handle_user_prompt_submit()`, and `handle_pre_tool_use()` bodies to use those helpers:

```python
def main() -> int:
    payload = json.load(sys.stdin)
    if should_skip_payload(payload):
        return 0
    event_name = payload.get("hook_event_name")
    if event_name == "PreToolUse":
        return handle_pre_tool_use(payload)
    if event_name == "UserPromptSubmit":
        return handle_user_prompt_submit(payload)
    return 0


def handle_user_prompt_submit(payload: dict) -> int:
    prompt = str(payload.get("prompt", "")).lower()
    matched = [marker for marker in BROAD_PROMPT_MARKERS if marker in prompt]
    if not matched:
        return 0

    claude_dir = Path(__file__).resolve().parents[1]
    log_path = claude_dir / "haiku-scribe-nudges.jsonl"
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "decision": "nudge",
        "reason": "broad_prompt_marker",
        "matched": matched,
        "session_id": payload.get("session_id"),
        "prompt_id": payload.get("prompt_id"),
        "cwd": payload.get("cwd"),
    }
    append_event(log_path, event)

    print(
        json.dumps(
            {
                "suppressOutput": True,
                "hookSpecificOutput": {
                    "hookEventName": "UserPromptSubmit",
                    "additionalContext": NUDGE,
                },
            }
        )
    )
    return 0


def handle_pre_tool_use(payload: dict) -> int:
    tool_name = payload.get("tool_name")
    if tool_name not in {"Read", "Grep"}:
        return 0

    claude_dir = Path(__file__).resolve().parents[1]
    log_path = claude_dir / "haiku-scribe-nudges.jsonl"
    events = list(iter_events(log_path))

    session_id = payload.get("session_id")
    prompt_id = payload.get("prompt_id")
    if not has_initial_nudge(events, session_id, prompt_id):
        return 0
    if has_followup(events, session_id, prompt_id):
        return 0

    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "decision": "pre_tool_followup",
        "reason": "direct_tool_after_nudge",
        "session_id": session_id,
        "prompt_id": prompt_id,
        "cwd": payload.get("cwd"),
        "tool_name": tool_name,
    }
    append_event(log_path, event)
    print(
        json.dumps(
            {
                "suppressOutput": True,
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "additionalContext": PRE_TOOL_NUDGE,
                },
            }
        )
    )
    return 0
```

- [ ] **Step 6: Rename settings helpers while keeping compatibility**

In `src/haiku_scribe/v1_2_hooks.py`, add public V1.2 helper names and keep prototype aliases:

```python
def hook_path_for(paths: ClaudePaths) -> Path:
    return paths.claude_dir / "hooks" / HOOK_SCRIPT_NAME


def hook_command_for(hook_path: Path) -> str:
    return f"python3 {hook_path}"


def merge_v1_2_hook(settings: dict[str, Any], command: str) -> dict[str, Any]:
    merged = json.loads(json.dumps(settings))
    hooks = merged.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise ValueError("settings.hooks must be a JSON object")

    prompt_groups = hooks.setdefault("UserPromptSubmit", [])
    if not isinstance(prompt_groups, list):
        raise ValueError("settings.hooks.UserPromptSubmit must be a JSON array")
    _append_group_once(
        prompt_groups,
        {
            "matcher": "",
            "hooks": [{"type": "command", "command": command}],
        },
    )

    pre_tool_groups = hooks.setdefault("PreToolUse", [])
    if not isinstance(pre_tool_groups, list):
        raise ValueError("settings.hooks.PreToolUse must be a JSON array")
    _append_group_once(
        pre_tool_groups,
        {
            "matcher": "Read|Grep",
            "hooks": [{"type": "command", "command": command}],
        },
    )

    ownership = merged.setdefault("haiku_scribe", {})
    if not isinstance(ownership, dict):
        raise ValueError("settings.haiku_scribe must be a JSON object")
    ownership[OWNED_HOOK_COMMAND_KEY] = command
    return merged


def remove_v1_2_hook(settings: dict[str, Any], command: str) -> bool:
    return remove_prototype_hook(settings, command)
```

Then update `_hook_path()` and `_hook_command()` to call the new names:

```python
def _hook_path(paths: ClaudePaths) -> Path:
    return hook_path_for(paths)


def _hook_command(hook_path: Path) -> str:
    return hook_command_for(hook_path)
```

Update `setup_prototype_hooks()` to call `merge_v1_2_hook(settings, command)`.

- [ ] **Step 7: Run hook tests**

Run:

```bash
rtk python -m pytest tests/test_hooks_proto.py -v
```

Expected: PASS.

- [ ] **Step 8: Commit Task 1**

Run:

```bash
rtk git add src/haiku_scribe/v1_2_hooks.py tests/test_hooks_proto.py
rtk git commit -m "fix: harden v1.2 nudge hook"
```

Expected: commit succeeds with only hook behavior and hook tests.

---

### Task 2: Add The Agent Exploration Budget

**Files:**
- Modify: `src/haiku_scribe/contracts.py`
- Modify or create: `tests/test_contracts.py`

**Interfaces:**
- Consumes: `render_agent_markdown() -> str`
- Produces: installed agent markdown containing `tools: Read, Glob, Grep`
- Produces: installed agent markdown containing budget phrases `Target about 12 file reads` and `Stop around 15 file reads`

- [ ] **Step 1: Write failing contract tests**

If `tests/test_contracts.py` exists, add these tests. If it does not exist, create it with this content:

```python
from __future__ import annotations

from haiku_scribe.contracts import render_agent_markdown


def test_agent_tools_remain_read_only() -> None:
    agent = render_agent_markdown()

    assert "tools: Read, Glob, Grep" in agent
    assert "Bash" not in agent.split("---", 2)[1]
    assert "Agent" not in agent.split("---", 2)[1]


def test_agent_contract_includes_exploration_budget() -> None:
    agent = render_agent_markdown()

    assert "Target about 12 file reads." in agent
    assert "Stop around 15 file reads unless the main session explicitly named the files to inspect." in agent
    assert "Do not run open-ended exploration loops." in agent
    assert "Keep the response short." in agent
```

- [ ] **Step 2: Run contract tests to verify failure**

Run:

```bash
rtk python -m pytest tests/test_contracts.py -v
```

Expected: FAIL because the budget phrases are not yet present.

- [ ] **Step 3: Update the agent markdown**

In `src/haiku_scribe/contracts.py`, update the `## How To Read` section inside `render_agent_markdown()` to include these bullets after the large-file bullet:

```markdown
- Keep the response short.
- Target about 12 file reads.
- Stop around 15 file reads unless the main session explicitly named the files to inspect.
- Do not run open-ended exploration loops.
- Stop once the brief has enough evidence, unknowns, and suggested direct reads.
```

Keep the existing frontmatter unchanged:

```yaml
name: haiku-scribe
description: Read-only context compression worker. Use when remaining work is broad context gathering: 4+ files, large files, directory/repo survey, logs, generated output, transcripts, architecture review, flow mapping, pattern audit, unfamiliar-area exploration, or evidence extraction before broad reasoning. Skip for small focused reads: 3 or fewer small files with no directory reads, shell search, logs, generated output, or cross-layer mapping. Do not use for final reasoning, edits, security conclusions, architecture decisions, commits, or public summaries.
model: haiku
tools: Read, Glob, Grep
```

- [ ] **Step 4: Run contract tests**

Run:

```bash
rtk python -m pytest tests/test_contracts.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit Task 2**

Run:

```bash
rtk git add src/haiku_scribe/contracts.py tests/test_contracts.py
rtk git commit -m "docs: add haiku scribe exploration budget"
```

Expected: commit succeeds with agent contract and tests.

---

### Task 3: Install V1.2 Hooks During Normal Setup

**Files:**
- Modify: `src/haiku_scribe/setup.py`
- Modify: `tests/test_cli_setup.py`

**Interfaces:**
- Consumes: `render_nudge_hook_script() -> str`
- Consumes: `hook_path_for(paths: ClaudePaths) -> Path`
- Consumes: `hook_command_for(hook_path: Path) -> str`
- Consumes: `merge_v1_2_hook(settings: dict[str, Any], command: str) -> dict[str, Any]`
- Produces: `setup_user(home: Path, dry_run: bool = False) -> SetupResult` writes hook script and merged hook settings by default

- [ ] **Step 1: Write failing setup tests**

Add this test to `tests/test_cli_setup.py`:

```python
def test_setup_installs_v1_2_hooks_by_default(tmp_path: Path) -> None:
    result = run_cli("setup", "--home", str(tmp_path))

    assert result.returncode == 0
    hook_path = tmp_path / ".claude" / "hooks" / "haiku-scribe-v1-2-nudge.py"
    settings_path = tmp_path / ".claude" / "settings.json"
    assert hook_path.exists()

    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    command = settings["haiku_scribe"]["owned_v1_2_nudge_hook_command"]
    assert command.endswith("haiku-scribe-v1-2-nudge.py")
    assert settings["hooks"]["UserPromptSubmit"] == [
        {"matcher": "", "hooks": [{"type": "command", "command": command}]}
    ]
    assert settings["hooks"]["PreToolUse"] == [
        {"matcher": "Read|Grep", "hooks": [{"type": "command", "command": command}]}
    ]
```

Update `test_setup_dry_run_writes_nothing()` to assert dry-run mentions the hook:

```python
def test_setup_dry_run_writes_nothing(tmp_path: Path) -> None:
    result = run_cli("setup", "--dry-run", "--home", str(tmp_path))

    assert result.returncode == 0
    assert "Dry run" in result.stdout
    assert "Would write" in result.stdout
    assert "haiku-scribe-v1-2-nudge.py" in result.stdout
    assert not (tmp_path / ".claude").exists()
```

Update `test_setup_is_idempotent()` to include hook idempotency:

```python
def test_setup_is_idempotent(tmp_path: Path) -> None:
    first = run_cli("setup", "--home", str(tmp_path))
    second = run_cli("setup", "--home", str(tmp_path))

    assert first.returncode == 0
    assert second.returncode == 0
    guidance = (tmp_path / ".claude" / "CLAUDE.md").read_text(encoding="utf-8")
    settings = json.loads((tmp_path / ".claude" / "settings.json").read_text(encoding="utf-8"))
    assert guidance.count("HAIKU_SCRIBE_START") == 1
    assert settings["permissions"]["deny"].count("Read(**/*credential*)") == 1
    assert len(settings["hooks"]["UserPromptSubmit"]) == 1
    assert len(settings["hooks"]["PreToolUse"]) == 1
```

- [ ] **Step 2: Run setup tests to verify failure**

Run:

```bash
rtk python -m pytest tests/test_cli_setup.py::test_setup_installs_v1_2_hooks_by_default tests/test_cli_setup.py::test_setup_dry_run_writes_nothing tests/test_cli_setup.py::test_setup_is_idempotent -v
```

Expected: FAIL because normal setup does not yet install V1.2 hooks.

- [ ] **Step 3: Implement hook installation in setup**

In `src/haiku_scribe/setup.py`, add imports:

```python
from haiku_scribe.v1_2_hooks import (
    hook_command_for,
    hook_path_for,
    merge_v1_2_hook,
    render_nudge_hook_script,
)
```

Update the `planned` list in `setup_user()`:

```python
hook_path = hook_path_for(paths)
hook_command = hook_command_for(hook_path)
planned = [
    f"Would write {paths.agent_path}",
    f"Would update {paths.guidance_path}",
    f"Would merge deny rules into {paths.settings_path}",
    f"Would write {hook_path}",
    f"Would merge UserPromptSubmit and PreToolUse hooks into {paths.settings_path}",
]
```

Create the hooks directory before writing:

```python
paths.agents_dir.mkdir(parents=True, exist_ok=True)
paths.claude_dir.mkdir(parents=True, exist_ok=True)
hook_path.parent.mkdir(parents=True, exist_ok=True)
```

Merge deny rules and hook settings in one settings object:

```python
settings = merge_deny_rules(load_json_object(paths.settings_path), DEFAULT_DENY_RULES)
settings = merge_v1_2_hook(settings, hook_command)
settings_text = json.dumps(settings, indent=2, sort_keys=True) + "\n"
hook_text = render_nudge_hook_script()
```

Write and back up the hook script before settings:

```python
if hook_path.exists() and hook_path.read_text(encoding="utf-8") != hook_text:
    backup_existing(hook_path, paths.claude_dir / "backups" / "haiku-scribe")
if _write_text_if_changed(hook_path, hook_text):
    written.append(hook_path)
```

- [ ] **Step 4: Run setup tests**

Run:

```bash
rtk python -m pytest tests/test_cli_setup.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit Task 3**

Run:

```bash
rtk git add src/haiku_scribe/setup.py tests/test_cli_setup.py
rtk git commit -m "feat: install v1.2 hooks by default"
```

Expected: commit succeeds with setup integration and tests.

---

### Task 4: Remove V1.2 Hooks During Normal Uninstall

**Files:**
- Modify: `src/haiku_scribe/uninstall.py`
- Modify: `tests/test_cli_setup.py`

**Interfaces:**
- Consumes: `hook_path_for(paths: ClaudePaths) -> Path`
- Consumes: `hook_command_for(hook_path: Path) -> str`
- Consumes: `remove_v1_2_hook(settings: dict[str, Any], command: str) -> bool`
- Produces: `uninstall_user(home: Path, dry_run: bool = False) -> UninstallResult` removes managed hook entries and script

- [ ] **Step 1: Write failing uninstall test**

Add this test to `tests/test_cli_setup.py`:

```python
def test_uninstall_removes_v1_2_hooks_but_preserves_user_hooks(tmp_path: Path) -> None:
    settings_path = tmp_path / ".claude" / "settings.json"
    settings_path.parent.mkdir(parents=True)
    settings_path.write_text(
        json.dumps(
            {
                "hooks": {
                    "UserPromptSubmit": [
                        {
                            "matcher": "",
                            "hooks": [{"type": "command", "command": "echo keep"}],
                        }
                    ]
                }
            }
        ),
        encoding="utf-8",
    )

    setup = run_cli("setup", "--home", str(tmp_path))
    uninstall = run_cli("uninstall", "--home", str(tmp_path))

    assert setup.returncode == 0
    assert uninstall.returncode == 0
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    assert settings["hooks"]["UserPromptSubmit"] == [
        {"matcher": "", "hooks": [{"type": "command", "command": "echo keep"}]}
    ]
    assert "PreToolUse" not in settings["hooks"]
    assert "owned_v1_2_nudge_hook_command" not in settings.get("haiku_scribe", {})
    assert not (tmp_path / ".claude" / "hooks" / "haiku-scribe-v1-2-nudge.py").exists()
```

- [ ] **Step 2: Run uninstall test to verify failure**

Run:

```bash
rtk python -m pytest tests/test_cli_setup.py::test_uninstall_removes_v1_2_hooks_but_preserves_user_hooks -v
```

Expected: FAIL because normal uninstall does not yet remove hook entries or the hook script.

- [ ] **Step 3: Implement hook removal in uninstall**

In `src/haiku_scribe/uninstall.py`, add imports:

```python
from haiku_scribe.v1_2_hooks import hook_command_for, hook_path_for, remove_v1_2_hook
```

Near the start of `uninstall_user()`, compute:

```python
hook_path = hook_path_for(paths)
hook_command = hook_command_for(hook_path)
```

Inside the settings block, after `remove_owned_deny_rules(settings)`, remove the hook:

```python
deny_changed = remove_owned_deny_rules(settings)
hook_changed = remove_v1_2_hook(settings, hook_command)
settings_changed = deny_changed or hook_changed
```

Append dry-run plans:

```python
if hook_changed:
    planned.append(f"Would remove owned V1.2 hooks from {paths.settings_path}")
```

Add hook script planning:

```python
if hook_path.exists():
    planned.append(f"Would remove {hook_path}")
```

After writing settings, remove the script:

```python
if hook_path.exists():
    hook_path.unlink()
    removed.append(hook_path)
```

- [ ] **Step 4: Run uninstall and full CLI tests**

Run:

```bash
rtk python -m pytest tests/test_cli_setup.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit Task 4**

Run:

```bash
rtk git add src/haiku_scribe/uninstall.py tests/test_cli_setup.py
rtk git commit -m "feat: uninstall v1.2 hooks"
```

Expected: commit succeeds with uninstall integration and tests.

---

### Task 5: Validate V1.2 Hooks In Doctor

**Files:**
- Modify: `src/haiku_scribe/doctor.py`
- Modify: `tests/test_cli_setup.py`

**Interfaces:**
- Consumes: `hook_path_for(paths: ClaudePaths) -> Path`
- Consumes: `hook_command_for(hook_path: Path) -> str`
- Produces: `doctor_user(home: Path) -> DoctorResult` checks hook script, settings entries, matcher, and ownership metadata

- [ ] **Step 1: Write failing doctor tests**

Add these tests to `tests/test_cli_setup.py`:

```python
def test_doctor_fails_when_v1_2_hook_script_missing(tmp_path: Path) -> None:
    assert run_cli("setup", "--home", str(tmp_path)).returncode == 0
    (tmp_path / ".claude" / "hooks" / "haiku-scribe-v1-2-nudge.py").unlink()

    result = run_cli("doctor", "--home", str(tmp_path))

    assert result.returncode == 1
    assert "missing V1.2 hook script" in result.stdout


def test_doctor_fails_when_v1_2_pre_tool_matcher_wrong(tmp_path: Path) -> None:
    assert run_cli("setup", "--home", str(tmp_path)).returncode == 0
    settings_path = tmp_path / ".claude" / "settings.json"
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    settings["hooks"]["PreToolUse"][0]["matcher"] = "Read|Grep|Bash"
    settings_path.write_text(json.dumps(settings), encoding="utf-8")

    result = run_cli("doctor", "--home", str(tmp_path))

    assert result.returncode == 1
    assert "missing V1.2 PreToolUse hook with matcher Read|Grep" in result.stdout


def test_doctor_fails_when_v1_2_hook_ownership_missing(tmp_path: Path) -> None:
    assert run_cli("setup", "--home", str(tmp_path)).returncode == 0
    settings_path = tmp_path / ".claude" / "settings.json"
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    settings["haiku_scribe"].pop("owned_v1_2_nudge_hook_command")
    settings_path.write_text(json.dumps(settings), encoding="utf-8")

    result = run_cli("doctor", "--home", str(tmp_path))

    assert result.returncode == 1
    assert "missing V1.2 hook ownership metadata" in result.stdout
```

- [ ] **Step 2: Run doctor tests to verify failure**

Run:

```bash
rtk python -m pytest tests/test_cli_setup.py::test_doctor_fails_when_v1_2_hook_script_missing tests/test_cli_setup.py::test_doctor_fails_when_v1_2_pre_tool_matcher_wrong tests/test_cli_setup.py::test_doctor_fails_when_v1_2_hook_ownership_missing -v
```

Expected: FAIL because doctor does not yet validate hooks.

- [ ] **Step 3: Implement doctor hook checks**

In `src/haiku_scribe/doctor.py`, add imports:

```python
from typing import Any

from haiku_scribe.v1_2_hooks import hook_command_for, hook_path_for
```

Add these helpers:

```python
def _group_has_command(groups: Any, matcher: str, command: str) -> bool:
    if not isinstance(groups, list):
        return False
    expected = {"type": "command", "command": command}
    for group in groups:
        if not isinstance(group, dict):
            continue
        if group.get("matcher") != matcher:
            continue
        hooks = group.get("hooks")
        if isinstance(hooks, list) and expected in hooks:
            return True
    return False


def _check_v1_2_hook(paths: ClaudePaths, settings: dict[str, Any]) -> list[str]:
    hook_path = hook_path_for(paths)
    command = hook_command_for(hook_path)
    failures: list[str] = []

    if not hook_path.exists():
        failures.append("missing V1.2 hook script")

    ownership = settings.get("haiku_scribe")
    if not isinstance(ownership, dict) or ownership.get("owned_v1_2_nudge_hook_command") != command:
        failures.append("missing V1.2 hook ownership metadata")

    hooks = settings.get("hooks")
    if not isinstance(hooks, dict):
        failures.append("settings hooks must be a JSON object")
        return failures

    if not _group_has_command(hooks.get("UserPromptSubmit"), "", command):
        failures.append("missing V1.2 UserPromptSubmit hook")
    if not _group_has_command(hooks.get("PreToolUse"), "Read|Grep", command):
        failures.append("missing V1.2 PreToolUse hook with matcher Read|Grep")

    return failures
```

Update `_check_settings_file()` so it accepts `paths: ClaudePaths` and calls `_check_v1_2_hook(paths, settings)` after deny-rule checks:

```python
def _check_settings_file(paths: ClaudePaths) -> list[str]:
    settings_path = paths.settings_path
    if not settings_path.exists():
        return ["missing settings file"]

    try:
        settings = load_json_object(settings_path)
    except SettingsError as exc:
        return [str(exc)]

    permissions = settings.get("permissions", {})
    if not isinstance(permissions, dict):
        return ["settings permissions must be a JSON object"]

    deny = permissions.get("deny", [])
    if not isinstance(deny, list):
        return ["settings permissions.deny not array"]

    failures: list[str] = []
    for rule in DEFAULT_DENY_RULES:
        if rule not in deny:
            failures.append(f"missing deny rule: {rule}")
    failures.extend(_check_v1_2_hook(paths, settings))
    return failures
```

Update `doctor_user()`:

```python
def doctor_user(home: Path) -> DoctorResult:
    paths = ClaudePaths.for_home(home)
    failures = []
    failures.extend(_check_agent_file(paths.agent_path))
    failures.extend(_check_guidance_file(paths.guidance_path))
    failures.extend(_check_settings_file(paths))
    return DoctorResult(ok=not failures, failures=failures)
```

- [ ] **Step 4: Run doctor and full CLI tests**

Run:

```bash
rtk python -m pytest tests/test_cli_setup.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit Task 5**

Run:

```bash
rtk git add src/haiku_scribe/doctor.py tests/test_cli_setup.py
rtk git commit -m "feat: validate v1.2 hooks in doctor"
```

Expected: commit succeeds with doctor validation and tests.

---

### Task 6: Keep Prototype CLI Compatibility And Verify The Suite

**Files:**
- Modify: `src/haiku_scribe/cli.py`
- Modify: `tests/test_hooks_proto.py`
- Modify: `README.md`

**Interfaces:**
- Consumes: `setup_prototype_hooks(home: Path, dry_run: bool = False) -> PrototypeHooksResult`
- Consumes: `uninstall_prototype_hooks(home: Path, dry_run: bool = False) -> PrototypeHooksResult`
- Produces: `haiku-scribe setup` as the documented V1.2 install path
- Produces: `haiku-scribe prototype-hooks` as a temporary compatibility command

- [ ] **Step 1: Update compatibility test expectations**

In `tests/test_hooks_proto.py`, update `test_prototype_hooks_install_is_idempotent()` so the matcher expectation is:

```python
assert pre_tool_groups[0]["matcher"] == "Read|Grep"
```

Add this test to ensure the compatibility command still works:

```python
def test_prototype_hooks_command_remains_compatible(tmp_path: Path) -> None:
    setup = run_cli("prototype-hooks", "setup", "--home", str(tmp_path))
    uninstall = run_cli("prototype-hooks", "uninstall", "--home", str(tmp_path))

    assert setup.returncode == 0
    assert uninstall.returncode == 0
    assert not (tmp_path / ".claude" / "hooks" / "haiku-scribe-v1-2-nudge.py").exists()
```

- [ ] **Step 2: Update README status and commands**

In `README.md`, update the status section so the normal setup description includes hooks:

```markdown
implementation includes:
- generated `~/.claude/agents/haiku-scribe.md` subagent;
- managed Haiku Scribe guidance block in `~/.claude/CLAUDE.md`;
- merged read-deny rules in `~/.claude/settings.json`;
- V1.2 prompt nudge hooks under `~/.claude/hooks/`;
- ownership metadata for deny rules and V1.2 hook entries;
- backups before mutating existing Claude Code files;
- dry-run support setup uninstall;
- `doctor` checks missing files, unsafe agent drift, missing guidance, missing deny rules, and V1.2 hooks;
- focused pytest coverage setup, doctor, uninstall, settings merge, markdown block handling, agent contract, hook behavior.
```

Remove `automatic invocation hooks` from the out-of-scope list and replace it with:

```markdown
- hard blocking of direct reads;
```

- [ ] **Step 3: Run the full test suite**

Run:

```bash
rtk python -m pytest -v
```

Expected: PASS.

- [ ] **Step 4: Commit Task 6**

Run:

```bash
rtk git add src/haiku_scribe/cli.py tests/test_hooks_proto.py README.md
rtk git commit -m "docs: document v1.2 default hooks"
```

Expected: commit succeeds with CLI compatibility expectations and README docs.

---

### Task 7: Re-Run And Document The V1.2 Benchmark

**Files:**
- Create: `docs/superpowers/evaluations/2026-07-06-v1-2-default-hooks-bench.md`

**Interfaces:**
- Consumes: benchmark procedure already used for `docs/superpowers/evaluations/2026-07-05-codegraph-agent-bench.md`
- Produces: benchmark record comparing V1.2 default hooks against prior run

- [ ] **Step 1: Run the benchmark procedure**

Use the same benchmark workflow used for the prior V1.2 evaluation. Capture these metrics for the new run:

```text
first cache_creation_input_tokens
total cache_creation_input_tokens
total cache_read_input_tokens
number of subagent messages
number of direct reads
final cost
whether PreToolUse nudged only once
whether haiku-scribe avoided self-nudging
whether the haiku-scribe response stayed short and within the intended exploration budget
```

Expected: You have a concrete metric set from a run with hooks installed through normal `haiku-scribe setup`.

- [ ] **Step 2: Write the benchmark document**

Create `docs/superpowers/evaluations/2026-07-06-v1-2-default-hooks-bench.md` after Step 1 has concrete run data. The document must contain:

```markdown
# Haiku Scribe V1.2 Default Hooks Benchmark

Date: 2026-07-06
Setup path: `haiku-scribe setup`
Compared against: `docs/superpowers/evaluations/2026-07-05-codegraph-agent-bench.md`

## Results

A three-column table with these columns: `Metric`, `Prior Run`, `V1.2 Default Hooks`.

The table must include rows for:
- First `cache_creation_input_tokens`
- Total `cache_creation_input_tokens`
- Total `cache_read_input_tokens`
- Subagent messages
- Direct reads
- Final cost

Every table value must be either a captured benchmark value or `not captured`.

## Hook Observations

Three bullets recording the observed yes/no result for:
- `PreToolUse` nudged only once per prompt
- `haiku-scribe` avoided self-nudging
- `haiku-scribe` response stayed short and within the intended exploration budget

## Notes

Explain any `not captured` metric and any qualitative observations that affect confidence.
```

- [ ] **Step 3: Run final verification**

Run:

```bash
rtk python -m pytest -v
```

Expected: PASS.

Run:

```bash
rtk git status --short
```

Expected: only `docs/superpowers/evaluations/2026-07-06-v1-2-default-hooks-bench.md` is unstaged.

- [ ] **Step 4: Commit Task 7**

Run:

```bash
rtk git add -f docs/superpowers/evaluations/2026-07-06-v1-2-default-hooks-bench.md
rtk git commit -m "docs: benchmark v1.2 default hooks"
```

Expected: commit succeeds with the benchmark document.

---

## Final Verification

- [ ] **Step 1: Run the complete test suite**

Run:

```bash
rtk python -m pytest -v
```

Expected: PASS.

- [ ] **Step 2: Verify setup, doctor, and uninstall manually**

Run:

```bash
rtk python -m haiku_scribe setup --dry-run --home /tmp/haiku-scribe-v1-2-check
rtk python -m haiku_scribe setup --home /tmp/haiku-scribe-v1-2-check
rtk python -m haiku_scribe doctor --home /tmp/haiku-scribe-v1-2-check
rtk python -m haiku_scribe uninstall --home /tmp/haiku-scribe-v1-2-check
```

Expected:

```text
Dry run: no files written
Wrote /tmp/haiku-scribe-v1-2-check/.claude/...
Haiku Scribe doctor: ok
Removed /tmp/haiku-scribe-v1-2-check/.claude/...
```

- [ ] **Step 3: Inspect final git state**

Run:

```bash
rtk git status --short
```

Expected: clean working tree.
