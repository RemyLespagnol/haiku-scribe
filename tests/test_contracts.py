from __future__ import annotations

from haiku_scribe.contracts import (
    GUIDANCE_END,
    GUIDANCE_START,
    render_agent_markdown,
    render_guidance_block,
)


def test_guidance_defaults_to_direct_reads() -> None:
    guidance = render_guidance_block()

    assert GUIDANCE_START in guidance
    assert GUIDANCE_END in guidance
    assert "Default: read directly." in guidance
    assert "Compact discovery tools may be used first" in guidance


def test_guidance_requires_both_conditions_to_delegate() -> None:
    guidance = render_guidance_block()

    assert "Delegate to `haiku-scribe` only when both hold:" in guidance
    assert "overflowing or dominating the main context window" in guidance
    assert "structured extraction is enough to finish the task" in guidance
    assert "4+ files;" not in guidance


def test_guidance_states_anti_double_read_rule() -> None:
    guidance = render_guidance_block()

    assert "Anti-double-read rule:" in guidance
    assert "costs more than either option alone" in guidance


def test_guidance_separates_evidence_gathering_from_final_judgment() -> None:
    guidance = render_guidance_block()

    assert "Main Claude performs focused direct reads" in guidance
    assert "These exclusions apply to final judgment, not pre-analysis." in guidance
    assert "Do not delegate:" in guidance
    assert "final debugging root-cause conclusions;" in guidance
    assert "architecture decisions;" in guidance
    assert "security, authentication, authorization, or permission-sensitive conclusions;" in guidance
    assert "precise edits;" in guidance
    assert "PR summaries, commit messages, release notes, or public project outputs." in guidance


def test_guidance_keeps_verification_and_fallback() -> None:
    guidance = render_guidance_block()

    assert "Main Claude verifies important claims with focused direct reads before editing." in guidance
    assert "If `haiku-scribe` is unavailable, say so explicitly and continue manually." in guidance


def test_guidance_stays_static_and_non_enforcing() -> None:
    guidance = render_guidance_block()

    assert "hooks" not in guidance.lower()
    assert "soft enforcement" not in guidance.lower()
    assert "block direct reads" not in guidance.lower()


def test_agent_description_carries_massive_and_substitutable_criteria() -> None:
    agent = render_agent_markdown()

    assert "material is massive enough to risk overflowing or dominating" in agent
    assert "structured extraction is enough to finish the task" in agent
    assert "read directly instead of delegating then re-reading" in agent
    assert "4+ files" not in agent


def test_agent_tools_remain_read_only() -> None:
    agent = render_agent_markdown()

    assert "tools: Read, Glob, Grep" in agent
    frontmatter = agent.split("---", 2)[1]
    assert "Bash" not in frontmatter
    assert "Agent" not in frontmatter


def test_agent_contract_includes_exploration_budget_for_multi_and_single_file() -> None:
    agent = render_agent_markdown()

    assert "Target about 12 file reads." in agent
    assert "Stop around 15 file reads unless the main session explicitly named the files to inspect." in agent
    assert "read it in full across offset/limit slices" in agent


def test_agent_boundaries_match_doctor_checks() -> None:
    agent = render_agent_markdown()

    for fragment in (
        "Browse web.",
        "Edit files.",
        "Write files.",
        "Run shell commands.",
        "Use MCP tools.",
        "Invoke other agents.",
    ):
        assert fragment in agent


def test_agent_response_shape_includes_structured_extraction() -> None:
    agent = render_agent_markdown()

    assert "### Structured Extraction" in agent
    assert "The main session must be able to answer without re-reading the source." in agent
