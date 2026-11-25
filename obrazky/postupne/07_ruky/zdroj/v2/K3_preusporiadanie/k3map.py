"""K3 obstacle map (both sides) from the R1 voxel map (map1.npz, 0.5 mm) + K1 category map (kmap.npz: shell wall / features).
HARD  = what K3 keeps: shell walls (inset <= WALL+0.25) of T_stred / T_bok / T_dvere, T_stred + T_dvere inner features,
        T_bok inner features within 3.0 of the seam (x |x| < 36.5), all bought / fixed parts not listed as removable,
        the T_spodok floor, spigot, cradle, posts (except the columns), the outside of the shell.
CHG   = removable / redesignable for K3: T_spodok columns (|x| >= 26 left, x <= -32.4 right, above the floor, inside the tub,
        except the two stop-pin posts), T_klb_L/P + screws / washers / magnets, F8 inserts, amplifier + buck + F14,
        F3a deck screws at the columns, T_bok inner features at |x| >= 36.5.
MOVE  = map1 'moving' (pan -90.3..+90.3, lift 0..20, crank, FFC loops; analytic duct).
Writes k3map.npz: lo, h, n, hard, chg, move, interior, ds (EDT to hard), dm (EDT to move), lab."""
import sys, os, time
sys.dont_write_bytecode = True
import numpy as np
from scipy import ndimage as ndi
HERE = os.path.dirname(os.path.abspath(__file__))
t0 = time.time()
M = np.load("/tmp/claude-0/gapwf/fin/R1/trup_servo/map1.npz")
K = np.load("/tmp/claude-0/gapwf/fin/R1/K1_roh_kolesa/kmap.npz")
lo, h, n = M["lo"], float(M["h"]), tuple(int(v) for v in M["n"])
lab, ln = M["label"], [str(s) for s in M["lab_names"]]
cat = K["cat"]
idx = {nm: i for i, nm in enumerate(ln)}
X, Y, Z = np.meshgrid(lo[0] + (np.arange(n[0]) + .5) * h, lo[1] + (np.arange(n[1]) + .5) * h, lo[2] + (np.arange(n[2]) + .5) * h,
                      indexing="ij")
def lid(names):
    return np.isin(lab, [idx[x] for x in names if x in idx])
rem_names = ["T_klb_L", "T_klb_P", "zosilnovac", "menic"] + [x for x in ln if x.startswith(
    ("magnet_klb", "podlozka_klb", "skrutka_klb", "vl_F8", "skr_F14", "pd_F14"))]
chg = lid(rem_names)
sp = lid(["T_spodok"])
pin_posts = ((np.hypot(X - 27.09, Y - 12.89) <= 4.0) | (np.hypot(X + 21.37, Y + 21.06) <= 4.0)) & (Z >= -62.0)
tub = (np.abs(X) / 39.55) ** 2.66 + (np.abs(Y) / 25.49) ** 2.66 < 1.0
col = sp & (Z >= -82.3) & ((Z >= -78.0) | tub) & ((X >= 26.0) | (X <= -32.4)) & ~pin_posts
chg |= col
# deck screws F3a sitting in the column zone
for nm in [x for x in ln if x.startswith(("skr_F3a", "pd_F3a", "vl_F3a"))]:
    m = lab == idx[nm]
    if m.any() and np.abs(X[m]).mean() > 26.0:
        chg |= m; print("removable deck screw part", nm, round(float(X[m].mean()), 1), round(float(Y[m].mean()), 1))
deck_trim = lid(["T_paluba"]) & (np.abs(X) >= 31.0)
chg |= deck_trim; print("deck voxels trimmed", deck_trim.sum())
bok_feat = (cat == 9) & lid(["T_bok_L", "T_bok_P"]) & (np.abs(X) >= 36.5)
chg |= bok_feat
interior = M["interior"]
static_all = (lab > 0) | (cat == 3) | (cat == 9)
hard = (static_all & ~chg) | ~interior
move = M["moving"] & ~hard
print("hard", hard.sum(), "chg", chg.sum(), "move", move.sum(), f"{time.time()-t0:.0f}s")
ds = ndi.distance_transform_edt(~hard, sampling=h).astype(np.float32)
dm = ndi.distance_transform_edt(~M["moving"], sampling=h).astype(np.float32)
np.savez_compressed(os.path.join(HERE, "k3map.npz"), lo=lo, h=h, n=np.array(n), hard=hard, chg=chg, move=move, interior=interior,
                    ds=ds, dm=dm, lab=lab, lab_names=np.array(ln), cat=cat)
print("saved", f"{time.time()-t0:.0f}s")
