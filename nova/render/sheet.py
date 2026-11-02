"""
Sheet composer for NOVA renders (PIL).  Works in either venv (/opt/venv/cad or /opt/venv/bl).

Typical use (from a script):
    from nova.render.sheet import six_view_sheet, matrix_sheet, project
    six_view_sheet("/tmp/x/head", "NOVA / HLAVA", "obrazky/05_hlava.png", footer="...")

Render dirs are produced by nova/render/render.py and contain <view>.png + views.json.
"""
from __future__ import annotations

import json
import math
import os

from PIL import Image, ImageDraw, ImageFont

BG = (243, 243, 241)
CELL = (234, 235, 236)
LINE = (214, 214, 210)
INK = (22, 24, 28)
MUTED = (110, 112, 118)
ACCENT = (20, 170, 200)

FONT_DIR = "/usr/share/fonts/opentype/inter"


def font(size, weight="Bold"):
    for fn in (f"Inter-{weight}.otf", f"InterDisplay-{weight}.otf", "Inter-Regular.otf"):
        p = os.path.join(FONT_DIR, fn)
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)


VIEW_LABELS = {
    "front": "SPREDU",
    "back": "ZOZADU",
    "right": "PRAVÝ BOK  (−X)",
    "left": "ĽAVÝ BOK  (+X)",
    "top": "ZHORA  (predok dole)",
    "bottom": "ZDOLA  (zrkadlovo, predok dole)",
    "iso": "IZOMETRIA",
    "iso_r": "IZOMETRIA",
    "iso_back": "IZOMETRIA ZOZADU",
    "iso_back_l": "IZOMETRIA ZOZADU",
    "hero": "",
}


def load_view(render_dir, view):
    im = Image.open(os.path.join(render_dir, f"{view}.png")).convert("RGBA")
    return im


def load_meta(render_dir):
    p = os.path.join(render_dir, "views.json")
    if os.path.exists(p):
        with open(p) as f:
            return json.load(f)
    return None


def fit(im, w, h):
    s = min(w / im.width, h / im.height)
    return im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS), s


def draw_scale_bar(d, x, y, mm_per_px, length_mm=50, label=None):
    px = length_mm / mm_per_px
    d.line([(x, y), (x + px, y)], fill=INK, width=3)
    for xx in (x, x + px):
        d.line([(xx, y - 7), (xx, y + 7)], fill=INK, width=3)
    if label and len(label) > 12:
        d.text((x + px + 16, y), label, fill=INK, font=font(22, "Medium"), anchor="lm")
    else:
        d.text((x + px / 2, y + 12), label or f"{length_mm} mm", fill=INK, font=font(22, "Medium"), anchor="mt")


def title_block(d, W, title, subtitle=None, right_note=None, y=34, size=78):
    d.text((60, y), title, fill=INK, font=font(size, "Bold"))
    if subtitle:
        d.text((64, y + size + 14), subtitle, fill=MUTED, font=font(28, "Medium"))
    if right_note:
        d.text((W - 60, y + 26), right_note, fill=MUTED, font=font(24, "Medium"), anchor="ra")


