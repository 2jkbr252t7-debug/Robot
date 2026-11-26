"""NOVA mini - arm drive B1+ (fixer revision): labelled Slovak sheets from the renders of v2b_scene.py.
Usage: /opt/venv/cad/bin/python v2b_sheets.py <render_dir> <out_dir> [rez rozlozene diely]"""
import sys, os, json, math
import numpy as np
from PIL import Image, ImageDraw
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R1/img_v1/work")
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T4")
import g2b as G
import t4_common as C
from sheetlib import (font, feather, dashed, arrow_head, badge, crop_alpha, _cross, BG, INK, MUTED, ACCENT, DIM)

V = G.V
D, OUT = sys.argv[1], sys.argv[2]
ONLY = sys.argv[3:]
os.makedirs(OUT, exist_ok=True)
fTitle, fSub, fPan, fLab, fSmall, fDim, fNum = font(50), font(26, "Regular"), font(32), font(24, "Medium"), font(21, "Regular"), font(26, "SemiBold"), font(21)
fTag = font(16, "Bold")
fSec = font(34)
GREEN = (28, 140, 90)          # printed
ORANGE = (222, 112, 20)        # bought
ORZONE = (235, 120, 20)
TAGC = {"T": GREEN, "K": ORANGE, "R": (120, 120, 126), "S": (120, 120, 126)}
TAGT = {"T": "TLAČ", "K": "KÚP", "R": "RUKA", "S": "TRUP"}


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
        f = self.d["lens"] / self.d["sensor_width"] * self.W
        return (self.W / 2 + f * q[0] / -q[2], self.H / 2 - f * q[1] / -q[2])

    def k(self):
        return self.W / self.d["ortho_scale"]


def load(name):
    return Image.open(os.path.join(D, name + ".png")).convert("RGBA")


def tw(t, f):
    return ImageDraw.Draw(Image.new("RGB", (4, 4))).textlength(t, font=f)


def header(d, title, intro, x=44, y=34):
    d.text((x, y), title, font=fTitle, fill=INK)
    d.multiline_text((x, y + 76), intro, font=fSub, fill=MUTED, spacing=10)
    return y + 76 + (intro.count("\n") + 1) * 37 + 20


def footer_block(d, x, y, text, fnt=None, fill=MUTED, spacing=9):
    fnt = fnt or fSmall
    d.multiline_text((x, y), text, font=fnt, fill=fill, spacing=spacing)
    return y + (text.count("\n") + 1) * (fnt.size + spacing)


def tag(d, x, y, kind, fnt=fTag):
    """rounded pill with TLAČ / KÚP; returns its width"""
    t = TAGT[kind]
    w = tw(t, fnt) + 14
    d.rounded_rectangle([x, y, x + w, y + fnt.size + 9], 6, fill=TAGC[kind])
    d.text((x + 7, y + 3), t, font=fnt, fill=(255, 255, 255))
    return w


def label_size(txt, fnt, sub_f):
    lines = txt.split("\n")
    w0 = tw(lines[0], fnt) + 62
    ws = [tw(t, sub_f) + 62 for t in lines[1:]]
    return max([w0] + ws), fnt.size + 10 + len(lines[1:]) * (sub_f.size + 7)


def _stack(items, H, gap):
    last = -1e9
    for it in items:
        it["ly"] = max(it["ay"] - it["h"] / 2, last)
        last = it["ly"] + it["h"] + gap
    if items:
        over = items[-1]["ly"] + items[-1]["h"] - (H - 6)
        if over > 0:
            last = 6
            for it in items:
                it["ly"] = max(it["ly"] - over, last)
                last = it["ly"] + it["h"] + gap


def place_tagged(d, items, side, x_text, colw, yi, H, ix0, fnt=None, sub_f=None, gap=12, color=ACCENT, y_min=0):
    """items: dict(ay, ax, txt, kind) in image pixels; first line of txt next to the tag, further lines smaller below"""
    fnt = fnt or fLab
    sub_f = sub_f or fSmall
    its = []
    for it in items:
        w, h = label_size(it["txt"], fnt, sub_f)
        its.append(dict(it, w=w, h=h, ly=0.0))
    its.sort(key=lambda t: t["ay"])
    ex = x_text + colw - 6 if side == "L" else x_text + 6
    for _ in range(80):
        _stack(its, H, gap)
        sw = False
        for i in range(len(its) - 1):
            a, b = its[i], its[i + 1]
            pa, pb = (ex, a["ly"] + 14), (ex, b["ly"] + 14)
            if _cross(pa, (ix0 + a["ax"], a["ay"]), pb, (ix0 + b["ax"], b["ay"])):
                its[i], its[i + 1] = b, a; sw = True
        if not sw:
            break
    _stack(its, H, gap)
    for it in its:
        lines = it["txt"].split("\n")
        ly = yi + it["ly"]
        if side == "L":
            x0 = x_text + colw - 16 - it["w"]
        else:
            x0 = x_text + 16
        wt = tag(d, x0, ly + 2, it["kind"])
        d.text((x0 + wt + 10, ly), lines[0], font=fnt, fill=INK)
        if len(lines) > 1:
            d.multiline_text((x0 + wt + 10, ly + fnt.size + 9), "\n".join(lines[1:]), font=sub_f, fill=MUTED, spacing=7)
        ey = ly + 14
        pxx, pyy = ix0 + it["ax"], yi + it["ay"]
        d.line([(ex, ey), (pxx, pyy)], fill=color, width=3)
        d.ellipse([pxx - 6, pyy - 6, pxx + 6, pyy + 6], fill=color, outline=(255, 255, 255), width=2)


