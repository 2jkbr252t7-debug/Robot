"""NOVA mini - arm drive v2: labelled Slovak sheets from the renders of v2_scene.py.
Usage: /opt/venv/cad/bin/python v2_sheets.py <render_dir> <out_dir> [spredu rez vnutro rozlozene hero]"""
import sys, os, json, math
import numpy as np
from PIL import Image, ImageDraw
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R1/img_v1/work")
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T4")
import g2 as G
import t4_common as C
from sheetlib import (font, feather, dashed, dim_h, place, badge, arrow_head, BG, INK, MUTED, ACCENT, DIM)

V = G.V
D, OUT = sys.argv[1], sys.argv[2]
ONLY = sys.argv[3:]
os.makedirs(OUT, exist_ok=True)
fTitle, fSub, fPan, fLab, fSmall, fDim, fNum = font(50), font(26, "Regular"), font(32), font(25, "Medium"), font(22, "Regular"), font(26, "SemiBold"), font(21)
NUMS = json.load(open(os.path.join(HERE, "nums.json")))
GREEN = (30, 150, 80)
ORANGE = (235, 120, 20)


def sk(v, nd=1):
    return f"{v:.{nd}f}".replace(".", ",")


class Cam:
    def __init__(self, path):
        d = json.load(open(path))
        self.d = d
        self.W, self.H = d["res"]
        self.Mcw = np.array(d["matrix"])
        self.Mwc = np.linalg.inv(self.Mcw)
        self.extra = d.get("extra", {})

    def px(self, p):
        p = np.asarray(p, float)
        q = self.Mwc[:3, :3] @ p + self.Mwc[:3, 3]
        if self.d["type"] == "ORTHO":
            k = self.W / self.d["ortho_scale"]
            return (self.W / 2 + q[0] * k, self.H / 2 - q[1] * k)
        if self.d.get("sensor_fit") == "VERTICAL":
            f = self.d["lens"] / self.d["sensor_height"] * self.H
        else:
            f = self.d["lens"] / self.d["sensor_width"] * self.W
        return (self.W / 2 + f * q[0] / -q[2], self.H / 2 - f * q[1] / -q[2])

    def k(self):
        return self.W / self.d["ortho_scale"]


def load(name):
    return Image.open(os.path.join(D, name + ".png")).convert("RGBA")


def header(d, title, intro, x=44, y=34):
    d.text((x, y), title, font=fTitle, fill=INK)
    d.multiline_text((x, y + 76), intro, font=fSub, fill=MUTED, spacing=10)
    return y + 76 + (intro.count("\n") + 1) * 37 + 20


def note(d, xy, text, anchor, fnt=fLab, color=ACCENT, box=True, fill=INK):
    x, y = xy
    lines = text.split("\n")
    w = max(d.textlength(t, font=fnt) for t in lines)
    h = len(lines) * (fnt.size + 8)
    if box:
        d.rounded_rectangle([x - 8, y - 6, x + w + 8, y + h + 2], 6, fill=(255, 255, 255))
    d.multiline_text((x, y), text, font=fnt, fill=fill, spacing=8)
    if anchor is not None:
        ax, ay = anchor
        sx = x - 8 if ax < x else (x + w + 8 if ax > x + w else ax)
        sy = y + h / 2 if (ax < x or ax > x + w) else (y - 6 if ay < y else y + h + 2)
        d.line([(sx, sy), (ax, ay)], fill=color, width=3)
        d.ellipse([ax - 6, ay - 6, ax + 6, ay + 6], fill=color, outline=(255, 255, 255), width=2)
    return (x - 8, y - 6, x + w + 8, y + h + 2)


def text_w(t, f):
    return ImageDraw.Draw(Image.new("RGB", (4, 4))).textlength(t, font=f)


