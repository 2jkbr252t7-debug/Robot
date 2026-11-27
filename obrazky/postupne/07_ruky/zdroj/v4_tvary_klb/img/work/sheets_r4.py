"""NOVA mini - R4 comparison sheets (Slovak labels with diacritics).  CAD venv (Pillow, numpy).
usage: /opt/venv/cad/bin/python sheets_r4.py <render_dir> <out_dir> [zaoblenia klb odporucanie]
Reads the renders of scene_r4.py + nums_r4.json (numbers from the designers' / verifiers' JSONs, see nums_r4.py).
Writes v4_ruka_B_zaoblenia.png, v4_klb_ramena.png, v4_odporucanie.png (style of R3 v3_porovnanie_spredu.png)."""
import sys, os, json
from decimal import Decimal, ROUND_HALF_UP
import numpy as np
from PIL import Image, ImageDraw
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from sheetlib import font, arrow_head, feather, BG, INK, MUTED, ACCENT, DIM

D, OUT = sys.argv[1], sys.argv[2]
ONLY = sys.argv[3:]
os.makedirs(OUT, exist_ok=True)
N = json.load(open(os.path.join(HERE, "nums_r4.json")))
NS, NJ, CC = N["shape"], N["joint"], N["combo"]
SW, M, GC = 1400, 36, 14
GREEN, ORANGE, RED = (28, 140, 74), (214, 112, 14), (196, 48, 36)
CARD, EDGE = (250, 250, 248), (222, 221, 216)
fT, fS, fH, fL, fN, fB, fSm, fD = (font(42), font(20, "Regular"), font(23, "SemiBold"), font(18, "Regular"), font(17, "Regular"),
                                   font(17, "SemiBold"), font(15, "Regular"), font(17, "SemiBold"))
fCap = font(14, "Medium")


def sk(v, nd=1):
    q = Decimal(str(v)).quantize(Decimal(1).scaleb(-nd), rounding=ROUND_HALF_UP)
    return f"{q:.{nd}f}".replace(".", ",").replace("-", "−")


class Cam:
    def __init__(self, path):
        d = json.load(open(path))
        self.d = d
        self.W, self.H = d["res"]
        self.Mwc = np.linalg.inv(np.array(d["matrix"]))

    def px(self, p):
        q = self.Mwc[:3, :3] @ np.asarray(p, float) + self.Mwc[:3, 3]
        if self.d["type"] == "ORTHO":
            k = self.W / self.d["ortho_scale"]
            return (self.W / 2 + q[0] * k, self.H / 2 - q[1] * k)
        if self.d.get("sensor_fit") == "VERTICAL":
            f = self.d["lens"] / self.d["sensor_height"] * self.H
        else:
            f = self.d["lens"] / self.d["sensor_width"] * self.W
        return (self.W / 2 + f * q[0] / -q[2], self.H / 2 - f * q[1] / -q[2])


class Panel:
    def __init__(self, img, cam, box, scale, at):
        self.cam, self.box, self.s, self.at = cam, box, scale, at
        im = img.crop(box)
        self.im = im.resize((int(round(im.width * scale)), int(round(im.height * scale))), Image.LANCZOS)

    def P(self, p):
        u, v = self.cam.px(p)
        return (self.at[0] + (u - self.box[0]) * self.s, self.at[1] + (v - self.box[1]) * self.s)

    def paste(self, S, bg=None):
        if bg is not None:
            b = Image.new("RGBA", self.im.size, bg + (255,)); b.alpha_composite(self.im)
            S.paste(b.convert("RGB"), (int(round(self.at[0])), int(round(self.at[1]))))
        else:
            S.paste(self.im, (int(round(self.at[0])), int(round(self.at[1]))), self.im)

    @property
    def w(self):
        return self.im.width

    @property
    def h(self):
        return self.im.height


def load(name):
    return Image.open(os.path.join(D, name + ".png")).convert("RGBA")


def cam(name):
    return Cam(os.path.join(D, name + "_cam.json"))


def tw(d, t, f):
    return d.textlength(t, font=f)


def nbsp(text):
    """Slovak typesetting: no single-letter preposition / conjunction at a line end, no number split from its unit"""
    import re
    text = re.sub(r"(?<![\w])([aikosuvzAIKOSUVZ]) ", "\\1\u00a0", text)
    return re.sub(r"(\d) (mm|°)", "\\1\u00a0\\2", text)


