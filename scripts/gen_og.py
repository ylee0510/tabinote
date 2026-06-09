#!/usr/bin/env python3
"""Clean icon.png and regenerate og.png for link previews.

Root cause of the white fringe on the rounded icon corners: icon.png's fully
transparent pixels carried leftover near-white RGB values. Any downscale/resample
of an RGBA image averages those ghost RGB values with neighbouring opaque navy
pixels, producing a bright halo along the edge.

Fix: "alpha-bleed" the icon (extend the nearest opaque colour outward into the
transparent region, leaving alpha untouched) so resampling can never pull in
white. Then composite the cleaned, premultiplied icon onto the navy card.
"""
from PIL import Image, ImageDraw, ImageFont
import numpy as np

ICON = "icon.png"
OG = "og.png"

# og card layout
OG_W, OG_H = 1200, 630
BG = (255, 255, 255, 255)   # flat white card colour
CARD_RADIUS = 48            # outer card corner radius

# brand
NAVY = (45, 62, 90)         # --accent #2d3e5a
MUTED = (120, 113, 108)     # --muted #78716c
FONT_TITLE = ("/System/Library/Fonts/Avenir.ttc", 4)       # Avenir Heavy
FONT_SUB = ("/System/Library/Fonts/Avenir Next.ttc", 5)    # Avenir Next Medium

# left-aligned icon + title block
ICON_SIZE = 300
GAP = 60                    # space between icon and text
TITLE = "Tavy"
SUBTITLE = "TRAVEL MEMO"
TITLE_SIZE = 168
SUB_SIZE = 44
SUB_TRACKING = 10           # extra px between subtitle letters
TITLE_SUB_GAP = 22          # vertical gap between title and subtitle


def alpha_bleed(img: Image.Image) -> Image.Image:
    """Extend edge colours into transparent regions; alpha is preserved."""
    arr = np.array(img.convert("RGBA"))
    rgb = arr[:, :, :3].astype(np.float32)
    known = arr[:, :, 3] > 0
    # iteratively dilate the known region, filling unknown pixels with the
    # mean RGB of their known neighbours
    while not known.all():
        nb_sum = np.zeros_like(rgb)
        nb_cnt = np.zeros(known.shape, np.float32)
        for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1),
                       (-1, -1), (-1, 1), (1, -1), (1, 1)):
            s_rgb = np.roll(np.roll(rgb * known[..., None], dy, 0), dx, 1)
            s_k = np.roll(np.roll(known, dy, 0), dx, 1)
            nb_sum += s_rgb
            nb_cnt += s_k
        fill = (~known) & (nb_cnt > 0)
        if not fill.any():
            break
        rgb[fill] = nb_sum[fill] / nb_cnt[fill, None]
        known |= fill
    out = arr.copy()
    out[:, :, :3] = np.clip(rgb, 0, 255).astype(np.uint8)
    return Image.fromarray(out, "RGBA")


def rounded_mask(size, radius) -> Image.Image:
    """High-res rounded-rectangle mask, downsampled for smooth anti-aliasing."""
    w, h = size
    ss = 4
    m = Image.new("L", (w * ss, h * ss), 0)
    ImageDraw.Draw(m).rounded_rectangle(
        (0, 0, w * ss - 1, h * ss - 1), radius=radius * ss, fill=255)
    return m.resize((w, h), Image.LANCZOS)


def tracked_width(font, text, tracking):
    return sum(font.getbbox(c)[2] for c in text) + tracking * (len(text) - 1)


def draw_tracked(draw, xy, text, font, fill, tracking):
    x, y = xy
    for c in text:
        draw.text((x, y), c, font=font, fill=fill)
        x += font.getbbox(c)[2] + tracking


def main():
    # 1) clean the icon in place
    icon = alpha_bleed(Image.open(ICON))
    icon.save(ICON)

    # 2) rebuild og.png
    card = Image.new("RGBA", (OG_W, OG_H), BG)
    card.putalpha(rounded_mask((OG_W, OG_H), CARD_RADIUS))
    draw = ImageDraw.Draw(card)

    title_font = ImageFont.truetype(FONT_TITLE[0], TITLE_SIZE, index=FONT_TITLE[1])
    sub_font = ImageFont.truetype(FONT_SUB[0], SUB_SIZE, index=FONT_SUB[1])

    # measure text block
    t_box = title_font.getbbox(TITLE)
    t_w, t_h = t_box[2] - t_box[0], t_box[3] - t_box[1]
    s_w = tracked_width(sub_font, SUBTITLE, SUB_TRACKING)
    s_box = sub_font.getbbox(SUBTITLE)
    s_h = s_box[3] - s_box[1]
    text_w = max(t_w, s_w)
    block_h = t_h + TITLE_SUB_GAP + s_h

    # centre the whole [icon | gap | text] group horizontally
    total_w = ICON_SIZE + GAP + text_w
    gx = (OG_W - total_w) // 2

    icon_y = (OG_H - ICON_SIZE) // 2
    icon_s = icon.resize((ICON_SIZE, ICON_SIZE), Image.LANCZOS)
    card.alpha_composite(icon_s, (gx, icon_y))

    text_x = gx + ICON_SIZE + GAP
    block_y = (OG_H - block_h) // 2
    # title (subtract bbox top offset so it sits where we expect)
    draw.text((text_x - t_box[0], block_y - t_box[1]), TITLE, font=title_font, fill=NAVY)
    sub_y = block_y + t_h + TITLE_SUB_GAP
    draw_tracked(draw, (text_x, sub_y - s_box[1]), SUBTITLE, sub_font, MUTED, SUB_TRACKING)

    card.save(OG)
    print(f"wrote {ICON} and {OG}")


if __name__ == "__main__":
    main()