def footer_block(d, x, y, text, fnt=None, fill=MUTED, spacing=9):
    fnt = fnt or fSmall
    d.multiline_text((x, y), text, font=fnt, fill=fill, spacing=spacing)
    return y + (text.count("\n") + 1) * (fnt.size + spacing)


V_Z_FLOOR = -116.5


# ================================================================================================ 1 front
def sheet_spredu():
    im = load("front")
    cam = Cam(os.path.join(D, "front_cam.json"))
    k = cam.k()
    W0, H0 = im.size
    crop_w = int(2 * 106 * k)
    cx0 = int(W0 / 2 - crop_w / 2)
    ytop = int(cam.px((0, 0, 92.0))[1]); ybot = int(cam.px((0, 0, V_Z_FLOOR - 2))[1])
    pan = im.crop((cx0, ytop, cx0 + crop_w, ybot))
    PW, PH = pan.size
    det = load("detail")
    dcam = Cam(os.path.join(D, "detail_cam.json"))
    DW, DH = det.size
    dscale = 0.88
    det_s = det.resize((int(DW * dscale), int(DH * dscale)), Image.LANCZOS)
    title = "NOVA mini · ruky v2: pohľad spredu"
    intro = ("Pravouhlý pohľad spredu. Obe servá rúk sú vnútri trupu, ruky sú pasívne biele škrupiny bez elektroniky.\n"
             "Ruka je o 1,0 mm bližšie k trupu než v schválenom tvare. Z kĺbu je vidieť len čierny krúžok Ø13 – zátka v boku je zapustená.")
    colgap = 90
    W = max(PW + det_s.width + colgap + 160, int(text_w(intro.split("\n")[1], fSub)) + 120)
    top = 34 + 76 + 2 * 37 + 40
    H = top + 40 + max(PH + 240, det_s.height + 30 + 330) + 110
    S = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(S)
    header(d, title, intro)
    x0 = 60; yp = top + 40
    d.rounded_rectangle([x0 - 14, yp - 30, x0 + PW + 14, yp + PH + 230], 14, fill=(250, 250, 248), outline=(222, 222, 218), width=2)
    S.paste(pan, (x0, yp), pan)

    def P(p):
        u, v = cam.px(p)
        return (x0 + u - cx0, yp + v - ytop)
    xa = NUMS["xmax_dx-1.0"]
    yfl = P((0, 0, V_Z_FLOOR))[1]
    bl, br = P((-73.0, 0, -100.0)), P((73.0, 0, -100.0))
    dim_h(d, bl[0], br[0], yfl + 55, "podstavec 146 mm – zatiaľ len tvar", fDim, fill=MUTED, ext=[(bl[0], bl[1] + 20), (br[0], br[1] + 20)], text_above=False)
    rows, _, _ = V.pebble_rows(120, 160)
    Wp = V.to_world(rows.reshape(-1, 3), G.DX)
    i = int(np.argmax(Wp[:, 0])); za = float(Wp[i, 2])
    al, ar = P((-xa, 0, za)), P((xa, 0, za))
    dim_h(d, al[0], ar[0], yfl + 150, f"celková šírka {sk(2 * xa, 0)} mm  (schválený tvar {sk(2 * NUMS['xmax_dx0.0'], 0)} mm)", fDim, fill=DIM,
          ext=[(al[0], al[1] + 12), (ar[0], ar[1] + 12)], text_above=False)
    # detail frame on the left shoulder (robot left = image right)
    dx0, dz0, half = 48.0, -17.0, 22.0
    f0, f1 = P((dx0 - half, 0, dz0 + half)), P((dx0 + half, 0, dz0 - half))
    d.rectangle([f0[0], f0[1], f1[0], f1[1]], outline=ACCENT, width=3)
    # detail panel
    px0 = x0 + PW + colgap; py0 = yp
    d.rounded_rectangle([px0 - 14, py0 - 30, px0 + det_s.width + 14, py0 + det_s.height + 330], 14, fill=(250, 250, 248), outline=(222, 222, 218), width=2)
    zoom = dcam.k() * dscale / k
    d.text((px0 + 6, py0 - 22), f"detail ľavého ramena ({sk(zoom)} × väčšie)", font=fPan, fill=INK)
    py0 += 30
    bgd = Image.new("RGBA", det_s.size, (255, 255, 255, 255)); bgd.alpha_composite(det_s)
    S.paste(bgd, (px0, py0))
    d.rectangle([px0, py0, px0 + det_s.width, py0 + det_s.height], outline=ACCENT, width=3)
    d.line([(f1[0], f0[1]), (px0, py0)], fill=ACCENT, width=2)
    d.line([(f1[0], f1[1]), (px0, py0 + det_s.height)], fill=ACCENT, width=2)

    def DP(p):
        u, v = dcam.px(p)
        return (px0 + u * dscale, py0 + v * dscale)
    gz, gxa, gxt, gg = NUMS["front_gap_dx-1.0"]
    pa, pb = DP((gxt, 0, gz)), DP((gxa, 0, gz))
    yy = pa[1] - 58
    for q in (pa, pb):
        d.line([(q[0], q[1] - 6), (q[0], yy - 10)], fill=DIM, width=2)
    d.line([(pa[0] - 60, yy), (pa[0], yy)], fill=DIM, width=3); arrow_head(d, (pa[0], yy), (pa[0] - 60, yy), DIM)
    d.line([(pb[0], yy), (pb[0] + 60, yy)], fill=DIM, width=3); arrow_head(d, (pb[0], yy), (pb[0] + 60, yy), DIM)
    t = f"{sk(gg)} mm"
    d.rounded_rectangle([pb[0] + 66, yy - 20, pb[0] + 76 + text_w(t, fDim), yy + 18], 5, fill=(255, 255, 255))
    d.text((pb[0] + 70, yy - 17), t, font=fDim, fill=DIM)
    ring = DP((47.8, 0, -17.0))
    note(d, (px0 + det_s.width * 0.52, py0 + det_s.height * 0.70), "čierny krúžok Ø13\n(jediné, čo z kĺbu vidno)", ring, fSmall)
    note(d, (px0 + 24, py0 + 24), "bočný kryt trupu\n(bez zmeny)", DP((38.0, 0, -5.0)), fSmall)
    note(d, (px0 + det_s.width - 250, py0 + 24), "ruka (pasívna,\nbez elektroniky)", DP((62.0, 0, -6.0)), fSmall)
    txt = (f"Medzera ruka – trup (ľavá aj pravá ruka rovnako):\n"
           f"• v tomto pohľade spredu {sk(gg)} mm (schválený tvar {sk(NUMS['front_gap_dx0.0'][3])} mm),\n"
           f"• najmenšia skutočná vzdialenosť v pokoji 3,7 mm (T4: 4,7 mm),\n"
           f"• pri pohybe ruky −45° … +135° nikde menej ako 1,0 mm\n  (najtesnejšie pri +135°, ruka hore vpredu).\n"
           f"Bližšie k trupu už nie: každý ďalší milimeter\nby ruke ubral asi 13° pohybu nahor.")
    footer_block(d, px0, py0 + det_s.height + 28, txt, fSmall, INK, 10)
    foot = ("Koncept na posúdenie, nie výkres na tlač. Tvar bielej ruky aj trupu je schválený (T3 / T4) a nemení sa; ruka je len posunutá o 1,0 mm k trupu.\n"
            "Hlava v strednej polohe (otočenie 0°, zdvih 0). Rozmery v mm.")
    yfoot = max(yp + PH + 240, py0 + det_s.height + 340)
    footer_block(d, 44, yfoot, foot)
    S = S.crop((0, 0, W, int(min(H, yfoot + 90))))
    S.save(os.path.join(OUT, "v2_spredu.png"), optimize=True)
    print("spredu", S.size)


