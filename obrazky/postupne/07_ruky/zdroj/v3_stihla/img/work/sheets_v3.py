"""NOVA mini - R3 slim-arm comparison sheets (Slovak labels).  CAD venv (Pillow, numpy).
Usage: /opt/venv/cad/bin/python sheets_v3.py <render_dir> <out_dir> [spredu 3d ruka rez]
Reads the renders of scene_v3.py + nums_v3.json (own numbers, checked against R3/tvar/chk_variants.json and the
R3/mech fit JSONs).  Writes v3_porovnanie_spredu.png, v3_porovnanie_3d.png, v3_ruka_zhora_zboku.png, v3_prierez_klbom.png"""
import sys, os, json, math
from decimal import Decimal, ROUND_HALF_UP
import numpy as np
from PIL import Image, ImageDraw
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R3/tvar")
import variants as VA
from sheetlib import font, arrow_head, BG, INK, MUTED, ACCENT, DIM

D, OUT = sys.argv[1], sys.argv[2]
ONLY = sys.argv[3:]
os.makedirs(OUT, exist_ok=True)
N = json.load(open(os.path.join(HERE, "nums_v3.json")))
VIDS = list(VA.VIDS)
SW = 1400                                     # sheet width (px)
M = 36                                        # outer margin
GREEN, ORANGE, RED = (28, 140, 74), (214, 112, 14), (196, 48, 36)
CARD, EDGE = (250, 250, 248), (222, 221, 216)
fT, fS, fH, fL, fN, fB, fSm, fD, fBadge = (font(42), font(20, "Regular"), font(23, "SemiBold"), font(18, "Regular"),
                                          font(17, "Regular"), font(17, "SemiBold"), font(15, "Regular"), font(17, "SemiBold"),
                                          font(15, "Bold"))
NAME = {"0": "0 – súčasná ruka (T3)", "A": "A – mierne štíhlejšia", "B": "B – štíhla", "C": "C – najštíhlejšia"}
JOINT = {  # one short line from the verification + colour
    "0": ("kĺb bez zmeny (B1+)", GREEN, "6700 + podložka M10 + magnety 5×2"),
    "A": ("kĺb treba sploštiť – zmestí sa", GREEN, "MR128 + podložka M12, rezerva 0,76 mm"),
    "B": ("kĺb treba sploštiť – len tesne", ORANGE, "MR128 + podložka M12, rezerva 0,085 mm"),
    "C": ("nezmestí sa žiadny navrhnutý kĺb", RED, "chýba ~3 mm; nepomôže ani spojka v trupe"),
}


def sk(v, nd=1):
    q = Decimal(str(v)).quantize(Decimal(1).scaleb(-nd), rounding=ROUND_HALF_UP)
    s = f"{q:.{nd}f}".replace(".", ",").replace("-", "−")
    return s


class Cam:
    def __init__(self, path):
        d = json.load(open(path))
        self.d = d
        self.W, self.H = d["res"]
        self.Mwc = np.linalg.inv(np.array(d["matrix"]))
        self.extra = d.get("extra", {})

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

    def k(self):
        return self.W / self.d["ortho_scale"]


class Panel:
    """a cropped + scaled render placed on the sheet; P(world) -> sheet pixel"""
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
            S.paste(b.convert("RGB"), (int(self.at[0]), int(self.at[1])))
        else:
            S.paste(self.im, (int(self.at[0]), int(self.at[1])), self.im)

    @property
    def w(self):
        return self.im.width

    @property
    def h(self):
        return self.im.height


def load(name):
    return Image.open(os.path.join(D, name + ".png")).convert("RGBA")


def tw(d, t, f):
    return d.textlength(t, font=f)


def header(d, title, intro, y=28):
    d.text((M, y), title, font=fT, fill=INK)
    d.multiline_text((M, y + 62), intro, font=fS, fill=MUTED, spacing=8)
    return y + 62 + (intro.count("\n") + 1) * 28 + 18


def card(d, x0, y0, x1, y1):
    d.rounded_rectangle((x0, y0, x1, y1), 12, fill=CARD, outline=EDGE, width=2)


def dimh(d, xa, xb, y, text, f=fD, fill=DIM, above=True, ext=None, inside=False, bg=(255, 255, 255)):
    for ex, ey in (ext or []):
        d.line([(ex, ey), (ex, y + (6 if y > ey else -6))], fill=fill, width=1)
    if inside:
        d.line([(xa, y), (xb, y)], fill=fill, width=2)
        arrow_head(d, (xa, y), (xb, y), fill, 9); arrow_head(d, (xb, y), (xa, y), fill, 9)
    else:
        d.line([(xa - 16, y), (xb + 16, y)], fill=fill, width=2)
        arrow_head(d, (xa, y), (xa - 16, y), fill, 9); arrow_head(d, (xb, y), (xb + 16, y), fill, 9)
    w = tw(d, text, f)
    tx = (xa + xb) / 2 - w / 2
    ty = y - f.size - 7 if above else y + 5
    if bg:
        d.rounded_rectangle((tx - 4, ty - 1, tx + w + 4, ty + f.size + 5), 4, fill=bg)
    d.text((tx, ty), text, font=f, fill=fill)


