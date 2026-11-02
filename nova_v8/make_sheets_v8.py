"""
NOVA mini v8.1 – image sheets for all three head variants (A flat glass, A+ curved R180, B visor).

    /opt/venv/cad/bin/python -m nova_v8.make_sheets_v8 [--quality draft|final] [--only spol,A,Aplus,B] [--reuse]

Reuses the v7.3 sheet machinery (nova/render/make_sheets.py) with v8 numbers, v8 build folders and the
head variant swapped in through the renderer's "extra"/"exclude" options.
Output: obrazky/v8/spolocne/ (body, sections, electronics, kinematics – shared) and
        obrazky/v8/hlava_<A|A_plus|B>/ (overview, 6 views, exploded view, head sheets, glass manufacturing).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import types

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
from nova import spec as S7  # noqa: E402
from nova.render import make_sheets as MS  # noqa: E402
from nova.render import sheet as S  # noqa: E402
from nova_v8 import spec as S8  # noqa: E402

BUILD = os.path.join(ROOT, "build_v8")
VAR = {
    "A": dict(label="A · ploché sklo", dir="hlava_A", extra=[], sub="head"),
    "Aplus": dict(label="A+ · jemne zakrivené sklo R180", dir="hlava_A_plus", sub="head_aplus",
                  extra=[dict(manifest_dir=os.path.join(ROOT, "build_v8_var_aplus", "manifest"),
                              glb_dir=os.path.join(ROOT, "build_v8_var_aplus"))]),
    "B": dict(label="B · vizor bez rámu R100", dir="hlava_B", sub="head_b",
              extra=[dict(manifest_dir=os.path.join(ROOT, "build_v8_var_b", "manifest"),
                          glb_dir=os.path.join(ROOT, "build_v8_var_b"))]),
}
AXES = {"J2": [[0, 0, 1], [0, 0, 0]], "J3": [[1, 0, 0], [0, S8.NECK["tilt_axis"]["y"], S8.NECK["tilt_axis"]["z"]]],
        "J4": [[1, 0, 0], [0, S8.ARM["axis"]["y"], S8.ARM["axis"]["z"]]],
        "J5": [[1, 0, 0], [0, S8.ARM["axis"]["y"], S8.ARM["axis"]["z"]]]}
HERO_CAM = {"name": "hero", "loc": [245, -735, 290], "target": [0, 0, 98], "lens": 95}
CUR = {"v": "A"}


def compat_spec():
    """v7-shaped namespace with v8 numbers so the generic v7 sheet functions draw the right values."""
    H = dict(S8.HEAD)
    H["display"] = dict(S8.DISPLAY, zc=S8.HEAD["zc"], label='3.5" 480×320, SPI/QSPI')
    H["camera"] = dict(S8.HEAD["camera"], hole_d=S8.HEAD["camera"]["d"])
    H["glass"] = dict(S8.HEAD["glass"], print_border=4.0, t=2.0)
    H["d"] = S8.HEAD["y1"] - S8.HEAD["y0"]
    return types.SimpleNamespace(
        VERSION=S8.VERSION, FLOOR_Z=0.0, BASE=dict(S8.BASE), TORSO=dict(S8.TORSO), HEAD=H, ARM=S8.ARM, NECK=S8.NECK,
        TILT_AXIS=S8.NECK["tilt_axis"], PAN_AXIS=dict(x=0.0, y=0.0), MATERIALS=S7.MATERIALS,
        OVERALL=dict(h=S8.HEAD["z1"], w=S8.BASE["w"], d=S8.BASE["d"]))


def head_a_ids():
    with open(os.path.join(BUILD, "manifest", "head.json")) as f:
        return [r["id"] for r in json.load(f)]


def superseded():
    """Simple bought-part envelopes in the shell modules that cad_internals replaces with detailed parts,
    plus the flat glass blanks (drawn only on the glass sheet)."""
    try:
        from nova_v8.cad_internals import SUPERSEDED
    except Exception:  # noqa: BLE001
        SUPERSEDED = []
    return set(SUPERSEDED) | {"HP04F", "HB03F"}


def manifest_v8():
    recs = []
    for nm in ("base", "torso", "head", "internals"):
        p = os.path.join(BUILD, "manifest", f"{nm}.json")
        if os.path.exists(p):
            with open(p) as f:
                recs.extend(json.load(f))
    v = VAR[CUR["v"]]
    if v["extra"]:
        drop = set(head_a_ids())
        recs = [r for r in recs if r["id"] not in drop]
        for ex in v["extra"]:
            for fn in os.listdir(ex["manifest_dir"]):
                with open(os.path.join(ex["manifest_dir"], fn)) as f:
                    recs.extend(json.load(f))
    drop = superseded()
    return [r for r in recs if r["id"] not in drop]


_render7 = MS.render


def render_v8(job, name):
    job = dict(job)
    job.setdefault("glb_dir", BUILD)
    job.setdefault("manifest_dir", os.path.join(BUILD, "manifest"))
    v = VAR[CUR["v"]]
    if v["extra"]:
        job["extra"] = v["extra"]
        job["exclude"] = list(job.get("exclude", [])) + head_a_ids()
    if not job.get("parts"):
        job["exclude"] = list(job.get("exclude", [])) + sorted(superseded())
    job["joint_axes"] = AXES
    return _render7(job, name)


_matrix7 = MS.sheet_matrix


def sheet_matrix_v8(name, title, rows, q, recs, subtitle=None):
    """v7 matrix sheet, but rows whose parts are not in the current manifest are dropped (modules evolve)."""
    have = {r["id"] for r in recs}
    ok = []
    for lab, ids, note in rows:
        ids2 = [i for i in ids if i in have]
        if ids2:
            ok.append((lab, ids2, note))
        else:
            print("  matrix row dropped (parts missing):", lab, ids)
    return _matrix7(name, title, ok, q, recs, subtitle=subtitle)


def auto_rows(recs, subs, skip=(), attach=None, short=None):
    """One matrix row per visible part of the given subassemblies (left side parts '-L' skipped)."""
    attach, short = attach or {}, short or {}
    rows = []
    for r in recs:
        if r["sub"] not in subs or r.get("internal") or r["id"] in skip or r["id"].endswith("-L"):
            continue
        desc = S7.MATERIALS.get(r["mat"], {}).get("desc", r["mat"]).split("(")[0].strip()
        nm = r["name"].split(" = ")[0].split(" (")[0].strip()
        rows.append((f"{r['id']} {nm}", [r["id"]] + attach.get(r["id"], []), short.get(r["id"], desc)))
    return rows


_group7 = MS.group_explode
_new_sheet7 = MS.new_sheet
_dim_v7 = MS.dim_v
TXT = {
    " (+1.2 nožičky)": " základňa",
    "čísla dielov podľa docs/REVIEW_NOTES.md · E = elektronika, M = ložiská a kovové diely, W = káble":
        "čísla dielov podľa nova_v8/BOM_v8.md · I = kupované diely (IH hlava · IN krk · IT trup · IB základňa · IW káble)",
}


def _t(s):
    if isinstance(s, str):
        for a, b in TXT.items():
            s = s.replace(a, b)
    return s


class _Draw:
    """ImageDraw proxy that rewrites v7-only strings drawn by the shared sheet functions."""
    def __init__(self, d):
        self._d = d

    def text(self, xy, text, *a, **k):
        return self._d.text(xy, _t(text), *a, **k)

    def textlength(self, text, *a, **k):
        return self._d.textlength(_t(text), *a, **k)

    def __getattr__(self, n):
        return getattr(self._d, n)


def new_sheet_v8(W, H, title, subtitle=None, note=None):
    if title.startswith("NOVA /"):
        title = "NOVA mini /" + title[len("NOVA /"):]
    sh, d = _new_sheet7(W, H, title, _t(subtitle), _t(note))
    return sh, _Draw(d)


def dim_v_v8(d, *a, **k):
    a = list(a)
    if len(a) >= 6:
        a[5] = _t(a[5])
    return _dim_v7(getattr(d, "_d", d), *a, **k)


def expr_v8(g, ey, disp, Hd, zc):
    px = 480 / disp["active"][0]
    lines = [
        ("Sklo", f"{g['w']:g} × {g['h']:g} mm, R{g['r']:g}, dymový PMMA 2 mm · A ploché, A+ R180, B R100"),
        ("Displej", "3.5\" IPS 480×320, dotyk, ESP32-S3 (Guition JC3248W535 / Waveshare)"),
        ("Kamera", f"voliteľná OV2640 za maskou v hornom páse (z={Hd['camera']['z']:g}) – zvonku nevidno"),
        ("Oči", f"{ey['w']:g}×{ey['h']:g} mm R{ey['r']:g}, stredy x=±{ey['x']:g}, z={ey['z']:g} ({zc - ey['z']:g} mm pod stredom skla)"),
        ("Farba očí", "teplá biela #FFDEAC; animácie 30–60 fps (LVGL), žmurknutie každých 3–8 s"),
        ("Rozlíšenie", f"{px:.1f} px/mm → oko ≈ {ey['w'] * px:.0f}×{ey['h'] * px:.0f} px"),
    ]
    leds = [((60, 230, 250), "tyrkysová svieti", "pokoj / pripravený"),
            ((60, 140, 255), "modrá pulzuje", "počúva (hlas)"),
            ((170, 90, 255), "fialová beží dookola", "premýšľa / AI"),
            ((60, 220, 120), "zelená dýcha", "nabíja sa (dok / USB-C)"),
            ((255, 160, 40), "oranžová bliká", "slabá batéria < 15 %"),
            ((255, 60, 60), "červená bliká", "okraj stola / chyba"),
            ((245, 245, 245), "biela – krátky záblesk", "dotyk displeja / temena")]
    return lines, "LED SIGNALIZÁCIA (uši · pás na hrudi · podsvietenie 360° pod základňou)", leds


def install(variant, quality_tmp):
    CUR["v"] = variant
    MS.spec = compat_spec()
    MS.manifest = manifest_v8
    MS.render = render_v8
    MS.group_explode = lambda recs, lift=55.0: _group7(recs, lift)
    MS.HERO_CAM = HERO_CAM
    MS.new_sheet = new_sheet_v8
    MS.sheet_matrix = sheet_matrix_v8
    MS.dim_v = dim_v_v8
    MS.EXPR_OVERRIDE = expr_v8
    MS.RENDER_ONLY = tuple(sorted(RENDER_ONLY))
    MS.TMP = os.path.join(quality_tmp, variant)
    MS.FOOT = f"NOVA mini {S8.VERSION} · hlava {VAR[variant]['label']} · render z CAD modelu (build123d → Blender Cycles) · mm"


OUT_ROOT = {"dir": os.path.join(ROOT, "obrazky", "v8")}   # draft runs write to /tmp (see main)


def out_dir(sub):
    p = os.path.join(OUT_ROOT["dir"], sub)
    os.makedirs(p, exist_ok=True)
    MS.OUT = p
    return p


# ---------------------------------------------------------------------------
# v8-specific sheets
# ---------------------------------------------------------------------------

def sheet_hero_v8(q, recs):
    rd = MS.render(dict(res=list(q["resp"]), samples=q["samples"] + 16, lens=70,
                        views=[HERO_CAM, "iso_back", "iso_r"], margin=0.12, floor_z=0.0), "00_hero")
    W, H = 3000, 2000
    sh, d = MS.new_sheet(W, H, "NOVA mini", f"stolový robot-spoločník {S8.VERSION} · hlava {VAR[CUR['v']]['label']}")
    hero = MS.load(rd, "hero", fade=None)
    bx = MS.alpha_bbox(hero, 220)
    pw, ph = int(0.30 * (bx[2] - bx[0])), int(0.12 * (bx[3] - bx[1]))
    hero = hero.crop((max(0, bx[0] - pw), max(0, bx[1] - ph), min(hero.width, bx[2] + pw), min(hero.height, bx[3] + ph)))
    MS.paste_fit(sh, MS.radial_fade(hero, inner=0.70), (40, 190, 1760, 1960))
    MS.paste_fit(sh, MS.load(rd, "iso_back"), (1790, 1250, 2380, 1930))
    MS.paste_fit(sh, MS.load(rd, "iso_r"), (2400, 1250, 2980, 1930))
    facts = [
        ("Rozmery", f"výška {S8.HEAD['z1']:.0f} mm · základňa {S8.BASE['w']:.0f} × {S8.BASE['d']:.0f} mm"),
        ("Pohyb", "jazda na 2 skrytých kolesách · trup ±150° · hlava ±90° / ±20° · 2 ruky"),
        ("Tvár", "3.5\" IPS 480×320 s ESP32-S3 · dymové krycie sklo (mŕtvy predok)"),
        ("Zmysly", "mikrofón, dotykový displej, ToF + svetlo za pásom na hrudi, 4 senzory proti pádu"),
        ("Svetlo", "LED krúžky v ušiach · pás v hrudi · podsvietenie stola 360°"),
        ("Mozog", "ESP32-S3 (hlava) + ESP32-C3 (trup) + uzol základne, AI cez Wi-Fi"),
        ("Napájanie", "2× 18650, USB-C a kontakty dokovania zospodu"),
        ("Cena dielov", "≈ 140 € najlacnejšia · ≈ 160 € odporúčaná (AliExpress, s DPH, bez filamentu)"),
    ]
    for k, (a, b) in enumerate(facts):
        d.text((1820, 230 + k * 120), a.upper(), fill=S.ACCENT, font=S.font(26, "Bold"))
        d.text((1820, 268 + k * 120), b, fill=S.INK, font=S.font(29, "Medium"))
    MS.footer(d, W, H)
    sh.save(os.path.join(MS.OUT, "00_NOVA_mini_prehlad.png"), optimize=True)
    base = MS.Image.new("RGBA", hero.size, S.BG + (255,))
    base.alpha_composite(MS.radial_fade(hero.copy(), inner=0.70))
    base.convert("RGB").save(os.path.join(MS.OUT, "00b_NOVA_mini_hero.png"), optimize=True)


def sheet_kin_v8(q, recs):
    ISO = {"name": "k", "loc": [420, -600, 330], "target": [0, 0, 100], "lens": 112}
    SIDE = {"name": "k", "loc": [-700, 0, 105], "target": [0, 0, 105], "ortho": True, "ortho_scale": 245}
    FRONT = {"name": "k", "loc": [0, -700, 110], "target": [0, 0, 110], "ortho": True, "ortho_scale": 270}
    poses = [
        ("J1  otáčanie trupu  +60°  (±150°, základňa stojí)", {"J1": 60}, ISO),
        ("J2  otáčanie hlavy  +60°  (±90°)", {"J2": 60}, ISO),
        ("J3  náklon hlavy  +20°  (hore)", {"J3": 20}, SIDE),
        ("J3  náklon hlavy  −20°  (dole)", {"J3": -20}, SIDE),
        ("J4 pravá +90°  ·  J5 ľavá −30°", {"J4": 90, "J5": -30}, ISO),
        ("J4/J5  obe ruky hore  +170°", {"J4": 170, "J5": 170}, FRONT),
    ]
    from concurrent.futures import ThreadPoolExecutor
    res = [760, 820]
    jobs = [(f"06_kin_{k}", dict(res=res, samples=max(16, q["samples"] // 2), pose=pose, views=[cam], shadow=False))
            for k, (_, pose, cam) in enumerate(poses)]
    for nm, cam in (("06_ghost_iso", ISO), ("06_ghost_side", SIDE), ("06_ghost_front", FRONT)):
        jobs.append((nm, dict(res=res, samples=12, views=[cam], shadow=False)))
    with ThreadPoolExecutor(max_workers=2) as ex:
        rds = dict(zip([j[0] for j in jobs], ex.map(lambda j: MS.render(j[1], j[0]), jobs)))
    W, H = 60 * 2 + 3 * 900, 200 + 2 * 1000 + 80
    sh, d = MS.new_sheet(W, H, "NOVA mini / KINEMATIKA",
                         "svetlý obrys = základná póza · jazda: 2 kolesá N20 (otočenie na mieste) · trup: STS3215 · hlava a ruky: mikro servá")
    import numpy as np
    for k, (lab, pose, cam) in enumerate(poses):
        r_, c = divmod(k, 3)
        x0, y0 = 60 + c * 900, 200 + r_ * 1000
        d.rectangle([x0, y0, x0 + 900, y0 + 1000], fill=S.CELL, outline=S.LINE, width=2)
        gname = {id(ISO): "06_ghost_iso", id(SIDE): "06_ghost_side", id(FRONT): "06_ghost_front"}[id(cam)]
        ghost = MS.Image.open(os.path.join(rds[gname], "k.png")).convert("RGBA")
        ga = np.array(ghost.split()[-1]).astype(float) * 0.22
        ghost.putalpha(MS.Image.fromarray(ga.astype("uint8")))
        im = MS.Image.open(os.path.join(rds[f"06_kin_{k}"], "k.png")).convert("RGBA")
        canvas = MS.Image.new("RGBA", im.size, (0, 0, 0, 0))
        canvas.alpha_composite(ghost)
        canvas.alpha_composite(im)
        MS.paste_fit(sh, canvas, (x0 + 20, y0 + 80, x0 + 880, y0 + 990))
        d.text((x0 + 24, y0 + 24), lab, fill=S.INK, font=S.font(27, "SemiBold"))
    MS.footer(d, W, H)
    sh.save(os.path.join(MS.OUT, "06_NOVA_mini_kinematika.png"), optimize=True)


RENDER_ONLY = {"H04C", "H04E", "HP04C", "HP04E", "HB03C", "HB03E"}


def sheet_internals_v8(q, recs):
    """Bought parts / electronics without the shells + callouts + a two-column part table (v8 has ~70 parts)."""
    ints = [r for r in recs if r.get("internal") and r["id"] not in RENDER_ONLY]
    by = {r["id"]: r for r in recs}
    rd = MS.render(dict(parts=[r["id"] for r in ints], internal=True, res=list(q["tall"]), samples=q["samples"],
                        views=["iso"], lens=70, margin=0.04, shadow=False, id_pass=True), "19_internals")
    W, H = 4200, 2300
    sh, d = MS.new_sheet(W, H, "NOVA mini / VNÚTORNÁ MECHANIKA A ELEKTRONIKA",
                         "bez krytov · I = kupované diely podľa nova_v8/BOM_v8.md (IH hlava · IN krk · IT trup · IB základňa · IW káble)"
                         " · T/N/H/B = tlačené nosiče a mechanika")
    im = MS.load(rd, "iso", fade=None)
    bx = MS.alpha_bbox(im, 10)
    bx = (max(0, bx[0] - 30), max(0, bx[1] - 30), min(im.width, bx[2] + 30), min(im.height, bx[3] + 30))
    imc = im.crop(bx)
    s_, ox, oy = MS.paste_fit(sh, imc, (700, 190, 1900, 2200))
    anc = MS.anchors(rd, "iso", min_px=120)
    pts = [(pid, ox + (x - bx[0]) * s_, oy + (y - bx[1]) * s_) for pid, (x, y, n) in anc.items() if pid in by]
    MS.callouts(d, pts, (40, 210, 2560, H - 120), lambda pid: f"{pid}  {by[pid]['name'][:34]}",
                split_x=ox + imc.width * s_ / 2, fs=22, gap=46)
    groups = [("HLAVA", ("head", "head_aplus", "head_b")), ("KRK", ("neck",)), ("TRUP", ("torso",)),
              ("RUKY", ("arm_R", "arm_L")), ("ZÁKLADŇA", ("base",))]
    cols = [(2620, 210), (3420, 210)]
    col, (tx, ty) = 0, cols[0]
    n_rows = sum(1 for r in ints if any(r["sub"] in g_[1] for g_ in groups)) + 2 * len(groups)
    ymax_half = 260 + (n_rows // 2 + 2) * 26
    d.text((tx, ty), "KUSOVNÍK – VNÚTRO", fill=S.ACCENT, font=S.font(28, "Bold"))
    ty += 50
    f = S.font(19, "Medium")
    ymax = min(H - 110, max(ymax_half, 900))
    for lab, subs in groups:
        rows = [r for r in ints if r["sub"] in subs]
        if not rows:
            continue
        if ty + 32 + 26 > ymax and col == 0:
            col, (tx, ty) = 1, (cols[1][0], cols[1][1] + 50)
            ymax = H - 110
        d.text((tx, ty), lab, fill=S.INK, font=S.font(22, "Bold"))
        ty += 32
        for r in rows:
            if ty + 26 > ymax and col == 0:
                col, (tx, ty) = 1, (cols[1][0], cols[1][1] + 50)
                ymax = H - 110
                d.text((tx, ty), lab + " (pokr.)", fill=S.INK, font=S.font(22, "Bold"))
                ty += 32
            d.text((tx + 10, ty), r["id"], fill=S.INK, font=S.font(19, "SemiBold"))
            nm = r["name"] if len(r["name"]) <= 40 else r["name"][:39] + "…"
            d.text((tx + 110, ty), nm, fill=(60, 62, 68), font=f)
            ty += 26
        ty += 8
    MS.footer(d, W, H)
    out = os.path.join(MS.OUT, "19_NOVA_mini_vnutorna_elektronika.png")
    sh.save(out, optimize=True)
    return out


def head_rows(v):
    if v == "A":
        return [("H01 Hlavný obal (jeden kus)", ["H01"], "biely, bez zadného krytu"),
                ("H03 Predný rám", ["H03"], "čierny soft-touch"),
                ("H04 Ploché dymové sklo + oči", ["H04", "H04E"], "PMMA 2 mm, mŕtvy predok"),
                ("H05-R Ucho + H06-R LED krúžok", ["H05-R", "H06-R"], "ľavé zrkadlovo")]
    if v == "Aplus":
        return [("HP01 Hlavný obal", ["HP01"], "biely"), ("HP03 Predný rám (čelo R180)", ["HP03"], "čierny"),
                ("HP04 Zakrivené sklo R180 + oči", ["HP04", "HP04E"], "PMMA 2 mm ohnuté"),
                ("HP05-R Ucho + HP06-R LED krúžok", ["HP05-R", "HP06-R"], "ľavé zrkadlovo")]
    return [("HB01 Predný obal", ["HB01"], "biely"), ("HB02 Zadný obal", ["HB02"], "biely"),
            ("HB03 Vizor R100 + oči", ["HB03", "HB03E", "HB03C"], "PMMA 2 mm ohnuté"),
            ("HB05-R LED krúžok ucha", ["HB05-R"], "zapustený, ľavý zrkadlovo")]


def sheet_glass(q, recs):
    """Manufacturing sheet of the bent cover (A+ / B): flat blank + mould drawings + steps + render of the part."""
    v = CUR["v"]
    import cairosvg
    from PIL import Image
    if v == "Aplus":
        svg = os.path.join(ROOT, "build_v8_var_aplus", "blank", "HP04F_prirez.svg")
        part, title, R, blank = "HP04", "A+ · ZAKRIVENÉ SKLO R180", 180, "92,5 × 60 mm, rohy R16"
        mould = "konvexná forma R178 (vnútorný polomer skla): 6 rebier z MDF 18 mm podľa šablóny 1:1, hladký povrch (HDF / teflónová fólia)"
    else:
        svg = os.path.join(ROOT, "build_v8_var_b", "HB03F_blank.svg")
        part, title, R, blank = "HB03", "B · VIZOR R100", 100, "99 × 60 mm, rohy R25 hore / R12 dole"
        mould = "vypuklá forma R100: kus PVC rúry KG DN200 (Ø200) alebo 5 rebier z MDF podľa HB03_mould_rib.dxf, obalené bavlnou"
    rd = MS.render(dict(parts=[part], res=[900, 700], samples=max(24, q["samples"] // 2), shadow=False,
                        views=["iso", "top"], internal=True), f"22_{part}")
    W, H = 3000, 1900
    sh, d = MS.new_sheet(W, H, f"NOVA mini / VÝROBA SKLA – {title}",
                         "dymový liaty akryl (PMMA) 2 mm · ohyb len v jednom smere (valec) · mŕtvy predok: vypnuté lesklo čierne, oči svietia cez sklo")
    png = "/tmp/claude-0/glass_blank.png"
    try:
        cairosvg.svg2png(url=svg, write_to=png, output_width=1300, background_color="white")
        bl = Image.open(png).convert("RGBA")
        MS.paste_fit(sh, bl, (60, 220, 1400, 1300))
        d.text((60, 205), "PRÍREZ NA LASER (výkres 1:1 je v SVG/DXF)", fill=S.MUTED, font=S.font(26, "SemiBold"), anchor="ls")
    except Exception as e:  # noqa: BLE001
        d.text((60, 400), f"výkres prírezu: {os.path.basename(svg)} ({e})", fill=S.INK, font=S.font(26, "Medium"))
    MS.paste_fit(sh, MS.load(rd, "iso", fade=None), (1460, 220, 2240, 900))
    MS.paste_fit(sh, MS.load(rd, "top", fade=None), (2260, 220, 2960, 900))
    d.text((1460, 205), "OHNUTÉ SKLO", fill=S.MUTED, font=S.font(26, "SemiBold"), anchor="ls")
    d.text((2260, 205), "ZHORA (polomer ohybu)", fill=S.MUTED, font=S.font(26, "SemiBold"), anchor="ls")
    steps = [
        ("Materiál", "liaty dymový akryl 2 mm, priepustnosť 25–40 % („smoke grey cast acrylic“, AliExpress) · alt.: PC 0,75–1 mm ohnutý za studena"),
        ("Prírez", f"{blank} – vyrezať laserom (miestna laserovňa alebo AliExpress „custom laser cut acrylic“)"),
        ("Forma", mould),
        ("Ohyb", f"stiahnuť fóliu · rúra 150–160 °C 4–10 min · položiť na formu R{R - 2} · pritlačiť cez látku · 10 min chladnúť na forme"),
        ("Maska", "po ohnutí zvnútra čierna vinylová fólia alebo sprej, okno displeja a otvor kamery prekryté šablónou"),
        ("Montáž", "obojstranná páska VHB / 0,2 mm PSA do lôžka · najprv 1 skúšobný kus (extrudovaný akryl sa zmršťuje)"),
    ]
    for k, (a, b) in enumerate(steps):
        y = 1000 + k * 140
        d.text((1460, y), f"{k + 1}. {a.upper()}", fill=S.ACCENT, font=S.font(26, "Bold"))
        # wrap b
        words, line, yy = b.split(" "), "", y + 40
        for w_ in words:
            cand = (line + " " + w_).strip()
            if d.textlength(cand, font=S.font(25, "Medium")) > 1480:
                d.text((1460, yy), line, fill=S.INK, font=S.font(25, "Medium"))
                line, yy = w_, yy + 32
            else:
                line = cand
        d.text((1460, yy), line, fill=S.INK, font=S.font(25, "Medium"))
    MS.footer(d, W, H)
    sh.save(os.path.join(MS.OUT, f"22_NOVA_mini_vyroba_skla_{v}.png"), optimize=True)


def sheet_compare_v8(q, tmp):
    """A / A+ / B side by side on the same body (uses the per-variant hero + six-view renders, renders them if missing)."""
    W, H = 3600, 2400
    out_dir("")
    sh, d = MS.new_sheet(W, H, "NOVA mini / TRI VARIANTY HLAVY",
                         f"rovnaké telo {S8.VERSION}: skryté kolesá, otočný trup, podsvietenie 360° · výška {S8.HEAD['z1']:.0f} mm"
                         " · ESP32-S3 + 3.5\" 480×320 · krycie sklo = dymový akryl (mŕtvy predok)")
    cols = [("A", "A · PLOCHÉ SKLO", "čierny rám, ploché sklo 92×60 · najlacnejšie a najjednoduchšie",
             "laserom vyrezaný dymový akryl 2 mm, nalepený na displej (OCA)"),
            ("Aplus", "A+ · JEMNE ZAKRIVENÉ R180", "rám ostáva, sklo sa jemne vydúva · moderné, stále jednoduché",
             "prírez 92.5×60 R16, ohyb v rúre 150–160 °C na MDF forme R178"),
            ("B", "B · VIZOR BEZ RÁMU R100", "zapustený vizor cez celé čelo · najmodernejší vzhľad",
             "prírez 99×60, ohyb na PVC rúre KG DN200 alebo MDF rebrách R100")]
    cw = (W - 120) // 3
    reuse0, MS.REUSE = MS.REUSE, True       # the per-variant runs already rendered these views
    for i, (v, lab, desc, mfg) in enumerate(cols):
        install(v, tmp)
        x0 = 60 + i * cw
        rd_h = MS.render(dict(res=list(q["resp"]), samples=q["samples"] + 16, lens=70,
                              views=[HERO_CAM, "iso_back", "iso_r"], margin=0.12, floor_z=0.0), "00_hero")
        rd_6 = MS.render(dict(res=list(q["res6"]), samples=q["samples"], views=MS.SIX, internal=True, exposure=MS.EXPO6),
                         "01_NOVA_mini_celok_6_pohladov")
        d.text((x0 + 10, 200), lab, fill=S.INK, font=S.font(44, "Bold"))
        d.text((x0 + 10, 260), desc, fill=S.MUTED, font=S.font(24, "Medium"))
        d.text((x0 + 10, 296), mfg, fill=S.ACCENT, font=S.font(23, "SemiBold"))
        hero = MS.load(rd_h, "hero", fade=None)
        bx = MS.alpha_bbox(hero, 220)
        pw, ph = int(0.18 * (bx[2] - bx[0])), int(0.06 * (bx[3] - bx[1]))
        hero = hero.crop((max(0, bx[0] - pw), max(0, bx[1] - ph), min(hero.width, bx[2] + pw), min(hero.height, bx[3] + ph)))
        MS.paste_fit(sh, MS.radial_fade(hero, inner=0.74), (x0, 350, x0 + cw - 20, 1600))
        for k, vv in enumerate(["front", "right"]):
            im = MS.load(rd_6, vv, fade=None)
            b2 = MS.alpha_bbox(im, 60)
            im = im.crop((max(0, b2[0] - 15), max(0, b2[1] - 15), min(im.width, b2[2] + 15), min(im.height, b2[3] + 15)))
            bxx = (x0 + 20 + k * (cw // 2), 1680, x0 + (k + 1) * (cw // 2) - 20, 2280)
            MS.paste_fit(sh, im, bxx)
            d.text(((bxx[0] + bxx[2]) / 2, 1660), "SPREDU" if vv == "front" else "BOK (−X)", fill=S.MUTED,
                   font=S.font(22, "SemiBold"), anchor="mb")
        if i:
            d.line([(x0 - 10, 200), (x0 - 10, 2290)], fill=S.LINE, width=3)
    d.text((W - 60, H - 36), f"NOVA mini {S8.VERSION} · render z CAD modelu (build123d → Blender Cycles) · varianty hlavy na porovnanie",
           fill=S.MUTED, font=S.font(22, "Medium"), anchor="rs")
    MS.REUSE = reuse0
    out = os.path.join(OUT_ROOT["dir"], "00_NOVA_mini_porovnanie_hlav.png")
    sh.save(out, optimize=True)
    return out


# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quality", default="draft")
    ap.add_argument("--only", default="spol,A,Aplus,B")
    ap.add_argument("--reuse", action="store_true")
    a = ap.parse_args()
    MS.REUSE = a.reuse
    q = MS.Q[a.quality]
    tmp = f"/tmp/claude-0/v8_renders_{a.quality}"
    if a.quality != "final":
        OUT_ROOT["dir"] = f"/tmp/claude-0/v8_sheets_{a.quality}"
    todo = a.only.split(",")
    jobs = []
    if "spol" in todo:
        def shared():
            install("A", tmp)
            out_dir("spolocne")
            recs = MS.manifest()
            B, T, A = S8.BASE, S8.TORSO, S8.ARM
            ext = lambda sub: [r["id"] for r in recs if r["sub"] == sub and not r.get("internal")]  # noqa: E731
            steps = [
                lambda: MS.sheet_dims(q, recs),
                lambda: MS.sheet_section(q, recs),
                lambda: MS.sheet_xray(q, recs),
                lambda: sheet_kin_v8(q, recs),
                lambda: MS.sheet_six("09_NOVA_mini_krk", "NOVA mini / KRK", ext("neck"), q, recs,
                                     subtitle=f"N01 golier · N02 kužeľ · N06 valec náklonu · os náklonu z = {S8.NECK['tilt_axis']['z']:.0f}"
                                              " · s ložiskom 6805, servom otáčania IN01 (modré) a ozubením náklonu 1:1"),
                lambda: MS.sheet_six("11_NOVA_mini_trup", "NOVA mini / TRUP", ext("torso"), q, recs,
                                     subtitle=f"{T['w']:.0f} × {T['d']:.0f} × {T['z1'] - T['z0']:.0f} mm · T01 predná škrupina · T02 zadná škrupina = servisný kryt"
                                              " na skrytých magnetoch · T04 otočný tanier · T05 dymový pás hrude"),
                lambda: MS.sheet_matrix("12_NOVA_mini_diely_trupu", "NOVA mini / DIELY TRUPU A KRKU",
                                        auto_rows(recs, ("torso", "neck"), skip=("T06",), attach={"T05": ["T06"]},
                                                  short={"T05": "dymový akrylát 2 mm", "T02": "servisný kryt, magnety"}),
                                        q, recs, subtitle="všetky riadky v rovnakej mierke"),
                lambda: MS.sheet_six("13_NOVA_mini_ruky", "NOVA mini / RUKY",
                                     ext("arm_R"), q, recs,
                                     subtitle=f"pravá ruka (−X), ľavá zrkadlovo · A01–A05 · os ramena z = {A['axis']['z']:.0f}"
                                              f" · rozpaženie {A['abduction_deg']:g}° · servo IT05 v trupe"),
                lambda: MS.sheet_matrix("15_NOVA_mini_diely_ruky", "NOVA mini / DIELY RUKY", [
                    ("A01 Vonkajšia škrupina", ["A01-R"], "biela"), ("A02 Vnútorná škrupina", ["A02-R"], "biela"),
                    ("A03 Špička", ["A03-R"], "čierne TPU"), ("A04 Spojka kĺbu", ["A04-R"], "čierna"),
                    ("A05 Krúžok ramena", ["A05-R"], "čierny")], q, recs, subtitle="pravá ruka, ľavá zrkadlovo · rovnaká mierka"),
                lambda: MS.sheet_six("17_NOVA_mini_zakladna", "NOVA mini / ZÁKLADŇA (SKRYTÉ KOLESÁ)", ext("base"), q, recs,
                                     subtitle=f"{B['w']:.0f} × {B['d']:.0f} × {B['z1']:.0f} mm · kolesá, senzory, USB-C a nabíjanie zospodu · podsvietenie 360°"),
                lambda: MS.sheet_matrix("18_NOVA_mini_diely_zakladne", "NOVA mini / DIELY ZÁKLADNE", [
                    ("B01 Horný kryt", ["B01"], "biely, uzavretý"), ("B02 Spodná vanička", ["B02"], "čierna"),
                    ("B-UG Podsvietenie 360°", ["B-UG"], "opálový svetlovod"),
                    ("B04/B05 Koleso", ["B04-R", "B05-R"], "Ø34, N20"), ("B11 Poklopy batérie", ["B11-1", "B11-2"], "bez náradia"),
                    ("B06/B07 Guľové kolieska", ["B06", "B07"], "Ø12")], q, recs, subtitle="rovnaká mierka"),
                lambda: sheet_internals_v8(q, recs),
                lambda: MS.sheet_expressions(q, recs),
            ]
            for st in steps:
                try:
                    print("->", st(), flush=True)
                except Exception as e:  # noqa: BLE001
                    import traceback
                    traceback.print_exc()
                    print("FAILED", e, flush=True)
        jobs.append(shared)
    for v in ("A", "Aplus", "B"):
        if v not in todo:
            continue

        def per_variant(v=v):
            install(v, tmp)
            out_dir(VAR[v]["dir"])
            recs = MS.manifest()
            hsub = VAR[v]["sub"]
            head_ext = [r["id"] for r in recs if r["sub"] == hsub and not r.get("internal")]
            steps = [
                lambda: sheet_hero_v8(q, recs),
                lambda: MS.sheet_six("01_NOVA_mini_celok_6_pohladov", f"NOVA mini / CELOK – HLAVA {v.replace('plus', '+')}", None, q, recs,
                                     subtitle=f"výška {S8.HEAD['z1']:.0f} mm · základňa {S8.BASE['w']:.0f}×{S8.BASE['d']:.0f} mm · kolesá skryté · hlava {VAR[v]['label']}"),
                lambda: MS.sheet_exploded(q, recs),
                lambda: MS.sheet_six("07_NOVA_mini_hlava", f"NOVA mini / HLAVA {v.replace('plus', '+')}", head_ext, q, recs,
                                     subtitle=VAR[v]["label"]),
                lambda: MS.sheet_matrix("08_NOVA_mini_diely_hlavy", f"NOVA mini / DIELY HLAVY {v.replace('plus', '+')}",
                                        head_rows(v), q, recs, subtitle="rovnaká mierka"),
            ]
            if v in ("Aplus", "B"):
                steps.append(lambda: sheet_glass(q, recs))
            for st in steps:
                try:
                    print("->", st(), flush=True)
                except Exception as e:  # noqa: BLE001
                    import traceback
                    traceback.print_exc()
                    print("FAILED", e, flush=True)
        jobs.append(per_variant)
    if "cmp" in todo:
        jobs.append(lambda: print("->", sheet_compare_v8(q, tmp), flush=True))
    for j in jobs:
        j()
    print("done")


if __name__ == "__main__":
    main()
