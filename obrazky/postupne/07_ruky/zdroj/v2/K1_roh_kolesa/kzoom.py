"""zoomed y-z slices around the shoulder (y -30..25, z -70..4) at given x; T_bok features light blue, wall dark blue,
T_spodok yellow, T_klb + other changeable orange-ish, moving red"""
import sys, os
import numpy as np
from PIL import Image, ImageDraw
HERE = "/tmp/claude-0/gapwf/fin/R1/K1_roh_kolesa"
D = np.load(os.path.join(HERE, "kmap.npz")); M = np.load("/tmp/claude-0/gapwf/fin/R1/trup_servo/map1.npz")
lo, h, cat = D["lo"], float(D["h"]), D["cat"].copy()
lab, ln = M["label"], [str(s) for s in M["lab_names"]]
idx = {nm: i for i, nm in enumerate(ln)}
cat[np.isin(lab, [idx["T_klb_L"], idx["T_klb_P"]])] = 7
cat[np.isin(lab, [idx[n] for n in ln if n.startswith(("skrutka_klb", "podlozka_klb", "vl_F8"))])] = 8
cols = {0: (35, 35, 35), 1: (255, 255, 255), 2: (235, 130, 130), 3: (60, 90, 200), 4: (150, 150, 150), 5: (250, 205, 70),
        6: (110, 200, 110), 7: (200, 130, 220), 8: (90, 60, 60), 9: (140, 200, 250)}
S = 8
y0, y1, z0, z1 = -32.0, 26.0, -72.0, 4.0
j0, j1 = int((y0 - lo[1]) / h), int((y1 - lo[1]) / h); k0, k1 = int((z0 - lo[2]) / h), int((z1 - lo[2]) / h)
for xv in [float(s) for s in sys.argv[1].split(",")]:
    i = int((xv - lo[0]) / h)
    sl = cat[i, j0:j1, k0:k1].T
    H_, W_ = sl.shape
    rgb = np.zeros((H_, W_, 3), np.uint8)
    for k, c in cols.items(): rgb[sl == k] = c
    im = Image.fromarray(rgb[::-1]).resize((W_ * S, H_ * S), Image.NEAREST); d = ImageDraw.Draw(im)
    for v in np.arange(np.ceil(y0), y1, 1.0):
        px = (v - y0) / h * S
        if v % 2 == 0 or True: d.line([(px, 0), (px, H_ * S)], fill=(225, 225, 225) if v % 5 else (80, 80, 80), width=1)
        if v % 5 == 0: d.text((px + 2, 2), f"{v:.0f}", fill=(0, 0, 0))
    for v in np.arange(np.ceil(z0), z1, 1.0):
        py = H_ * S - (v - z0) / h * S
        d.line([(0, py), (W_ * S, py)], fill=(225, 225, 225) if v % 5 else (80, 80, 80), width=1)
        if v % 5 == 0: d.text((2, py + 2), f"{v:.0f}", fill=(0, 0, 0))
    cy, cz = (3 - y0) / h * S, H_ * S - (-17 - z0) / h * S
    for r in (10, 14, 16):
        d.ellipse([cy - r / h * S, cz - r / h * S, cy + r / h * S, cz + r / h * S], outline=(255, 0, 0))
    d.text((10, H_ * S - 14), f"x = {xv}  (y right, z up); circles r 10/14/16 about the shoulder axis", fill=(255, 0, 0))
    im.save(os.path.join(HERE, "img", f"zx{xv:+.1f}.png"))
