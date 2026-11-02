"""
Produce the final image set in obrazky/ from the CAD exports in build/.

    /opt/venv/cad/bin/python -m nova.render.make_sheets [--only 01,07] [--quality draft|final]

Rendering is delegated to Blender (nova/render/render.py) in subprocesses; composition uses PIL.
Callout anchors come from an ID pass (flat unique colour per part) so leaders always point at visible pixels.
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)
from nova import spec  # noqa: E402
from nova.render import sheet as S  # noqa: E402

BL = "/opt/venv/bl/bin/python"
RENDER = os.path.join(ROOT, "nova", "render", "render.py")
OUT = os.path.join(ROOT, "obrazky")
TMP = os.environ.get("NOVA_TMP", "/tmp/claude-0/nova_renders")
FOOT = f"NOVA {spec.VERSION} · render z CAD modelu (build123d → Blender Cycles) · rozmery v mm"
EXPO6 = -1.9            # orthographic sheets: a bit darker so white forms read

Q = {
    "draft": dict(res6=(560, 480), resp=(900, 1000), samples=16, cell_res=(360, 320), big=(1100, 900),
                  tall=(700, 1000), sec=(800, 950)),
    "final": dict(res6=(1000, 860), resp=(1700, 1900), samples=64, cell_res=(560, 500), big=(1800, 1500),
                  tall=(1300, 1800), sec=(1300, 1550)),
}
SIX = ["front", "back", "right", "left", "top", "bottom"]
HERO_CAM = {"name": "hero", "loc": [330, -1000, 380], "target": [0, 0, 138], "lens": 95}


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

SECTION_X = 0.0                     # A–A cut plane (x); v8 uses 0.4 to miss the caster-ball poles
RENDER_ONLY = ("H04C", "H04E")      # render-only objects never called out
DEFAULT_DISP_LABEL = '4.3" 800×480, RGB'
EXPR_OVERRIDE = None   # optional fn(g, ey, disp, head, zc) -> (lines, led_title, leds) for other robots


def manifest():
    recs = []
    for fn in sorted(glob.glob(os.path.join(ROOT, "build", "manifest", "*.json"))):
        with open(fn) as f:
            recs.extend(json.load(f))
    return recs


REUSE = False


def render(job, name):
    out = os.path.join(TMP, name)
    if REUSE and os.path.exists(os.path.join(out, "views.json")):
        print(f"  reuse {name}", flush=True)
        return out
    job = {k: v for k, v in job.items() if v is not None}
    job["out"] = out
    t = time.time()
    r = subprocess.run([BL, RENDER, "--job", json.dumps(job)], capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout[-3000:], r.stderr[-3000:])
        raise RuntimeError(f"render {name} failed")
    print(f"  render {name}: {time.time() - t:.0f}s", flush=True)
    return out


def ids(recs, pred):
    return [r["id"] for r in recs if pred(r)]


def meta(rd):
    with open(os.path.join(rd, "views.json")) as f:
        return json.load(f)


def radial_fade(im, cx=0.5, cy=0.5, inner=0.62, outer=0.98):
    """Elliptical alpha falloff (hides floor shadows that would be clipped by the frame)."""
    a = np.array(im.split()[-1]).astype(float)
    h, w = a.shape
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.sqrt(((xx / w - cx) / 0.5) ** 2 + ((yy / h - cy) / 0.5) ** 2)
    f = np.clip((outer - r) / (outer - inner), 0, 1)
    a *= f
    im.putalpha(Image.fromarray(a.astype("uint8")))
    return im


def load(rd, view, fade="radial"):
    im = Image.open(os.path.join(rd, f"{view}.png")).convert("RGBA")
    if fade == "radial":
        im = radial_fade(im)
    return im


def composite(rd, view, bg=S.BG, fade="radial"):
    im = load(rd, view, fade)
    base = Image.new("RGBA", im.size, bg + (255,))
    base.alpha_composite(im)
    return base.convert("RGB")


def alpha_bbox(im, thresh=200):
    a = np.array(im.split()[-1])
    ys, xs = np.where(a >= thresh)
    if len(xs) == 0:
        return (0, 0, im.width, im.height)
    return (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)


def paste_fit(sh, im, box, align="center"):
    """Fit RGBA image into box (x0,y0,x1,y1) and alpha-paste; returns (scale, ox, oy)."""
    x0, y0, x1, y1 = box
    s = min((x1 - x0) / im.width, (y1 - y0) / im.height)
    imr = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
    ox = x0 + ((x1 - x0) - imr.width) // 2
    oy = y0 + ((y1 - y0) - imr.height) // 2 if align == "center" else y0
    sh.paste(imr, (ox, oy), imr)
    return s, ox, oy


def anchors(rd, view, min_px=40):
    """Visible-pixel anchor per part from the ID pass: the part pixel nearest to its visible centroid."""
    m = meta(rd)["views"][view]
    idm = m.get("id_map") or {}
    p = os.path.join(rd, f"{view}_id.png")
    if not idm or not os.path.exists(p):
        return {}
    a = np.array(Image.open(p).convert("RGBA")).astype(int)
    rgb, al = a[..., :3], a[..., 3]
    keys = list(idm.keys())
    cols = np.array([idm[k] for k in keys])                       # (K,3)
    flat = rgb.reshape(-1, 3)
    # nearest id colour per pixel (robust to tone-mapping rounding), reject far matches / background
    best = np.full(flat.shape[0], -1)
    bestd = np.full(flat.shape[0], 1e9)
    for j, c in enumerate(cols):
        dd = np.abs(flat - c).sum(-1)
        better = dd < bestd
        best[better], bestd[better] = j, dd[better]
    lab = np.where((bestd <= 9) & (al.reshape(-1) > 200), best, -1).reshape(rgb.shape[:2])
    out = {}
    for j, pid in enumerate(keys):
        msk = lab == j
        n = int(msk.sum())
        if n < min_px:
            continue
        ys, xs = np.nonzero(msk)
        cx, cy = xs.mean(), ys.mean()
        try:                       # deepest visible pixel (max distance to the mask edge), biased to the centroid
            from scipy.ndimage import distance_transform_edt
            dt = distance_transform_edt(msk)[ys, xs]
            score = dt - 0.02 * np.sqrt((xs - cx) ** 2 + (ys - cy) ** 2)
            k = int(np.argmax(score))
        except Exception:  # noqa: BLE001
            k = int(np.argmin((xs - cx) ** 2 + (ys - cy) ** 2))
        out[pid] = (float(xs[k]), float(ys[k]), n)
    return out


def short_name(name, n=40):
    """Callout text: drop parenthesised details / '= …' and cut on a word boundary with an ellipsis."""
    s = name.split(" (")[0].split(" = ")[0].strip()
    if len(s) <= n:
        return s
    words = s[:n - 1].rsplit(" ", 1)[0].split(" ")
    while len(words) > 1 and (len(words[-1]) <= 1 or words[-1] in ("–", "-", "+", "/")):
        words.pop()                                   # never end on a dangling preposition or dash
    return " ".join(words) + "…"


def new_sheet(W, H, title, subtitle=None, note=None):
    sh = Image.new("RGB", (W, H), S.BG)
    d = ImageDraw.Draw(sh)
    S.title_block(d, W, title, subtitle, note)
    return sh, d


def footer(d, W, H):
    d.text((W - 60, H - 36), FOOT, fill=S.MUTED, font=S.font(22, "Medium"), anchor="rs")


def callouts(d, pts, area, label_fn, split_x, fs=24, gap=50):
    """pts: list of (pid, x, y) in sheet pixels. Labels in two columns (left/right of split_x),
    y close to the anchor, never overlapping; leaders: text -> elbow column -> anchor dot."""
    x0, y0, x1, y1 = area
    f = S.font(fs, "SemiBold")
    left = sorted([p for p in pts if p[1] < split_x], key=lambda p: p[2])
    right = sorted([p for p in pts if p[1] >= split_x], key=lambda p: p[2])

    def distribute(group):
        n = len(group)
        if not n:
            return []
        g = min(gap, (y1 - y0) / n)
        out = []
        for (_, _, y) in group:
            y = min(max(y, (out[-1] + g) if out else y0), y1)
            out.append(y)
        over = out[-1] - y1
        if over > 0:
            out = [y - over for y in out]
        for i in range(n - 2, -1, -1):
            out[i] = min(out[i], out[i + 1] - g)
        if out and out[0] < y0:
            out = [y + (y0 - out[0]) for y in out]
        return out

    for side, group in (("L", left), ("R", right)):
        if not group:
            continue
        lys = distribute(group)
        tws = [d.textlength(label_fn(pid), font=f) for pid, _, _ in group]
        col = max(tws) + 28
        for (pid, px, py), ly, tw in zip(group, lys, tws):
            lx = x0 if side == "L" else x1
            elbow = lx + (col + 26 if side == "L" else -(col + 26))
            start = lx + (tw + 10 if side == "L" else -(tw + 10))
            d.line([(start, ly), (elbow, ly), (px, py)], fill=S.ACCENT, width=2)
            d.ellipse([px - 6, py - 6, px + 6, py + 6], fill=S.ACCENT, outline=(255, 255, 255), width=2)
            d.text((lx, ly), label_fn(pid), fill=S.INK, font=f, anchor="lm" if side == "L" else "rm")


def sheet_pts(anc, keep, scale, ox, oy):
    return [(pid, ox + x * scale, oy + y * scale) for pid, (x, y, n) in anc.items() if pid in keep]


# ---------------------------------------------------------------------------
# dimension lines
# ---------------------------------------------------------------------------
DIM = (30, 120, 170)


def arrow(d, p, direction, size=12, color=DIM):
    x, y = p
    dx, dy = direction
    n = math.hypot(dx, dy) or 1
    dx, dy = dx / n, dy / n
    a = (x - dx * size + dy * size * 0.4, y - dy * size - dx * size * 0.4)
    b = (x - dx * size - dy * size * 0.4, y - dy * size + dx * size * 0.4)
    d.polygon([p, a, b], fill=color)


def dim_h(d, x1, x2, y_feature1, y_feature2, y_line, text, color=DIM, fs=26, box=True):
    """Horizontal dimension between x1 and x2 placed at y_line, extension lines from feature y's."""
    for x, yf in ((x1, y_feature1), (x2, y_feature2)):
        d.line([(x, yf + (6 if y_line > yf else -6)), (x, y_line + (10 if y_line > yf else -10))], fill=color, width=2)
    d.line([(x1, y_line), (x2, y_line)], fill=color, width=2)
    arrow(d, (x1, y_line), (-1, 0), color=color)
    arrow(d, (x2, y_line), (1, 0), color=color)
    font = S.font(fs, "SemiBold")
    tw = d.textlength(text, font=font)
    xm = (x1 + x2) / 2
    if box:
        d.rectangle([xm - tw / 2 - 8, y_line - fs / 2 - 6, xm + tw / 2 + 8, y_line + fs / 2 + 4], fill=S.BG)
    d.text((xm, y_line), text, fill=color, font=font, anchor="mm")


