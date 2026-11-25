"""exact STL plane sections (line segments) of the T4 torso, drawn with PIL.  K2 work (diagnostic, not for the user)."""
import sys, os, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T4/overenie3"); import vlib
T4 = "/tmp/claude-0/gapwf/fin/T4"; BST = "/tmp/claude-0/gapwf/fin/B/stl"
PJ = json.load(open(T4 + "/parts.json")); REC = {p["name"]: p for p in PJ["parts"]}
FONT = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
_C = {}
def tris(name):
    if name not in _C:
        p = T4 + "/stl/" + name + ".stl"
        if not os.path.exists(p): p = BST + "/" + name + ".stl"
        _C[name] = vlib.load_stl(p)
    return _C[name]
def cut(tr, axis, v):
    d = tr[:, :, axis] - v
    s = np.sign(d); s[s == 0] = 1e-9
    m = ~((s[:, 0] > 0) & (s[:, 1] > 0) & (s[:, 2] > 0)) & ~((s[:, 0] < 0) & (s[:, 1] < 0) & (s[:, 2] < 0))
    T = tr[m]; D = d[m]
    segs = []
    for (i, j) in ((0, 1), (1, 2), (2, 0)):
        a, b = D[:, i], D[:, j]
        cr = (a * b) < 0
        t = a / np.where(cr, a - b, 1)
        P = T[:, i] + (T[:, j] - T[:, i]) * t[:, None]
        segs.append(np.where(cr[:, None], P, np.nan))
    S = np.stack(segs, 1)  # (n, 3 edges, 3)
    out = []
    for k in range(len(S)):
        q = S[k][~np.isnan(S[k][:, 0])]
        if len(q) >= 2: out.append(q[:2])
    return np.array(out)
PAL = [(31, 119, 180), (255, 127, 14), (44, 160, 44), (214, 39, 40), (148, 103, 189), (140, 86, 75), (227, 119, 194),
       (127, 127, 127), (188, 189, 34), (23, 190, 207), (0, 0, 0)]
def draw(axis, v, rh, rv, parts=None, scale=10, extra=None, fname=None, title=""):
    ah, av = {0: (1, 2), 1: (0, 2), 2: (0, 1)}[axis]
    W = int((rh[1] - rh[0]) * scale); Hh = int((rv[1] - rv[0]) * scale)
    im = Image.new("RGB", (W, Hh), (255, 255, 255)); dr = ImageDraw.Draw(im)
    def px(h, vv): return ((h - rh[0]) * scale, (rv[1] - vv) * scale)
    for g in np.arange(np.ceil(rh[0]), rh[1], 1.0):
        c = (200, 200, 255) if g % 5 else (140, 140, 255)
        if g % 1 == 0 and (g % 5 == 0 or scale >= 8): dr.line([px(g, rv[0]), px(g, rv[1])], fill=c if g % 5 == 0 else (235, 235, 255))
        if g % 5 == 0: dr.text((px(g, rv[1])[0] + 2, 2), f"{g:.0f}", fill=(0, 0, 150), font=FONT)
    for g in np.arange(np.ceil(rv[0]), rv[1], 1.0):
        c = (140, 140, 255) if g % 5 == 0 else (235, 235, 255)
        dr.line([px(rh[0], g), px(rh[1], g)], fill=c)
        if g % 5 == 0: dr.text((2, px(rh[0], g)[1] + 1), f"{g:.0f}", fill=(0, 0, 150), font=FONT)
    if parts is None:
        parts = [n for n, r in REC.items() if r["group"] in ("T",)] + ["golier_prstenec"]
    legend = []
    k = 0
    for n in parts:
        tr = tris(n)
        lo = tr.reshape(-1, 3).min(0); hi = tr.reshape(-1, 3).max(0)
        if not (lo[axis] <= v <= hi[axis]): continue
        if hi[ah] < rh[0] or lo[ah] > rh[1] or hi[av] < rv[0] or lo[av] > rv[1]: continue
        S = cut(tr, axis, v)
        if len(S) == 0: continue
        col = PAL[k % len(PAL)]; k += 1
        for s in S:
            dr.line([px(s[0][ah], s[0][av]), px(s[1][ah], s[1][av])], fill=col, width=2)
        m = S.reshape(-1, 3).mean(0)
        legend.append((n, col))
    if extra:
        extra(dr, px)
    y0 = 18
    for n, c in legend:
        dr.rectangle([W - 170, y0, W - 160, y0 + 10], fill=c); dr.text((W - 156, y0 - 2), n, fill=(0, 0, 0), font=FONT); y0 += 14
    an = "xyz"
    dr.text((4, Hh - 16), f"{title} {an[axis]} = {v}  (h {an[ah]}, v {an[av]})", fill=(0, 0, 0), font=FONT)
    fname = fname or f"/tmp/claude-0/gapwf/fin/R1/K2_dole_remen/diag/e_{an[axis]}{v:+.1f}.png"
    im.save(fname); return fname
if __name__ == "__main__":
    for a in sys.argv[1:]:
        ax = "xyz".index(a[0]); v = float(a[1:])
        if ax == 0: print(draw(0, v, (-26, 30), (-50, 0), scale=10))
        elif ax == 1: print(draw(1, v, (28, 52), (-50, 0), scale=12))
        else: print(draw(2, v, (25, 52), (-30, 30), scale=12))
