"""slices of kmap.npz.  usage: kslice.py x=36,40 z=-45 y=-20  [tag]"""
import sys, os
import numpy as np
from PIL import Image, ImageDraw
HERE = "/tmp/claude-0/gapwf/fin/R1/K1_roh_kolesa"
D = np.load(os.path.join(HERE, "kmap.npz"))
lo, h, n, cat = D["lo"], float(D["h"]), D["n"], D["cat"]
cols = {0: (35, 35, 35), 1: (255, 255, 255), 2: (235, 130, 130), 3: (60, 90, 200), 4: (150, 150, 150), 5: (250, 205, 70),
        6: (110, 200, 110), 9: (140, 200, 250)}
S = 5
def save(img2d, name, x0, y0, title, extra=None):
    H_, W_ = img2d.shape
    rgb = np.zeros((H_, W_, 3), np.uint8)
    for k, c in cols.items():
        rgb[img2d == k] = c
    im = Image.fromarray(rgb[::-1]).resize((W_ * S, H_ * S), Image.NEAREST)
    d = ImageDraw.Draw(im)
    for v in np.arange(np.ceil(x0 / 2) * 2, x0 + W_ * h, 2):
        px = (v - x0) / h * S
        d.line([(px, 0), (px, H_ * S)], fill=(215, 215, 215) if v % 10 else (90, 90, 90), width=1)
        if v % 10 == 0: d.text((px + 2, 2), f"{v:.0f}", fill=(0, 0, 0))
    for v in np.arange(np.ceil(y0 / 2) * 2, y0 + H_ * h, 2):
        py = H_ * S - (v - y0) / h * S
        d.line([(0, py), (W_ * S, py)], fill=(215, 215, 215) if v % 10 else (90, 90, 90), width=1)
        if v % 10 == 0: d.text((2, py + 2), f"{v:.0f}", fill=(0, 0, 0))
    if extra: extra(d, x0, y0, H_)
    d.text((10, H_ * S - 14), title, fill=(255, 0, 0))
    im.save(os.path.join(HERE, "img", name))
tag = sys.argv[-1] if not "=" in sys.argv[-1] else ""
for arg in sys.argv[1:]:
    if "=" not in arg: continue
    a, vals = arg.split("=")
    for v in [float(s) for s in vals.split(",")]:
        if a == "x":
            i = int((v - lo[0]) / h); sl = cat[i, :, :].T
            save(sl, f"kx{v:+.1f}{tag}.png", lo[1], lo[2], f"x = {v}  (y right, z up)")
        elif a == "z":
            k = int((v - lo[2]) / h); i0 = int((0 - lo[0]) / h); sl = cat[i0:, :, k].T
            save(sl, f"kz{v:+.1f}{tag}.png", 0.0, lo[1], f"z = {v}  (x right, y up)")
        elif a == "y":
            j = int((v - lo[1]) / h); i0 = int((0 - lo[0]) / h); sl = cat[i0:, j, :].T
            save(sl, f"ky{v:+.1f}{tag}.png", 0.0, lo[2], f"y = {v}  (x right, z up)")
