"""slices of the K1 obstacle model: usage k1_slice.py x=40 y=-20 z=-50 [label=name]
colours: black outside, dark blue shell wall, grey other HARD, red MOVE, yellow CHG (may be removed), white free,
pale yellow-white = free but closer than 0.3 / 1.0 (+0.25) to HARD / MOVE. Part names of HARD voxels are printed per slice."""
import sys, os
import numpy as np
from PIL import Image, ImageDraw
HERE = "/tmp/claude-0/gapwf/fin/R1/K1_roh_kolesa"
D = np.load(os.path.join(HERE, "k1_hard.npz")); M = np.load("/tmp/claude-0/gapwf/fin/R1/trup_servo/map1.npz")
K = np.load(os.path.join(HERE, "kmap.npz"))
lo, h = D["lo"], float(D["h"]); i0 = int(round((lo[0] - M["lo"][0]) / h))
lab = M["label"][i0:]; ln = [str(s) for s in M["lab_names"]]; cat = K["cat"][i0:]
hard, move, chg, inter = D["hard"], D["move"], D["chg"], D["interior"]
near = ((D["ds"] < 0.55) | (D["dm"] < 1.25)) & ~hard & ~move
img = np.full(hard.shape, 1, np.uint8)
img[near] = 7; img[chg] = 5; img[hard] = 4; img[hard & (cat == 3)] = 3; img[move] = 2; img[~inter] = 0
cols = {0: (30, 30, 30), 1: (255, 255, 255), 2: (235, 120, 120), 3: (50, 80, 190), 4: (150, 150, 150), 5: (250, 205, 70),
        7: (245, 240, 215)}
S = 6
tag = ""
for arg in sys.argv[1:]:
    if arg.startswith("label="): tag = arg[6:]
for arg in sys.argv[1:]:
    if "=" not in arg or arg.startswith("label="): continue
    a, vals = arg.split("=")
    for v in [float(s) for s in vals.split(",")]:
        ax = "xyz".index(a); k = int((v - lo[ax]) / h)
        if ax == 0: sl = img[k].T; ls = lab[k]; hh = hard[k]; o0, o1 = lo[1], lo[2]; xl = "y"; yl = "z"
        elif ax == 1: sl = img[:, k].T; ls = lab[:, k]; hh = hard[:, k]; o0, o1 = lo[0], lo[2]; xl = "x"; yl = "z"
        else: sl = img[:, :, k].T; ls = lab[:, :, k]; hh = hard[:, :, k]; o0, o1 = lo[0], lo[1]; xl = "x"; yl = "y"
        ids, cnt = np.unique(ls[hh], return_counts=True)
        print(a, v, "HARD parts:", ", ".join(f"{ln[i]}:{c}" for i, c in zip(ids, cnt) if i > 0))
        H_, W_ = sl.shape
        rgb = np.zeros((H_, W_, 3), np.uint8)
        for kk, c in cols.items(): rgb[sl == kk] = c
        im = Image.fromarray(rgb[::-1]).resize((W_ * S, H_ * S), Image.NEAREST); d = ImageDraw.Draw(im)
        for g in np.arange(np.ceil(o0), o0 + W_ * h, 1.0):
            px = (g - o0) / h * S
            if g % 5 == 0: d.line([(px, 0), (px, H_ * S)], fill=(200, 200, 200) if g % 10 else (90, 90, 90), width=1)
            if g % 10 == 0: d.text((px + 2, 2), f"{g:.0f}", fill=(0, 120, 0))
        for g in np.arange(np.ceil(o1), o1 + H_ * h, 1.0):
            py = H_ * S - (g - o1) / h * S
            if g % 5 == 0: d.line([(0, py), (W_ * S, py)], fill=(200, 200, 200) if g % 10 else (90, 90, 90), width=1)
            if g % 10 == 0: d.text((2, py + 2), f"{g:.0f}", fill=(0, 120, 0))
        if ax == 0:
            cy, cz = (3 - o0) / h * S, H_ * S - (-17 - o1) / h * S
            d.ellipse([cy - 4, cz - 4, cy + 4, cz + 4], outline=(255, 0, 0), width=2)
        d.text((10, H_ * S - 14), f"{a} = {v}  ({xl} right, {yl} up)", fill=(255, 0, 0))
        im.save(os.path.join(HERE, "img", f"h{a}{v:+.1f}{tag}.png"))