def dimv(d, x, ya, yb, text, f=fD, fill=DIM, left=True, ext=None, bg=(255, 255, 255)):
    for ex, ey in (ext or []):
        d.line([(ex, ey), (x + (6 if x > ex else -6), ey)], fill=fill, width=1)
    d.line([(x, ya), (x, yb)], fill=fill, width=2)
    arrow_head(d, (x, ya), (x, yb), fill, 9); arrow_head(d, (x, yb), (x, ya), fill, 9)
    w = tw(d, text, f)
    tx = x - w - 8 if left else x + 8
    ty = (ya + yb) / 2 - f.size / 2 - 2
    if bg:
        d.rounded_rectangle((tx - 4, ty - 1, tx + w + 4, ty + f.size + 5), 4, fill=bg)
    d.text((tx, ty), text, font=f, fill=fill)


def rows_table(d, x, y, w, rows, lh=25):
    for a, b, sty in rows:
        col = MUTED if sty == "sub" else INK
        d.text((x, y), a, font=fN, fill=col)
        d.text((x + w, y), b, font=fB if sty != "sub" else fN, fill=col, anchor="ra")
        y += lh
    return y


def badge(d, xy, n, fill=ACCENT, r=11):
    x, y = xy
    d.ellipse((x - r, y - r, x + r, y + r), fill=fill, outline=(255, 255, 255), width=2)
    t = str(n)
    d.text((x, y + 1), t, font=fBadge, fill=(255, 255, 255), anchor="mm")


def footer(d, y, text):
    d.multiline_text((M, y), text, font=fSm, fill=MUTED, spacing=6)
    return y + (text.count("\n") + 1) * 21


def finish(S, ybot, name):
    S = S.crop((0, 0, S.width, int(ybot)))
    S.save(os.path.join(OUT, name), optimize=True)
    print(name, S.size)


