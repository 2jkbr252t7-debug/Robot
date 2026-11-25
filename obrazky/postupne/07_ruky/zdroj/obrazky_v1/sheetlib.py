"""Small Pillow helpers for the v1 arm sheets (Slovak labels; Inter font like nova/render/sheet.py, DejaVu fallback)."""
import os, json, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont

BG = (243, 243, 241)
INK = (22, 24, 28)
MUTED = (110, 112, 118)
ACCENT = (20, 170, 200)
DIM = (200, 70, 40)
FONT_DIR = "/usr/share/fonts/opentype/inter"


def font(size, weight="Bold"):
    for fn in (f"Inter-{weight}.otf", f"InterDisplay-{weight}.otf", "Inter-Regular.otf"):
        p = os.path.join(FONT_DIR, fn)
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)


class Cam:
    def __init__(self, path):
        d = json.load(open(path))
        self.d = d
        self.W, self.H = d["res"]
        self.Mcw = np.array(d["matrix"])
        self.Mwc = np.linalg.inv(self.Mcw)
        self.anchors = d.get("anchors", {})
        self.lines = d.get("lines", {})

    def px(self, p):
        p = np.asarray(p, float)
        q = self.Mwc[:3, :3] @ p + self.Mwc[:3, 3]
        if self.d["type"] == "ORTHO":
            k = self.W / self.d["ortho_scale"]
            return (self.W / 2 + q[0] * k, self.H / 2 - q[1] * k)
        f = self.d["lens"] / self.d["sensor_width"] * self.W
        return (self.W / 2 + f * q[0] / -q[2], self.H / 2 - f * q[1] / -q[2])

    def k(self):
        return self.W / self.d["ortho_scale"]


def feather(im, m=40):
    a = np.array(im.split()[-1], dtype=np.float32)
    h, w = a.shape
    ry = np.clip(np.minimum(np.arange(h), np.arange(h)[::-1]) / m, 0, 1)
    rx = np.clip(np.minimum(np.arange(w), np.arange(w)[::-1]) / m, 0, 1)
    a *= np.outer(ry, rx)
    im.putalpha(Image.fromarray(a.astype(np.uint8)))
    return im


def dashed(d, pts, fill, width=3, dash=12, gap=8):
    pts = [tuple(map(float, p)) for p in pts]
    acc = 0.0; on = True
    for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
        L = math.hypot(x1 - x0, y1 - y0)
        t = 0.0
        while t < L:
            seg = (dash if on else gap) - acc
            t1 = min(L, t + seg)
            if on:
                d.line([(x0 + (x1 - x0) * t / L, y0 + (y1 - y0) * t / L), (x0 + (x1 - x0) * t1 / L, y0 + (y1 - y0) * t1 / L)], fill=fill, width=width)
            acc += t1 - t
            if acc >= (dash if on else gap) - 1e-9:
                acc = 0.0; on = not on
            t = t1


def arrow_head(d, tip, frm, fill, size=13):
    ang = math.atan2(tip[1] - frm[1], tip[0] - frm[0])
    a1, a2 = ang + math.radians(152), ang - math.radians(152)
    d.polygon([tip, (tip[0] + size * math.cos(a1), tip[1] + size * math.sin(a1)), (tip[0] + size * math.cos(a2), tip[1] + size * math.sin(a2))], fill=fill)


def dim_h(d, xa, xb, y, text, fnt, fill=DIM, ext=None, text_above=True, width=3, bg=None):
    """horizontal dimension line between pixel x xa..xb at pixel y; ext = [(x, y_from), ...] extension lines up to y"""
    for (ex, ey) in (ext or []):
        d.line([(ex, ey), (ex, y + (8 if y > ey else -8))], fill=fill, width=2)
    d.line([(xa, y), (xb, y)], fill=fill, width=width)
    arrow_head(d, (xa, y), (xb, y), fill); arrow_head(d, (xb, y), (xa, y), fill)
    w = d.textlength(text, font=fnt)
    tx = (xa + xb) / 2 - w / 2
    ty = y - fnt.size - 8 if text_above else y + 6
    if bg:
        d.rounded_rectangle([tx - 6, ty - 2, tx + w + 6, ty + fnt.size + 6], 5, fill=bg)
    d.text((tx, ty), text, font=fnt, fill=fill)


