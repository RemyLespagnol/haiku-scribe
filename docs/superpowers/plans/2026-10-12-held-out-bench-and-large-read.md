# Held-out bench, field audit and large-file Read gate — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Strengthen the evidence that haiku-scribe saves money (held-out cases, n=3 medians, scout citation check, a free audit of real sessions), then ship a whole-file `Read` gate for large text files only if the held-out runs show it pays.

**Architecture:** Bench changes stay in `bench/` (never loaded by Claude Code). Their pure helpers get a free test file, `test_bench.py`. The only shipped change is one more broad rule in `hooks/route`. It is evidence-gated: Task 4 measures whether the main model ever reads a large file whole, and Task 5 ships the gate only if the ship rule holds.

**Tech Stack:** POSIX sh + awk (hooks), Python 3.11+ stdlib (bench, tests), pytest/ruff, `claude -p` for paid runs.

**Spec:** none written. The decisions come from the 2026-10-12 competitor review (Context below) and from `docs/superpowers/evaluations/2026-07-06-v1-2-break-even-sweep.md`. Read the break-even sweep before Task 5.

## Context

- Competitors reviewed 2026-10-12: token-economy-kit, cheap-llm-router, token-saver (bryanvine), claude-code-model-router, subagent-bouncer. None has a behavioral delegation eval. What we take from them:
  - **Large-file Read gate:** token-economy-kit at about 10k tokens, cheap-llm-router at 200 lines.
  - **Token audit from transcripts:** split cache writes by TTL and dedup by `message.id` (token-saver, bouncer).
  - **Medians, not means:** the bouncer's −63% headline came from one outlier run.
  - **Citation check on briefs:** from cheap-llm-router.
- `hooks/route:29-31` gates `Read` only on the 4th distinct file. One large log or source file read whole is never routed, yet the agent description promises "large files, logs".
- **Known loss shape (break-even sweep):** a large file plus a detail-demanding task makes the main model re-read after the brief, for +50% cost. The gate can push into that shape, so it ships only on held-out evidence.
- The bench already prices runs cache-aware (`total_cost_usd` from `claude -p`). The field audit therefore reports token buckets, not dollars.

## Global Constraints

- Hooks: POSIX sh + awk only, no `jq`. Must pass on macOS `/bin/sh` + BSD grep/awk and on Debian dash + GNU grep/mawk. No `{n,}` regex intervals. Fail open.
- `bench/` and tests: Python ≥3.11 stdlib only. No same-quote nesting inside f-strings (that needs 3.12).
- Test files run as `python3 test_x.py` and under pytest.
- Code comments: none by default. At most one line, and only for a non-obvious why.
- Large-file threshold: `40000` bytes (about 10k tokens), whole-file `Read` only (no `offset`/`limit`), text files only.
- Paid runs: `bench/route_eval.py` already uses a clean env (`--setting-sources project,local`, scrubbed `CLAUDE_EFFORT`). Run them with `run_in_background`. Never commit `bench/runs/` (gitignored).
- Held-out cases: never tune `hooks/route` or `agents/haiku-scribe.md` against them.
- Medium effort, n=3 per cell for every number that goes into README or an evaluation doc.

## Review Focus

1. A `Read` of a screenshot or PDF over 40 KB must never be denied: the main model needs to see it. Pinned in Task 5 (binary file test).
2. A ranged `Read` (`offset` or `limit`) of a large file must pass: it is the cheap, targeted path after a grep. Pinned in Task 5.
3. A path with spaces, or a file that does not exist or is unreadable, must not deny and must not crash the hook. Pinned in Task 5.
4. A live session whose last transcript line is half-written must not crash the audit. Pinned in Task 3.
5. One API message streamed as several transcript rows (same `message.id`), and sidechain rows inside a main transcript, must be counted once and never twice. Pinned in Task 3.

---

### Task 1: Bench stats — medians, cost range, citation check

**Files:**
- Modify: `bench/route_eval.py` (`analyze`, `run`, new `text`, `CITE`, `cites`)
- Modify: `bench/summary.py` (whole file)
- Create: `test_bench.py`
- Modify: `pyproject.toml` (`testpaths`), `.github/workflows/ci.yml` (one step)

**Interfaces:**
- Produces: `route_eval.cites(brief: str, wd: Path) -> tuple[int, int]` (citations, bad citations). `analyze()` result gains `brief_text` (popped in `run`). Each run row gains `cites` and `bad_cites`. `test_bench.py` exposes the `write`/`say`/`use`/`result`/`prompt` fixture helpers that Task 3 reuses.

- [ ] **Step 1: Write the failing test**

Create `test_bench.py`:

```python
"""bench/ helpers that cost nothing to run: the citation check and the field audit.
Runnable as `python3 test_bench.py` or via pytest."""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "bench"))
import route_eval  # noqa: E402


def test_cites_flags_missing_files_and_lines_past_eof():
    wd = Path(tempfile.mkdtemp())
    (wd / "pkg").mkdir()
    (wd / "pkg" / "a.py").write_text("x\n" * 10)
    brief = (f"pkg/a.py:3 and a.py:10 (basename) and pkg/a.py:2-4 and {wd}/pkg/a.py:5 are fine; "
             "pkg/a.py:11 is past the end and ghost.py:1 does not exist")
    assert route_eval.cites(brief, wd) == (6, 2)


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
    print("ok")
```

- [ ] **Step 2: Run it to make sure it fails**

