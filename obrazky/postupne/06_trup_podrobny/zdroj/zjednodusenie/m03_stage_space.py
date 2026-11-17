"""m03 - free space ON the pan stage (stage frame) for a cable junction / lift loop, and door access.
Occupied = every pan-stage part (P_*, servo, bracket, crank, FPC excluded) + every lift part swept over lift 0..20
(crank also over its 180 deg; envelope r 12.2 about the shaft, front half used, from t4_common CRANK).
Free cell = not occupied, inside PAN_ENV (r limit by z), z >= -41.3 (pinion rule outside the back sector).
Reports free boxes at the +X end, -X end, front face and back-right corner of the well, and whether a straight
line from the door opening reaches a point at each candidate when the stage is turned to face the door.
Run: /opt/venv/cad/bin/python m03_stage_space.py   (about 60 s)"""
import numpy as np, math
from zj_lib import read_stl, sample, rotz, dump, say

H = 0.5
xs = np.arange(-36, 36.01, H); ys = np.arange(-36, 36.01, H); zs = np.arange(-46, -10.99, H)
NX, NY, NZ = len(xs), len(ys), len(zs)
occ = np.zeros((NX, NY, NZ), bool)


def mark(P, pad=0.5):
    """mark the grid cells within pad of the points (dilated point cloud)"""
    for dx in (-pad, 0, pad):
        for dy in (-pad, 0, pad):
            for dz in (-pad, 0, pad):
                Q = P + (dx, dy, dz)
                i = np.round((Q[:, 0] - xs[0]) / H).astype(int); j = np.round((Q[:, 1] - ys[0]) / H).astype(int)
                k = np.round((Q[:, 2] - zs[0]) / H).astype(int)
                ok = (i >= 0) & (i < NX) & (j >= 0) & (j < NY) & (k >= 0) & (k < NZ)
                occ[i[ok], j[ok], k[ok]] = True


BOXFILL = ("servo_zdvih", "krk_predna_polovica", "krk_zadna_polovica", "L_pata")


def fill_solid(name, lifts=(0.0,)):
    """surface points dilated by 0.5 (walls >= 1.0 are then solid in the grid); for compact solids listed in
    BOXFILL the whole bounding box is marked (conservative). A z-parity interior fill was tried first and gave
    wrong intervals on the open-bottom well (non-convex, coincident crossings), so it is not used."""
    T = read_stl(name)
    for L in lifts:
        TT = T + (0, 0, L)
        P = sample(TT, 0.35)
        mark(P)
        if name in BOXFILL:
            lo, hi = TT.reshape(-1, 3).min(0), TT.reshape(-1, 3).max(0)
            i0, i1 = np.searchsorted(xs, lo[0]), np.searchsorted(xs, hi[0], "right")
            j0, j1 = np.searchsorted(ys, lo[1]), np.searchsorted(ys, hi[1], "right")
            k0, k1 = np.searchsorted(zs, lo[2]), np.searchsorted(zs, hi[2], "right")
            occ[i0:i1, j0:j1, k0:k1] = True


stage = ["P_sachta", "P_koleso", "P_drziak_serva", "servo_zdvih", "spoj_zdvih", "kabel_zdvih", "skr_F10_1",
         "skr_F10_2", "skr_F11", "vl_F10_1", "vl_F10_2"]
lift = ["L_pata", "L_ucho", "skr_F12", "kolik_ucha", "krk_predna_polovica", "krk_zadna_polovica"]
for n in stage:
    fill_solid(n); say("stage", n)
for n in lift:
    fill_solid(n, lifts=(0.0, 5.0, 10.0, 15.0, 20.0)); say("lift", n)
# crank sweep: disc r 12.2 about (y 23.2, z -24.2) for x -17..-14.5 (front half y <= 25.4) + hub r 3.6 x -17..-12.8
X, Y, Z = np.meshgrid(xs, ys, zs, indexing="ij")
crank = ((X >= -17.5) & (X <= -12.3) & (np.hypot(Y - 23.2, Z + 24.2) <= 12.7))
occ |= crank
# the present tongue / FPC fin are NOT counted as occupied (they are replaced)

# allowed region: inside PAN_ENV and above the pinion rule
PAN_ENV = [(-45.7, -41.9, 15.9), (-41.9, -22.0, 34.0), (-22.0, -18.0, 33.5), (-18.0, -11.5, 32.2),
           (-11.5, -10.5, 28.3)]
rlim = np.full(NZ, 0.0)
for k, z in enumerate(zs):
    for z0, z1, r in PAN_ENV:
        if z0 <= z + H / 2 <= z1:
            rlim[k] = r
R = np.hypot(X, Y)
allowed = (R <= rlim[None, None, :] - 0.3) & (Z >= -41.2)
free = allowed & ~occ


def box_free(x0, x1, y0, y1, z0, z1):
    m = (X >= x0) & (X <= x1) & (Y >= y0) & (Y <= y1) & (Z >= z0) & (Z <= z1)
    return round(float(free[m].mean()), 3), int(m.sum())


