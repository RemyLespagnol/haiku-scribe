# Discoverability & Top-of-Fold Pass Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the repo discoverable (GitHub metadata + social preview) and give the README a one-line hook, without touching the shipped plugin.

**Architecture:** Four independent changes — GitHub repo metadata via `gh`, a Pillow-generated social-preview PNG, a one-line README tagline, and untracking a stray `.DS_Store`. Nothing touches `agents/` or `hooks/`, so the shipped plugin is unchanged and `test_contract.py` stays green as a regression guard.

**Tech Stack:** `gh` CLI, Python 3 + Pillow 10.4.0 (already installed), git.

## Global Constraints

- Target repo: `RemyLespagnol/haiku-scribe`.
- Do NOT modify `agents/haiku-scribe.md`, `hooks/hooks.json`, or `.claude-plugin/*` — the shipped surfaces stay untouched.
- `python3 test_contract.py` must pass after every task (no-op guard; it never should have changed).
- Description text (verbatim): `Claude Code plugin: a read-only Haiku subagent that compresses broad context (surveys, logs, transcripts) into a compact brief — sparing your main model's context.`
- Tagline text (verbatim): `Offload broad reading to a cheap Haiku scout — keep your main model's context for thinking.`
- Topics (exactly these 10): `claude-code`, `claude-code-plugin`, `anthropic`, `claude`, `ai-agents`, `subagent`, `context-management`, `llm`, `developer-tools`, `haiku`.
- Social preview image: 1280×640 PNG at `assets/social-preview.png`.

---

### Task 1: GitHub repository metadata

**Files:** none (remote repo settings via `gh`).

**Interfaces:**
- Consumes: nothing.
- Produces: populated `description` and `repositoryTopics` on the remote repo (no local artifact).

- [ ] **Step 1: Verify current state is empty (baseline)**

Run:
```bash
gh repo view RemyLespagnol/haiku-scribe --json description,repositoryTopics,homepageUrl
```
Expected: `{"description":"","repositoryTopics":null,"homepageUrl":""}` (or description empty/absent).

- [ ] **Step 2: Set the description**

Run:
```bash
gh repo edit RemyLespagnol/haiku-scribe \
  --description "Claude Code plugin: a read-only Haiku subagent that compresses broad context (surveys, logs, transcripts) into a compact brief — sparing your main model's context."
```
Expected: no error; prints the repo URL.

- [ ] **Step 3: Set the 10 topics**

Run:
```bash
gh repo edit RemyLespagnol/haiku-scribe \
  --add-topic claude-code \
  --add-topic claude-code-plugin \
  --add-topic anthropic \
  --add-topic claude \
  --add-topic ai-agents \
  --add-topic subagent \
  --add-topic context-management \
  --add-topic llm \
  --add-topic developer-tools \
  --add-topic haiku
```
Expected: no error; prints the repo URL.

- [ ] **Step 4: Verify metadata is populated**

Run:
```bash
gh repo view RemyLespagnol/haiku-scribe --json description,repositoryTopics --jq '{desc: .description, topics: [.repositoryTopics[].name]}'
```
Expected: `desc` is the full description string; `topics` is a 10-element array containing every topic above.

- [ ] **Step 5: Commit**

No local files changed — nothing to commit. Skip.

---

### Task 2: Social preview image

**Files:**
- Create: `assets/gen_social_preview.py` (generator script, kept in repo for regeneration)
- Create: `assets/social-preview.png` (the 1280×640 output)

**Interfaces:**
- Consumes: `assets/logo.png` (existing).
- Produces: `assets/social-preview.png`, 1280×640.

- [ ] **Step 1: Write the generator script**