# ================================================================================================ 2 section
def xs_in(z, inset=1.0):
    return C.x_surface(G.YA, z) - inset


def sheet_rez():
    im = load("rez")
    cam = Cam(os.path.join(D, "rez_cam.json"))
    k = cam.k()
    IW, IH = im.size
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
    do = ImageDraw.Draw(ov)
    P = lambda x, z: cam.px((x, G.YA, z))
    # lift / neck sweep boundary in the plane y = 3
    pts = []
    for z0, z1, r in G.PAN_ENV2:
        x = G.sweep_x(r)
        pts += [P(x, max(z0, -84)), P(x, min(z1, 3))]
    pts = [p for p in pts if 0 <= p[1] <= IH]
    zone = [(18.0, -41.9), (G.sweep_x(26.5), -41.9), (G.sweep_x(26.5), -40.9), (G.sweep_x(33.4), -40.9), (G.sweep_x(33.4), -17.0),
            (G.sweep_x(32.2), -17.0), (G.sweep_x(32.2), -11.5), (G.sweep_x(26.5), -11.5), (G.sweep_x(26.5), 3.0), (18.0, 3.0)]
    zl = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(zl).polygon([P(x, z) for x, z in zone], fill=ORANGE + (46,))
    im.alpha_composite(zl)
    dashed(do, pts, ORANGE + (255,), width=4, dash=14, gap=8)
    # shoulder axis + vertical drive axis (dash-dot)
    dashed(do, [P(18.5, G.ZA), P(83.5, G.ZA)], (40, 40, 40, 170), width=2, dash=22, gap=6)
    dashed(do, [P(G.XV, -70.0), P(G.XV, -6.0)], (40, 40, 40, 170), width=2, dash=22, gap=6)
    # clearance column <-> sweep
    zc = -36.0
    xa, xb = G.sweep_x(33.4), 34.4
    pa, pb = P(xa, zc), P(xb, zc)
    do.line([(pa[0] - 50, pa[1]), pa], fill=DIM + (255,), width=3); arrow_head(do, pa, (pa[0] - 50, pa[1]), DIM + (255,))
    do.line([pb, (pb[0] + 50, pb[1])], fill=DIM + (255,), width=3); arrow_head(do, pb, (pb[0] + 50, pb[1]), DIM + (255,))
    im.alpha_composite(ov)
    xin = lambda z: V.skins(G.YA, z, 0.0, G.DX)[0]
    xout = lambda z: V.skins(G.YA, z, 0.0, G.DX)[1]
    zseam = -60.0
    xs_seam = V.x_at_local_x(G.YA, zseam, 0.0, G.DX)
    Lft = [
        ((36.8, -8.0), "skrutka M2 do mosadznej vložky (3×)"),
        ((42.7, -11.2), "kužeľové koleso 24 z (prevod 1,5 : 1)"),
        ((36.4, -13.0), "nový stĺp – časť dna trupu T_spodok\n(1,0 mm od otáčajúceho sa krku)"),
        ((35.3, -22.1), "kužeľový pastorok 16 z (m 0,5, mosadz)"),
        ((41.3, -25.1), "ložisko MR63 v jazýčku stĺpa"),
        ((30.0, -30.0), "priestor, kde sa otáča krk a servo\nzdvihu pri otáčaní hlavy (oranžovo)"),
        ((39.0, -33.0), "zvislý hriadeľ Ø3 (oceľ)"),
        ((41.4, -40.0), "spojka na výstupe serva\n(páka + mosadzné puzdro)"),
        ((37.0, -56.0), "servo Feetech SCS0009 stojí,\nvýstup hore (os x 39)"),
        ((31.6, -60.0), "stena kapsy serva"),
        ((38.0, -67.9), "podložka + PORON pod servom"),
        ((28.0, -75.4), "menič napätia (presunutý na dno)"),
    ]
    Rgt = [
        ((56.0, -7.6), "náboj ruky"),
        ((55.5, -10.8), "ložisko 6700 – na ňom sa točí ruka"),
        ((51.0, -22.6), "čierny krúžok Ø13 – cez medzeru 3,9 mm"),
        ((54.5, -17.0), "hriadeľ ruky Ø4 (oceľ)"),
        ((59.95, -13.6), "trecia spojka: podložky + tanierová\npružina + skrutka M2 (0,06 N·m)"),
        ((49.8, -19.8), "2× ložisko MR74 (4 × 7 × 2,5) v zátke"),
        ((46.4, -27.0), "čierna zátka (nová, namiesto T_klb),\nčelo 1 mm pod povrchom trupu"),
        ((xout(-36.0) - 0.8, -36.0), "vonkajší kryt ruky (drží na magnetoch)"),
        ((xin(-40.0) + 0.8, -40.0), "vnútorná škrupina ruky (nosná)"),
        ((xs_in(-52.0, 1.1), -52.0), "bočný kryt trupu T_bok\n(biely, zvonka bez zmeny)"),
        ((xs_seam, zseam), "šev 0,5"),
    ]
    colw = 610
    W = IW + 2 * colw
    title = "NOVA mini · ruky v2: rez ľavým ramenom"
    intro = ("Rez zvislou rovinou cez os ramena a cez os serva (y = 3), pohľad spredu; ľavá strana robota je vpravo. Pravé rameno je zrkadlové.\n"
             "Servo stojí v trupe pod ramenom. Jeho výstup otáča zvislým hriadeľom a jediným tichým kužeľovým párom hriadeľom ruky.\n"
             "Ruka je pasívna, točí sa na ložisku 6700 nasadenom na čiernom krúžku zátky; hriadeľ ju len otáča cez treciu spojku.\n"
             "Farba rezu: oranžová = biela živica · modrá = čierna živica · fialová = servo · zlatá = mosadz · sivá = oceľ.")
    top = 34 + 76 + 4 * 37 + 40
    foot = ("Prečo nie servo priamo na osi ruky (bez kolies): na osi je od otáčajúceho sa krku (+1 mm vôľa, x 34,3) po povrch trupu (x 46,8) len 12,5 mm,\n"
            "servo SCS0009 potrebuje pozdĺž hriadeľa ~25 mm (telo 21,5 + výstup 3,75) → trčalo by 9 mm z trupu a ruka by musela ísť o 8–12 mm ďalej.\n"
            "Prevod 1,5 : 1 – servo 300° dá ruke 200° (treba 180°: −45° … +135°), presnosť 0,2°. Mazaný mosadzný pár sa točí pomaly, je tichší ako vlastná prevodovka serva.\n"
            "Ruka potrebuje 0,004 N·m; spojka prekĺzne pri 0,06 N·m (1,2 N na konci ruky) – chráni zuby aj servo pred zatlačením rukou.\n"
            "Koncept, nie výkres na tlač. Výška tela serva 21,5 mm je neoverená (zmestí sa aj 25,25 mm).")
    H = top + IH + 30 + 5 * 32 + 40
    S = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(S)
    header(d, title, intro)
    ix0, yi = colw, top
    bgi = Image.new("RGBA", im.size, (255, 255, 255, 255)); bgi.alpha_composite(im)
    S.paste(bgi, (ix0, yi))
    d.rectangle([ix0, yi, ix0 + IW - 1, yi + IH - 1], outline=(215, 215, 210), width=2)
    # clearance text next to the arrows
    pa = cam.px((G.sweep_x(33.4), G.YA, -36.0))
    t = "≥ 1,0"
    d.rounded_rectangle([ix0 + pa[0] - 62 - text_w(t, fDim), yi + pa[1] - 20, ix0 + pa[0] - 52, yi + pa[1] + 18], 5, fill=(255, 255, 255))
    d.text((ix0 + pa[0] - 57 - text_w(t, fDim), yi + pa[1] - 17), t, font=fDim, fill=DIM)
    sides = {"L": [], "R": []}
    for (x, z), txt in Lft:
        u, v = cam.px((x, G.YA, z)); sides["L"].append([min(max(v, 4), IH - 4), min(max(u, 4), IW - 4), txt])
    for (x, z), txt in Rgt:
        u, v = cam.px((x, G.YA, z)); sides["R"].append([min(max(v, 4), IH - 4), min(max(u, 4), IW - 4), txt])
    place(d, sides["L"], "L", 0, colw, yi, IH, ix0, fLab, LH=30, gap=14)
    place(d, sides["R"], "R", colw + IW, colw, yi, IH, ix0, fLab, LH=30, gap=14)
    footer_block(d, 44, yi + IH + 26, foot)
    S.save(os.path.join(OUT, "v2_rez_ramenom.png"), optimize=True)
    print("rez", S.size)


