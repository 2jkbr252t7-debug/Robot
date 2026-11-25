"""diagnostic label slices of the R1 voxel map (left half), for K2 (not for the user)"""
import sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
D = np.load("/tmp/claude-0/gapwf/fin/R1/trup_servo/map1.npz")
lo, H = D["lo"], float(D["h"]); n = tuple(D["n"])
interior, static, moving, label = D["interior"], D["static"], D["moving"], D["label"]
names = [str(s) for s in D["lab_names"]]
lower, s1 = D["lower"], D["s1"]
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11)
OUT = "/tmp/claude-0/gapwf/fin/R1/K2_dole_remen/diag"
COL = {"T_spodok": (70, 80, 110), "T_bok_L": (200, 200, 170), "T_bok_P": (200, 200, 170), "T_stred": (225, 215, 190),
       "T_klb_L": (40, 40, 40), "servo_J1": (60, 110, 220), "servo_pan": (60, 200, 220), "zosilnovac": (40, 160, 40),
       "DPS_riadenie": (20, 120, 20), "menic": (40, 160, 40), "kondenzator": (120, 200, 60), "T_paluba": (150, 90, 160),
       "T_most": (170, 170, 170), "usb_predlzovac": (100, 220, 100), "T_dvere": (230, 200, 200)}
def col(nm):
    if nm in COL: return COL[nm]
    h = (hash(nm) % 97)
    return (150 + h % 60, 100 + (h * 7) % 80, 100 + (h * 13) % 90)
def make(axis, value, rng_h, rng_v, scale=6):
    i = int((value - lo[axis]) / H)
    sl = [slice(None)] * 3; sl[axis] = i; sl = tuple(sl)
    S, M, L, I, LO, S1 = static[sl], moving[sl], label[sl], interior[sl], lower[sl], s1[sl]
    ah, av = [a for a in range(3) if a != axis]
    if axis == 0: ah, av = 1, 2
    if axis == 1: ah, av = 0, 2
    if axis == 2: ah, av = 0, 1
    # S indexed [ah, av] after removing axis (order preserved)
    img = np.full(S.shape + (3,), 255, np.uint8)
    img[I] = (245, 245, 245)
    img[I & LO] = (225, 235, 250)
    img[I & S1] = (240, 225, 245)
    labs = np.unique(L[S])
    for lb in labs:
        img[S & (L == lb)] = col(names[lb])
    img[M] = (240, 150, 40)
    img = np.transpose(img, (1, 0, 2))[::-1]  # rows = av (top = +), cols = ah
    ha = lo[ah] + (np.arange(S.shape[0]) + 0.5) * H; va = lo[av] + (np.arange(S.shape[1]) + 0.5) * H
    c0, c1 = np.searchsorted(ha, rng_h[0]), np.searchsorted(ha, rng_h[1])
    va_r = va[::-1]
    r0 = np.searchsorted(-va_r, -rng_v[1]); r1 = np.searchsorted(-va_r, -rng_v[0])
    img = img[r0:r1, c0:c1]
    im = Image.fromarray(img).resize((img.shape[1] * scale // 2 * 2 // 2 * 1, img.shape[0] * scale), Image.NEAREST) if False else Image.fromarray(img).resize((img.shape[1] * scale, img.shape[0] * scale), Image.NEAREST)
    dr = ImageDraw.Draw(im)
    pxmm = scale / H
    for g in np.arange(np.ceil(rng_h[0] / 5) * 5, rng_h[1], 5):
        x = (g - rng_h[0]) * pxmm; dr.line([(x, 0), (x, im.size[1])], fill=(150, 150, 255) if g % 10 else (90, 90, 255))
        if g % 10 == 0: dr.text((x + 2, 2), f"{g:.0f}", fill=(0, 0, 160), font=font)
    for g in np.arange(np.ceil(rng_v[0] / 5) * 5, rng_v[1], 5):
        y = (rng_v[1] - g) * pxmm; dr.line([(0, y), (im.size[0], y)], fill=(150, 150, 255) if g % 10 else (90, 90, 255))
        if g % 10 == 0: dr.text((2, y + 1), f"{g:.0f}", fill=(0, 0, 160), font=font)
    # labels at centroid of each label region
    for lb in labs:
        m = (L == lb) & S
        if m.sum() < 6: continue
        ii, jj = np.nonzero(m)
        hh = ha[int(np.median(ii))]; vv = va[int(np.median(jj))]
        if not (rng_h[0] < hh < rng_h[1] and rng_v[0] < vv < rng_v[1]): continue
        dr.text(((hh - rng_h[0]) * pxmm, (rng_v[1] - vv) * pxmm), names[lb], fill=(120, 0, 0), font=font)
    an = "xyz"
    dr.text((4, im.size[1] - 14), f"{an[axis]} = {value}  (h: {an[ah]}, v: {an[av]})", fill=(0, 0, 0), font=font)
    p = os.path.join(OUT, f"s_{an[axis]}{value:+.1f}.png"); im.save(p); return p
if __name__ == "__main__":
    for a in sys.argv[1:]:
        ax, v = a[0], float(a[1:])
        axis = "xyz".index(ax)
        if axis == 0: print(make(0, v, (-41, 41), (-85, 4)))
        elif axis == 1: print(make(1, v, (10, 53), (-85, 4)))
        else: print(make(2, v, (5, 53), (-41, 41)))
