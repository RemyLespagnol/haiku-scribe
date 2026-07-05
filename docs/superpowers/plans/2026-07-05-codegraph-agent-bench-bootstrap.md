# CodeGraph Agent Bench Bootstrap Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a code-first semi-manual benchmark scaffold for comparing baseline agent exploration, direct CodeGraph use, and a simulated `haiku-codegraph` workflow.

**Architecture:** Add a small Python fixture codebase that models a Haiku Scribe-style CLI with real symbols, call paths, and tests. Add replayable benchmark task prompts plus a lightweight report script that aggregates manually recorded JSONL run metrics into Markdown.

**Tech Stack:** Python standard library, pytest-compatible fixture tests, Markdown, JSONL

## Global Constraints

- The benchmark is evaluation scaffolding only, not Haiku Scribe product surface.
- Keep CodeGraph out of the base `haiku-scribe` MVP.
- Do not implement a real `haiku-codegraph` agent.
- Do not parse real Claude transcripts or claim exact token savings.
- Use context-usage proxies: tool calls, direct file reads, large outputs, line evidence, task success, and friction notes.

---

### Task 1: Add Sample CLI Fixture

**Files:**
- Create: `bench/fixtures/sample-cli/haiku_scribe_sample/__init__.py`
- Create: `bench/fixtures/sample-cli/haiku_scribe_sample/agent_config.py`
- Create: `bench/fixtures/sample-cli/haiku_scribe_sample/settings_merge.py`
- Create: `bench/fixtures/sample-cli/haiku_scribe_sample/installer.py`
- Create: `bench/fixtures/sample-cli/haiku_scribe_sample/doctor.py`
- Create: `bench/fixtures/sample-cli/tests/test_sample_cli.py`

**Interfaces:**
- Produces: `AgentConfig`, `default_agent_config()`, `render_agent_markdown(config)`, `merge_deny_rules(settings, deny_rules)`, `install_config(home)`, `doctor_report(home)`
- Consumes: Python standard library only

- [ ] **Step 1: Write failing fixture tests**
  Create `bench/fixtures/sample-cli/tests/test_sample_cli.py`:

```python
from pathlib import Path

from haiku_scribe_sample.agent_config import default_agent_config, render_agent_markdown
from haiku_scribe_sample.doctor import doctor_report
from haiku_scribe_sample.installer import install_config
from haiku_scribe_sample.settings_merge import merge_deny_rules


def test_render_agent_markdown_includes_read_only_contract():
    markdown = render_agent_markdown(default_agent_config())

    assert "name: haiku-scribe" in markdown
    assert "model: haiku" in markdown
    assert "tools: Read, Glob, Grep" in markdown
    assert "Write" in markdown
    assert "Bash" in markdown


def test_merge_deny_rules_preserves_existing_settings():
    settings = {"permissions": {"allow": ["Read(src/**)"], "deny": ["Read(.env)"]}}

    merged = merge_deny_rules(settings, ["Read(.env)", "Read(**/*.pem)"])

    assert merged["permissions"]["allow"] == ["Read(src/**)"]
    assert merged["permissions"]["deny"] == ["Read(.env)", "Read(**/*.pem)"]


def test_install_config_writes_agent_and_settings(tmp_path):
    result = install_config(tmp_path)

    assert result.agent_path == tmp_path / ".claude" / "agents" / "haiku-scribe.md"
    assert result.settings_path == tmp_path / ".claude" / "settings.json"
    assert result.agent_path.exists()
    assert result.settings_path.exists()


def test_doctor_report_detects_safe_install(tmp_path):
    install_config(tmp_path)

    report = doctor_report(tmp_path)

    assert report.ok is True
    assert report.failures == []
```

- [ ] **Step 2: Run test and verify failure**
  Run: `rtk pytest bench/fixtures/sample-cli/tests/test_sample_cli.py -q`
  Expected: FAIL because `haiku_scribe_sample` does not exist.

- [ ] **Step 3: Implement fixture package**
  Create the package files with minimal implementation:

