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