# ================================================================================================ 3 cut-away
def sheet_vnutro():
    im = load("vnutro")
    cam = Cam(os.path.join(D, "vnutro_cam.json"))
    IW, IH = im.size
    gd = cam.extra.get("pan_ghost", [-61, 33.4])
    title = "NOVA mini · ruky v2: kde je servo v trupe"
    intro = ("Pohľad zľava spredu zhora. Nie je zobrazený ľavý bočný kryt, predná časť stredného pásu trupu, hlava s krkom ani ľavá ruka.\n"
             "Servo ľavej ruky stojí v novom stĺpe pri boku trupu, hneď vedľa otáčania hlavy. Pravá strana je zrkadlová (za šachtou krku).\n"
             f"Otáčanie hlavy je v polohe 0°; oranžovo priesvitne je servo zdvihu v polohe najbližšie k stĺpu (hlava otočená o {sk(abs(gd[0]), 0)}°).")
    colw = 560
    W = IW + 2 * colw
    top = 34 + 76 + 3 * 37 + 40
    H = top + IH + 200
    S = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(S)
    header(d, title, intro)
    ix0, yi = colw, top
    S.paste(im, (ix0, yi), im)

    AN = cam.extra["anchors"]

    def pp(k):
        u, v = AN[k]
        return [min(max(v, 4), IH - 4), min(max(u, 4), IW - 4)]
    R = [pp("boss") + ["nový stĺp (časť dna trupu T_spodok)"],
         pp("zatka") + ["čierna zátka (ruka je zložená)"],
         pp("kruzok") + ["krúžok Ø13 – na ňom sa točí ruka"],
         pp("spojka") + ["spojka + zvislý hriadeľ\nk ozubeniu v zátke"],
         pp("vzpera") + ["vzpera stĺpa"],
         pp("servo") + ["servo ľavej ruky SCS0009\n(stojí, výstup hore)"],
         pp("noha") + ["predná noha stĺpa\n(drážka pre kábel serva)"],
         pp("menic") + ["menič napätia\n(presunutý na dno)"]]
    Lf = [pp("sachta") + ["šachta krku – otáčanie hlavy\n(poloha 0°)"],
          pp("bokP") + ["pravá ruka (za trupom)"],
          pp("duch") + [f"servo zdvihu v najbližšej\npolohe (hlava −{sk(abs(gd[0]), 0)}°):\nod stĺpa 1,0 mm"],
          pp("paluba") + ["paluba (okraj vľavo orezaný)"],
          pp("servo_pan") + ["servo otáčania hlavy"]]
    place(d, Lf, "L", 0, colw, yi, IH, ix0, fLab, LH=30, gap=18)
    place(d, R, "R", colw + IW, colw, yi, IH, ix0, fLab, LH=30, gap=18)
    foot = ("Pohyblivé časti krku (otáčanie ±90°, zdvih 0–20 mm) ostávajú bez zmeny; nový stĺp je od ich dráhy vždy aspoň 1,0 mm (vľavo 1,02, vpravo 1,40 mm).\n"
            "Kábel serva ostáva pevne v trupe (nič neprechádza kĺbom): z drážky v prednej nohe dole po stĺpe k rozbočke J_BUS_5 na doske riadenia.\n"
            "Výmena serva asi za 10 minút: kryt ruky, skrutka, ruka dole → zátka von → bočný kryt dole → povoliť spojku → servo zboku von. Krk ani hlava sa nerozoberajú.")
    footer_block(d, 44, yi + IH + 30, foot)
    S.save(os.path.join(OUT, "v2_vnutro_trupu.png"), optimize=True)
    print("vnutro", S.size)


