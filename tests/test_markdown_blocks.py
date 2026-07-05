from haiku_scribe.contracts import render_guidance_block
from haiku_scribe.markdown_blocks import insert_or_replace_block, remove_owned_block


def test_insert_block_preserves_existing_content():
    updated = insert_or_replace_block("# User notes\n", render_guidance_block())

    assert updated.startswith("# User notes\n")
    assert "<!-- HAIKU_SCRIBE_START -->" in updated
    assert "<!-- HAIKU_SCRIBE_END -->" in updated


def test_insert_block_replaces_existing_owned_block():
    first = insert_or_replace_block("# User notes\n", render_guidance_block())
    second = insert_or_replace_block(first, render_guidance_block())

    assert second.count("<!-- HAIKU_SCRIBE_START -->") == 1
    assert second.count("<!-- HAIKU_SCRIBE_END -->") == 1


def test_insert_block_preserves_surrounding_structure():
    original = "# User notes\n\n" + render_guidance_block() + "\nKeep this.\n"

    updated = insert_or_replace_block(original, render_guidance_block())

    assert updated == original


def test_remove_owned_block_keeps_unrelated_content():
    original = "# User notes\n\n" + render_guidance_block() + "\nKeep this.\n"
    cleaned = remove_owned_block(original)

    assert cleaned == "# User notes\n\n\nKeep this.\n"
    assert "HAIKU_SCRIBE_START" not in cleaned
    assert "HAIKU_SCRIBE_END" not in cleaned
