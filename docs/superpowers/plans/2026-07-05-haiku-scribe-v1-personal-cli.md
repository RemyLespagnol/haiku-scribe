# Haiku Scribe V1 Personal CLI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build V1 personal packaging: a local CLI that installs, verifies, and removes the validated `haiku-scribe` Claude Code subagent safely for one user.

**Architecture:** Create a small Python package with a public CLI seam and focused modules for static contracts, JSON settings merge, owned Markdown block management, backups, setup, doctor, and uninstall. Tests drive behavior through temporary homes and the CLI command boundary; no test requires live Claude Code, network, OAuth, model calls, hooks, reports, nudges, enforcement, MCP, or CodeGraph.

**Tech Stack:** Python 3.11+, standard library only for runtime, `pytest` for tests, `pyproject.toml` packaging, console script `haiku-scribe`.

## Global Constraints

- V1 scope includes `setup`, `setup --dry-run`, `doctor`, `uninstall`, backups, dry-run behavior, safe user settings merge, bounded ownership markers, and validation that the subagent still matches the intended safety contract.
- V1 scope excludes audit events, usage reports, prompt nudges, enforcement, team distribution, plugin packaging, enterprise-managed policy, MCP, and CodeGraph in the base product.
- The installed agent must be named `haiku-scribe`, use `model: haiku`, and allow only `Read`, `Glob`, `Grep`.
- The installed agent must explicitly forbid file writes, file edits, shell execution, web access, MCP tools, and recursive agent calls.
- Setup must preserve unrelated user configuration and update only owned files or owned blocks.
- Uninstall must remove only Haiku Scribe-owned content and preserve unrelated user content.
- Runtime code must not depend on external API keys, external model providers, local LLM runtimes, live Claude Code sessions, network access, or MCP servers.
- Use `rtk` prefix for shell commands in this repository.

---

## File Structure

- Create: `pyproject.toml` - package metadata, Python floor, pytest config, console script.
- Create: `src/haiku_scribe/__init__.py` - package version.
- Create: `src/haiku_scribe/__main__.py` - supports `python -m haiku_scribe`.
- Create: `src/haiku_scribe/cli.py` - argparse CLI; routes `setup`, `doctor`, `uninstall`.
- Create: `src/haiku_scribe/contracts.py` - source-of-truth agent Markdown, Claude guidance block, deny rules, owned markers.
- Create: `src/haiku_scribe/paths.py` - resolves user-scope Claude paths from an explicit home.
- Create: `src/haiku_scribe/settings.py` - JSON parse and idempotent deny-rule merge.
- Create: `src/haiku_scribe/markdown_blocks.py` - bounded block insert, replace, remove for `CLAUDE.md`.
- Create: `src/haiku_scribe/backups.py` - timestamped backups before writes.
- Create: `src/haiku_scribe/setup.py` - dry-run and install orchestration.
- Create: `src/haiku_scribe/doctor.py` - diagnostic checks and user-facing report.
- Create: `src/haiku_scribe/uninstall.py` - owned-content removal.
- Create: `tests/test_cli_setup.py` - setup acceptance tests through CLI.
- Create: `tests/test_doctor.py` - doctor acceptance tests through CLI.
- Create: `tests/test_uninstall.py` - uninstall acceptance tests through CLI.
- Create: `tests/test_settings.py` - settings merge edge cases.
- Create: `tests/test_markdown_blocks.py` - owned block operations.

The bench fixture under `bench/fixtures/sample-cli` remains reference material only. Do not turn it into the product package.

### Task 1: Package Skeleton And CLI Routing

**Files:**
- Create: `pyproject.toml`
- Create: `src/haiku_scribe/__init__.py`
- Create: `src/haiku_scribe/__main__.py`
- Create: `src/haiku_scribe/cli.py`
- Test: `tests/test_cli_setup.py`

**Interfaces:**
- Produces: `haiku_scribe.cli.main(argv: list[str] | None = None) -> int`
- Produces: commands `setup`, `doctor`, `uninstall`
- Produces: shared option `--home PATH` for tests and non-destructive local use
- Later tasks replace placeholder command handlers with real behavior.

- [ ] **Step 1: Write failing CLI smoke tests**

Create `tests/test_cli_setup.py`:

```python
import subprocess
import sys


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "haiku_scribe", *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_cli_help_lists_v1_commands():
    result = run_cli("--help")

    assert result.returncode == 0
    assert "setup" in result.stdout
    assert "doctor" in result.stdout
    assert "uninstall" in result.stdout


def test_setup_dry_run_command_exists(tmp_path):
    result = run_cli("setup", "--dry-run", "--home", str(tmp_path))

    assert result.returncode == 0
    assert "Dry run" in result.stdout
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `rtk pytest tests/test_cli_setup.py -v`

Expected: FAIL because package `haiku_scribe` does not exist.

- [ ] **Step 3: Add packaging metadata**

Create `pyproject.toml`:

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "haiku-scribe"
version = "0.1.0"
description = "Personal installer for the Haiku Scribe Claude Code subagent"
requires-python = ">=3.11"
dependencies = []

[project.scripts]
haiku-scribe = "haiku_scribe.cli:main"

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
```

