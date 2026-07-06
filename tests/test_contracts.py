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
    assert "Before loading raw repository context, classify remaining work." in guidance
    assert "Compact discovery tools may be used first" in guidance
    assert "Use main session directly only when remaining work is a small focused read:" in guidance
    assert "Use `haiku-scribe` when remaining work is broad context gathering:" in guidance


def test_guidance_separates_evidence_gathering_from_final_judgment() -> None:
    guidance = render_guidance_block()

    assert "Use `haiku-scribe` when remaining work is broad context gathering:" in guidance
    assert "evidence extraction before broad reasoning." in guidance
    assert "Main Claude performs focused direct reads" in guidance
    assert "Main Claude makes final decisions, edits, commits, user-facing conclusions." in guidance
    assert "These exclusions apply final judgment, not pre-analysis." in guidance


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
    assert "Do not ask user whether recover." in guidance


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
    assert "Skip small focused reads:" in agent
    assert "3 or fewer small files" in agent


def test_agent_tools_remain_read_only() -> None:
    agent = render_agent_markdown()

    assert "tools: Read, Glob, Grep" in agent
    frontmatter = agent.split("---", 2)[1]
    assert "Bash" not in frontmatter
    assert "Agent" not in frontmatter


def test_agent_contract_includes_exploration_budget() -> None:
    agent = render_agent_markdown()

    assert "Target about 12 file reads." in agent
    assert "Stop around 15 file reads unless the main session explicitly named the files to inspect." in agent
