"""measurements on P_sachta + gear: floor / hub-disc thickness map (vertical rays), bond area with the gear top face,
wall thickness per level (distance transform of slices), F15 engagement, washer overlap"""
import json, math, numpy as np
from scipy import ndimage as ndi
import sa_lib as L
S = L.part("P_sachta"); G = L.part("koleso_pan")
res = {}
h = 0.05
xs = np.arange(-26.6, 26.6, h); ys = np.arange(-26.6, 26.6, h)
crS = L.column_crossings(S, xs, ys); crG = L.column_crossings(G, xs, ys)
nx, ny = len(xs), len(ys)
floor_t = np.full((nx, ny), np.nan); floor_bot = np.full((nx, ny), np.nan); floor_top = np.full((nx, ny), np.nan)
lowest = np.full((nx, ny), np.nan)
gear = np.zeros((nx, ny), bool)
for (i, j), w in crG.items():
    for a, b in L.intervals(w):
        if a < -41.85 and b > -41.95:
            gear[i, j] = True
bond = np.zeros((nx, ny), bool)
for (i, j), w in crS.items():
    iv = L.intervals(w)
    if not iv:
        continue
    lowest[i, j] = iv[0][0]
    for a, b in iv:
        if a <= -41.85 and b >= -41.85:          # solid just above the gear top plane
            bond[i, j] = gear[i, j] or bond[i, j]
        if a < -40.6 and a > -42.0:              # an interval that starts at the floor level (hub disc / back floor / wall foot)
            floor_bot[i, j] = a; floor_top[i, j] = b; floor_t[i, j] = b - a
            break
A = h * h
res["bond_area_mm2"] = float(bond.sum() * A)
res["gear_top_face_area_mm2"] = float(gear.sum() * A)
X, Y = np.meshgrid(xs, ys, indexing="ij"); R = np.hypot(X, Y)
res["bond_area_hub_ring_r6.5_12.6"] = float((bond & (R <= 12.62)).sum() * A)
res["bond_area_outside_r12.6"] = float((bond & (R > 12.62)).sum() * A)
# polar moment of the bond about the axis (for torque) and centroid
res["bond_sum_r_dA"] = float((R[bond]).sum() * A)
res["bond_sum_r2_dA"] = float((R[bond] ** 2).sum() * A)
res["bond_centroid"] = [float(X[bond].mean()), float(Y[bond].mean())]
# floor thickness classes: pure floor (top <= -40.0) vs where walls rise (top > -39)
pure = floor_top <= -40.0
res["floor_thickness_values"] = sorted(set(np.round(floor_t[pure & ~np.isnan(floor_t)], 2).tolist()))[:20]
np.savez_compressed("g02_maps.npz", xs=xs, ys=ys, floor_t=floor_t, floor_bot=floor_bot, floor_top=floor_top, bond=bond, gear=gear, lowest=lowest)
# where is the floor thinnest (pure floor zone)
ft = np.where(pure, floor_t, np.nan)
for thr in (0.6, 0.8, 0.95, 1.0, 1.2, 1.25):
    res[f"floor_area_t_le_{thr}"] = float((ft <= thr + 1e-6).sum() * A)
mn = np.nanmin(ft); ii = np.argwhere(np.abs(ft - mn) < 1e-6)
res["floor_t_min"] = float(mn); res["floor_t_min_at_sample"] = [[float(xs[i]), float(ys[j])] for i, j in ii[:: max(1, len(ii) // 6)]]
# F15 / washer / T_cap
F = L.part("skr_F15"); Tm = L.part("T_most"); W = L.part("pd_F15"); Tc = L.part("T_cap")
res["F15_tip_z"] = float(F[:, :, 2].min()); res["T_most_z"] = [float(Tm[:, :, 2].min()), float(Tm[:, :, 2].max())]
res["F15_engagement_in_T_most"] = float(Tm[:, :, 2].max() - F[:, :, 2].min())
res["washer_z"] = [float(W[:, :, 2].min()), float(W[:, :, 2].max())]
res["washer_r_out"] = float(np.hypot(W[:, :, 0], W[:, :, 1]).max())
# gear bore radius from the mesh at z -43.9
segs = L.slice_segments(G, 2, -43.9); rr = np.hypot(segs[:, :, 0], segs[:, :, 1])
res["gear_bore_r"] = float(rr.min()); res["gear_tip_r"] = float(rr.max())
res["washer_overlap_on_gear_nominal"] = res["washer_r_out"] - res["gear_bore_r"]
segs = L.slice_segments(Tc, 2, -44.0); rr = np.hypot(segs[:, :, 0], segs[:, :, 1])
res["T_cap_r_at_z-44"] = [float(rr.min()), float(rr.max())]
for z in (-46.15, -46.0, -45.8, -45.6):
    segs = L.slice_segments(Tc, 2, z); rr = np.hypot(segs[:, :, 0], segs[:, :, 1]); res[f"T_cap_r_at_z{z}"] = [float(rr.min()), float(rr.max())]
print(json.dumps(res, indent=1))
json.dump(res, open("g02_measure.json", "w"), indent=1)
