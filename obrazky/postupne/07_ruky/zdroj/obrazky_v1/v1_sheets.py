"""NOVA mini - arm proposal v1: labelled Slovak sheets from the renders of v1_scene.py.
Usage: /opt/venv/cad/bin/python v1_sheets.py <render_dir> <out_dir> [spredu rez rozlozena rozsah hero]"""
import sys, os, json, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T4/overenie3")
import v1geo as V
from sheetlib import (font, Cam, feather, dashed, dim_h, dim_v, place, badge, crop_alpha, arrow_head, BG, INK, MUTED, ACCENT, DIM)

D, OUT = sys.argv[1], sys.argv[2]
ONLY = sys.argv[3:]
os.makedirs(OUT, exist_ok=True)
fTitle, fSub, fPan, fLab, fSmall, fDim, fNum = font(50), font(26, "Regular"), font(34), font(25, "Medium"), font(22, "Regular"), font(26, "SemiBold"), font(22)
WHITE_BG = (255, 255, 255, 215)


def load(name):
    return Image.open(os.path.join(D, name + ".png")).convert("RGBA")


def header(d, title, intro, x=44, y=34):
    d.text((x, y), title, font=fTitle, fill=INK)
    d.multiline_text((x, y + 76), intro, font=fSub, fill=MUTED, spacing=10)
    return y + 76 + (intro.count("\n") + 1) * 37 + 20


def note(d, xy, text, anchor, fnt=fLab, color=ACCENT, box=True):
    """free label at pixel xy (top-left) with a leader to the pixel anchor"""
    x, y = xy
    lines = text.split("\n")
    w = max(d.textlength(t, font=fnt) for t in lines)
    h = len(lines) * (fnt.size + 8)
    if box:
        d.rounded_rectangle([x - 8, y - 6, x + w + 8, y + h + 2], 6, fill=(255, 255, 255))
    d.multiline_text((x, y), text, font=fnt, fill=INK, spacing=8)
    if anchor is not None:
        ax, ay = anchor
        sx = x - 8 if ax < x else (x + w + 8 if ax > x + w else ax)
        sy = y + h / 2 if (ax < x or ax > x + w) else (y - 6 if ay < y else y + h + 2)
        d.line([(sx, sy), (ax, ay)], fill=color, width=3)
        d.ellipse([ax - 6, ay - 6, ax + 6, ay + 6], fill=color, outline=(255, 255, 255), width=2)


def pebble_section(y0, dx, inset=0.0, z_rng=(-72.0, 1.2), n=500):
    """outline of the pebble cut by the plane y = y0 (polygon in (x, z))"""
    L, R = [], []
    for z in np.linspace(*z_rng, n):
        a, b = V.skins(y0, float(z), inset, dx)
        if a is None:
            continue
        L.append((a, z)); R.append((b, z))
    return R + L[::-1] + [R[0]] if R else []