def legend_tags(d, x, y):
    w = tag(d, x, y + 3, "T"); d.text((x + w + 10, y), "tlačíš sám z Elegoo Tough", font=fSmall, fill=INK)
    x2 = x + w + 10 + tw("tlačíš sám z Elegoo Tough", fSmall) + 40
    w = tag(d, x2, y + 3, "K"); d.text((x2 + w + 10, y), "kúpiš hotové v bežnej veľkosti (nič sa na ňom neobrába)", font=fSmall, fill=INK)
    return y + 34


# ================================================================================================ 1 section
def xs_in(z, inset=1.0):
    return C.x_surface(G.YA, z) - inset


def sheet_rez():
    det = load("rez_det"); dcam = Cam(os.path.join(D, "rez_det_cam.json"))
    ov = load("rez"); ocam = Cam(os.path.join(D, "rez_cam.json"))
    DW, DH = det.size
    # ---- overview overlays (sweep zone, axes)
    IW, IH = ov.size
    zl = Image.new("RGBA", ov.size, (0, 0, 0, 0))
    Po = lambda x, z: ocam.px((x, G.YA, z))
    zone = [(18.0, -41.9), (G.sweep_x(26.5), -41.9), (G.sweep_x(26.5), -40.9), (G.sweep_x(33.4), -40.9), (G.sweep_x(33.4), -17.0),
            (G.sweep_x(32.2), -17.0), (G.sweep_x(32.2), -11.5), (G.sweep_x(26.5), -11.5), (G.sweep_x(26.5), 3.0), (18.0, 3.0)]
    ImageDraw.Draw(zl).polygon([Po(x, z) for x, z in zone], fill=ORZONE + (46,))
    ov.alpha_composite(zl)
    do = ImageDraw.Draw(ov)
    pts = []
    for z0, z1, r in G.PAN_ENV2:
        x = G.sweep_x(r)
        pts += [Po(x, max(z0, -84)), Po(x, min(z1, 3))]
    dashed(do, pts, ORZONE + (255,), width=3, dash=12, gap=7)
    dashed(do, [Po(18.5, G.ZA), Po(83.5, G.ZA)], (40, 40, 40, 170), width=2, dash=18, gap=5)
    dashed(do, [Po(G.XV, -70.0), Po(G.XV, -6.0)], (40, 40, 40, 170), width=2, dash=18, gap=5)
    # ---- detail overlays (axes)
    dd = ImageDraw.Draw(det)
    Pd = lambda x, z: dcam.px((x, G.YA, z))
    dashed(dd, [Pd(31.2, G.ZA), Pd(69.8, G.ZA)], (40, 40, 40, 150), width=2, dash=22, gap=6)
    dashed(dd, [Pd(G.XV, -47.3), Pd(G.XV, -3.0)], (40, 40, 40, 150), width=2, dash=22, gap=6)

    title = "NOVA mini · ruky v2b: rez ľavým ramenom"
    intro = ("Rez zvislou rovinou cez os ramena a cez os serva (y = 3), pohľad spredu; ľavá strana robota je vpravo. Pravé rameno je zrkadlové.\n"
             "Servo stojí v trupe; jeho výstup otáča tlačeným zvislým hriadeľom a tlačeným kužeľovým párom 12/18 hriadeľ ruky – obyčajnú skrutku M4×20.\n"
             "Ruka je pasívna a točí sa na ložisku 6800 na čiernej zátke. Skrutka ju otáča cez magnetickú treciu spojku (prekĺzne pri 0,0082–0,0113 N·m).\n"
             "Farba rezu: oranžová = biela živica · modrá = čierna živica · zelená = tlačené diely pohonu (Elegoo Tough) · fialová = servo\n"
             "· sivá = oceľ (kúpené skrutky, ložiská, podložka) · zlatá = mosadz · červená = magnety.")
    colL, colR = 600, 640
    gapc = 0
    W = colL + DW + colR
    top = 34 + 76 + 5 * 37 + 20
    ylg = top
    S0 = Image.new("RGB", (W, 10), BG)
    # overview scale
    osc = 0.8
    ovs = ov.resize((int(IW * osc), int(IH * osc)), Image.LANCZOS)
    OW, OH = ovs.size
    H = top + 50 + DH + 40 + 46 + OH + 30 + 4 * 31 + 60
    S = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(S)
    header(d, title, intro)
    legend_tags(d, 44, ylg)
    yi = top + 80
    ix0 = colL
    bgi = Image.new("RGBA", det.size, (255, 255, 255, 255)); bgi.alpha_composite(det)
    S.paste(bgi, (ix0, yi))
    d.rectangle([ix0, yi, ix0 + DW - 1, yi + DH - 1], outline=(215, 215, 210), width=2)
    d.text((ix0, yi - 44), "detail kĺbu a pohonu", font=fPan, fill=INK)

    def DP(x, z):
        u, v = dcam.px((x, G.YA, z))
        return [min(max(v, 4), DH - 4), min(max(u, 4), DW - 4)]
    xin = lambda z: V.skins(G.YA, z, 0.0, G.DX)[0]
    s12 = (G.XV + 4.15, -8.0)
    Lft = [
        ((35.0, -31.0), "T", "výplň a nová priečka stĺpa (z −35 … −27)\nčasť T_spodok; spevňuje stĺp proti krúteniu"),
        ((36.6, -8.6), "K", "mosadzná závitová vložka M2 (3×)\nkrátka, d 3,2 – 3,6; vlepená epoxidom"),
        ((40.2, -8.0), "K", "zápustná skrutka DIN 965 M2×8 (hore)\nvľavo a vpravo dole 2× M2×10"),
        ((41.5, -5.0), "T", "zátka (čierna) – nahrádza T_klb\nčelo 1 mm pod povrchom trupu, 2 kolíky Ø2,4"),
        ((35.3, -13.0), "T", "stĺp s nálitkom – časť dna trupu T_spodok\ntlačí sa s trupom (zatiaľ netlačiť, pozri dole)"),
        ((42.9, -11.3), "T", "kužeľové koleso 18 z so závitom M4\nnaskrutkované na M4 a zalepené"),
        ((44.39, -14.6), "T", "podložka pod koleso 0,20 / 0,30 / 0,40\nvyberie sa meraním hĺbky 3,24 mm"),
        ((45.8, -13.75), "K", "ložisko MR74ZZ (4 × 7 × 2,5) – A1"),
        ((35.6, -22.2), "T", "kužeľový pastorok 12 z\nm 0,67, záber 25°"),
        ((37.4, -23.64), "T", "podložka pod pastorok 0,22 … 0,57\n8 hrúbok, nastavuje vôľu zubov"),
        ((41.75, -25.1), "K", "ložisko MR63ZZ (3 × 6 × 2,5)\nvlepené v jazýčku stĺpa"),
        ((39.0, -31.5), "T", "zvislý hriadeľ\nšesťhran 5 / Ø3 / Ø2,5 s plôškou"),
        ((40.4, -39.6), "K", "skrutka DIN 912 M2×5 (imbus)\nprechádza šesťhranom spojky do serva"),
        ((34.8, -42.5), "T", "spojka serva (drážkovanie 20 z)\nalebo vlepená orezaná páka, ak je v balení"),
    ]
    Rgt = [
        ((50.0, -13.75), "T", "rozperné puzdro Ø7 / Ø5 × 5,56"),
        ((53.85, -13.75), "K", "ložisko MR74ZZ – A2\nvonkajší krúžok vlepený na doraz"),
        ((57.8, -8.05), "K", "ložisko 6800ZZ (10 × 19 × 5)\nna ňom sa točí ruka"),
        ((56.6, -6.9), "T", "náboj ruky (biely, vlepený v ruke)\nrebro dorazu 90° je vpredu, mimo rezu"),
        ((59.72, -13.5), "T", "C-podložka 0,45 (alebo 0,47)\nzastaví zatlačenie ruky k telu"),
        ((61.0, -18.6), "K", "skrutka DIN 912 M4×20 = hriadeľ ruky\nštandardná dĺžka, nič sa nereže"),
        ((62.2, -9.6), "K", "podložka DIN 125 M10, pozinkovaná oceľ\nnie nerez (musí sa chytiť magnetu)"),
        ((64.45, -24.7), "K", "magnety NdFeB 5 × 2 N38 (4 ks)\naxiálne, striedavá polarita"),
        ((65.2, -19.8), "T", "unášač spojky (nasadený na hlavu M4)\n8 vreciek na magnety, koža 0,25"),
        ((67.15, -5.95), "T", "krúžok (vlepený) – drží unášač v náboji"),
        ((53.6, -23.0), "T", "doraz v zátke (výstupok 83,5°)\nruka sa zastaví na −51° a +135,5°"),
        ((xin(-40.0) + 0.8, -40.0), "R", "vnútorná škrupina ruky (nosná)"),
    ]
    L = [dict(ay=DP(*p)[0], ax=DP(*p)[1], txt=t, kind=k) for p, k, t in Lft]
    R = [dict(ay=DP(*p)[0], ax=DP(*p)[1], txt=t, kind=k) for p, k, t in Rgt]
    place_tagged(d, L, "L", 0, colL, yi, DH, ix0, gap=16)
    place_tagged(d, R, "R", colL + DW, colR, yi, DH, ix0, gap=22)
    # ---- overview row
    yo = yi + DH + 40
    xo = 60
    d.text((xo, yo - 4), "celý rez (zmenšený; modrý rámik = detail hore)", font=fPan, fill=INK)
    yo += 46
    bgo = Image.new("RGBA", ovs.size, (255, 255, 255, 255)); bgo.alpha_composite(ovs)
    S.paste(bgo, (xo, yo))
    d.rectangle([xo, yo, xo + OW - 1, yo + OH - 1], outline=(215, 215, 210), width=2)
    x0, x1, z0, z1 = dcam.extra["crop"]
    a = ocam.px((x0, G.YA, z1)); b = ocam.px((x1, G.YA, z0))
    d.rectangle([xo + a[0] * osc, yo + a[1] * osc, xo + b[0] * osc, yo + b[1] * osc], outline=ACCENT, width=3)

    def OP(x, z):
        u, v = ocam.px((x, G.YA, z))
        return [v * osc, u * osc]
    xout = lambda z: V.skins(G.YA, z, 0.0, G.DX)[1]
    zseam = -60.0
    Ov = [((39.0, -58.0), "K", "servo Feetech SCS0009 (Waveshare SC09), stojí v kapse\nvýška 21,5 mm z modelu v2; výkres udáva 25,25 – odmerať"),
          ((xout(-40.0) - 0.8, -40.0), "R", "vonkajší kryt ruky (drží na magnetoch)"),
          ((xs_in(-56.0, 1.1), -56.0), "S", "bočný kryt trupu T_bok (zvonka bez zmeny)"),
          ((28.0, -75.4), "S", "menič napätia (na dne, ako vo v2)"),
          ((26.0, -30.0), "S", "oranžovo: priestor otáčania krku a serva zdvihu;\nstĺp je od neho ≥ 1,0 mm"),
          ((32.2, -60.0), "S", "kapsa serva v stĺpe (T_spodok)")]
    O = [dict(ay=OP(*p)[0], ax=OP(*p)[1], txt=t, kind=k) for p, k, t in Ov]
    place_tagged(d, O, "R", xo + OW, 700, yo, OH, xo, gap=12)
    # ---- notes right of the overview labels
    xn = xo + OW + 760
    notes = ("Nič sa neobrába: žiadne rezanie, vŕtanie, závitovanie\n"
             "ani sústruženie kovu. Kúpené diely sú v štandardnej\n"
             "veľkosti a dĺžke; špeciálne diely sa tlačia.\n\n"
             "Vôľa zubov: podložka pod koleso podľa merania 3,24 mm,\n"
             "potom podložka pod pastorok (0,22 … 0,57); na konci ruky\n"
             "má byť vôľa 0,9 – 2,0 mm a nikde nesmie drhnúť.\n\n"
             "Rozsah ruky −45° … +130° (medzera k trupu ≥ 1,15 mm).\n"
             "Skryté dorazy −51° / +135,5° slúžia len na nulovanie;\n"
             "spojka sa pri nich na chvíľu prešmykne.")
    d.text((xn, yo - 50), "Ako to funguje", font=fPan, fill=INK)
    footer_block(d, xn, yo, notes, fLab, INK, 12)
    foot = ("Koncept, nie výkres na tlač. Otvorené: pevnosť stĺpa pri +135° (MKP samotného stĺpa je nad 8,5 MPa) – T_spodok zatiaľ netlačiť; skutočná výška a drážkovanie serva;\n"
            "dostupnosť kupovaných dielov v SK/CZ obchodoch nie je overená. Zistené pri kreslení: horné magnetové stĺpiky krytu ruky (vpredu a vzadu) zasahujú do steny\n"
            "náboja 6800 až o 1,2 mm – v CAD ich treba posunúť alebo zlúčiť s nábojom. Zuby sú nakreslené zjednodušene (bez zaoblenia hláv r 0,1).")
    yf = yo + OH + 24
    footer_block(d, 44, yf, foot)
    S = S.crop((0, 0, W, yf + 4 * 31 + 20))
    S.save(os.path.join(OUT, "v2b_rez_ramenom.png"), optimize=True)
    print("rez", S.size)