def largest_free_box(region, name):
    """greedy: for the region (x0,x1,y0,y1,z0,z1) report the free fraction per 1 mm slab along its long axis"""
    x0, x1, y0, y1, z0, z1 = region
    f, n = box_free(*region)
    return dict(name=name, box=region, free_fraction=f, cells=n)


cands = [
    ((25.4, 31.0, -6.0, 6.0, -41.2, -13.5), "+X end exterior: lift-loop zone (present FPC_LIFT x 25.2..28.4)"),
    ((25.4, 31.0, -8.0, 8.0, -41.2, -24.0), "+X end exterior, lower half"),
    ((-31.0, -25.4, -8.0, 8.0, -41.2, -13.5), "-X end exterior (|y|<=8)"),
    ((-31.0, -25.4, -8.0, 8.0, -41.2, -24.0), "-X end exterior, lower half"),
    ((-16.0, 16.0, -20.0, -13.0, -41.2, -12.0), "front face exterior (y -13..-20, inside r 26.5)"),
    ((-12.0, 12.0, -19.0, -13.0, -41.2, -26.0), "front face exterior, lower part"),
    ((23.0, 30.0, 12.8, 17.0, -41.2, -22.0), "back-right corner beside bracket"),
    ((16.6, 23.0, 12.8, 18.3, -41.2, -36.8), "back-right corner below the bracket lug (present micro junction)"),
]
res = {"grid_mm": H, "candidates": [largest_free_box(r, n) for r, n in cands]}
for c in res["candidates"]:
    say(c)

# r extent of free space inside r 26.5 in the front sector: is the whole front face zone within r 26.5?
m = free & (Y < -12.8) & (R <= 26.2)
res["front_free_cells_within_r26.2"] = int(m.sum())
res["front_free_bbox_within_r26.2"] = [round(float(v), 1) for v in (X[m].min(), X[m].max(), Y[m].min(), Y[m].max(),
                                                                    Z[m].min(), Z[m].max())] if m.any() else None

# ---- door line of sight: torso-frame points of candidates when the stage is turned to face the door -------------
tri = []
for n in ("T_stred", "T_bok_L", "T_bok_P", "T_ram", "T_paluba", "DPS_riadenie", "menic", "zosilnovac", "kondenzator",
          "T_spodok"):
    tri.append(read_stl(n))
TS = np.concatenate(tri)
stg = np.concatenate([read_stl(n) for n in stage + ["L_pata", "L_ucho"]])


def ray_hits(TRI, O, D, tmax):
    """Moller-Trumbore, returns True if any triangle hit with 0 < t < tmax"""
    e1 = TRI[:, 1] - TRI[:, 0]; e2 = TRI[:, 2] - TRI[:, 0]
    p = np.cross(D, e2); det = (e1 * p).sum(1)
    ok = np.abs(det) > 1e-12
    inv = np.where(ok, 1.0 / np.where(ok, det, 1), 0)
    s = O - TRI[:, 0]; u = (s * p).sum(1) * inv
    q = np.cross(s, e1); v = (q * D).sum(1) * inv; t = (q * e2).sum(1) * inv
    return bool((ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 0.05) & (t < tmax)).any())


def door_reach(p_stage, pan, dirs=9):
    """from points spread over the door opening (y = 41, x +-26, z -70..-14) to the target: fraction of free lines"""
    p = rotz(np.array([p_stage]), pan)[0]
    S = rotz(stg, pan)
    tri_all = np.concatenate([TS, S.reshape(-1, 3, 3)])
    # drop triangles of the door itself is not needed: T_dvere is not loaded (door open)
    n_ok = 0; n = 0
    for x in np.linspace(-24, 24, dirs):
        for z in np.linspace(-68, -16, dirs):
            O = np.array([x, 41.0, z]); D = p - O; L = np.linalg.norm(D); D = D / L
            n += 1
            if not ray_hits(tri_all, O, D, L - 0.6):
                n_ok += 1
    return round(n_ok / n, 3), [round(float(v), 2) for v in p]


targets = [((28.0, 0.0, -38.0), 85.0, "+X end, low (pan +85)"), ((28.0, 0.0, -30.0), 85.0, "+X end, mid (pan +85)"),
           ((24.0, 0.0, -39.0), 85.0, "+X end window at the foot (pan +85)"),
           ((-28.0, 0.0, -38.0), -85.0, "-X end, low (pan -85)"),
           ((20.0, 15.5, -39.0), 0.0, "back-right corner below the lug (pan 0)"),
           ((26.0, 14.5, -30.0), 0.0, "back-right corner beside the bracket (pan 0)"),
           ((0.0, -15.0, -35.0), 85.0, "front face (pan +85)"), ((0.0, -15.0, -35.0), -85.0, "front face (pan -85)")]
res["door_line_of_sight(fraction of 81 lines from the opening)"] = []
for p, pan, name in targets:
    f, pt = door_reach(p, pan)
    res["door_line_of_sight(fraction of 81 lines from the opening)"].append(dict(target=name, stage_pt=p, pan=pan,
                                                                                torso_pt=pt, free=f))
    say(name, f, pt)
dump("m03_stage_space.json", res)