- [ ] **Step 4: Add minimal package files**

Create `src/haiku_scribe/__init__.py`:

```python
__version__ = "0.1.0"
```

Create `src/haiku_scribe/__main__.py`:

```python
from .cli import main


raise SystemExit(main())
```

Create `src/haiku_scribe/cli.py`:

```python
from __future__ import annotations

import argparse
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="haiku-scribe")
    subparsers = parser.add_subparsers(dest="command", required=True)

    setup = subparsers.add_parser("setup", help="Install Haiku Scribe for one user")
    setup.add_argument("--dry-run", action="store_true", help="Print planned changes without writing files")
    setup.add_argument("--home", type=Path, default=Path.home(), help=argparse.SUPPRESS)

    doctor = subparsers.add_parser("doctor", help="Validate the personal Haiku Scribe installation")
    doctor.add_argument("--home", type=Path, default=Path.home(), help=argparse.SUPPRESS)

    uninstall = subparsers.add_parser("uninstall", help="Remove Haiku Scribe-owned personal configuration")
    uninstall.add_argument("--dry-run", action="store_true", help="Print planned removals without writing files")
    uninstall.add_argument("--home", type=Path, default=Path.home(), help=argparse.SUPPRESS)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "setup":
        print("Dry run: no files written" if args.dry_run else "Setup not implemented")
        return 0
    if args.command == "doctor":
        print("Doctor not implemented")
        return 1
    if args.command == "uninstall":
        print("Dry run: no files removed" if args.dry_run else "Uninstall not implemented")
        return 0

    parser.error(f"unknown command: {args.command}")
    return 2
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `rtk pytest tests/test_cli_setup.py -v`

Expected: PASS.

- [ ] **Step 6: Commit**

Run:

```bash
rtk git add pyproject.toml src/haiku_scribe tests/test_cli_setup.py
rtk git commit -m "feat: scaffold haiku scribe cli"
```

Expected: commit created.

### Task 2: Static Contracts And Path Resolution

**Files:**
- Create: `src/haiku_scribe/contracts.py`
- Create: `src/haiku_scribe/paths.py`
- Modify: `tests/test_cli_setup.py`

**Interfaces:**
- Produces: `DEFAULT_DENY_RULES: tuple[str, ...]`
- Produces: `render_agent_markdown() -> str`
- Produces: `render_guidance_block() -> str`
- Produces: `ClaudePaths.for_home(home: Path) -> ClaudePaths`
- Consumed by: setup, doctor, uninstall.

- [ ] **Step 1: Add failing contract tests**

Append to `tests/test_cli_setup.py`:

```python
from pathlib import Path

from haiku_scribe.contracts import DEFAULT_DENY_RULES, render_agent_markdown, render_guidance_block
from haiku_scribe.paths import ClaudePaths


def test_agent_contract_is_read_only_haiku():
    text = render_agent_markdown()

    assert "name: haiku-scribe" in text
    assert "model: haiku" in text
    assert "tools: Read, Glob, Grep" in text
    assert "Write files" in text
    assert "Edit files" in text
    assert "Run shell commands" in text
    assert "Use MCP tools" in text
    assert "Invoke other agents" in text


def test_guidance_block_uses_owned_markers():
    block = render_guidance_block()

    assert block.startswith("<!-- HAIKU_SCRIBE_START -->")
    assert block.rstrip().endswith("<!-- HAIKU_SCRIBE_END -->")
    assert "Main Claude must verify important claims before editing." in block


def test_default_deny_rules_cover_common_secret_files():
    assert "Read(./.env)" in DEFAULT_DENY_RULES
    assert "Read(./.env.*)" in DEFAULT_DENY_RULES
    assert "Read(./secrets/**)" in DEFAULT_DENY_RULES
    assert "Read(**/*.pem)" in DEFAULT_DENY_RULES
    assert "Read(**/*.key)" in DEFAULT_DENY_RULES
    assert "Read(**/*secret*)" in DEFAULT_DENY_RULES
    assert "Read(**/*credential*)" in DEFAULT_DENY_RULES


def test_claude_paths_are_user_scoped(tmp_path: Path):
    paths = ClaudePaths.for_home(tmp_path)

    assert paths.claude_dir == tmp_path / ".claude"
    assert paths.agent_path == tmp_path / ".claude" / "agents" / "haiku-scribe.md"
    assert paths.guidance_path == tmp_path / ".claude" / "CLAUDE.md"
    assert paths.settings_path == tmp_path / ".claude" / "settings.json"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `rtk pytest tests/test_cli_setup.py -v`

Expected: FAIL because `contracts.py` and `paths.py` do not exist.

- [ ] **Step 3: Add contracts**

Create `src/haiku_scribe/contracts.py`:

