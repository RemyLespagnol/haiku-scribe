from dataclasses import dataclass, field


@dataclass(frozen=True)
class AgentConfig:
    name: str
    model: str
    tools: tuple[str, ...]
    disallowed_tools: tuple[str, ...]
    max_turns: int = 6
    deny_rules: tuple[str, ...] = field(default_factory=tuple)


def default_agent_config() -> AgentConfig:
    return AgentConfig(
        name="haiku-scribe",
        model="haiku",
        tools=("Read", "Glob", "Grep"),
        disallowed_tools=("Write", "Edit", "Bash", "WebFetch", "WebSearch", "Agent", "mcp__*"),
        deny_rules=("Read(.env)", "Read(.env.*)", "Read(**/*.pem)", "Read(**/*.key)"),
    )


def render_agent_markdown(config: AgentConfig) -> str:
    tools = ", ".join(config.tools)
    disallowed = ", ".join(config.disallowed_tools)
    return f"""---
name: {config.name}
model: {config.model}
tools: {tools}
disallowedTools: {disallowed}
maxTurns: {config.max_turns}
---

## Role

Read repository context and return concise evidence.

## Boundaries

Do not write files, run shell commands, use web tools, use MCP tools, or invoke other agents.
"""