# ================================================================================================ 1 front comparison
def sheet_spredu():
    A_, B_ = load("front_A"), load("front_B")
    cam = Cam(os.path.join(D, "front_B_cam.json"))
    k = cam.k()
    W0, H0 = A_.size
    crop_w = int(2 * 112 * k)                       # +-112 mm around the centre
    cx0 = int(W0 / 2 - crop_w / 2)
    ytop = int(cam.px((0, 0, 92.0))[1]); ybot = H0
    panA = A_.crop((cx0, ytop, cx0 + crop_w, ybot)); panB = B_.crop((cx0, ytop, cx0 + crop_w, ybot))
    PW, PH = panA.size
    gap = 70
    title = "NOVA mini · ruky – návrh v1: porovnanie spredu"
    intro = ("Pohľad spredu, pravouhlý, rovnaká mierka. Vľavo schválený tvar – servo sa do ruky nezmestí: na osi ramena ostáva len 13,3 mm.\n"
             "Vpravo návrh v1: biela ruka (presne schválený tvar) je o 12 mm ďalej od trupu a medzi ňou a trupom je dlhší čierny kĺb.")
    tmp = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    W = int(max(2 * PW + gap + 2 * 50, tmp.textlength(title, font=fTitle) + 100, max(tmp.textlength(t, font=fSub) for t in intro.split("\n")) + 100))
    xm = (W - (2 * PW + gap)) // 2
    S = Image.new("RGB", (W, 260 + 60 + PH + 400), BG)
    d = ImageDraw.Draw(S)
    yb = header(d, title, intro)
    yp = yb + 70
    xs = (xm, xm + PW + gap)
    for (pan, ttl), x0 in zip(((panA, "schválené (servo sa nezmestí)"), (panB, "návrh v1: ruka o 12 mm ďalej, dlhší čierny kĺb")), xs):
        yfl0 = yp + cam.px((0, 0, V_Z_FLOOR))[1] - ytop
        d.rounded_rectangle([x0 - 10, yp - 62, x0 + PW + 10, yfl0 + 190], 14, fill=(250, 250, 248), outline=(222, 222, 218), width=2)
        d.text((x0 + 14, yp - 50), ttl, font=fPan, fill=INK)
        S.paste(pan, (x0, yp), pan)

    def P(x0, p):
        u, v = cam.px(p)
        return (x0 + u - cx0, yp + v - ytop)

    for which, x0 in (("A", xs[0]), ("B", xs[1])):
        dx = 0.0 if which == "A" else V.DX
        rows, _, _ = V.pebble_rows(120, 160)
        Wp = V.to_world(rows.reshape(-1, 3), dx)
        i = int(np.argmax(Wp[:, 0])); xa, za = float(Wp[i, 0]), float(Wp[i, 2])
        yfl = P(x0, (0, 0, V_Z_FLOOR))[1]
        # base width
        bl, br = P(x0, (-73.0, 0, -100.0)), P(x0, (73.0, 0, -100.0))
        dim_h(d, bl[0], br[0], yfl + 50, "podstavec 146 – zatiaľ len tvar", fDim, fill=MUTED, ext=[(bl[0], bl[1] + 20), (br[0], br[1] + 20)], text_above=False)
        al, ar = P(x0, (-xa, 0, za)), P(x0, (xa, 0, za))
        width = 2 * xa
        dim_h(d, al[0], ar[0], yfl + 135, f"celková šírka {width:.0f} mm", fDim, fill=DIM, ext=[(al[0], al[1] + 12), (ar[0], ar[1] + 12)],
              text_above=False)
        if which == "A":
            j = P(x0, (-48.6, -14.0, -27.0))
            note(d, (x0 + 22, yp + 170), "čierny kĺb\ndnes ~4 mm\n(servo sa\nnezmestí)", j, fSmall)
        else:
            j = P(x0, (-56.5, -13.5, -24.0))
            note(d, (x0 + 22, yp + 170), "kryt kĺbu\n(nový, čierny,\notáča sa\ns rukou)", j, fSmall)
            zt = 10.0
            a1 = P(x0, (78.67, 0, zt)); a2 = P(x0, (90.67, 0, zt))
            dashed(d, [P(x0, (78.67, 0, zt - 1.5)), P(x0, (78.67, 0, -60.0))], (120, 120, 128), width=2, dash=8, gap=6)
            d.line([P(x0, (90.67, 0, zt - 1.5)), P(x0, (90.67, 0, za))], fill=DIM, width=2)
            d.line([a1, a2], fill=DIM, width=3); arrow_head(d, a1, a2, DIM); arrow_head(d, a2, a1, DIM)
            tw = d.textlength("+12 mm", font=fDim)
            d.text((a2[0] - tw, a1[1] - fDim.size - 12), "+12 mm", font=fDim, fill=DIM)
        ybox = yfl + 135 + 50
    foot = ("Rozmery v mm. Tvar bielej ruky je presne schválený (T3): dĺžka 72, hrúbka 23,0, šírka 33,6 – v1 ju len posúva von (čiarkovaná čiara vpravo = koniec schválenej ruky).\n"
            "Posun 12 mm je ilustračný, skutočný bude 11–14 mm podľa zmeraného serva.\n"
            "Ruky v1 presahujú podstavec (146 mm) – podstavec by mal mať šírku ≥ ~190 mm (rozhodne sa pri jeho návrhu).")
    yfoot = yp + cam.px((0, 0, V_Z_FLOOR))[1] - ytop + 215
    d.multiline_text((xm, yfoot), foot, font=fSmall, fill=MUTED, spacing=8)
    S = S.crop((0, 0, W, int(yfoot + 115)))
    S.save(os.path.join(OUT, "v1_spredu_porovnanie.png"), optimize=True)
    print("spredu", S.size)


