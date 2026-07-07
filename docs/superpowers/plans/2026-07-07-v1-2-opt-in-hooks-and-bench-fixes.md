# V1.2 Opt-In Hooks + Bench Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make V1.2 nudge hooks opt-in (default off, `setup --hooks on` to enable, plain `setup` removes owned hooks), and fix two trivial blockers (crashing `bench/report.py`, undeclared dev deps).

**Architecture:** `setup_user` gains an `install_hooks` flag (default `False`); when off it strips any Haiku-Scribe-owned hook so re-running `setup` self-heals a previously default-on install. `doctor` only validates hooks when hooks are actually present, so an opt-out install is healthy. The CLI exposes `setup --hooks {off,on}`. Generated content stays source-of-truth as string literals; `doctor.py` remains the health spec and is updated in lockstep.

**Tech Stack:** Python 3.11+ stdlib only (argparse, json, dataclasses, pathlib), pytest, ruff.

## Global Constraints

- No runtime third-party dependencies; stdlib only in `src/haiku_scribe/**`. (`pyproject.toml:10` — `dependencies = []`)
- Every file write goes through a `_write_text_if_changed` helper and backs up pre-existing user content into `~/.claude/backups/haiku-scribe/` before overwriting. (`CLAUDE.md` — "Idempotent, backup-before-mutate writes")
- Never remove non-owned user content: hook removal must be ownership-scoped via `remove_v1_2_hook(settings, command)`. (`CLAUDE.md` — "Ownership tracking so uninstall only removes what we added")
- Generated agent/guidance/hook bodies live only as string literals in `contracts.py` / `v1_2_hooks.py`; editing behavior means editing those literals plus the matching `doctor.py` checks and tests. (`CLAUDE.md` — "Generated content is source-of-truth as string literals")
- Run the suite with `python3 -m pytest` (the `rtk` proxy shadows bare `pytest`; use `rtk proxy python3 -m pytest` in this environment). Expected baseline before changes: 68 passed.

---

### Task 1: Fix `bench/report.py` crash on mixed run schemas

`bench/report.py` globs every `bench/runs/*.jsonl` and indexes `run["task_id"]`, but `bench/runs/sweep.jsonl` is a different benchmark (the V1.2 break-even sweep) whose records use `task`/`total_cost` and have no `task_id`, so `python3 bench/report.py` crashes with `KeyError: 'task_id'`. `report.py` is specifically the CodeGraph Agent Bench report; the sweep has its own reporting (the evaluation markdown). Fix: `load_runs` keeps only records that carry a `task_id`.

**Files:**
- Modify: `bench/report.py:6-15` (the `load_runs` function)
- Test: `bench/test_report.py` (append one test)

**Interfaces:**
- Consumes: nothing new.
- Produces: `load_runs(runs_dir: Path) -> list[dict]` now returns only dicts containing a `"task_id"` key.

- [ ] **Step 1: Write the failing test**