# ================================================================================================ 1 front comparison
def sheet_spredu():
    cw = (SW - 2 * M - 3 * 14) // 4
    title = "NOVA mini · štíhlejšia ruka: porovnanie spredu"
    intro = ("Pravouhlý pohľad spredu, všetky štyri obrázky v rovnakej mierke. Ruka chudne zvonka: vnútorná plocha pri trupe, miesto\n"
             "uchytenia a medzera k trupu ostávajú, tenší je hlavne vonkajší kryt (od švu von). Ruka je aj o 5 / 10 / 15 % užšia spredu dozadu.")
    S = Image.new("RGB", (SW, 2400), BG)
    d = ImageDraw.Draw(S)
    y0 = header(d, title, intro) + 6
    cam = Cam(os.path.join(D, "front_cam.json"))
    zc = Cam(os.path.join(D, "armfront_cam.json"))
    # robot crop (same for all)
    k = cam.k()
    cx = cam.px((0, 0, 0))[0]
    xl, xr = cx - 84 * k, cx + 84 * k
    yt, yb = cam.px((0, 0, 93.0))[1], cam.px((0, 0, -118.5))[1]
    box = tuple(int(round(v)) for v in (xl, yt, xr, yb))
    sc = (cw - 20) / (box[2] - box[0])
    zbox = (0, 0, zc.W, int(zc.H * 0.90))
    zsc = (cw - 20) / zc.W
    ytitle = y0 + 12
    yimg = ytitle + 64
    hrob = (box[3] - box[1]) * sc
    ydim = yimg + hrob + 30
    yz = ydim + 44
    hz = zbox[3] * zsc
    ytab = yz + hz + 16
    rows_h = 8 * 25
    yj = ytab + rows_h + 8
    ycard1 = yj + 58
    for i, v in enumerate(VIDS):
        n = N[v]
        x0 = M + i * (cw + 14)
        card(d, x0, y0, x0 + cw, ycard1)
        d.text((x0 + 14, ytitle), NAME[v], font=fH, fill=INK if v == "0" else ACCENT)
        d.text((x0 + 14, ytitle + 32), f"hrúbka ruky {sk(n['thickness_max'])} mm", font=fL, fill=MUTED)
        pr = Panel(load(f"front_{v}"), cam, box, sc, (x0 + 10, yimg))
        pr.paste(S)
        # zoom frame on the robot
        zx0, zz0 = zc.d["matrix"][0][3] - zc.d["ortho_scale"] / 2, zc.d["matrix"][2][3]
        hw_ = zc.d["ortho_scale"] / 2; hh_ = hw_ * zc.H / zc.W
        za, zb = pr.P((zc.d["matrix"][0][3] - hw_, 0, zz0 + hh_)), pr.P((zc.d["matrix"][0][3] + hw_, 0, zz0 + hh_ - 2 * hh_ * 0.90))
        d.rectangle((za[0], za[1], min(zb[0], pr.at[0] + pr.w - 2), zb[1]), outline=ACCENT, width=2)
        # overall width over the arms
        xo = n["outermost_x"]; zo = n["outermost_z"]
        pa, pb = pr.P((-xo, 0, zo)), pr.P((xo, 0, zo))
        dimh(d, pa[0], pb[0], ydim, f"{sk(n['robot_width'])} mm", above=True, ext=[(pa[0], pa[1] + 6), (pb[0], pb[1] + 6)],
             inside=True, bg=CARD)
        d.text(((pa[0] + pb[0]) / 2, ydim + 6), "šírka cez ruky", font=fSm, fill=MUTED, anchor="ma")
        # shoulder zoom with the outer cover band
        pz = Panel(load(f"armfront_{v}"), zc, zbox, zsc, (x0 + 10, yz))
        pz.paste(S, bg=(255, 255, 255))
        d.rectangle((pz.at[0], pz.at[1], pz.at[0] + pz.w, pz.at[1] + pz.h), outline=ACCENT, width=2)
        fb = n["front_band"]
        qa, qb = pz.P((fb["x_seam"], 0, fb["z"])), pz.P((fb["x_out"], 0, fb["z"]))
        yb_ = qa[1]
        d.line([(qa[0], yb_), (qb[0], yb_)], fill=DIM, width=3)
        arrow_head(d, (qa[0], yb_), (qb[0], yb_), DIM, 9); arrow_head(d, (qb[0], yb_), (qa[0], yb_), DIM, 9)
        t = f"kryt {sk(n['outer_joint'])}"
        alpha = np.asarray(pz.im.split()[-1]) > 12

        def _free(bx):   # label box (sheet px) must not cover the rendered robot (3 px margin) and stay in the panel
            x0_, y0_, x1_, y1_ = (int(bx[0] - pz.at[0]) - 3, int(bx[1] - pz.at[1]) - 3, int(bx[2] - pz.at[0]) + 3, int(bx[3] - pz.at[1]) + 3)
            if x0_ < 2 or y0_ < 2 or x1_ > pz.w - 2 or y1_ > pz.h - 2:
                return False
            return not alpha[y0_:y1_, x0_:x1_].any()
        lab = None
        for fnt_, lines_ in ((fD, [t]), (font(15, "SemiBold"), [t]), (font(15, "SemiBold"), ["kryt", sk(n['outer_joint'])])):
            wl_ = max(tw(d, ln, fnt_) for ln in lines_); hl_ = 23 if len(lines_) == 1 else 40
            for dy in (-40, -55, -70, -85, -100, 18, 34):
                tx = min(qb[0] + 10, pz.at[0] + pz.w - wl_ - 10)
                ty = yb_ + dy
                if _free((tx - 5, ty - 2, tx + wl_ + 5, ty + hl_)):
                    lab = (fnt_, lines_, wl_, hl_, tx, ty); break
            if lab:
                break
        if lab is None:
            raise SystemExit(f"no free spot for the cover label in column {v}")
        fnt_, lines_, wl_, hl_, tx, ty = lab
        d.rounded_rectangle((tx - 5, ty - 2, tx + wl_ + 5, ty + hl_), 4, fill=(255, 255, 255), outline=DIM)
        d.multiline_text((tx, ty), "\n".join(lines_), font=fnt_, fill=DIM, spacing=2)
        ya_ = ty + hl_ if ty < yb_ else ty - 2
        d.line([(tx + 10, ya_), ((qa[0] + qb[0]) / 2, yb_ + (-4 if ty < yb_ else 4))], fill=DIM, width=1)
        if i == 0:
            t0 = "detail ľavého ramena"
            d.rounded_rectangle((pz.at[0] + 4, pz.at[1] + pz.h - 28, pz.at[0] + 16 + tw(d, t0, fSm), pz.at[1] + pz.h - 5), 4,
                                fill=(255, 255, 255))
            d.text((pz.at[0] + 10, pz.at[1] + pz.h - 26), t0, font=fSm, fill=MUTED)
        rows = [("hrúbka max / pri kĺbe", f"{sk(n['thickness_max'])} / {sk(n['thick_joint'])}", ""),
                ("  vonkajší kryt pri kĺbe", sk(n["outer_joint"]), "sub"),
                ("  vnútorná časť pri kĺbe", sk(n["inner_joint"]), "sub"),
                ("šírka ruky spredu dozadu", sk(n["width_max"]), ""),
                ("šírka cez ruky", sk(n["robot_width"]), ""),
                ("medzera k trupu v pokoji", sk(n["gap_rest"]), ""),
                ("  najmenšia pri pohybe", sk(n["gap_min"]), "sub")]
        rows_table(d, x0 + 14, ytab, cw - 28, rows)
        jt, jc, jsub = JOINT[v]
        d.rounded_rectangle((x0 + 10, yj, x0 + cw - 10, yj + 48), 8, fill=jc)
        f1, f2 = font(16, "SemiBold"), font(14, "Regular")
        for sz in (15, 14, 13):     # one font size for all four boxes (the longest text decides)
            if all(tw(d, a_, f1) <= cw - 40 and tw(d, c_, f2) <= cw - 40 for a_, _, c_ in JOINT.values()):
                break
            f1, f2 = font(sz, "SemiBold"), font(sz - 1, "Regular")
        d.text((x0 + 20, yj + 5), jt, font=f1, fill=(255, 255, 255))
        d.text((x0 + 20, yj + 26), jsub, font=f2, fill=(255, 255, 255))
    yf = ycard1 + 18
    foot = ("Rozmery v mm; hrúbka = do strany (k trupu – von), šírka = spredu dozadu. Kĺb podľa nezávislej kontroly zmestenia (steny ≥ 1,2 mm, vôľa ≥ 0,3 mm):\n"
            "A – rezerva 0,76 mm; B – rezerva len 0,085 mm (posun unášača o 0,1 mm alebo bežná skrutka DIN 912 = nezmestí sa); C – chýba 1,9 až 5,5 mm pri všetkých 5 návrhoch.\n"
            "Medzera k trupu: v pokoji 3,7 mm vo všetkých variantoch, pri pohybe −45° … +135° najmenej 1,0 – 1,1 mm (nikde horšie ako dnes). Hlava v strednej polohe.\n"
            "Podstavec (zatiaľ koncept) je široký 146 mm, takže v B a C je najširším miestom robota on, nie ruky.\n"
            "Koncept na posúdenie tvaru, nie výkres. Čierny krúžok kĺbu je z modelu v2 (len vizuálne).")
    yb = footer(d, yf, foot) + 22
    finish(S, yb, "v3_porovnanie_spredu.png")


