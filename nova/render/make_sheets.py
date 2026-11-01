"""
Produce the final image set in obrazky/ from the CAD exports in build/.

    /opt/venv/cad/bin/python -m nova.render.make_sheets [--only 01,07] [--quality draft|final] [--jobs 2]

Rendering is delegated to Blender (nova/render/render.py) in subprocesses; composition uses PIL.
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

Q = {
    "draft": dict(res6=(560, 480), resp=(900, 1000), samples=16, cell_res=(360, 320), big=(1100, 900)),
    "final": dict(res6=(1000, 860), resp=(1800, 2000), samples=80, cell_res=(560, 500), big=(1800, 1500)),
}
SIX = ["front", "back", "right", "left", "top", "bottom"]


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def manifest():
    recs = []
    for fn in sorted(glob.glob(os.path.join(ROOT, "build", "manifest", "*.json"))):
        with open(fn) as f:
            recs.extend(json.load(f))
    return recs


def render(job, name):
    out = os.path.join(TMP, name)
    job = dict(job)
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


def composite(rd, view, bg=S.BG):
    im = Image.open(os.path.join(rd, f"{view}.png")).convert("RGBA")
    base = Image.new("RGBA", im.size, bg + (255,))
    base.alpha_composite(im)
    return base.convert("RGB")


def new_sheet(W, H, title, subtitle=None, note=None):
    sh = Image.new("RGB", (W, H), S.BG)
    d = ImageDraw.Draw(sh)
    S.title_block(d, W, title, subtitle, note)
    return sh, d


def footer(d, W, H):
    d.text((W - 60, H - 36), FOOT, fill=S.MUTED, font=S.font(22, "Medium"), anchor="rs")


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


def dim_h(d, x1, x2, y_feature1, y_feature2, y_line, text, color=DIM, fs=26):
    """Horizontal dimension between x1 and x2 placed at y_line, extension lines from feature y's."""
    for x, yf in ((x1, y_feature1), (x2, y_feature2)):
        d.line([(x, yf + (6 if y_line > yf else -6)), (x, y_line + (10 if y_line > yf else -10))], fill=color, width=2)
    d.line([(x1, y_line), (x2, y_line)], fill=color, width=2)
    arrow(d, (x1, y_line), (-1, 0), color=color)
    arrow(d, (x2, y_line), (1, 0), color=color)
    tw = d.textlength(text, font=S.font(fs, "SemiBold"))
    xm = (x1 + x2) / 2
    d.rectangle([xm - tw / 2 - 8, y_line - fs / 2 - 6, xm + tw / 2 + 8, y_line + fs / 2 + 4], fill=S.BG)
    d.text((xm, y_line), text, fill=color, font=S.font(fs, "SemiBold"), anchor="mm")


def dim_v(d, y1, y2, x_feature1, x_feature2, x_line, text, color=DIM, fs=26):
    for y, xf in ((y1, x_feature1), (y2, x_feature2)):
        d.line([(xf + (6 if x_line > xf else -6), y), (x_line + (10 if x_line > xf else -10), y)], fill=color, width=2)
    d.line([(x_line, y1), (x_line, y2)], fill=color, width=2)
    arrow(d, (x_line, y1), (0, -1) if y1 < y2 else (0, 1), color=color)
    arrow(d, (x_line, y2), (0, 1) if y1 < y2 else (0, -1), color=color)
    font = S.font(fs, "SemiBold")
    tw = d.textlength(text, font=font)
    ym = (y1 + y2) / 2
    # rotated text
    tmp = Image.new("RGBA", (int(tw + 16), fs + 14), S.BG + (255,))
    ImageDraw.Draw(tmp).text((tmp.width / 2, tmp.height / 2), text, fill=color, font=font, anchor="mm")
    tmp = tmp.rotate(90, expand=True)
    return tmp, (int(x_line - tmp.width / 2), int(ym - tmp.height / 2))


def level_mark(d, x0, x1, y, text, color=(150, 150, 150)):
    for xx in range(int(x0), int(x1), 14):
        d.line([(xx, y), (min(xx + 7, x1), y)], fill=color, width=1)
    d.text((x1 + 8, y), text, fill=(90, 92, 98), font=S.font(21, "Medium"), anchor="lm")


# ---------------------------------------------------------------------------
# sheet builders
# ---------------------------------------------------------------------------

