"""K2: 'hard' free-space map = R1 voxel map with the parts that this concept may move / reshape removed.
soft (removable): T_spodok columns / cradle-wall ends at |x| >= 26 above z -78 (except stop-pin posts), T_klb_L/P + their
screws / magnets / washers, F8 inserts, amplifier, buck converter, capacitor, USB extension, F14 screws, F3a_2 (deck screw
at (30.6, 4)), F1 inserts / screws / washers (boss may be relocated - flagged separately).
writes hard.npz (free_h = interior & ds_hard >= 0.55 & dm >= 1.25)"""
import numpy as np, time
from scipy import ndimage as ndi
t0 = time.time()
D = np.load("/tmp/claude-0/gapwf/fin/R1/trup_servo/map1.npz")
lo, H = D["lo"], float(D["h"]); n = tuple(D["n"])
label, static, interior, dm = D["label"], D["static"], D["interior"], D["dm"]
names = [str(s) for s in D["lab_names"]]
soft_names = {"T_klb_L", "T_klb_P", "zosilnovac", "menic", "kondenzator", "usb_predlzovac"}
soft_names |= {s for s in names if s.startswith(("magnet_klb", "podlozka_klb", "skrutka_klb", "vl_F8", "skr_F14", "pd_F14",
                                                 "skr_F3a_2", "pd_F3a_2", "vl_F3a_2", "vlozka_stred", "skr_F1", "pd_F1"))}
soft_lab = np.array([nm in soft_names for nm in names])
hard = static & ~soft_lab[label]
X = lo[0] + (np.arange(n[0]) + 0.5) * H; Y = lo[1] + (np.arange(n[1]) + 0.5) * H; Z = lo[2] + (np.arange(n[2]) + 0.5) * H
XX, YY, ZZ = np.meshgrid(X, Y, Z, indexing="ij")
sp = label == names.index("T_spodok")
pin_posts = (np.hypot(XX - 27.09, YY - 12.89) <= 4.0) | (np.hypot(XX + 21.37, YY + 21.06) <= 4.0)
tub = (np.abs(XX) / 39.55) ** 2.66 + (np.abs(YY) / 25.49) ** 2.66 < 1.0
pin_posts &= ZZ >= -62.0
soft_sp = sp & (ZZ >= -82.3) & ((ZZ >= -78.0) | tub) & ((XX >= 26.0) | (XX <= -32.4)) & ~pin_posts
hard &= ~soft_sp
ds_h = ndi.distance_transform_edt(~hard, sampling=H).astype(np.float32)
free_h = interior & ~hard & (ds_h >= 0.55) & (dm >= 1.25)
np.savez_compressed("/tmp/claude-0/gapwf/fin/R1/K2_dole_remen/hard.npz", free_h=free_h, ds_h=ds_h, hard=hard, soft_sp=soft_sp)
print("free_h cm3", free_h.sum() * H ** 3 / 1000, "  t", round(time.time() - t0))
