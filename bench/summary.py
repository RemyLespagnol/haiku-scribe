"""Summarize bench/runs/route-eval.jsonl by tag and case: python3 bench/summary.py [tag...]"""
import json
import sys
from collections import defaultdict
from pathlib import Path

rows = [json.loads(line) for line in (Path(__file__).parent / "runs" / "route-eval.jsonl").read_text().splitlines()]
tags = sys.argv[1:] or sorted({r.get("tag") for r in rows})
by = defaultdict(list)
for r in rows:
    if r.get("tag") in tags:
        by[(r["tag"], r["case"])].append(r)
print(f"{'tag':6} {'case':15} {'scout':6} {'pass':5} {'cost':>7} {'haiku':>6} {'raw':>7} {'tools':>5} {'secs':>5}")
for (tag, case), rs in sorted(by.items()):
    ok = [r for r in rs if "error" not in r]
    avg = lambda k: sum(r.get(k) or 0 for r in ok) / max(len(ok), 1)  # noqa: E731
    print(f"{tag:6} {case:15} {sum(r['scout'] for r in ok)}/{len(rs):<4} {sum(r['pass'] for r in ok)}/{len(rs):<3} "
          f"{avg('cost'):7.3f} {avg('haiku'):6.3f} {avg('raw_main_chars'):7.0f} {avg('main_tools'):5.1f} {avg('secs'):5.0f}")