V_Z_FLOOR = -116.5


# ================================================================================================ 2 section
def nearest_on_plane(stl, guess, y0=3.0, tol=0.35, behind=False):
    import vlib
    T = vlib.load_stl(stl)
    P = vlib.sample_surface(T, 0.25)
    m = np.abs(P[:, 1] - y0) < tol if not behind else (P[:, 1] > y0)
    P = P[m]
    i = np.argmin(np.linalg.norm(P[:, [0, 2]] - np.array([guess[0], guess[2]]), axis=1))
    return (float(P[i, 0]), y0, float(P[i, 2]))


def sheet_rez():
    im = load("rez")
    cam = Cam(os.path.join(D, "rez_cam.json"))
    k = cam.k()
    IW, IH = im.size
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
    do = ImageDraw.Draw(ov)
    z_ax = V.ZS
    P = lambda x, z: cam.px((x, V.SH_Y, z))
    # approved pebble (dx 0) outline - dashed
    poly = pebble_section(V.SH_Y, 0.0)
    dashed(do, [P(x, z) for x, z in poly], (70, 70, 80, 255), width=3, dash=14, gap=9)
    # shoulder axis (dash-dot)
    dashed(do, [P(30.0, z_ax), P(93.5, z_ax)], (40, 40, 40, 200), width=2, dash=22, gap=6)
    # dimension rows above the arm
    x_end, x_wall0, x_case1, x_wall1 = V.X_END, V.skins(V.SH_Y, z_ax, V.WALL, 0.0)[1], V.X_CASE1, V.skins(V.SH_Y, z_ax, V.WALL, V.DX)[1]
    rows = [(14.6, x_end, x_wall0, f"dnes len {x_wall0 - x_end:.1f} mm voľného miesta".replace(".", ","), (120, 120, 128, 255)),
            (10.6, x_end, x_case1, f"servo potrebuje ~{V.SERVO['H']:.1f} + 0,3 mm".replace(".", ","), (140, 60, 170, 255)),
            (6.6, x_end, x_wall1, f"v1: {x_wall1 - x_end:.1f} mm (ruka o 12 mm ďalej)".replace(".", ","), DIM + (255,))]
    for z, xa, xb, txt, col in rows:
        pa, pb = P(xa, z), P(xb, z)
        for xx in (xa, xb):
            dashed(do, [P(xx, z_ax), P(xx, z - 0.5)], col[:3] + (150,), width=2, dash=6, gap=5)
        do.line([pa, pb], fill=col, width=3)
        arrow_head(do, pa, pb, col); arrow_head(do, pb, pa, col)
        w = do.textlength(txt, font=fDim)
        tx = pa[0] - 14 - w
        do.rounded_rectangle([tx - 6, pa[1] - fDim.size / 2 - 5, tx + w + 6, pa[1] + fDim.size / 2 + 7], 5, fill=(255, 255, 255, 235))
        do.text((tx, pa[1] - fDim.size / 2 - 2), txt, font=fDim, fill=col)
    # shift 12 mm at z -46 between the approved and the new outer skin
    zs = -57.0
    xo0, xo1 = V.skins(V.SH_Y, zs, 0.0, 0.0)[1], V.skins(V.SH_Y, zs, 0.0, V.DX)[1]
    pa, pb = P(xo0, zs), P(xo1, zs)
    do.line([pa, pb], fill=DIM, width=3); arrow_head(do, pa, pb, DIM); arrow_head(do, pb, pa, DIM)
    t = "posun 12"
    w = do.textlength(t, font=fDim)
    do.rounded_rectangle([(pa[0] + pb[0]) / 2 - w / 2 - 5, pa[1] - 40, (pa[0] + pb[0]) / 2 + w / 2 + 5, pa[1] - 8], 5, fill=(255, 255, 255, 225))
    do.text(((pa[0] + pb[0]) / 2 - w / 2, pa[1] - 38), t, font=fDim, fill=DIM)
    im.alpha_composite(ov)
    # ---- anchors (world points on / behind the cut plane)
    T4S = "/tmp/claude-0/gapwf/fin/T4/stl/"
    ab = lambda a, b=0.0: float(V.ab_to_yz(a, b)[1])
    xin = lambda z: V.skins(V.SH_Y, z)[0]
    xout = lambda z: V.skins(V.SH_Y, z)[1]
    zseam = None
    for z in np.linspace(1.0, -10, 400):
        a, b = V.skins(V.SH_Y, float(z))
        if a is not None and a <= V.x_at_local_x(V.SH_Y, float(z), 0.0) <= b:
            zseam = float(z); break
    mg = V.to_world(V.magnet_spots_local()[3] + np.array([1.2, 0, 0]))
    L = {
        "bok": (nearest_on_plane(T4S + "T_bok_L.stl", (49.0, 3, -46.0)), "bočný kryt trupu T_bok (biely)"),
        "stlp": (nearest_on_plane(T4S + "T_spodok.stl", (36.6, 3, -25.0)), "stĺp trupu (T_spodok), čelo x 38,4"),
        "klb": ((46.0, 3, z_ax + 9.5), "T_klb – ramenný kĺb trupu (bez zmeny)"),
        "kruzok": ((39.65, 3, z_ax - 3.8), "dištančný krúžok ~2,4 mm (doplniť)"),
        "pruz": ((41.45, 3, z_ax + 3.9), "2 tanierové pružinky 10 × 5,2 × 0,4"),
        "puzdro": ((50.0, 3, z_ax - 2.6), "drážkované puzdro Ø8, príruba Ø10 × 2"),
        "drazka": ((45.0, 3.4, z_ax - 11.45), "drážka pre kábel pod T_klb (už v trupe)"),
        "cap": ((56.0, 3, z_ax - 10.5), "čap Ø22 (T_klb) – nesie ruku"),
        "kryt": ((57.5, 3, z_ax + 14.9), "kryt kĺbu (čierny, otáča sa s rukou)"),
        "oring": ((V.ORING["x"], 3, z_ax + 11.45), "O-krúžok (drží ruku osovo)"),
        "komora": ((52.6, 3.4, z_ax - 13.4), "komôrka kábla: 3 vodiče, pol otáčky"),
        "kanal": ((58.2, 3.4, z_ax + 13.42), "kanálik kábla do ruky"),
        "puzdro_lozisko": ((55.0, 3, z_ax + 11.9), "puzdro krytu na čape (klzné, ~6 mm)"),
        "hriadel": ((56.6, 3, z_ax + 0.6), "hriadeľ serva (20 z, Ø3,95 – overiť)"),
        "servo": ((72.0, 3, z_ax - 8.0), "servo Feetech SCS0009 – telo\n23,2 × 12,1 × ~21,5 (neoverené)"),
        "kon": ((68.0, 3.5, ab(-8.8)), "konektor JST-SH 3p (v ruke)"),
        "vnut": ((xin(-42.0) + 1.0, 3, -42.0), "vnútorná škrupina (nosná,\nlôžko serva), stena 2,0"),
        "vonk": ((xout(-30.0) - 1.0, 3, -30.0), "vonkajšia škrupina (kryt),\nstena 2,0, drží na magnetoch"),
        "sev": ((V.x_at_local_x(V.SH_Y, zseam - 1.0, 0.0), 3, zseam - 1.0), "šev 0,5 medzi škrupinami"),
        "lozko": ((xin(ab(18.3)) + 2.5, 3, ab(18.3)), "lôžko serva (doraz)"),
        "magnet": (tuple(mg), "magnety Ø3 × 2 (4 páry)"),
        "spicka": ((xin(-63.0) + 1.0, 3, -63.0), "čierna vložka špičky"),
    }
    LEFT = {"bok", "stlp", "klb", "kruzok", "pruz", "puzdro", "drazka", "cap", "komora", "kryt", "oring", "puzdro_lozisko", "kanal", "hriadel"}
    colw = 640
    W = IW + 2 * colw
    title = "NOVA mini · ruky – návrh v1: rez ľavým ramenom"
    intro = ("Rez zvislou rovinou cez os ramena (y = 3), pohľad spredu; ľavá strana robota je vpravo. Čiarkovane = schválená poloha ruky.\n"
             "Servo sedí hriadeľom priamo na osi, drážkovaným puzdrom sa opiera o trup; ruka sa točí na čape Ø22 (T_klb). Trup sa netlačí znova.\n"
             "Puzdro tlačia 2 tanierové pružinky na osadenie v T_klb = trecia spojka ≈ 0,12–0,15 N·m (ruka pri silnom zatlačení prešmykne).\n"
             "Farba rezu: oranžová = biela živica · modré odtiene = čierna živica · fialová = servo · sivá = kov · červená = O-krúžok.")
    top = 34 + 76 + 4 * 37 + 40
    foot = ("Koncept na posúdenie, nie výkres na tlač. Rozmery serva SCS0009 sú neoverené (výška tela bez hriadeľa ~21,5 je odhad; nákružok Ø7 × 1, drážkovanie Ø3,95 × 3).\n"
            "Posun ruky 12 mm je ilustračný – skutočný bude 11–14 mm podľa zmeraného serva. Vybranie Ø10,2 v T_klb je od čela stĺpa (x 38,4) po osadenie (x 44,0) dlhé 5,6 mm:\n"
            "príruba 2 mm + 2 pružinky ~1,2 mm ho nevyplnia, preto je v modeli dištančný krúžok ~2,4 mm (alebo hrubšia príruba puzdra, alebo 4 pružinky).\n"
            "Kábel: 3 vodiče idú z trupu drážkou pod T_klb do komôrky, obtáčajú čap pol otáčky (zozadu) a kanálikom hore vchádzajú do ruky ku konektoru.")
    H = top + IH + 30 + 4 * 32 + 40
    S = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(S)
    header(d, title, intro)
    ix0, yi = colw, top
    bgi = Image.new("RGBA", im.size, (255, 255, 255, 255)); bgi.alpha_composite(im)
    S.paste(bgi, (ix0, yi))
    d.rectangle([ix0, yi, ix0 + IW - 1, yi + IH - 1], outline=(215, 215, 210), width=2)
    sides = {"L": [], "R": []}
    for key, (p, txt) in L.items():
        u, v = cam.px(p)
        u, v = min(max(u, 4), IW - 4), min(max(v, 4), IH - 4)
        sides["L" if key in LEFT else "R"].append([v, u, txt])
    place(d, sides["L"], "L", 0, colw, yi, IH, ix0, fLab, LH=30, gap=12)
    place(d, sides["R"], "R", colw + IW, colw, yi, IH, ix0, fLab, LH=31, gap=16)
    d.multiline_text((44, yi + IH + 26), foot, font=fSmall, fill=MUTED, spacing=9)
    S.save(os.path.join(OUT, "v1_rez_ramenom.png"), optimize=True)
    print("rez", S.size)