Create `assets/gen_social_preview.py`:
```python
"""Generate assets/social-preview.png (1280x640) from logo.png + tagline.
Regenerate with: python3 assets/gen_social_preview.py
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).parent
W, H = 1280, 640
BG = (13, 17, 23)        # GitHub dark canvas
FG = (230, 237, 243)     # near-white
MUTED = (139, 148, 158)  # GitHub muted gray
TAGLINE = "Offload broad reading to a cheap Haiku scout —"
TAGLINE2 = "keep your main model's context for thinking."


def load_font(size, bold=False):
    candidates = (
        ["/System/Library/Fonts/SFNS.ttf"]
        + (["/System/Library/Fonts/Supplemental/Arial Bold.ttf"] if bold
           else ["/System/Library/Fonts/Supplemental/Arial.ttf"])
        + ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    )
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def centered(draw, text, y, font, fill):
    box = draw.textbbox((0, 0), text, font=font)
    w = box[2] - box[0]
    draw.text(((W - w) / 2, y), text, font=font, fill=fill)


def main():
    canvas = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(canvas)

    # Logo, scaled to ~200px tall, centered horizontally near the top third.
    logo = Image.open(HERE / "logo.png").convert("RGBA")
    target_h = 200
    scale = target_h / logo.height
    logo = logo.resize((round(logo.width * scale), target_h), Image.LANCZOS)
    canvas.paste(logo, ((W - logo.width) // 2, 90), logo)

    title_font = load_font(64, bold=True)
    tag_font = load_font(34)
    centered(draw, "haiku-scribe", 320, title_font, FG)
    centered(draw, TAGLINE, 420, tag_font, MUTED)
    centered(draw, TAGLINE2, 468, tag_font, MUTED)

    out = HERE / "social-preview.png"
    canvas.save(out)
    print(f"wrote {out} ({W}x{H})")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Generate the image**

Run:
```bash
python3 assets/gen_social_preview.py
```
Expected: prints `wrote .../assets/social-preview.png (1280x640)`.

- [ ] **Step 3: Verify dimensions**

Run:
```bash
python3 -c "from PIL import Image; im=Image.open('assets/social-preview.png'); print(im.size)"
```
Expected: `(1280, 640)`.

- [ ] **Step 4: Eyeball the result**

Open `assets/social-preview.png` and confirm the logo is centered, "haiku-scribe" is legible, and the two tagline lines fit within the frame with margin. If text overflows the 1280px width, reduce `tag_font` size in the script and regenerate.

- [ ] **Step 5: Commit**

```bash
git add assets/gen_social_preview.py assets/social-preview.png
git commit -m "docs: add generated 1280x640 social preview image"
```

---

### Task 3: README top-of-fold tagline

**Files:**
- Modify: `README.md:5-6` (insert tagline after the `# haiku-scribe` H1, before the badges)

**Interfaces:**
- Consumes: nothing.
- Produces: rendered tagline line under the title.

- [ ] **Step 1: Insert the tagline**

In `README.md`, immediately after the line `# haiku-scribe` (line 5) and its following blank line, insert:
```markdown
> _Offload broad reading to a cheap Haiku scout — keep your main model's context for thinking._

```
The result reads: H1, blank line, the blockquote tagline, blank line, then the existing CI/License badges.

- [ ] **Step 2: Verify placement**

Run:
```bash
sed -n '5,10p' README.md
```
Expected: line 5 is `# haiku-scribe`, followed by a blank line, then the `> _Offload broad reading...` blockquote, a blank line, then the `[![CI]...` badge line.

- [ ] **Step 3: Contract test still green**

Run:
```bash
python3 test_contract.py
```
Expected: passes (README isn't part of the contract; this confirms nothing collateral broke).

- [ ] **Step 4: Commit**

```bash
git add README.md
git commit -m "docs: add one-line tagline under README title"
```

---

### Task 4: Untrack stray .DS_Store

**Files:**
- Delete from index only: `assets/.DS_Store` (already listed in `.gitignore:4`, but tracked)

**Interfaces:**
- Consumes: nothing.
- Produces: cleaner `git ls-files` (public repo no longer ships macOS cruft).

- [ ] **Step 1: Confirm it is tracked**

Run:
```bash
git ls-files assets/.DS_Store
```
Expected: prints `assets/.DS_Store` (confirming it's tracked despite the gitignore entry).

- [ ] **Step 2: Untrack it (keep the local file)**

Run:
```bash
git rm --cached assets/.DS_Store
```
Expected: `rm 'assets/.DS_Store'`.

- [ ] **Step 3: Verify it is gone from the index and ignored going forward**

Run:
```bash
git ls-files assets/.DS_Store; git check-ignore assets/.DS_Store
```
Expected: first command prints nothing; second prints `assets/.DS_Store` (confirming `.gitignore:4` covers it — no gitignore edit needed).

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "chore: untrack stray assets/.DS_Store"
```

---

## Manual Hand-off (not automatable)

After Task 2, the social preview PNG exists but GitHub has **no API to upload it**. The user must do this once in the browser:

1. Go to `https://github.com/RemyLespagnol/haiku-scribe/settings`.
2. Scroll to **Social preview**.
3. Click **Edit** → **Upload an image** → choose `assets/social-preview.png`.

Surface this explicitly when reporting completion; do not mark the social-preview work "done" without it.
