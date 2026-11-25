"""quick PIL slices of k3map.npz: usage slices.py axis=value [axis=value ...] [--zoom x0 x1 y0 y1] ; colours:
hard grey, removable (chg) yellow, moving orange, free white (ds>=0.55 & dm>=1.25 & interior), tight-free light green, outside dark"""
import sys, os
sys.dont_write_bytecode = True
import numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
D = np.load(os.path.join(HERE, "k3map.npz"))
lo, h, n = D["lo"], float(D["h"]), tuple(D["n"])
hard, chg, move, interior, ds, dm = D["hard"], D["chg"], D["move"], D["interior"], D["ds"], D["dm"]
free = interior & ~hard & (ds >= 0.55) & (dm >= 1.25)
def rgb():
    C = np.zeros(n + (3,), np.uint8); C[:] = (40, 40, 40)
    C[interior] = (200, 240, 200)
    C[free] = (255, 255, 255)
    C[chg] = (250, 200, 60)
    C[move] = (240, 140, 40)
    C[hard & interior] = (130, 130, 140)
    return C
C = rgb()
S = 6
for arg in sys.argv[1:]:
    ax, v = arg.split("="); a = "xyz".index(ax); v = float(v)
    k = int(np.floor((v - lo[a]) / h))
    sl = [slice(None)] * 3; sl[a] = k
    img = C[tuple(sl)]               # 2-D: remaining axes in order
    rem = [i for i in range(3) if i != a]
    im = np.transpose(img, (1, 0, 2))[::-1]   # rows = second remaining axis (up), cols = first
    I = Image.fromarray(np.repeat(np.repeat(im, S, 0), S, 1))
    d = ImageDraw.Draw(I)
    H, W = I.size[1], I.size[0]
    for g in range(-100, 101, 5):
        for j, axi in enumerate(rem):
            p = (g - lo[axi]) / h * S
            if j == 0 and 0 <= p < W:
                d.line([(p, 0), (p, H)], fill=(80, 80, 255) if g % 10 == 0 else (190, 190, 255), width=1)
                if g % 10 == 0: d.text((p + 2, 2), str(g), fill=(0, 0, 160))
            if j == 1 and 0 <= p < H:
                q = H - p
                d.line([(0, q), (W, q)], fill=(80, 80, 255) if g % 10 == 0 else (190, 190, 255), width=1)
                if g % 10 == 0: d.text((2, q + 2), str(g), fill=(0, 0, 160))
    d.text((10, H - 14), f"{ax} = {v}", fill=(255, 0, 0))
    out = os.path.join(HERE, "img", f"s_{ax}{v:+.1f}.png"); I.save(out); print(out)