```python
# bench/fixtures/sample-cli/haiku_scribe_sample/agent_config.py
from dataclasses import dataclass, field


@dataclass(frozen=True)
class AgentConfig:
    name: str
    model: str
    tools: tuple[str, ...]
    disallowed_tools: tuple[str, ...]
    max_turns: int = 6
    deny_rules: tuple[str, ...] = field(default_factory=tuple)


def default_agent_config() -> AgentConfig:
    return AgentConfig(
        name="haiku-scribe",
        model="haiku",
        tools=("Read", "Glob", "Grep"),
        disallowed_tools=("Write", "Edit", "Bash", "WebFetch", "WebSearch", "Agent", "mcp__*"),
        deny_rules=("Read(.env)", "Read(.env.*)", "Read(**/*.pem)", "Read(**/*.key)"),
    )


def render_agent_markdown(config: AgentConfig) -> str:
    tools = ", ".join(config.tools)
    disallowed = ", ".join(config.disallowed_tools)
    return f"""---
name: {config.name}
model: {config.model}
tools: {tools}
disallowedTools: {disallowed}
maxTurns: {config.max_turns}
---

## Role

Read repository context and return concise evidence.

## Boundaries

Do not write files, run shell commands, use web tools, use MCP tools, or invoke other agents.
"""
```

```python
# bench/fixtures/sample-cli/haiku_scribe_sample/settings_merge.py
from copy import deepcopy


def merge_deny_rules(settings: dict, deny_rules: list[str]) -> dict:
    merged = deepcopy(settings)
    permissions = merged.setdefault("permissions", {})
    existing = list(permissions.get("deny", []))
    for rule in deny_rules:
        if rule not in existing:
            existing.append(rule)
    permissions["deny"] = existing
    return merged
```

```python
# bench/fixtures/sample-cli/haiku_scribe_sample/installer.py
import json
from dataclasses import dataclass
from pathlib import Path

from .agent_config import default_agent_config, render_agent_markdown
from .settings_merge import merge_deny_rules


@dataclass(frozen=True)
class InstallResult:
    agent_path: Path
    settings_path: Path


def install_config(home: Path) -> InstallResult:
    config = default_agent_config()
    claude_dir = home / ".claude"
    agent_dir = claude_dir / "agents"
    agent_dir.mkdir(parents=True, exist_ok=True)

    agent_path = agent_dir / "haiku-scribe.md"
    settings_path = claude_dir / "settings.json"

    existing_settings = {}
    if settings_path.exists():
        existing_settings = json.loads(settings_path.read_text())

    agent_path.write_text(render_agent_markdown(config))
    settings = merge_deny_rules(existing_settings, list(config.deny_rules))
    settings_path.write_text(json.dumps(settings, indent=2, sort_keys=True))

    return InstallResult(agent_path=agent_path, settings_path=settings_path)
```

```python
# bench/fixtures/sample-cli/haiku_scribe_sample/doctor.py
import json
from dataclasses import dataclass
from pathlib import Path

from .agent_config import default_agent_config


@dataclass(frozen=True)
class DoctorReport:
    ok: bool
    failures: list[str]


def doctor_report(home: Path) -> DoctorReport:
    config = default_agent_config()
    agent_path = home / ".claude" / "agents" / "haiku-scribe.md"
    settings_path = home / ".claude" / "settings.json"
    failures: list[str] = []

    if not agent_path.exists():
        failures.append("missing agent file")
    else:
        agent_text = agent_path.read_text()
        if f"model: {config.model}" not in agent_text:
            failures.append("agent model is not haiku")
        if "Bash" not in agent_text:
            failures.append("agent does not disallow Bash")

    if not settings_path.exists():
        failures.append("missing settings file")
    else:
        settings = json.loads(settings_path.read_text())
        deny = settings.get("permissions", {}).get("deny", [])
        missing = [rule for rule in config.deny_rules if rule not in deny]
        if missing:
            failures.append(f"missing deny rules: {', '.join(missing)}")

    return DoctorReport(ok=not failures, failures=failures)
```

```python
# bench/fixtures/sample-cli/haiku_scribe_sample/__init__.py
"""Small code fixture for CodeGraph benchmark tasks."""
```

- [ ] **Step 4: Run fixture tests and verify pass**
  Run: `PYTHONPATH=bench/fixtures/sample-cli rtk pytest bench/fixtures/sample-cli/tests/test_sample_cli.py -q`
  Expected: PASS.

---

### Task 2: Add Benchmark Tasks And README

**Files:**
- Create: `bench/tasks/01-orientation.md`
- Create: `bench/tasks/02-impact-analysis.md`
- Create: `bench/tasks/03-edit-readiness.md`
- Create: `bench/tasks/04-docs-control.md`
- Create: `bench/README.md`
- Create: `bench/runs/.gitkeep`