```python
from __future__ import annotations

AGENT_NAME = "haiku-scribe"
GUIDANCE_START = "<!-- HAIKU_SCRIBE_START -->"
GUIDANCE_END = "<!-- HAIKU_SCRIBE_END -->"

DEFAULT_DENY_RULES: tuple[str, ...] = (
    "Read(./.env)",
    "Read(./.env.*)",
    "Read(./secrets/**)",
    "Read(./config/credentials.json)",
    "Read(**/*.pem)",
    "Read(**/*.key)",
    "Read(**/*secret*)",
    "Read(**/*credential*)",
)


def render_agent_markdown() -> str:
    return """---
name: haiku-scribe
description: Read-only context compression worker for bulk file reading, large-file orientation, log or transcript summarization, generated output summarization, cross-file flow mapping, and evidence extraction. Use before loading broad raw context. Do not use for final reasoning, edits, security conclusions, architecture decisions, commits, or public summaries.
model: haiku
tools: Read, Glob, Grep
---

# Haiku Scribe

## Role
You are a read-only context-compression worker for Claude Code. Read only the context needed for the request and return a compact brief so the main Claude session can reason without loading excessive raw files, logs, transcripts, or generated output.

## Boundaries
You may:
- Read files requested by the main Claude session.
- Search repository text for exact patterns.
- List files with glob patterns.
- Summarize large files, logs, transcripts, generated output, and related files.
- Extract evidence with file paths and line numbers when available.
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
- When specific files are named, inspect those files first.
- For broad orientation, use `Glob` and `Grep` to find relevant files before reading.
- For large files, summarize structure and read only regions needed to answer.
- If content appears secret-bearing, credential-like, or unrelated to the request, stop and say direct user confirmation is needed before inspecting it.
- Do not invent evidence or line numbers.

## Response Shape
### Summary
Two to six bullets with the compressed answer.

### Evidence
`path/to/file.ext:line`: Relevant observed fact.

### Unknowns And Risks
Unknown or risk that affects confidence.

### Suggested Direct Reads
`path/to/file.ext:line`: Why the main Claude session should inspect this exact location.
"""


def render_guidance_block() -> str:
    return f"""{GUIDANCE_START}
## Cost-aware Scribe routing

For direct bulk reading, use `haiku-scribe`.

Use `haiku-scribe` when:
- reading 3+ files;
- reading a file likely over 400 lines;
- mapping a flow across files;
- summarizing logs, bundles, generated JavaScript, transcripts, or large docs;
- extracting evidence before reasoning.

Do not delegate:
- final debugging or root-cause conclusions;
- architecture decisions;
- security, authentication, authorization, or permission-sensitive code;
- precise edits;
- final PR summaries;
- commits.

Main Claude must verify important claims before editing.
{GUIDANCE_END}
"""
```

- [ ] **Step 4: Add path resolution**

Create `src/haiku_scribe/paths.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ClaudePaths:
    home: Path
    claude_dir: Path
    agents_dir: Path
    agent_path: Path
    guidance_path: Path
    settings_path: Path

    @classmethod
    def for_home(cls, home: Path) -> "ClaudePaths":
        claude_dir = home / ".claude"
        agents_dir = claude_dir / "agents"
        return cls(
            home=home,
            claude_dir=claude_dir,
            agents_dir=agents_dir,
            agent_path=agents_dir / "haiku-scribe.md",
            guidance_path=claude_dir / "CLAUDE.md",
            settings_path=claude_dir / "settings.json",
        )
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `rtk pytest tests/test_cli_setup.py -v`

Expected: PASS.

- [ ] **Step 6: Commit**

Run:

```bash
rtk git add src/haiku_scribe/contracts.py src/haiku_scribe/paths.py tests/test_cli_setup.py
rtk git commit -m "feat: define v1 install contracts"
```

Expected: commit created.

### Task 3: Settings Merge And Owned Markdown Blocks

**Files:**
- Create: `src/haiku_scribe/settings.py`
- Create: `src/haiku_scribe/markdown_blocks.py`
- Create: `tests/test_settings.py`
- Create: `tests/test_markdown_blocks.py`

**Interfaces:**
- Produces: `load_json_object(path: Path) -> dict[str, object]`
- Produces: `merge_deny_rules(settings: dict[str, object], deny_rules: tuple[str, ...]) -> dict[str, object]`
- Produces: `insert_or_replace_block(existing: str, block: str) -> str`
- Produces: `remove_owned_block(existing: str) -> str`
- Consumed by: setup, doctor, uninstall.

- [ ] **Step 1: Write failing settings tests**

Create `tests/test_settings.py`:

```python
import json

import pytest

from haiku_scribe.contracts import DEFAULT_DENY_RULES
from haiku_scribe.settings import SettingsError, load_json_object, merge_deny_rules


def test_merge_deny_rules_preserves_existing_settings():
    settings = {"theme": "dark", "permissions": {"allow": ["Read(./docs/**)"], "deny": ["Read(./private)"]}}

    merged = merge_deny_rules(settings, DEFAULT_DENY_RULES)

    assert merged["theme"] == "dark"
    assert merged["permissions"]["allow"] == ["Read(./docs/**)"]
    assert merged["permissions"]["deny"].count("Read(./private)") == 1
    assert merged["permissions"]["deny"].count("Read(**/*credential*)") == 1


