"""bench/ helpers that cost nothing to run: the citation check and the field audit.
Runnable as `python3 test_bench.py` or via pytest."""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "bench"))
import route_eval  # noqa: E402


def test_cites_flags_missing_files_and_lines_past_eof():
    wd = Path(tempfile.mkdtemp())
    (wd / "pkg").mkdir()
    (wd / "pkg" / "a.py").write_text("x\n" * 10)
    brief = (f"pkg/a.py:3 and a.py:10 (basename) and pkg/a.py:2-4 and {wd}/pkg/a.py:5 are fine; "
             "pkg/a.py:11 is past the end and ghost.py:1 does not exist")
    assert route_eval.cites(brief, wd) == (6, 2)


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


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
    print("ok")