def dim_v(d, y1, y2, x_feature1, x_feature2, x_line, text, color=DIM, fs=26):
    for y, xf in ((y1, x_feature1), (y2, x_feature2)):
        d.line([(xf + (6 if x_line > xf else -6), y), (x_line + (10 if x_line > xf else -10), y)], fill=color, width=2)
    d.line([(x_line, y1), (x_line, y2)], fill=color, width=2)
    arrow(d, (x_line, y1), (0, -1) if y1 < y2 else (0, 1), color=color)
    arrow(d, (x_line, y2), (0, 1) if y1 < y2 else (0, -1), color=color)
    font = S.font(fs, "SemiBold")
    tw = d.textlength(text, font=font)
    ym = (y1 + y2) / 2
    tmp = Image.new("RGBA", (int(tw + 16), fs + 14), S.BG + (255,))
    ImageDraw.Draw(tmp).text((tmp.width / 2, tmp.height / 2), text, fill=color, font=font, anchor="mm")
    tmp = tmp.rotate(90, expand=True)
    return tmp, (int(x_line - tmp.width / 2), int(ym - tmp.height / 2))


# ---------------------------------------------------------------------------
# sheet builders
# ---------------------------------------------------------------------------

def with_internals(recs, parts):
    """Exterior part list + the internal parts of the same subassemblies (they fill vents/holes)."""
    subs = {r["sub"] for r in recs if r["id"] in parts}
    return list(parts) + [r["id"] for r in recs if r.get("internal") and r["sub"] in subs]


def sheet_six(name, title, parts, q, recs, subtitle=None):
    job = dict(res=list(q["res6"]), samples=q["samples"], views=SIX, internal=True, exposure=EXPO6)
    if parts:
        job["parts"] = with_internals(recs, parts)
    rd = render(job, name)
    return S.six_view_sheet(rd, title, os.path.join(OUT, f"{name}.png"), views=tuple(SIX), cols=3,
                            cell=(q["res6"][0], q["res6"][1] + 60), subtitle=subtitle, footer=FOOT)


def union_bbox(recs, pids):
    by = {r["id"]: r for r in recs}
    mn = [min(by[p]["bbox"]["min"][i] for p in pids if p in by) for i in range(3)]
    mx = [max(by[p]["bbox"]["max"][i] for p in pids if p in by) for i in range(3)]
    return mn, mx


