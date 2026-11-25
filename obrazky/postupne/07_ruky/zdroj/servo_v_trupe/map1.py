"""STEP 1 - free-space voxel map inside the T4 torso (0.5 mm).  Writes map1.npz + map1.json in this directory.
static  = every group-T part of T4 + B golier_prstenec + the static FFC run (t4_pan.ffc_static)
moving  = pan stage + lift module (group P, + B collar disc, + FFC riser) swept about Z over pan -90.3..+90.3 (continuous,
          0.5 deg bins), lift group L + B neck / cable / tilt parts lifted 0..20 and swept the same way, crank posed at
          lift 0..20 (0.5 steps), FFC lift loop + lift-servo pigtail posed at lift 0..20 (1.25 steps, as K3 uses 2.5),
          pan FFC rolling-loop duct reserved analytically (r 15.2..25.1, z -46.2..-41.9, all azimuths)
assembly sweeps (cumulative along the withdrawal direction of t4_assembly.py):
          T5 T_stred + front stack + F1 inserts + frame magnets (+z), S1/T9 lift module at pan 0 (+y),
          T13 side caps (+x / -x), T13b shoulder joints (+x / -x), T4c/T4d buck / amp (-x / +x)
"""
import sys, os, json, time, math
sys.dont_write_bytecode = True
import numpy as np
from scipy import ndimage as ndi
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import voxlib as V  # noqa: E402
T4 = V.T4
sys.path.insert(0, T4)
os.chdir(T4)
import t4_common as C  # noqa: E402
import t4_assembly as A  # noqa: E402

t00 = time.time()
H = 0.5
g = V.Grid((-53.0, -41.0, -85.0), (53.0, 41.0, 4.5), H)
print("grid", g.n, np.prod(g.n))
PJ = json.load(open(os.path.join(T4, "parts.json")))
REC = {p["name"]: p for p in PJ["parts"]}
grp = {n: r["group"] for n, r in REC.items()}

# ---------------------------------------------------------------- interior of the outer surface
Pc = g.centres()
interior = C.inside_outer(Pc).reshape(g.n)
del Pc
print("interior voxels", interior.sum(), f"{time.time()-t00:.0f}s")

# ---------------------------------------------------------------- static
names_static = [n for n in REC if grp[n] == "T"]
label = np.zeros(g.n, np.int16)
lab_names = ["-"]
static = np.zeros(g.n, bool)
TR = {}
for n in names_static:
    tr = V.load(n); TR[n] = tr
    m = V.vox_solid(tr, g)
    lab_names.append(n)
    label[m & (label == 0)] = len(lab_names) - 1
    static |= m
extra = {"golier_prstenec": V.load("golier_prstenec", V.BST)}
try:
    import t4_pan as MP
    V_, T_ = C.mesh_of(MP.ffc_static(), 0.01, 0.1)
    extra["ffc_static"] = V_[T_]
    HAVE_MP = True
except Exception as e:  # pragma: no cover
    print("t4_pan import failed:", e); HAVE_MP = False
for n, tr in extra.items():
    m = V.vox_solid(tr, g); lab_names.append(n); label[m & (label == 0)] = len(lab_names) - 1; static |= m
print("static done", static.sum(), f"{time.time()-t00:.0f}s")

# ---------------------------------------------------------------- moving: cylindrical sweep grid
DR, DT, DZ = 0.25, 0.5, 0.5
RMAX, ZC0, ZC1 = 37.0, -50.0, 4.5
NR, NT, NZ = int(RMAX / DR), int(360 / DT), int((ZC1 - ZC0) / DZ)


def cyl_mark(Cg, P):
    r = np.hypot(P[:, 0], P[:, 1]); th = np.degrees(np.arctan2(P[:, 1], P[:, 0])) % 360.0
    ir = np.floor(r / DR).astype(int); it = np.floor(th / DT).astype(int) % NT; iz = np.floor((P[:, 2] - ZC0) / DZ).astype(int)
    ok = (ir < NR) & (iz >= 0) & (iz < NZ)
    Cg[ir[ok], it[ok], iz[ok]] = True


