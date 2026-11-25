"""Diagnostic slices of the existing voxel map (map1.npz) for the left half: category colours."""
import sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
D = np.load("/tmp/claude-0/gapwf/fin/R1/trup_servo/map1.npz")
lo, h, n = D["lo"], float(D["h"]), D["n"]
lab, ln = D["label"], list(D["lab_names"])
interior, moving, static = D["interior"], D["moving"], D["static"]
SHELL = {"T_stred", "T_bok_L", "T_bok_P", "T_dvere"}
cat = np.zeros(lab.shape, np.uint8)  # 0 outside, 1 free interior
cat[interior] = 1
cols = {0: (40, 40, 40), 1: (255, 255, 255), 2: (230, 120, 120), 3: (120, 160, 230), 4: (160, 160, 160), 5: (250, 200, 60),
        6: (120, 200, 120), 7: (200, 120, 220), 8: (90, 90, 160)}
idx = {nm: i for i, nm in enumerate(ln)}
def lid(names):
    return np.isin(lab, [idx[x] for x in names if x in idx])
cat[static] = 4
cat[lid(SHELL)] = 3
cat[lid(["T_spodok"])] = 5
cat[lid(["servo_pan", "pastorok_pan"])] = 6
cat[lid(["T_klb_L", "T_klb_P"])] = 7
cat[lid(["servo_J1"])] = 8
cat[moving & (cat <= 1)] = 2
out = "/tmp/claude-0/gapwf/fin/R1/K1_roh_kolesa/img"
S = 4
def ax(a):
    return lo[a] + (np.arange(n[a]) + 0.5) * h
def save(img2d, name, xlab, ylab, x0, y0, title):
    H_, W_ = img2d.shape
    rgb = np.zeros((H_, W_, 3), np.uint8)
    for k, c in cols.items():
        rgb[img2d == k] = c
    im = Image.fromarray(rgb[::-1]).resize((W_ * S, H_ * S), Image.NEAREST)
    d = ImageDraw.Draw(im)
    # grid every 5 mm
    for v in np.arange(np.ceil(x0 / 5) * 5, x0 + W_ * h, 5):
        px = (v - x0) / h * S
        d.line([(px, 0), (px, H_ * S)], fill=(200, 200, 200) if v % 10 else (120, 120, 120), width=1)
        if v % 10 == 0: d.text((px + 2, 2), f"{v:.0f}", fill=(0, 0, 0))
    for v in np.arange(np.ceil(y0 / 5) * 5, y0 + H_ * h, 5):
        py = H_ * S - (v - y0) / h * S
        d.line([(0, py), (W_ * S, py)], fill=(200, 200, 200) if v % 10 else (120, 120, 120), width=1)
        if v % 10 == 0: d.text((2, py + 2), f"{v:.0f}", fill=(0, 0, 0))
    d.text((10, H_ * S - 14), title + f"  ({xlab} right, {ylab} up)", fill=(255, 0, 0))
    im.save(os.path.join(out, name))
X, Y, Z = ax(0), ax(1), ax(2)
for xv in [float(v) for v in sys.argv[1].split(",")] if len(sys.argv) > 1 else []:
    i = int((xv - lo[0]) / h)
    sl = cat[i, :, :].T  # rows z, cols y
    save(sl, f"x{xv:+.1f}.png", "y", "z", Y[0] - h / 2, Z[0] - h / 2, f"x = {xv}")
for zv in [float(v) for v in sys.argv[2].split(",")] if len(sys.argv) > 2 else []:
    k = int((zv - lo[2]) / h)
    i0 = int((0 - lo[0]) / h)
    sl = cat[i0:, :, k].T  # rows y, cols x
    save(sl, f"z{zv:+.1f}.png", "x", "y", 0.0, Y[0] - h / 2, f"z = {zv}")