def dim_v(d, x, ya, yb, text, fnt, fill=DIM, left=True, width=3, bg=None):
    d.line([(x, ya), (x, yb)], fill=fill, width=width)
    arrow_head(d, (x, ya), (x, yb), fill); arrow_head(d, (x, yb), (x, ya), fill)
    w = d.textlength(text, font=fnt)
    tx = x - w - 10 if left else x + 10
    ty = (ya + yb) / 2 - fnt.size / 2
    if bg:
        d.rounded_rectangle([tx - 6, ty - 2, tx + w + 6, ty + fnt.size + 6], 5, fill=bg)
    d.text((tx, ty), text, font=fnt, fill=fill)


# ---------------------------------------------------------------------------------------------- leader labels (sheet_t4 technique)
def _stack(items, IH, LH, gap=18):
    last = -1e9
    for it in items:
        h = LH * (it[2].count("\n") + 1)
        it[4] = max(it[0] - h / 2, last)
        last = it[4] + h + gap
    if items:
        over = items[-1][4] + LH * (items[-1][2].count("\n") + 1) - (IH - 6)
        if over > 0:
            last = 6
            for it in items:
                it[4] = max(it[4] - over, last)
                last = it[4] + LH * (it[2].count("\n") + 1) + gap


def _cross(p1, p2, q1, q2):
    def o(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    return o(p1, p2, q1) * o(p1, p2, q2) < 0 and o(q1, q2, p1) * o(q1, q2, p2) < 0


def place(d, items, side, x_text, colw, yi, IH, ix0, fnt, LH=32, gap=18, color=ACCENT, numbered=False):
    """items: [ay, ax, txt]; label column at x_text (width colw), image top-left at (ix0, yi)"""
    items = [list(it[:3]) + [side, 0.0] for it in items]
    items.sort(key=lambda t: t[0])
    ex = x_text + colw - 8 if side == "L" else x_text + 8
    for _ in range(60):
        _stack(items, IH, LH, gap)
        sw = False
        for i in range(len(items) - 1):
            a, b = items[i], items[i + 1]
            pa, pb = (ex, a[4] + LH / 2), (ex, b[4] + LH / 2)
            if _cross(pa, (ix0 + a[1], a[0] - 0 + 0), pb, (ix0 + b[1], b[0])):
                items[i], items[i + 1] = b, a; sw = True
        if not sw:
            break
    _stack(items, IH, LH, gap)
    for ay, ax, txt, _, ly in items:
        pxx, pyy = ix0 + ax, yi + ay
        lines = txt.split("\n")
        w = max(d.textlength(t, font=fnt) for t in lines)
        tx = x_text + colw - 18 - w if side == "L" else x_text + 18
        d.multiline_text((tx, yi + ly), txt, font=fnt, fill=INK, spacing=LH - fnt.size)
        ey = yi + ly + LH / 2
        d.line([(ex, ey), (pxx, pyy)], fill=color, width=3)
        d.ellipse([pxx - 6, pyy - 6, pxx + 6, pyy + 6], fill=color, outline=(255, 255, 255), width=2)


def badge(d, xy, n, fnt, fill=ACCENT, r=17):
    x, y = xy
    d.ellipse([x - r, y - r, x + r, y + r], fill=fill, outline=(255, 255, 255), width=3)
    t = str(n)
    w = d.textlength(t, font=fnt)
    d.text((x - w / 2, y - fnt.size * 0.62), t, font=fnt, fill=(255, 255, 255))


def crop_alpha(im, pad=10):
    a = np.array(im.split()[-1])
    ys, xs = np.nonzero(a > 8)
    x0, x1, y0, y1 = max(0, xs.min() - pad), min(im.width, xs.max() + pad), max(0, ys.min() - pad), min(im.height, ys.max() + pad)
    return im.crop((x0, y0, x1, y1)), (x0, y0)