Run: `python3 test_bench.py`
Expected: `AttributeError: module 'route_eval' has no attribute 'cites'`

- [ ] **Step 3: Implement `text`, `cites`, and the `analyze`/`run` changes in `bench/route_eval.py`**

Add `import re` to the imports (alphabetical, after `import os`). Add below the `callers` fixture:

```python
CITE = re.compile(r"([\w./-]+\.\w+):(\d+)(?:-(\d+))?")


def text(content):
    return content if isinstance(content, str) else "".join(
        b.get("text", "") for b in content or [] if isinstance(b, dict))


def cites(brief, wd):
    n = bad = 0
    for path, start, end in CITE.findall(brief):
        n += 1
        # shortcut: checks the file exists and the line is in range, not the cited text; diff it if briefs misquote
        hits = [p for p in [Path(path) if path.startswith("/") else wd / path] if p.is_file()]
        hits = hits or [p for p in wd.rglob(Path(path).name) if p.is_file()]
        bad += not any(len(p.read_text(errors="replace").splitlines()) >= int(end or start) for p in hits)
    return n, bad
```

In `analyze`, keep the brief texts:

```python
def analyze(events):
    scout_ids, scout_ok, tools_before, tools_total, raw, stub, briefs, bodies = set(), set(), None, 0, 0, {}, {}, {}
    for e in events:
        if e.get("parent_tool_use_id") is not None:
            continue
        if e.get("subtype") == "task_notification":
            briefs[e.get("tool_use_id")] = e.get("summary") or ""
        content = (e.get("message") or {}).get("content") if isinstance(e.get("message"), dict) else None
        if not isinstance(content, list):
            continue
        for c in content:
            if e.get("type") == "assistant" and c.get("type") == "tool_use":
                if c["name"] in ("Task", "Agent") and "haiku-scribe" in str(c.get("input", {}).get("subagent_type")):
                    scout_ids.add(c["id"])
                    if tools_before is None:
                        tools_before = tools_total
                tools_total += 1
            elif e.get("type") == "user" and c.get("type") == "tool_result":
                raw += len(json.dumps(c.get("content", "")))
                stub[c.get("tool_use_id")] = len(json.dumps(c.get("content", "")))
                if c.get("tool_use_id") in scout_ids and not c.get("is_error"):
                    scout_ok.add(c["tool_use_id"])
                    bodies[c["tool_use_id"]] = text(c.get("content", ""))
    # a backgrounded scout's tool_result is a launch stub; its brief arrives in task_notification
    texts = {t: briefs.get(t, "") if stub.get(t, 0) < 2000 else bodies[t] for t in scout_ok}
    raw += sum(len(b) for t, b in briefs.items() if stub.get(t, 0) < 2000)
    brief = max((len(texts[t]) if stub.get(t, 0) < 2000 else stub[t] for t in scout_ok), default=0)
    return {"scout": bool(scout_ok), "scout_failed": bool(scout_ids) and not scout_ok,
            "tools_before_scout": tools_before, "main_tools": tools_total, "raw_main_chars": raw, "brief_chars": brief,
            "brief_text": "\n".join(texts.values())}
```

In `run`, check citations before the workdir is deleted:

```python
def run(job):
    name, plugin, model, effort, i, tag, sources = job
    setup, prompt, expect, must = CASES[name]
    wd = Path(tempfile.mkdtemp(prefix="hs-route-"))
    setup(wd)
    t0 = time.time()
    try:
        out = subprocess.run(
            ["claude", "-p", "--model", model, "--effort", effort, "--setting-sources", sources,
             "--settings", ONLY_UNDER_TEST, "--plugin-dir", str(plugin), "--dangerously-skip-permissions",
             "--output-format", "stream-json", "--verbose", "--include-hook-events", prompt],
            cwd=wd, env=ENV, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=600, check=False)
        events = [json.loads(line) for line in out.stdout.splitlines() if line.startswith("{")]
        stats = analyze(events)
        stats["cites"], stats["bad_cites"] = cites(stats.pop("brief_text"), wd)
    except subprocess.TimeoutExpired:
        return {"case": name, "tag": tag, "i": i, "error": "timeout"}
    finally:
        shutil.rmtree(wd)
    RUNS.mkdir(exist_ok=True)
    (RUNS / f"route-{tag}-{name}-{i}.jsonl").write_text(out.stdout)
    result = next((e for e in reversed(events) if e.get("type") == "result"), {})
    usage = result.get("modelUsage") or {}
    r = {"case": name, "tag": tag, "model": model, "i": i, "expect": expect, **stats,
         "cost": round(result.get("total_cost_usd") or 0, 4),
         "haiku": round(sum(v.get("costUSD", 0) for k, v in usage.items() if "haiku" in k), 4),
         "secs": round(time.time() - t0), "correct": all(m in (result.get("result") or "") for m in must)}
    r["pass"] = out.returncode == 0 and not r["scout_failed"] and r["correct"] and expect in (None, r["scout"])
    return r
```

- [ ] **Step 4: Rewrite `bench/summary.py` with medians, a cost range and bad citations**

