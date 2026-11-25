"""which moving part sets the swept radius near a shoulder: for B-azimuth window [a0,a1] and z bins, max r of every moving part
(pan +-90.3, lift 0..20 for group L + B neck parts, crank posed)."""
import sys, os, json, math
sys.dont_write_bytecode = True
import numpy as np
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R1/trup_servo")
import voxlib as V
T4 = V.T4
sys.path.insert(0, T4); os.chdir(T4)
import t4_common as C
import t4_pan as MP
PJ = json.load(open(os.path.join(T4, "parts.json"))); REC = {p["name"]: p for p in PJ["parts"]}
a0, a1 = float(sys.argv[1]), float(sys.argv[2])
CRANK = ("rameno_zdvih", "cap_kluky", "skr_ramena")
P_rigid = [n for n in REC if REC[n]["group"] == "P" and n not in CRANK + ("pigtail_zdvih",)]
L_rigid = [n for n in REC if REC[n]["group"] == "L" and n not in ("pigtail_zdvih",)]
B_L = ["krk_predna_polovica", "krk_zadna_polovica", "kabel", "capy", "klzny_kruzok", "loziska_MR85", "paka", "pena_serva",
       "servo_MG90S", "usko_kryt", "usko_lozisko", "skrutky"]
def pts(tr):
    return V.vlib.sample_surface(tr, 0.4)
sets = {}
for n in P_rigid: sets[n] = (pts(V.load(n)), False)
sets["golier_kotuc"] = (pts(V.load("golier_kotuc", V.BST)), False)
for n in L_rigid: sets[n] = (pts(V.load(n)), True)
for n in B_L:
    P = pts(V.load(n, V.BST)); sets["B:" + n] = (P[P[:, 2] < 6.0], True)
for n in CRANK:
    P0 = pts(V.load(n)); Q = []
    for lf in np.arange(0.0, 20.01, 1.0):
        th = MP.crank_angle(lf); a = math.radians(-th); c, s = math.cos(a), math.sin(a)
        q = P0.copy(); y, z = P0[:, 1] - C.Y_LIFT, P0[:, 2] - C.Z_LIFT
        q[:, 1] = C.Y_LIFT + c * y - s * z; q[:, 2] = C.Z_LIFT + s * y + c * z; Q.append(q)
    sets[n] = (np.concatenate(Q), False)
Q = []
for lf in np.arange(0.0, 20.01, 2.5):
    V_, T_ = C.mesh_of(MP.fpc_lift(lf), 0.01, 0.1); Q.append(pts(V_[T_])); Q.append(pts(MP.pigtail_tris(lf)))
sets["fpc_lift+pigtail"] = (np.concatenate(Q), False)
zb = np.arange(-46.0, 4.0, 1.0)
res = {}
for nm, (P, lifted) in sets.items():
    az = np.degrees(np.arctan2(P[:, 1], P[:, 0]))
    # stage az reaching the B window: [a0-90.3, a1+90.3]
    d0 = ((az - (a0 - 90.3)) % 360.0)
    ok = d0 <= (a1 - a0 + 180.6)
    P = P[ok]
    if not len(P): continue
    r = np.hypot(P[:, 0], P[:, 1])
    for k, z in enumerate(zb):
        if lifted:
            m = (P[:, 2] <= z + 1.0) & (P[:, 2] + 20.0 >= z)
        else:
            m = (P[:, 2] >= z) & (P[:, 2] < z + 1.0)
        if m.any():
            rr = float(r[m].max())
            if rr > res.get(k, (0, ""))[0]: res[k] = (rr, nm)
for k, z in enumerate(zb):
    if k in res: print(f"z {z:6.1f}..{z+1:6.1f}  r_max {res[k][0]:6.2f}  {res[k][1]}")