def sheet_matrix(name, title, rows, q, recs, subtitle=None):
    """rows: list of (label, [part ids], note). All rows share ONE orthographic scale (+ scale bar)."""
    sizes = []
    for _, pids, _ in rows:
        mn, mx = union_bbox(recs, pids)
        sizes.append([mx[i] - mn[i] for i in range(3)])
    cr = q["cell_res"]
    osc = max(max(s) for s in sizes) * 1.12 * max(cr) / min(cr)   # ortho_scale spans the larger image side

    def one(i_row):
        i, (label, pids, note) = i_row
        rd = render(dict(parts=pids, res=list(q["cell_res"]), samples=max(12, q["samples"] // 2), views=SIX,
                         ortho_scale=osc, shadow=False, internal=True, exposure=EXPO6), f"{name}_{i:02d}")
        sz = sizes[i]
        note2 = (note + "\n" if note else "") + f"{sz[0]:.0f} × {sz[1]:.0f} × {sz[2]:.0f} mm (x × y × z)"
        return (label, rd, note2)
    with ThreadPoolExecutor(max_workers=2) as ex:
        rr = list(ex.map(one, list(enumerate(rows))))
    cw, ch = q["cell_res"][0] * 3 // 5 + 20, q["cell_res"][1] * 3 // 5 + 20
    return S.matrix_sheet(rr, title, os.path.join(OUT, f"{name}.png"), subtitle=subtitle, footer=FOOT,
                          cell=(cw, ch), label_w=360, scale_bar=50 if osc > 120 else 20)


def arm_width(recs):
    by = {r["id"]: r for r in recs}
    if "A01-R" in by and "A01-L" in by:
        return by["A01-L"]["bbox"]["max"][0] - by["A01-R"]["bbox"]["min"][0]
    return spec.OVERALL["w"]


def sheet_hero(q, recs):
    rd = render(dict(res=list(q["resp"]), samples=q["samples"] + 16, lens=70,
                     views=[HERO_CAM, "iso_back", "iso_r"], margin=0.12, floor_z=spec.FLOOR_Z), "00_hero")
    W, H = 3000, 2000
    sh, d = new_sheet(W, H, "NOVA", f"stolový robot-spoločník · {spec.VERSION}")
    hero = load(rd, "hero", fade=None)
    bx = alpha_bbox(hero, 220)
    pw, ph = int(0.30 * (bx[2] - bx[0])), int(0.12 * (bx[3] - bx[1]))
    hero = hero.crop((max(0, bx[0] - pw), max(0, bx[1] - ph), min(hero.width, bx[2] + pw), min(hero.height, bx[3] + ph)))
    paste_fit(sh, radial_fade(hero, inner=0.70), (40, 190, 1760, 1960))
    paste_fit(sh, load(rd, "iso_back"), (1790, 1250, 2380, 1930))
    paste_fit(sh, load(rd, "iso_r"), (2400, 1250, 2980, 1930))
    x0, y = 1820, 230
    facts = [
        ("Rozmery", f"základňa {spec.BASE['w']:.0f} × {spec.BASE['d']:.0f} mm · výška {spec.OVERALL['h']:.0f} mm · šírka cez ruky {arm_width(recs):.0f} mm"),
        ("Pohyb", "5 DOF: telo 360°, hlava ±90° / −20…+30°, ruky −30…+180°"),
        ("Tvár", "4.3\" IPS 800×480 (ESP32-S3 v hlave), tvrdené sklo, kamera"),
        ("Zmysly", "2 mikrofóny v ušiach, ToF + svetlo, dotyk, IMU"),
        ("Svetlo", "LED krúžky v ušiach, pásik na hrudi a základni"),
        ("Mozog", "Raspberry Pi CM5 + 2× ESP32-S3 + RP2040"),
        ("Napájanie", "2× 18650 (25 Wh, vymeniteľné), USB-C PD, ~3 h"),
        ("Materiály", "biely PC/ABS satén, čierny soft-touch, TPU, tvrdené sklo"),
    ]
    for k, (a, b) in enumerate(facts):
        d.text((x0, y + k * 120), a.upper(), fill=S.ACCENT, font=S.font(26, "Bold"))
        d.text((x0, y + k * 120 + 38), b, fill=S.INK, font=S.font(31 if len(b) < 60 else 27, "Medium"))
    footer(d, W, H)
    out = os.path.join(OUT, "00_NOVA_prehlad.png")
    sh.save(out, optimize=True)
    hb = radial_fade(hero.copy(), inner=0.70)
    base = Image.new("RGBA", hb.size, S.BG + (255,))
    base.alpha_composite(hb)
    base.convert("RGB").save(os.path.join(OUT, "00b_NOVA_hero.png"), optimize=True)
    return out


def sil_extent(alpha, y, thresh=128):
    """(xmin, xmax) of the silhouette on image row y (alpha array)."""
    y = int(max(0, min(alpha.shape[0] - 1, y)))
    xs = np.nonzero(alpha[y] >= thresh)[0]
    if len(xs) == 0:
        return None
    return int(xs.min()), int(xs.max())


def sheet_dims(q, recs):
    rd = render(dict(res=[1100, 1500], samples=q["samples"], views=["front", "right"], margin=0.17,
                     floor_z=spec.FLOOR_Z, shadow=False, exposure=EXPO6), "02_dims")
    m = meta(rd)["views"]
    W, H = 3000, 2050
    sh, d = new_sheet(W, H, "NOVA / HLAVNÉ ROZMERY", "pohľad spredu a z pravého boku (−X) · mm · základná póza")
    sc = 1750 / 1500
    panels = {"front": (60, 200), "right": (1560, 200)}
    alphas = {}
    rot = []
    for v, (ox, oy) in panels.items():
        im = Image.open(os.path.join(rd, f"{v}.png")).convert("RGBA")
        im = im.resize((int(im.width * sc), int(im.height * sc)), Image.LANCZOS)
        alphas[v] = np.array(im.split()[-1])
        base = Image.new("RGBA", im.size, S.BG + (255,))
        base.alpha_composite(im)
        sh.paste(base.convert("RGB"), (ox, oy))
        d.text((ox + 10, oy - 6), S.VIEW_LABELS[v], fill=S.INK, font=S.font(30, "SemiBold"))

    def P(view, p):
        px, py = S.project(m[view], p)
        ox, oy = panels[view]
        return ox + px * sc, oy + py * sc

    def edge(view, zmm, side):
        x, y = P(view, (0, 0, zmm))
        ox, oy = panels[view]
        e = sil_extent(alphas[view], y - oy)
        if not e:
            return x, y
        return (ox + (e[0] if side < 0 else e[1])), y

    B, T, Hd = spec.BASE, spec.TORSO, spec.HEAD
    zf = spec.FLOOR_Z
    # ---- FRONT ----
    a = P("front", (-B["w"] / 2, 0, 2)); b = P("front", (B["w"] / 2, 0, 2))
    yfl = P("front", (0, 0, zf))[1]
    dim_h(d, a[0], b[0], a[1], b[1], yfl + 60, f"{B['w']:.0f} (základňa)")
    aw = arm_width(recs)
    by = {r["id"]: r for r in recs}
    zarm = 75
    a = P("front", (by["A01-R"]["bbox"]["min"][0], 0, zarm)) if "A01-R" in by else a
    b = P("front", (by["A01-L"]["bbox"]["max"][0], 0, zarm)) if "A01-L" in by else b
    dim_h(d, a[0], b[0], a[1], b[1], yfl + 130, f"{aw:.0f} (cez ruky)")
    a = P("front", (-Hd["w"] / 2, 0, Hd["z1"] - 25)); b = P("front", (Hd["w"] / 2, 0, Hd["z1"] - 25))
    ytop = P("front", (0, 0, Hd["z1"]))[1]
    dim_h(d, a[0], b[0], a[1], b[1], ytop - 50, f"{Hd['w']:.0f}")
    ear = Hd["w"] / 2 + Hd["ear"]["protrude"]
    a = P("front", (-ear, 0, Hd["ear"]["z"])); b = P("front", (ear, 0, Hd["ear"]["z"]))
    dim_h(d, a[0], b[0], a[1] - 22, b[1] - 22, ytop - 115, f"{2 * ear:.0f} (cez uši)")
    zt = 62
    a = P("front", (-T["w"] / 2, 0, zt)); b = P("front", (T["w"] / 2, 0, zt))
    dim_h(d, a[0] + 2, b[0] - 2, a[1], b[1], a[1], f"{T['w']:.0f} (trup)", fs=24)
    # overall height, left column
    xl = min(edge("front", z, -1)[0] for z in (60, 115, 220)) - 70
    top = P("front", (0, 0, Hd["z1"])); bot = P("front", (0, 0, zf))
    xe_top = edge("front", Hd["z1"] - 1, -1)[0]
    xe_bot = edge("front", zf + 1, -1)[0]
    rot.append(dim_v(d, top[1], bot[1], xe_top, xe_bot, xl, f"{spec.OVERALL['h']:.0f} celková výška"))
    # level marks on the right (dashed from the silhouette edge to the label column)
    cols_ = np.nonzero(alphas["front"].max(axis=0) > 40)[0]
    xr_lab = max(panels["front"][0] + 1100 * sc - 20, panels["front"][0] + (cols_.max() if len(cols_) else 0) + 235)
    for z, lab in [(Hd["z1"], f"z {Hd['z1']:.0f} vrch hlavy"), (spec.TILT_AXIS["z"], f"z {spec.TILT_AXIS['z']:.0f} os náklonu"),
                   (Hd["z0"], f"z {Hd['z0']:.0f} spodok hlavy"), (T["z1"], f"z {T['z1']:.0f} vrch trupu"),
                   (spec.ARM["axis"]["z"], f"z {spec.ARM['axis']['z']:.0f} os ramien"), (B["z1"], f"z {B['z1']:.0f} vrch základne")]:
        x_e, y = edge("front", z, +1)
        for xx in range(int(x_e + 10), int(xr_lab - 210), 14):
            d.line([(xx, y), (min(xx + 7, xr_lab - 210), y)], fill=(150, 150, 150), width=1)
        d.text((xr_lab - 200, y), lab, fill=(70, 72, 78), font=S.font(22, "Medium"), anchor="lm")
    # ---- SIDE (right view: robot front on the image right) ----
    a = P("right", (0, -B["d"] / 2, 2)); b = P("right", (0, B["d"] / 2, 2))
    yfl = P("right", (0, 0, zf))[1]
    dim_h(d, min(a[0], b[0]), max(a[0], b[0]), a[1], b[1], yfl + 60, f"{B['d']:.0f} (základňa)")
    hf = Hd["y0"] - Hd["bezel"]["protrude"]
    a = P("right", (0, hf, Hd["z1"] - 25)); b = P("right", (0, Hd["y1"], Hd["z1"] - 25))
    ytop = P("right", (0, 0, Hd["z1"]))[1]
    dim_h(d, min(a[0], b[0]), max(a[0], b[0]), a[1], b[1], ytop - 50, f"{Hd['y1'] - hf:.0f} (hlava s rámom)")
    a = P("right", (0, -T["d"] / 2, zt)); b = P("right", (0, T["d"] / 2, zt))
    dim_h(d, min(a[0], b[0]) + 2, max(a[0], b[0]) - 2, a[1], b[1], a[1], f"{T['d']:.0f} (trup)", fs=24)
    # vertical chain on the robot's back side (image left)
    xback = min(edge("right", z, -1)[0] for z in (20, 90, 220))
    col1, col2 = xback - 60, xback - 130
    for z0, z1, lab, col in [(0, B["z1"], f"{B['z1']:.0f} (+1.2 nožičky)", col1),
                             (T["z0"], T["z1"], f"{T['z1'] - T['z0']:.0f} trup", col2),
                             (Hd["z0"], Hd["z1"], f"{Hd['h']:.0f} hlava", col1)]:
        p0 = P("right", (0, 0, z0)); p1 = P("right", (0, 0, z1))
        e0 = edge("right", z0 + 0.5, -1)[0]; e1 = edge("right", z1 - 0.5, -1)[0]
        rot.append(dim_v(d, p1[1], p0[1], e1, e0, col, lab, fs=24))
    for img, pos in rot:
        sh.paste(img, pos)
    footer(d, W, H)
    out = os.path.join(OUT, "02_NOVA_rozmery.png")
    sh.save(out, optimize=True)
    return out


def group_explode(recs, lift=75.0):
    """Hierarchical explode: everything above the base lifts by `lift`, then each part's own vector."""
    ov = {}
    for r in recs:
        own = list(r.get("explode", [0, 0, 0]))
        g = 0.0 if r["sub"] == "base" else lift
        if r["id"] == "B05":
            g, own = lift * 0.25, [0, 0, 0]
        if r["id"] == "T04":
            own = [0, 0, -15]
        if r["id"] == "B03":
            own = [0, -40, 0]
        if r["id"] in ("H04", "H04E", "H04C"):
            own = [own[0], own[1] - 25, own[2]]
        ov[r["id"]] = [own[0], own[1], own[2] + g]
    return ov


def sheet_exploded(q, recs):
    ovr = group_explode(recs)
    rd = render(dict(res=list(q["big"]), samples=q["samples"], explode_override=ovr, views=["iso_r"], lens=60,
                     margin=0.03, dist=0.95, shadow=False, id_pass=True), "03_explode")
    W, H = 3200, 2250
    sh, d = new_sheet(W, H, "NOVA / ROZLOŽENÝ POHĽAD",
                      "vonkajšie diely · pohľad spredu sprava (pravá strana robota) · ľavé diely sú zrkadlové (-L)")
    im = load(rd, "iso_r", fade=None)
    bx = alpha_bbox(im, 10)
    pad = 20
    bx = (max(0, bx[0] - pad), max(0, bx[1] - pad), min(im.width, bx[2] + pad), min(im.height, bx[3] + pad))
    imc = im.crop(bx)
    s, ox, oy = paste_fit(sh, imc, (760, 180, W - 760, H - 100))
    by = {r["id"]: r for r in recs}
    anc = anchors(rd, "iso_r", min_px=60)
    keep = {r["id"] for r in recs if not r.get("internal") and r["id"] not in RENDER_ONLY}
    keep = {k for k in keep if not (k.endswith("-L") and k[:-2] + "-R" in anc)}
    pts = [(pid, ox + (x - bx[0]) * s, oy + (y - bx[1]) * s) for pid, (x, y, n) in anc.items() if pid in keep]
    callouts(d, pts, (40, 200, W - 40, H - 120), lambda pid: f"{pid}  {by[pid]['name']}", split_x=ox + imc.width * s / 2)
    footer(d, W, H)
    out = os.path.join(OUT, "03_NOVA_rozlozeny_pohlad.png")
    sh.save(out, optimize=True)
    return out


def draw_cut_inset(d, box):
    """Small top-view key with the section planes A–A (x=0) and B–B (y=6)."""
    x0, y0, x1, y1 = box
    k = min((x1 - x0) / 210, (y1 - y0) / 170)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2 + 8

    def P(x, y):
        return cx + x * k, cy - y * k
    B = spec.BASE
    d.rounded_rectangle([*P(-B["w"] / 2, B["d"] / 2), *P(B["w"] / 2, -B["d"] / 2)], radius=B["plan_r"] * k,
                        outline=(120, 120, 120), width=2)
    a, b = spec.TORSO["w"] / 2, spec.TORSO["d"] / 2
    pts = []
    for i in range(72):
        t = 2 * math.pi * i / 72
        c, s_ = math.cos(t), math.sin(t)
        n = spec.TORSO["n"]
        pts.append(P(a * math.copysign(abs(c) ** (2 / n), c), b * math.copysign(abs(s_) ** (2 / n), s_)))
    d.polygon(pts, outline=(120, 120, 120))
    red = (200, 60, 20)
    ya, yb = B["d"] / 2 + 10, -B["d"] / 2 - 10
    d.line([P(0, ya), P(0, yb)], fill=red, width=3)
    d.line([P(-B["w"] / 2 - 10, 6), P(B["w"] / 2 + 10, 6)], fill=red, width=3)
    f = S.font(22, "Bold")
    for (xx, yy) in ((0, ya), (0, yb)):
        px, py = P(xx, yy)
        arrow(d, (px + 22, py), (1, 0), size=14, color=red)
        d.line([(px, py), (px + 14, py)], fill=red, width=3)
        d.text((px - 8, py), "A", fill=red, font=f, anchor="rm")
    for xx in (-B["w"] / 2 - 10, B["w"] / 2 + 10):
        px, py = P(xx, 6)
        arrow(d, (px, py - 22), (0, -1), size=14, color=red)
        d.line([(px, py), (px, py - 14)], fill=red, width=3)
        d.text((px, py + 10), "B", fill=red, font=f, anchor="mt")
    d.text((x0, y0 - 8), "poloha rezov (zhora, predok dole)", fill=S.MUTED, font=S.font(20, "Medium"), anchor="ls")


def sheet_section(q, recs):
    by = {r["id"]: r for r in recs}
    rdA = render(dict(res=list(q["sec"]), samples=q["samples"], internal=True, views=["left"], id_pass=True,
                      section=dict(axis="x", offset=SECTION_X, keep="neg"), margin=0.06, shadow=False, exposure=EXPO6),
                 "04_sec_x")
    rdB = render(dict(res=list(q["sec"]), samples=q["samples"], internal=True, views=["front"], id_pass=True,
                      section=dict(axis="y", offset=6.0, keep="pos"), margin=0.06, shadow=False, exposure=EXPO6),
                 "04_sec_y")
    W, H = 3700, 2250
    sh, d = new_sheet(W, H, "NOVA / REZY A ZÁSTAVBA",
                      "oranžové plochy = rez vonkajšími krytmi · modrosivé = rez vnútornými dielmi · čísla dielov podľa kusovníka")
    draw_cut_inset(d, (W - 560, 60, W - 80, 330))
    for k, (rd, v, lab, box, side) in enumerate([
            (rdA, "left", "REZ A–A  (x = 0, pohľad z ľavého boku, predok vľavo)", (640, 400, 1780, 2150), "L"),
            (rdB, "front", "REZ B–B  (y = 6, pohľad spredu)", (1900, 400, 3060, 2150), "R")]):
        im = load(rd, v, fade=None)
        bx = alpha_bbox(im, 10)
        bx = (max(0, bx[0] - 20), max(0, bx[1] - 20), min(im.width, bx[2] + 20), min(im.height, bx[3] + 20))
        imc = im.crop(bx)
        s, ox, oy = paste_fit(sh, imc, box)
        d.text((box[0], 350), lab, fill=S.INK, font=S.font(28, "SemiBold"))
        anc = anchors(rd, v, min_px=250)
        top = sorted(anc.items(), key=lambda kv: -kv[1][2])[:26]
        top = [kv for kv in top if not (kv[0].endswith("-R") and kv[0][:-2] + "-L" in anc)] if side == "R" else top
        pts = [(pid, ox + (x - bx[0]) * s, oy + (y - bx[1]) * s) for pid, (x, y, n) in top if pid not in RENDER_ONLY]
        if side == "L":
            callouts(d, pts, (40, 400, box[0] - 20, H - 120), lambda pid: f"{pid} {short_name(by[pid]['name'], 34)}", split_x=1e9, fs=21, gap=44)
        else:
            callouts(d, pts, (box[2] + 20, 400, W - 40, H - 120), lambda pid: f"{pid} {short_name(by[pid]['name'], 34)}", split_x=-1e9, fs=21, gap=44)
    footer(d, W, H)
    out = os.path.join(OUT, "04_NOVA_rezy.png")
    sh.save(out, optimize=True)
    return out


def sheet_xray(q, recs):
    by = {r["id"]: r for r in recs}
    rd = render(dict(res=list(q["tall"]), samples=q["samples"], internal=True, xray=True, xray_alpha=0.05,
                     views=["iso", "iso_back"], lens=70, margin=0.05, shadow=False, id_pass=True), "05_xray")
    W, H = 3500, 2250
    sh, d = new_sheet(W, H, "NOVA / VNÚTRO (RÖNTGEN)", "kryty takmer priehľadné · elektronika a mechanika na svojich miestach")
    ints = {r["id"] for r in recs if r.get("internal")}
    for k, (v, lab, box, side) in enumerate([("iso", "SPREDU ZĽAVA", (640, 260, 1720, 2160), "L"),
                                             ("iso_back", "ZOZADU SPRAVA", (1780, 260, 2860, 2160), "R")]):
        im = load(rd, v, fade=None)
        bx = alpha_bbox(im, 10)
        bx = (max(0, bx[0] - 20), max(0, bx[1] - 20), min(im.width, bx[2] + 20), min(im.height, bx[3] + 20))
        imc = im.crop(bx)
        s, ox, oy = paste_fit(sh, imc, box)
        d.text(((box[0] + box[2]) / 2, 230), lab, fill=S.INK, font=S.font(30, "SemiBold"), anchor="mm")
        anc = anchors(rd, v, min_px=200)
        top = sorted([kv for kv in anc.items() if kv[0] in ints], key=lambda kv: -kv[1][2])[:22]
        pts = [(pid, ox + (x - bx[0]) * s, oy + (y - bx[1]) * s) for pid, (x, y, n) in top]
        if side == "L":
            callouts(d, pts, (40, 280, box[0], H - 120), lambda pid: f"{pid} {short_name(by[pid]['name'], 34)}", split_x=1e9, fs=21, gap=44)
        else:
            callouts(d, pts, (box[2], 280, W - 40, H - 120), lambda pid: f"{pid} {short_name(by[pid]['name'], 34)}", split_x=-1e9, fs=21, gap=44)
    footer(d, W, H)
    out = os.path.join(OUT, "05_NOVA_vnutro.png")
    sh.save(out, optimize=True)
    return out


def sheet_kinematics(q, recs):
    ISO = {"name": "k", "loc": [560, -800, 440], "target": [0, 0, 140], "lens": 62}
    SIDE = {"name": "k", "loc": [-900, 0, 150], "target": [0, 0, 150], "ortho": True, "ortho_scale": 330}
    FRONT = {"name": "k", "loc": [0, -900, 160], "target": [0, 0, 160], "ortho": True, "ortho_scale": 360}
    poses = [
        ("J1  otáčanie tela  +45°  (rozsah 360°)", {"J1": 45}, ISO),
        ("J2  otáčanie hlavy  +60°  (rozsah ±90°)", {"J2": 60}, ISO),
        ("J3  náklon hlavy  +30°  (hore)", {"J3": 30}, SIDE),
        ("J3  náklon hlavy  −20°  (dole)", {"J3": -20}, SIDE),
        ("J4 pravá +90°  ·  J5 ľavá −30°", {"J4": 90, "J5": -30}, ISO),
        ("J4/J5  obe ruky hore  +170°  (len pri hlave rovno)", {"J4": 170, "J5": 170}, FRONT),
    ]
    res = [760, 820]
    jobs = [(f"06_kin_{k}", dict(res=res, samples=max(16, q["samples"] // 2), pose=pose, views=[cam], shadow=False))
            for k, (_, pose, cam) in enumerate(poses)]
    for nm, cam in (("06_ghost_iso", ISO), ("06_ghost_side", SIDE), ("06_ghost_front", FRONT)):
        jobs.append((nm, dict(res=res, samples=12, views=[cam], shadow=False)))
    with ThreadPoolExecutor(max_workers=2) as ex:
        rds = dict(zip([j[0] for j in jobs], ex.map(lambda j: render(j[1], j[0]), jobs)))
    W, H = 60 * 2 + 3 * 900, 200 + 2 * 1000 + 80
    sh, d = new_sheet(W, H, "NOVA / KINEMATIKA – 5 STUPŇOV VOĽNOSTI",
                      "svetlý obrys = základná póza · J1 BLDC v základni · J2–J5 serial-bus servá so spätnou väzbou polohy")
    for k, (lab, pose, cam) in enumerate(poses):
        r_, c = divmod(k, 3)
        x0, y0 = 60 + c * 900, 200 + r_ * 1000
        d.rectangle([x0, y0, x0 + 900, y0 + 1000], fill=S.CELL, outline=S.LINE, width=2)
        gname = {id(ISO): "06_ghost_iso", id(SIDE): "06_ghost_side", id(FRONT): "06_ghost_front"}[id(cam)]
        ghost = Image.open(os.path.join(rds[gname], "k.png")).convert("RGBA")
        ga = np.array(ghost.split()[-1]).astype(float) * 0.22
        ghost.putalpha(Image.fromarray(ga.astype("uint8")))
        im = Image.open(os.path.join(rds[f"06_kin_{k}"], "k.png")).convert("RGBA")
        canvas = Image.new("RGBA", im.size, (0, 0, 0, 0))
        canvas.alpha_composite(ghost)
        canvas.alpha_composite(im)
        paste_fit(sh, canvas, (x0 + 20, y0 + 80, x0 + 880, y0 + 990))
        d.text((x0 + 24, y0 + 24), lab, fill=S.INK, font=S.font(27, "SemiBold"))
    footer(d, W, H)
    out = os.path.join(OUT, "06_NOVA_kinematika.png")
    sh.save(out, optimize=True)
    return out


def sheet_arm_explode(q, recs):
    side = "R"
    by = {r["id"]: r for r in recs}
    pids = [r["id"] for r in recs if r["id"].endswith("-" + side) and r["id"][0] == "A"]
    ovr = {"A01-R": [-150, 0, 0], "A02-R": [-95, 0, 0], "A03-R": [-95, 0, -45], "A04-R": [-48, 0, 0],
           "A05-R": [-12, 0, 0], "A06-R": [-30, 0, 0]}
    cam = {"name": "ex", "loc": [-260, -720, 300], "target": [-140, 0, 100], "lens": 85}
    rd = render(dict(parts=pids, internal=True, res=[1600, 1000], samples=q["samples"], explode_override=ovr,
                     views=[cam], shadow=False, id_pass=True), "16_arm_ex")
    W, H = 2900, 1500
    sh, d = new_sheet(W, H, "NOVA / RUKA A RAMENO – SKLADANIE",
                      "pravá ruka (ľavá zrkadlovo) · os ramena y = 0, z = 115 · servo v trupe, unášač A06 so spojkou nesie ruku")
    im = load(rd, "ex", fade=None)
    bx = alpha_bbox(im, 10)
    bx = (max(0, bx[0] - 60), max(0, bx[1] - 40), min(im.width, bx[2] + 60), min(im.height, bx[3] + 40))
    imc = im.crop(bx)
    s, ox, oy = paste_fit(sh, imc, (560, 200, W - 560, H - 110))
    # dash-dot shoulder axis through the exploded parts
    m = meta(rd)["views"]["ex"]
    p_a = S.project(m, (-30, 0, 115)); p_b = S.project(m, (-260, 0, 115))
    A = (ox + (p_a[0] - bx[0]) * s, oy + (p_a[1] - bx[1]) * s)
    Bp = (ox + (p_b[0] - bx[0]) * s, oy + (p_b[1] - bx[1]) * s)
    n = 40
    for i in range(n):
        if i % 3 == 2:
            continue
        t0, t1 = i / n, (i + 0.8) / n
        d.line([(A[0] + (Bp[0] - A[0]) * t0, A[1] + (Bp[1] - A[1]) * t0),
                (A[0] + (Bp[0] - A[0]) * t1, A[1] + (Bp[1] - A[1]) * t1)], fill=(200, 60, 20), width=2)
    anc = anchors(rd, "ex", min_px=40)
    pts = [(pid, ox + (x - bx[0]) * s, oy + (y - bx[1]) * s) for pid, (x, y, nn) in anc.items()]
    callouts(d, pts, (40, 230, W - 40, H - 130), lambda pid: f"{pid}  {by[pid]['name']}", split_x=ox + imc.width * s / 2, gap=58)
    footer(d, W, H)
    out = os.path.join(OUT, "16_NOVA_ruka_skladanie.png")
    sh.save(out, optimize=True)
    return out


def sheet_compare(q, recs):
    rd = os.path.join(TMP, "00_hero")
    if not os.path.exists(os.path.join(rd, "hero.png")):
        sheet_hero(q, recs)
    ref = Image.open(os.path.join(ROOT, "referencie", "R01_celok_zadanie.png")).convert("RGB")
    ref = ref.crop((20, 560, 1300, 2330))
    ren = load(rd, "hero", fade=None)
    bx = alpha_bbox(ren, 220)
    pad = int(0.04 * (bx[3] - bx[1]))
    ren = ren.crop((max(0, bx[0] - pad), max(0, bx[1] - pad), min(ren.width, bx[2] + pad), min(ren.height, bx[3] + pad)))
    bg = Image.new("RGBA", ren.size, (205, 205, 203, 255))
    bg.alpha_composite(ren)
    ren = bg.convert("RGB")
    h = 1250
    a = ref.resize((int(ref.width * h / ref.height), h), Image.LANCZOS)
    b = ren.resize((int(ren.width * h / ren.height), h), Image.LANCZOS)
    W, H = 60 + a.width + 60 + b.width + 60, 230 + h + 90
    sh, d = new_sheet(W, H, f"NOVA / ZADANIE vs. {spec.VERSION}",
                      "podobný uhol kamery · biely PC/ABS satén, čierny soft-touch, tyrkysové LED")
    sh.paste(a, (60, 230))
    sh.paste(b, (60 + a.width + 60, 230))
    d.text((60, 205), "OBRÁZOK ZO ZADANIA", fill=S.MUTED, font=S.font(28, "SemiBold"), anchor="ls")
    d.text((60 + a.width + 60, 205), f"NOVA {spec.VERSION} – RENDER Z CAD MODELU", fill=S.MUTED, font=S.font(28, "SemiBold"), anchor="ls")
    footer(d, W, H)
    out = os.path.join(OUT, "21_NOVA_porovnanie_so_zadanim.png")
    sh.save(out, optimize=True)
    return out


def sheet_internals(q, recs):
    """Internal mechanics & electronics without the shells + callouts + BOM table."""
    ints = [r for r in recs if r.get("internal")]
    by = {r["id"]: r for r in recs}
    rd = render(dict(parts=[r["id"] for r in ints], internal=True, res=list(q["tall"]), samples=q["samples"],
                     views=["iso"], lens=70, margin=0.04, shadow=False, id_pass=True), "19_internals")
    W, H = 3700, 2300
    sh, d = new_sheet(W, H, "NOVA / VNÚTORNÁ MECHANIKA A ELEKTRONIKA",
                      "bez krytov · čísla dielov podľa docs/REVIEW_NOTES.md · E = elektronika, M = ložiská a kovové diely, W = káble")
    im = load(rd, "iso", fade=None)
    bx = alpha_bbox(im, 10)
    bx = (max(0, bx[0] - 30), max(0, bx[1] - 30), min(im.width, bx[2] + 30), min(im.height, bx[3] + 30))
    imc = im.crop(bx)
    s, ox, oy = paste_fit(sh, imc, (760, 190, 1960, 2200))
    anc = anchors(rd, "iso", min_px=120)
    pts = [(pid, ox + (x - bx[0]) * s, oy + (y - bx[1]) * s) for pid, (x, y, n) in anc.items()]
    callouts(d, pts, (40, 210, 2660, H - 120), lambda pid: f"{pid}  {by[pid]['name'][:34]}",
             split_x=ox + imc.width * s / 2, fs=22, gap=46)
    tx, ty = 2720, 210
    d.text((tx, ty), "KUSOVNÍK – VNÚTRO", fill=S.ACCENT, font=S.font(28, "Bold"))
    ty += 50
    groups = [("HLAVA", ("head",)), ("KRK", ("neck",)), ("TRUP", ("torso",)), ("RUKY", ("arm_R", "arm_L")), ("ZÁKLADŇA", ("base",))]
    f = S.font(20, "Medium")
    for lab, subs in groups:
        rows = [r for r in ints if r["sub"] in subs]
        if not rows:
            continue
        d.text((tx, ty), lab, fill=S.INK, font=S.font(22, "Bold"))
        ty += 32
        for r in rows:
            d.text((tx + 10, ty), r["id"], fill=S.INK, font=S.font(20, "SemiBold"))
            nm = r["name"] if len(r["name"]) <= 44 else r["name"][:43] + "…"
            d.text((tx + 110, ty), nm, fill=(60, 62, 68), font=f)
            ty += 27
        ty += 8
    footer(d, W, H)
    out = os.path.join(OUT, "19_NOVA_vnutorna_elektronika.png")
    sh.save(out, optimize=True)
    return out


def sheet_expressions(q, recs):
    """2D sheet: screen layout (true scale) and the expression set drawn on the 4.3" display."""
    Hd = spec.HEAD
    g, ey, disp = Hd["glass"], Hd["eyes"], Hd["display"]
    k = 7.0                      # px per mm
    cw, ch = int(g["w"] * k) + 60, int(g["h"] * k) + 120
    exprs = ["Neutrálny", "Šťastný", "Žmurknutie", "Prekvapený", "Ospalý", "Zvedavý", "Smutný", "Nahnevaný",
             "Počúvam", "Láska"]
    cols = 5
    rows = math.ceil(len(exprs) / cols)
    W, H = 60 * 2 + cols * cw, 260 + int(spec.HEAD["glass"]["h"] * 9.0) + 180 + rows * ch + 80
    sh, d = new_sheet(W, H, "NOVA / DISPLEJ A VÝRAZY",
                      f"sklo {g['w']:g}×{g['h']:g} R{g['r']:g} · aktívna plocha {disp['active'][0]:g}×{disp['active'][1]:g} "
                      f"({disp.get('label', DEFAULT_DISP_LABEL)}) · oči {ey['w']:g}×{ey['h']:g} R{ey['r']:g}")
    eye_col = (255, 222, 172)
    zc = g.get("zc", Hd["zc"])            # drawing reference = glass centre

    def glass(x0, y0, kk):
        w, h = g["w"] * kk, g["h"] * kk
        d.rounded_rectangle([x0, y0, x0 + w, y0 + h], radius=g["r"] * kk, fill=(12, 12, 14))
        # visible (unprinted) window: 4 mm print border, 9 mm at the top
        pb, pt = g["print_border"] * kk, g.get("print_top", g["print_border"]) * kk
        ps = g.get("print_side", g["print_border"]) * kk
        d.rounded_rectangle([x0 + ps, y0 + pt, x0 + w - ps, y0 + h - pb], radius=max(1, (g["r"] - g["print_border"]) * kk),
                            outline=(48, 50, 56), width=max(1, int(kk / 4)))
        b = g["print_border"] * kk
        aw, ah = disp["active"][0] * kk, disp["active"][1] * kk
        acx, acy = x0 + w / 2, y0 + h / 2 + (zc - disp["zc"]) * kk
        return acx, acy

    def cam(x0, y0, kk):
        if Hd["camera"].get("hidden"):       # camera behind the mask (not visible from outside)
            return
        cx = x0 + g["w"] * kk / 2
        cy = y0 + (g["h"] / 2 - (Hd["camera"]["z"] - zc)) * kk
        r = Hd["camera"]["hole_d"] / 2 * kk
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(30, 40, 70))

    def pill(cx, cy, w, h, kk, squash=1.0):
        h2 = h * squash
        d.rounded_rectangle([cx - w * kk / 2, cy - h2 * kk / 2, cx + w * kk / 2, cy + h2 * kk / 2],
                            radius=min(w, h2) * kk / 2, fill=eye_col)

    def draw_expr(name, acx, acy, kk):
        ex, ez = ey["x"], (ey["z"] - disp["zc"])
        for sgn in (-1, 1):
            cx, cy = acx + sgn * ex * kk, acy - ez * kk
            w, h = ey["w"], ey["h"]
            if name == "Neutrálny":
                pill(cx, cy, w, h, kk)
            elif name == "Šťastný":
                d.arc([cx - w * kk * 0.7, cy - h * kk * 0.25, cx + w * kk * 0.7, cy + h * kk * 0.55], 200, 340,
                      fill=eye_col, width=int(3.2 * kk))
            elif name == "Žmurknutie":
                if sgn < 0:
                    pill(cx, cy, w, h, kk)
                else:
                    d.rounded_rectangle([cx - w * kk * 0.6, cy - 1.6 * kk, cx + w * kk * 0.6, cy + 1.6 * kk],
                                        radius=1.6 * kk, fill=eye_col)
            elif name == "Prekvapený":
                r = 8.5 * kk
                d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=eye_col)
            elif name == "Ospalý":
                pill(cx, cy, w, h, kk)
                d.rectangle([cx - w * kk, cy - h * kk, cx + w * kk, cy + 1.5 * kk], fill=(12, 12, 14))
            elif name == "Zvedavý":
                pill(cx + 3 * kk, cy - (2 * kk if sgn > 0 else -1 * kk), w, h, kk, 1.15 if sgn > 0 else 0.8)
            elif name in ("Smutný", "Nahnevaný"):
                pill(cx, cy, w, h, kk)
                outer_high = (name == "Nahnevaný")
                # eyelid polygon (glass colour) cutting the top of the pill at a slant
                hi, lo = cy - h * kk * 0.62, cy - h * kk * 0.05
                yl = hi if (sgn < 0) == outer_high else lo
                yr = lo if (sgn < 0) == outer_high else hi
                d.polygon([(cx - w * kk, yl - 0.4 * w * kk), (cx + w * kk, yr - 0.4 * w * kk), (cx + w * kk, cy - h * kk),
                           (cx - w * kk, cy - h * kk)], fill=(12, 12, 14))
                d.polygon([(cx - w * kk, cy - h * kk), (cx + w * kk, cy - h * kk), (cx + w * kk, yr), (cx - w * kk, yl)],
                          fill=(12, 12, 14))
            elif name == "Počúvam":
                pill(cx, cy, w, h * 0.85, kk)
            elif name == "Láska":
                r = 4.2 * kk
                d.ellipse([cx - 2 * r + r * 0.15, cy - r * 1.2, cx + r * 0.15, cy + r * 0.8], fill=(255, 120, 150))
                d.ellipse([cx - r * 0.15, cy - r * 1.2, cx + 2 * r - r * 0.15, cy + r * 0.8], fill=(255, 120, 150))
                d.polygon([(cx - 2 * r + r * 0.3, cy), (cx + 2 * r - r * 0.3, cy), (cx, cy + 2.2 * r)], fill=(255, 120, 150))
        if name == "Počúvam":
            for i, hh in enumerate([3, 6, 9, 6, 3]):
                xx = acx + (i - 2) * 3.2 * kk
                d.rounded_rectangle([xx - 0.9 * kk, acy + 18 * kk - hh * kk / 2, xx + 0.9 * kk, acy + 18 * kk + hh * kk / 2],
                                    radius=0.9 * kk, fill=(70, 230, 250))

    # big dimensioned screen
    kk = 9.0
    gx, gy = 140, 260
    acx, acy = glass(gx, gy, kk)
    cam(gx, gy, kk)
    aw, ah = disp["active"][0] * kk, disp["active"][1] * kk
    d.rectangle([acx - aw / 2, acy - ah / 2, acx + aw / 2, acy + ah / 2], outline=(60, 70, 80), width=2)
    draw_expr("Neutrálny", acx, acy, kk)
    gw, gh = g["w"] * kk, g["h"] * kk
    dim_h(d, gx, gx + gw, gy + gh, gy + gh, gy + gh + 50, f"sklo {g['w']:g}")
    dim_h(d, acx - aw / 2, acx + aw / 2, acy + ah / 2, acy + ah / 2, gy + gh + 110, f"aktívna plocha {disp['active'][0]:.2f}")
    exx = ey["x"] * kk
    # eye spacing: label above a short dimension line (no background box hiding the line)
    yl = gy - 40
    for xx in (acx - exx, acx + exx):
        d.line([(xx, acy - (ey["h"] / 2) * kk - 8), (xx, yl - 10)], fill=DIM, width=2)
    d.line([(acx - exx, yl), (acx + exx, yl)], fill=DIM, width=2)
    arrow(d, (acx - exx, yl), (-1, 0)); arrow(d, (acx + exx, yl), (1, 0))
    d.text((acx, yl - 22), f"rozostup očí {2 * ey['x']:g}", fill=DIM, font=S.font(26, "SemiBold"), anchor="mm")
    # vertical dims: glass height, top print band, eye height
    dims_ = [dim_v(d, gy, gy + gh, gx, gx, gx - 60, f"sklo {g['h']:g}")]
    if g.get("print_dim", True):
        dims_.append(dim_v(d, gy, gy + g.get("print_top", 4) * kk, gx + gw, gx + gw, gx + gw + 50, f"potlač {g.get('print_top', 4):g}"))
    for img_, pos_ in dims_:
        sh.paste(img_, pos_)
    tx = gx + gw + 120
    lines = [
        ("Sklo", f"{g['w']:g} × {g['h']:g} mm, R{g['r']:g}, hr. {g['t']} mm, tvrdené; potlač {g['print_border']:g} mm, hore {g.get('print_top', 4):g} mm"),
        ("Displej", f"4.3\" IPS 800×480, paralelné RGB (ESP32-S3 v hlave), obrys {disp['outline'][0]:g}×{disp['outline'][1]:g} mm, stred z={disp['zc']:g}"),
        ("Kamera", f"nepotlačené okienko Ø{Hd['camera']['hole_d']:g} v hornom páse (z={Hd['camera']['z']:g}), USB modul 8.5×8.5 mm"),
        ("Oči", f"{ey['w']:g}×{ey['h']:g} mm R{ey['r']:g}, stredy x=±{ey['x']:g}, z={ey['z']:g} ({zc - ey['z']:g} mm pod stredom skla)"),
        ("Farba očí", "teplá biela #FFDEAC; animácie 60 fps, žmurknutie každých 3–8 s"),
        ("Rozlíšenie", f"{800 / disp['active'][0]:.1f} px/mm → oko ≈ {ey['w'] * 800 / disp['active'][0]:.0f}×{ey['h'] * 800 / disp['active'][0]:.0f} px"),
    ]
    led_title = "LED SIGNALIZÁCIA (uši H06 · hruď T05 · základňa B03)"
    leds = None
    if EXPR_OVERRIDE is not None:          # robot-specific texts (e.g. NOVA mini v8)
        lines, led_title, leds = EXPR_OVERRIDE(g, ey, disp, Hd, zc)
    for i, (a_, b_) in enumerate(lines):
        d.text((tx, 280 + i * 118), a_.upper(), fill=S.ACCENT, font=S.font(28, "Bold"))
        d.text((tx, 280 + i * 118 + 38), b_, fill=S.INK, font=S.font(34, "Medium"))
    # LED signalling palette
    lx0 = tx + 1500
    d.text((lx0, 280), led_title, fill=S.ACCENT, font=S.font(24, "Bold"))
    leds = leds or [((60, 230, 250), "tyrkysová svieti", "pokoj / pripravený"),
            ((60, 140, 255), "modrá pulzuje", "počúva (hlas)"),
            ((170, 90, 255), "fialová beží dookola", "premýšľa / AI"),
            ((60, 220, 120), "zelená dýcha", "nabíja sa"),
            ((255, 160, 40), "oranžová bliká", "slabá batéria < 15 %"),
            ((255, 60, 60), "červená bliká", "chyba / zablokované servo"),
            ((245, 245, 245), "biela – krátky záblesk", "dotyk temena / ucha")]
    for i, (col, a_, b_) in enumerate(leds):
        yy = 340 + i * 82
        d.ellipse([lx0, yy, lx0 + 46, yy + 46], fill=col, outline=(150, 150, 150), width=2)
        d.ellipse([lx0 + 12, yy + 12, lx0 + 34, yy + 34], fill=S.BG)
        d.text((lx0 + 70, yy + 2), a_, fill=S.INK, font=S.font(28, "SemiBold"))
        d.text((lx0 + 70, yy + 36), b_, fill=S.MUTED, font=S.font(24, "Medium"))
    # expression grid
    y_base = gy + gh + 180
    for i, name in enumerate(exprs):
        r, c = divmod(i, cols)
        x0, y0 = 60 + c * cw, y_base + r * ch
        d.rectangle([x0, y0, x0 + cw, y0 + ch], fill=S.CELL, outline=S.LINE, width=2)
        gx2, gy2 = x0 + 30, y0 + 70
        acx2, acy2 = glass(gx2, gy2, k)
        cam(gx2, gy2, k)
        draw_expr(name, acx2, acy2, k)
        d.text((x0 + 26, y0 + 22), name.upper(), fill=S.INK, font=S.font(28, "SemiBold"))
    footer(d, W, H)
    out = os.path.join(OUT, "20_NOVA_displej_vyrazy.png")
    sh.save(out, optimize=True)
    return out




# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ap.add_argument("--quality", default="draft")
    ap.add_argument("--reuse", action="store_true", help="reuse existing renders in TMP (recompose only)")
    a = ap.parse_args()
    global REUSE
    REUSE = a.reuse
    q = Q[a.quality]
    only = set(x for x in a.only.split(",") if x)
    recs = manifest()
    os.makedirs(OUT, exist_ok=True)
    have = {r["sub"] for r in recs}
    has_int = any(r.get("internal") for r in recs)
    H, N, T, A, B = spec.HEAD, spec.NECK, spec.TORSO, spec.ARM, spec.BASE

    def want(k):
        return not only or k in only

    def P(pred):
        return ids(recs, pred)

    ext = lambda sub: P(lambda r: r["sub"] == sub and not r.get("internal"))
    tasks = []
    if want("00"):
        tasks.append(lambda: sheet_hero(q, recs))
    if want("01"):
        tasks.append(lambda: sheet_six("01_NOVA_celok_6_pohladov", "NOVA / CELOK", None, q, recs,
                                       subtitle=f"výška {spec.OVERALL['h']:.0f} mm · základňa {B['w']:.0f}×{B['d']:.0f} mm · šírka cez ruky {arm_width(recs):.0f} mm · 5 stupňov voľnosti"))
    if want("02"):
        tasks.append(lambda: sheet_dims(q, recs))
    if want("03"):
        tasks.append(lambda: sheet_exploded(q, recs))
    if want("04") and has_int:
        tasks.append(lambda: sheet_section(q, recs))
    if want("05") and has_int:
        tasks.append(lambda: sheet_xray(q, recs))
    if want("06"):
        tasks.append(lambda: sheet_kinematics(q, recs))
    if want("07") and "head" in have:
        tasks.append(lambda: sheet_six("07_NOVA_hlava", "NOVA / HLAVA", ext("head"), q, recs,
                                       subtitle=f"H01–H06 · {H['w']:.0f} ({H['w'] + 2 * H['ear']['protrude']:.0f} cez uši) × {H['y1'] - H['y0'] + H['bezel']['protrude']:.0f} × {H['h']:.0f} mm (š × h × v) · z {H['z0']:.0f}–{H['z1']:.0f}"))
    if want("08") and "head" in have:
        tasks.append(lambda: sheet_matrix("08_NOVA_kryty_hlavy", "NOVA / DIELY HLAVY", [
            ("H01 Hlavný obal", ["H01"], "biely PC/ABS satén"),
            ("H02 Zadný kryt", ["H02"], "biely PC/ABS satén"),
            ("H03 Predný rám", ["H03"], "čierny soft-touch"),
            ("H04 Sklo (s očami a okienkom kamery)", ["H04", "H04E", "H04C"], "tvrdené sklo 1.1 mm"),
            ("H05-R Ucho + H06-R LED krúžok", ["H05-R", "H06-R"], "pravé (−X); ľavé zrkadlovo"),
        ], q, recs, subtitle="všetky riadky v rovnakej mierke"))
    if want("09") and "neck" in have:
        tasks.append(lambda: sheet_six("09_NOVA_krk", "NOVA / KRK A GOLIER", ext("neck"), q, recs,
                                       subtitle=f"N01 golier {N['collar']['w']:.0f}×{N['collar']['d']:.0f} · N02 kužeľ Ø{2 * N['cone']['r_bottom']:.0f}→Ø{2 * N['cone']['r_top']:.0f} · N06 valec Ø{N['tilt_housing']['barrel_d']:.0f}×{N['tilt_housing']['barrel_len']:.0f} · os náklonu z = {spec.TILT_AXIS['z']:.0f}"))
    if want("10") and "neck" in have:
        tasks.append(lambda: sheet_matrix("10_NOVA_kryty_krku", "NOVA / DIELY KRKU", [
            ("N01 Spodný golier", ["N01"], "pevný na trupe (J1)"),
            ("N02 Plast krku", ["N02"], "jeden kus, otáča sa (J2)"),
            ("N06 Kryt náklonu", ["N06"], "servo náklonu vnútri (J2)"),
            ("N07-R Koncová krytka pravá", ["N07-R"], "strana serva, s hlavou (J3)"),
            ("N07-L Koncová krytka ľavá", ["N07-L"], "pasívna: dutý čap, ložisko 6703"),
        ], q, recs, subtitle="všetky riadky v rovnakej mierke"))
    if want("11") and "torso" in have:
        tasks.append(lambda: sheet_six("11_NOVA_trup", "NOVA / TRUP",
                                       P(lambda r: (r["sub"] == "torso" or r["id"].startswith("A05")) and not r.get("internal")), q, recs,
                                       subtitle=f"T01–T06 · superelipsa n={T['n']:g}, {T['w']:.0f} × {T['d']:.0f} × {T['z1'] - T['z0']:.0f} mm · os ramien z = {A['axis']['z']:.0f}"))
    if want("12") and "torso" in have:
        tasks.append(lambda: sheet_matrix("12_NOVA_kryty_trupu", "NOVA / DIELY TRUPU", [
            ("T01 Stredový pás", ["T01"], "biely, spredu–cez vrch–dozadu"),
            ("T02-R Bočný kryt pravý", ["T02-R"], "ľavý (T02-L) zrkadlovo"),
            ("T03 Zadné dvierka", ["T03"], "2 háčiky + 2 magnety"),
            ("T04 Spodná vanička", ["T04"], "čierna · 4+2× M2.5 · 3× M3 (J1)"),
            ("T05 LED svetlovod hrude", ["T05"], "PMMA opál"),
            ("T06 Senzorové okienko", ["T06"], "ToF zóna 0.8 mm + matná zóna ALS"),
        ], q, recs, subtitle="všetky riadky v rovnakej mierke"))
    arm_sub = (f"A01–A05 · pádlo {2 * A['egg']['half_w']:.0f} × {2 * A['egg']['half_t']:.0f} × {A['egg']['top_z'] - A['egg']['bottom_z']:.0f} mm · "
               f"rozpaženie {A['abduction_deg']:g}° · os ramena z = {A['axis']['z']:.0f}")
    if want("13") and "arm_R" in have:
        tasks.append(lambda: sheet_six("13_NOVA_prava_ruka", "NOVA / PRAVÁ RUKA", P(lambda r: r["sub"] == "arm_R" and not r.get("internal")), q, recs,
                                       subtitle=arm_sub + " · pravá strana robota (−X)"))
    if want("14") and "arm_L" in have:
        tasks.append(lambda: sheet_six("14_NOVA_lava_ruka", "NOVA / ĽAVÁ RUKA", P(lambda r: r["sub"] == "arm_L" and not r.get("internal")), q, recs,
                                       subtitle=arm_sub + " · ľavá strana (+X), zrkadlovo"))
    if want("15") and "arm_R" in have:
        tasks.append(lambda: sheet_matrix("15_NOVA_diely_ruky", "NOVA / DIELY RUKY", [
            ("A01 Vonkajšia skrupina", ["A01-R"], "biely PC/ABS, šošovkový panel"),
            ("A02 Vnútorná skrupina", ["A02-R"], "biely PC/ABS, náboj Ø26"),
            ("A03 Vložka špičky", ["A03-R"], "čierne TPU 85A"),
            ("A04 Kryt kĺbu", ["A04-R"], "čierny soft-touch"),
            ("A05 Prechodový krúžok", ["A05-R"], "čierny, pevný v trupe"),
        ], q, recs, subtitle="pravá ruka (A0x-R), ľavá zrkadlovo · všetky riadky v rovnakej mierke"))
    if want("16") and "arm_R" in have:
        tasks.append(lambda: sheet_arm_explode(q, recs))
    if want("17") and "base" in have:
        tasks.append(lambda: sheet_six("17_NOVA_zakladna", "NOVA / ZÁKLADŇA", ext("base"), q, recs,
                                       subtitle=f"B01–B08 · {B['w']:.0f} × {B['d']:.0f} × {B['z1']:.0f} mm · batérie, reproduktor, otáčanie tela · poklop batérie vpravo (−X)"))
    if want("18") and "base" in have:
        tasks.append(lambda: sheet_matrix("18_NOVA_kryty_zakladne", "NOVA / DIELY ZÁKLADNE", [
            ("B01 Horný kryt", ["B01"], "biely PC/ABS"), ("B02 Spodná doska", ["B02"], "čierna, 4× M3"),
            ("B03 Svetlovod", ["B03"], "PMMA opál"), ("B04 Nožičky (4×)", ["B04"], "TPU"),
            ("B05 Otočný tanier", ["B05"], "čierny, spojený s trupom (J1)"),
            ("B08 Poklop batérie", ["B08"], "1× M3 + 2 háčiky"),
        ], q, recs, subtitle="všetky riadky v rovnakej mierke"))
    if want("19") and has_int:
        tasks.append(lambda: sheet_internals(q, recs))
    if want("20"):
        tasks.append(lambda: sheet_expressions(q, recs))
    if want("21"):
        tasks.append(lambda: sheet_compare(q, recs))
    for t in tasks:
        try:
            print("->", t(), flush=True)
        except Exception as e:  # keep going, report
            import traceback
            traceback.print_exc()
            print("FAILED", e, flush=True)
    print("done")


if __name__ == "__main__":
    main()