def wrap(d, text, f, width):
    text = nbsp(text)
    out = []
    for para in text.split("\n"):
        line = ""
        for w in para.split(" "):
            t = (line + " " + w).strip()
            if tw(d, t, f) <= width:
                line = t
            else:
                out.append(line); line = w
        out.append(line)
    return out


def header(d, title, intro, y=28):
    d.text((M, y), title, font=fT, fill=INK)
    lines = []
    for para in intro.split("\n"):
        lines += wrap(d, para, fS, SW - 2 * M)
    d.multiline_text((M, y + 62), "\n".join(lines), font=fS, fill=MUTED, spacing=8)
    return y + 62 + len(lines) * 28 + 18


def card(d, x0, y0, x1, y1):
    d.rounded_rectangle((x0, y0, x1, y1), 12, fill=CARD, outline=EDGE, width=2)


def dimh(d, xa, xb, y, text, f=fD, fill=DIM, ext=None, below=True, bg=CARD, sub=None):
    for ex, ey in (ext or []):
        d.line([(ex, ey), (ex, y + (6 if y > ey else -6))], fill=fill, width=1)
    d.line([(xa, y), (xb, y)], fill=fill, width=2)
    arrow_head(d, (xa, y), (xb, y), fill, 9); arrow_head(d, (xb, y), (xa, y), fill, 9)
    w = tw(d, text, f)
    tx = (xa + xb) / 2 - w / 2
    ty = y + 5 if below else y - f.size - 7
    if bg:
        d.rounded_rectangle((tx - 4, ty - 1, tx + w + 4, ty + f.size + 5), 4, fill=bg)
    d.text((tx, ty), text, font=f, fill=fill)


def rows_table(d, x, y, w, rows, lh=24):
    for a, b, sty in rows:
        bad = sty.endswith("!")
        sty = sty.rstrip("!")
        col = MUTED if sty == "sub" else INK
        fa = fN if sty != "sub" else fSm
        d.text((x, y), a, font=fa, fill=col)
        fb = fB if sty == "" else fN
        if sty == "sub":
            fb = fSm
        if isinstance(b, list):   # [(text, bad), ...] joined by " / ", only the failing values in red
            full = " / ".join(t for t, _ in b)
            assert tw(d, a, fa) + tw(d, full, fb) + 12 <= w, (a, full)
            xx = x + w - tw(d, full, fb)
            for k, (t, bb) in enumerate(b):
                if k:
                    d.text((xx, y), " / ", font=fb, fill=col)
                    xx += tw(d, " / ", fb)
                d.text((xx, y), t, font=fb, fill=RED if bb else col)
                xx += tw(d, t, fb)
            y += lh
            continue
        assert tw(d, a, fa) + tw(d, b, fb) + 12 <= w, (a, b)
        d.text((x + w, y), b, font=fb, fill=RED if bad else col, anchor="ra")
        y += lh
    return y


def caption(d, x, y, t):
    d.text((x, y), t, font=fCap, fill=MUTED)


def verdict(d, x0, y, w, t1, t2, col, f1, f2):
    d.rounded_rectangle((x0, y, x0 + w, y + 50), 8, fill=col)
    d.text((x0 + 10, y + 6), t1, font=f1, fill=(255, 255, 255))
    d.text((x0 + 10, y + 28), t2, font=f2, fill=(255, 255, 255))


def fit_verdict_fonts(d, items, w):
    for sz in (16, 15, 14, 13):
        f1, f2 = font(sz, "SemiBold"), font(sz - 1, "Regular")
        if all(tw(d, a, f1) <= w - 20 and tw(d, b, f2) <= w - 20 for a, b in items):
            return f1, f2
    raise SystemExit(f"verdict text too long: {items}")


def footer(d, y, text, width=SW - 2 * M):
    lines = []
    for para in text.split("\n"):
        lines += wrap(d, para, fSm, width)
    d.multiline_text((M, y), "\n".join(lines), font=fSm, fill=MUTED, spacing=6)
    return y + len(lines) * 21


def finish(S, ybot, name):
    S = S.crop((0, 0, S.width, int(ybot)))
    S.save(os.path.join(OUT, name), optimize=True)
    print(name, S.size)