# ================================================================================================ 2 hero 2x2
def sheet_3d():
    cw = (SW - 2 * M - 16) // 2
    title = "NOVA mini · štíhlejšia ruka: pohľad zboku spredu"
    intro = ("Ľavá ruka zdvihnutá o 90°, hlava otočená o 20° k nej – rovnaká kamera aj mierka pre všetky štyri varianty.\n"
             "Zdvihnutá ruka je otočená vonkajším krytom k nám: vidno užší a menej vypuklý kryt. Samotnú hrúbku lepšie ukazuje pohľad spredu.")
    cam = Cam(os.path.join(D, "hero_cam.json"))
    im0 = load("hero_0")
    W0, H0 = im0.size
    a = np.array(im0)[:, :, 3]
    ys, xs = np.nonzero(a > 200)
    box = (max(0, int(xs.min()) - 30), max(0, int(ys.min()) - 22), min(W0, int(xs.max()) + 30), min(H0, int(ys.max()) + 16))  # keep the whole base
    sc = (cw - 20) / (box[2] - box[0])
    S = Image.new("RGB", (SW, 3000), BG)
    d = ImageDraw.Draw(S)
    y0 = header(d, title, intro) + 6
    ph = (box[3] - box[1]) * sc
    chh = 56 + ph + 50
    for i, v in enumerate(VIDS):
        n = N[v]
        r, c = divmod(i, 2)
        x0 = M + c * (cw + 16); yc = y0 + r * (chh + 16)
        card(d, x0, yc, x0 + cw, yc + chh)
        d.text((x0 + 16, yc + 12), NAME[v], font=fH, fill=INK if v == "0" else ACCENT)
        p = Panel(load(f"hero_{v}"), cam, box, sc, (x0 + 10, yc + 50))
        p.paste(S)
        t = (f"hrúbka {sk(n['thickness_max'])} mm  ·  z toho kryt {sk(n['outer_joint'])} mm  ·  "
             f"šírka {sk(n['width_max'])} mm  ·  cez ruky {sk(n['robot_width'])} mm")
        d.text((x0 + 16, yc + chh - 36), t, font=fN, fill=INK)
    # row of close-ups of the raised arm (same camera direction, framed on the arm)
    ya = y0 + 2 * chh + 2 * 16
    cw4 = (SW - 2 * M - 3 * 14) // 4
    hc = Cam(os.path.join(D, "heroarm_cam.json"))
    hb = (int(hc.W * 0.30), int(hc.H * 0.10), int(hc.W * 0.97), int(hc.H * 0.74))
    hs = (cw4 - 16) / (hb[2] - hb[0])
    hah = (hb[3] - hb[1]) * hs
    for i, v in enumerate(VIDS):
        x0 = M + i * (cw4 + 14)
        card(d, x0, ya, x0 + cw4, ya + 40 + hah + 12)
        d.text((x0 + 12, ya + 9), NAME[v].split(" – ")[0] + " – detail zdvihnutej ruky", font=fB, fill=INK if v == "0" else ACCENT)
        p = Panel(load(f"heroarm_{v}"), hc, hb, hs, (x0 + 8, ya + 40))
        p.paste(S, bg=(246, 246, 244))
    yf = ya + 40 + hah + 12 + 18
    foot = ("Rozmery v mm (hrúbka ruky max, vonkajší kryt pri kĺbe, šírka ruky spredu dozadu, šírka robota cez ruky; podstavec má 146 mm).\n"
            "Tvar trupu, hlavy a krku sa nemení. Koncept – podstavec je zatiaľ len tvar; čierny krúžok kĺbu je z modelu v2 (len vizuálne).")
    yb = footer(d, yf, foot) + 22
    finish(S, yb, "v3_porovnanie_3d.png")


