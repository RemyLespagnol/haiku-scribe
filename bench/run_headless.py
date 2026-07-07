"""Automated break-even sweep driver: real headless `claude -p` runs.

For each file size and each arm this launches a real non-interactive Claude Code
session on a fixed task over a deterministic log fixture, then records the run's
*real* cost (via `cost.py`) into the sweep.

Two arms, toggled by (un)installing haiku-scribe against the real `~/.claude`:
  - `raw`   : haiku-scribe UNINSTALLED — no agent, no guidance. The main model
              reads the file directly. This is the true non-delegated baseline.
  - `scout` : full v1.2 INSTALLED — the main model delegates to the subagent.

Install state flips once per arm (not per run) to minimise churn; the driver
re-runs `setup` at the end so your normal v1.2 install is left in place.

The task is whole-file comprehension (incident summary), not needle-grepping,
and Bash/Grep/Glob are hard-denied so the file must actually be Read into a
model's context. Correctness is still auto-checked: the summary must name all
needle tokens.

    python3 bench/run_headless.py --sizes 500 2000 5000 10000 --runs 3

Each run spends real money on your account. Use `--sizes 2000 --runs 1` to smoke
the chain first.
"""

import argparse
import json
import os
import subprocess
import sys
from argparse import Namespace
from pathlib import Path

import sweep
from cost import DEFAULT_PROJECTS
from fixtures.gen_large_file import generate

BENCH = Path(__file__).parent
FIXTURES = BENCH / "fixtures"
NEEDLES = 5

PROMPT = (
    "Read the ENTIRE log file bench/fixtures/large-{n}.log and write an incident "
    "summary covering: (1) the distribution of log levels, (2) the busiest "
    "component, (3) the ordered sequence of every billing NEEDLE incident with its "
    "timestamp, and (4) whether NEEDLE errors correlate with preceding WARN lines. "
    "You must read the whole file to answer accurately."
)

# Hard-denied main-session tools per arm (--disallowedTools wins even under
# --dangerously-skip-permissions, unlike --allowedTools). `raw` loses every
# escape hatch — no delegation, no shell, no grep — so it MUST Read the file
# itself (the heavy-context regime we price). `scout` keeps Task/Agent to
# delegate but still can't shell out.
# NOTE: the deny list also applies inside subagents, so `scout` denies Grep/Glob
# to the haiku-scribe agent too. Fine for the single-file task (it only needs
# Read); drop Grep/Glob from the scout deny for future multi-file scenarios.
MODE_DENY = {
    "raw": "Task,Agent,Bash,Grep,Glob,WebFetch,WebSearch",
    "scout": "Bash,Grep,Glob,WebFetch,WebSearch",
}


def ensure_fixture(lines: int) -> Path:
    path = FIXTURES / f"large-{lines}.log"
    if not path.exists():
        path.write_text(generate(lines, NEEDLES))
    return path


def _haiku_scribe(cmd: str) -> None:
    """Flip real ~/.claude install state (setup / uninstall)."""
    env = {**os.environ, "PYTHONPATH": str(BENCH.parent / "src")}
    subprocess.run([sys.executable, "-m", "haiku_scribe", cmd],
                   cwd=BENCH.parent, env=env, text=True,
                   capture_output=True, check=True)


def run_one(lines: int, mode: str, run_idx: int, model: str) -> dict:
    ensure_fixture(lines)
    proc = subprocess.run(
        [
            "claude", "-p", PROMPT.format(n=lines),
            "--output-format", "json",
            "--model", model,
            "--disallowedTools", MODE_DENY[mode],
            "--dangerously-skip-permissions",
        ],
        cwd=BENCH.parent,
        env=os.environ.copy(),
        text=True,
        capture_output=True,
        check=True,
    )
    out = json.loads(proc.stdout)
    result_text = out.get("result", "")
    correct = all(f"NEEDLE_TOKEN_{i}" in result_text for i in range(NEEDLES))

    sweep._record(
        Namespace(
            session=out["session_id"],
            task=f"single-file-{lines}",
            mode=mode,
            correct=correct,
            note=f"headless run {run_idx}; cli_cost={out.get('total_cost_usd')}",
            projects=DEFAULT_PROJECTS,
        )
    )
    return {"session": out["session_id"], "correct": correct,
            "cli_cost": out.get("total_cost_usd")}


MODE_INSTALL = {"raw": "uninstall", "scout": "setup"}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sizes", type=int, nargs="+", default=[500, 2000, 5000, 10000])
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--modes", nargs="+", default=["raw", "scout"],
                    choices=["raw", "scout"])
    ap.add_argument("--model", default="sonnet",
                    help="main-session model, e.g. 'sonnet[1m]' to avoid compaction")
    args = ap.parse_args()

    # Alternate arm order per size (raw-first, then scout-first, ...) so neither
    # arm systematically runs on a warmer prompt cache.
    cells: list[tuple[int, str]] = []
    for i, lines in enumerate(args.sizes):
        order = args.modes if i % 2 == 0 else list(reversed(args.modes))
        for mode in order:
            cells.extend((lines, mode) for _ in range(args.runs))

    total = len(cells)
    installed: str | None = None
    try:
        for done, (lines, mode) in enumerate(cells, 1):
            if installed != mode:  # flip real ~/.claude only when the arm changes
                print(f"=== haiku-scribe {MODE_INSTALL[mode]} (arm {mode}) ===", flush=True)
                _haiku_scribe(MODE_INSTALL[mode])
                installed = mode
            print(f"[{done}/{total}] size={lines} mode={mode} ...", flush=True)
            try:
                info = run_one(lines, mode, done, args.model)
                print(f"    session={info['session']} correct={info['correct']} "
                      f"cli_cost={info['cli_cost']}", flush=True)
            except subprocess.CalledProcessError as e:
                print(f"    FAILED: {e.stderr[:300]}", file=sys.stderr, flush=True)
    finally:
        print("=== restoring full v1.2 install (setup) ===", flush=True)
        _haiku_scribe("setup")

    print("\n--- report ---")
    sweep._report(Namespace())


if __name__ == "__main__":
    main()