```python
"""Summarize bench/runs/route-eval.jsonl by tag and case, as medians (cost also min-max):
python3 bench/summary.py [tag...]"""
import json
import sys
from collections import defaultdict
from pathlib import Path
from statistics import median

rows = [json.loads(line) for line in (Path(__file__).parent / "runs" / "route-eval.jsonl").read_text().splitlines()]
tags = sys.argv[1:] or sorted({r.get("tag") for r in rows})
by = defaultdict(list)
for r in rows:
    if r.get("tag") in tags:
        by[(r["tag"], r["case"])].append(r)
print(f"{'tag':10} {'case':23} {'scout':6} {'pass':5} {'cost':>7} {'min-max':>13} {'haiku':>6} {'raw':>7} "
      f"{'brief':>6} {'tools':>5} {'secs':>5} {'badcite':>7}")


def med(ok, k):
    return median([r.get(k) or 0 for r in ok]) if ok else 0


for (tag, case), rs in sorted(by.items()):
    ok = [r for r in rs if "error" not in r]
    costs = [r.get("cost") or 0 for r in ok] or [0]
    print(f"{tag:10} {case:23} {sum(r['scout'] for r in ok)}/{len(rs):<4} {sum(r['pass'] for r in ok)}/{len(rs):<3} "
          f"{med(ok, 'cost'):7.3f} {min(costs):6.3f}-{max(costs):<6.3f} {med(ok, 'haiku'):6.3f} "
          f"{med(ok, 'raw_main_chars'):7.0f} {med(ok, 'brief_chars'):6.0f} {med(ok, 'main_tools'):5.1f} "
          f"{med(ok, 'secs'):5.0f} {sum(r.get('bad_cites') or 0 for r in ok)}/{sum(r.get('cites') or 0 for r in ok)}")
```

- [ ] **Step 5: Wire the new test into pytest and CI**

`pyproject.toml`: `testpaths = ["test_contract.py", "test_route.py", "test_bench.py"]`

`.github/workflows/ci.yml`, after the "Route hook test" step:

```yaml
      - name: Bench helpers test
        run: python3 test_bench.py
```

- [ ] **Step 6: Run the tests, lint and summary on old runs**

Run: `python3 test_bench.py && python3 -m pytest -q && ruff check && python3 bench/summary.py af rt bl2`
Expected: `ok`, all pytest tests pass, ruff clean. The summary prints the old tags with medians; `badcite` reads `0/0` because old rows have no citation fields.

- [ ] **Step 7: Commit**

```bash
git add bench/route_eval.py bench/summary.py test_bench.py pyproject.toml .github/workflows/ci.yml
git commit -m "bench: medians, cost range and a citation check on scout briefs"
```

---

### Task 2: Held-out cases

**Files:**
- Modify: `bench/route_eval.py` (`biglog`, `bigmod` fixtures; 6 new `CASES` entries)
- Modify: `test_bench.py` (one test)

**Interfaces:**
- Consumes: `route_eval.CASES`, `route_eval.stdlib` (existing).
- Produces: case names `logging-flow`, `unittest-flow`, `configparser-explain`, `configparser-signatures`, `big-log`, `big-edit`, and fixtures `route_eval.biglog(wd)`, which writes `app.log`, and `route_eval.bigmod(wd)`, which writes `big.py`.

- [ ] **Step 1: Write the failing test** (append to `test_bench.py`, above `if __name__`)

```python
HELD_OUT = ("logging-flow", "unittest-flow", "configparser-explain", "configparser-signatures", "big-log", "big-edit")


def test_held_out_fixtures_sit_in_the_large_read_window():
    for name in HELD_OUT:
        wd = Path(tempfile.mkdtemp())
        route_eval.CASES[name][0](wd)
        assert any(wd.iterdir()), name
    wd = Path(tempfile.mkdtemp())
    route_eval.biglog(wd)
    route_eval.bigmod(wd)
    for f in ("app.log", "big.py"):
        size, lines = (wd / f).stat().st_size, len((wd / f).read_text().splitlines())
        # a whole-file Read must return all of it (2000-line cap) and still be over the 40 KB gate
        assert 40_000 < size < 75_000 and lines <= 2000, (f, size, lines)
    log = (wd / "app.log").read_text()
    assert "02:14:00Z ERROR" in log and "req-e1a01" in log and "req-e1a06" in log and "req-e1a07" not in log
```

- [ ] **Step 2: Run it to make sure it fails**

Run: `python3 test_bench.py`
Expected: `KeyError: 'logging-flow'`

- [ ] **Step 3: Check the exact `configparser` signatures on this Python**

Run: `grep -n "def read_dict\|def has_option\|def _read" "$(python3 -c 'import configparser; print(configparser.__file__)')"`
Expected: lines containing `def read_dict(self, dictionary, source='<dict>'):`, `def has_option(self, section, option):` and `def _read(self, fp, fpname):`. If a signature differs on this Python, change the matching `must` string in Step 4 to the printed text, minus `def ` and the trailing `):`.

- [ ] **Step 4: Add the fixtures and cases**

Below `callers` in `bench/route_eval.py`:

```python
def biglog(wd):
    out = []
    for n in range(750):
        s = n * 8
        ts = f"2026-10-11T{1 + s // 3600:02d}:{s // 60 % 60:02d}:{s % 60:02d}Z"
        if n == 525:
            out.append(f"{ts} WARN db pool high-water 30/32")
        if 555 <= n < 567 and n % 2:
            out.append(f"{ts} ERROR api GET /items/{n} 503 db pool exhausted (32/32) req-e1a{(n - 555) // 2 + 1:02d}")
        else:
            out.append(f"{ts} INFO api GET /items/{n} 200 {n % 37 + 5}ms req-{n:05x}")
    (wd / "app.log").write_text("\n".join(out) + "\n")


def bigmod(wd):
    doc = "Return a copy of xs with every item multiplied by {n}; an empty input gives an empty list."
    fns = "".join(f'def scale_{n:03d}(xs):\n    """{doc.format(n=n)}"""\n    return [x * {n} for x in xs]\n\n\n'
                  for n in range(330))
    (wd / "big.py").write_text(fns + "def total(xs):\n    s = 0\n    for i in range(1, len(xs)):\n        s += xs[i]\n"
                               "    return s\n")
```

`555 <= n < 567 and n % 2` picks n = 555, 557, …, 565: six errors, `req-e1a01`…`req-e1a06`, the first at 02:14:00 (555 × 8 s = 4440 s after 01:00).

Append to `CASES`, after `"one-file-q"`:

```python
    # held out (added 2026-10-12): never tune the hook or the agent contract on these
    "logging-flow": (stdlib("logging"), ("How does a logger.warning() call end up written to a stream? Using the "
                     "logging/ package here, name the classes and methods on the path and say where level filtering "
                     "happens."), None, ["callHandlers", "StreamHandler"]),
    "unittest-flow": (stdlib("unittest"), ("Using the unittest/ package here, trace what `python -m unittest "
                      "discover` does: which modules and functions find the test files, load them into suites, run "
                      "them and print the results."), True, ["TestLoader", "TextTestRunner"]),
    # one ~54 KB file: a summary-tolerant question, then the detail-demanding shape that lost in the break-even sweep
    "configparser-explain": (stdlib("configparser.py"), ("How does configparser.py turn an INI file into sections "
                             "and options? Walk through the parsing loop and explain when interpolation is applied."),
                             None, ["_read", "Interpolation"]),
    "configparser-signatures": (stdlib("configparser.py"), ("List every public method of RawConfigParser in "
                                "configparser.py with its exact signature, in source order."), None,
                                ["read_dict(self, dictionary, source=", "has_option(self, section, option)"]),
    "big-log": (biglog, ("app.log is last night's service log. What went wrong, when did it start, and which "
                "request IDs failed?"), None, ["02:14", "req-e1a01", "req-e1a06"]),
    # coding turn on one ~50 KB file: a whole-file Read gate must cost at most one retry here
    "big-edit": (bigmod, "big.py has an off-by-one bug in total(); fix it.", False, []),
```

- [ ] **Step 5: Run the tests and lint**

Run: `python3 test_bench.py && ruff check`
Expected: `ok`, ruff clean.

- [ ] **Step 6: Commit**

```bash
git add bench/route_eval.py test_bench.py
git commit -m "bench: six held-out cases, two built around one large file"
```

---

### Task 3: Field audit over real transcripts

**Files:**
- Create: `bench/field_audit.py`
- Modify: `test_bench.py` (fixture helpers + one test)

**Interfaces:**
- Consumes: the transcript layout verified on Claude Code 2.1.29x:
  - **Main sessions:** `<config>/projects/<slug>/<session>.jsonl`.
  - **Subagents:** `<config>/projects/<slug>/<session>/subagents/agent-<id>.jsonl`, plus `agent-<id>.meta.json` carrying `{"agentType": "haiku-scribe:haiku-scribe", ...}`.
  - **Message rows:** one API message is written as several rows sharing `message.id` and its usage.
  - **Denials:** a `tool_result` with `is_error: true` and text `"PreToolUse:<Tool> hook error: haiku-scribe routing: ..."`.
  - **Background briefs:** a user row with string content `"<task-notification>…<tool-use-id>ID</tool-use-id>…<result>BRIEF</result>…"`.
- Produces: `field_audit.audit(root, since=None) -> dict` with keys:
  - `sessions`: int
  - `turns`: int
  - `outcomes`: `Counter` over scout/retry/other/ended
  - `briefs`: list of brief lengths in chars
  - `reads_after`: list of Read/Grep/Glob counts after each brief, same turn
  - `tokens`: `dict[(role, model)] -> Counter` over input, cache_read, write_5m, write_1h, output

- [ ] **Step 1: Write the failing test**

Add `import json` to the top imports of `test_bench.py` and `import field_audit  # noqa: E402` right after `import route_eval  # noqa: E402`. Then append the helpers and the test above `if __name__`:

```python
DENY = "PreToolUse:Bash hook error: haiku-scribe routing: this call reads broadly"
USAGE = {"input_tokens": 1, "cache_read_input_tokens": 10, "cache_creation_input_tokens": 4,
         "cache_creation": {"ephemeral_5m_input_tokens": 0, "ephemeral_1h_input_tokens": 4}, "output_tokens": 1}


def write(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))


def say(mid, out=1, model="claude-opus-5-5", blocks=()):
    return {"type": "assistant", "message": {"id": mid, "model": model, "content": list(blocks),
                                             "usage": {**USAGE, "output_tokens": out}}}


def use(tid, name, mid, **inp):
    return say(mid, blocks=[{"type": "tool_use", "id": tid, "name": name, "input": inp}])


def result(tid, body, err=False):
    return {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": tid, "content": body,
                                                     "is_error": err}]}}


def prompt(body):
    return {"type": "user", "timestamp": "2026-10-12T10:00:00Z", "message": {"content": body}}


def test_field_audit_outcomes_reads_and_tokens():
    root = Path(tempfile.mkdtemp())
    main = root / "proj" / "s1.jsonl"
    write(main, [
        prompt("map the email package"),
        say("m1", out=7, blocks=[{"type": "text", "text": "looking"}]),
        use("t1", "Bash", "m1", command="grep -rn x ."),
        result("t1", DENY, err=True),
        use("t2", "Agent", "m2", subagent_type="haiku-scribe:haiku-scribe", prompt="map it"),
        result("t2", "### Summary\n- brief"),
        use("t3", "Read", "m3", file_path="/x/a.py"),
        result("t3", "code"),
        {**say("m9", out=1000), "isSidechain": True},
        prompt("rename total"),
        use("t4", "Bash", "m4", command="grep -rnw total ."),
        result("t4", DENY, err=True),
        use("t5", "Bash", "m5", command="grep -rnw total ."),
    ])
    with open(main, "a") as f:
        f.write('{"type": "assist')
    sub = root / "proj" / "s1" / "subagents" / "agent-a1.jsonl"
    write(sub, [say("h1", out=20, model="claude-haiku-5-5")])
    sub.with_name("agent-a1.meta.json").write_text('{"agentType": "haiku-scribe:haiku-scribe"}')
    a = field_audit.audit(root)
    assert (a["sessions"], a["turns"]) == (1, 2)
    assert a["outcomes"] == {"scout": 1, "retry": 1}
    assert a["briefs"] == [len("### Summary\n- brief")] and a["reads_after"] == [1]
    assert a["tokens"][("main", "claude-opus-5-5")]["output"] == 7 + 1 + 1 + 1 + 1
    assert a["tokens"][("haiku-scribe:haiku-scribe", "claude-haiku-5-5")]["write_1h"] == 4
    assert field_audit.audit(root, since="2026-10-13")["sessions"] == 0
```

`m1` appears as two rows (text, then tool_use) and is counted once at its largest `output_tokens` (7). The sidechain row `m9` is skipped. The half-written last line is ignored.

- [ ] **Step 2: Run it to make sure it fails**

Run: `python3 test_bench.py`
Expected: `ModuleNotFoundError: No module named 'field_audit'`

- [ ] **Step 3: Write `bench/field_audit.py`**

