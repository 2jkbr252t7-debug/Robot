"""K1 - obstacle model for a new arm drive in the LEFT half of the T4 torso (x >= -2).
Re-labels the R1 voxel map (map1.npz, 0.5 mm) into
  HARD  : must stay where it is (shell wall inset <= 2.45, kept shell features, fixed bought parts, kept T_spodok,
          pan servo group, deck, carrier, capacitor, USB, outside of the shell)
  MOVE  : swept pan stage + lift module + neck (map1 'moving')
  CHG   : may be removed / redesigned for the arm drive (column x >= 31.5 above z -78, T_klb_L + its screws / inserts,
          T_bok_L socket tube + seat flange (r <= 18.5 about the shoulder axis, x >= 37), amplifier + F14, F3a_2)
Writes k1_hard.npz (lo, h, n, hard, move, chg, lower, ds = distance to HARD, dm = distance to MOVE) for x >= -2."""
import sys, os, time
sys.dont_write_bytecode = True
import numpy as np
from scipy import ndimage as ndi
HERE = "/tmp/claude-0/gapwf/fin/R1/K1_roh_kolesa"
t0 = time.time()
M = np.load("/tmp/claude-0/gapwf/fin/R1/trup_servo/map1.npz")
K = np.load(os.path.join(HERE, "kmap.npz"))
lo, h = M["lo"], float(M["h"])
lab, ln = M["label"], [str(s) for s in M["lab_names"]]
idx = {nm: i for i, nm in enumerate(ln)}
cat = K["cat"]
RIGHT = "R" in (sys.argv[1] if len(sys.argv) > 1 else "")
i0 = int(round((-2.0 - lo[0]) / h))
if RIGHT:   # mirror the right half (x <= 2) onto x >= -2: index i -> N-1-i (grid symmetric: lo -53, 212 cells)
    flip = lambda A: A[::-1]
    lab = flip(lab); cat = flip(cat)
    interior = flip(M["interior"]); moving = flip(M["moving"]); lower = flip(M["lower"])
    sl = (slice(i0, None), slice(None), slice(None))
    lab = lab[sl]; cat = cat[sl]; interior = interior[sl]; moving = moving[sl]; lower = lower[sl]
    for a, b in (("T_klb_P", "T_klb_L"), ("menic", "zosilnovac"), ("skr_F14_1", "skr_F14_3"), ("skr_F14_2", "skr_F14_4"),
                 ("pd_F14_1", "pd_F14_3"), ("pd_F14_2", "pd_F14_4"), ("T_bok_P", "T_bok_L")) + tuple(
                 (f"{p}_P{k}", f"{p}_L{k}") for p in ("vl_F8", "skrutka_klb", "podlozka_klb") for k in (1, 2, 3)):
        idx[b + "_orig"] = idx.get(b); idx[b] = idx[a]
else:
    sl = (slice(i0, None), slice(None), slice(None))
    lab = lab[sl]; cat = cat[sl]
    interior = M["interior"][sl]; moving = M["moving"][sl]; lower = M["lower"][sl]
n = lab.shape
lo2 = lo + np.array([i0 * h, 0, 0])
X, Y, Z = np.meshgrid(lo2[0] + (np.arange(n[0]) + .5) * h, lo2[1] + (np.arange(n[1]) + .5) * h, lo2[2] + (np.arange(n[2]) + .5) * h,
                      indexing="ij")
r_ax = np.hypot(Y - 3.0, Z + 17.0)


def lid(names):
    return np.isin(lab, [idx[x] for x in names if x in idx])


chg = np.zeros(n, bool)
# column of T_spodok (web, ribs, foot, head, shoulder plate, box closure, boss, stop ring) - everything at x >= 31.5 above z -78
sp = lid(["T_spodok"])
chg |= sp & (X >= 31.5) & (Z > -78.0)
chg |= lid(["T_klb_L", "zosilnovac", "skr_F14_3", "skr_F14_4", "pd_F14_3", "pd_F14_4", "vl_F8_L1", "vl_F8_L2", "vl_F8_L3",
            "skrutka_klb_L1", "skrutka_klb_L2", "skrutka_klb_L3", "podlozka_klb_L1", "podlozka_klb_L2", "podlozka_klb_L3",
            "skr_F3a_2", "pd_F3a_2", "vl_F3a_2"])
# T_bok_L inner features around the shoulder (socket tube, seat flange): shell-feature voxels (cat 9) near the axis
bokL = lid(["T_bok_L"])
chg |= bokL & (cat == 9) & (r_ax <= 18.5) & (X >= 37.0)
VAR = sys.argv[1] if len(sys.argv) > 1 else ""
if "p" in VAR:      # pan servo group + its two posts (T_spodok x 11..18, y -25..-17, z > -78)
    chg |= lid(["servo_pan", "pastorok_pan", "skr_F4_1", "skr_F4_2", "mat_F4_1", "mat_F4_2"])
    chg |= sp & (X > 10.5) & (X < 18.5) & (Y < -16.5) & (Y > -25.5) & (Z > -78.0)
if "c" in VAR:      # carrier board, USB extension, capacitor, carrier FFC tails, F7
    chg |= lid(["DPS_riadenie", "usb_predlzovac", "kondenzator", "ffc_A_nosic", "ffc_B_nosic", "skr_F7_1", "skr_F7_2", "vl_F7_1", "vl_F7_2"])
if "d" in VAR:      # deck T_paluba outside r 27 and the F3a_1 boss
    chg |= lid(["T_paluba"]) & (np.hypot(X, Y) > 27.0)
    chg |= lid(["skr_F3a_1", "pd_F3a_1", "vl_F3a_1"]) | (sp & (np.hypot(X - 26.0, Y + 11.7) < 4.0) & (Z > -53.0))
static_all = (lab > 0) | (cat == 3) | (cat == 9)
hard = (static_all & ~chg) | ~interior
move = moving & ~hard
print("voxels hard", hard.sum(), "move", move.sum(), "chg", chg.sum(), f"{time.time()-t0:.0f}s")
ds = ndi.distance_transform_edt(~hard, sampling=h).astype(np.float32)
dm = ndi.distance_transform_edt(~move, sampling=h).astype(np.float32)
np.savez_compressed(os.path.join(HERE, f"k1_hard{VAR}.npz"), lo=lo2, h=h, n=np.array(n), hard=hard, move=move, chg=chg, lower=lower,
                    ds=ds, dm=dm, interior=interior)
print("saved", f"{time.time()-t0:.0f}s")
