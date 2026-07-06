"""Record and report the break-even sweep.

Operator-driven: you run the fixed task in Claude Code (hook-on / hook-off) yourself,
then record the session so its *real* cost is pulled from the transcript by `cost.py`
(no hand-estimation). `report` prints the cost-vs-size curve per arm.

    # after a run, grab its session id (/status) and record it:
    python3 bench/sweep.py record --session <id> --task single-file-2000 --mode hook-on --correct

    python3 bench/sweep.py report

`--task` should encode the size (e.g. `single-file-2000`) so the report groups the
crossover cleanly. `--mode` is `hook-on` or `hook-off`. `--correct` sets the quality
pass (omit it for a wrong/degraded answer).
"""

import argparse
import json
import statistics
from pathlib import Path

from cost import _find_main, _subagent_transcripts, session_cost, tool_counts

RUNS_FILE = Path(__file__).parent / "runs" / "sweep.jsonl"


def _record(args) -> None:
    cost = session_cost(args.session, args.projects)
    main = _find_main(args.session, args.projects)
    main_tools = tool_counts(main)
    sub_reads = sum(tool_counts(s).get("Read", 0) for s in _subagent_transcripts(main))

    run = {
        "task": args.task,
        "mode": args.mode,
        "session": args.session,
        "total_cost": cost["total_cost"],
        "raw_into_main": cost["raw_into_main"],
        "main_reads": main_tools.get("Read", 0),
        "main_greps": main_tools.get("Grep", 0),
        "subagent_reads": sub_reads,
        "correct": bool(args.correct),
        "note": args.note or "",
    }
    RUNS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with RUNS_FILE.open("a") as f:
        f.write(json.dumps(run) + "\n")
    print(json.dumps(run, indent=2))


def _report(args) -> None:
    if not RUNS_FILE.exists():
        print("no runs yet — record some first")
        return
    runs = [json.loads(line) for line in RUNS_FILE.read_text().splitlines() if line.strip()]
    groups: dict[tuple[str, str], list[dict]] = {}
    for r in runs:
        groups.setdefault((r["task"], r["mode"]), []).append(r)

    def med(group, key):
        return statistics.median(r[key] for r in group)

    print("| Task | Mode | N | Median $ | Median raw→main | Median main reads | Correct |")
    print("| --- | --- | ---: | ---: | ---: | ---: | ---: |")
    for (task, mode), group in sorted(groups.items()):
        correct = sum(1 for r in group if r["correct"])
        print(
            f"| {task} | {mode} | {len(group)} | {med(group, 'total_cost'):.4f} | "
            f"{med(group, 'raw_into_main'):.0f} | {med(group, 'main_reads'):.0f} | "
            f"{correct}/{len(group)} |"
        )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--projects", type=Path, default=None)
    sub = ap.add_subparsers(dest="cmd", required=True)

    rec = sub.add_parser("record")
    rec.add_argument("--session", required=True)
    rec.add_argument("--task", required=True, help="e.g. single-file-2000")
    rec.add_argument("--mode", required=True, choices=["hook-on", "hook-off"])
    rec.add_argument("--correct", action="store_true", help="quality pass")
    rec.add_argument("--note", default="")
    rec.set_defaults(func=_record)

    rep = sub.add_parser("report")
    rep.set_defaults(func=_report)

    args = ap.parse_args()
    # session_cost defaults handle projects=None; make it concrete only when given.
    if args.projects is None:
        from cost import DEFAULT_PROJECTS
        args.projects = DEFAULT_PROJECTS
    args.func(args)


if __name__ == "__main__":
    main()
