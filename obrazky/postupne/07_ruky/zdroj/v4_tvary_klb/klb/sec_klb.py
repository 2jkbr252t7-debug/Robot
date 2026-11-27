"""R4/klb: check sections through the shoulder axis (plane y = 3, seen from the front) of each variant: outlines of the
exact meshes (T_bok_L, plug, collar / ring, printable hub part, M2b joint parts) + the analytic arm B section.
CAD venv: /opt/venv/cad/bin/python sec_klb.py -> prev500/rez_<vid>.png + prev500/rez_klb.png"""
import os, sys, json, math
import numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "work"))
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R3/img/work")
import klb as K, stlu
import sheetlib as SL
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R3/tvar")
import variants as VA

PPM = 22
X0, X1, Z0, Z1 = 38.0, 64.0, -34.0, 0.0
Y = K.YA
M2B = "/tmp/claude-0/gapwf/fin/R3/mech/stl/M2b"


def slice_y(T, y):
    """segments of the triangle soup T cut by the plane Y = y -> list of ((x, z), (x, z))"""
    d = T[:, :, 1] - y
    s = np.sign(d)
    m = (s.max(1) > 0) & (s.min(1) < 0)
    segs = []
    for tri, dd in zip(T[m], d[m]):
        pts = []
        for i in range(3):
            a, b = tri[i], tri[(i + 1) % 3]
            da, db = dd[i], dd[(i + 1) % 3]
            if (da > 0) != (db > 0):
                t = da / (da - db)
                p = a + t * (b - a)
                pts.append((p[0], p[2]))
        if len(pts) == 2:
            segs.append(pts)
    return segs


def px(x, z):
    return ((x - X0) * PPM, (Z1 - z) * PPM)


def draw_segs(d, segs, col, w=2):
    for a, b in segs:
        d.line([px(*a), px(*b)], fill=col, width=w)


TB = stlu.load("/tmp/claude-0/gapwf/fin/R1/img_v2/work/stl_mod/T_bok_L.stl")
SEG_TB = slice_y(TB, Y)
M2 = {f[:-4]: slice_y(stlu.load(os.path.join(M2B, f)), Y) for f in os.listdir(M2B) if f.endswith(".stl")}


def arm_mask(dx):
    w, h = int((X1 - X0) * PPM), int((Z1 - Z0) * PPM)
    xs = X0 + (np.arange(w) + 0.5) / PPM
    zs = Z1 - (np.arange(h) + 0.5) / PPM
    X, Z = np.meshgrid(xs, zs)
    P = np.c_[X.ravel(), np.full(X.size, Y), Z.ravel()]
    ins = VA.inside_local("B", VA.to_local(P, "B", dx)).reshape(h, w)
    return ins


imgs = []
for vid in K.VIDS:
    v = K.variant(vid)
    dx = v["dx"]; sh = dx - K.DX0
    w, h = int((X1 - X0) * PPM), int((Z1 - Z0) * PPM)
    im = Image.new("RGB", (w, h), (250, 250, 248))
    a = arm_mask(dx)
    arr = np.asarray(im).copy()
    arr[a] = (226, 226, 222)
    # arm opening (inner half): show as background inside r < hole_r on the inner side
    im = Image.fromarray(arr)
    d = ImageDraw.Draw(im)
    for xg in range(int(X0), int(X1) + 1):
        d.line([px(xg, Z0), px(xg, Z1)], fill=(238, 238, 235) if xg % 5 else (220, 220, 216), width=1)
    d.line([px(X0, K.ZA), px(X1, K.ZA)], fill=(180, 180, 200), width=1)
    draw_segs(d, SEG_TB, (120, 120, 120), 2)
    for nm, sg in M2.items():
        if nm.startswith(("PLG_",)):
            continue
        sgs = [((p[0] + sh, p[1]), (q[0] + sh, q[1])) for p, q in sg]
        draw_segs(d, sgs, (150, 160, 190), 1)
    for p in v["parts"]:
        T = stlu.load(p["stl"])
        col = (30, 60, 140) if p["role"] == "static" else (220, 110, 20)
        if p["id"] == "PLG_skrutky":
            col = (90, 90, 90)
        draw_segs(d, slice_y(T, Y), col, 2)
        if "print_stl" in p:
            draw_segs(d, slice_y(stlu.load(p["print_stl"]), Y), (240, 170, 60), 1)
    d.text((8, 6), v["name_sk"], font=SL.font(18), fill=SL.INK)
    d.text((8, 30), "rez rovinou y = 3 (os ramena), pohľad spredu", font=SL.font(13, "Regular"), fill=SL.MUTED)
    p_ = os.path.join(HERE, "prev500", f"rez_{vid}.png")
    im.save(p_)
    imgs.append(im)
    print(p_)
W_ = sum(i.size[0] for i in imgs) + 8 * (len(imgs) - 1)
S = Image.new("RGB", (W_, imgs[0].size[1] + 40), (255, 255, 255))
x = 0
for i in imgs:
    S.paste(i, (x, 0)); x += i.size[0] + 8
d = ImageDraw.Draw(S)
d.text((8, imgs[0].size[1] + 10), "šedá: bok trupu T_bok_L · modrá: zátka/kryt (pevné) · oranžová: golier/prstenec (s rukou), svetlooranžová: čierny "
       "náboj tlačený s ním · sivomodrá: diely kĺbu M2b · plocha: ruka B", font=SL.font(14, "Regular"), fill=SL.MUTED)
S.save(os.path.join(HERE, "prev500", "rez_klb.png"))
print("ok", S.size)