# ================================================================================================ 4 exploded
def sheet_rozlozene():
    im = load("rozlozene")
    cam = Cam(os.path.join(D, "rozlozene_cam.json"))
    IW, IH = im.size
    off = cam.extra["off"]; arm = cam.extra["arm"]

    def at(name, p):
        o = off.get(name, [0, 0])
        return cam.px((p[0] + o[0], p[1], p[2] + o[1]))

    def at_arm(key, p):
        return cam.px((p[0] + arm[key], p[1], p[2]))
    ya, za = G.YA, G.ZA
    AN = cam.extra["anchors"]
    items = [
        (AN["stlp"], "nový stĺp (časť T_spodok) s ložiskom MR63 v jazýčku", "up"),
        (AN["pastorok"], "kužeľový pastorok 16 z (lepený na hriadeľ)", "up"),
        (AN["hriadel_zvisly"], "zvislý hriadeľ Ø3 – vkladá sa zdola cez MR63", "down"),
        (AN["spojka"], "spojka: páka serva + mosadzné puzdro, skrutka M2", "down"),
        (AN["servo"], "servo SCS0009 – zasúva sa zboku do kapsy", "down"),
        (AN["koleso"], "hriadeľ ruky Ø4 s kužeľovým kolesom 24 z", "down"),
        (AN["A1"], "ložisko MR74 (A1)", "up"),
        (AN["zatka"], "čierna zátka s krúžkom Ø13 a 3 skrutkami M2", "up"),
        (AN["A2"], "ložisko MR74 (A2)", "up"),
        (AN["poistka"], "poistný krúžok", "down"),
        (AN["L6700"], "ložisko 6700 (nalisované v náboji ruky)", "up"),
        (AN["podlozka_1"], "podložka s plôškou (na osadení hriadeľa)", "down"),
        (AN["vnut"], "vnútorná škrupina ruky s nábojom a mosadznou prírubou", "down"),
        (AN["podlozka_2"], "podložka", "up"),
        (AN["pruzina"], "tanierová pružina (trecia spojka 0,06 N·m)", "down"),
        (AN["podlozka_3"], "podložka", "up"),
        (AN["skrutka_ruky"], "skrutka M2 do konca hriadeľa", "down"),
        (AN["mag_von"], "4 magnety Ø3 × 2", "up"),
        (AN["vonk"], "vonkajší kryt ruky (drží na magnetoch)", "down"),
    ]
    title = "NOVA mini · ruky v2: rozložené ľavé rameno"
    intro = ("Pohľad spredu zľava zhora. Čísla = poradie montáže. Servo a jeho hriadeľ sú v trupe pod ramenom, ozubenie je ukryté v čiernej zátke.\n"
             "Hriadeľ ruky s kolesom, ložiská MR74 a poistný krúžok sa zložia do zátky na stole (kazeta), do trupu sa zasunie celá zátka.")
    top = 34 + 76 + 2 * 37 + 30
    ncol = 2
    rows_n = math.ceil(len(items) / ncol)
    W = max(IW + 80, 1700)
    H = top + IH + 40 + rows_n * 40 + 190
    S = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(S)
    header(d, title, intro)
    ix0, yi = (W - IW) // 2, top
    S.paste(im, (ix0, yi), im)
    used = []
    for n, ((u, v), txt, dr) in enumerate(items, 1):
        sg = -1 if dr == "up" else 1
        bx, by = ix0 + u, yi + v + sg * 58
        for _ in range(30):
            if all(math.hypot(bx - qx, by - qy) > 40 for qx, qy in used):
                break
            by += sg * 30
        by = min(max(by, yi + 20), yi + IH - 20)
        d.line([(bx, by), (ix0 + u, yi + v)], fill=ACCENT, width=3)
        d.ellipse([ix0 + u - 5, yi + v - 5, ix0 + u + 5, yi + v + 5], fill=ACCENT, outline=(255, 255, 255), width=2)
        badge(d, (bx, by), n, fNum)
        used.append((bx, by))
    colw = (W - 100) // ncol
    for n, (_, txt, _) in enumerate(items, 1):
        c, r = (n - 1) // rows_n, (n - 1) % rows_n
        x, y = 50 + c * colw, yi + IH + 30 + r * 40
        badge(d, (x + 17, y + 15), n, font(19), r=17)
        d.text((x + 42, y + 2), txt, font=fLab, fill=INK)
    footer_block(d, 50, H - 150,
                 "Montáž v trupe (bočný kryt dole): 3 zdola cez MR63 → 2 nalepiť na podložku 0,5 → hriadeľ nadvihnúť → 5 so spojkou 4 zasunúť zboku\n"
                 "→ hriadeľ spustiť do spojky, dotiahnuť → bočný kryt nasadiť → zátku 8 (s 6, 7, 9, 10) zasunúť, koleso zapadne → 3 skrutky M2, vôľu nastaviť podložkami\n"
                 "→ 12, ruka 13 so 6700 (11) na krúžok → 14–17 (predpätie spojky podložkami) → kryt 19 na magnety. Pravé rameno zrkadlovo.\n"
                 "Koncept – rozmery serva neoverené; drobné skrutky a vložky nie sú všetky zobrazené.")
    S.save(os.path.join(OUT, "v2_rameno_rozlozene.png"), optimize=True)
    print("rozlozene", S.size)


