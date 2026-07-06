from __future__ import annotations

from haiku_scribe.contracts import GUIDANCE_END, GUIDANCE_START


def insert_or_replace_block(existing: str, block: str) -> str:
    start = existing.find(GUIDANCE_START)
    end = existing.find(GUIDANCE_END)
    if start == -1 or end == -1 or end < start:
        if not existing:
            return block
        if existing.endswith("\n\n"):
            return existing + block
        if existing.endswith("\n"):
            return existing + "\n" + block
        return existing + "\n\n" + block

    end += len(GUIDANCE_END)
    if end < len(existing) and existing[end] == "\n":
        end += 1
    return existing[:start] + block + existing[end:]


def remove_owned_block(existing: str) -> str:
    start = existing.find(GUIDANCE_START)
    end = existing.find(GUIDANCE_END)
    if start == -1 or end == -1 or end < start:
        return existing
    end += len(GUIDANCE_END)
    if end < len(existing) and existing[end] == "\n":
        end += 1
    return existing[:start] + existing[end:]