```python
"""Field audit: what the routing hook did in your real Claude Code sessions. Free (reads local
transcripts). Denial outcomes, scout briefs and the reads that followed them, and tokens by
role and model with cache writes split by TTL. Dollars come from bench/route_eval.py instead.

  python3 bench/field_audit.py --since 2026-10-01 [projects-dir]
"""
import argparse
import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median

DENY = "haiku-scribe routing:"
BUCKETS = ("input", "cache_read", "write_5m", "write_1h", "output")


def rows(path):
    with open(path, encoding="utf-8") as f:
        for line in f:
            try:
                yield json.loads(line)
            except ValueError:
                continue


def content(r):
    m = r.get("message")
    return m.get("content") if isinstance(m, dict) else None


def text(c):
    return c if isinstance(c, str) else "".join(b.get("text", "") for b in c or [] if isinstance(b, dict))


def is_prompt(r):
    c = content(r)
    if r.get("type") != "user" or r.get("isMeta") or not isinstance(c, (str, list)):
        return False
    if isinstance(c, list) and any(b.get("type") == "tool_result" for b in c if isinstance(b, dict)):
        return False
    return not text(c).startswith(("<task-notification>", "<local-command"))


def is_scout(call):
    name, inp = call
    return name in ("Agent", "Task") and "haiku-scribe" in str((inp or {}).get("subagent_type"))


def judge(seq, calls, a):
    for i, (kind, x) in enumerate(seq):
        after = [calls[y] for k, y in seq[i + 1:] if k == "use"]
        if kind == "deny":
            nxt = after[0] if after else None
            out = "ended" if nxt is None else "scout" if is_scout(nxt) else "retry" if nxt == calls.get(x) else "other"
            a["outcomes"][out] += 1
        elif kind == "brief":
            a["briefs"].append(len(x))
            a["reads_after"].append(sum(name in ("Read", "Grep", "Glob") for name, _ in after))


def turns(rs, a):
    seq, calls, scouts = [], {}, set()
    for r in rs:
        if is_prompt(r):
            a["turns"] += 1
            judge(seq, calls, a)
            seq = []
            continue
        c = content(r)
        if r.get("type") == "user" and isinstance(c, str) and c.startswith("<task-notification>"):
            tid = re.search(r"<tool-use-id>(.*?)</tool-use-id>", c)
            body = re.search(r"<result>(.*)</result>", c, re.S)
            if tid and tid.group(1) in scouts:
                seq.append(("brief", body.group(1) if body else c))
        for b in c if isinstance(c, list) else []:
            if r.get("type") == "assistant" and b.get("type") == "tool_use":
                calls[b["id"]] = (b["name"], b.get("input"))
                seq.append(("use", b["id"]))
                if is_scout(calls[b["id"]]):
                    scouts.add(b["id"])
            elif b.get("type") == "tool_result":
                body = text(b.get("content"))
                if b.get("is_error") and DENY in body:
                    seq.append(("deny", b.get("tool_use_id")))
                elif b.get("tool_use_id") in scouts and "Async agent launched" not in body:
                    seq.append(("brief", body))
    judge(seq, calls, a)


def tokens(rs, role, acc):
    best = {}
    for r in rs:
        m = r.get("message")
        if r.get("type") != "assistant" or not isinstance(m, dict) or not m.get("usage") or not m.get("id"):
            continue
        if m["id"] not in best or (m["usage"].get("output_tokens") or 0) >= (best[m["id"]]["usage"].get("output_tokens") or 0):
            best[m["id"]] = m
    for m in best.values():
        if m.get("model") == "<synthetic>":
            continue
        u, t = m["usage"], acc[(role, m.get("model", "?"))]
        cc = u.get("cache_creation") or {}
        t["input"] += u.get("input_tokens") or 0
        t["cache_read"] += u.get("cache_read_input_tokens") or 0
        t["write_5m"] += (cc.get("ephemeral_5m_input_tokens") or 0) if cc else (u.get("cache_creation_input_tokens") or 0)
        t["write_1h"] += cc.get("ephemeral_1h_input_tokens") or 0
        t["output"] += u.get("output_tokens") or 0


def audit(root, since=None):
    a = {"sessions": 0, "turns": 0, "outcomes": Counter(), "briefs": [], "reads_after": [],
         "tokens": defaultdict(Counter)}
    for path in sorted(Path(root).glob("*/*.jsonl")):
        rs = list(rows(path))
        if since and next((r["timestamp"] for r in rs if r.get("timestamp")), "") < since:
            continue
        a["sessions"] += 1
        main = [r for r in rs if not r.get("isSidechain")]
        tokens(main, "main", a["tokens"])
        for sub in sorted(path.with_suffix("").glob("subagents/agent-*.jsonl")):
            meta = sub.with_name(sub.stem + ".meta.json")
            role = json.loads(meta.read_text()).get("agentType", "?") if meta.exists() else "?"
            tokens(list(rows(sub)), role, a["tokens"])
        turns(main, a)
    return a


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root", nargs="?", default=Path(os.environ.get("CLAUDE_CONFIG_DIR", Path.home() / ".claude")) / "projects")
    ap.add_argument("--since", help="YYYY-MM-DD: skip sessions that started earlier")
    args = ap.parse_args()
    a = audit(args.root, args.since)
    o, b, r = a["outcomes"], a["briefs"], a["reads_after"]
    print(f"sessions {a['sessions']}, turns {a['turns']}")
    print(f"denials {sum(o.values())}: " + ", ".join(f"{k} {o[k]}" for k in ("scout", "retry", "other", "ended")))
    if b:
        print(f"scout briefs {len(b)}: median {median(b):.0f} chars; "
              f"no read after the brief in {r.count(0)}/{len(r)}, median {median(r):.0f} reads")
    print(f"{'role / model':52}" + "".join(f"{k:>11}" for k in BUCKETS))
    for (role, model), t in sorted(a["tokens"].items()):
        print(f"{role + ' / ' + model:52}" + "".join(f"{t[k]:>11}" for k in BUCKETS))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the tests and lint**

Run: `python3 test_bench.py && ruff check`
Expected: `ok`, ruff clean.

- [ ] **Step 5: Run it on real sessions (free)**

Run: `python3 bench/field_audit.py --since 2026-10-10`
Expected: non-zero sessions, at least one denial (this repo's own sessions hit the hook), and a `haiku-scribe:haiku-scribe / claude-haiku-5-5` token row. Save the output for Task 6. If `denials 0` while you know a deny happened, compare the denial text in one transcript with `DENY` before going further.

- [ ] **Step 6: Commit**

```bash
git add bench/field_audit.py test_bench.py
git commit -m "bench: free field audit of real sessions (denial outcomes, re-reads, tokens by TTL)"
```

---

### Task 4: Baseline paid runs on v0.3.4 (no code change)

**Files:**
- Create: `docs/superpowers/evaluations/2026-10-12-held-out-bench.md` (dated the day the runs finish)

**Interfaces:**
- Consumes: Tasks 1–2 (`route_eval` cases, `summary.py`).
- Produces: tags `h0`, `h0off`, `h0-opus`, `h0off-opus` (held-out) and `r3`, `r3off`, `r3-opus`, `r3off-opus` (headline re-run) in `bench/runs/route-eval.jsonl`. Task 5's decision reads them.

Budget: 120 runs, about $15 at list price on the Max seat, about 40 min with `-j 4`.

- [ ] **Step 1: Held-out cases, routing on and off, both models** (`run_in_background`)

```bash
H="logging-flow unittest-flow configparser-explain configparser-signatures big-log big-edit"
python3 bench/route_eval.py --tag h0 --model sonnet -n 3 $H
HAIKU_SCRIBE_ROUTE=off python3 bench/route_eval.py --tag h0off --model sonnet -n 3 $H
python3 bench/route_eval.py --tag h0-opus --model opus -n 3 $H
HAIKU_SCRIBE_ROUTE=off python3 bench/route_eval.py --tag h0off-opus --model opus -n 3 $H
```

- [ ] **Step 2: Headline re-run at n=3** (README numbers are n=1–2 means)

```bash
B="email-survey specs-history email-headers json-flow"
python3 bench/route_eval.py --tag r3 --model sonnet -n 3 $B
HAIKU_SCRIBE_ROUTE=off python3 bench/route_eval.py --tag r3off --model sonnet -n 3 $B
python3 bench/route_eval.py --tag r3-opus --model opus -n 3 $B
HAIKU_SCRIBE_ROUTE=off python3 bench/route_eval.py --tag r3off-opus --model opus -n 3 $B
```

- [ ] **Step 3: Summarize**

Run: `python3 bench/summary.py h0 h0off h0-opus h0off-opus r3 r3off r3-opus r3off-opus`
Expected: one row per tag and case. Every timeout or `pass` below 3/3 gets a sentence in the doc.

- [ ] **Step 4: Count whole-file Reads of large files** (the input to Task 5's decision)

```bash
python3 - <<'PY'
import glob, json, os
from collections import Counter
hits = Counter()
for p in sorted(glob.glob("bench/runs/route-h0*-*.jsonl")):
    for line in open(p):
        e = json.loads(line) if line.startswith("{") else {}
        if e.get("type") != "assistant" or e.get("parent_tool_use_id"):
            continue
        for c in e["message"]["content"]:
            if c.get("type") == "tool_use" and c["name"] == "Read" and not {"offset", "limit"} & set(c["input"]):
                f = c["input"]["file_path"].rsplit("/", 1)[-1]
                if f in ("app.log", "big.py", "configparser.py") or c["input"]["file_path"].endswith("logging/__init__.py"):
                    hits[os.path.basename(p).rsplit("-", 1)[0]] += 1
