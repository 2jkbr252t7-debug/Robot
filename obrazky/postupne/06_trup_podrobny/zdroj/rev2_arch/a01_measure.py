"""rev2 architect - measurements on the real rev.1 STLs + exterior functions (read only)."""
import sys, json, math
import numpy as np
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T4"); sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T4/zjednodusenie")
import t4_common as C
from zj_lib import read_stl, sample
out = {}
# --- A. shell inner half depth / width (true offset 2.2) at stage-relevant z
rows = []
for z in (1.75, 0, -2, -3, -4.5, -6, -8, -10.5, -11.5, -12, -13.5, -15, -18, -20, -22, -24, -28, -30, -34, -38, -41.9, -46, -55, -60, -65, -70, -72, -75, -78, -80, -81):
    ai, bi = C.inner_half(z)
    rows.append((z, round(ai, 3), round(bi, 3)))
out["inner_half"] = rows
# --- B. T_stred bore / tube from the STL
T = read_stl("T_stred"); P = sample(T, 0.4)
r = np.hypot(P[:, 0], P[:, 1])
bore = []
for z0 in np.arange(-11.0, 4.0, 0.5):
    m = (P[:, 2] >= z0) & (P[:, 2] < z0 + 0.5) & (r < 33)
    if m.sum():
        bore.append((round(float(z0), 2), round(float(r[m].min()), 3), round(float(np.percentile(r[m], 50)), 3)))
out["T_stred_bore_rmin_by_z"] = bore
# tube outer: radius of T_stred material in r 28.3..33 at azimuths 0,90,180,270 for z -10..-3
tube = {}
for az in (0, 45, 90, 135, 180, 225, 270, 315):
    a = math.radians(az); d = np.abs(np.arctan2(np.sin(np.arctan2(P[:,1],P[:,0]) - a), np.cos(np.arctan2(P[:,1],P[:,0]) - a)))
    m = (d < 0.03) & (P[:, 2] > -10.4) & (P[:, 2] < -3.0) & (r > 28.2) & (r < 34.0)
    tube[az] = [round(float(r[m].min()), 2), round(float(r[m].max()), 2)] if m.sum() else None
out["T_stred_tube_r_by_az(z-10.4..-3)"] = tube
# door opening: free box check in the back wall
m = (P[:, 1] > 20) & (np.abs(P[:, 0]) < 28.0) & (P[:, 2] > -72.0) & (P[:, 2] < -12.0)
inside = P[m]
# points inside the opening outline (rounded rect 56.5 x 60.5 r 10.25)
def in_door(x, z, grow=0.25):
    w, h, rr = 28.0 + grow, 30.0 + grow, 10.0 + grow
    dx, dz = np.abs(x) - (w - rr), np.abs(z + 42.0) - (h - rr)
    return np.where((dx > 0) & (dz > 0), np.hypot(dx, dz) <= rr, (np.abs(x) <= w) & (np.abs(z + 42.0) <= h))
q = inside[in_door(inside[:, 0], inside[:, 2], 0.0)]
out["T_stred_points_inside_door_outline(y>20)"] = int(len(q))
out["T_stred_door_ledge_y_range"] = [round(float(q[:, 1].min()), 2), round(float(q[:, 1].max()), 2)] if len(q) else None
# --- C. white lip outline (z -81) half depth at x
L = C.lip_outline()
lip = []
for x in (0, 5, 10, 14, 16.25, 18, 20, 22, 24, 25, 26, 28, 30, 33):
    sel = np.abs(L[:, 0] - x) < 0.6
    lip.append((x, round(float(np.abs(L[sel, 1]).min()), 2)))
out["lip_half_depth_at_x(z-81)"] = lip
tub = []
for x in (0, 10, 20, 25, 30, 34, 36, 38):
    th = np.linspace(0, 2*np.pi, 3600); rr = C.se_r(*C.TUB_SE, th); X, Y = rr*np.cos(th), rr*np.sin(th)
    sel = np.abs(X - x) < 0.3
    tub.append((x, round(float(np.abs(Y[sel]).min()), 2)))
out["tub_half_depth_at_x"] = tub
# --- D. B parts: collar ring / disc / neck
for nm in ("golier_prstenec", "golier_kotuc", "krk_predna_polovica", "krk_zadna_polovica"):
    Tb = read_stl("/tmp/claude-0/gapwf/fin/B/stl/" + nm + ".stl"); V = Tb.reshape(-1, 3)
    out[nm + "_bbox"] = [round(float(v), 3) for v in (*V.min(0), *V.max(0))]
Tb = read_stl("/tmp/claude-0/gapwf/fin/B/stl/golier_kotuc.stl"); Q = sample(Tb, 0.3)
m = (np.abs(Q[:, 1]) < 2.0); out["kotuc_slot_half_x"] = round(float(np.abs(Q[m, 0]).min()), 3)
m = (np.abs(Q[:, 0]) < 2.0); out["kotuc_slot_half_y"] = round(float(np.abs(Q[m, 1]).min()), 3)
# neck: section near the bottom, x / y extents and the wire exits (holes in the bottom face)
for nm in ("krk_predna_polovica", "krk_zadna_polovica"):
    Tb = read_stl("/tmp/claude-0/gapwf/fin/B/stl/" + nm + ".stl"); Q = sample(Tb, 0.3)
    m = Q[:, 2] < -36.0
    out[nm + "_bottom_face_xy_bbox"] = [round(float(v), 2) for v in (Q[m, 0].min(), Q[m, 0].max(), Q[m, 1].min(), Q[m, 1].max())]
# --- E. foot / stage for the neck board: L_pata current bbox, end window
for nm in ("L_pata", "P_sachta", "P_drziak_serva", "servo_zdvih", "L_ucho", "P_kluka", "DPS_riadenie", "T_ram", "T_paluba", "T_spodok", "servo_J1", "servo_pan", "pastorok_pan", "P_koleso", "menic", "zosilnovac", "kondenzator", "T_dvere"):
    V = read_stl(nm).reshape(-1, 3)
    out[nm + "_bbox"] = [round(float(v), 2) for v in (*V.min(0), *V.max(0))]
json.dump(out, open("a01_measure.json", "w"), indent=1)
for k, v in out.items():
    print(k, v)
