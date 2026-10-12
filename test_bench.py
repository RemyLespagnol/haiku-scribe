"""bench/ helpers that cost nothing to run: the citation check and the field audit.
Runnable as `python3 test_bench.py` or via pytest."""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "bench"))
import route_eval  # noqa: E402
import field_audit  # noqa: E402


def test_cites_flags_missing_files_and_lines_past_eof():
    wd = Path(tempfile.mkdtemp())
    (wd / "pkg").mkdir()
    (wd / "pkg" / "a.py").write_text("x\n" * 10)
    brief = (f"pkg/a.py:3 and a.py:10 (basename) and pkg/a.py:2-4 and {wd}/pkg/a.py:5 are fine; "
             "pkg/a.py:11 is past the end and ghost.py:1 does not exist")
    assert route_eval.cites(brief, wd) == (6, 2)
    (wd / "2026-07-04-design.md").write_text("x\n" * 5)
    assert route_eval.cites("design.md:5 (dated name shortened), sign.md:1 (not a name)", wd) == (2, 1)


def test_any_result_turn_can_carry_the_answer():
    # a backgrounded command re-opens the -p session; its last turn only acknowledges the notification
    events = [{"type": "result", "result": "read_dict(self) and has_option(self)"},
              {"type": "result", "result": "background find finished, answer stands"}]
    assert route_eval.correct(events, ["read_dict(self)", "has_option(self)"])
    assert not route_eval.correct(events, ["read_dict(self)", "missing"])


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
    write(root / "-private-var-folders-T-hs-route-abc" / "s2.jsonl", [prompt("bench run"), say("b1", out=500)])
    a = field_audit.audit(root)
    assert (a["sessions"], a["turns"]) == (1, 2)
    assert a["outcomes"] == {"scout": 1, "retry": 1}
    assert a["briefs"] == [len("### Summary\n- brief")] and a["reads_after"] == [1]
    assert a["tokens"][("main", "claude-opus-5-5")]["output"] == 7 + 1 + 1 + 1 + 1
    assert a["tokens"][("haiku-scribe:haiku-scribe", "claude-haiku-5-5")]["write_1h"] == 4
    assert field_audit.audit(root, since="2026-10-13")["sessions"] == 0


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
    print("ok")