print(dict(hits) or "no whole-file Read of a large file")
PY
```

Expected: a dict of `route-<tag>-<case>` → count, or the "no whole-file Read" line.

- [ ] **Step 5: Write the evaluation doc**

Follow the shape of `evaluations/2026-10-10-route-hook.md`:
- a header with date, Claude Code version (`claude --version`), clean env and medium effort;
- the summary table pasted as-is;
- one paragraph each on held-out delegation (scout/pass against `expect`), cost and raw on vs off (medians and ranges), bad citations, and the whole-file Read count from Step 4;
- the field audit output from Task 3 Step 5;
- a "Limits" section: n=3, one Python version of the stdlib fixtures, `-p` one-shot runs only.

Also answer the open INDEX question with the `configparser-signatures` numbers: on the current contract, does the large-file detail task still re-read after the brief?

- [ ] **Step 6: Commit**

```bash
git add docs/superpowers/evaluations/2026-10-12-held-out-bench.md
git commit -m "eval: held-out cases and n=3 headline re-run on v0.3.4"
```

---

### Task 5: Whole-file Read gate for large text files (evidence-gated)

**Files:**
- Modify: `hooks/route:21-31` (new `big()`, `Read` branch, deny text)
- Modify: `test_route.py` (one test)
- Modify: `docs/superpowers/evaluations/2026-10-12-held-out-bench.md` (gate section)

**Interfaces:**
- Consumes: Task 4 Step 4 output; tags `h0`, `h0-opus`.
- Produces: tags `h1`, `h1-opus`, `h1-old`. The ship decision is recorded in the evaluation doc.

- [ ] **Step 1: Decide whether there is anything to catch**

If Task 4 Step 4 printed `no whole-file Read of a large file`, stop here. Write in the evaluation doc: "Gate not built: in N held-out runs the main model never read a large file whole (it grepped or sliced), so a whole-file gate has nothing to catch." Commit the doc and go to Task 6. Otherwise continue.

- [ ] **Step 2: Write the failing test** (append to `test_route.py`, above `test_hooks_json_wiring`)

```python
def test_large_whole_file_read_is_denied():
    d = Path(tempfile.mkdtemp(dir=TMP))
    (d / "big file.log").write_text("x\n" * 25_000)
    (d / "shot.png").write_bytes(b"\x89PNG\r\n\x1a\n" + bytes(50_000))

    def read(f, **kw):
        return hook("tool", sid="s-7", tool_name="Read", tool_input={"file_path": str(d / f), **kw})
    turn("s-7")
    assert read("missing.log") is None
    assert read("shot.png") is None
    assert read("big file.log", offset=1200) is None
    assert read("big file.log", limit=200) is None
    assert read("big file.log") == "deny"
```

That is three distinct files, so the deny comes from the size rule and not from the 4th-file rule.

- [ ] **Step 3: Run it to make sure it fails**

Run: `python3 test_route.py`
Expected: `AssertionError` on the last line (`None == "deny"`).

- [ ] **Step 4: Implement in `hooks/route`**

Below the `field()` line add:

```sh
# ranged Reads are already targeted; binary files (images, PDFs) are for the main model to see
big() { ! printf '%s' "$in" | grep -Eq '"(offset|limit)" *: *[0-9]' && [ -f "$1" ] && [ -r "$1" ] && [ $(wc -c < "$1") -gt 40000 ] && grep -Iq . "$1"; }
```

Replace the `Read)` branch:

```sh
  Read)
    p=$(field file_path)
    echo "read:$p" >> "$state"
    [ "$(grep '^read:' "$state" | sort -u | wc -l)" -ge 4 ] || big "$p" || exit 0 ;;