def alpha_box(names, thr=8, pad=6):
    x0 = y0 = 10 ** 9; x1 = y1 = -1
    for n in names:
        a = np.asarray(load(n).split()[-1])
        ys, xs = np.nonzero(a > thr)
        x0, x1, y0, y1 = min(x0, xs.min()), max(x1, xs.max()), min(y0, ys.min()), max(y1, ys.max())
    im = load(names[0])
    return (max(0, int(x0) - pad), max(0, int(y0) - pad), min(im.width, int(x1) + pad + 1), min(im.height, int(y1) + pad + 1))


# ================================================================================================ 1 arm roundings
SV = ["B0", "B1", "B2", "B3"]
SNAME = {"B0": "B0 – dnešná B", "B1": "B1 – squircle", "B2": "B2 – kvapka", "B3": "B3 – plochý kryt"}
SIDEA = {"B0": "Dnešná B na porovnanie: mydlový kamienok so zrezaným, takmer rovným vrchom, šev na rovníku.",
         "B1": "Mäkký hranol: plochší kryt aj vnútro, tesná, ale plynulá hrana, obrys kapsuly; vrch je oblúk okolo kĺbu.",
         "B2": "Kvapka: plná a okrúhla pri kĺbe, pokojne sa zužuje k menšej špičke; šev s tieňovou škárou 0,35.",
         "B3": "Takmer rovná tvár krytu s mäkkým lemom; kryt presahuje vnútornú vaničku o 0,35 ako veko (R11)."}
SEAMT = {"B0": "0,5 ako dnes", "B1": "0,5 ako dnes", "B2": "tieňová škára 0,35", "B3": "kryt presahuje 0,35"}


