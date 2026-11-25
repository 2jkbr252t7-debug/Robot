"""K1 - one Slovak overview image: img/K1_prehlad.png
A: horizontal section z = -58 through the front-left corner, with the closest SCS0009 pose (shaft parallel to X) and its overlap
B: gear plane x 39.5..42.5 (y-z): room for gears after the column / joint / amplifier are removed, shoulder axis, max shoulder gear,
   nearest feasible-ish shaft positions and the distances a spur train would have to bridge."""
import sys, os, math, json
sys.dont_write_bytecode = True
import numpy as np
from PIL import Image, ImageDraw, ImageFont
HERE = "/tmp/claude-0/gapwf/fin/R1/K1_roh_kolesa"
FN = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"; FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
f12, f14, f16, b16, b20, b26 = (ImageFont.truetype(FN, 12), ImageFont.truetype(FN, 14), ImageFont.truetype(FN, 16),
                                ImageFont.truetype(FB, 16), ImageFont.truetype(FB, 20), ImageFont.truetype(FB, 26))
D = np.load(os.path.join(HERE, "k1_hard.npz")); K = np.load(os.path.join(HERE, "kmap.npz"))
lo, h = D["lo"], float(D["h"]); i0 = int(round((lo[0] - K["lo"][0]) / h)); cat = K["cat"][i0:]
hard, move, chg, inter = D["hard"], D["move"], D["chg"], D["interior"]
COL = dict(out=(235, 235, 235), wall=(60, 90, 190), hard=(150, 150, 150), move=(235, 125, 125), chg=(250, 215, 120), free=(255, 255, 255))


def classify(sl_hard, sl_move, sl_chg, sl_int, sl_cat):
    img = np.zeros(sl_hard.shape + (3,), np.uint8); img[:] = COL["free"]
    img[sl_chg] = COL["chg"]; img[sl_hard] = COL["hard"]; img[sl_hard & (sl_cat == 3)] = COL["wall"]
    img[sl_move] = COL["move"]; img[~sl_int] = COL["out"]
    return img


W, H = 1900, 1300
im = Image.new("RGB", (W, H), (250, 250, 250)); d = ImageDraw.Draw(im)
d.text((30, 18), "K1 – servo v rohu trupu + čelné ozubené kolesá: NEDÁ SA (ľavá strana; pravá zrkadlovo tiež nie)", fill=(20, 20, 20), font=b26)
d.text((30, 56), "Zmerané na trupe T4 (mriežka 0,5 mm). Stĺp, kĺb ramena, zosilňovač a vnútro bočného krytu som pre K1 úplne odstránil; "
       "vôľa 0,3 mm k pevným dielom, 1,0 mm k otáčaniu/zdvihu krku.", fill=(60, 60, 60), font=f16)


def panel(img, ox, oy, S, x0, y0, title, xl, yl, step=10):
    Hh, Ww = img.shape[1], img.shape[0]
    pim = Image.fromarray(img.transpose(1, 0, 2)[::-1]).resize((Ww * S, Hh * S), Image.NEAREST)
    im.paste(pim, (ox, oy))
    d.rectangle([ox, oy, ox + Ww * S, oy + Hh * S], outline=(80, 80, 80))
    for v in np.arange(math.ceil(x0 / step) * step, x0 + Ww * h + 1e-6, step):
        px = ox + (v - x0) / h * S
        d.line([(px, oy), (px, oy + Hh * S)], fill=(205, 205, 225)); d.text((px - 8, oy + Hh * S + 3), f"{v:.0f}", fill=(70, 70, 110), font=f12)
    for v in np.arange(math.ceil(y0 / step) * step, y0 + Hh * h + 1e-6, step):
        py = oy + Hh * S - (v - y0) / h * S
        d.line([(ox, py), (ox + Ww * S, py)], fill=(205, 205, 225)); d.text((ox - 32, py - 7), f"{v:.0f}", fill=(70, 70, 110), font=f12)
    d.text((ox, oy - 26), title, fill=(20, 20, 20), font=b16)
    d.text((ox + Ww * S - 70, oy + Hh * S + 18), f"{xl} [mm]", fill=(70, 70, 110), font=f12)
    d.text((ox - 36, oy - 8), f"{yl}", fill=(70, 70, 110), font=f12)

    def P(a, b):
        return ox + (a - x0) / h * S, oy + Hh * S - (b - y0) / h * S
    return P


# ---- panel A: z = -58, x 0..52, y -40..12
z = -58.0; k = int((z - lo[2]) / h)
ia, ib = int((0 - lo[0]) / h), int((52 - lo[0]) / h); ja, jb = int((-40 - lo[1]) / h), int((12 - lo[1]) / h)
img = classify(hard[ia:ib, ja:jb, k], move[ia:ib, ja:jb, k], chg[ia:ib, ja:jb, k], inter[ia:ib, ja:jb, k], cat[ia:ib, ja:jb, k])
SA = 8
PA = panel(img, 70, 130, SA, 0.0, -40.0, "A: vodorovný rez z = −58 (predný ľavý roh, pohľad zhora)", "x", "y")
# closest SCS0009 pose in the corner (k1_opt): case outline in this plane
sys.argv = ["k1_opt.py", "scs", ""]
src = open(os.path.join(HERE, "k1_opt.py")).read(); src = src[:src.index("t0 = time.time()")]
ns = {}; exec(src, ns)
x = np.array([39.42, -21.16, -58.23, math.radians(279.1), 1.0])
Q = ns["world"](x); m = ns["margin"](x)
sel = np.abs(Q[:, 2] - z) < 0.35
for q, mm in zip(Q[sel], m[sel]):
    a, b = PA(q[0], q[1]); d.ellipse([a - 1.5, b - 1.5, a + 1.5, b + 1.5], fill=(0, 140, 0))