# ================================================================================================ 2 exploded
EXP_ITEMS = [   # (anchor key, text, kind, badge direction)
    ("stlp", "stĺp v T_spodok – tlačí sa s trupom (s výplňou a priečkou)", "T", "down"),
    ("B1", "ložisko MR63ZZ 3×6×2,5 – vlepiť do jazýčka stĺpa", "K", "up"),
    ("vlozky", "3× mosadzná vložka M2 – vlepiť do nálitku", "K", "up"),
    ("zatka", "zátka (čierna) s 2 kolíkmi Ø2,4 a dorazom", "T", "up"),
    ("A2", "ložisko MR74ZZ (A2) – vlepiť na doraz v zátke", "K", "up"),
    ("puzdro", "rozperné puzdro Ø7 / Ø5", "T", "down"),
    ("A1", "ložisko MR74ZZ (A1) – zasunúť", "K", "up"),
    ("skrutka_M4", "skrutka DIN 912 M4×20 = hriadeľ ruky (s epoxidom)", "K", "up"),
    ("podlozka_kolesa", "podložka pod koleso 0,20 / 0,30 / 0,40", "T", "down"),
    ("koleso", "kužeľové koleso 18 z – naskrutkovať na M4, zalepiť", "T", "up"),
    ("c_podlozka", "C-podložka 0,45 – zacvaknúť pod hlavu po vytvrdnutí", "T", "down"),
    ("hriadel_zvisly", "zvislý hriadeľ – zdola cez MR63", "T", "down"),
    ("podlozka_pastorka", "podložka pod pastorok (začni s 0,42)", "T", "up"),
    ("pastorok", "kužeľový pastorok 12 z – navrch hriadeľa", "T", "up"),
    ("spojka", "spojka s drážkovaním 20 z – natlačiť na servo", "T", "down"),
    ("skrutka_spojky", "skrutka DIN 912 M2×5 – cez šesťhran do serva", "K", "down"),
    ("servo", "servo SCS0009 so spojkou – zasunúť zboku do kapsy v stĺpe", "K", "down"),
    ("zatka_skrutky", "zápustné skrutky DIN 965: M2×8 hore, 2× M2×10", "K", "up"),
    ("L6800", "ložisko 6800ZZ – vlepiť do náboja ruky", "K", "up"),
    ("vnut", "vnútorná škrupina ruky s vlepeným tlačeným nábojom", "T", "down"),
    ("podlozka_M10", "podložka DIN 125 M10 (pozinkovaná) – vlepiť do náboja", "K", "up"),
    ("unasac", "unášač spojky (tlačený) – nasadí sa na hlavu M4", "T", "down"),
    ("magnety_spojky", "4 magnety 5×2 do protiľahlých vreciek unášača", "K", "up"),
    ("kruzok", "krúžok – nalepiť do náboja, drží unášač", "T", "down"),
    ("mag_von", "magnety krytu Ø3×2 (bez zmeny oproti v2)", "K", "up"),
    ("vonk", "vonkajší kryt ruky – drží na magnetoch", "T", "down"),
]


