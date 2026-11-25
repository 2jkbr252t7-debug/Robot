"""NOVA mini - arm drive v2: comparison sheet of the concepts K1 / K2 / K3 (+ the direct drive the user asked about).
Small schematic sections drawn to scale from the real numbers (torso surface of T4, pan/lift sweep PAN_ENV2, concept data).
Usage: /opt/venv/cad/bin/python v2_koncepty.py <out_png>"""
import sys, os, math
import numpy as np
from PIL import Image, ImageDraw
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R1/img_v1/work")
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T4")
import g2 as G
import t4_common as C
from sheetlib import font, dashed, arrow_head, BG, INK, MUTED

V = G.V
OUTP = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "sheets", "porovnanie_konceptov.png")
SS = 2                                     # supersampling
fT, fSub, fH, fTx, fSm, fLab, fBig = font(50), font(26, "Regular"), font(30), font(22, "Regular"), font(19, "Regular"), font(19, "Medium"), font(34)
RED = (205, 45, 40); GREEN = (30, 150, 80); ORANGE = (235, 120, 20)
WALL = (186, 188, 194); INSIDE = (252, 252, 250); ZONE = (255, 222, 186); STAT = (150, 152, 160)
VIOLET = (128, 92, 196); GOLD = (214, 160, 40); STEEL = (120, 124, 132); NAVY = (40, 62, 110); SLATE = (70, 86, 112)
ARMC = (236, 236, 232)


class Panel:
    """world (u, v) -> pixel, equal scale, v up; drawn on a supersampled RGBA layer"""
    def __init__(self, u0, u1, v0, v1, wpx):
        self.u0, self.u1, self.v0, self.v1 = u0, u1, v0, v1
        self.s = wpx / (u1 - u0)
        self.W = int(wpx); self.H = int((v1 - v0) * self.s)
        self.im = Image.new("RGBA", (self.W * SS, self.H * SS), (255, 255, 255, 0))
        self.d = ImageDraw.Draw(self.im)

    def p(self, u, v):
        return ((u - self.u0) * self.s * SS, (self.v1 - v) * self.s * SS)

    def poly(self, pts, fill=None, outline=None, width=2):
        P = [self.p(u, v) for u, v in pts]
        self.d.polygon(P, fill=fill)
        if outline:
            self.d.line(P + [P[0]], fill=outline, width=width * SS, joint="curve")

    def rect(self, u0, u1, v0, v1, fill=None, outline=None, width=2):
        self.poly([(u0, v0), (u1, v0), (u1, v1), (u0, v1)], fill, outline, width)

    def circle(self, u, v, r, fill=None, outline=None, width=2):
        a, b = self.p(u - r, v + r), self.p(u + r, v - r)
        self.d.ellipse([a, b], fill=fill, outline=outline, width=width * SS)

    def line(self, pts, fill, width=2):
        self.d.line([self.p(u, v) for u, v in pts], fill=fill, width=width * SS)

    def dashed(self, pts, fill, width=2, dash=10, gap=6):
        dashed(self.d, [self.p(u, v) for u, v in pts], fill, width * SS, dash * SS, gap * SS)

    def text(self, u, v, t, fnt, fill=INK, anchor="la"):
        f2 = font(fnt.size * SS, "Medium")
        self.d.multiline_text(self.p(u, v), t, font=f2, fill=fill, anchor=anchor, spacing=4 * SS)

    def hatch(self, u0, u1, v0, v1, col, step=1.2, width=1):
        pts = []
        L = (u1 - u0) + (v1 - v0)
        t = 0.0
        while t < L:
            a = (u0 + t, v0) if t <= u1 - u0 else (u1, v0 + t - (u1 - u0))
            b = (u0, v0 + t) if t <= v1 - v0 else (u0 + t - (v1 - v0), v1)
            pts.append((a, b)); t += step
        for a, b in pts:
            self.line([a, b], col, width)
        self.rect(u0, u1, v0, v1, None, col, 2)

    def done(self):
        return self.im.resize((self.W, self.H), Image.LANCZOS)


# ------------------------------------------------------------------------------------------------ common geometry
ZS = np.linspace(C.TOP, C.Z_BOT, 240)


