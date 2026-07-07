from __future__ import annotations

from haiku_scribe.contracts import (
    GUIDANCE_END,
    GUIDANCE_START,
    render_agent_markdown,
    render_guidance_block,
)


def test_guidance_classifies_before_raw_context() -> None:
    guidance = render_guidance_block()

    assert GUIDANCE_START in guidance
    assert GUIDANCE_END in guidance
    assert "Before loading raw repository context, classify remaining work." in guidance
    assert "Compact discovery tools may be used first" in guidance


def test_guidance_defines_broad_context_and_anti_double_read() -> None:
    guidance = render_guidance_block()

    assert "Use `haiku-scribe` when remaining work is broad context gathering:" in guidance
    assert "4+ files;" in guidance
    assert "large files;" in guidance
    assert "architecture review, flow mapping, pattern audit, unfamiliar-area exploration;" in guidance
    assert "Avoid the costly double-read pattern" in guidance


def test_guidance_states_anti_double_read_rule() -> None:
    guidance = render_guidance_block()

    assert "If the task needs exact, line-level detail immediately, read directly" in guidance
    assert "do not delegate and then re-read the same raw source." in guidance


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


def test_agent_description_carries_context_routing_boundary_and_cost_caution() -> None:
    agent = render_agent_markdown()

    assert "Use proactively before broad exploration:" in agent
    assert "4+ files, directory or repository surveys, large files, logs, transcripts, generated output" in agent
    assert "Skip for small focused reads (3 or fewer known files)" in agent
    assert "when exact line-level detail is needed immediately" in agent
    assert "Not for edits, final debugging/architecture/security conclusions, or user-facing summaries." in agent


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
    assert "The main session should not need to re-read broad raw context" in agent


def test_guidance_positions_against_builtin_explore() -> None:
    guidance = render_guidance_block()

    assert (
        "Prefer `haiku-scribe` over the built-in Explore agent for bulk digestion and evidence "
        "extraction; use Explore only when the search itself needs parent-model reasoning." in guidance
    )