# ================================================================================================ 3 single arm: front + top
def sheet_ruka():
    cw = (SW - 2 * M - 3 * 14) // 4
    title = "NOVA mini · samotná ľavá ruka: spredu a zhora"
    intro = ("Ruka vyrovnaná zvislo (bez náklonu 12°), všetky v rovnakej mierke. Vľavo je strana k trupu, vpravo vonkajší kryt.\n"
             "Čierna čiara = šev medzi vonkajším krytom a vnútornou časťou; čierna špička = tlačená čierna časť. Dĺžka ruky 72 mm vo všetkých.")
    fc, tc = Cam(os.path.join(D, "armF_cam.json")), Cam(os.path.join(D, "armT_cam.json"))
    kf = fc.k()
    fbox = tuple(int(round(v)) for v in (fc.px((-21, 0, 0))[0], fc.px((0, 0, 9.5))[1], fc.px((21, 0, 0))[0], fc.px((0, 0, -76.0))[1]))
    tbox = tuple(int(round(v)) for v in (tc.px((-21, 0, 0))[0], tc.px((0, 19.0, 0))[1], tc.px((21, 0, 0))[0], tc.px((0, -19.0, 0))[1]))
    sc = (cw - 24) / (fbox[2] - fbox[0])
    S = Image.new("RGB", (SW, 3000), BG)
    d = ImageDraw.Draw(S)
    y0 = header(d, title, intro) + 6
    yt = y0 + 12
    yf = yt + 62
    hf = (fbox[3] - fbox[1]) * sc
    ylab2 = yf + hf + 14
    ytop = ylab2 + 34
    ht = (tbox[3] - tbox[1]) * sc
    ytab = ytop + ht + 40
    yend = ytab + 4 * 25 + 14
    for i, v in enumerate(VIDS):
        n = N[v]
        x0 = M + i * (cw + 14)
        card(d, x0, y0, x0 + cw, yend)
        d.text((x0 + 14, yt), NAME[v], font=fH, fill=INK if v == "0" else ACCENT)
        pf = Panel(load(f"armF_{v}"), fc, fbox, sc, (x0 + 12, yf))
        pf.paste(S)
        if i == 0:
            d.multiline_text((x0 + 14, yf + 46), "pohľad\nspredu", font=fSm, fill=MUTED, spacing=3)
        # dims at the joint (u 0.22) and the max thickness (u of max)
        ci, co, cs = [float(a) for a in VA.faces(v, 0.22)]
        um = n["thickness_max_u"]
        mi, mo, _ = [float(a) for a in VA.faces(v, um)]
        zj, zm = -VA.L * 0.22, -VA.L * um
        a1, a2, a3 = pf.P((ci, 0, zj)), pf.P((cs, 0, zj)), pf.P((co, 0, zj))
        ytier1 = pf.P((0, 0, 3.6))[1]
        ytier2 = pf.P((0, 0, 8.4))[1]
        d.line([(a1[0], ytier1), (a3[0], ytier1)], fill=DIM, width=2)
        ytopa = pf.P((0, 0, 1.2))[1]
        for q in (a1, a2, a3):
            d.line([(q[0], ytopa), (q[0], ytier1 - 6)], fill=DIM, width=1)
        for qa, qb in ((a1, a2), (a2, a3)):
            arrow_head(d, (qa[0], ytier1), (qb[0], ytier1), DIM, 8); arrow_head(d, (qb[0], ytier1), (qa[0], ytier1), DIM, 8)
        tin, tout = sk(n["inner_joint"]), sk(n["outer_joint"])
        d.text((a2[0] - 6, ytier1 + 4), tin, font=fSm, fill=DIM, anchor="ra")
        d.text((a2[0] + 6, ytier1 + 4), tout, font=fSm, fill=DIM, anchor="la")
        b1, b3 = pf.P((mi, 0, zm)), pf.P((mo, 0, zm))
        dimh(d, b1[0], b3[0], ytier2, f"{sk(n['thickness_max'])}", above=True, inside=False, bg=CARD,
             ext=[(b1[0], ytier1 - 2), (b3[0], ytier1 - 2)])
        d.text(((b1[0] + b3[0]) / 2, ytier2 - 44), "hrúbka", font=fSm, fill=MUTED, anchor="ma")
        # labels of the halves
        pv = pf.P(((ci + cs) / 2, 0, -42.0)); po = pf.P(((cs + co) / 2, 0, -42.0))
        if i == 0:
            yl_ = pv[1] - 60
            d.multiline_text((x0 + 12, yl_), "vnútro\n(k trupu)", font=fSm, fill=INK, spacing=3)
            d.line([(x0 + 40, yl_ + 40), (pv[0], pv[1])], fill=ACCENT, width=2)
            d.ellipse((pv[0] - 4, pv[1] - 4, pv[0] + 4, pv[1] + 4), fill=ACCENT)
            tx = x0 + cw - 12 - tw(d, "vonkajší", fSm)
            d.multiline_text((tx, yl_), "vonkajší\nkryt", font=fSm, fill=INK, spacing=3)
            d.line([(tx + 20, yl_ + 40), (po[0], po[1])], fill=ACCENT, width=2)
            d.ellipse((po[0] - 4, po[1] - 4, po[0] + 4, po[1] + 4), fill=ACCENT)
        # top view
        if i == 0:
            d.text((x0 + 14, ylab2), "pohľad zhora (vpredu = dole)", font=fSm, fill=MUTED)
        pt = Panel(load(f"armT_{v}"), tc, tbox, sc, (x0 + 12, ytop))
        pt.paste(S)
        rows, top, bot = VA.pebble_rows(v, 160, 240)
        P = rows.reshape(-1, 3)
        xa, xb = float(P[:, 0].min()), float(P[:, 0].max())
        ya, yb2 = float(P[:, 1].min()), float(P[:, 1].max())
        q1, q2 = pt.P((xa, ya, 0)), pt.P((xb, ya, 0))
        ydt = q1[1] + 22
        dimh(d, q1[0], q2[0], ydt, f"{sk(n['thickness_max'])}", above=False, inside=True, bg=CARD,
             ext=[(q1[0], pt.P((xa, 0, 0))[1]), (q2[0], pt.P((xb, 0, 0))[1])])
        r1, r2 = pt.P((xa, yb2, 0)), pt.P((xa, ya, 0))
        xdt = pt.P((xa, 0, 0))[0] - 16
        dimv(d, xdt, r1[1], r2[1], f"{sk(n['width_max'])}", left=True, bg=CARD,
             ext=[(pt.P((0, yb2, 0))[0], r1[1]), (pt.P((0, ya, 0))[0], r2[1])])
        rows_t = [("hrúbka max", sk(n["thickness_max"]), ""),
                  ("  vnútro / kryt pri kĺbe", f"{sk(n['inner_joint'])} / {sk(n['outer_joint'])}", "sub"),
                  ("šírka max (spredu dozadu)", sk(n["width_max"]), ""),
                  ("šírka oproti dnešku", "100 %" if v == "0" else f"{round(100 * n['width_max'] / N['0']['width_max'])} %", "sub")]
        rows_table(d, x0 + 14, ytab, cw - 28, rows_t)
    yfo = yend + 18
    foot = ("Rozmery v mm. Hrúbka max je v hornej tretine ruky (asi 15 mm pod vrcholom), pri kĺbe (u = 0,22) je takmer rovnaká.\n"
            "Vnútro = časť od švu k trupu (nosná škrupina s nábojom kĺbu), kryt = vonkajšia časť od švu von (drží na magnetoch).\n"
            "V B a C sa šev posúva dovnútra a je mierne zakrivený; obe špičky ruky idú s ním, aby obrys nebol rovná čepeľ.")
    yb = footer(d, yfo, foot) + 22
    finish(S, yb, "v3_ruka_zhora_zboku.png")