for q, mm in zip(Q[m < 0], m[m < 0]):      # every colliding point, projected from any height
    a, b = PA(q[0], q[1]); d.ellipse([a - 2.5, b - 2.5, a + 2.5, b + 2.5], fill=(210, 0, 0))
a, b = PA(14.0, -31.5); d.text((a, b), "SCS0009 (23,2 × 12,1 × 21,5), hriadeľ ‖ X", fill=(150, 0, 0), font=b16)
a, b = PA(1.0, -9.0); d.text((a, b), "servo J1", fill=(40, 40, 40), font=f14)
a, b = PA(1.0, -24.0); d.text((a, b), "servo otáčania", fill=(40, 40, 40), font=f14)
a, b = PA(1.0, -26.5); d.text((a, b), "hlavy (STS3032)", fill=(40, 40, 40), font=f14)
a, b = PA(38.0, 2.0); d.text((a, b), "stĺp (zmenený)", fill=(120, 90, 0), font=f14)
tA = ["Najlepšia poloha v rohu: chýba 2,1 mm", "(narazí na servo hlavy, kolísku J1, čelnú stenu", "a bočný kryt) – a aj tak by bol hriadeľ",
      "47,8 mm od osi ramena.", "Najlepšia poloha v celom trupe: chýba 1,6 mm", "(dole pri servo J1, 45,7–56 mm od osi)."]
for i, t in enumerate(tA):
    d.text((70, 130 + 104 * SA + 34 + i * 21), t, fill=(150, 0, 0) if i in (0, 4) else (30, 30, 30), font=b16 if i in (0, 4) else f16)

# ---- panel B: gear plane x 39.5..42.5, y -30..26, z -82..2
fd = np.load(os.path.join(HERE, "plane_39.5_42.5.npy"))
ja, jb = int((-30 - lo[1]) / h), int((26 - lo[1]) / h); ka, kb = int((-82 - lo[2]) / h), int((2 - lo[2]) / h)
ok = fd[ja:jb, ka:kb] > 0
img = np.zeros(ok.shape + (3,), np.uint8); img[:] = COL["hard"]; img[ok] = COL["free"]
SB = 5
PB = panel(img, 1000, 130, SB, -30.0, -82.0, "B: rovina kolies x 39,5…42,5 (pohľad zboku, y doprava, z hore)", "y", "z")
cy, cz = PB(3.0, -17.0)
for r, c, w in ((10.6, (200, 0, 0), 2), (0.6, (200, 0, 0), 3)):
    d.ellipse([cy - r / h * SB, cz - r / h * SB, cy + r / h * SB, cz + r / h * SB], outline=c, width=w)
d.text((cy + 75, cz - 95), "os ramena; najväčšie koleso", fill=(150, 0, 0), font=b16)
d.text((cy + 75, cz - 75), "na osi: hlavová kružnica r 10,6", fill=(150, 0, 0), font=f16)
for (yy, zz, lab) in ((-21.2, -58.2, "hriadeľ v rohu\n47,8 mm"), (-7.4, -61.5, "hriadeľ dole\n45,7 mm")):
    a, b = PB(yy, zz); d.ellipse([a - 6, b - 6, a + 6, b + 6], outline=(0, 0, 160), width=3)
    d.line([(a, b), (cy, cz)], fill=(0, 0, 160), width=2)
    for i, t in enumerate(lab.split("\n")):
        d.text((a - 60, b + 10 + i * 18), t, fill=(0, 0, 160), font=b16)
tB = ["Čelné kolesá by museli preklenúť 40–56 mm:", "pastorok + medzikoleso Ø 30–40 mm + koleso na osi,",
      "alebo 4 kolesá. To je presne ten hlučný mechanizmus,", "ktorý nechceš – a servo sa tam aj tak nezmestí."]
for i, t in enumerate(tB):
    d.text((1000, 130 + 168 * SB + 34 + i * 21), t, fill=(30, 30, 30), font=f16)
# legend
lx, ly = 70, H - 70
for i, (k_, t) in enumerate((("wall", "stena trupu (zostáva)"), ("hard", "pevné diely, ktoré zostávajú"), ("move", "otáčanie + zdvih krku (+1 mm)"),
                             ("chg", "diely, ktoré by sa smeli zmeniť"), ("free", "voľné miesto"))):
    d.rectangle([lx + i * 330, ly, lx + i * 330 + 22, ly + 16], fill=COL[k_], outline=(80, 80, 80))
    d.text((lx + i * 330 + 30, ly - 1), t, fill=(30, 30, 30), font=f14)
d.text((70, H - 40), "Červené body = miesta serva, ktoré narazia (v hociktorej výške, premietnuté); zelené = prierez serva v rovine rezu.  Skripty: k1_hard.py, k1_fit.py, k1_opt.py, k1_plane.py, k1_train.py",
       fill=(90, 90, 90), font=f12)
im.save(os.path.join(HERE, "img", "K1_prehlad.png"))
print("saved")