**Interfaces:**
- Consumes: sample CLI fixture from Task 1
- Produces: replayable prompts and manual run recording protocol

- [ ] **Step 1: Create task prompts**
  Write each task with sections `Goal`, `Run Modes`, `Prompt`, and `Record`.

- [ ] **Step 2: Create README**
  Document the three modes, JSONL run format, and exact command for generating a report.

- [ ] **Step 3: Inspect markdown**
  Run: `rtk read bench/README.md`
  Expected: README explains code-first benchmark and warns that docs-only results are only a control.

---

### Task 3: Add Report Script

**Files:**
- Create: `bench/test_report.py`
- Create: `bench/report.py`

**Interfaces:**
- Consumes: JSONL files from `bench/runs/*.jsonl`
- Produces: Markdown table printed to stdout

- [ ] **Step 1: Write failing report tests**
  Create `bench/test_report.py` with tests for parsing and aggregation:

```python
from pathlib import Path

from report import build_markdown_report, load_runs


def test_load_runs_reads_jsonl_files(tmp_path):
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir()
    (runs_dir / "sample.jsonl").write_text(
        '{"task_id":"01-orientation","mode":"agent-codegraph","tool_calls":2,'
        '"direct_file_reads":1,"large_outputs":0,"line_evidence_count":3,'
        '"found_right_area":true,"edit_ready":false,"estimated_context_cost":"low"}\n'
    )

    runs = load_runs(runs_dir)

    assert len(runs) == 1
    assert runs[0]["mode"] == "agent-codegraph"


def test_build_markdown_report_groups_by_task_and_mode():
    runs = [
        {
            "task_id": "01-orientation",
            "mode": "agent-codegraph",
            "tool_calls": 2,
            "direct_file_reads": 1,
            "large_outputs": 0,
            "line_evidence_count": 3,
            "found_right_area": True,
            "edit_ready": False,
            "estimated_context_cost": "low",
        },
        {
            "task_id": "01-orientation",
            "mode": "agent-codegraph",
            "tool_calls": 4,
            "direct_file_reads": 1,
            "large_outputs": 0,
            "line_evidence_count": 1,
            "found_right_area": False,
            "edit_ready": True,
            "estimated_context_cost": "medium",
        },
    ]

    markdown = build_markdown_report(runs)

    assert "| 01-orientation | agent-codegraph | 2 | 3.0 | 1.0 | 0.0 | 2.0 | 50% | 50% | low:1, medium:1 |" in markdown
```

- [ ] **Step 2: Run report tests and verify failure**
  Run: `PYTHONPATH=bench rtk pytest bench/test_report.py -q`
  Expected: FAIL because `report` does not exist.

- [ ] **Step 3: Implement report script**
  Implement `load_runs(runs_dir: Path) -> list[dict]`, `build_markdown_report(runs: list[dict]) -> str`, and a `main()` that prints the report.

- [ ] **Step 4: Run report tests and verify pass**
  Run: `PYTHONPATH=bench rtk pytest bench/test_report.py -q`
  Expected: PASS.

---

### Task 4: Add Evaluation Document And Verify

**Files:**
- Create: `docs/superpowers/evaluations/2026-07-05-codegraph-agent-bench.md`

**Interfaces:**
- Consumes: benchmark tasks and report script
- Produces: human-readable evaluation worksheet

- [ ] **Step 1: Create evaluation worksheet**
  Include sections for hypothesis, run matrix, raw observations, report output, decision criteria, and final decision.

- [ ] **Step 2: Run all tests**
  Run: `PYTHONPATH=bench/fixtures/sample-cli rtk pytest bench/fixtures/sample-cli/tests/test_sample_cli.py -q`
  Expected: PASS.
  Run: `PYTHONPATH=bench rtk pytest bench/test_report.py -q`
  Expected: PASS.

- [ ] **Step 3: Generate empty report**
  Run: `rtk python bench/report.py`
  Expected: Markdown explaining no runs were found.

- [ ] **Step 4: Review final diff**
  Run: `rtk git diff -- bench docs/superpowers/specs/2026-07-05-codegraph-agent-bench-design.md docs/superpowers/plans/2026-07-05-codegraph-agent-bench-bootstrap.md docs/superpowers/evaluations/2026-07-05-codegraph-agent-bench.md`
  Expected: diff only contains benchmark scaffold and design docs.