# ================================================================================================ 3 exploded
def sheet_rozlozena():
    im = load("rozlozena")
    cam = Cam(os.path.join(D, "rozlozena_cam.json"))
    IW, IH = im.size
    A = cam.anchors
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0)); do = ImageDraw.Draw(ov)
    if "os" in cam.lines:
        p0, p1 = cam.lines["os"]
        dashed(do, [p0, p1], (60, 60, 70, 140), width=2, dash=26, gap=8)
    bgi = Image.new("RGBA", im.size, (0, 0, 0, 0)); bgi.alpha_composite(ov); bgi.alpha_composite(im)
    items = [("kruzok", "dištančný krúžok ~2,4 mm (doplniť)", "up"),
             ("pruz", "2 tanierové pružinky 10 × 5,2 × 0,4", "up"),
             ("puzdro", "drážkované puzdro Ø8 (príruba Ø10 × 2)", "down"),
             ("T_klb", "T_klb – ramenný kĺb trupu (bez zmeny)", "up"),
             ("oring", "O-krúžok na čap Ø22", "up"),
             ("kryt", "kryt kĺbu s komôrkou kábla (čierny)", "up"),
             ("servo", "servo Feetech SCS0009", "down"),
             ("konektor", "konektor JST-SH 3p", "up"),
             ("vnut", "vnútorná škrupina s lôžkom serva", "down"),
             ("spicka", "čierna vložka špičky (nalepená)", "down"),
             ("mag_vnu", "4 magnety Ø3 × 2 – vnútorná škrupina", "up"),
             ("mag_von", "4 magnety Ø3 × 2 – vonkajšia škrupina", "up"),
             ("vonk", "vonkajšia škrupina (drží na magnetoch)", "up")]
    title = "NOVA mini · ruky – návrh v1: rozložená ľavá ruka"
    intro = ("Rozložené pozdĺž osi ramena, pohľad spredu zľava zhora. Čísla = poradie montáže od trupu von.\n"
             "Puzdro s pružinkami sa vkladá zvnútra pod T_klb (T_klb je preto na obrázku vysunutý); trup sa netlačí znova.")
    top = 34 + 76 + 2 * 37 + 30
    ncol = 2
    rows_n = math.ceil(len(items) / ncol)
    W = max(IW + 80, 1700)
    H = top + IH + 40 + rows_n * 40 + 140
    S = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(S)
    header(d, title, intro)
    ix0, yi = (W - IW) // 2, top
    S.paste(bgi, (ix0, yi), bgi)
    used = []
    for n, (key, txt, dr) in enumerate(items, 1):
        if key not in A:
            print("missing anchor", key); continue
        u, v = A[key]
        sg = -1 if dr == "up" else 1
        bx, by = ix0 + u, yi + v + sg * 60
        for _ in range(20):
            if all(math.hypot(bx - qx, by - qy) > 42 for qx, qy in used):
                break
            by += sg * 32
        d.line([(bx, by), (ix0 + u, yi + v)], fill=ACCENT, width=3)
        d.ellipse([ix0 + u - 5, yi + v - 5, ix0 + u + 5, yi + v + 5], fill=ACCENT, outline=(255, 255, 255), width=2)
        badge(d, (bx, by), n, fNum)
        used.append((bx, by))
    colw = (W - 100) // ncol
    for n, (key, txt, _) in enumerate(items, 1):
        c, r = (n - 1) // rows_n, (n - 1) % rows_n
        x, y = 50 + c * colw, yi + IH + 30 + r * 40
        badge(d, (x + 17, y + 15), n, font(19), r=17)
        d.text((x + 42, y + 2), txt, font=fLab, fill=INK)
    d.multiline_text((50, H - 112), "Montáž: T_klb povoliť (3 skrutky M2), vložiť 1–3 zvnútra, T_klb dotiahnuť → servo do lôžka v 9 → kryt 6 priskrutkovať k 9 →\n"
                     "kábel do komôrky, konektor 8 → ruku nasunúť na čap (hriadeľ serva zapadne do puzdra 3) → nasadiť 13.\n"
                     "Koncept: rozmery serva neoverené, posun ruky 12 mm ilustračný; skrutky (3 × M2 kryt – škrupina, 2 cez servo) nie sú zobrazené.",
                     font=fSmall, fill=MUTED, spacing=8)
    S.save(os.path.join(OUT, "v1_rozlozena_ruka.png"), optimize=True)
    print("rozlozena", S.size)


