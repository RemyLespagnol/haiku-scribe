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


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
    print("ok")
