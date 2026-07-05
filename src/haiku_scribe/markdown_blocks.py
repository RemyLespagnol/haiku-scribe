from __future__ import annotations

from haiku_scribe.contracts import GUIDANCE_END, GUIDANCE_START


def insert_or_replace_block(existing: str, block: str) -> str:
    without = remove_owned_block(existing).rstrip()
    if without:
        return without + "\n\n" + block.rstrip() + "\n"
    return block.rstrip() + "\n"


def remove_owned_block(existing: str) -> str:
    start = existing.find(GUIDANCE_START)
    end = existing.find(GUIDANCE_END)
    if start == -1 or end == -1 or end < start:
        return existing
    end += len(GUIDANCE_END)
    before = existing[:start].rstrip()
    after = existing[end:].lstrip("\n")
    if before and after:
        return before + "\n\n" + after
    if before:
        return before + "\n"
    return after