def six_view_sheet(render_dir, title, out, views=("front", "back", "right", "left", "top", "bottom"),
                   labels=None, subtitle=None, footer=None, right_note=None, cols=3, cell=(760, 640),
                   scale_bar_mm=50, dims_text=None):
    """Grid of views with labels, shared scale bar (views rendered with a shared ortho scale)."""
    labels = labels or {}
    rows = math.ceil(len(views) / cols)
    head_h = 190 if subtitle else 150
    foot_h = 90
    W = 60 * 2 + cols * cell[0]
    H = head_h + rows * cell[1] + foot_h
    sheet = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(sheet)
    title_block(d, W, title, subtitle, right_note)
    meta = load_meta(render_dir)
    mmpp = None
    for i, v in enumerate(views):
        r, c = divmod(i, cols)
        x0 = 60 + c * cell[0]
        y0 = head_h + r * cell[1]
        d.rectangle([x0, y0, x0 + cell[0], y0 + cell[1]], fill=CELL, outline=LINE, width=2)
        im = load_view(render_dir, v)
        inner_w, inner_h = cell[0] - 40, cell[1] - 90
        imf, s = fit(im, inner_w, inner_h)
        px = x0 + (cell[0] - imf.width) // 2
        py = y0 + 70 + (inner_h - imf.height) // 2
        sheet.paste(imf, (px, py), imf)
        lab = labels.get(v, VIEW_LABELS.get(v, v.upper()))
        d.text((x0 + 26, y0 + 22), lab, fill=INK, font=font(30, "SemiBold"))
        if meta and v in meta["views"] and meta["views"][v].get("mm_per_px"):
            mmpp = meta["views"][v]["mm_per_px"] / s
    if mmpp and scale_bar_mm:
        draw_scale_bar(d, 64, H - foot_h + 22, mmpp, scale_bar_mm)
    if dims_text:
        d.text((W // 2, H - foot_h + 30), dims_text, fill=INK, font=font(26, "Medium"), anchor="mt")
    if footer:
        d.text((W - 60, H - 40), footer, fill=MUTED, font=font(22, "Medium"), anchor="rs")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    sheet.save(out, optimize=True)
    return out


def matrix_sheet(rows, title, out, views=("front", "back", "right", "left", "top", "bottom"), labels=None,
                 cell=(300, 270), subtitle=None, footer=None, label_w=300, scale_bar=None):
    """rows: list of (row_label, render_dir[, row_note]).  One row per part, one column per view."""
    labels = labels or {}
    head_h = 150 + (40 if subtitle else 0)
    col_head = 56
    W = 40 + label_w + len(views) * cell[0] + 40
    H = head_h + col_head + len(rows) * cell[1] + 110
    sheet = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(sheet)
    title_block(d, W, title, subtitle, size=64)
    x_start = 40 + label_w
    mm_per_px = None
    if scale_bar and rows:
        m0 = load_meta(rows[0][1])
        if m0 and views[0] in m0["views"] and m0["views"][views[0]].get("mm_per_px"):
            im0 = Image.open(os.path.join(rows[0][1], f"{views[0]}.png"))
            _, s0 = fit(im0, cell[0] - 24, cell[1] - 24)
            mm_per_px = m0["views"][views[0]]["mm_per_px"] / s0
    for j, v in enumerate(views):
        x0 = x_start + j * cell[0]
        d.rectangle([x0, head_h, x0 + cell[0], head_h + col_head], fill=(232, 232, 229), outline=LINE, width=2)
        hdr = labels.get(v, VIEW_LABELS.get(v, v)).replace("  ", " ")
        hdr = {"ZHORA (predok dole)": "ZHORA", "ZDOLA (zrkadlovo, predok dole)": "ZDOLA (zrkadl.)"}.get(hdr, hdr)
        d.text((x0 + cell[0] / 2, head_h + col_head / 2), hdr, fill=INK, font=font(21, "SemiBold"), anchor="mm")
    for i, row in enumerate(rows):
        lab, rdir = row[0], row[1]
        note = row[2] if len(row) > 2 else None
        y0 = head_h + col_head + i * cell[1]
        d.rectangle([40, y0, W - 40, y0 + cell[1]], fill=CELL, outline=LINE, width=2)
        # wrap label by pixel width
        words = lab.split(" ")
        j_ = 0
        while j_ < len(words) - 1:                      # Slovak typography: no one-letter word at a line end
            if len(words[j_]) == 1 and words[j_].lower() in "szvkouai":
                words[j_:j_ + 2] = [words[j_] + "\u00a0" + words[j_ + 1]]
            j_ += 1
        lines, cur = [], ""
        lf = font(27, "Bold")
        for w in words:
            cand = (cur + " " + w).strip()
            if d.textlength(cand, font=lf) > label_w - 40 and cur:
                lines.append(cur)
                cur = w
            else:
                cur = cand
        lines.append(cur)
        for k, ln in enumerate(lines):
            d.text((58, y0 + 22 + k * 32), ln, fill=INK, font=font(25 if k else 27, "Bold" if k == 0 else "SemiBold"))
        if note:
            for k, nl in enumerate(reversed(note.split("\n"))):
                d.text((58, y0 + cell[1] - 18 - k * 26), nl, fill=MUTED, font=font(20, "Medium"), anchor="ls")
        for j, v in enumerate(views):
            x0 = x_start + j * cell[0]
            d.line([(x0, y0), (x0, y0 + cell[1])], fill=LINE, width=2)
            p = os.path.join(rdir, f"{v}.png")
            if not os.path.exists(p):
                continue
            im = Image.open(p).convert("RGBA")
            imf, _ = fit(im, cell[0] - 24, cell[1] - 24)
            sheet.paste(imf, (x0 + (cell[0] - imf.width) // 2, y0 + (cell[1] - imf.height) // 2), imf)
    if scale_bar and mm_per_px:
        draw_scale_bar(d, 44, H - 58, mm_per_px, scale_bar, label=f"{scale_bar} mm (spoločná mierka všetkých riadkov)")
    if footer:
        d.text((W - 40, H - 30), footer, fill=MUTED, font=font(22, "Medium"), anchor="rs")
    sheet.save(out, optimize=True)
    return out


# ---------------------------------------------------------------------------
# projection of 3D points (mm) to pixel coords of a rendered view (for callouts / dimensions)
# ---------------------------------------------------------------------------

def project(view_meta, p_mm):
    """Return (px, py) pixel coordinates in the rendered image for world point p_mm."""
    M = view_meta["matrix_world"]   # 4x4 camera->world, rows
    res = view_meta["res"]
    loc = [M[0][3], M[1][3], M[2][3]]
    right = [M[0][0], M[1][0], M[2][0]]
    up = [M[0][1], M[1][1], M[2][1]]
    back = [M[0][2], M[1][2], M[2][2]]
    p = [c / 1000.0 for c in p_mm]
    v = [p[i] - loc[i] for i in range(3)]
    x = sum(v[i] * right[i] for i in range(3))
    y = sum(v[i] * up[i] for i in range(3))
    z = -sum(v[i] * back[i] for i in range(3))   # depth in front of camera
    W, H = res
    if view_meta["type"] == "ORTHO":
        s = view_meta["ortho_scale_mm"] / 1000.0
        scale = W / s if W >= H else H / s
        return W / 2 + x * scale, H / 2 - y * scale
    f = view_meta.get("lens", 70)
    sw = view_meta.get("sensor", 36)
    fx = f / sw * (W if W >= H else H)
    return W / 2 + x / z * fx, H / 2 - y / z * fx


def bg_composite(render_png, out_png, bg=BG):
    im = Image.open(render_png).convert("RGBA")
    base = Image.new("RGBA", im.size, bg + (255,))
    base.alpha_composite(im)
    base.convert("RGB").save(out_png)
