"""Real per-session cost from a Claude Code transcript.

Sums the real `usage` records in a session `.jsonl` (plus its subagent
transcripts) and applies calibrated Anthropic prices. Reproduces the official
`/cost` baseline ($1.04) instead of hand-estimating it.

Usage:
    python3 bench/cost.py <session-id-or-path> [--projects DIR]

All cache-write / cache-read rates derive from the model's input rate:
    cache_read = input * 0.10
    cache_write_5m = input * 1.25
    cache_write_1h = input * 2.00
So only (input, output) per model is table-driven.
"""

import argparse
import json
from pathlib import Path

# (input, output) $ per MTok. Keys match a substring of message.model.
MODEL_RATES = {
    "haiku": (1.0, 5.0),
    "sonnet": (3.0, 15.0),
    "opus": (15.0, 75.0),
}
DEFAULT_PROJECTS = Path.home() / ".claude" / "projects"


def _rate(model: str) -> tuple[float, float]:
    for key, rates in MODEL_RATES.items():
        if key in model:
            return rates
    raise ValueError(f"unknown model rate for {model!r}")


def message_cost(model: str, usage: dict) -> float:
    """Dollars for one assistant message's usage record."""
    in_rate, out_rate = _rate(model)
    creation = usage.get("cache_creation") or {}
    # Fall back to all-1h when the split is absent (matches the official baseline).
    write_1h = creation.get("ephemeral_1h_input_tokens")
    write_5m = creation.get("ephemeral_5m_input_tokens", 0)
    if write_1h is None:
        write_1h = usage.get("cache_creation_input_tokens", 0)
        write_5m = 0
    tokens_cost = (
        usage.get("input_tokens", 0) * in_rate
        + usage.get("output_tokens", 0) * out_rate
        + usage.get("cache_read_input_tokens", 0) * in_rate * 0.10
        + write_5m * in_rate * 1.25
        + write_1h * in_rate * 2.00
    )
    return tokens_cost / 1_000_000


def iter_usage(path: Path):
    """Yield (msg_id, model, usage) for each assistant message that carries usage.

    Only the top-level `message.usage` is read; the nested `iterations` array
    repeats the same tokens and must not be double-counted. Claude Code also
    sometimes writes the same assistant message twice (same `message.id`); the
    caller dedupes on the yielded id.
    """
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        obj = json.loads(line)
        msg = obj.get("message") or {}
        usage = msg.get("usage")
        if usage and msg.get("model"):
            yield msg.get("id"), msg["model"], usage


def tool_counts(path: Path) -> dict:
    """Count `tool_use` blocks by name in a transcript, deduped by block id.

    Main-session `Read`/`Grep` counts are the substitution signal: with the scout
    doing the reading, a good outcome is the main session reading little raw material.
    """
    counts: dict[str, int] = {}
    seen: set[str] = set()
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        content = (json.loads(line).get("message") or {}).get("content")
        if not isinstance(content, list):
            continue
        for block in content:
            if isinstance(block, dict) and block.get("type") == "tool_use":
                bid = block.get("id")
                if bid in seen:
                    continue
                seen.add(bid)
                name = block.get("name", "?")
                counts[name] = counts.get(name, 0) + 1
    return counts


def _find_main(session: str, projects: Path) -> Path:
    p = Path(session)
    if p.suffix == ".jsonl" and p.exists():
        return p
    matches = list(projects.glob(f"*/{session}.jsonl"))
    if not matches:
        raise FileNotFoundError(f"no transcript for session {session!r} under {projects}")
    return matches[0]


def _subagent_transcripts(main: Path) -> list[Path]:
    sub = main.with_suffix("") / "subagents"
    return sorted(sub.glob("*.jsonl")) if sub.is_dir() else []


def session_cost(session: str, projects: Path = DEFAULT_PROJECTS) -> dict:
    """Real cost breakdown for a session and its subagents.

    Returns total $, per-model $, and `raw_into_main` — the main transcript's
    total cache_creation tokens, a proxy for how much raw context landed in the
    expensive model's window (the "context preserved" KPI).
    """
    main = _find_main(session, projects)
    transcripts = [("main", main)] + [("subagent", s) for s in _subagent_transcripts(main)]

    by_model: dict[str, float] = {}
    raw_into_main = 0
    seen: set[str] = set()
    for role, path in transcripts:
        for msg_id, model, usage in iter_usage(path):
            if msg_id in seen:
                continue
            seen.add(msg_id)
            by_model[model] = by_model.get(model, 0.0) + message_cost(model, usage)
            if role == "main":
                raw_into_main += usage.get("cache_creation_input_tokens", 0)

    return {
        "session": session,
        "main_transcript": str(main),
        "subagent_count": len(transcripts) - 1,
        "cost_by_model": {m: round(c, 6) for m, c in by_model.items()},
        "total_cost": round(sum(by_model.values()), 6),
        "raw_into_main": raw_into_main,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("session", help="session id or path to a transcript .jsonl")
    ap.add_argument("--projects", type=Path, default=DEFAULT_PROJECTS)
    args = ap.parse_args()
    result = session_cost(args.session, args.projects)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
