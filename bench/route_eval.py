"""Routing eval: does the main model delegate to haiku-scribe when reading is broad,
and stay direct when it is not? Paid (runs `claude -p` on the logged-in account);
never in CI. Clean env: `--setting-sources project,local` drops the user's global
CLAUDE.md, plugins and hooks, so only the plugin under test steers routing.

  python3 bench/route_eval.py --plugin . --model sonnet -n 2 json-flow bug-line
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RUNS = REPO / "bench" / "runs"
STDLIB = Path(argparse.__file__).parent
# with --sources user..., the installed marketplace copy would shadow the plugin under test
ONLY_UNDER_TEST = json.dumps({"enabledPlugins": {"haiku-scribe@haiku-scribe": False}})
# the parent session's effort leaks through these and would override --effort
ENV = {k: v for k, v in os.environ.items() if k not in ("CLAUDE_EFFORT", "CLAUDE_CODE_EFFORT_LEVEL")}


def stdlib(*names):
    def setup(wd):
        for n in names:
            src = STDLIB / n
            if src.is_dir():
                shutil.copytree(src, wd / n, ignore=shutil.ignore_patterns("__pycache__"))
            else:
                shutil.copy(src, wd / n)
    return setup


def specs(wd):
    shutil.copytree(REPO / "docs" / "superpowers" / "specs", wd / "specs")


def transcript(wd):
    shutil.copy(REPO / "docs" / "superpowers" / "evaluations" / "fixtures" / "noisy-claude-session-sample.md",
                wd / "session.md")
    stdlib("email")(wd)


def bug(wd):
    (wd / "calc.py").write_text("def total(xs):\n    s = 0\n    for i in range(1, len(xs)):\n        s += xs[i]\n"
                                "    return s\n")


def callers(wd):
    (wd / "calc.py").write_text("def total(xs):\n    return sum(xs)\n")
    for n in ("cart", "invoice", "report", "stats"):
        (wd / f"{n}.py").write_text(f"from calc import total\n\n\ndef {n}_sum(xs):\n    return total(xs)\n")


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


# name: (setup, prompt, expect_scout, answer must contain)
CASES = {
    # two files carry the answer: the model may decline the scout after the gate and read directly
    "json-flow": (stdlib("json"), ("Explain how json.dumps turns a Python object into a string, using the json/ "
                  "package here: modules and functions involved, and when the C accelerator is used instead of "
                  "pure Python."), None, ["iterencode", "c_make_encoder"]),
    "specs-history": (specs, ("Read the design specs in specs/ and explain how the project's position on "
                      "PreToolUse hooks changed over time. Cite the spec for each change."), True, ["PreToolUse"]),
    "email-survey": (stdlib("email"), ("I'm new to this package. Give me an architecture overview: the main "
                     "modules, how parsing flows from raw bytes to a Message object, and where policy objects "
                     "plug in."), True, ["feedparser", "policy"]),
    # one large file: a class/def grep answers it about as cheaply as a scout, so either route passes
    "argparse-tour": (stdlib("argparse.py"), ("What's in argparse.py? List the main classes and what each one "
                      "is for."), None, ["ArgumentParser", "Action"]),
    # broad-sounding wording on a one-file task: the hook fires, the model should still read directly
    "explain-small": (bug, "Explain what total() in calc.py does.", False, ["total"]),
    # broad, with none of the usual "overview/explain/how does" wording
    "email-headers": (stdlib("email"), ("Which files in email/ deal with header parsing or folding, and what does "
                      "each one depend on?"), True, ["headerregistry", "_header_value_parser"]),
    # coding turn over 5 files: what the 4th-Read gate costs real work
    "rename": (callers, "Rename the function total() to sum_items() everywhere in this project.", False, []),
    "bug-line": (bug, "calc.py has an off-by-one bug in total(); fix it.", False, []),
    "one-file-q": (stdlib("json"), "In json/decoder.py, what attributes does JSONDecodeError set?", False,
                   ["lineno", "colno"]),
}


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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cases", nargs="*")
    ap.add_argument("--plugin", default=str(REPO))
    ap.add_argument("--model", default="sonnet")
    ap.add_argument("--effort", default="medium")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--tag", default="wt")
    ap.add_argument("-j", type=int, default=4)
    ap.add_argument("--sources", default="project,local", help="user,project,local = the user's real setup")
    a = ap.parse_args()
    jobs = [(c, Path(a.plugin).resolve(), a.model, a.effort, i, a.tag, a.sources) for c in a.cases or CASES for i in range(a.n)]
    with ThreadPoolExecutor(a.j) as pool, open(RUNS / "route-eval.jsonl", "a") as log:
        for r in pool.map(run, jobs):
            log.write(json.dumps(r) + "\n")
            log.flush()
            print("PASS" if r.get("pass") else "FAIL", json.dumps(r), flush=True)


if __name__ == "__main__":
    RUNS.mkdir(exist_ok=True)
    sys.exit(main())
