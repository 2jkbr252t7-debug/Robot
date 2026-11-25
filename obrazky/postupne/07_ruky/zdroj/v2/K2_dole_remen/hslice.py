"""diagnostic slices of the K2 'hard' map: hard static (dark, per label hue), removable static (light grey),
moving sweep (orange), free_h (green), free_h on the T_stred lowering path (blue). usage: hslice.py x38 z-70 ..."""
import sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
D = np.load("/tmp/claude-0/gapwf/fin/R1/trup_servo/map1.npz"); lo, H = D["lo"], float(D["h"])
Hd = np.load("/tmp/claude-0/gapwf/fin/R1/K2_dole_remen/hard.npz")
hard, free_h = Hd["hard"], Hd["free_h"]
static, moving, label, interior, lower = D["static"], D["moving"], D["label"], D["interior"], D["lower"]
names = [str(s) for s in D["lab_names"]]
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11)
OUT = "/tmp/claude-0/gapwf/fin/R1/K2_dole_remen/d2"
def make(axis, v, rh, rv, sc=8):
    i = int((v - lo[axis]) / H); sl = [slice(None)] * 3; sl[axis] = i; sl = tuple(sl)
    ah, av = [a for a in range(3) if a != axis]
    S, HD, M, F, L, I, LO = static[sl], hard[sl], moving[sl], free_h[sl], label[sl], interior[sl], lower[sl]
    img = np.full(S.shape + (3,), 255, np.uint8)
    img[I] = (240, 240, 240)
    img[S & ~HD] = (200, 200, 200)
    hue = (L.astype(np.int64) * 53) % 110
    img[HD] = np.stack([40 + hue, 40 + hue // 2, 60 + hue], -1)[HD]
    img[M] = (240, 150, 40)
    img[F] = (60, 190, 80)
    img[F & LO] = (70, 130, 220)
    ha = lo[ah] + (np.arange(S.shape[0]) + 0.5) * H; va = lo[av] + (np.arange(S.shape[1]) + 0.5) * H
    i0, i1 = np.searchsorted(ha, rh[0]), np.searchsorted(ha, rh[1]); j0, j1 = np.searchsorted(va, rv[0]), np.searchsorted(va, rv[1])
    img = img[i0:i1, j0:j1]; L2 = L[i0:i1, j0:j1]; HD2 = HD[i0:i1, j0:j1]
    img = np.transpose(img, (1, 0, 2))[::-1]
    im = Image.fromarray(img).resize((img.shape[1] * sc, img.shape[0] * sc), Image.NEAREST)
    dr = ImageDraw.Draw(im); pxmm = sc / H
    for g in np.arange(np.ceil(rh[0]), rh[1], 1.0):
        x = (g - rh[0]) * pxmm
        if g % 5 == 0: dr.line([(x, 0), (x, im.size[1])], fill=(90, 90, 255) if g % 10 == 0 else (160, 160, 255)); dr.text((x + 2, 2), f"{g:.0f}", fill=(0, 0, 160), font=font)
    for g in np.arange(np.ceil(rv[0]), rv[1], 1.0):
        y = (rv[1] - g) * pxmm
        if g % 5 == 0: dr.line([(0, y), (im.size[0], y)], fill=(90, 90, 255) if g % 10 == 0 else (160, 160, 255)); dr.text((2, y + 1), f"{g:.0f}", fill=(0, 0, 160), font=font)
    for lb in np.unique(L2[HD2]):
        m = (L2 == lb) & HD2
        if m.sum() < 8: continue
        ii, jj = np.nonzero(m); k = len(ii) // 2
        o = np.lexsort((jj, ii)); ii, jj = ii[o], jj[o]
        dr.text((ii[k] * sc, (L2.shape[1] - 1 - jj[k]) * sc), names[lb], fill=(255, 255, 0), font=font)
    an = "xyz"; dr.text((4, im.size[1] - 14), f"{an[axis]} = {v}  (h {an[ah]}, v {an[av]})", fill=(0, 0, 0), font=font)
    p = os.path.join(OUT, f"h_{an[axis]}{v:+.1f}.png"); im.save(p); print(p)
for a in sys.argv[1:]:
    ax = "xyz".index(a[0]); v = float(a[1:])
    if ax == 0: make(0, v, (-33, 33), (-84, 4), 6)
    elif ax == 1: make(1, v, (10, 52), (-84, 4), 6)
    else: make(2, v, (5, 52), (-33, 33), 8)