CP = np.zeros((NR, NT, NZ), bool)     # rigid stage parts (lift independent)
CL = np.zeros((NR, NT, NZ), bool)     # lift group at lift 0 (extruded 0..20 below)
CC = np.zeros((NR, NT, NZ), bool)     # posed parts (crank, FFC lift loop, pigtail)
CRANK = ("rameno_zdvih", "cap_kluky", "skr_ramena")
CABLE = ("pigtail_zdvih",)
P_rigid = [n for n in REC if grp[n] == "P" and n not in CRANK + CABLE]
L_rigid = [n for n in REC if grp[n] == "L" and n not in CABLE]
B_P = ["golier_kotuc"]
B_L = ["krk_predna_polovica", "krk_zadna_polovica", "kabel", "capy", "klzny_kruzok", "loziska_MR85", "paka", "pena_serva",
       "servo_MG90S", "usko_kryt", "usko_lozisko", "skrutky"]
for n in P_rigid:
    cyl_mark(CP, V.solid_points(V.load(n)))
for n in B_P:
    cyl_mark(CP, V.solid_points(V.load(n, V.BST)))
if HAVE_MP:
    V_, T_ = C.mesh_of(MP.ffc_riser(), 0.01, 0.1); cyl_mark(CP, V.solid_points(V_[T_]))
for n in L_rigid:
    cyl_mark(CL, V.solid_points(V.load(n)))
for n in B_L:
    tr = V.load(n, V.BST)
    keep = tr[:, :, 2].min(1) < 6.0
    P = V.solid_points(tr) if n != "skrutky" else V.vlib.sample_surface(tr[keep], 0.25)
    cyl_mark(CL, P[P[:, 2] < 6.0])
print("rigid moving points marked", f"{time.time()-t00:.0f}s")
# crank posed
for n in CRANK:
    P0 = V.solid_points(V.load(n))
    for lf in np.arange(0.0, 20.01, 0.5):
        th = MP.crank_angle(lf) if HAVE_MP else math.degrees(math.acos(max(-1, min(1, 1 - lf / 10.0))))
        a = math.radians(-th); c, s = math.cos(a), math.sin(a)
        Q = P0.copy(); y, z = P0[:, 1] - C.Y_LIFT, P0[:, 2] - C.Z_LIFT
        Q[:, 1] = C.Y_LIFT + c * y - s * z; Q[:, 2] = C.Z_LIFT + s * y + c * z
        cyl_mark(CC, Q)
if HAVE_MP:
    for lf in np.arange(0.0, 20.01, 1.25):
        V_, T_ = C.mesh_of(MP.fpc_lift(lf), 0.01, 0.1); cyl_mark(CC, V.solid_points(V_[T_]))
        cyl_mark(CC, V.solid_points(MP.pigtail_tris(lf)))
else:
    cyl_mark(CC, V.solid_points(V.load("pigtail_zdvih")))
