"""Deterministic large log-like fixture for the break-even sweep.

Emits a log file of `--lines` lines with `--needles` findable NEEDLE lines spread
through it. The sweep task ("find every NEEDLE line and summarize its context") is
checkable: the answer is correct iff all needle tokens are reported.

Deterministic (fixed seed, synthetic timestamps) so the same size is byte-identical
across runs — the only variable in the sweep is line count.

    python3 bench/fixtures/gen_large_file.py --lines 2000 --needles 5 -o bench/fixtures/large-2000.log
"""

import argparse
import random
from pathlib import Path

LEVELS = ["INFO", "DEBUG", "WARN", "ERROR"]
COMPONENTS = ["auth", "db", "cache", "http", "worker", "scheduler", "billing"]
MESSAGES = [
    "request handled", "connection opened", "connection closed", "cache miss",
    "cache hit", "retry scheduled", "token refreshed", "query executed",
    "job enqueued", "job completed", "rate limit checked", "session validated",
]


def generate(lines: int, needles: int, seed: int = 1234) -> str:
    rng = random.Random(seed)
    # Evenly spread needle positions, avoiding the first/last few lines.
    step = max(1, lines // (needles + 1))
    needle_at = {step * (i + 1): i for i in range(needles)}

    out = []
    for i in range(lines):
        ts = f"2026-01-01T00:{i // 60 % 60:02d}:{i % 60:02d}Z"
        if i in needle_at:
            out.append(
                f"{ts} ERROR billing NEEDLE_TOKEN_{needle_at[i]} "
                f"unexpected negative balance for account acct_{rng.randint(1000, 9999)}"
            )
        else:
            out.append(
                f"{ts} {rng.choice(LEVELS)} {rng.choice(COMPONENTS)} "
                f"{rng.choice(MESSAGES)} id={rng.randint(100000, 999999)}"
            )
    return "\n".join(out) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--lines", type=int, required=True)
    ap.add_argument("--needles", type=int, default=5)
    ap.add_argument("-o", "--out", type=Path, help="output path (default: stdout)")
    args = ap.parse_args()
    text = generate(args.lines, args.needles)
    if args.out:
        args.out.write_text(text)
        print(f"wrote {args.lines} lines, {args.needles} needles -> {args.out}")
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
