"""Guard the static agent contract: the product is this file, so the test is
that the file still says what it must. Runnable as `python3 test_contract.py`
or `python -m pytest test_contract.py`."""
from pathlib import Path

AGENT = Path(__file__).parent / "agents" / "haiku-scribe.md"

REQUIRED = [
    "model: haiku",
    "tools: Read, Glob, Grep",
    # routing carrier (description trigger)
    "Use proactively before broad exploration",
    "Skip for small focused reads (3 or fewer known files)",
    # don't-re-read carrier (coverage statement)
    "State coverage explicitly",
    "Never present a sample or partial scan as a total count",
    # read-restraint clause (deny-rule replacement)
    "never open `.env`",
]


def test_agent_contract_has_required_clauses():
    text = AGENT.read_text()
    missing = [c for c in REQUIRED if c not in text]
    assert not missing, f"agent contract missing required clauses: {missing}"


if __name__ == "__main__":
    test_agent_contract_has_required_clauses()
    print("ok")
