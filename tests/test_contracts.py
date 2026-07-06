from __future__ import annotations

from haiku_scribe.contracts import GUIDANCE_END, GUIDANCE_START, render_guidance_block


def test_guidance_requires_scribe_before_bulk_exploration() -> None:
    guidance = render_guidance_block()

    assert GUIDANCE_START in guidance
    assert GUIDANCE_END in guidance
    assert "Before broad code exploration, call `haiku-scribe` first." in guidance
    assert "You are about to read 3+ files." in guidance
    assert "Do not read files yourself first" in guidance


def test_guidance_separates_evidence_gathering_from_final_judgment() -> None:
    guidance = render_guidance_block()

    assert "Haiku Scribe gathers compact evidence." in guidance
    assert "Main Claude performs focused direct reads" in guidance
    assert "Main Claude makes final decisions, edits, commits, and user-facing conclusions." in guidance
    assert "These exclusions apply to final judgment, not pre-analysis." in guidance


def test_guidance_uses_codegraph_before_scribe_for_indexed_repositories() -> None:
    guidance = render_guidance_block()

    assert "For indexed repositories, use CodeGraph first for symbol and file discovery." in guidance
    assert "If CodeGraph narrows the work to 2 or fewer direct file reads, continue in the main session." in guidance
    assert "If broad reading remains after CodeGraph, call `haiku-scribe` before direct Read, Grep, or shell exploration." in guidance


def test_guidance_recovers_from_skipped_scribe_gate() -> None:
    guidance = render_guidance_block()

    assert "If you already crossed a mandatory trigger without `haiku-scribe`, stop and call it immediately." in guidance
    assert "Do not ask the user whether to recover." in guidance


def test_guidance_stays_static_and_non_enforcing() -> None:
    guidance = render_guidance_block()

    assert "hooks" not in guidance.lower()
    assert "soft enforcement" not in guidance.lower()
    assert "block direct reads" not in guidance.lower()