Append to `bench/test_report.py` (inside the existing `ReportTests` class, keeping the file's existing imports `tempfile`, `unittest`, `Path`, `build_markdown_report`, `load_runs`):

```python
    def test_load_runs_skips_records_without_task_id(self):
        with tempfile.TemporaryDirectory() as directory:
            runs_dir = Path(directory) / "runs"
            runs_dir.mkdir()
            # One conforming CodeGraph record and one foreign sweep record.
            (runs_dir / "mixed.jsonl").write_text(
                '{"task_id":"01-orientation","mode":"agent-codegraph","tool_calls":1,'
                '"direct_file_reads":0,"large_outputs":0,"line_evidence_count":0,'
                '"found_right_area":true,"edit_ready":false,'
                '"estimated_context_cost":"low","input_tokens":1,"output_tokens":1,'
                '"cache_creation_tokens":0,"cache_read_tokens":0,'
                '"gross_tokens":2,"no_cache_tokens":2}\n'
                '{"task":"whole-file","mode":"scout","total_cost":0.48,'
                '"raw_into_main":69000,"correct":true}\n'
            )
            runs = load_runs(runs_dir)
            self.assertEqual(len(runs), 1)
            self.assertEqual(runs[0]["task_id"], "01-orientation")
            # build must not raise on the filtered set.
            report = build_markdown_report(runs)
            self.assertIn("01-orientation", report)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `rtk proxy python3 -m pytest bench/test_report.py -k skips_records_without_task_id -v`
Expected: FAIL — `AssertionError: 2 != 1` (both records currently loaded).

- [ ] **Step 3: Filter non-conforming records in `load_runs`**

In `bench/report.py`, replace the loop body so only records with a `task_id` are kept. The current function is:

```python
def load_runs(runs_dir: Path) -> list[dict]:
    if not runs_dir.exists():
        return []

    runs: list[dict] = []
    for path in sorted(runs_dir.glob("*.jsonl")):
        for line in path.read_text().splitlines():
            if line.strip():
                runs.append(json.loads(line))
    return runs
```

Change it to:

```python
def load_runs(runs_dir: Path) -> list[dict]:
    if not runs_dir.exists():
        return []

    runs: list[dict] = []
    for path in sorted(runs_dir.glob("*.jsonl")):
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            # report.py is the CodeGraph Agent Bench report; skip records from
            # other benchmarks (e.g. sweep.jsonl uses "task", not "task_id").
            if isinstance(record, dict) and "task_id" in record:
                runs.append(record)
    return runs
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `rtk proxy python3 -m pytest bench/test_report.py -v`
Expected: PASS (existing report tests + the new one).

- [ ] **Step 5: Verify the documented command runs on checked-in data**

Run: `python3 bench/report.py | head -5`
Expected: prints the `# CodeGraph Agent Bench Report` markdown table with no traceback.

- [ ] **Step 6: Commit**

```bash
git add bench/report.py bench/test_report.py
git commit -m "fix(bench): skip non-codegraph records in report loader"
```

---

### Task 2: Declare dev dependencies in `pyproject.toml`

`pytest` and `ruff` are not declared, so a fresh checkout cannot run the documented `python -m pytest` / `ruff check` commands without ad-hoc installs.

**Files:**
- Modify: `pyproject.toml:5-10` (add an optional-dependencies group)

**Interfaces:**
- Consumes: nothing.
- Produces: `pip install -e ".[dev]"` provides `pytest` and `ruff`.

- [ ] **Step 1: Add the dev optional-dependencies group**

In `pyproject.toml`, after the `dependencies = []` line (line 10) and before `[project.scripts]` (line 12), insert:

```toml

[project.optional-dependencies]
dev = ["pytest>=8", "ruff>=0.6"]
```

The `[project]` table now ends:

```toml
requires-python = ">=3.11"
dependencies = []

[project.optional-dependencies]
dev = ["pytest>=8", "ruff>=0.6"]

[project.scripts]
haiku-scribe = "haiku_scribe.cli:main"
```

- [ ] **Step 2: Verify the metadata parses and resolves**

Run: `python3 -c "import tomllib,pathlib; d=tomllib.loads(pathlib.Path('pyproject.toml').read_text()); print(d['project']['optional-dependencies']['dev'])"`
Expected: `['pytest>=8', 'ruff>=0.6']`

- [ ] **Step 3: Verify a fresh install exposes the tools**

Run: `python3 -m pip install -e ".[dev]" >/dev/null 2>&1 && python3 -m pytest -q 2>&1 | tail -1 && python3 -m ruff check 2>&1 | tail -1`
Expected: pytest reports `68 passed` (or `69 passed` if run after Task 1); ruff prints `All checks passed!` or a concrete lint list (no "command not found").

Note: if `ruff check` reports pre-existing lint findings unrelated to this plan, record them but do not fix them here — this task only makes the tool runnable.

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml
git commit -m "build: declare pytest and ruff as dev dependencies"
```

---

### Task 3: Make `doctor` tolerate an opt-out (hooks-absent) install

Today `_check_settings_file` always calls `_check_v1_2_hook`, so an install with no hooks fails `doctor`. Gate the hook checks on hooks actually being present, so opt-out installs are healthy while any partial/present hook install is still fully validated. This lands *before* the setup default flips so the existing suite stays green throughout.

**Files:**
- Modify: `src/haiku_scribe/doctor.py:16` (import), `src/haiku_scribe/doctor.py:108-131` (`_check_settings_file`), add `_hooks_present` helper.
- Test: `tests/test_doctor.py` (append one test)

**Interfaces:**
- Consumes: `hook_path_for`, `hook_command_for` (already imported), `_group_has_command` (already defined at `doctor.py:68`).
- Produces: `_hooks_present(paths: ClaudePaths, settings: dict[str, Any]) -> bool`.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_doctor.py`. Match the file's existing style for building an install dir. Use the CLI so the whole surface is exercised, then delete the hook file and strip the hook settings to simulate opt-out:

```python
def test_doctor_ok_when_hooks_absent(tmp_path: Path) -> None:
    # Install with hooks, then remove them to model an opt-out install.
    run_cli("setup", "--hooks", "on", "--home", str(tmp_path))

    hook_path = tmp_path / ".claude" / "hooks" / "haiku-scribe-v1-2-nudge.py"
    hook_path.unlink()
    settings_path = tmp_path / ".claude" / "settings.json"
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    settings.pop("hooks", None)
    settings.get("haiku_scribe", {}).pop("owned_v1_2_nudge_hook_command", None)
    settings_path.write_text(json.dumps(settings, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    result = run_cli("doctor", "--home", str(tmp_path))
    assert result.returncode == 0
    assert "Haiku Scribe doctor: ok" in result.stdout
```

Ensure `tests/test_doctor.py` imports `json`, `Path`, and the shared `run_cli` helper (mirror `tests/test_cli_setup.py`; if `run_cli` is not already imported/defined there, import it from the same module the other doctor tests use). This test also depends on `setup --hooks on`, which Task 4 adds — so it is expected to error until Task 4. To keep Task 3 self-contained and green, in Task 3 build the hooks-present install with the existing `prototype-hooks setup` command instead:

```python
    run_cli("setup", "--home", str(tmp_path))
    run_cli("prototype-hooks", "setup", "--home", str(tmp_path))
```

Use those two lines in place of the `run_cli("setup", "--hooks", "on", ...)` line for this task.

- [ ] **Step 2: Run test to verify it fails**

Run: `rtk proxy python3 -m pytest tests/test_doctor.py -k hooks_absent -v`
Expected: FAIL — doctor returns 1 with failures like `missing V1.2 hook script`.

- [ ] **Step 3: Add `_hooks_present` and gate the hook check**

In `src/haiku_scribe/doctor.py`, add this helper directly above `_check_settings_file` (before line 108):

```python
def _hooks_present(paths: ClaudePaths, settings: dict[str, Any]) -> bool:
    if hook_path_for(paths).exists():
        return True
    ownership = settings.get("haiku_scribe")
    if isinstance(ownership, dict) and ownership.get("owned_v1_2_nudge_hook_command"):
        return True
    command = hook_command_for(hook_path_for(paths))
    hooks = settings.get("hooks")
    if isinstance(hooks, dict):
        if _group_has_command(hooks.get("UserPromptSubmit"), "", command):
            return True
        if _group_has_command(hooks.get("PreToolUse"), "Read|Grep", command):
            return True
    return False
```

Then in `_check_settings_file`, replace the unconditional call (line 130):

```python
    failures.extend(_check_v1_2_hook(paths, settings))
    return failures
```

with:

```python
    if _hooks_present(paths, settings):
        failures.extend(_check_v1_2_hook(paths, settings))
    return failures
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `rtk proxy python3 -m pytest tests/test_doctor.py -v`
Expected: PASS — including the new test and all existing doctor tests (a hooks-on install still validates hooks fully because `_hooks_present` is true).

- [ ] **Step 5: Run the full suite to confirm no regressions**

Run: `rtk proxy python3 -m pytest -q 2>&1 | tail -1`
Expected: all pass (69 with Task 1 in place).

- [ ] **Step 6: Commit**

```bash
git add src/haiku_scribe/doctor.py tests/test_doctor.py
git commit -m "feat(doctor): treat hooks as optional, validate only when present"
```

---

### Task 4: Make hooks opt-in in `setup` (`--hooks {off,on}`, default off, off removes owned hooks)

Flip the product default: plain `setup` installs agent + guidance + deny rules only, and removes any Haiku-Scribe-owned hook so a previously default-on install self-heals. `setup --hooks on` installs the V1.2 hooks (current behavior). Removal is ownership-scoped via `remove_v1_2_hook`, so user-authored hooks are never touched.

**Files:**
- Modify: `src/haiku_scribe/setup.py` (add `install_hooks` param; branch planned/real-run; add `removed` to `SetupResult`)
- Modify: `src/haiku_scribe/v1_2_hooks.py` (expose `owned_hook_command`)
- Modify: `src/haiku_scribe/cli.py:18-20` (add `--hooks` arg) and `src/haiku_scribe/cli.py:44-57` (pass flag, print removals)
- Test: `tests/test_cli_setup.py` (update two tests, add three)

**Interfaces:**
- Consumes: `merge_deny_rules`, `render_agent_markdown`, `render_guidance_block`, `render_nudge_hook_script`, `merge_v1_2_hook`, `remove_v1_2_hook`, `hook_path_for`, `hook_command_for`.
- Produces:
  - `setup_user(home: Path, dry_run: bool = False, install_hooks: bool = False) -> SetupResult`
  - `SetupResult(planned: list[str], written: list[Path], removed: list[Path])` (new `removed` field, default empty)
  - `owned_hook_command(settings: dict[str, Any]) -> str | None` in `v1_2_hooks`
  - CLI: `haiku-scribe setup [--hooks {off,on}]` (default `off`)

- [ ] **Step 1: Write the failing tests**

In `tests/test_cli_setup.py`, first **replace** `test_setup_installs_v1_2_hooks_by_default` (lines 85-101) with a default-off test plus an explicit-on test:

```python
def test_setup_installs_no_hooks_by_default(tmp_path: Path) -> None:
    result = run_cli("setup", "--home", str(tmp_path))

    assert result.returncode == 0
    hook_path = tmp_path / ".claude" / "hooks" / "haiku-scribe-v1-2-nudge.py"
    settings_path = tmp_path / ".claude" / "settings.json"
    assert not hook_path.exists()
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    assert "hooks" not in settings
    assert "owned_v1_2_nudge_hook_command" not in settings.get("haiku_scribe", {})


def test_setup_hooks_on_installs_v1_2_hooks(tmp_path: Path) -> None:
    result = run_cli("setup", "--hooks", "on", "--home", str(tmp_path))

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


def test_setup_default_removes_previously_owned_hooks(tmp_path: Path) -> None:
    run_cli("setup", "--hooks", "on", "--home", str(tmp_path))
    result = run_cli("setup", "--home", str(tmp_path))

    assert result.returncode == 0
    hook_path = tmp_path / ".claude" / "hooks" / "haiku-scribe-v1-2-nudge.py"
    settings_path = tmp_path / ".claude" / "settings.json"
    assert not hook_path.exists()
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    assert "hooks" not in settings
    assert "owned_v1_2_nudge_hook_command" not in settings.get("haiku_scribe", {})
    # deny rules survive the hook removal
    assert "Read(**/*credential*)" in settings["permissions"]["deny"]
```

Then **update `test_setup_is_idempotent`** (lines 71-82): it asserts hooks exist, so run it with `--hooks on`:

```python
def test_setup_is_idempotent(tmp_path: Path) -> None:
    first = run_cli("setup", "--hooks", "on", "--home", str(tmp_path))
    second = run_cli("setup", "--hooks", "on", "--home", str(tmp_path))

    assert first.returncode == 0
    assert second.returncode == 0
    guidance = (tmp_path / ".claude" / "CLAUDE.md").read_text(encoding="utf-8")
    settings = json.loads((tmp_path / ".claude" / "settings.json").read_text(encoding="utf-8"))
    assert guidance.count("HAIKU_SCRIBE_START") == 1
    assert settings["permissions"]["deny"].count("Read(**/*credential*)") == 1
    assert len(settings["hooks"]["UserPromptSubmit"]) == 1
    assert len(settings["hooks"]["PreToolUse"]) == 1
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `rtk proxy python3 -m pytest tests/test_cli_setup.py -k "no_hooks_by_default or hooks_on_installs or default_removes_previously or is_idempotent" -v`
Expected: FAIL — `--hooks` is an unrecognized argument (argparse error, exit 2), so these error/fail.

- [ ] **Step 3: Expose `owned_hook_command` in `v1_2_hooks`**

In `src/haiku_scribe/v1_2_hooks.py`, add a public alias next to the existing private helper (after `_owned_hook_command`, around line 459):

```python
def owned_hook_command(settings: dict[str, Any]) -> str | None:
    return _owned_hook_command(settings)
```

- [ ] **Step 4: Add `removed` to `SetupResult` and the `install_hooks` branch in `setup.py`**

In `src/haiku_scribe/setup.py`, update the imports and dataclass. Change the dataclass import line to include `field`:

```python
from dataclasses import dataclass, field
```

Add the hook helpers to the existing `haiku_scribe.v1_2_hooks` import block so it reads:

```python
from haiku_scribe.v1_2_hooks import (
    hook_command_for,
    hook_path_for,
    merge_v1_2_hook,
    owned_hook_command,
    remove_v1_2_hook,
    render_nudge_hook_script,
)
```

Replace the `SetupResult` dataclass:

```python
@dataclass(frozen=True)
class SetupResult:
    planned: list[str]
    written: list[Path]
    removed: list[Path] = field(default_factory=list)
```

Now rewrite `setup_user` to take `install_hooks` and branch. The full new function:

```python
def setup_user(home: Path, dry_run: bool = False, install_hooks: bool = False) -> SetupResult:
    paths = ClaudePaths.for_home(home)
    hook_path = hook_path_for(paths)
    hook_command = hook_command_for(hook_path)

    existing_settings = load_json_object(paths.settings_path) if paths.settings_path.exists() else {}
    prior_hook_command = owned_hook_command(existing_settings)

    planned = [
        f"Would write {paths.agent_path}",
        f"Would update {paths.guidance_path}",
        f"Would merge deny rules into {paths.settings_path}",
    ]
    if install_hooks:
        planned.append(f"Would write {hook_path}")
        planned.append(f"Would merge UserPromptSubmit and PreToolUse hooks into {paths.settings_path}")
    else:
        if hook_path.exists():
            planned.append(f"Would remove {hook_path}")
        if prior_hook_command:
            planned.append(f"Would remove Haiku Scribe-owned hooks from {paths.settings_path}")

    if dry_run:
        return SetupResult(planned=planned, written=[], removed=[])

    paths.agents_dir.mkdir(parents=True, exist_ok=True)
    paths.claude_dir.mkdir(parents=True, exist_ok=True)

    agent_text = render_agent_markdown()
    guidance_existing = paths.guidance_path.read_text(encoding="utf-8") if paths.guidance_path.exists() else ""
    guidance_text = insert_or_replace_block(guidance_existing, render_guidance_block())

    settings = merge_deny_rules(load_json_object(paths.settings_path), DEFAULT_DENY_RULES)
    if install_hooks:
        settings = merge_v1_2_hook(settings, hook_command)
    else:
        remove_v1_2_hook(settings, hook_command)
        if prior_hook_command and prior_hook_command != hook_command:
            remove_v1_2_hook(settings, prior_hook_command)
    settings_text = json.dumps(settings, indent=2, sort_keys=True) + "\n"

    written: list[Path] = []
    removed: list[Path] = []

    if paths.agent_path.exists() and paths.agent_path.read_text(encoding="utf-8") != agent_text:
        backup_existing(paths.agent_path, paths.claude_dir / "backups" / "haiku-scribe")
    if _write_text_if_changed(paths.agent_path, agent_text):
        written.append(paths.agent_path)

    if paths.guidance_path.exists() and paths.guidance_path.read_text(encoding="utf-8") != guidance_text:
        backup_existing(paths.guidance_path, paths.claude_dir / "backups" / "haiku-scribe")
    if _write_text_if_changed(paths.guidance_path, guidance_text):
        written.append(paths.guidance_path)

    if install_hooks:
        hook_path.parent.mkdir(parents=True, exist_ok=True)
        hook_text = render_nudge_hook_script()
        if hook_path.exists() and hook_path.read_text(encoding="utf-8") != hook_text:
            backup_existing(hook_path, paths.claude_dir / "backups" / "haiku-scribe")
        if _write_text_if_changed(hook_path, hook_text):
            written.append(hook_path)
    elif hook_path.exists():
        hook_path.unlink()
        removed.append(hook_path)

    current_settings = paths.settings_path.read_text(encoding="utf-8") if paths.settings_path.exists() else None
    if paths.settings_path.exists() and current_settings != settings_text:
        backup_existing(paths.settings_path, paths.claude_dir / "backups" / "haiku-scribe")
    if _write_text_if_changed(paths.settings_path, settings_text):
        written.append(paths.settings_path)

    return SetupResult(planned=planned, written=written, removed=removed)
```

This assumes `setup.py` already imports `insert_or_replace_block`, `load_json_object`, `merge_deny_rules`, `render_agent_markdown`, `render_guidance_block`, `DEFAULT_DENY_RULES`, and `backup_existing` (it does — see the current import block at `setup.py:7-16`). Keep the existing module-level `_write_text_if_changed` helper unchanged.

- [ ] **Step 5: Add the `--hooks` flag and print removals in `cli.py`**

In `src/haiku_scribe/cli.py`, add the argument to the `setup` subparser (after line 20, the `--home` line):

```python
    setup.add_argument(
        "--hooks",
        choices=["off", "on"],
        default="off",
        help="Install the opt-in V1.2 nudge hooks (default: off)",
    )
```

Then update the `setup` dispatch block. Replace lines 45-57:

```python
        try:
            result = setup_user(args.home, dry_run=args.dry_run, install_hooks=args.hooks == "on")
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
            for path in result.removed:
                print(f"Removed {path}")
        return 0
```

- [ ] **Step 6: Run the updated setup tests**

Run: `rtk proxy python3 -m pytest tests/test_cli_setup.py -v`
Expected: PASS — the two default-off tests, the hooks-on test, the removal test, and the (now `--hooks on`) idempotency test all pass.

- [ ] **Step 7: Run the full suite**

Run: `rtk proxy python3 -m pytest -q 2>&1 | tail -1`
Expected: all pass. (`test_full_v1_user_journey` now installs no hooks by default and doctor stays green thanks to Task 3.)

- [ ] **Step 8: Manual end-to-end check against a scratch home**

Run:
```bash
TMP=$(mktemp -d)
python3 -m haiku_scribe setup --hooks on --home "$TMP" && python3 -m haiku_scribe doctor --home "$TMP"
python3 -m haiku_scribe setup --home "$TMP"
test ! -f "$TMP/.claude/hooks/haiku-scribe-v1-2-nudge.py" && echo "HOOK REMOVED OK"
python3 -m haiku_scribe doctor --home "$TMP"
rm -rf "$TMP"
```
Expected: first doctor `ok`; second setup prints a `Removed ...` line; `HOOK REMOVED OK`; final doctor `ok`.

- [ ] **Step 9: Commit**

```bash
git add src/haiku_scribe/setup.py src/haiku_scribe/cli.py src/haiku_scribe/v1_2_hooks.py tests/test_cli_setup.py
git commit -m "feat(setup): make V1.2 hooks opt-in via --hooks, default off"
```

---

### Task 5: Update docs to reflect opt-in hooks

`README.md` and the project `CLAUDE.md` state hooks are installed as part of setup; correct them to describe hooks as opt-in.

**Files:**
- Modify: `README.md:44`, `README.md:48`
- Modify: `CLAUDE.md` (the sentence describing what `setup` writes, and the V1.2 hooks bullet in "The four surfaces it manages")

- [ ] **Step 1: Update README**

In `README.md`, replace line 44:

```
- V1.2 prompt nudge hooks under `~/.claude/hooks/`, with a size-gated fallback for very large direct reads;
```

with:

```
- opt-in V1.2 prompt nudge hooks under `~/.claude/hooks/` (install with `setup --hooks on`; plain `setup` leaves them off and removes any previously installed ones), with a size-gated fallback for very large direct reads;
```

And replace line 48:

```
- `doctor` checks for missing files, unsafe agent drift, missing guidance, missing deny rules, and V1.2 hooks;
```

with:

```
- `doctor` checks for missing files, unsafe agent drift, missing guidance, and missing deny rules, and validates the V1.2 hooks only when they are installed;
```

- [ ] **Step 2: Update the project `CLAUDE.md`**

In `CLAUDE.md`, in the "What this is" paragraph, change the sentence that reads "It writes an agent file, a managed `CLAUDE.md` guidance block, safety deny rules, and V1.2 nudge hooks." to:

```
It writes an agent file, a managed `CLAUDE.md` guidance block, and safety deny rules, and can optionally install V1.2 nudge hooks via `setup --hooks on`.
```

Then in the "**V1.2 nudge hooks**" bullet under "The four surfaces it manages", prepend a sentence noting they are opt-in:

```
- **V1.2 nudge hooks** *(opt-in; `setup --hooks on`, off by default, and plain `setup` removes any Haiku-Scribe-owned hook)* — `v1_2_hooks.py` writes a standalone hook script ...
```

(keep the remainder of that bullet unchanged).

- [ ] **Step 3: Verify no test or doctor references broke**

Run: `rtk proxy python3 -m pytest -q 2>&1 | tail -1`
Expected: all pass (docs-only change; sanity re-run).

- [ ] **Step 4: Commit**

```bash
git add README.md CLAUDE.md
git commit -m "docs: describe V1.2 hooks as opt-in"
```

---

## Self-Review

**Spec coverage** (request was "passage opt-in + 2 fix triviaux"):
- Opt-in hooks: Task 4 (setup flag + default off + owned-hook removal), Task 3 (doctor tolerates absent hooks), Task 5 (docs). Covered.
- Fix 1 (`bench/report.py` crash): Task 1. Covered.
- Fix 2 (dev deps): Task 2. Covered.

**Placeholder scan:** No "TBD"/"handle edge cases"/"similar to"/bare-prose code steps — every code step shows full code. Clear.

**Type consistency:**
- `setup_user(home, dry_run=False, install_hooks=False)` — defined Task 4 Step 4, called with `install_hooks=args.hooks == "on"` Task 4 Step 5. Consistent.
- `SetupResult` gains `removed: list[Path]` — defined Task 4 Step 4, consumed in cli Step 5 (`result.removed`). Consistent.
- `owned_hook_command(settings)` — defined Task 4 Step 3, used Task 4 Step 4. Consistent.
- `_hooks_present(paths, settings)` — defined Task 3 Step 3, used same step. Consistent.
- `load_runs` return contract (only `task_id` records) — Task 1, matches `build_markdown_report` indexing on `run["task_id"]`. Consistent.

**Sequencing note:** Task 3 lands the doctor tolerance before Task 4 flips the default, so `python3 -m pytest` is green after every task's final commit. Task 3's new test builds its hooks-present fixture via `prototype-hooks setup` (available today), not `setup --hooks on` (added in Task 4).
