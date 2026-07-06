from __future__ import annotations

from haiku_scribe.contracts import (
    GUIDANCE_END,
    GUIDANCE_START,
    render_agent_markdown,
    render_guidance_block,
)


def test_guidance_classifies_remaining_context_work() -> None:
    guidance = render_guidance_block()

    assert GUIDANCE_START in guidance
    assert GUIDANCE_END in guidance
    assert "Before loading raw repository context, classify the remaining work." in guidance
    assert "Compact discovery tools may be used first" in guidance
    assert "Use the main session directly only when the remaining work is a small focused read:" in guidance
    assert "Use `haiku-scribe` when the remaining work is broad context gathering:" in guidance


def test_guidance_separates_evidence_gathering_from_final_judgment() -> None:
    guidance = render_guidance_block()

    assert "Use `haiku-scribe` when the remaining work is broad context gathering:" in guidance
    assert "evidence extraction before broad reasoning." in guidance
    assert "Main Claude performs focused direct reads" in guidance
    assert "Main Claude makes final decisions, edits, commits, and user-facing conclusions." in guidance
    assert "These exclusions apply to final judgment, not pre-analysis." in guidance


def test_guidance_defines_small_focused_reads_and_broad_context() -> None:
    guidance = render_guidance_block()

    assert "3 or fewer small files;" in guidance
    assert "no directory reads;" in guidance
    assert "no shell search over many files;" in guidance
    assert "4+ files;" in guidance
    assert "architecture review, flow mapping, pattern audit, unfamiliar-area exploration;" in guidance


def test_guidance_recovers_from_skipped_scribe_gate() -> None:
    guidance = render_guidance_block()

    assert "If you already crossed into broad context gathering without `haiku-scribe`, stop and call it immediately." in guidance
    assert "Do not ask the user whether to recover." in guidance


def test_guidance_stays_static_and_non_enforcing() -> None:
    guidance = render_guidance_block()

    assert "hooks" not in guidance.lower()
    assert "soft enforcement" not in guidance.lower()
    assert "block direct reads" not in guidance.lower()


def test_agent_description_carries_context_routing_boundary() -> None:
    agent = render_agent_markdown()

    assert "Use when remaining work is broad context gathering:" in agent
    assert "4+ files, large files, directory/repo survey" in agent
    assert "architecture review, flow mapping, pattern audit" in agent
    assert "Skip for small focused reads:" in agent
    assert "3 or fewer small files" in agent
