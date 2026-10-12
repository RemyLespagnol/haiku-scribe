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
READER = re.compile(r"(^|[;&|]\s*)(cat|sed|head|tail|grep|rg|awk|nl)\s")
BUCKETS = ("input", "cache_read", "write_5m", "write_1h", "output")


def rows(path):
    with open(path, encoding="utf-8", errors="replace") as f:
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


def same_call(a, b):
    def strip(c):
        # a retry often rewords only the Bash description
        return c[0], {k: v for k, v in (c[1] or {}).items() if k != "description"}
    return b is not None and strip(a) == strip(b)


def judge(seq, calls, a):
    for i, (kind, x) in enumerate(seq):
        after = [calls[y] for k, y in seq[i + 1:] if k == "use"]
        if kind == "deny":
            nxt = after[0] if after else None
            out = "ended" if nxt is None else "scout" if is_scout(nxt) else "retry" if same_call(nxt, calls.get(x)) else "other"
            a["outcomes"][out] += 1
        elif kind == "brief":
            a["briefs"].append(len(x))
            a["reads_after"].append(sum(name in ("Read", "Grep", "Glob") or name == "Bash" and bool(
                READER.search(str((inp or {}).get("command", "")))) for name, inp in after))


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
            body = re.search(r"<result>(.*)</result>", c, re.DOTALL)
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
        # route_eval's own `claude -p` runs share this store, from temp dirs named hs-route-*
        if "hs-route-" in path.parent.name:
            continue
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
