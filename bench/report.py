import json
from collections import Counter, defaultdict
from pathlib import Path


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


def build_markdown_report(runs: list[dict]) -> str:
    if not runs:
        return "# CodeGraph Agent Bench Report\n\nNo runs found in `bench/runs/*.jsonl`.\n"

    grouped: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for run in runs:
        grouped[(run["task_id"], run["mode"])].append(run)

    lines = [
        "# CodeGraph Agent Bench Report",
        "",
        "| Task | Mode | Runs | Avg Tool Calls | Avg Direct Reads | Avg Large Outputs | Avg Line Evidence | Found Right Area | Edit Ready | Context Cost | Avg Gross Tokens | Avg No-Cache Tokens | Avg Input Tokens | Avg Output Tokens | Avg Cache Create | Avg Cache Read |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]

    for (task_id, mode), group in sorted(grouped.items()):
        lines.append(
            "| {task_id} | {mode} | {runs} | {tool_calls:.1f} | {direct_reads:.1f} | "
            "{large_outputs:.1f} | {line_evidence:.1f} | {found_rate} | {edit_rate} | {costs} | "
            "{gross_tokens:.1f} | {no_cache_tokens:.1f} | {input_tokens:.1f} | {output_tokens:.1f} | "
            "{cache_creation_tokens:.1f} | {cache_read_tokens:.1f} |".format(
                task_id=task_id,
                mode=mode,
                runs=len(group),
                tool_calls=_average(group, "tool_calls"),
                direct_reads=_average(group, "direct_file_reads"),
                large_outputs=_average(group, "large_outputs"),
                line_evidence=_average(group, "line_evidence_count"),
                found_rate=_percentage(group, "found_right_area"),
                edit_rate=_percentage(group, "edit_ready"),
                costs=_cost_distribution(group),
                gross_tokens=_average(group, "gross_tokens"),
                no_cache_tokens=_average(group, "no_cache_tokens"),
                input_tokens=_average(group, "input_tokens"),
                output_tokens=_average(group, "output_tokens"),
                cache_creation_tokens=_average(group, "cache_creation_tokens"),
                cache_read_tokens=_average(group, "cache_read_tokens"),
            )
        )

    return "\n".join(lines) + "\n"


def _average(group: list[dict], key: str) -> float:
    return sum(float(run.get(key, 0)) for run in group) / len(group)


def _percentage(group: list[dict], key: str) -> str:
    passed = sum(1 for run in group if run.get(key) is True)
    return f"{round((passed / len(group)) * 100)}%"


def _cost_distribution(group: list[dict]) -> str:
    counts = Counter(str(run.get("estimated_context_cost", "unknown")) for run in group)
    return ", ".join(f"{name}:{counts[name]}" for name in sorted(counts))


def main() -> None:
    runs = load_runs(Path(__file__).parent / "runs")
    print(build_markdown_report(runs), end="")


if __name__ == "__main__":
    main()