def torso_front(Pn, y=G.YA):
    out = [(0.0, C.TOP)] + [(C.x_surface(y, z), z) for z in ZS] + [(0.0, C.Z_BOT)]
    inn = [(0.0, C.TOP - 2.2)] + [(C.x_surface(y, z) - 2.2, z) for z in ZS if C.TOP - 2.2 >= z >= C.Z_BOT + 2.2] + [(0.0, C.Z_BOT + 2.2)]
    Pn.poly(out, WALL)
    Pn.poly(inn, INSIDE)


def zone_front(Pn):
    pts = [(0.0, -47.2)]
    for z0, z1, r in G.PAN_ENV2:
        x = G.sweep_x(r)
        pts += [(x, z0), (x, min(z1, C.TOP - 2.2))]
    pts += [(0.0, C.TOP - 2.2)]
    Pn.poly(pts, ZONE)
    Pn.line(pts[1:-1], ORANGE, 2)


def arm_front(Pn, dx, y=G.YA, fill=ARMC, outline=(120, 120, 126), dash=False):
    L, R = [], []
    for z in np.linspace(-75, 3, 300):
        a, b = V.skins(y, float(z), 0.0, dx)
        if a is None:
            continue
        L.append((a, z)); R.append((b, z))
    poly = R + L[::-1]
    if dash:
        Pn.dashed(poly + [poly[0]], outline, 2, 6, 5)
    else:
        Pn.poly(poly, fill, outline, 2)


def plug_front(Pn):
    """black plug cartridge section at y = 3 (schematic)"""
    face = lambda z: C.x_surface(G.YA, z) - 1.0
    up = [(38.6, -6.0), (40.6, -6.0), (40.6, -3.5)] + [(face(z), z) for z in np.linspace(-3.5, -10.5, 12)] + \
         [(52.5, -10.5), (52.5, -12.0), (57.5, -12.0), (57.5, -22.0), (52.5, -22.0), (52.5, -23.5)] + \
         [(face(z), z) for z in np.linspace(-23.5, -30.5, 10)] + [(44.0, -30.5), (44.0, -23.8), (38.6, -23.8)]
    Pn.poly(up, NAVY)
    Pn.rect(38.4, 44.6, G.ZA - 6.8, G.ZA + 6.8, (60, 70, 90))        # gear cavity (dark)


def wrap(text, fnt, w):
    d = ImageDraw.Draw(Image.new("RGB", (4, 4)))
    out = []
    for para in text.split("\n"):
        cur = ""
        for word in para.split(" "):
            t = (cur + " " + word).strip()
            if d.textlength(t, font=fnt) <= w:
                cur = t
            else:
                out.append(cur); cur = word
        out.append(cur)
    return out


# ------------------------------------------------------------------------------------------------ panels
PW = 560


def panel_k1():
    """side view from +X (plane x = 41): corner servo + 3-gear train"""
    Pn = Panel(-40, 40, -88, 8, PW)
    xs = 41.0
    L, R = [], []
    for z in ZS:
        a, b, n = C.prof(C.TOP - z)
        if a <= xs:
            continue
        yv = b * (1 - (xs / a) ** n) ** (1 / n)
        L.append((-yv, z)); R.append((yv, z))
    poly = R + L[::-1]
    Pn.poly(poly, WALL)
    L2, R2 = [], []
    for z in ZS:
        a, b, n = C.prof(C.TOP - z)
        if a <= xs + 2.2:
            continue
        yv = (b - 2.2) * (1 - (xs / (a - 2.2)) ** n) ** (1 / n) if a - 2.2 > xs else 0
        L2.append((-yv, z)); R2.append((yv, z))
    Pn.poly(R2 + L2[::-1], INSIDE)
    # servo (closest corner pose of k1_opt: shaft (y -21.16, z -58.23), phi 279.1 deg)
    yc, zc, ph = -21.16, -58.23, math.radians(279.1)
    ux, uy = math.cos(ph), math.sin(ph); vx, vy = -uy, ux
    corners = []
    for a, b in ((-5.9, -6.05), (17.3, -6.05), (17.3, 6.05), (-5.9, 6.05)):
        corners.append((yc + a * ux + b * vx, zc + a * uy + b * vy))
    Pn.poly(corners, (VIOLET[0], VIOLET[1], VIOLET[2], 120), RED, 3)
    # gear train: pinion r 4 at the servo shaft, idler, gear r 10.6 on the arm axis
    ya, za = G.YA, G.ZA
    D = math.hypot(ya - yc, za - zc)
    rg, rp = 10.6, 4.0
    ri = (D - rg - rp) / 2
    t = (rp + ri) / D
    yi, zi = yc + (ya - yc) * t + 2.0, zc + (za - zc) * t
    for (u, v, r) in ((yc, zc, rp), (yi, zi, ri), (ya, za, rg)):
        Pn.circle(u, v, r, (GOLD[0], GOLD[1], GOLD[2], 90), GOLD, 3)
        Pn.circle(u, v, 0.8, INK)
    Pn.text(ya + 2, za + 12.5, "os ruky", fLab, INK)
    Pn.text(yi - 7.0, zi + 7.0, f"medzikoleso Ø {sk(2 * ri, 0)}", fLab, (120, 80, 0))
    Pn.text(-12.0, -76.5, "servo (hriadeľ ‖ osi ruky):\nnezmestí sa, chýba 2,1 mm", fLab, RED)
    Pn.line([(yc, zc), (ya, za)], (120, 120, 126), 1)
    Pn.text(-39, -85.0, "pohľad zboku, rez x = 41", fSm, MUTED)
    return Pn.done()