print("posed parts marked", f"{time.time()-t00:.0f}s")
# lift 0..20: windowed OR along z (41 cells of 0.5)
w = int(round(20.0 / DZ))
cs = np.concatenate([np.zeros((NR, NT, 1), np.int32), np.cumsum(CL, axis=2, dtype=np.int32)], axis=2)
lo_idx = np.maximum(np.arange(NZ) - w, 0)
CLs = (cs[:, :, np.arange(NZ) + 1] - cs[:, :, lo_idx]) > 0
del cs
CM = CP | CLs | CC
# closing in r / z (point spacing 0.5 vs 0.25 r bins)
CM = ndi.binary_dilation(CM, structure=np.ones((3, 1, 3), bool))
# pan sweep: windowed circular OR along theta, +-90.5 deg
k = int(math.ceil(90.3 / DT)) + 1
ext = np.concatenate([CM[:, -k:, :], CM, CM[:, :k, :]], axis=1).astype(np.int32)
cs = np.concatenate([np.zeros((NR, 1, NZ), np.int32), np.cumsum(ext, axis=1, dtype=np.int32)], axis=1)
idx = np.arange(NT) + k
SW = (cs[:, idx + k + 1, :] - cs[:, idx - k, :]) > 0
del cs, ext
print("sweep done", SW.sum(), f"{time.time()-t00:.0f}s")
# back to the cartesian grid
X, Y, Z = np.meshgrid(g.axis(0), g.axis(1), g.axis(2), indexing="ij")
r = np.hypot(X, Y); th = np.degrees(np.arctan2(Y, X)) % 360.0
ir = np.floor(r / DR).astype(np.int32); it = np.floor(th / DT).astype(np.int32) % NT; iz = np.floor((Z - ZC0) / DZ).astype(np.int32)
ok = (ir < NR) & (iz >= 0) & (iz < NZ)
moving = np.zeros(g.n, bool)
moving[ok] = SW[ir[ok], it[ok], iz[ok]]
duct = (r >= 15.2) & (r <= 25.1) & (Z >= -46.2) & (Z <= -41.9)
moving |= duct
del X, Y, ir, it, iz, ok
print("moving voxels", moving.sum(), f"{time.time()-t00:.0f}s")

# ---------------------------------------------------------------- assembly sweeps
def occ(names, d=None):
    m = np.zeros(g.n, bool)
    for n in names:
        tr = TR.get(n) if d is None and n in TR else V.load(n, d)
        m |= V.vox_solid(tr, g)
    return m


T5 = [s for s in A.STEPS if s["id"] == "T5"][0]["move"]
lower = V.sweep_cum(occ(T5), 2, +1)
S1 = [s for s in A.STEPS if s["id"] == "S1"][0]["move"]
s1 = V.sweep_cum(occ(S1), 1, +1)
bokL = V.sweep_cum(occ(["T_bok_L"]), 0, +1); bokP = V.sweep_cum(occ(["T_bok_P"]), 0, -1)
klbL = V.sweep_cum(occ(["T_klb_L"]), 0, +1); klbP = V.sweep_cum(occ(["T_klb_P"]), 0, -1)
amp = V.sweep_cum(occ(["zosilnovac"]), 0, +1) | V.sweep_cum(occ(["menic"]), 0, -1)
print("assembly sweeps", f"{time.time()-t00:.0f}s")

# ---------------------------------------------------------------- clearance fields
ds = ndi.distance_transform_edt(~static, sampling=H).astype(np.float32)
dm = ndi.distance_transform_edt(~moving, sampling=H).astype(np.float32)
CL_S, CL_M, HALF = 0.3, 1.0, 0.25
free0 = interior & ~static & ~moving
free = free0 & (ds >= CL_S + HALF) & (dm >= CL_M + HALF)
print("free voxels", free.sum(), "=", free.sum() * H ** 3 / 1000.0, "cm3", f"{time.time()-t00:.0f}s")
np.savez_compressed(os.path.join(HERE, "map1.npz"), lo=g.lo, h=H, n=np.array(g.n), interior=interior, static=static,
                    moving=moving, label=label, lab_names=np.array(lab_names), ds=ds, dm=dm, free=free, lower=lower, s1=s1,
                    bokL=bokL, bokP=bokP, klbL=klbL, klbP=klbP, amp=amp)
json.dump(dict(grid=dict(lo=list(g.lo), h=H, n=list(g.n)), n_static=len(lab_names) - 1, have_t4_pan=HAVE_MP,
               moving_P=P_rigid + B_P + ["ffc_riser"], moving_L=L_rigid + B_L, posed=list(CRANK) + ["fpc_lift", "pigtail"],
               clearance=dict(static=CL_S, moving=CL_M, voxel_half=HALF),
               free_cm3=float(free.sum() * H ** 3 / 1000.0), seconds=round(time.time() - t00)),
          open(os.path.join(HERE, "map1.json"), "w"), indent=1)
print("saved", f"{time.time()-t00:.0f}s")