# ================================================================================================ 4 range of motion
def outline_of(img, rgb, width=3):
    a = img.split()[-1]
    m = a.point(lambda v: 255 if v > 90 else 0)
    big = m.filter(ImageFilter.MaxFilter(2 * width + 1))
    edge = Image.eval(Image.merge("L", [big]), lambda v: v)
    ring = Image.composite(big, Image.new("L", m.size, 0), Image.eval(m, lambda v: 255 - v))
    o = Image.new("RGBA", img.size, rgb + (0,))
    o.putalpha(ring)
    return o


def sheet_rozsah(clear_head=None):
    cam = Cam(os.path.join(D, "rozsah_cam.json"))
    base = load("rozsah_telo")
    IW, IH = base.size
    comp = Image.new("RGBA", base.size, (0, 0, 0, 0))
    comp.alpha_composite(base)
    tint = {"m45": (120, 140, 200), "90": (120, 140, 200), "135": (120, 140, 200)}
    for n in ("m45", "90", "135"):
        g = load("rozsah_" + n)
        r, gg, b, a = g.split()
        g2 = Image.merge("RGBA", (r, gg, b, a.point(lambda v: int(v * 0.42))))
        tl = Image.new("RGBA", g.size, tint[n] + (0,)); tl.putalpha(a.point(lambda v: int(v * 0.18)))
        comp.alpha_composite(g2); comp.alpha_composite(tl)
        comp.alpha_composite(outline_of(g, (90, 110, 170), 2))
    comp.alpha_composite(load("rozsah_0"))
    ov = Image.new("RGBA", base.size, (0, 0, 0, 0)); do = ImageDraw.Draw(ov)
    A = cam.anchors
    ax = cam.px((100.0, V.SH_Y, V.ZS))
    # angle arcs about the shoulder axis (image: right = +Y = back, robot faces left)
    k = cam.k()
    rr = 64 * k / 1.0 / 3.2
    def dir_px(deg):
        # arm direction at rest = D_DOWN; swing + = forward (to -Y = image left)
        M = V.swing_matrix(deg)
        v = M[:3, :3] @ V.D_DOWN
        return (v[1], -v[2])
    def ang_of(deg):
        vx, vy = dir_px(deg)
        return math.degrees(math.atan2(vy, vx))
    R0 = 74 * k
    for deg, col in ((-45, (90, 110, 170)), (90, (90, 110, 170)), (135, (90, 110, 170)), (0, DIM)):
        vx, vy = dir_px(deg)
        p1 = (ax[0] + vx * R0 * 1.02, ax[1] + vy * R0 * 1.02)
        dashed(do, [ax, p1], col + (220,), width=2, dash=10, gap=6)
    # arc from -45 to +135 (through 0 = down)
    a0, a1 = ang_of(-45), ang_of(135)
    pts = []
    for t in np.linspace(0, 1, 120):
        deg = -45 + 180 * t
        vx, vy = dir_px(deg)
        pts.append((ax[0] + vx * R0 * 0.9, ax[1] + vy * R0 * 0.9))
    do.line(pts, fill=DIM + (255,), width=3)
    arrow_head(do, pts[0], pts[3], DIM + (255,), 16); arrow_head(do, pts[-1], pts[-4], DIM + (255,), 16)
    do.ellipse([ax[0] - 8, ax[1] - 8, ax[0] + 8, ax[1] + 8], fill=(30, 30, 30, 255), outline=(255, 255, 255, 255), width=2)
    comp.alpha_composite(ov)
    colw = 520
    W = IW + 2 * colw
    title = "NOVA mini · ruky – návrh v1: rozsah pohybu ruky"
    intro = ("Pohľad zľava (zo strany +X), robot pozerá doľava. Ľavá ruka je plne v 0° (dole), priesvitne v −45°, +90° a +135°.\n"
             "Ruka sa otáča okolo osi ramena (čierny bod). Hlava je v strednej polohe (otočenie 0°, zdvih 0).")
    top = 34 + 76 + 2 * 37 + 30
    H = top + IH + 165
    S = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(S)
    header(d, title, intro)
    ix0, yi = colw, top
    S.paste(comp, (ix0, yi), comp)
    def lab_at(deg, txt, side):
        p = A.get(f"tip_{deg}")
        u, v = p
        return [v, u, txt]
    L = [lab_at(90, "+90° – ruka vpred", "L"), lab_at(135, "+135° – najvyššie (vpred hore)", "L")]
    R = [lab_at(-45, "−45° – dozadu", "R"), lab_at(0, "0° – ruka dole (pokoj)", "R")]
    hl = A.get("head_low")
    if clear_head:
        (pb, pa), (kb, ka) = clear_head
        ch = (f"hlava ruke nezavadzia:\nbiela ruka min. {math.floor(pb):d} mm (pri {pa:+d}°),\nkryt kĺbu min. {math.floor(kb):d} mm (v každej polohe)").replace("-", "−")
    else:
        ch = "hlava ruke nezavadzia (min. 9 mm)"
    L.append([hl[1], hl[0], ch])
    axl = [ax[1], ax[0], "os ramena (y 3, z −17)"]
    R.append(axl)
    place(d, L, "L", 0, colw, yi, IH, ix0, fLab, LH=31)
    place(d, R, "R", colw + IW, colw, yi, IH, ix0, fLab, LH=31)
    d.text((ix0 + 20, yi + IH - 10), "rozsah −45° … +135° (spolu 180°)", font=fDim, fill=DIM)
    d.multiline_text((44, yi + IH + 40), "Koncept. Vôle ruky posunutej o 12 mm sú prepočítané pre celý rozsah po 5° (hlava v strednej polohe): k trupu biela ruka min. 13 mm (pri +135°),\n"
                     "kryt kĺbu je od bočného krytu trupu 1,8 mm (stála medzera, kryt je okolo osi okrúhly).\n"
                     "Pri schválenej polohe ruky bola najmenšia vôľa k hlave 9,3 mm cez všetky polohy hlavy (otočenie ±85°, zdvih, náklon); po posune je väčšia.",
                     font=fSmall, fill=MUTED, spacing=8)
    S.save(os.path.join(OUT, "v1_rozsah_pohybu.png"), optimize=True)
    print("rozsah", S.size)