def sk(v, nd=1):
    return f"{v:.{nd}f}".replace(".", ",")


def panel_k2():
    """front view: servo lying along X low in the torso, belt up to the arm"""
    Pn = Panel(0, 82, -88, 8, PW)
    torso_front(Pn, -2.0)
    zone_front(Pn)
    # J1 servo + its connector zone (static)
    Pn.rect(0, 15.7, -88.0, -48.3, STAT)
    Pn.text(1.0, -50.5, "servo J1", fLab, (255, 255, 255))
    Pn.rect(15.7, 18.3, -88.0, -60.0, (175, 177, 184))
    Pn.rect(15.7, 27.0, -66.3, -48.3, (205, 207, 212))
    Pn.text(16.2, -48.8, "konektory J1", fSm, (90, 90, 96))
    # servo case + collisions
    Pn.rect(16.5, 38.0, -81.4, -58.2, (VIOLET[0], VIOLET[1], VIOLET[2], 130), VIOLET, 2)
    Pn.hatch(16.5, 18.3, -81.4, -60.0, RED, 1.3, 1)
    Pn.hatch(16.5, 27.0, -66.3, -58.2, RED, 1.3, 1)
    # belt (plane x 38.3..42.9) up to the arm axis
    Pn.rect(38.6, 41.6, -80.5, -12.0, (40, 40, 44))
    Pn.rect(38.3, 42.9, -80.45, -70.45, (GOLD[0], GOLD[1], GOLD[2], 200), GOLD, 1)
    Pn.rect(38.3, 42.9, -22.0, -12.0, (GOLD[0], GOLD[1], GOLD[2], 200), GOLD, 1)
    arm_front(Pn, 0.0, -2.0)
    Pn.text(18.0, -84.5, "telo serva by vošlo do J1", fLab, RED)
    Pn.text(44.0, -48.0, "remeň", fLab, INK)
    Pn.text(58.0, 6.8, "pohľad spredu", fSm, MUTED)
    return Pn.done()


def panel_direct():
    """front view section y = 3: servo directly on the arm axis"""
    Pn = Panel(0, 90, -88, 8, PW)
    torso_front(Pn)
    zone_front(Pn)
    arm_front(Pn, 0.0, dash=True, outline=(140, 140, 150))
    arm_front(Pn, 8.1)
    x0 = G.sweep_x(33.4) + 1.0
    Pn.rect(x0, x0 + 21.5, G.ZA - 17.3, G.ZA + 5.9, (VIOLET[0], VIOLET[1], VIOLET[2], 150), VIOLET, 2)
    Pn.rect(x0 + 21.5, x0 + 25.25, G.ZA - 2.0, G.ZA + 2.0, GOLD)
    xs = C.X_SH
    Pn.line([(xs, G.ZA - 4), (xs, G.ZA + 13)], RED, 2)
    Pn.line([(x0 + 21.5, G.ZA + 6.5), (x0 + 21.5, G.ZA + 13)], RED, 2)
    a, b = Pn.p(xs, G.ZA + 11), Pn.p(x0 + 21.5, G.ZA + 11)
    Pn.d.line([a, b], fill=RED, width=3 * SS); arrow_head(Pn.d, a, b, RED, 12 * SS); arrow_head(Pn.d, b, a, RED, 12 * SS)
    Pn.text(47.0, 6.8, "servo trčí 9,1 mm z trupu", fLab, RED)
    Pn.text(x0 + 1.0, G.ZA - 9.0, "servo", fLab, (255, 255, 255))
    Pn.text(60.0, -76.0, "ruka o 8–12 mm\nďalej od trupu", fLab, INK)
    Pn.text(1.0, -83.6, "pohľad spredu, rez osou ruky", fSm, MUTED)
    return Pn.done()


