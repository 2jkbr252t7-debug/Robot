"""compose the review images: Blender render (transparent) on a light background + title + labels with leader lines
(anchors from <shot>_anchors.json).  Label specs in LABELS (Slovak, diacritics)."""
import json, sys, textwrap
from PIL import Image, ImageDraw, ImageFont
F = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"; FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def font(sz, bold=False):
    return ImageFont.truetype(FB if bold else F, sz)


def compose(shot, title, subtitle, labels, out, pad=(0, 0, 0, 0), legend=None, scale_mm=None, crop=None):
    """labels: list of dict(a=anchor key or (x, y) px, t=text, at=(x, y) text box position in output px, col=(r,g,b), w=wrap chars)"""
    im = Image.open(f"img/{shot}.png").convert("RGBA")
    an = json.load(open(f"img/{shot}_anchors.json"))
    if crop:
        im = im.crop(crop)
    l, t, r, b = pad
    W, H = im.size[0] + l + r, im.size[1] + t + b + 110
    bg = Image.new("RGBA", (W, H), (246, 246, 243, 255))
    ox, oy = l - (crop[0] if crop else 0), t + 110 - (crop[1] if crop else 0)
    bg.alpha_composite(im, (l, t + 110))
    d = ImageDraw.Draw(bg)
    d.text((24, 18), title, font=font(30, True), fill=(20, 20, 20))
    d.text((24, 62), subtitle, font=font(17), fill=(70, 70, 70))
    for L in labels:
        a = L["a"]
        p = an["anchors"][a] if isinstance(a, str) else a
        px, py = p[0] + ox, p[1] + oy
        col = L.get("col", (200, 30, 30))
        txt = "\n".join(textwrap.wrap(L["t"], L.get("w", 34)))
        f = font(L.get("sz", 17), L.get("bold", False))
        tx, ty = L["at"]
        bb = d.multiline_textbbox((tx, ty), txt, font=f, spacing=3)
        d.rectangle((bb[0] - 6, bb[1] - 4, bb[2] + 6, bb[3] + 4), fill=(255, 255, 255, 235), outline=col, width=2)
        d.multiline_text((tx, ty), txt, font=f, fill=(15, 15, 15), spacing=3)
        # leader from the nearest box edge point to the anchor
        cx = min(max(px, bb[0] - 6), bb[2] + 6); cy = min(max(py, bb[1] - 4), bb[3] + 4)
        d.line((cx, cy, px, py), fill=col, width=2)
        d.ellipse((px - 5, py - 5, px + 5, py + 5), outline=col, width=3)
    if scale_mm:
        mmpx = an["mm_per_px"]; n = scale_mm / mmpx
        x0, y0 = 30, H - 40
        d.line((x0, y0, x0 + n, y0), fill=(0, 0, 0), width=4); d.line((x0, y0 - 8, x0, y0 + 8), fill=(0, 0, 0), width=3); d.line((x0 + n, y0 - 8, x0 + n, y0 + 8), fill=(0, 0, 0), width=3)
        d.text((x0 + n + 10, y0 - 12), f"{scale_mm} mm", font=font(18), fill=(0, 0, 0))
    if legend:
        f = font(16); y = H - 40 - 24 * len(legend)
        for i, (c, s) in enumerate(legend):
            d.rectangle((W - 420, y + 24 * i, W - 400, y + 24 * i + 16), fill=c); d.text((W - 390, y + 24 * i - 2), s, font=f, fill=(20, 20, 20))
    bg.convert("RGB").save(out)
    print("wrote", out, bg.size)
