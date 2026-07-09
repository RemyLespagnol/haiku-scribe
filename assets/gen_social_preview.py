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