def sheet_zaoblenia():
    cw = (SW - 2 * M - 3 * GC) // 4
    iw = cw - 20
    title = "NOVA mini · ruka B: varianty zaoblení"
    intro = ("Vybraná ruka B (vľavo B0 – ako je dnes) a tri modernejšie zaoblenia. Plocha ruky pri trupe, poloha švu a uchytenie ostávajú a medzera "
             "k trupu sa nikde nezhoršila. Obrázky v jednom riadku sú v rovnakej mierke. Kĺb ramena je zatiaľ všade dnešný (K0) – varianty kĺbu "
             "sú na ďalšom liste.")
    S = Image.new("RGB", (SW, 3200), BG)
    d = ImageDraw.Draw(S)
    y0 = header(d, title, intro) + 4
    # ---- geometry of the rows
    nid = max(len(wrap(d, SIDEA[v], fSm, cw - 28)) for v in SV)
    ycap1 = y0 + 12 + 34 + nid * 19 + 10
    yr1 = ycap1 + 22
    fc = cam("frontu")
    k = fc.W / fc.d["ortho_scale"]
    b1 = (fc.px((-80.0, 0, 0))[0], fc.px((0, 0, 89.5))[1], fc.px((80.0, 0, 0))[0], fc.px((0, 0, -86.2))[1])
    b1 = tuple(int(round(v)) for v in b1)
    s1 = iw / (b1[2] - b1[0])
    h1 = (b1[3] - b1[1]) * s1
    ydim = yr1 + h1 + 16
    ycap2 = ydim + 40
    yr2 = ycap2 + 22
    hc = cam("hero")
    b2 = alpha_box([f"hero_{v}_v3" for v in SV], thr=200, pad=34)
    s2 = iw / (b2[2] - b2[0])
    h2 = (b2[3] - b2[1]) * s2
    ycap3 = yr2 + h2 + 12
    yr3 = ycap3 + 22
    # arm alone: union boxes per view, one scale for all
    bz = alpha_box([f"look_zvonka_{v}" for v in SV] + [f"look_spredu_{v}" for v in SV], thr=8, pad=3)
    bzv = alpha_box([f"look_zvonka_{v}" for v in SV], thr=8, pad=3)
    bsp = alpha_box([f"look_spredu_{v}" for v in SV], thr=8, pad=3)
    bzh = alpha_box([f"look_zhora_{v}" for v in SV], thr=8, pad=3)
    bzv = (bzv[0], bz[1], bzv[2], bz[3]); bsp = (bsp[0], bz[1], bsp[2], bz[3])
    gap3 = 14
    s3 = (iw - 2 * gap3) / ((bzv[2] - bzv[0]) + (bsp[2] - bsp[0]) + (bzh[2] - bzh[0]))
    h3 = (bz[3] - bz[1]) * s3
    ytab = yr3 + h3 + 30
    rows_n = 10
    yj = ytab + rows_n * 24 + 8
    ycard1 = yj + 62
    JB = {"B0": ("kĺb M2b sa zmestí len tesne", f"stena {sk(NS['B0']['wall'], 2)}, rezerva len +0,085 mm", ORANGE)}
    for v in SV[1:]:
        JB[v] = (f"kĺb M2b sa zmestí, stena {sk(NS[v]['wall'], 2)}", f"rezerva +{sk(NS[v]['reserve'], 2)} mm (B0: +0,085)", GREEN)
    f1, f2 = fit_verdict_fonts(d, [(a, b) for a, b, _ in JB.values()], cw - 20)
    lv = fc.px((0, 0, 0))
    for i, v in enumerate(SV):
        n = NS[v]
        x0 = M + i * (cw + GC)
        card(d, x0, y0, x0 + cw, ycard1)
        d.text((x0 + 14, y0 + 12), SNAME[v], font=fH, fill=INK if v == "B0" else ACCENT)
        d.multiline_text((x0 + 14, y0 + 46), "\n".join(wrap(d, SIDEA[v], fSm, cw - 28)), font=fSm, fill=MUTED, spacing=4)
        # row 1: front (upper robot)
        caption(d, x0 + 14, ycap1, "spredu" if i else "spredu (bez podstavca)")
        p1 = Panel(load(f"frontu_{v}_v3"), fc, b1, s1, (x0 + 10, yr1))
        p1.paste(S)
        pa, pb = p1.P((-n["out_x"], 0, n["out_z"])), p1.P((n["out_x"], 0, n["out_z"]))
        dimh(d, pa[0], pb[0], ydim, f"šírka cez ruky {sk(n['robot_width'])} mm", f=font(15, "SemiBold"),
             ext=[(pa[0], pa[1] + 5), (pb[0], pb[1] + 5)], below=True)
        # row 2: hero
        caption(d, x0 + 14, ycap2, "šikmo spredu · ľavá ruka hore 90°")
        p2 = Panel(load(f"hero_{v}_v3"), hc, b2, s2, (x0 + 10, yr2))
        p2.im = feather(p2.im, 24)
        p2.paste(S)
        # row 3: arm alone
        caption(d, x0 + 14, ycap3, "samotná ľavá ruka (rovnaká mierka)")
        xa = x0 + 10
        for nm, bx in (("zvonka", bzv), ("spredu", bsp), ("zhora", bzh)):
            pv = Panel(load(f"look_{nm}_{v}"), None, bx, s3, (xa, yr3))
            pv.paste(S)
            lab_y = yr3 + pv.h + 4
            d.text((xa + pv.w / 2, lab_y), nm, font=font(13, "Regular"), fill=MUTED, anchor="ma")
            xa += pv.w + gap3
        rows = [("hrúbka max / pri kĺbe", f"{sk(n['t_max'])} / {sk(n['t_joint'])}", ""),
                ("  kryt / vnútro pri kĺbe", f"{sk(n['cover_joint'])} / {sk(n['inner_joint'])}", "sub"),
                ("šírka spredu dozadu", sk(n["w_max"]), ""),
                ("šírka cez ruky", sk(n["robot_width"]), ""),
                ("medzera k trupu v pokoji", sk(n["gap_rest"], 2), ""),
                ("  najmenšia pri pohybe", sk(n["gap_min"], 2), "sub"),
                ("stena nad kĺbom (M2b)", sk(n["wall"], 2), "!" if n["wall"] < 2.0 else ""),
                ("  za magnetom kryt / vnútro", [(sk(n['post_cover'], 2), n["post_cover"] < 1.2), (sk(n['post_inner'], 2), n["post_inner"] < 1.2)],
                 "sub"),
                ("šev", SEAMT[v], ""),
                ("najmenší polomer krytu", sk(n["r_min_cover"]), "sub")]
        assert len(rows) == rows_n
        rows_table(d, x0 + 14, ytab, cw - 28, rows)
        a, b, col = JB[v]
        verdict(d, x0 + 10, yj, cw - 20, a, b, col, f1, f2)
    yf = ycard1 + 18
    s = {v: NS[v] for v in SV}
    foot = ("Rozmery v mm. Hrúbka = do strany (k trupu – von), šírka = spredu dozadu. Medzera k trupu nezávisle prepočítaná: v pokoji a najmenšia pri "
            "pohybe −45° … +135°; pri skrytom doraze +140,5° je " + " · ".join(f"{v} {sk(s[v]['gap_stop'], 2)}" for v in SV) + ".\n"
            "Stena nad kĺbom = najtenšie miesto plastu nad unášačom kĺbu M2b. Kĺb sa zmestí od 1,5 (stena 1,2 + vôľa 0,3), cieľ je ≥ 2,0 "
            "(rezerva aspoň 0,5) – B0 ho nesplní (červená hodnota). Kĺb sa ešte prerobí na ložisko 6700ZZ – M2b je zatiaľ len priestor, "
            "ktorý mechanika v ruke potrebuje.\n"
            "Stena za magnetom (treba ≥ 1,2): B0 má na kryte len 0,85 – nevyhovuje. B2 má na kryte len tesných 1,22 a B3 vo vnútri 1,43 "
            "(inde má vnútorná polovica stenu 1,6), preto pri nich treba posunúť os magnetov na 3,7 mm od okraja: "
            f"B2 {sk(s['B2']['post37_cover'], 2)} / {sk(s['B2']['post37_inner'], 2)}, "
            f"B3 {sk(s['B3']['post37_cover'], 2)} / {sk(s['B3']['post37_inner'], 2)}. B1 nepotrebuje nič.\n"
            "Najmenší polomer krytu je tesne nad čiernou špičkou; všetky sa dajú vytlačiť so stenou 1,2. B3 má presah krytu, preto sa steny krytu "
            "a vaničky na šve prekrývajú len 0,85 mm – spoj musí niesť plánovaný vodiaci lem.\n"
            "Šírka cez ruky: podstavec má 146 mm, takže je stále najširším miestom robota. Koncept na posúdenie tvaru, nie výkres.")
    yb = footer(d, yf, foot) + 22
    finish(S, yb, "v4_ruka_B_zaoblenia.png")