# ================================================================================================ 5 hero
def sheet_hero():
    im = load("hero")
    cam = Cam(os.path.join(D, "hero_cam.json"))
    IW, IH = im.size
    W = IW + 80
    title = "NOVA mini · ruky v2"
    intro = ("Ľavá ruka zdvihnutá o 90°, hlava otočená o 20° k nej. Servá sú v trupe, ruky sú len biele škrupiny\n"
             "a sedia o 1 mm bližšie k trupu ako v schválenom tvare. Z kĺbu je vidieť iba tenký čierny krúžok.")
    top = 34 + 76 + 2 * 37 + 20
    H = top + IH + 70
    S = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(S)
    header(d, title, intro)
    ix0, yi = 40, top
    im = feather(im, 90)
    S.paste(im, (ix0, yi), im)
    u, v = cam.extra["anchors"]["zatka_L"]
    note(d, (ix0 + IW - 285, yi + IH * 0.395), "kĺb: čierny krúžok Ø13\na zapustená zátka", (ix0 + u, yi + v), fSmall)
    d.text((40, H - 50), "Koncept – podstavec je zatiaľ len tvar. Tvar trupu, hlavy aj ruky je schválený a nemení sa.", font=fSmall, fill=MUTED)
    S.save(os.path.join(OUT, "v2_hero.png"), optimize=True)
    print("hero", S.size)


if not ONLY or "spredu" in ONLY:
    sheet_spredu()
if not ONLY or "rez" in ONLY:
    sheet_rez()
if not ONLY or "vnutro" in ONLY:
    sheet_vnutro()
if not ONLY or "rozlozene" in ONLY:
    sheet_rozlozene()
if not ONLY or "hero" in ONLY:
    sheet_hero()
