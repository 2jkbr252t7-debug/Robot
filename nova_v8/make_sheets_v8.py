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
    H["display"] = dict(S8.DISPLAY, zc=S8.HEAD["zc"])
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
    return recs


_render7 = MS.render


def render_v8(job, name):
    job = dict(job)
    job.setdefault("glb_dir", BUILD)
    job.setdefault("manifest_dir", os.path.join(BUILD, "manifest"))
    v = VAR[CUR["v"]]
    if v["extra"]:
        job["extra"] = v["extra"]
        job["exclude"] = list(job.get("exclude", [])) + head_a_ids()
    job["joint_axes"] = AXES
    return _render7(job, name)


_group7 = MS.group_explode


def install(variant, quality_tmp):
    CUR["v"] = variant
    MS.spec = compat_spec()
    MS.manifest = manifest_v8
    MS.render = render_v8
    MS.group_explode = lambda recs, lift=55.0: _group7(recs, lift)
    MS.HERO_CAM = HERO_CAM
    MS.TMP = os.path.join(quality_tmp, variant)
    MS.FOOT = f"NOVA mini {S8.VERSION} · hlava {VAR[variant]['label']} · render z CAD modelu (build123d → Blender Cycles) · mm"


def out_dir(sub):
    p = os.path.join(ROOT, "obrazky", "v8", sub)
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
        ("Zmysly", "mikrofón, dotyk, IMU, ToF + svetlo v hrudi, 4 senzory proti pádu"),
        ("Svetlo", "LED krúžky v ušiach · pás v hrudi · podsvietenie stola 360°"),
        ("Mozog", "ESP32-S3 (hlava) + ESP32-C3 (trup), AI cez Wi-Fi"),
        ("Napájanie", "2× 18650, USB-C a kontakty dokovania zospodu"),
        ("Cena dielov", "~65–105 € (MG90S) · ~90–140 € (SCS0009) z AliExpressu"),
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
    ISO = {"name": "k", "loc": [420, -600, 330], "target": [0, 0, 100], "lens": 62}
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
                                     subtitle=f"N01 golier · N02 kužeľ · N06 valec náklonu · os náklonu z = {S8.NECK['tilt_axis']['z']:.0f}"),
                lambda: MS.sheet_six("11_NOVA_mini_trup", "NOVA mini / TRUP", ext("torso"), q, recs,
                                     subtitle=f"T01–T05 · {T['w']:.0f} × {T['d']:.0f} × {T['z1'] - T['z0']:.0f} mm · dymový pás hrude · dvierka na magnetoch"),
                lambda: MS.sheet_matrix("12_NOVA_mini_diely_trupu", "NOVA mini / DIELY TRUPU", [
                    ("T01 Predná škrupina", ["T01"], "biela"), ("T02 Zadná škrupina", ["T02"], "biela"),
                    ("T03 Servisné dvierka", ["T03"], "na magnetoch"), ("T04 Otočný tanier", ["T04"], "čierny, ložisko 6806"),
                    ("T05 Dymové okno hrude", ["T05"], "LED + ToF za jedným oknom"),
                    ("N01–N06 Krk", ["N01", "N02", "N06"], "golier, kužeľ, valec")], q, recs, subtitle="všetky riadky v rovnakej mierke"),
                lambda: MS.sheet_six("13_NOVA_mini_ruky", "NOVA mini / RUKY",
                                     [r["id"] for r in recs if r["sub"] in ("arm_R", "arm_L") and not r.get("internal")], q, recs,
                                     subtitle=f"A01–A05 · os ramien z = {A['axis']['z']:.0f} · rozpaženie {A['abduction_deg']:g}°"),
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
                lambda: MS.sheet_internals(q, recs),
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
    for j in jobs:
        j()
    print("done")


if __name__ == "__main__":
    main()