# ================================================================================================ 2 shoulder joint
KV = ["K0", "K1", "K2", "K3"]
KNAME = {"K0": "K0 – dnes: krúžok D13", "K1": "K1 – golier D22", "K2": "K2 – kryt D26 v trupe", "K3": "K3 – jeden valec D26"}
KIDEA = {"K0": "Medzi trupom a rukou je vidieť len tenký čierny krúžok zo zátky (medzera 3,7 mm). Referencia, nič sa nemení.",
         "K1": "Čierny golier je súčasťou ruky a točí sa s ňou; zasúva sa do plytkého vybrania v zátke. Koniec má mäkké zaoblenie R1,5.",
         "K2": "Zátka vyrastie z jamky trupu ako pevný čierny valec D26,4 (ako kryt 04 na R08). Ruka sa nemení, v medzere ostáva krúžok D13.",
         "K3": "Pevný kryt D26,4 z trupu + čierny prstenec D26,2 na ruke, škára 0,9: pôsobí ako jeden veľký čierny valec (R01, R08)."}
KROT = {"K0": "trupom (pevný)", "K1": "rukou", "K2": "trupom (pevný)", "K3": "kryt trupom, prstenec rukou"}
KCLR = {"K0": [("krúžok – otvor v ruke (vnútri)", "0,50"), ("skrutky zátky – ruka", "3,28")],
        "K1": [("golier – vybranie v zátke", "0,90"), ("golier – hrdlo zátky (skryté)", "0,40")],
        "K2": [("ruka – pevný kryt (vždy)", "1,29"), ("kryt – jamka v trupe", "0,80")],
        "K3": [("prstenec – kryt / jamka", "0,89 / 0,90"), ("biela ruka – kryt (vždy)", "2,16")]}
