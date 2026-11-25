"""K1 category map: re-labels the R1 voxel map (map1.npz, 0.5 mm) into FIXED / CHANGEABLE categories for the K1 study
and computes the shell inset of every T_stred / T_bok / T_dvere voxel (wall vs internal feature).
Writes kmap.npz.  Nothing outside this directory is written."""
import sys, os, time
sys.dont_write_bytecode = True
import numpy as np
from scipy import ndimage as ndi
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T4"); sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T4/overenie3")
os.chdir("/tmp/claude-0/gapwf/fin/T4")
import t4_common as C
HERE = "/tmp/claude-0/gapwf/fin/R1/K1_roh_kolesa"
t0 = time.time()
D = np.load("/tmp/claude-0/gapwf/fin/R1/trup_servo/map1.npz")
lo, h, n = D["lo"], float(D["h"]), tuple(int(v) for v in D["n"])
lab, ln = D["label"], [str(s) for s in D["lab_names"]]
interior, moving, static = D["interior"], D["moving"], D["static"]
idx = {nm: i for i, nm in enumerate(ln)}
SHELL = ["T_stred", "T_bok_L", "T_bok_P", "T_dvere"]
CHANGE = ["T_spodok", "T_paluba", "T_klb_L", "T_klb_P", "DPS_riadenie", "usb_predlzovac", "menic", "zosilnovac", "kondenzator",
          "pena_J1_celo", "podlozka_C_J1"] + [x for x in ln if x.startswith(("skr_F3a", "pd_F3a", "vl_F3a", "skr_F3b", "vl_F3b", "skr_F7",
          "vl_F7", "vl_F8", "skr_F14", "pd_F14", "skrutka_klb", "podlozka_klb", "ffc_A_nosic", "ffc_B_nosic"))]
PANS = ["servo_pan", "pastorok_pan", "skr_F4_1", "skr_F4_2", "mat_F4_1", "mat_F4_2"]
def lid(names):
    return np.isin(lab, [idx[x] for x in names if x in idx])
shell = lid(SHELL)
# inset of shell voxels: distance to the outer surface (exact cloud)
I = np.argwhere(shell)
P = lo + (I + 0.5) * h
d = C.dist_outer(P)
inset = np.zeros(n, np.float32); inset[shell] = d
wall = shell & (inset <= C.WALL + 0.25)
feat = shell & ~wall
chg = lid(CHANGE); pan = lid(PANS)
fixed = static & ~shell & ~chg & ~pan
cat = np.zeros(n, np.uint8)
cat[interior] = 1
cat[fixed] = 4; cat[wall] = 3; cat[feat] = 9; cat[chg] = 5; cat[pan] = 6; cat[moving & (cat <= 1)] = 2
print("cats", np.bincount(cat.ravel()), f"{time.time()-t0:.0f}s")
np.savez_compressed(os.path.join(HERE, "kmap.npz"), lo=lo, h=h, n=np.array(n), cat=cat, inset=inset)
print("saved")
