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
from PIL import Image, ImageDraw
import numpy as np

ICON = "icon.png"
OG = "og.png"

# og card layout (measured from the existing og.png)
OG_W, OG_H = 1200, 630
BG = (255, 255, 255, 255)   # flat white card colour
CARD_RADIUS = 48            # outer card corner radius
ICON_SIZE = 280             # icon size inside the card
ICON_POS = (460, 135)       # top-left placement (horizontally centred, slightly high)


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


def main():
    # 1) clean the icon in place
    icon = alpha_bleed(Image.open(ICON))
    icon.save(ICON)

    # 2) rebuild og.png
    card = Image.new("RGBA", (OG_W, OG_H), BG)
    card.putalpha(rounded_mask((OG_W, OG_H), CARD_RADIUS))

    icon_s = icon.resize((ICON_SIZE, ICON_SIZE), Image.LANCZOS)
    card.alpha_composite(icon_s, ICON_POS)
    card.save(OG)
    print(f"wrote {ICON} and {OG}")


if __name__ == "__main__":
    main()