KCHG = {"K0": "Nič.",
        "K1": "Nová zátka s plytkým vybraním. Čierny náboj s golierom sa lepí do ruky, otvor v ruke D14 → D22.",
        "K2": "Len nová zátka s krytom. Ruka ani jej mechanika sa nemenia (najlacnejšie).",
        "K3": "Nová zátka s krytom (ako K2). Čierny náboj s prstencom sa lepí do ruky, otvor v ruke D14 → D26,4."}
KVER = {"K0": ("funguje, ale pôsobí úzko", "čierny pás spredu len 12,8 mm", ORANGE),
        "K1": ("zmestí sa, všetky vôle OK", "treba osový doraz lepeného náboja", GREEN),
        "K2": ("zmestí sa, ruka je však 1,29 od krytu", "dnes 3,70; spodok kĺbu ostáva úzky", ORANGE),
        "K3": ("odporúčam – zmestí sa, vôle OK", "treba doraz náboja a zraziť hranu otvoru", GREEN)}


def sheet_klb():
    cw = (SW - 2 * M - 3 * GC) // 4
    iw = cw - 20
    title = "NOVA mini · kĺb ramena: varianty"
    intro = ("Ľavé rameno s rukou B0, rovnaké kamery a mierka pre všetky varianty. Tvar ruky aj biela medzera ruka–trup ostávajú; mení sa len čierny "
             "kĺb medzi nimi (inšpirácia R01 a R08). Čierne diely sú rotačne súmerné okolo osi ramena, preto majú rovnakú vôľu v každej polohe ruky.")
    S = Image.new("RGB", (SW, 3400), BG)
    d = ImageDraw.Draw(S)
    y0 = header(d, title, intro) + 4
    nid = max(len(wrap(d, KIDEA[v], fSm, cw - 28)) for v in KV)
    ycap1 = y0 + 12 + 34 + nid * 19 + 10
    yr1 = ycap1 + 22
    kc = cam("kfront")
    s1 = iw / kc.W
    h1 = kc.H * s1
    ycap2 = yr1 + h1 + 12
    yr2 = ycap2 + 22
    pc = cam("kp34")
    s2 = iw / pc.W
    h2 = pc.H * s2
    ycap3 = yr2 + h2 + 12
    yr3 = ycap3 + 22
    rc = cam("kp34r")
    h3 = rc.H * (iw / rc.W)
    ycap4 = yr3 + h3 + 12
    yr4 = ycap4 + 22
    wc = cam("frontw")
    b4 = (wc.px((-80.0, 0, 0))[0], wc.px((0, 0, 89.5))[1], wc.px((80.0, 0, 0))[0], wc.px((0, 0, -117.5))[1])
    b4 = tuple(int(round(v)) for v in b4)
    w4 = int(iw * 0.80)
    s4 = w4 / (b4[2] - b4[0])
    h4 = (b4[3] - b4[1]) * s4
    ytab = yr4 + h4 + 16
    rows_n = 8
    ychg = ytab + rows_n * 24 + 6
    nchg = max(len(wrap(d, KCHG[v], fSm, cw - 28)) for v in KV)
    yj = ychg + 22 + nchg * 19 + 10
    ycard1 = yj + 62
    f1, f2 = fit_verdict_fonts(d, [(a, b) for a, b, _ in KVER.values()], cw - 20)
    for i, v in enumerate(KV):
        n = NJ[v]
        x0 = M + i * (cw + GC)
        card(d, x0, y0, x0 + cw, ycard1)
        d.text((x0 + 14, y0 + 12), KNAME[v], font=fH, fill=INK if v == "K0" else ACCENT)
        d.multiline_text((x0 + 14, y0 + 46), "\n".join(wrap(d, KIDEA[v], fSm, cw - 28)), font=fSm, fill=MUTED, spacing=4)
        caption(d, x0 + 14, ycap1, "spredu – detail ľavého ramena")
        p1 = Panel(load(f"kfront_B0_{v}"), kc, (0, 0, kc.W, kc.H), s1, (x0 + 10, yr1))
        p1.paste(S, bg=(255, 255, 255))
        caption(d, x0 + 14, ycap2, "šikmo spredu · ruka visí")
        Panel(load(f"kp34_B0_{v}"), pc, (0, 0, pc.W, pc.H), s2, (x0 + 10, yr2)).paste(S, bg=(255, 255, 255))
        caption(d, x0 + 14, ycap3, "šikmo spredu · ľavá ruka hore 90°")
        Panel(load(f"kp34r_B0_{v}"), rc, (0, 0, rc.W, rc.H), iw / rc.W, (x0 + 10, yr3)).paste(S, bg=(255, 255, 255))
        caption(d, x0 + 14, ycap4, "celý robot spredu")
        Panel(load(f"frontw_B0_{v}"), wc, b4, s4, (x0 + 10 + (iw - w4) / 2, yr4)).paste(S)
        g = n["gap"]
        rows = [("viditeľný priemer", "Ø " + (sk(n["visible_d"]) if n["visible_d"] % 1 else str(int(n["visible_d"]))), ""),
                ("čierny pás spredu (výška)", sk(n["band"]), ""),
                ("točí sa s", KROT[v], "sub"),
                ("biela medzera ruka–trup", f"{sk(g['rest'], 2)} / {sk(g['at_135'], 2)}", ""),
                ("  v pokoji / pri 135°", "", "sub")] + [(a, b, "") for a, b in KCLR[v]] + [("šírka cez ruky", sk(n["width"]), "")]
        assert len(rows) == rows_n, len(rows)
        rows_table(d, x0 + 14, ytab, cw - 28, rows)
        d.text((x0 + 14, ychg), "Čo sa mení:", font=fB, fill=INK)
        d.multiline_text((x0 + 14, ychg + 22), "\n".join(wrap(d, KCHG[v], fSm, cw - 28)), font=fSm, fill=INK, spacing=4)
        a, b, col = KVER[v]
        verdict(d, x0 + 10, yj, cw - 20, a, b, col, f1, f2)
    yf = ycard1 + 18
    k3v = NJ["K3v"]
    foot = ("Rozmery v mm, vôle nezávisle prepočítané zo sietí (krok 1°). Biela medzera ruka–trup je vo všetkých variantoch ako dnes: 3,70 v pokoji, "
            "1,12 pri 135°, 0,97 pri skrytom doraze +140,5°. Čierny pás = výška čiernej plochy medzi trupom a rukou v pohľade spredu.\n"
            "Pravidlá: vôľa medzi dielmi, ktoré sa voči sebe otáčajú, ≥ 0,3; viditeľná medzera otáčajúci sa diel – trup ≥ 0,8; steny ≥ 1,2. "
            "K2: ruka je od pevného krytu 1,29 namiesto dnešných 3,70 k trupu (≥ 1,0 je splnené, ale je to menej ako dnes).\n"
            "K1 a K3: čierny náboj sa lepí do bielej ruky – potrebuje osový doraz (osadenie alebo 3 rebrá), inak by medzera závisela od presnosti lepenia. "
            f"K3: biely lem okolo otvoru D26,4 je pri ruke B0 vpredu a vzadu len 1,7 mm (pri B1 {sk(CC['B1']['band_front'])}, "
            f"pri B2 {sk(CC['B2']['band_front'])}) – hranu treba zraziť o 0,3–0,5.\n"
            "Zátky všetkých variantov (aj K0) majú zatiaľ vnútro z modelu v2 – sú len na vizualizáciu; vnútro sa prerobí spolu s kĺbom na ložisko 6700ZZ.\n"
            f"Voliteľne K3v = K3 a ruka o 1,5 mm ďalej: kĺb je dlhší, biela medzera {sk(k3v['gap']['rest'], 2)} / {sk(k3v['gap']['at_135'], 2)}, "
            f"ale robot má {sk(k3v['width'])} mm (širší ako podstavec 146) a treba dlhšiu skrutku pohonu – len ak by K3 bolo stále málo.")
    yb = footer(d, yf, foot) + 22
    finish(S, yb, "v4_klb_ramena.png")


KBAND = {}


def main():
    ks = json.load(open("/tmp/claude-0/gapwf/fin/R4/klb/klb_summary.json"))
    for v in ("K0", "K1", "K2", "K3", "K3v"):
        KBAND[v] = ks[v]["front_band"]["band_z"]
    if not ONLY or "zaoblenia" in ONLY:
        sheet_zaoblenia()
    if not ONLY or "klb" in ONLY:
        sheet_klb()
    if "odporucanie" in ONLY:
        import sheet3_r4
        sheet3_r4.run(sys.modules[__name__])


main()