def sheet_rozlozene():
    im = load("rozlozene")
    cam = Cam(os.path.join(D, "rozlozene_cam.json"))
    IW, IH = im.size
    AN = cam.extra["anchors"]
    title = "NOVA mini · ruky v2b: rozložené ľavé rameno"
    intro = ("Pohľad spredu zľava zhora. Hore diely v trupe a kazeta v zátke, dole ruka, ktorá sa nakoniec nasunie na zátku. Pravé rameno je zrkadlové.\n"
             "Čísla = poradie montáže: zelené = tlačený diel z Elegoo Tough (pohon je na obrázku zelený len pre prehľadnosť), oranžové = kúpený hotový diel.\n"
             "Nič sa neobrába: skrutka M4×20 je hriadeľ ruky v pôvodnej dĺžke, ozubené kolesá, hriadeľ, spojka a unášač sa tlačia.")
    top = 34 + 76 + 3 * 37 + 20
    ncol = 2
    rows_n = math.ceil(len(EXP_ITEMS) / ncol)
    W = max(IW + 80, 1900)
    H = top + IH + 40 + rows_n * 42 + 260
    S = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(S)
    header(d, title, intro)
    ix0, yi = (W - IW) // 2, top
    S.paste(im, (ix0, yi), im)
    RW = cam.extra.get("rows", {})
    if "r1" in RW:
        t1 = "hore: trup + kazeta v zátke"
        d.text((ix0 + IW - 40 - tw(t1, fPan), yi + 14), t1, font=fPan, fill=INK)
    if "r2" in RW:
        t2 = "dole: ruka – zloží sa na stole,\npotom sa nasunie na zátku"
        d.multiline_text((ix0 + 40, yi + IH - 110), t2, font=fPan, fill=INK, spacing=10)
    used = []
    pts = [(ix0 + AN[k][0], yi + AN[k][1]) for k, _, _, _ in EXP_ITEMS]
    for n, (k, txt, kind, dr) in enumerate(EXP_ITEMS, 1):
        u, v = AN[k]
        sg = -1 if dr == "up" else 1
        bx, by = ix0 + u, yi + v + sg * 62
        for _ in range(40):
            if all(math.hypot(bx - qx, by - qy) > 42 for qx, qy in used) and all(math.hypot(bx - qx, by - qy) > 26 for qx, qy in pts):
                break
            by += sg * 22
        by = min(max(by, yi + 20), yi + IH - 20)
        col = TAGC[kind]
        d.line([(bx, by), (ix0 + u, yi + v)], fill=col, width=3)
        d.ellipse([ix0 + u - 5, yi + v - 5, ix0 + u + 5, yi + v + 5], fill=col, outline=(255, 255, 255), width=2)
        badge(d, (bx, by), n, fNum, fill=col)
        used.append((bx, by))
    colw = (W - 100) // ncol
    for n, (_, txt, kind, _) in enumerate(EXP_ITEMS, 1):
        c, r = (n - 1) // rows_n, (n - 1) % rows_n
        x, y = 50 + c * colw, yi + IH + 30 + r * 42
        badge(d, (x + 17, y + 15), n, font(19), fill=TAGC[kind], r=17)
        d.text((x + 44, y + 2), txt, font=fLab, fill=INK)
    yf = yi + IH + 30 + rows_n * 42 + 24
    footer_block(d, 50, yf,
                 "Kazeta na stole: 4 → 5 (epoxid, vytvrdnúť) → 6, 7 → 8 zvonka s kalibrom 0,5 pod hlavou → 9, 10 s epoxidom → po vytvrdnutí 11.\n"
                 "Trup (bočný kryt dole): 12 zdola cez 2 → 13, 14 navrch → hriadeľ nadvihnúť o 3,5 → 17 so spojkou 15 a skrutkou 16 zasunúť zboku → hriadeľ spustiť\n"
                 "→ bočný kryt → kazetu zasunúť, koleso zapadne → 18 (len jemne) → skontrolovať vôľu → ruka 19–24 vo visiacej polohe nasadiť → 25, 26.\n"
                 "Koncept – výška serva neoverená; zuby zjednodušené. Pravé rameno je zrkadlové.", fSmall, MUTED)
    S = S.crop((0, 0, W, yf + 4 * 31 + 20))
    S.save(os.path.join(OUT, "v2b_rameno_rozlozene.png"), optimize=True)
    print("rozlozene", S.size)