# ================================================================================================ 5 hero
def sheet_hero():
    im = load("hero")
    cam = Cam(os.path.join(D, "hero_cam.json"))
    IW, IH = im.size
    W = IW + 80
    title = "NOVA mini · ruky – návrh v1"
    intro = "Pravá ruka v pokoji, ľavá zdvihnutá o 90°, hlava otočená o 20° k nej.\nBiele ruky majú schválený tvar, sú o 12 mm ďalej od trupu; čierny kryt kĺbu skrýva servo."
    top = 34 + 76 + 2 * 37 + 20
    H = top + IH + 70
    S = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(S)
    header(d, title, intro)
    ix0, yi = 40, top
    im = feather(im, 90)
    S.paste(im, (ix0, yi), im)
    A = dict(cam.anchors)
    def pxv(p):
        q = cam.Mwc[:3, :3] @ np.asarray(p, float) + cam.Mwc[:3, 3]
        f = cam.d["lens"] / 24.0 * cam.H
        return (cam.W / 2 + f * q[0] / -q[2], cam.H / 2 - f * q[1] / -q[2])
    A["kryt_L"] = pxv((52.5, 3.0, -1.6))
    if "kryt_L" in A:
        u, v = A["kryt_L"]
        note(d, (ix0 + IW - 360, yi + 90), "kryt kĺbu (čierny),\notáča sa s rukou", (ix0 + u, yi + v), fSmall)
    if "kryt_P" in A:
        u, v = A["kryt_P"]
        note(d, (ix0 + 30, yi + IH * 0.44), "dlhší čierny kĺb\n(~16 mm namiesto ~4)", (ix0 + u, yi + v), fSmall)
    d.text((40, H - 50), "Koncept – podstavec je zatiaľ len tvar. Posun ruky 12 mm ilustračný (11–14 mm podľa zmeraného serva).", font=fSmall, fill=MUTED)
    S.save(os.path.join(OUT, "v1_hero.png"), optimize=True)
    print("hero", S.size)


if not ONLY or "spredu" in ONLY:
    sheet_spredu()
if not ONLY or "rez" in ONLY:
    sheet_rez()
if not ONLY or "rozlozena" in ONLY:
    sheet_rozlozena()
if not ONLY or "rozsah" in ONLY:
    ch = None
    p = os.path.join(HERE, "chk_head.json")
    if os.path.exists(p):
        r = json.load(open(p))
        bp = min(r["pebble"], key=lambda o: o[1]); bk = min(r["kryt"], key=lambda o: o[1])
        ch = ((bp[1], int(bp[0])), (bk[1], int(bk[0])))
    sheet_rozsah(ch)
if not ONLY or "hero" in ONLY:
    sheet_hero()