def test_merge_deny_rules_is_idempotent():
    once = merge_deny_rules({}, DEFAULT_DENY_RULES)
    twice = merge_deny_rules(once, DEFAULT_DENY_RULES)

    assert twice == once


def test_load_json_object_reports_invalid_json(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text("{broken", encoding="utf-8")

    with pytest.raises(SettingsError, match="invalid JSON"):
        load_json_object(path)


def test_load_json_object_rejects_json_array(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text(json.dumps([]), encoding="utf-8")

    with pytest.raises(SettingsError, match="must contain a JSON object"):
        load_json_object(path)
```

- [ ] **Step 2: Write failing Markdown block tests**

Create `tests/test_markdown_blocks.py`:

```python
from haiku_scribe.contracts import render_guidance_block
from haiku_scribe.markdown_blocks import insert_or_replace_block, remove_owned_block


def test_insert_block_preserves_existing_content():
    updated = insert_or_replace_block("# User notes\n", render_guidance_block())

    assert updated.startswith("# User notes\n")
    assert "<!-- HAIKU_SCRIBE_START -->" in updated
    assert "<!-- HAIKU_SCRIBE_END -->" in updated


def test_insert_block_replaces_existing_owned_block():
    first = insert_or_replace_block("# User notes\n", render_guidance_block())
    second = insert_or_replace_block(first, render_guidance_block())

    assert second.count("<!-- HAIKU_SCRIBE_START -->") == 1
    assert second.count("<!-- HAIKU_SCRIBE_END -->") == 1


def test_remove_owned_block_keeps_unrelated_content():
    original = "# User notes\n\n" + render_guidance_block() + "\nKeep this.\n"

    cleaned = remove_owned_block(original)

    assert "# User notes" in cleaned
    assert "Keep this." in cleaned
    assert "HAIKU_SCRIBE_START" not in cleaned
    assert "HAIKU_SCRIBE_END" not in cleaned
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `rtk pytest tests/test_settings.py tests/test_markdown_blocks.py -v`

Expected: FAIL because modules do not exist.

- [ ] **Step 4: Implement settings merge**

Create `src/haiku_scribe/settings.py`:

```python
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any


class SettingsError(ValueError):
    pass


def load_json_object(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SettingsError(f"{path} contains invalid JSON: {exc.msg}") from exc
    if not isinstance(value, dict):
        raise SettingsError(f"{path} must contain a JSON object")
    return value


def merge_deny_rules(settings: dict[str, Any], deny_rules: tuple[str, ...]) -> dict[str, Any]:
    merged = deepcopy(settings)
    permissions = merged.setdefault("permissions", {})
    if not isinstance(permissions, dict):
        raise SettingsError("settings.permissions must be a JSON object")

    existing = permissions.get("deny", [])
    if not isinstance(existing, list):
        raise SettingsError("settings.permissions.deny must be a JSON array")

    deny = list(existing)
    for rule in deny_rules:
        if rule not in deny:
            deny.append(rule)
    permissions["deny"] = deny
    return merged
```

- [ ] **Step 5: Implement Markdown block helpers**

Create `src/haiku_scribe/markdown_blocks.py`:

```python
from __future__ import annotations

from haiku_scribe.contracts import GUIDANCE_END, GUIDANCE_START


def insert_or_replace_block(existing: str, block: str) -> str:
    without = remove_owned_block(existing).rstrip()
    if without:
        return without + "\n\n" + block.rstrip() + "\n"
    return block.rstrip() + "\n"


def remove_owned_block(existing: str) -> str:
    start = existing.find(GUIDANCE_START)
    end = existing.find(GUIDANCE_END)
    if start == -1 or end == -1 or end < start:
        return existing
    end += len(GUIDANCE_END)
    before = existing[:start].rstrip()
    after = existing[end:].lstrip("\n")
    if before and after:
        return before + "\n\n" + after
    if before:
        return before + "\n"
    return after
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `rtk pytest tests/test_settings.py tests/test_markdown_blocks.py -v`

Expected: PASS.

- [ ] **Step 7: Commit**

Run:

```bash
rtk git add src/haiku_scribe/settings.py src/haiku_scribe/markdown_blocks.py tests/test_settings.py tests/test_markdown_blocks.py
rtk git commit -m "feat: add safe config merge helpers"
```

Expected: commit created.

### Task 4: Setup Dry-Run And Installation

**Files:**
- Create: `src/haiku_scribe/backups.py`
- Create: `src/haiku_scribe/setup.py`
- Modify: `src/haiku_scribe/cli.py`
- Modify: `tests/test_cli_setup.py`

**Interfaces:**
- Produces: `setup_user(home: Path, dry_run: bool = False) -> SetupResult`
- Produces: `SetupResult.planned: list[str]`
- Produces: `SetupResult.written: list[Path]`
- Consumes: contracts, paths, settings, markdown blocks, backups.

- [ ] **Step 1: Replace dry-run smoke test with acceptance tests**

Append to `tests/test_cli_setup.py`:

```python
import json


def test_setup_dry_run_writes_nothing(tmp_path):
    result = run_cli("setup", "--dry-run", "--home", str(tmp_path))

    assert result.returncode == 0
    assert "Dry run" in result.stdout
    assert "Would write" in result.stdout
    assert not (tmp_path / ".claude").exists()


def test_setup_installs_agent_guidance_and_settings(tmp_path):
    result = run_cli("setup", "--home", str(tmp_path))

    assert result.returncode == 0
    agent = tmp_path / ".claude" / "agents" / "haiku-scribe.md"
    guidance = tmp_path / ".claude" / "CLAUDE.md"
    settings = tmp_path / ".claude" / "settings.json"
    assert agent.exists()
    assert "model: haiku" in agent.read_text(encoding="utf-8")
    assert "HAIKU_SCRIBE_START" in guidance.read_text(encoding="utf-8")
    parsed = json.loads(settings.read_text(encoding="utf-8"))
    assert "Read(**/*credential*)" in parsed["permissions"]["deny"]


def test_setup_is_idempotent(tmp_path):
    first = run_cli("setup", "--home", str(tmp_path))
    second = run_cli("setup", "--home", str(tmp_path))

    assert first.returncode == 0
    assert second.returncode == 0
    guidance = (tmp_path / ".claude" / "CLAUDE.md").read_text(encoding="utf-8")
    settings = json.loads((tmp_path / ".claude" / "settings.json").read_text(encoding="utf-8"))
    assert guidance.count("HAIKU_SCRIBE_START") == 1
    assert settings["permissions"]["deny"].count("Read(**/*credential*)") == 1


def test_setup_creates_backups_for_existing_files(tmp_path):
    claude = tmp_path / ".claude"
    (claude / "agents").mkdir(parents=True)
    (claude / "CLAUDE.md").write_text("# User guidance\n", encoding="utf-8")
    (claude / "settings.json").write_text('{"permissions":{"deny":["Read(./private)"]}}', encoding="utf-8")

    result = run_cli("setup", "--home", str(tmp_path))

    assert result.returncode == 0
    backups = sorted((claude / "backups" / "haiku-scribe").glob("*"))
    assert len(backups) == 2
    assert any(path.name.endswith("CLAUDE.md.bak") for path in backups)
    assert any(path.name.endswith("settings.json.bak") for path in backups)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `rtk pytest tests/test_cli_setup.py -v`

Expected: FAIL because setup still uses placeholder implementation.

- [ ] **Step 3: Implement backups**

Create `src/haiku_scribe/backups.py`:

```python
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from shutil import copy2


def backup_existing(path: Path, backup_root: Path) -> Path | None:
    if not path.exists():
        return None
    backup_root.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = backup_root / f"{timestamp}-{path.name}.bak"
    copy2(path, backup_path)
    return backup_path
```

- [ ] **Step 4: Implement setup orchestration**

Create `src/haiku_scribe/setup.py`:

```python
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from haiku_scribe.backups import backup_existing
from haiku_scribe.contracts import DEFAULT_DENY_RULES, render_agent_markdown, render_guidance_block
from haiku_scribe.markdown_blocks import insert_or_replace_block
from haiku_scribe.paths import ClaudePaths
from haiku_scribe.settings import load_json_object, merge_deny_rules


@dataclass(frozen=True)
class SetupResult:
    planned: list[str]
    written: list[Path]


def setup_user(home: Path, dry_run: bool = False) -> SetupResult:
    paths = ClaudePaths.for_home(home)
    planned = [
        f"Would write {paths.agent_path}",
        f"Would update {paths.guidance_path}",
        f"Would merge deny rules into {paths.settings_path}",
    ]
    if dry_run:
        return SetupResult(planned=planned, written=[])

    paths.agents_dir.mkdir(parents=True, exist_ok=True)
    backup_root = paths.claude_dir / "backups" / "haiku-scribe"

    agent_text = render_agent_markdown()
    guidance_existing = paths.guidance_path.read_text(encoding="utf-8") if paths.guidance_path.exists() else ""
    guidance_text = insert_or_replace_block(guidance_existing, render_guidance_block())
    settings = merge_deny_rules(load_json_object(paths.settings_path), DEFAULT_DENY_RULES)

    written: list[Path] = []
    paths.agent_path.write_text(agent_text, encoding="utf-8")
    written.append(paths.agent_path)

    backup_existing(paths.guidance_path, backup_root)
    paths.guidance_path.write_text(guidance_text, encoding="utf-8")
    written.append(paths.guidance_path)

    backup_existing(paths.settings_path, backup_root)
    paths.settings_path.write_text(json.dumps(settings, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    written.append(paths.settings_path)

    return SetupResult(planned=planned, written=written)
```

- [ ] **Step 5: Wire setup into CLI**

Modify `src/haiku_scribe/cli.py` so imports include:

```python
from haiku_scribe.setup import setup_user
from haiku_scribe.settings import SettingsError
```

Replace the `if args.command == "setup":` block with:

```python
    if args.command == "setup":
        try:
            result = setup_user(args.home, dry_run=args.dry_run)
        except SettingsError as exc:
            print(f"setup failed: {exc}", file=sys.stderr)
            return 1
        if args.dry_run:
            print("Dry run: no files written")
            for item in result.planned:
                print(item)
        else:
            for path in result.written:
                print(f"Wrote {path}")
        return 0
```

Also add this import at the top:

```python
import sys
```

- [ ] **Step 6: Run setup tests**

Run: `rtk pytest tests/test_cli_setup.py -v`

Expected: PASS.

- [ ] **Step 7: Commit**

Run:

```bash
rtk git add src/haiku_scribe/backups.py src/haiku_scribe/setup.py src/haiku_scribe/cli.py tests/test_cli_setup.py
rtk git commit -m "feat: implement personal setup command"
```

Expected: commit created.

### Task 5: Doctor Diagnostics

**Files:**
- Create: `src/haiku_scribe/doctor.py`
- Modify: `src/haiku_scribe/cli.py`
- Create: `tests/test_doctor.py`

**Interfaces:**
- Produces: `doctor_user(home: Path) -> DoctorResult`
- Produces: `DoctorResult.ok: bool`
- Produces: `DoctorResult.failures: list[str]`
- Consumes: installed agent, guidance block, settings.

- [ ] **Step 1: Write failing doctor tests**

Create `tests/test_doctor.py`:

```python
import subprocess
import sys


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "haiku_scribe", *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_doctor_passes_after_setup(tmp_path):
    assert run_cli("setup", "--home", str(tmp_path)).returncode == 0

    result = run_cli("doctor", "--home", str(tmp_path))

    assert result.returncode == 0
    assert "Haiku Scribe doctor: ok" in result.stdout


def test_doctor_reports_missing_installation(tmp_path):
    result = run_cli("doctor", "--home", str(tmp_path))

    assert result.returncode == 1
    assert "missing agent file" in result.stdout
    assert "missing CLAUDE.md guidance block" in result.stdout
    assert "missing settings file" in result.stdout


def test_doctor_reports_unsafe_agent_drift(tmp_path):
    assert run_cli("setup", "--home", str(tmp_path)).returncode == 0
    agent = tmp_path / ".claude" / "agents" / "haiku-scribe.md"
    agent.write_text(agent.read_text(encoding="utf-8").replace("model: haiku", "model: sonnet"), encoding="utf-8")

    result = run_cli("doctor", "--home", str(tmp_path))

    assert result.returncode == 1
    assert "agent model is not haiku" in result.stdout


def test_doctor_reports_missing_deny_rule(tmp_path):
    assert run_cli("setup", "--home", str(tmp_path)).returncode == 0
    settings = tmp_path / ".claude" / "settings.json"
    settings.write_text('{"permissions":{"deny":[]}}', encoding="utf-8")

    result = run_cli("doctor", "--home", str(tmp_path))

    assert result.returncode == 1
    assert "missing deny rule: Read(**/*credential*)" in result.stdout
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `rtk pytest tests/test_doctor.py -v`

Expected: FAIL because doctor uses placeholder implementation.

- [ ] **Step 3: Implement doctor**

Create `src/haiku_scribe/doctor.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from haiku_scribe.contracts import DEFAULT_DENY_RULES, GUIDANCE_END, GUIDANCE_START
from haiku_scribe.paths import ClaudePaths
from haiku_scribe.settings import SettingsError, load_json_object


@dataclass(frozen=True)
class DoctorResult:
    ok: bool
    failures: list[str]


def doctor_user(home: Path) -> DoctorResult:
    paths = ClaudePaths.for_home(home)
    failures: list[str] = []

    if not paths.agent_path.exists():
        failures.append("missing agent file")
    else:
        agent = paths.agent_path.read_text(encoding="utf-8")
        required_agent_fragments = {
            "agent name is not haiku-scribe": "name: haiku-scribe",
            "agent model is not haiku": "model: haiku",
            "agent tools are not read-only": "tools: Read, Glob, Grep",
            "agent does not forbid file edits": "Edit files",
            "agent does not forbid file writes": "Write files",
            "agent does not forbid shell execution": "Run shell commands",
            "agent does not forbid MCP tools": "Use MCP tools",
            "agent does not forbid recursive agents": "Invoke other agents",
        }
        for message, fragment in required_agent_fragments.items():
            if fragment not in agent:
                failures.append(message)

    if not paths.guidance_path.exists():
        failures.append("missing CLAUDE.md guidance block")
    else:
        guidance = paths.guidance_path.read_text(encoding="utf-8")
        if GUIDANCE_START not in guidance or GUIDANCE_END not in guidance:
            failures.append("missing CLAUDE.md guidance block")

    if not paths.settings_path.exists():
        failures.append("missing settings file")
    else:
        try:
            settings = load_json_object(paths.settings_path)
            deny = settings.get("permissions", {}).get("deny", [])
            if not isinstance(deny, list):
                failures.append("settings permissions.deny is not an array")
            else:
                for rule in DEFAULT_DENY_RULES:
                    if rule not in deny:
                        failures.append(f"missing deny rule: {rule}")
        except SettingsError as exc:
            failures.append(str(exc))

    return DoctorResult(ok=not failures, failures=failures)
```

- [ ] **Step 4: Wire doctor into CLI**

Modify `src/haiku_scribe/cli.py` imports:

```python
from haiku_scribe.doctor import doctor_user
```

Replace the `if args.command == "doctor":` block with:

```python
    if args.command == "doctor":
        result = doctor_user(args.home)
        if result.ok:
            print("Haiku Scribe doctor: ok")
            return 0
        print("Haiku Scribe doctor: failed")
        for failure in result.failures:
            print(f"- {failure}")
        return 1
```

- [ ] **Step 5: Run doctor tests**

Run: `rtk pytest tests/test_doctor.py -v`

Expected: PASS.

- [ ] **Step 6: Commit**

Run:

```bash
rtk git add src/haiku_scribe/doctor.py src/haiku_scribe/cli.py tests/test_doctor.py
rtk git commit -m "feat: implement doctor diagnostics"
```

Expected: commit created.

### Task 6: Uninstall Owned Content

**Files:**
- Create: `src/haiku_scribe/uninstall.py`
- Modify: `src/haiku_scribe/cli.py`
- Create: `tests/test_uninstall.py`

**Interfaces:**
- Produces: `uninstall_user(home: Path, dry_run: bool = False) -> UninstallResult`
- Produces: `UninstallResult.planned: list[str]`
- Produces: `UninstallResult.removed: list[Path]`
- Consumes: paths, markdown block removal.

- [ ] **Step 1: Write failing uninstall tests**

Create `tests/test_uninstall.py`:

```python
import json
import subprocess
import sys


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "haiku_scribe", *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_uninstall_dry_run_writes_nothing(tmp_path):
    assert run_cli("setup", "--home", str(tmp_path)).returncode == 0

    result = run_cli("uninstall", "--dry-run", "--home", str(tmp_path))

    assert result.returncode == 0
    assert "Dry run" in result.stdout
    assert (tmp_path / ".claude" / "agents" / "haiku-scribe.md").exists()


def test_uninstall_removes_agent_and_guidance_but_keeps_settings_and_user_content(tmp_path):
    claude = tmp_path / ".claude"
    claude.mkdir()
    (claude / "CLAUDE.md").write_text("# My guidance\n", encoding="utf-8")
    (claude / "settings.json").write_text('{"theme":"dark","permissions":{"deny":["Read(./private)"]}}', encoding="utf-8")
    assert run_cli("setup", "--home", str(tmp_path)).returncode == 0

    result = run_cli("uninstall", "--home", str(tmp_path))

    assert result.returncode == 0
    assert not (claude / "agents" / "haiku-scribe.md").exists()
    guidance = (claude / "CLAUDE.md").read_text(encoding="utf-8")
    settings = json.loads((claude / "settings.json").read_text(encoding="utf-8"))
    assert "# My guidance" in guidance
    assert "HAIKU_SCRIBE_START" not in guidance
    assert settings["theme"] == "dark"
    assert "Read(./private)" in settings["permissions"]["deny"]


def test_uninstall_is_idempotent(tmp_path):
    assert run_cli("setup", "--home", str(tmp_path)).returncode == 0
    assert run_cli("uninstall", "--home", str(tmp_path)).returncode == 0

    result = run_cli("uninstall", "--home", str(tmp_path))

    assert result.returncode == 0
    assert "Nothing to remove" in result.stdout
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `rtk pytest tests/test_uninstall.py -v`

Expected: FAIL because uninstall uses placeholder implementation.

- [ ] **Step 3: Implement uninstall**

Create `src/haiku_scribe/uninstall.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from haiku_scribe.markdown_blocks import remove_owned_block
from haiku_scribe.paths import ClaudePaths


@dataclass(frozen=True)
class UninstallResult:
    planned: list[str]
    removed: list[Path]


def uninstall_user(home: Path, dry_run: bool = False) -> UninstallResult:
    paths = ClaudePaths.for_home(home)
    planned: list[str] = []
    removed: list[Path] = []

    if paths.agent_path.exists():
        planned.append(f"Would remove {paths.agent_path}")

    guidance_changed = False
    guidance_text = ""
    if paths.guidance_path.exists():
        guidance_text = paths.guidance_path.read_text(encoding="utf-8")
        guidance_changed = remove_owned_block(guidance_text) != guidance_text
        if guidance_changed:
            planned.append(f"Would remove owned block from {paths.guidance_path}")

    if dry_run:
        return UninstallResult(planned=planned, removed=[])

    if paths.agent_path.exists():
        paths.agent_path.unlink()
        removed.append(paths.agent_path)

    if guidance_changed:
        paths.guidance_path.write_text(remove_owned_block(guidance_text), encoding="utf-8")
        removed.append(paths.guidance_path)

    return UninstallResult(planned=planned, removed=removed)
```

- [ ] **Step 4: Wire uninstall into CLI**

Modify `src/haiku_scribe/cli.py` imports:

```python
from haiku_scribe.uninstall import uninstall_user
```

Replace the `if args.command == "uninstall":` block with:

```python
    if args.command == "uninstall":
        result = uninstall_user(args.home, dry_run=args.dry_run)
        if args.dry_run:
            print("Dry run: no files removed")
            for item in result.planned:
                print(item)
            if not result.planned:
                print("Nothing to remove")
            return 0
        if not result.removed:
            print("Nothing to remove")
            return 0
        for path in result.removed:
            print(f"Removed {path}")
        return 0
```

- [ ] **Step 5: Run uninstall tests**

Run: `rtk pytest tests/test_uninstall.py -v`

Expected: PASS.

- [ ] **Step 6: Commit**

Run:

```bash
rtk git add src/haiku_scribe/uninstall.py src/haiku_scribe/cli.py tests/test_uninstall.py
rtk git commit -m "feat: implement personal uninstall"
```

Expected: commit created.

### Task 7: End-To-End V1 Verification And Documentation Note

**Files:**
- Modify: `docs/haiku_scribe_skill_prd.md` only if a short V1 implementation note is needed.
- Verify: all `src/haiku_scribe/*.py`
- Verify: all `tests/*.py`

**Interfaces:**
- Consumes: all previous task outputs.
- Produces: passing V1 acceptance suite.

- [ ] **Step 1: Add full journey regression test**

Append to `tests/test_cli_setup.py`:

```python
def test_full_v1_user_journey(tmp_path):
    dry = run_cli("setup", "--dry-run", "--home", str(tmp_path))
    setup = run_cli("setup", "--home", str(tmp_path))
    doctor_ok = run_cli("doctor", "--home", str(tmp_path))
    uninstall = run_cli("uninstall", "--home", str(tmp_path))
    doctor_missing = run_cli("doctor", "--home", str(tmp_path))

    assert dry.returncode == 0
    assert setup.returncode == 0
    assert doctor_ok.returncode == 0
    assert uninstall.returncode == 0
    assert doctor_missing.returncode == 1
    assert "missing agent file" in doctor_missing.stdout
```

- [ ] **Step 2: Run full test suite**

Run: `rtk pytest -v`

Expected: PASS for all tests, including existing `bench/test_report.py`.

- [ ] **Step 3: Run CLI manually against a temp home**

Run:

```bash
tmp_home="$(mktemp -d)"
rtk proxy python -m haiku_scribe setup --home "$tmp_home"
rtk proxy python -m haiku_scribe doctor --home "$tmp_home"
rtk proxy python -m haiku_scribe uninstall --home "$tmp_home"
```

Expected: PASS. Output includes installed paths, `Haiku Scribe doctor: ok`, and removed paths.

- [ ] **Step 4: Check V1 excludes later-version surfaces**

Run:

```bash
rtk rg -n "audit|report|nudge|enforcement|plugin|enterprise|mcp__|CodeGraph|codegraph" src tests
```

Expected: no matches, except if a test file explicitly asserts those words are absent. If matches appear in runtime implementation, remove that scope from V1.

- [ ] **Step 5: Verify worktree scope**

Run: `rtk git status --short`

Expected: only V1 package, tests, and intentional documentation files are modified. No `.claude`, `.omc`, `.tokensave`, or bench run artifacts should be staged.

- [ ] **Step 6: Commit final verification test**

Run:

```bash
rtk git add tests/test_cli_setup.py
rtk git commit -m "test: cover v1 personal cli journey"
```

Expected: commit created.

## Self-Review

Spec coverage:
- `setup`, `setup --dry-run`, personal user-scope installation, agent creation, bounded `CLAUDE.md` guidance, settings merge, backups, and idempotency are covered by Tasks 2-4.
- `doctor` diagnostics for missing files, unsafe model drift, unsafe tool drift, missing guidance, invalid settings, and missing deny rules are covered by Task 5.
- `uninstall` removes the agent and owned guidance while preserving unrelated settings and user content in Task 6.
- V1 excludes audit/report/nudge/enforcement/team/plugin/enterprise/MCP/CodeGraph by Global Constraints and Task 7 verification.
- Tests use the public CLI seam with temporary homes and no live Claude Code, network, OAuth, or model calls.

Placeholder scan:
- No unresolved placeholder markers remain.
- Each task includes exact files, exact commands, expected results, and concrete code for tests and implementation.

Type consistency:
- CLI entrypoint is consistently `haiku_scribe.cli.main(argv: list[str] | None = None) -> int`.
- Setup interface is consistently `setup_user(home: Path, dry_run: bool = False) -> SetupResult`.
- Doctor interface is consistently `doctor_user(home: Path) -> DoctorResult`.
- Uninstall interface is consistently `uninstall_user(home: Path, dry_run: bool = False) -> UninstallResult`.
- Owned markers are consistently `<!-- HAIKU_SCRIBE_START -->` and `<!-- HAIKU_SCRIBE_END -->`.