# ================================================================================================ 3 parts sheet
PRINTED = [
    ("zatka", "zátka (čierna)", "1×", "Ø27 × 21 · 2 kolíky Ø2,4 · doraz 83,5°\nsedlo Ø10 pre 6800, otvor Ø7 pre MR74\ntlač na osi; uloženia podľa kupónov"),
    ("koleso", "kužeľové koleso 18 z", "1×", "Ø12,6 · m 0,67 · 25° · vnútorný závit M4\nvrstva 20 µm, os zvislo,\npodpery len na zadnej strane"),
    ("pastorok", "kužeľový pastorok 12 z", "1×", "Ø9 · otvor Ø2,5 s plôškou\nvrstva 20 µm; najprv 3 skúšobné\npáry s rôznou hrúbkou zubov"),
    ("hriadel_zvisly", "zvislý hriadeľ", "1×", "dĺžka 17,9 · šesťhran 5 / Ø3 / Ø2,5\ns plôškou; Ø3 do MR63 podľa kupónu"),
    ("spojka", "spojka serva", "1×", "Ø9 × 9,2 · drážkovanie 20 z (Ø3,95)\nkupóny +0 / +0,02 / +0,04 / +0,06\n(alebo vrecko na páku, ak je v balení)"),
    ("unasac", "unášač spojky (+ 4 magnety)", "1×", "Ø22 × 6,25 · 8 vreciek Ø5,1\nkoža 0,25 · otvor na hlavu M4 podľa\nnameraného Ø hlavy (−0,01/−0,02/−0,03)"),
    ("naboj", "náboj ruky (biely)", "1×", "otvor Ø19 pre 6800 · rebro dorazu 90°\nvlepí sa do vnútornej škrupiny ruky"),
    ("kruzok", "krúžok", "1×", "Ø23 / Ø20,8 × 0,8\nnalepí sa do náboja, drží unášač"),
    ("puzdro", "rozperné puzdro", "1×", "Ø7 / Ø5 × 5,56\nmedzi ložiskami MR74"),
    ("podlozky", "podložky", "sady", "pod pastorok 0,22 … 0,57 (8 ks, Ø3,8)\npod koleso 0,20 / 0,30 / 0,40 (Ø5,8)\nC-podložka 0,45 a 0,47 (Ø8,8)"),
    (None, "pomôcky (tiež tlačené)", "", "rozpierky pod magnety 0,2 / 0,4 / 0,6 / 0,8\nkaliber 0,5 mm (vidlička) · háčik na koniec\nruky na skúšku mincami · skúšobné kupóny"),
    ("stlp", "stĺp so servom – súčasť T_spodok", "", "tlačí sa s dnom trupu; ZATIAĽ NETLAČIŤ:\npevnosť stĺpa pri +135° ešte nevyhovuje\n(výpočet MKP nad 8,5 MPa)"),
]
BOUGHT = [   # key, short name, qty, exact size / designation, where + note
    ("servo", "servo", "1×", "Feetech SCS0009 / Waveshare SC09", "e-shop s elektronikou (napr. LaskaKit CZ)\nalebo priamo Waveshare (~9 USD)\nna 2 ruky kúp 3 ks (1 rezerva)"),
    ("MR63", "ložisko MR63ZZ", "1×", "3 × 6 × 2,5 mm", "predajňa ložísk, RC alebo 3D-tlač e-shop\n(RC označenie „630“)"),
    ("MR74", "ložisko MR74ZZ", "2×", "4 × 7 × 2,5 mm", "predajňa ložísk, RC e-shop („740“)\nnajskôr bude treba objednať poštou"),
    ("L6800", "ložisko 6800ZZ / 6800-2RS", "1×", "10 × 19 × 5 mm (aj „61800“)", "predajňa ložísk, cyklo\nnáhrada: 6700ZZ s inou verziou náboja"),
    ("M4", "skrutka – hriadeľ ruky", "1×", "DIN 912 M4×20, imbus, celý závit", "železiarstvo / spojovací materiál; kúp 2 balenia\n(zinok aj 12.9 čierna) a posuvkou vyber\nØ závitu ≥ 3,93 (najmenej 3,90)"),
    ("M2_spojka", "skrutka do spojky", "1×", "DIN 912 M2×5, imbus", "sada skrutiek M2 / spojovací materiál\n(M2×6 alebo M2×8, ak lepíš páku);\nzávit v serve over pri rozbalení"),
    ("M2_zapustne", "skrutky zátky", "3×", "DIN 965 M2×8 (1×) + M2×10 (2×)", "zápustné, krížová drážka, zinok alebo nerez\nspojovací materiál, sada M2"),
    ("vlozky", "závitové vložky", "3×", "mosadz M2, krátka: dĺžka 3 – 4, Ø 3,2 – 3,6", "3D-tlač e-shop\nlepí sa epoxidom (nie teplom)"),
    ("M10", "podložka spojky", "1×", "DIN 125 M10: 10,5 × 20 × 2", "železiarstvo · POZINKOVANÁ OCEĽ, nie nerez\n(magnet sa musí prichytiť)"),
    ("magnety", "magnety spojky", "4 – 8", "NdFeB 5 × 2 mm, N38, axiálne", "e-shop s magnetmi (balenie 16 – 20 ks)\nAliExpress len ako záloha"),
    (None, "lepidlo, mazivo, mince", "", "", "2K epoxid (máš) · PTFE tuk alebo grafit\nmince 2 €, 50 c a 2 c na kalibráciu spojky\nvoliteľne plstená páska do kapsy serva"),
]
HANDS = [
    ("Strihanie a pilovanie len plastu", "Bočnými štípačkami odstrihni plastové úšká serva a zabrús ich. Ak je v balení páka serva, odstrihni\n"
     "jej rameno a pilníkom zapiluj 2 plôšky na 6,2 mm (len pre spojku s pákou)."),
    ("Meranie posuvkou", "Vyber skrutku M4×20 s Ø závitu ≥ 3,93 mm a odmeraj Ø jej hlavy (podľa toho vyber kupón unášača).\n"
     "Hĺbkomerom zmeraj od čela krčku zátky po čelo kolesa 3,24 mm – podľa toho podložka pod koleso."),
    ("Lepenie 2K epoxidom", "MR63 do jazýčka · 3 vložky M2 do nálitku · MR74 (A2) na doraz · vnútorné krúžky MR74 na závit M4 ·\n"
     "koleso na M4 · 6800 a podložka M10 do náboja (hladkou stranou von, otrep do drážky) · magnety · krúžok."),
    ("Natlačiť rukou, zacvaknúť", "Spojku na drážkovanie serva, unášač na hlavu M4, C-podložku pod hlavu M4 (po vytvrdnutí, kaliber von).\n"
     "Skrutky M2 do vložiek len jemne dotiahnuť, bez zaisťovača."),
    ("Nastavenie a skúška", "Vôľa na konci ruky 0,9 – 2,0 mm (podložky pod pastorok, najviac 0,57). Zuby natrieť PTFE tukom.\n"
     "Skúška mincami na háčiku (ruka vodorovne): 2 € + 2 c musí držať, 2 € + 50 c sa musí prešmyknúť."),
]