def sheet_six(name, title, parts, q, subtitle=None, subs=None, internal=False, extra_views=None):
    views = SIX + (extra_views or [])
    job = dict(res=list(q["res6"]), samples=q["samples"], views=views, internal=internal)
    if parts:
        job["parts"] = parts
    if subs:
        job["subs"] = subs
    rd = render(job, name)
    cols = 4 if extra_views else 3
    return S.six_view_sheet(rd, title, os.path.join(OUT, f"{name}.png"), views=tuple(views), cols=cols,
                            cell=(q["res6"][0], q["res6"][1] + 60) if cols == 3 else (q["res6"][0] * 3 // 4 + 40, q["res6"][1] * 3 // 4 + 80),
                            subtitle=subtitle, footer=FOOT)


def sheet_matrix(name, title, rows, q, subtitle=None):
    """rows: list of (label, [part ids], note)"""
    def one(i_row):
        i, (label, pids, note) = i_row
        rd = render(dict(parts=pids, res=list(q["cell_res"]), samples=max(12, q["samples"] // 2), views=SIX,
                         scale_fit="shared", shadow=False, internal=True, margin=0.08), f"{name}_{i:02d}")
        return (label, rd, note)
    with ThreadPoolExecutor(max_workers=2) as ex:
        rr = list(ex.map(one, list(enumerate(rows))))
    cw, ch = q["cell_res"][0] * 3 // 5 + 20, q["cell_res"][1] * 3 // 5 + 20
    return S.matrix_sheet(rr, title, os.path.join(OUT, f"{name}.png"), subtitle=subtitle, footer=FOOT,
                          cell=(cw, ch), label_w=330)


def sheet_hero(q, recs):
    rd = render(dict(res=list(q["resp"]), samples=q["samples"] + 32, lens=85,
                     views=["iso", "iso_back", "iso_r"], margin=0.06, floor_z=spec.FLOOR_Z), "00_hero")
    W, H = 3000, 2000
    sh, d = new_sheet(W, H, "NOVA", "stolový spoločník – najlepšia verzia (v7)")
    hero = composite(rd, "iso")
    hero, _ = S.fit(hero, 1700, 1820)
    sh.paste(hero, (40, 150))
    for k, v in enumerate(["iso_back", "iso_r"]):
        im = composite(rd, v)
        im, _ = S.fit(im, 640, 700)
        sh.paste(im, (1760 + k * 610, 1240))
    x0, y = 1800, 210
    facts = [
        ("Rozmery", f"{spec.BASE['w']:.0f} × {spec.BASE['d']:.0f} × {spec.OVERALL['h']:.0f} mm (základňa × výška)"),
        ("Pohyb", "5 DOF: telo 360°, hlava ±90° / −20…+30°, ruky −30…+180°"),
        ("Tvár", "4.3\" IPS 800×480 (ESP32-S3 v hlave), tvrdené sklo, kamera"),
        ("Zmysly", "2 mikrofóny v ušiach, ToF + svetlo, dotyk, IMU"),
        ("Svetlo", "LED krúžky v ušiach, pásik na hrudi a základni"),
        ("Mozog", "Raspberry Pi 5 + 2× ESP32-S3 + RP2040"),
        ("Napájanie", "2× 18650 (25 Wh), USB-C PD"),
        ("Materiály", "biely PC/ABS satén, čierny soft-touch, TPU"),
    ]
    for k, (a, b) in enumerate(facts):
        d.text((x0, y + k * 118), a.upper(), fill=S.ACCENT, font=S.font(26, "Bold"))
        d.text((x0, y + k * 118 + 38), b, fill=S.INK, font=S.font(34, "Medium"))
    footer(d, W, H)
    out = os.path.join(OUT, "00_NOVA_prehlad.png")
    sh.save(out, optimize=True)
    # standalone hero image too
    composite(rd, "iso").save(os.path.join(OUT, "00b_NOVA_hero.png"), optimize=True)
    return out


def sheet_dims(q, recs):
    rd = render(dict(res=[1400, 1500], samples=q["samples"], views=["front", "right", "top"], margin=0.16,
                     floor_z=spec.FLOOR_Z), "02_dims")
    m = meta(rd)["views"]
    W, H = 3000, 1900
    sh, d = new_sheet(W, H, "NOVA / HLAVNÉ ROZMERY", "pohľad spredu a z pravého boku · mm")
    panels = {"front": (60, 170), "right": (1540, 170)}
    scale = 1700 / 1500
    rot_texts = []

    def P(view, p):
        px, py = S.project(m[view], p)
        ox, oy = panels[view]
        return ox + px * scale, oy + py * scale

    for v, (ox, oy) in panels.items():
        im = composite(rd, v).resize((int(1400 * scale), int(1500 * scale)), Image.LANCZOS)
        sh.paste(im, (ox, oy))
        d.text((ox + 20, oy + 10), S.VIEW_LABELS[v], fill=S.INK, font=S.font(30, "SemiBold"))
    # FRONT view dims
    B, T, Hd = spec.BASE, spec.TORSO, spec.HEAD
    zf = spec.FLOOR_Z
    a = P("front", (-B["w"] / 2, -100, zf)); b = P("front", (B["w"] / 2, -100, zf))
    dim_h(d, a[0], b[0], a[1], b[1], a[1] + 60, f"{B['w']:.0f}")
    a = P("front", (-Hd["w"] / 2, -100, Hd["z1"])); b = P("front", (Hd["w"] / 2, -100, Hd["z1"]))
    dim_h(d, a[0], b[0], a[1], b[1], a[1] - 50, f"{Hd['w']:.0f}")
    ear = Hd["w"] / 2 + Hd["ear"]["protrude"]
    a = P("front", (-ear, -100, Hd["ear"]["z"])); b = P("front", (ear, -100, Hd["ear"]["z"]))
    dim_h(d, a[0], b[0], a[1] - 70, b[1] - 70, P("front", (0, 0, Hd["z1"]))[1] - 110, f"{2 * ear:.0f} (uši)")
    a = P("front", (-T["w"] / 2, -100, 85)); b = P("front", (T["w"] / 2, -100, 85))
    dim_h(d, a[0], b[0], a[1], b[1], P("front", (0, 0, 20))[1], f"{T['w']:.0f}")
    # vertical overall + levels
    xl = P("front", (-B["w"] / 2, 0, 0))[0] - 70
    top = P("front", (0, 0, Hd["z1"])); bot = P("front", (0, 0, zf))
    img, pos = dim_v(d, top[1], bot[1], top[0] - 70, bot[0] - 90, xl, f"{spec.OVERALL['h']:.0f}")
    rot_texts.append((img, pos))
    xr = P("front", (B["w"] / 2, 0, 0))[0] + 30
    for z, lab in [(B["z1"], f"z {B['z1']:.0f} základňa"), (T["z1"], f"z {T['z1']:.0f} trup"),
                   (spec.ARM["axis"]["z"], f"z {spec.ARM['axis']['z']:.0f} os ramien"),
                   (Hd["z0"], f"z {Hd['z0']:.0f} spodok hlavy"), (spec.TILT_AXIS["z"], f"z {spec.TILT_AXIS['z']:.0f} os náklonu"),
                   (Hd["z1"], f"z {Hd['z1']:.0f} vrch")]:
        p = P("front", (B["w"] / 2, 0, z))
        level_mark(d, p[0] - 40 if z > 150 else p[0] + 5, xr + 60, p[1], lab)
    # SIDE view dims (right = camera at -X, front of robot on the right side of the image)
    a = P("right", (0, -B["d"] / 2, zf)); b = P("right", (0, B["d"] / 2, zf))
    dim_h(d, min(a[0], b[0]), max(a[0], b[0]), a[1], b[1], a[1] + 60, f"{B['d']:.0f}")
    hf = Hd["y0"] - Hd["bezel"]["protrude"]
    a = P("right", (0, hf, Hd["z1"])); b = P("right", (0, Hd["y1"], Hd["z1"]))
    dim_h(d, min(a[0], b[0]), max(a[0], b[0]), a[1], b[1], a[1] - 50, f"{Hd['y1'] - hf:.1f}")
    a = P("right", (0, -T["d"] / 2, 85)); b = P("right", (0, T["d"] / 2, 85))
    dim_h(d, min(a[0], b[0]), max(a[0], b[0]), a[1], b[1], P("right", (0, 0, 20))[1], f"{T['d']:.0f}")
    # heights on side view: base, torso, head
    xs = P("right", (0, -B["d"] / 2, 0))[0] + 60
    for z0, z1, lab in [(zf, B["z1"], f"{B['z1'] - zf:.1f}"), (T["z0"], T["z1"], f"{T['z1'] - T['z0']:.0f}"),
                        (Hd["z0"], Hd["z1"], f"{Hd['h']:.0f}")]:
        p0 = P("right", (0, -B["d"] / 2, z0)); p1 = P("right", (0, -B["d"] / 2, z1))
        img, pos = dim_v(d, p1[1], p0[1], p1[0] - 200, p0[0] - 200, xs, lab)
        rot_texts.append((img, pos))
    for img, pos in rot_texts:
        sh.paste(img, pos)
    footer(d, W, H)
    out = os.path.join(OUT, "02_NOVA_rozmery.png")
    sh.save(out, optimize=True)
    return out


def callouts(sh, d, rd, view, recs, factor, items, area, label_fn, scale=1.0, offset=(0, 0)):
    """Draw numbered leader-line labels for parts in an exploded render."""
    m = meta(rd)["views"][view]
    by = {r["id"]: r for r in recs}
    pts = []
    for pid in items:
        r = by.get(pid)
        if not r:
            continue
        bb = r["bbox"]
        c = [(bb["min"][i] + bb["max"][i]) / 2 + r["explode"][i] * factor for i in range(3)]
        px, py = S.project(m, c)
        pts.append((pid, offset[0] + px * scale, offset[1] + py * scale))
    if not pts:
        return
    x0, y0, x1, y1 = area
    left = sorted([p for p in pts if p[1] < (x0 + x1) / 2], key=lambda p: p[2])
    right = sorted([p for p in pts if p[1] >= (x0 + x1) / 2], key=lambda p: p[2])
    f = S.font(24, "SemiBold")
    for side, group in (("L", left), ("R", right)):
        n = len(group)
        for k, (pid, px, py) in enumerate(group):
            ly = y0 + (k + 0.5) * (y1 - y0) / max(n, 1)
            lx = x0 + 20 if side == "L" else x1 - 20
            d.line([(px, py), (lx + (150 if side == "L" else -150), ly), (lx + (140 if side == "L" else -140), ly)],
                   fill=S.ACCENT, width=2)
            d.ellipse([px - 6, py - 6, px + 6, py + 6], fill=S.ACCENT)
            txt = label_fn(pid)
            if side == "L":
                d.text((lx, ly), txt, fill=S.INK, font=f, anchor="lm")
            else:
                d.text((lx, ly), txt, fill=S.INK, font=f, anchor="rm")


def sheet_exploded(q, recs):
    factor = 1.0
    rd = render(dict(res=list(q["big"]), samples=q["samples"], explode=factor, views=["iso"], lens=60,
                     margin=0.05, shadow=False), "03_explode")
    W, H = 3000, 2100
    sh, d = new_sheet(W, H, "NOVA / ROZLOŽENÝ POHĽAD", "všetky vonkajšie diely · čísla dielov podľa kusovníka")
    im = Image.open(os.path.join(rd, "iso.png")).convert("RGBA")
    sc = min(2000 / im.width, 1850 / im.height)
    im = im.resize((int(im.width * sc), int(im.height * sc)), Image.LANCZOS)
    ox = (W - im.width) // 2
    sh.paste(im, (ox, 170), im)
    by = {r["id"]: r for r in recs}
    vis = [r["id"] for r in recs if not r.get("internal") and not r["id"].endswith("-L") and r["id"] not in ("H04E", "H04C")]
    callouts(sh, d, rd, "iso", recs, factor, vis, (40, 200, W - 40, H - 120),
             lambda pid: f"{pid}  {by[pid]['name']}", scale=sc, offset=(ox, 170))
    footer(d, W, H)
    out = os.path.join(OUT, "03_NOVA_rozlozeny_pohlad.png")
    sh.save(out, optimize=True)
    return out


def sheet_section(q, recs):
    rd1 = render(dict(res=[1300, 1500], samples=q["samples"], internal=True, views=["left"],
                      section=dict(axis="x", offset=0.0, keep="neg"), margin=0.08, floor_z=spec.FLOOR_Z), "04_sec_x")
    rd2 = render(dict(res=[1300, 1500], samples=q["samples"], internal=True, views=["front"],
                      section=dict(axis="y", offset=6.0, keep="pos"), margin=0.08, floor_z=spec.FLOOR_Z), "04_sec_y")
    W, H = 2900, 1900
    sh, d = new_sheet(W, H, "NOVA / REZY A ZÁSTAVBA", "oranžová = rezné plochy krytov · vnútorné komponenty v reze")
    for k, (rd, v, lab) in enumerate([(rd1, "left", "REZ A–A  (rovina x = 0, pohľad z ľavého boku)"),
                                       (rd2, "front", "REZ B–B  (rovina y = 6, pohľad spredu)")]):
        im = composite(rd, v)
        im, _ = S.fit(im, 1380, 1600)
        sh.paste(im, (60 + k * 1420, 200))
        d.text((80 + k * 1420, 180), lab, fill=S.INK, font=S.font(28, "SemiBold"))
    footer(d, W, H)
    out = os.path.join(OUT, "04_NOVA_rezy.png")
    sh.save(out, optimize=True)
    return out


def sheet_xray(q, recs):
    rd = render(dict(res=list(q["big"]), samples=q["samples"], internal=True, xray=True, xray_alpha=0.12,
                     views=["iso", "iso_back"], lens=70, margin=0.05), "05_xray")
    W, H = 3000, 1700
    sh, d = new_sheet(W, H, "NOVA / VNÚTRO (RÖNTGEN)", "kryty priehľadné · elektronika a mechanika na svojich miestach")
    for k, v in enumerate(["iso", "iso_back"]):
        im = composite(rd, v)
        im, _ = S.fit(im, 1420, 1420)
        sh.paste(im, (60 + k * 1460, 190))
    footer(d, W, H)
    out = os.path.join(OUT, "05_NOVA_vnutro.png")
    sh.save(out, optimize=True)
    return out


def sheet_kinematics(q, recs):
    poses = [
        ("J1  otáčanie tela  +45°  (rozsah 360°)", {"J1": 45}, "iso"),
        ("J2  otáčanie hlavy  +60°  (±90°)", {"J2": 60}, "iso"),
        ("J3  náklon hlavy  +30° hore", {"J3": 30}, "right"),
        ("J3  náklon hlavy  −20° dole", {"J3": -20}, "right"),
        ("J4/J5  ruky  +90° / −30°", {"J4": 90, "J5": -30}, "iso"),
        ("J4/J5  ruky hore  +170°", {"J4": 170, "J5": 170}, "front"),
    ]

    def one(k_p):
        k, (lab, pose, view) = k_p
        return render(dict(res=[760, 820], samples=max(16, q["samples"] // 2), pose=pose, views=[view], lens=70,
                           margin=0.1, floor_z=spec.FLOOR_Z, ortho_scale=300 if view in SIX else None), f"06_kin_{k}")
    with ThreadPoolExecutor(max_workers=2) as ex:
        rds = list(ex.map(one, list(enumerate(poses))))
    W, H = 60 * 2 + 3 * 900, 190 + 2 * 1000 + 80
    sh, d = new_sheet(W, H, "NOVA / KINEMATIKA – 5 STUPŇOV VOĽNOSTI",
                      "J1 BLDC v základni · J2–J5 serial-bus servá s enkodérom")
    for k, ((lab, pose, view), rd) in enumerate(zip(poses, rds)):
        r, c = divmod(k, 3)
        x0, y0 = 60 + c * 900, 190 + r * 1000
        d.rectangle([x0, y0, x0 + 900, y0 + 1000], fill=S.CELL, outline=S.LINE, width=2)
        im = Image.open(os.path.join(rd, f"{view}.png")).convert("RGBA")
        im, _ = S.fit(im, 860, 900)
        sh.paste(im, (x0 + (900 - im.width) // 2, y0 + 80), im)
        d.text((x0 + 24, y0 + 24), lab, fill=S.INK, font=S.font(28, "SemiBold"))
    footer(d, W, H)
    out = os.path.join(OUT, "06_NOVA_kinematika.png")
    sh.save(out, optimize=True)
    return out


def sheet_arm_explode(q, recs):
    side = "R"
    pids = [r["id"] for r in recs if r["id"].endswith("-" + side) and r["id"].startswith("A")]
    rd = render(dict(parts=pids, res=[1600, 1100], samples=q["samples"], explode=1.0, views=[
        {"name": "ex", "loc": [-520, -380, 260], "target": [-110, 0, 95], "lens": 85}], shadow=False), "16_arm_ex")
    W, H = 2600, 1500
    sh, d = new_sheet(W, H, "NOVA / RUKA A RAMENO – SKLADANIE", "pravá ruka (ľavá zrkadlovo) · servo v trupe, kryt kĺbu nesie ruku")
    im = Image.open(os.path.join(rd, "ex.png")).convert("RGBA")
    sc = min(2300 / im.width, 1250 / im.height)
    im = im.resize((int(im.width * sc), int(im.height * sc)), Image.LANCZOS)
    ox = (W - im.width) // 2
    sh.paste(im, (ox, 180), im)
    by = {r["id"]: r for r in recs}
    callouts(sh, d, rd, "ex", recs, 1.0, pids, (40, 220, W - 40, H - 120),
             lambda pid: f"{pid}  {by[pid]['name']}", scale=sc, offset=(ox, 180))
    footer(d, W, H)
    out = os.path.join(OUT, "16_NOVA_ruka_skladanie.png")
    sh.save(out, optimize=True)
    return out


def sheet_compare(q, recs):
    rd = os.path.join(TMP, "00_hero")
    ref = Image.open(os.path.join(ROOT, "referencie", "R01_celok_zadanie.png")).convert("RGB")
    ref = ref.crop((0, 350, ref.width, 1750))
    W, H = 2400, 1500
    sh, d = new_sheet(W, H, "NOVA / ZADANIE vs. v7")
    a, _ = S.fit(ref, 1100, 1250)
    sh.paste(a, (60 + (1100 - a.width) // 2, 200))
    b, _ = S.fit(composite(rd, "iso"), 1100, 1250)
    sh.paste(b, (1240 + (1100 - b.width) // 2, 200))
    d.text((80, 170), "OBRÁZOK ZO ZADANIA", fill=S.MUTED, font=S.font(28, "SemiBold"))
    d.text((1260, 170), "NOVA v7 – RENDER Z CAD MODELU", fill=S.MUTED, font=S.font(28, "SemiBold"))
    footer(d, W, H)
    out = os.path.join(OUT, "21_NOVA_porovnanie_so_zadanim.png")
    sh.save(out, optimize=True)
    return out


def sheet_expressions(q, recs):
    """2D sheet: screen layout (true scale) and the expression set drawn on the 4.3" display."""
    Hd = spec.HEAD
    g, ey, disp = Hd["glass"], Hd["eyes"], Hd["display"]
    k = 7.0                      # px per mm
    cw, ch = int(g["w"] * k) + 60, int(g["h"] * k) + 120
    exprs = ["Neutrálny", "Šťastný", "Žmurk", "Prekvapený", "Ospalý", "Zvedavý", "Smutný", "Nahnevaný",
             "Počúvam", "Láska"]
    cols = 5
    rows = math.ceil(len(exprs) / cols)
    W, H = 60 * 2 + cols * cw, 190 + 900 + rows * ch + 80
    sh, d = new_sheet(W, H, "NOVA / DISPLEJ A VÝRAZY",
                      f"sklo {g['w']:.0f}×{g['h']:.0f} R{g['r']:.0f} · aktívna plocha {disp['active'][0]:.1f}×{disp['active'][1]:.1f} (4.3\" 800×480) · oči {ey['w']:.0f}×{ey['h']:.0f} R{ey['r']:.1f}")
    eye_col = (255, 222, 172)
    zc = Hd["zc"]

    def glass(x0, y0, kk):
        w, h = g["w"] * kk, g["h"] * kk
        d.rounded_rectangle([x0, y0, x0 + w, y0 + h], radius=g["r"] * kk, fill=(12, 12, 14))
        b = g["print_border"] * kk
        aw, ah = disp["active"][0] * kk, disp["active"][1] * kk
        acx, acy = x0 + w / 2, y0 + h / 2 + (zc - disp["zc"]) * kk
        return acx, acy

    def cam(x0, y0, kk):
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
            elif name == "Žmurk":
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
    dim_h(d, gx, gx + gw, gy + gh, gy + gh, gy + gh + 50, f"sklo {g['w']:.0f}")
    dim_h(d, acx - aw / 2, acx + aw / 2, acy + ah / 2, acy + ah / 2, gy + gh + 110, f"aktívna plocha {disp['active'][0]:.2f}")
    exx = ey["x"] * kk
    dim_h(d, acx - exx, acx + exx, acy - 120, acy - 120, gy - 40, f"rozostup očí {2 * ey['x']:.0f}")
    tx = gx + gw + 120
    lines = [
        ("Sklo", f"{g['w']:.0f} × {g['h']:.0f} mm, R{g['r']:.0f}, hr. {g['t']} mm, tvrdené, čierna potlač okraja {g['print_border']:.0f} mm"),
        ("Displej", f"4.3\" IPS 800×480 MIPI-DSI, obrys {disp['outline'][0]}×{disp['outline'][1]} mm, stred z={disp['zc']:.0f}"),
        ("Kamera", f"otvor Ø{Hd['camera']['hole_d']} v potlači hore v strede (z={Hd['camera']['z']:.0f}), modul 8.5×8.5 mm"),
        ("Oči", f"{ey['w']:.0f}×{ey['h']:.0f} mm R{ey['r']}, stredy x=±{ey['x']}, z={ey['z']:.0f} (mierne pod stredom skla)"),
        ("Farba očí", "teplá biela #FFDEAC; animácie 60 fps, žmurknutie každých 3–8 s"),
        ("Rozlíšenie", f"{800 / disp['active'][0]:.1f} px/mm → oko ≈ {ey['w'] * 800 / disp['active'][0]:.0f}×{ey['h'] * 800 / disp['active'][0]:.0f} px"),
    ]
    for i, (a_, b_) in enumerate(lines):
        d.text((tx, 280 + i * 105), a_.upper(), fill=S.ACCENT, font=S.font(24, "Bold"))
        d.text((tx, 280 + i * 105 + 34), b_, fill=S.INK, font=S.font(29, "Medium"))
    # LED signalling palette
    lx0 = tx + 1250
    d.text((lx0, 280), "LED SIGNALIZÁCIA (uši H06 · hruď T05 · základňa B03)", fill=S.ACCENT, font=S.font(24, "Bold"))
    leds = [((60, 230, 250), "tyrkysová svieti", "pokoj / pripravený"),
            ((60, 140, 255), "modrá pulzuje", "počúva (hlas)"),
            ((170, 90, 255), "fialová beží dookola", "premýšľa / AI"),
            ((60, 220, 120), "zelená dýcha", "nabíja sa"),
            ((255, 160, 40), "oranžová bliká", "slabá batéria < 15 %"),
            ((255, 60, 60), "červená bliká", "chyba / zablokované servo"),
            ((245, 245, 245), "biela záblesk", "dotyk temena / ucha")]
    for i, (col, a_, b_) in enumerate(leds):
        yy = 340 + i * 82
        d.ellipse([lx0, yy, lx0 + 46, yy + 46], fill=col, outline=(200, 200, 200))
        d.ellipse([lx0 + 12, yy + 12, lx0 + 34, yy + 34], fill=S.BG)
        d.text((lx0 + 70, yy + 2), a_, fill=S.INK, font=S.font(28, "SemiBold"))
        d.text((lx0 + 70, yy + 36), b_, fill=S.MUTED, font=S.font(24, "Medium"))
    # expression grid
    y_base = 190 + 900
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
    a = ap.parse_args()
    q = Q[a.quality]
    only = set(x for x in a.only.split(",") if x)
    recs = manifest()
    os.makedirs(OUT, exist_ok=True)
    have = {r["sub"] for r in recs}

    def want(k):
        return not only or k in only

    def P(pred):
        return ids(recs, pred)

    tasks = []
    if want("00"):
        tasks.append(lambda: sheet_hero(q, recs))
    if want("01"):
        tasks.append(lambda: sheet_six("01_NOVA_celok_6_pohladov", "NOVA / CELOK", None, q,
                                       subtitle=f"výška {spec.OVERALL['h']:.0f} mm · základňa {spec.BASE['w']:.0f}×{spec.BASE['d']:.0f} mm · 5 stupňov voľnosti"))
    if want("02"):
        tasks.append(lambda: sheet_dims(q, recs))
    if want("03"):
        tasks.append(lambda: sheet_exploded(q, recs))
    if want("04") and "internal" in {r.get("sub") for r in recs} | ({"internal"} if any(r.get("internal") for r in recs) else set()):
        tasks.append(lambda: sheet_section(q, recs))
    if want("05") and any(r.get("internal") for r in recs):
        tasks.append(lambda: sheet_xray(q, recs))
    if want("06"):
        tasks.append(lambda: sheet_kinematics(q, recs))
    if want("07") and "head" in have:
        tasks.append(lambda: sheet_six("07_NOVA_hlava", "NOVA / HLAVA", P(lambda r: r["sub"] == "head" and not r.get("internal")), q,
                                       subtitle=f"H01–H06 · {spec.HEAD['w']:.0f} × {spec.HEAD['y1'] - spec.HEAD['y0'] + spec.HEAD['bezel']['protrude']:.0f} × {spec.HEAD['h']:.0f} mm (š × h × v)"))
    if want("08") and "head" in have:
        tasks.append(lambda: sheet_matrix("08_NOVA_kryty_hlavy", "NOVA / DIELY HLAVY", [
            ("H01 Hlavný obal", ["H01"], "biely PC/ABS"),
            ("H02 Zadný kryt", ["H02"], "biely PC/ABS"),
            ("H03 Predný rám", ["H03"], "čierny soft-touch"),
            ("H04 Sklo + oči + okienko kamery", ["H04", "H04E", "H04C"], "sklo 1.1 mm"),
            ("H05 Ucho + H06 LED krúžok", ["H05-R", "H06-R"], "pravé, ľavé zrkadlovo"),
        ], q))
    if want("09") and "neck" in have:
        tasks.append(lambda: sheet_six("09_NOVA_krk", "NOVA / KRK A GOLIER", P(lambda r: r["sub"] == "neck" and not r.get("internal")), q,
                                       subtitle="N01 golier · N02 plast krku · N06 kryt náklonu · N07 krytky"))
    if want("10") and "neck" in have:
        tasks.append(lambda: sheet_matrix("10_NOVA_kryty_krku", "NOVA / DIELY KRKU", [
            ("N01 Spodný golier", ["N01"], "pevný na trupe"),
            ("N02 Plast krku", ["N02"], "otáča sa (J2)"),
            ("N06 Kryt náklonu", ["N06"], "servo náklonu vnútri"),
            ("N07 Koncová krytka", ["N07-R"], "s hlavou (J3)"),
        ], q))
    if want("11") and "torso" in have:
        tasks.append(lambda: sheet_six("11_NOVA_trup", "NOVA / TRUP", P(lambda r: (r["sub"] == "torso" or r["id"].startswith("A05")) and not r.get("internal")), q,
                                       subtitle=f"T01–T06 · superelipsa {spec.TORSO['w']:.0f} × {spec.TORSO['d']:.0f} × {spec.TORSO['z1'] - spec.TORSO['z0']:.0f} mm"))
    if want("12") and "torso" in have:
        tasks.append(lambda: sheet_matrix("12_NOVA_kryty_trupu", "NOVA / DIELY TRUPU", [
            ("T01 Stredový pás", ["T01"], "biely, spredu–cez vrch–dozadu"), ("T02 Bočný kryt", ["T02-R"], "pravý, ľavý zrkadlovo"),
            ("T03 Zadné dvierka", ["T03"], "servisný prístup"), ("T04 Spodná vanička", ["T04"], "čierna, 4× M2.5"),
            ("T05 LED svetlovod", ["T05"], "PMMA opál"), ("T06 Senzorové okienko", ["T06"], "ToF + svetlo"),
        ], q))
    if want("13") and "arm_R" in have:
        tasks.append(lambda: sheet_six("13_NOVA_prava_ruka", "NOVA / PRAVÁ RUKA", P(lambda r: r["sub"] == "arm_R" and not r.get("internal")), q,
                                       subtitle="pravá strana robota = vľavo pri pohľade spredu (−X)"))
    if want("14") and "arm_L" in have:
        tasks.append(lambda: sheet_six("14_NOVA_lava_ruka", "NOVA / ĽAVÁ RUKA", P(lambda r: r["sub"] == "arm_L" and not r.get("internal")), q,
                                       subtitle="ľavá strana robota = vpravo pri pohľade spredu (+X)"))
    if want("15") and "arm_R" in have:
        tasks.append(lambda: sheet_matrix("15_NOVA_diely_ruky", "NOVA / DIELY RUKY", [
            ("01 Vonkajšia skrupina", ["A01-R"], "A01"), ("02 Vnútorná skrupina", ["A02-R"], "A02"),
            ("03 Vložka špičky", ["A03-R"], "A03 TPU"), ("04 Kryt kĺbu", ["A04-R"], "A04"),
            ("05 Prechodový krúžok", ["A05-R"], "A05"),
        ], q))
    if want("16") and "arm_R" in have:
        tasks.append(lambda: sheet_arm_explode(q, recs))
    if want("17") and "base" in have:
        tasks.append(lambda: sheet_six("17_NOVA_zakladna", "NOVA / ZÁKLADŇA", P(lambda r: r["sub"] == "base" and not r.get("internal")), q,
                                       subtitle=f"B01–B08 · {spec.BASE['w']:.0f} × {spec.BASE['d']:.0f} × {spec.BASE['z1']:.0f} mm · batérie, reproduktor, otáčanie tela"))
    if want("18") and "base" in have:
        tasks.append(lambda: sheet_matrix("18_NOVA_kryty_zakladne", "NOVA / DIELY ZÁKLADNE", [
            ("B01 Horný kryt", ["B01"], "biely"), ("B02 Spodná doska", ["B02"], "čierna"),
            ("B03 Svetlovod", ["B03"], "PMMA"), ("B04 Nožičky", ["B04"], "TPU"), ("B05 Otočný tanier", ["B05"], "J1"),
            ("B08 Poklop batérie", ["B08"], "1× M3 + 2 háčiky"),
        ], q))
    if want("20"):
        tasks.append(lambda: sheet_expressions(q, recs))
    if want("21"):
        tasks.append(lambda: sheet_compare(q, recs))
    for t in tasks:
        try:
            print("->", t())
        except Exception as e:  # keep going, report
            import traceback
            traceback.print_exc()
            print("FAILED", e)
    print("done")


if __name__ == "__main__":
    main()