```

In the deny JSON, change `(a recursive search, many files, or a 4th file this turn). If this search locates code you are about to change` to `(a recursive search, many files, a large file, or a 4th file this turn). If this call locates or opens code you are about to change`.

Also update the header comment's parenthetical on line 4 to `(recursive search, many files, a large file read whole, a 4th distinct file)`.

- [ ] **Step 5: Run the hook tests on both shells**

Run: `python3 test_route.py && ruff check`
Expected: `ok`.

Then the Debian path:

```bash
docker run --rm -v "$PWD":/w -w /w python:3.12-slim sh -c 'python3 test_route.py'
```

Expected: `ok`. `python:3.12-slim` is Debian with dash as `/bin/sh`. If Docker is unavailable, say so and rely on the CI ubuntu job.

- [ ] **Step 6: Commit (gate on, not yet decided)**

```bash
git add hooks/route test_route.py
git commit -m "feat(route): deny a whole-file Read of a large text file once"
```

- [ ] **Step 7: Paid runs with the gate** (`run_in_background`)

```bash
H="logging-flow unittest-flow configparser-explain configparser-signatures big-log big-edit"
python3 bench/route_eval.py --tag h1 --model sonnet -n 3 $H
python3 bench/route_eval.py --tag h1-opus --model opus -n 3 $H
python3 bench/route_eval.py --tag h1-old --model sonnet -n 2 json-flow specs-history email-survey argparse-tour explain-small email-headers rename bug-line one-file-q
python3 bench/summary.py h0 h1 h0-opus h1-opus h1-old af rt
```

- [ ] **Step 8: Apply the ship rule**

Ship only if all four hold, per model:
1. Each case where Task 4 Step 4 found a whole-file Read: h1 median `raw` is below h0, and h1 median cost is ≤ h0.
2. `configparser-signatures` and `big-edit`: h1 median cost ≤ 1.10 × h0, and `pass` is 3/3.
3. `big-edit`: scout 0/3 (an edit turn retries; it does not delegate).
4. `h1-old`: scout and pass match the earlier tags `af`/`rt` on the same cases.

If any fails, run `git revert --no-edit HEAD` (this reverts the Step 6 commit) and write which rule failed, with numbers.

Either way, add a "Large-file Read gate" section to the evaluation doc with the h0/h1 table and the decision, then commit:

```bash
git add docs/superpowers/evaluations/2026-10-12-held-out-bench.md
git commit -m "eval: large-file Read gate, held-out decision"
```

---

### Task 6: Docs, version, PR

**Files:**
- Modify: `CLAUDE.md`, `README.md`, `docs/superpowers/INDEX.md`
- Modify (only if the gate shipped): `.claude-plugin/plugin.json`, `pyproject.toml` (`version` → `0.3.5`)

**Interfaces:**
- Consumes: the evaluation doc's numbers and the Task 5 decision.

- [ ] **Step 1: `CLAUDE.md`**

- Commands block: add `python3 test_bench.py        # bench helpers: citation check, field audit (free)` and `python3 bench/field_audit.py --since YYYY-MM-DD  # free: what the hook did in your real sessions`.
- Notes: replace the `pyproject.toml` bullet's "scoped to the two test files on purpose (`bench/` is paid and never runs in CI)" with "scoped to the three test files on purpose (`bench/` runs are paid and never run in CI; their pure helpers are tested in `test_bench.py`)".
- Only if the gate shipped: in item 2's "Broad =" sentence, append ", or a whole-file `Read` of a text file over 40 KB".

- [ ] **Step 2: `README.md`**

- "Use" section: replace the "Measured in a clean environment…" sentence with the n=3 numbers from the evaluation doc. Delegation counts on broad prompts with and without the hook, one-file runs, and median context and cost change, per model. Only if the gate shipped: add "a large text file read whole" to the parenthetical list of broad reads.
- "Development" section: add `- Field audit (free, reads your local transcripts): python3 bench/field_audit.py --since YYYY-MM-DD`.

- [ ] **Step 3: `docs/superpowers/INDEX.md`**

- Add a row under Current: `` | `evaluations/2026-10-12-held-out-bench.md` | Latest numbers: held-out cases, n=3 medians, field audit; large-file Read gate <shipped v0.3.5 | not shipped: reason>. | ``
- Change the break-even row's "Open: never re-run on current contract." to "Re-run on the current contract in `evaluations/2026-10-12-held-out-bench.md` (`configparser-signatures`)."
- Change the route-hook row's "Latest numbers." to "Superseded numbers: see 2026-10-12."

- [ ] **Step 4: Version (gate shipped only)**

Set `"version": "0.3.5"` in `.claude-plugin/plugin.json` and `version = "0.3.5"` in `pyproject.toml`.

- [ ] **Step 5: Full check**

Run: `python3 test_contract.py && python3 test_route.py && python3 test_bench.py && python3 -m pytest -q && ruff check && claude plugin validate .`
Expected: all pass. Then grep the changed files for leftovers: `git diff main --stat` and `git diff main | grep -n "TODO\|TBD\|\.only\|skip("`. Expected: no hits.

- [ ] **Step 6: Commit and open the PR**

```bash
git add CLAUDE.md README.md docs/superpowers/INDEX.md .claude-plugin/plugin.json pyproject.toml
git commit -m "docs: held-out bench numbers, field audit, gate decision"
git push -u origin HEAD
gh pr create --title "Held-out bench, field audit, large-file Read gate" --body-file - <<'EOF'
## What
- bench: medians and cost range, a citation check on scout briefs, six held-out cases, a free field audit of real sessions.
- hooks/route: a whole-file Read of a text file over 40 KB is denied once (only if the held-out runs passed the ship rule; see the evaluation doc).

## Evidence
docs/superpowers/evaluations/2026-10-12-held-out-bench.md

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
```

Run this on a branch (`git switch -c feat/held-out-bench` before Task 1), never on `main`.