def icon(key, box):
    p = os.path.join(D, f"ikona_{key}.png")
    if not os.path.exists(p):
        return None
    im = Image.open(p).convert("RGBA")
    im, _ = crop_alpha(im, 6)
    s = min(box / im.width, box / im.height)
    return im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)


def card(S, d, x, y, w, h, key, name, qty, txt, kind, size=""):
    d.rounded_rectangle([x, y, x + w, y + h], 14, fill=(252, 252, 250), outline=(222, 222, 218), width=2)
    ib = h - 24
    im = icon(key, ib) if key else None
    tx = x + 20
    if im is not None:
        S.paste(im, (int(x + 12 + (ib - im.width) / 2), int(y + 12 + (ib - im.height) / 2)), im)
        tx = x + 24 + ib
    wt = tag(d, tx, y + 18, kind)
    d.text((tx + wt + 10, y + 14), name, font=font(25, "SemiBold"), fill=INK)
    if qty:
        d.text((x + w - 18 - tw(qty, font(25, "SemiBold")), y + 14), qty, font=font(25, "SemiBold"), fill=TAGC[kind])
    yt = y + 54
    if size:
        d.text((tx, yt - 2), size, font=font(23, "SemiBold"), fill=TAGC[kind])
        yt += 34
    d.multiline_text((tx, yt), txt, font=fSmall, fill=(70, 72, 78), spacing=8)