# ================================================================================================ 4 sections
OPT = {"0": "M1", "A": "M2b", "B": "M2b", "C": "M2b"}
OPTNAME = {"M1": "kĺb B1+ bez zmeny", "M2b": "kĺb B1+ naplocho (MR128 + M12)"}
VERD = {"0": ("zmestí sa", GREEN), "A": ("zmestí sa", GREEN), "B": ("len tesne", ORANGE), "C": ("nezmestí sa", RED)}
SPOTTXT = {
    "0": ("najtenšie: stena náboja ku krytu", "{w} mm (treba ≥ {r})", "rezerva {m} mm · asi 3,5 mm nad rezom"),
    "A": ("najtenšie: podložka M12 ku vnútru", "{w} mm (treba ≥ {r})", "rezerva {m} mm · asi 1,4 mm pod rezom"),
    "B": ("najtenšie: unášač ku krytu", "{w} mm (treba ≥ {r})", "rezerva len {m} mm"),
    "C": ("unášač trčí von cez kryt", "{w} mm von (treba {r} dnu)", "chýba {c} mm"),
}
# badge anchors (world, plane y = 3, seen from the front): part number -> point per option
BADGE = {
    "M1": {1: None, 2: None, 3: (57.5, 3.0, -10.3), 4: (61.6, 3.0, -25.0), 5: (64.0, 3.0, -9.4), 6: (49.0, 3.0, -17.0),
           7: (47.5, 3.0, -11.6), 8: (45.4, 3.0, -38.0)},
    "M2b": {1: None, 2: None, 3: (56.4, 3.0, -11.6), 4: (57.2, 3.0, -27.0), 5: (61.9, 3.0, -17.0), 6: (49.0, 3.0, -17.0),
            7: (47.5, 3.0, -11.6), 8: (45.4, 3.0, -38.0)},
}
LEGEND = [(1, "vonkajší kryt ruky (biely, drží na magnetoch)"), (2, "vnútorná škrupina ruky s nábojom (biela)"),
          (3, "ložisko ruky (6700 v 0, MR128 v A–C)"), (4, "oceľová podložka = trecia plocha spojky (M10 / M12)"),
          (5, "unášač spojky s magnetmi (tlačený)"), (6, "skrutka M4 = hriadeľ ruky"),
          (7, "čierna zátka v trupe: krúžok Ø13, sedlo, doraz"), (8, "bočný kryt trupu (bez zmeny)")]


