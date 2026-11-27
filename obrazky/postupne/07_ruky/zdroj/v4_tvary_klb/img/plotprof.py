"""line drawing of the variants vs B0: side outline (wi, wo), front view (inner / outer face + seam), sections at a few u.
usage: plotprof.py OUT.png v1,v2,...   (CAD venv)"""
import sys
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R4/tvar")
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import variants_b as VA
out, vids = sys.argv[1], sys.argv[2].split(",")
S = 6.0                     # px per mm
F = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
u = np.linspace(0, 1, 801)
def panel(v):
    W, H = int(150 * S), int(84 * S)
    im = Image.new("RGB", (W, H), "white"); d = ImageDraw.Draw(im)
    def P(y, z, ox, oy):
        return list(zip((ox + np.asarray(y) * S).tolist(), (oy - np.asarray(z) * S).tolist()))
    for vid, col, wd in (("B0", (170, 170, 170), 2), (v, (20, 90, 200), 2)):
        c, ti, to, w, ni, no = [np.asarray(a, float) * np.ones_like(u) for a in VA.section(vid, u)]
        wi_, wo = [np.asarray(a, float) * np.ones_like(u) for a in VA.half_widths(vid, u)] if hasattr(VA, "half_widths") else (w, w)
        z = -VA.L * u
        # side outline (from outside): y = +-w, centred at x0
        ox, oy = 22 * S, 6 * S
        d.line(P(w, z, ox, oy) + P(-w[::-1], z[::-1], ox, oy) + P(w[:1], z[:1], ox, oy), fill=col, width=wd)
        if vid != "B0" and VA.reveal(vid) != 0:
            ww2 = wo if VA.reveal(vid) > 0 else wi_
            d.line(P(ww2, z, ox, oy), fill=(200, 60, 40), width=1); d.line(P(-ww2, z, ox, oy), fill=(200, 60, 40), width=1)
        if vid == "B0":
            zax = -16.2
            for rr, colc in ((13.0, (230, 150, 40)), (15.0, (240, 200, 120))):
                t_ = np.linspace(0, 2 * np.pi, 200)
                d.line(P(rr * np.cos(t_), zax + rr * np.sin(t_), ox, oy), fill=colc, width=1)
        # front view: x faces
        ox2 = 62 * S
        d.line(P(c - ti, z, ox2, oy), fill=col, width=wd); d.line(P(c + to, z, ox2, oy), fill=col, width=wd)
        d.line(P(c, z, ox2, oy), fill=col, width=1)
        # sections
        for k, uu in enumerate((0.06, 0.22, 0.45, 0.75)):
            cc, tti, tto, ww, nni, nno = [float(np.asarray(a)) for a in VA.section(vid, uu)]
            wwi, wwo = [float(np.asarray(a)) for a in VA.half_widths(vid, uu)] if hasattr(VA, "half_widths") else (ww, ww)
            th = np.linspace(0, 2 * np.pi, 400)
            outer = np.cos(th) >= 0
            r = np.where(outer, VA._se_r(tto, wwo, nno, th), VA._se_r(tti, wwi, nni, th))
            x, y = cc + r * np.cos(th), r * np.sin(th)
            ox3, oy3 = (95 + 27 * (k % 2)) * S, (24 + 38 * (k // 2)) * S
            d.line(list(zip((ox3 + x * S).tolist(), (oy3 - y * S).tolist())), fill=col, width=wd)
            d.text((ox3 - 12 * S, oy3 - 19 * S), f"u {uu}", fill=(0, 0, 0), font=F)
    d.text((8, 8), v + "  (modrá) vs B0 (sivá)   bok | spredu | rezy (x vodorovne, von = vpravo)", fill=(0, 0, 0), font=F)
    return im
ims = [panel(v) for v in vids]
sheet = Image.new("RGB", (ims[0].size[0], sum(i.size[1] for i in ims)), "white")
y = 0
for i in ims:
    sheet.paste(i, (0, y)); y += i.size[1]
sheet.save(out); print(out, sheet.size)