def section_bar(d, x, y, w, text, col, sub):
    d.rounded_rectangle([x, y, x + w, y + 56], 10, fill=col)
    d.text((x + 20, y + 9), text, font=fSec, fill=(255, 255, 255))
    d.text((x + 34 + tw(text, fSec), y + 17), sub, font=font(22, "Medium"), fill=(255, 255, 255))
    return y + 72


def sheet_diely():
    W = 2400
    ncol = 3
    gx = 22
    cw = (W - 2 * 44 - (ncol - 1) * gx) // ncol
    ch = 214
    title = "NOVA mini · ruky v2b: diely na jednu ruku"
    intro = ("Druhá ruka je zrkadlová – všetko kúp a vytlač 2×. Rozmery v mm.\n"
             "Nič sa neobrába: žiadne rezanie, vŕtanie, závitovanie, sústruženie ani brúsenie kovu. Netreba žiadne špeciálne diely z katalógov –\n"
             "okrem serva sa kupujú len skrutky, podložka, ložiská, magnety a vložky v bežných veľkostiach a dĺžkach; všetko tvarované (kolesá, hriadeľ, spojka, unášač) sa tlačí.")
    rows_p = math.ceil(len(PRINTED) / ncol)
    rows_b = math.ceil(len(BOUGHT) / ncol)
    H = 34 + 76 + 3 * 37 + 40 + 72 + rows_p * (ch + gx) + 40 + 72 + 60 + rows_b * (ch + gx) + 40 + 72 + len(HANDS) * 92 + 160
    S = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(S)
    y = header(d, title, intro) + 10
    y = section_bar(d, 44, y, W - 88, "TLAČÍŠ", GREEN, "z Elegoo Tough na Saturn 4 Ultra 16K · umyť a vytvrdiť · rozmery uložení podľa skúšobných kupónov")
    for i, (k, n, q, t) in enumerate(PRINTED):
        c, r = i % ncol, i // ncol
        card(S, d, 44 + c * (cw + gx), y + r * (ch + gx), cw, ch, k, n, q, t, "T")
    y += rows_p * (ch + gx) + 26
    y = section_bar(d, 44, y, W - 88, "KÚPIŠ V BEŽNOM OBCHODE", ORANGE, "hotové, v štandardnej veľkosti – nič sa na nich nereže ani neupravuje (okrem plastových úšok serva)")
    d.text((50, y - 4), "Pozor: či sú položky skladom v konkrétnom obchode v SK/CZ, sa zatiaľ nepodarilo overiť (stránky obchodov sa nedali otvoriť). "
                        "Pred nákupom to over – najmä MR74ZZ.", font=font(22, "Medium"), fill=DIM)
    y += 40
    for i, (k, n, q, sz, t) in enumerate(BOUGHT):
        c, r = i % ncol, i // ncol
        card(S, d, 44 + c * (cw + gx), y + r * (ch + gx), cw, ch, k, n, q, t, "K", sz)
    y += rows_b * (ch + gx) + 26
    y = section_bar(d, 44, y, W - 88, "ČO ROBÍŠ RUKAMI", (60, 100, 150), "náradie: bočné štípačky, pilník, posuvka, imbusy, pinzeta, 2K epoxid")
    for i, (h, t) in enumerate(HANDS, 1):
        badge(d, (64, y + 18), i, font(19), fill=(60, 100, 150), r=17)
        d.text((92, y + 2), h, font=font(25, "SemiBold"), fill=INK)
        d.multiline_text((520, y + 4), t, font=fSmall, fill=(60, 62, 68), spacing=8)
        y += 92
    y += 6
    d.rounded_rectangle([44, y, W - 44, y + 62], 10, fill=(255, 255, 255), outline=GREEN, width=3)
    d.text((64, y + 15), "Žiadny kovový diel sa neobrába a nepotrebuješ žiadne špeciálne súčiastky – strihá a pilí sa len plast (úšká serva, páka).",
           font=font(25, "SemiBold"), fill=GREEN)
    y += 84
    d.text((44, y), "Koncept – rozmery serva treba pred tlačou odmerať; pevnosť stĺpa v T_spodok ešte nie je overená (T_spodok zatiaľ netlačiť).",
           font=fSmall, fill=MUTED)
    S = S.crop((0, 0, W, y + 44))
    S.save(os.path.join(OUT, "v2b_diely.png"), optimize=True)
    print("diely", S.size)


if not ONLY or "rez" in ONLY:
    sheet_rez()
if not ONLY or "rozlozene" in ONLY:
    sheet_rozlozene()
if not ONLY or "diely" in ONLY:
    sheet_diely()