def skin_pt(v, plane, side, at):
    """a point 0.6 mm inside the arm skin in the section plane: side 'out' = max x, 'in' = min x, at = z (v) or y (h)"""
    rows, _, _ = VA.pebble_rows(v, 300, 400)
    W = VA.to_world(rows.reshape(-1, 3), v)
    if plane == "v":
        m = (np.abs(W[:, 1] - 3.0) < 0.5) & (np.abs(W[:, 2] - at) < 0.5)
        x = W[m, 0].max() - 0.7 if side == "out" else W[m, 0].min() + 0.9
        return (float(x), 3.0, at)
    m = (np.abs(W[:, 2] + 17.0) < 0.5) & (np.abs(W[:, 1] - at) < 0.5)
    x = W[m, 0].max() - 0.7 if side == "out" else W[m, 0].min() + 0.9
    return (float(x), at, -17.0)


def sheet_rez():
    cw = (SW - 2 * M - 3 * 14) // 4
    title = "NOVA mini · štíhlejšia ruka: rez kĺbom ramena"
    intro = ("Do každého variantu je vložený najlepšie sediaci navrhnutý kĺb. Hore rez zvislou rovinou cez os ramena (pohľad spredu),\n"
             "dole rez vodorovnou rovinou cez os (pohľad zhora, vpredu = dole). Ľavá ruka; trup je vľavo. Krúžok = najtenšie miesto.")
    S = Image.new("RGB", (SW, 3400), BG)
    d = ImageDraw.Draw(S)
    y0 = header(d, title, intro) + 6
    cams = {(v, pl): Cam(os.path.join(D, f"rez{pl}_{v}_{OPT[v]}_cam.json")) for v in VIDS for pl in "vh"}
    c0 = cams[("0", "v")]
    sc = (cw - 20) / c0.W
    hv = c0.H * sc
    hh = cams[("0", "h")].H * sc
    yt = y0 + 12
    yv = yt + 104
    yh = yv + hv + 46
    yspot = yh + hh + 12
    yend = yspot + 70
    for i, v in enumerate(VIDS):
        n = N[v]
        x0 = M + i * (cw + 14)
        card(d, x0, y0, x0 + cw, yend)
        d.text((x0 + 14, yt), NAME[v], font=fH, fill=INK if v == "0" else ACCENT)
        d.text((x0 + 14, yt + 31), OPTNAME[OPT[v]], font=fN, fill=INK)
        vt, vc = VERD[v]
        wv = tw(d, vt, font(15, "SemiBold"))
        d.rounded_rectangle((x0 + 14, yt + 54, x0 + 14 + wv + 16, yt + 74), 6, fill=vc)
        d.text((x0 + 22, yt + 55), vt, font=font(15, "SemiBold"), fill=(255, 255, 255))
        d.text((x0 + 14 + wv + 26, yt + 56), f"hrúbka pri kĺbe {sk(n['thick_joint'])} mm", font=fSm, fill=MUTED)
        pan = {}
        for pl, yy in (("v", yv), ("h", yh)):
            p = Panel(load(f"rez{pl}_{v}_{OPT[v]}"), cams[(v, pl)], (0, 0, cams[(v, pl)].W, cams[(v, pl)].H), sc, (x0 + 10, yy))
            p.paste(S, bg=(255, 255, 255))
            d.rectangle((p.at[0], p.at[1], p.at[0] + p.w, p.at[1] + p.h), outline=EDGE, width=1)
            pan[pl] = p
        if i == 0:
            d.text((x0 + 14, yv - 20), "zvislý rez (spredu)", font=fSm, fill=MUTED)
            d.text((x0 + 14, yh - 20), "vodorovný rez (zhora)", font=fSm, fill=MUTED)
        # shoulder axis
        for pl in "vh":
            p = pan[pl]
            a, b = p.P((44.0, 3.0, -17.0)), p.P((79.0, 3.0, -17.0))
            for t in np.arange(0, 1, 0.03):
                xa = a[0] + (b[0] - a[0]) * t; xb = a[0] + (b[0] - a[0]) * min(1, t + 0.015)
                d.line([(xa, a[1]), (xb, b[1])], fill=(90, 90, 96), width=1)
        # thin spot: circle + short line to the skin; label in the panel corner nearest to it, with a leader
        sp = n["spot"]
        pl = "h" if v in ("0", "A") else "v"
        p = pan[pl]
        q, s_ = p.P(sp["p"]), p.P(sp["skin"])
        wj, rq = sp["wall_json"], sp["req"]
        col = VERD[v][1]
        rr = 13
        d.line([q, s_], fill=col, width=2)
        d.ellipse((q[0] - rr, q[1] - rr, q[0] + rr, q[1] + rr), outline=col, width=3)
        nd_ = 3 if v == "B" else 2      # B is within 0.1 mm of the limit: show the checker value unrounded (1.585 / +0.085)
        lab = f"{sk(wj, nd_)} mm" if wj >= 0 else f"{sk(-wj, 2)} mm VON"
        wl = tw(d, lab, fD)
        right = q[0] > p.at[0] + p.w * 0.5
        top = q[1] < p.at[1] + p.h * 0.5
        lx = p.at[0] + p.w - wl - 12 if right else p.at[0] + 12
        ly = p.at[1] + 10 if top else p.at[1] + p.h - 34
        la = (lx + wl / 2, ly + (23 if top else -2))
        dl = math.hypot(q[0] - la[0], q[1] - la[1])
        if dl > rr + 2:
            d.line([la, (q[0] - (q[0] - la[0]) * rr / dl, q[1] - (q[1] - la[1]) * rr / dl)], fill=col, width=2)
        d.rounded_rectangle((lx - 5, ly - 2, lx + wl + 5, ly + 23), 4, fill=(255, 255, 255), outline=col, width=2)
        d.text((lx, ly), lab, font=fD, fill=col)
        t1, t2, t3 = SPOTTXT[v]
        d.text((x0 + 14, yspot), t1, font=fN, fill=INK)
        d.text((x0 + 14, yspot + 23), t2.format(w=sk(abs(wj), nd_), r=sk(rq, 2)), font=fB, fill=col)
        d.text((x0 + 14, yspot + 46), t3.format(m=sk(round(wj - rq, 3), nd_), c=sk(round(rq - wj, 3), 2)), font=fSm, fill=MUTED)
        # badges (front section, panels 0 and A)
        if v in ("0", "A"):
            bd = dict(BADGE[OPT[v]])
            bd[1] = skin_pt(v, "v", "out", -30.0)
            bd[2] = skin_pt(v, "v", "in", -34.0)
            for k_, w_ in bd.items():
                badge(d, pan["v"].P(w_), k_)
    # legend
    yl = yend + 16
    card(d, M, yl, SW - M, yl + 150)
    d.text((M + 16, yl + 10), "Diely (čísla v reze 0 a A):", font=fB, fill=INK)
    colx = [M + 16, M + 16 + (SW - 2 * M) // 2]
    for j, (k_, t) in enumerate(LEGEND):
        cx_, cy_ = colx[j // 4], yl + 44 + (j % 4) * 25
        badge(d, (cx_ + 11, cy_ + 10), k_)
        d.text((cx_ + 30, cy_), t, font=fN, fill=INK)
    yc = yl + 150 + 14
    sw = [((0.95, 0.66, 0.34), "biela živica (ruka, bok trupu)"), ((0.20, 0.32, 0.58), "čierna živica (zátka)"),
          ((0.45, 0.68, 0.52), "tlačený unášač"), ((0.66, 0.68, 0.72), "oceľ (kúpené)"), ((0.86, 0.40, 0.42), "magnety")]
    xx = M
    d.text((xx, yc), "Farba rezu:", font=fN, fill=MUTED); xx += tw(d, "Farba rezu:", fN) + 12
    for rgb, t in sw:
        c = tuple(int(255 * a) for a in rgb)
        d.rectangle((xx, yc + 3, xx + 16, yc + 17), fill=c, outline=(120, 120, 120))
        d.text((xx + 22, yc), t, font=fN, fill=MUTED); xx += 22 + tw(d, t, fN) + 18
    foot = ("Steny v reze: vonkajší kryt 1,2 mm (minimum podľa kontroly), vnútorná škrupina 1,6 mm. Prerušovaná čiara = os ramena. Rozmery v mm.\n"
            "Čísla najtenších miest sú z kontroly zmestenia (rovnaké dvoma nezávislými metódami); požiadavka = stena 1,2 mm (+ 0,3 mm vôľa pri dieloch, ktoré sa točia).\n"
            "B: pri posune unášača o 0,1 mm von alebo s bežnou skrutkou DIN 912 namiesto DIN 7984 sa už nezmestí. C: unášač trčí cez kryt; nesedí žiadna\n"
            "z 5 navrhnutých možností (chýba 1,9 – 5,5 mm), ani tá so spojkou presunutou do trupu. Magnety krytu nie sú nakreslené (treba ich presunúť).")
    yb = footer(d, yc + 34, foot) + 22
    finish(S, yb, "v3_prierez_klbom.png")


todo = ONLY or ["spredu", "3d", "ruka", "rez"]
if "spredu" in todo:
    sheet_spredu()
if "3d" in todo:
    sheet_3d()
if "ruka" in todo:
    sheet_ruka()
if "rez" in todo:
    sheet_rez()