def panel_k3():
    """front view section y = 3: the chosen design"""
    Pn = Panel(0, 82, -88, 8, PW)
    torso_front(Pn)
    zone_front(Pn)
    arm_front(Pn, G.DX)
    # column (schematic): boss + legs + pad
    Pn.rect(34.4, 38.4, -29.8, -4.2, SLATE)
    Pn.rect(34.4, 41.5, -78.0, -33.0, (110, 124, 146))
    Pn.rect(32.65, 44.0, -69.0, -66.8, SLATE)
    Pn.rect(30.5, 32.65, -70.5, -48.8, SLATE)
    plug_front(Pn)
    # servo + shaft + bevel pair + arm shaft
    s = G.SERVO
    Pn.rect(s["x"][0], s["x"][1], s["z"][0], s["z"][1], VIOLET)
    Pn.rect(35.0, 43.0, -44.0, -37.0, GOLD)
    Pn.rect(37.5, 40.5, -41.0, -20.8, STEEL)
    Pn.poly([(34.6, -23.35), (43.4, -23.35), (41.6, -20.8), (36.4, -20.8)], GOLD)
    Pn.poly([(41.4, -23.3), (44.0, -23.3), (44.0, -10.7), (41.4, -13.9), (41.4, -20.1)], GOLD)
    Pn.rect(41.4, 60.5, G.ZA - 2.0, G.ZA + 2.0, STEEL)
    Pn.text(33.5, -57.0, "servo", fLab, (255, 255, 255))
    Pn.text(46.5, -40.0, "jeden kužeľový\npár 16/24", fLab, INK)
    a = Pn.p(46.4, -36.0); b = Pn.p(42.2, -24.0)
    Pn.d.line([a, b], fill=INK, width=2 * SS)
    Pn.text(57.0, -76.0, "ruka o 1 mm\nbližšie", fLab, GREEN)
    Pn.text(1.0, -83.6, "pohľad spredu, rez osou ruky", fSm, MUTED)
    return Pn.done()


CARDS = [
    dict(key="K1", title="K1 – servo v rohu trupu\n+ čelné ozubené kolesá", ok=False, score="1,5 / 10", draw=panel_k1,
         verdict="NEDÁ SA",
         text=("Pre čelné kolesá musí hriadeľ serva ležať rovnobežne s osou ruky. Také servo SCS0009 sa nezmestí nikde v trupe – "
               "ani keď z trupu odstránim celý stĺp, kĺb, zosilňovač a vnútro bočného krytu: chýba 1,6 mm, v prednom rohu 2,1 mm. "
               "Hriadeľ by bol 46–58 mm od osi ruky, takže by bolo treba medzikoleso Ø 30–40 mm alebo 4 kolesá – "
               "presne ten hlučný mechanizmus, ktorý nechceš.")),
    dict(key="K2", title="K2 – servo dole v trupe\n+ remeň alebo lanko", ok=False, score="2 / 10", draw=panel_k2,
         verdict="NEDÁ SA",
         text=("Remeň aj lanko spájajú len rovnobežné hriadele, takže servo musí ležať pozdĺž osi ruky. Pri ramene je medzi otáčaním "
               "krku a stenou len 10,1 mm, preto by telo serva siahalo až k servu J1. Vľavo je miesto najviac pre 19,5 mm telo "
               "(treba 21,5–25,25 mm), vpravo len pre 6,6 mm. Remeň by bol tichý, ale servo sa nezmestí.")),
    dict(key="D", title="Otázka: servo priamo na osi\nruky (bez kolies)", ok=False, score="–", draw=panel_direct,
         verdict="NEDÁ SA (bez odsunutia ruky)",
         text=("Na osi ruky je od otáčajúceho sa krku (+1 mm vôľa) po povrch trupu len 12,5 mm. Servo SCS0009 potrebuje pozdĺž "
               "hriadeľa asi 25 mm (telo 21,5 + výstup 3,75), takže by trčalo 9,1 mm z trupu a ruka by sa musela odsunúť o 8–12 mm. "
               "Nepomôže ani úplné odstránenie modulu zdvihu – ostane otáčajúca sa šachta krku a voľných by bolo len 19,3 mm.")),
    dict(key="K3", title="K3 – servo stojí pod ramenom\n+ jeden kužeľový pár", ok=True, score="8 / 10", draw=panel_k3,
         verdict="VYBRANÉ",
         text=("Jediný koncept, ktorý sa dá postaviť. Servo stojí v novom stĺpe (výstup hore), tenký hriadeľ Ø3 ide k jedinému "
               "mazanému mosadznému kužeľovému páru 16/24 v čiernej zátke – pomalý a tichý. Ruka je pasívna škrupina na ložisku, "
               "kábel serva ostáva v trupe. Hlava, krk, otáčanie hlavy, zdvih aj vonkajšok trupu bez zmeny. "
               "Medzera 3,7 mm (ruka o 1 mm bližšie), v celom rozsahu aspoň 1,0 mm. Pred zatlačením rukou chráni trecia spojka.")),
]


