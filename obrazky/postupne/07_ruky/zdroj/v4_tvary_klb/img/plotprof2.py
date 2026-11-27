"""R4 technical comparison (line drawing, Slovak): each new variant (colour) over B0 (grey): outline seen from outside,
thickness seen from the front, sections at u 0.06 / 0.22 / 0.45 / 0.75, plus the joint disc r 13 and its 2.0 wall.
usage: plotprof2.py OUT.png   (CAD venv)"""
import sys, os
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R4/tvar"); sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R3/img/work")
import numpy as np
from PIL import Image, ImageDraw
import variants_b as VA
import sheetlib as SL
out = sys.argv[1]
S = 5.2
F_T, F_H, F_S = SL.font(34), SL.font(22), SL.font(16, "Regular")
COL = {"B1": (20, 150, 190), "B2": (215, 110, 30), "B3": (120, 80, 190)}
GREY = (165, 165, 165)
u = np.linspace(0, 1, 1201)
W = 1400
PH = int(84 * S) + 70
img = Image.new("RGB", (W, 120 + 3 * PH + 80), SL.BG)
d = ImageDraw.Draw(img)
d.text((36, 24), "NOVA mini · ruka B: tvary v číslach (náhľad)", font=F_T, fill=SL.INK)
d.text((36, 74), "Farebne nový variant, sivo dnešná B0. Ľavá ruka v jej vlastnej sústave, mierka 1:1 pre všetky kresby (5,2 px/mm). "
       "Oranžovo unášač kĺbu r 13 a jeho stena 2 mm.", font=F_S, fill=SL.MUTED)


def P(y, z, ox, oy):
    return list(zip((ox + np.asarray(y) * S).tolist(), (oy - np.asarray(z) * S).tolist()))


def sec(vid, uu):
    cc, tti, tto, ww, nni, nno = [float(np.asarray(a)) for a in VA.section(vid, uu)]
    wwi, wwo = [float(np.asarray(a)) for a in VA.half_widths(vid, uu)]
    th = np.linspace(0, 2 * np.pi, 600)
    r = np.where(np.cos(th) >= 0, VA._se_r(tto, wwo, nno, th), VA._se_r(tti, wwi, nni, th))
    return cc + r * np.cos(th), r * np.sin(th)


for k, v in enumerate(("B1", "B2", "B3")):
    y0 = 120 + k * PH
    d.rounded_rectangle([24, y0, W - 24, y0 + PH - 12], 12, fill=(250, 250, 248), outline=(222, 222, 218))
    d.text((40, y0 + 10), VA.params(v)["name"], font=F_H, fill=COL[v])
    oy = y0 + 50
    ox1, ox2 = 40 + 18 * S, 40 + 18 * S + 40 * S
    d.text((ox1 - 17 * S, oy - 6), "zvonka (obrys)", font=F_S, fill=SL.MUTED)
    d.text((ox2 - 13 * S, oy - 6), "spredu (hrúbka; vľavo trup)", font=F_S, fill=SL.MUTED)
    zax = -16.9            # shoulder axis at the disc (local x ~ -1.5); the disc plane is tilted 12 deg -> ellipse in this view
    for rr, cc_ in ((13.0, (235, 160, 60)), (15.0, (245, 205, 140))):
        t_ = np.linspace(0, 2 * np.pi, 240)
        d.line(P(rr * np.cos(t_), zax + rr * np.cos(np.radians(12)) * np.sin(t_), ox1, oy + 18), fill=cc_, width=2)
    for vid, col, wd in (("B0", GREY, 2), (v, COL[v], 3)):
        c, ti, to, w, _, _ = [np.asarray(a, float) * np.ones_like(u) for a in VA.section(vid, u)]
        wi, wo = [np.asarray(a, float) * np.ones_like(u) for a in VA.half_widths(vid, u)]
        z = -VA.L * u
        oyy = oy + 18
        d.line(P(w, z, ox1, oyy) + P(-w[::-1], z[::-1], ox1, oyy), fill=col, width=wd)
        if vid != "B0" and VA.reveal(vid) != 0:
            ww2 = np.minimum(wi, wo)
            d.line(P(ww2, z, ox1, oyy), fill=col, width=1); d.line(P(-ww2, z, ox1, oyy), fill=col, width=1)
        d.line(P(c - ti, z, ox2, oyy), fill=col, width=wd); d.line(P(c + to, z, ox2, oyy), fill=col, width=wd)
        d.line(P(c, z, ox2, oyy), fill=col, width=1)
        for j, uu in enumerate((0.06, 0.22, 0.45, 0.75)):
            x, y = sec(vid, uu)
            ox3, oy3 = 40 + 98 * S + j * 46 * S, oy + 40 * S
            # section: x horizontal (towards the torso = left), y vertical (front = down)
            d.line(list(zip((ox3 + x * S).tolist(), (oy3 + y * S).tolist())), fill=col, width=wd)
            if vid == "B0":
                d.text((ox3 - 8 * S, oy3 - 22 * S), f"rez u = {uu:.2f}".replace(".", ","), font=F_S, fill=SL.MUTED)
    d.text((40 + 98 * S - 14 * S, oy + 64 * S), "rezy zhora: vľavo trup, vpravo von, hore predok", font=F_S, fill=SL.MUTED)
img.save(out)
print(out, img.size)
