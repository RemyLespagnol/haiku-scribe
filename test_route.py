"""hooks/route + hooks/broad-bash: deny the first broad read of a turn once, judged by
the tool call, never by prompt wording. Runnable as `python3 test_route.py` or via pytest."""
import json
import os
import subprocess
import tempfile
from pathlib import Path

HOOKS = Path(__file__).parent / "hooks"
TMP = tempfile.mkdtemp()
os.environ.pop("XDG_RUNTIME_DIR", None)


def hook(mode, sid="s-1", env=None, **payload):
    out = subprocess.run([str(HOOKS / "route"), mode], input=json.dumps({"session_id": sid, **payload}), text=True,
                         capture_output=True, env={**os.environ, "TMPDIR": TMP, **(env or {})}, check=True).stdout
    return json.loads(out)["hookSpecificOutput"]["permissionDecision"] if out else None


def turn(sid="s-1"):
    hook("prompt", sid=sid, prompt="anything")


def bash(cmd, sid="s-1", **kw):
    return hook("tool", sid=sid, tool_name="Bash", tool_input={"command": cmd}, **kw)


def broad(cmd):
    return subprocess.run([str(HOOKS / "broad-bash"), json.dumps(cmd)[1:-1]]).returncode == 0


def test_broad_bash_classifier():
    for cmd in ("find . -type f | head -200", "find . -path '*json*' -name '*.py'", "ls -la specs/ && grep -rn -i x specs/",
                "grep -n foo *.py", "rg PreToolUse", "ls -R", "tree src", "wc -l json/*.py", "cat a.py b.py c.py",
                "sed -n 1,20p a.md b.md c.md", "cd specs; for f in a.md b.md c.md; do head -3 $f; done",
                "rtk grep -rn x .", 'cd /x && grep -n "c_make\\|enc" *.py', "cd /x\ngrep -rn foo .",
                "rg -n foo src/", 'echo "a\\"b" && find . -type f'):
        assert broad(cmd), cmd
    for cmd in ("ls", "ls -la specs/", "cat -n calc.py", "find . -name argparse.py", "find . -path '*json/decoder.py'",
                'grep -n "class .*Error" -A 25 ./json/decoder.py', "sed -n 105,120p json/__init__.py",
                "head -60 argparse.py", "python3 -c 'import glob; print(glob.glob(\"*\"))'", "git log --oneline -5",
                "tail -n 50 app.log", "cat a.py b.py", "cat package.json 2>/dev/null | head",
                "tail -n 50 app.log 2>&1 | grep ERROR", "head -5 a.log > out.txt", "cat a b | wc -l",
                "cat a b > c", "rg -n foo file.py", "for i in 1 2 3 4; do echo $i; done",
                "cat > f.md <<'EOF'\n- *bold*\nEOF", 'echo "a\\"b" && ls', "x" * 30000):
        assert not broad(cmd), cmd


def test_denies_first_broad_read_once_per_turn():
    turn()
    assert bash("cat -n calc.py") is None
    assert bash("cd /x && grep -rn foo .") == "deny"
    assert bash("grep -rn foo .") is None
    turn()
    assert bash("find . -type f") == "deny"


def test_fourth_distinct_file_read_is_denied():
    turn("s-2")
    for f in ("a", "b", "a", "c"):
        assert hook("tool", sid="s-2", tool_name="Read", tool_input={"file_path": f"/x/{f}.py"}) is None
    assert hook("tool", sid="s-2", tool_name="Read", tool_input={"file_path": "/x/d.py"}) == "deny"


def test_scout_call_disarms_and_other_agents_are_never_gated():
    turn()
    assert hook("tool", tool_name="Agent", tool_input={"subagent_type": "Explore"}) is None
    assert hook("tool", tool_name="Agent", tool_input={"subagent_type": "haiku-scribe:haiku-scribe"}) is None
    assert bash("find . -type f") is None


def test_edit_disarms_the_turn():
    turn("s-4")
    assert hook("tool", sid="s-4", tool_name="Edit", tool_input={"file_path": "/x/a.py"}) is None
    assert bash("find . -type f", sid="s-4") is None


def test_parallel_calls_deny_once():
    turn("s-5")
    payload = json.dumps({"session_id": "s-5", "tool_name": "Bash", "tool_input": {"command": "find . -type f"}})
    outs = subprocess.run(f"for i in 1 2 3 4 5 6; do printf '%s' '{payload}' | {HOOKS / 'route'} tool & done; wait",
                          shell=True, capture_output=True, text=True, env={**os.environ, "TMPDIR": TMP}).stdout
    assert outs.count('"deny"') == 1


def test_unwritable_state_never_denies():
    env = {"TMPDIR": "/nonexistent"}
    hook("prompt", sid="s-6", prompt="x", env=env)
    assert bash("find . -type f", sid="s-6", env=env) is None


def test_glob_grep_tools():
    turn("s-3")
    assert hook("tool", sid="s-3", tool_name="Glob", tool_input={"pattern": "*.py"}) is None
    assert hook("tool", sid="s-3", tool_name="Grep", tool_input={"pattern": "x", "path": __file__}) is None
    assert hook("tool", sid="s-3", tool_name="Glob", tool_input={"pattern": "src/**/*.ts"}) == "deny"
    turn("s-3")
    assert hook("tool", sid="s-3", tool_name="Grep", tool_input={"pattern": '"agent_id":'}) == "deny"


def test_subagents_notifications_and_off_switch_are_ignored():
    turn()
    assert bash("find . -type f", agent_id="a1") is None
    assert bash("find . -type f") == "deny"
    hook("prompt", prompt="<task-notification>done</task-notification>")
    assert bash("find . -type f") is None
    turn()
    assert bash("find . -type f", env={"HAIKU_SCRIBE_ROUTE": "off"}) is None


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
    print("ok")