def main():
    imgs = [c["draw"]() for c in CARDS]
    gap = 34
    cw = PW + 40
    W = 4 * cw + 5 * gap
    ih = max(i.height for i in imgs)
    top = 34 + 76 + 2 * 37 + 40
    text_lines = [wrap(c["text"], fTx, cw - 40) for c in CARDS]
    th = max(len(t) for t in text_lines) * 31
    card_h = 20 + 2 * 38 + 16 + ih + 24 + 50 + 16 + th + 70
    H = top + card_h + 150
    S = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(S)
    d.text((44, 34), "NOVA mini · ruky v2: porovnanie konceptov (servá v trupe)", font=fT, fill=INK)
    d.multiline_text((44, 110), "Všetko merané na skutočnom trupe T4 (vôľa 1,0 mm k otáčaniu a zdvihu krku, 0,3 mm k pevným dielom). "
                     "Nákresy sú v mierke, zjednodušené.\nOranžová plocha = kam siaha krk a servo zdvihu pri otáčaní hlavy · sivá = stena trupu a pevné diely · "
                     "fialová = servo ruky · zlatá = kolesá / remenice.", font=fSub, fill=MUTED, spacing=10)
    for i, (c, im, tl) in enumerate(zip(CARDS, imgs, text_lines)):
        x0 = gap + i * (cw + gap); y0 = top
        col = GREEN if c["ok"] else (200, 200, 196)
        d.rounded_rectangle([x0, y0, x0 + cw, y0 + card_h], 18, fill=(255, 255, 255), outline=col, width=6 if c["ok"] else 2)
        d.multiline_text((x0 + 20, y0 + 20), c["title"], font=fH, fill=INK, spacing=8)
        yi = y0 + 20 + 2 * 38 + 16
        S.paste(im, (x0 + 20 + (PW - im.width) // 2, yi), im)
        yb = yi + ih + 24
        vc = GREEN if c["ok"] else RED
        mark = "✓ " if c["ok"] else "✗ "
        tw = d.textlength(mark + c["verdict"], font=fBig)
        d.rounded_rectangle([x0 + 20, yb, x0 + 20 + tw + 28, yb + 50], 10, fill=vc)
        d.text((x0 + 34, yb + 6), mark + c["verdict"], font=fBig, fill=(255, 255, 255))
        if c["score"] != "–":
            st = "hodnotenie " + c["score"]
            d.text((x0 + cw - 20 - d.textlength(st, font=fTx), yb + 14), st, font=fTx, fill=MUTED)
        ty = yb + 66
        for ln in tl:
            d.text((x0 + 20, ty), ln, font=fTx, fill=INK); ty += 31
    d.multiline_text((44, top + card_h + 30),
                     "Prečo K3: je to jediné riešenie, kde sa servo zmestí do trupu a ruka sa môže dokonca priblížiť k trupu. Má len jeden ozubený pár "
                     "(žiadna sada kolies), servo má spätnú väzbu polohy aj zaťaženia,\na pri náraze prekĺzne trecia spojka. Pravé rameno je zrkadlové. "
                     "Znova sa tlačí: dno trupu T_spodok (nové stĺpy), oba bočné kryty (malý vnútorný zárez), paluba a nové čierne zátky namiesto T_klb.",
                     font=fTx, fill=INK, spacing=10)
    S.save(OUTP, optimize=True)
    print("koncepty", S.size)


main()
