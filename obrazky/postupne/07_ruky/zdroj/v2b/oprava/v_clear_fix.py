"""FIXER copy (fill = oprava/colfill_fix_<S>.npz; lifted hex = 5 AF, z -38.4..-35.5 + 4.5 lift).
VERIFIER: own clearance check of the B1+ drive parts and the merged column fill (both sides).
Own surface point models built from final_B1plus.json numbers (not the designer/judge point models).
 (a) distance to the pan (+-90.3 deg about Z) / lift (0..20 mm +Z) sweep of the moving model (mov.npz samples, stage frame = B),
     exact azimuth formula, lift handled exactly as an interval in z;
 (b) distance to kept static T4 parts (STL surface samples; T_spodok column zone and T_paluba lobe removed as in the brief;
     T_bok with the v2 notch);
 (c) fill voxel corners vs sweep / static / servo + coupler slide corridor / T_stred lowering (+Z) / cap removal (+X)
usage: v_clear.py L|R  -> v_clear_<side>.json"""
import sys, os, json, math, time
sys.dont_write_bytecode = True
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T4/overenie3")
import vlib  # noqa  (mesh loading / surface sampling only)
SIDE = sys.argv[1] if len(sys.argv) > 1 else "L"
sg = 1.0 if SIDE == "L" else -1.0
T4 = "/tmp/claude-0/gapwf/fin/T4"; BST = "/tmp/claude-0/gapwf/fin/B/stl"
H = 0.12
t0 = time.time()
YA, ZA, XV = 3.0, -17.0, 39.0


def rev_surface(prof, axis, c1, c2, h=H):
    """surface samples of a solid of revolution; prof = closed polygon in (a, r)"""
    pts = []
    P = np.asarray(prof, float)
    for i in range(len(P)):
        p, q = P[i], P[(i + 1) % len(P)]
        n = max(2, int(math.hypot(*(q - p)) / h) + 1)
        for t in np.linspace(0, 1, n, endpoint=False):
            a, r = p + t * (q - p)
            k = max(1, int(2 * math.pi * r / h)) if r > 1e-6 else 1
            ph = np.linspace(0, 2 * math.pi, k, endpoint=False)
            pts.append(np.c_[np.full(k, a), r * np.cos(ph), r * np.sin(ph)])
    A = np.concatenate(pts)
    if axis == "x":
        return np.c_[A[:, 0], c1 + A[:, 1], c2 + A[:, 2]]
    return np.c_[c1 + A[:, 1], c2 + A[:, 2], A[:, 0]]


def tube(axis, c1, c2, ri, ro, a0, a1, h=H):
    return rev_surface([(a0, ri), (a1, ri), (a1, ro), (a0, ro)], axis, c1, c2, h)


def cyl(axis, c1, c2, r, a0, a1, h=H):
    return rev_surface([(a0, 0), (a1, 0), (a1, r), (a0, r)], axis, c1, c2, h)


F = json.load(open("/tmp/claude-0/gapwf/fin/R2c/vyber/final_B1plus.json"))
pin, gear = F["pinion_12T"], F["gear_18T"]
P = {}
P["ROT_coupler"] = cyl("z", XV, YA, F["coupler"]["r"], *F["coupler"]["z"])
vs = F["vertical_shaft"]
P["ROT_vshaft"] = np.concatenate([cyl("z", XV, YA, 4.0 / math.sqrt(3), *vs["hex_AF4_z"]), cyl("z", XV, YA, 1.5, *vs["journal_D3_z"]),
                                  cyl("z", XV, YA, 1.25, *vs["Dkey_D2p5_z"])])
zr = pin["heel_root_z"]
P["ROT_pinion"] = rev_surface([(pin["toe_z"], 0), (pin["toe_z"], pin["toe_r"]), (pin["crown_z"], pin["crown_r"]), (zr, pin["crown_r"]),
                               (zr, 3.6), (zr + 0.2, 3.6), (zr + 0.2, 1.95), (zr, 1.95), (zr, 0)], "z", XV, YA)
P["ROT_pinion_shim0.60"] = P["ROT_pinion"] + [0, 0, 0.18]       # highest shim
P["STAT_MR63"] = tube("z", XV, YA, 1.5, 3.0, *F["MR63ZZ_B1"]["z"])
P["STAT_tongue"] = tube("z", XV, YA, 3.0, 4.4, -26.85, -24.05)
g = gear
P["ROT_gear"] = rev_surface([(g["toe_x"], 0), (g["toe_x"], g["toe_r"]), (g["crown_x"], g["crown_r"]), (g["root_x"], g["crown_r"]),
                             (g["root_x"], g["root_r"]), (g["back_relief_x_for_r_gt_3"], g["root_r"]), (g["back_relief_x_for_r_gt_3"], 3.0),
                             (g["back_x"], 3.0), (g["back_x"], 0)], "x", YA, ZA)
P["ROT_M4"] = np.concatenate([cyl("x", YA, ZA, 2.0, 40.0, 60.0), cyl("x", YA, ZA, 3.5, 60.0, 64.0)])
P["STAT_A1A2spacer"] = np.concatenate([tube("x", YA, ZA, 2.0, 3.5, *F["MR74_A1"]["x"]), tube("x", YA, ZA, 2.5, 3.5, *F["spacer_sleeve"]["x"]),
                                       tube("x", YA, ZA, 2.0, 3.5, *F["MR74_A2"]["x"])])
# boss (v2 + slot 5.1): solid disc r 12.8 x 34.4..38.4 + stop ring r 11.6..12.8 x 38.4..39.1, slot |y-3|<=5.1 z -24.55..-15.5
bz = cyl("x", YA, ZA, 12.8, 34.4, 38.4)
bz = np.concatenate([bz, tube("x", YA, ZA, 11.6, 12.8, 38.4, 39.1)])
bz = bz[~((np.abs(bz[:, 1] - YA) < 5.1) & (bz[:, 2] > -24.55) & (bz[:, 2] < -15.5))]
P["STAT_boss"] = bz
if sg < 0:
    P = {k: v * [-1, 1, 1] for k, v in P.items()}
# fill voxels (0.5 mm) -> corners
FV = np.load(f"/tmp/claude-0/gapwf/fin/R2c/oprava/colfill_fix_{SIDE}.npz")["P"].astype(float)
off = np.array([[dx, dy, dz] for dx in (-0.25, 0.25) for dy in (-0.25, 0.25) for dz in (-0.25, 0.25)])
FC = (FV[:, None, :] + off[None]).reshape(-1, 3)
FC = np.unique(np.round(FC, 3), axis=0)
P["FILL_corners"] = FC
res = dict(side=SIDE, sweep={}, static={}, fill={})
print("parts", {k: len(v) for k, v in P.items()}, f"{time.time()-t0:.0f}s", flush=True)

# ------------------------------------------------------------------ (a) sweep
D = np.load("/tmp/claude-0/gapwf/fin/R1/vyber/mov.npz")
R, L, LOOP = D["R"].astype(float), D["L"].astype(float), D["LOOP"].astype(float)
Rt, Lt = D["Rt"], D["Lt"]
rR = np.hypot(R[:, 0], R[:, 1]); rL = np.hypot(L[:, 0], L[:, 1])
kR = rR > 27.0; kL = rL > 27.0
R, Rt, rR = R[kR], Rt[kR], rR[kR]; L, Lt, rL = L[kL], Lt[kL], rL[kL]
tR = np.arctan2(R[:, 1], R[:, 0]); tL = np.arctan2(L[:, 1], L[:, 0])
PAN = math.radians(90.3)
# combined arrays: zlo, zhi (lift interval)
Mr = np.r_[rR, rL]; Mt = np.r_[tR, tL]; Mz0 = np.r_[R[:, 2], L[:, 2]]; Mz1 = np.r_[R[:, 2], L[:, 2] + 20.0]
Mtag = np.r_[Rt, Lt]
# KD-tree over (r, z) with the lift interval sampled every 0.4 mm (candidate search only; exact distance below)
reps = []
for i in range(len(Mr)):
    pass
nrep = np.maximum(1, np.ceil((Mz1 - Mz0) / 0.4).astype(int) + 1)
idx = np.repeat(np.arange(len(Mr)), nrep)
frac = np.concatenate([np.linspace(0, 1, k) if k > 1 else np.zeros(1) for k in nrep])
Kz = Mz0[idx] + frac * (Mz1[idx] - Mz0[idx])
tree = cKDTree(np.c_[Mr[idx], Kz])
loop_tree = cKDTree(LOOP)
print("sweep samples", len(Mr), "tree", len(idx), f"{time.time()-t0:.0f}s", flush=True)


def sweep_min(Q, cap=2.5):
    rq = np.hypot(Q[:, 0], Q[:, 1]); tq = np.arctan2(Q[:, 1], Q[:, 0]); zq = Q[:, 2]
    best = (9.9, None, None)
    dlb, _ = tree.query(np.c_[rq, zq], distance_upper_bound=cap + 0.5)
    dlb = dlb - 0.2
    cand = np.nonzero(dlb < 1.8)[0]
    if len(cand) == 0 and np.isfinite(dlb).any():
        k = int(np.nanargmin(np.where(np.isfinite(dlb), dlb, np.nan)))
        best = (float(dlb[k]), Q[k].round(2).tolist(), "lower bound (azimuth ignored)")
    for c0 in range(0, len(cand), 2000):
      cc = cand[c0:c0 + 2000]
      lists = tree.query_ball_point(np.c_[rq[cc], zq[cc]], 2.0)
      for ii, li in enumerate(lists):
        if not li: continue
        i = cc[ii]
        j = np.unique(idx[np.asarray(li)])
        dth = np.abs((tq[i] - Mt[j] + math.pi) % (2 * math.pi) - math.pi)
        a = np.maximum(dth - PAN, 0.0)
        dz = np.maximum(0.0, np.maximum(Mz0[j] - zq[i], zq[i] - Mz1[j]))
        d = np.sqrt(np.maximum(rq[i] ** 2 + Mr[j] ** 2 - 2 * rq[i] * Mr[j] * np.cos(a), 0.0) + dz ** 2)
        k = int(np.argmin(d))
        if d[k] < best[0]:
            best = (float(d[k]), Q[i].round(2).tolist(), str(Mtag[j[k]]))
    dl, kk = loop_tree.query(Q)
    if dl.min() < best[0]:
        best = (float(dl.min()), Q[int(dl.argmin())].round(2).tolist(), "fpc_loop")
    return best


for name, Q in P.items():
    b = sweep_min(Q)
    res["sweep"][name] = dict(min=round(b[0], 3), at=b[1], by=b[2])
    print("sweep %-20s %s" % (name, res["sweep"][name]), f"{time.time()-t0:.0f}s", flush=True)

# ------------------------------------------------------------------ (b) kept static parts
PJ = json.load(open(os.path.join(T4, "parts.json")))
REM = {"T_klb_L", "T_klb_P", "zosilnovac", "menic"}
REMP = ("magnet_klb", "podlozka_klb", "skrutka_klb", "vl_F8", "skr_F14", "pd_F14", "skr_F3a_2", "pd_F3a_2", "vl_F3a_2")
SP, ST = [], []
bok = "T_bok_L" if sg > 0 else "T_bok_P"
for p in PJ["parts"]:
    n = p["name"]
    if p["group"] != "T" or n in REM or n.startswith(REMP): continue
    bb = p["bbox"]
    if (bb[3] if sg > 0 else -bb[0]) < 18.0: continue
    S = vlib.sample_surface(vlib.load_stl(f"{T4}/stl/{n}.stl"), 0.12)
    if n == "T_spodok":
        X, Y, Z = S[:, 0], S[:, 1], S[:, 2]
        pinm = (np.hypot(X - 27.09, Y - 12.89) <= 4.0) | (np.hypot(X + 21.37, Y + 21.06) <= 4.0)
        tub = (np.abs(X) / 39.55) ** 2.66 + (np.abs(Y) / 25.49) ** 2.66 < 1.0
        col = (Z >= -82.3) & ((Z >= -78.0) | tub) & ((X >= 26.0) | (X <= -32.4)) & ~pinm
        S = S[~col]
    if n == "T_paluba":
        S = S[sg * S[:, 0] <= 31.0]
    if n == bok:   # v2 notch for the vertical shaft
        notch = (sg * S[:, 0] >= 39.0) & (sg * S[:, 0] <= 41.2) & (np.abs(S[:, 1] - 3.0) <= 2.0) & (S[:, 2] >= -33.5) & (S[:, 2] <= -27.5)
        S = S[~notch]
    S = S[sg * S[:, 0] > 15.0]
    SP.append(S); ST += [n] * len(S)
E = vlib.sample_surface(vlib.load_stl(f"{BST}/golier_prstenec.stl"), 0.12); E = E[sg * E[:, 0] > 15.0]
SP.append(E); ST += ["golier_prstenec"] * len(E)
SP = np.concatenate(SP); ST = np.array(ST)
stree = cKDTree(SP)
print("static", len(SP), f"{time.time()-t0:.0f}s", flush=True)
for name, Q in P.items():
    d, j = stree.query(Q, distance_upper_bound=8.0)
    near = {}
    for kk in np.argsort(d)[:30000]:
        if d[kk] > 8: break
        t = str(ST[j[kk]]); near[t] = min(near.get(t, 99.0), float(d[kk]))
    k = int(np.argmin(d))
    res["static"][name] = dict(min=round(float(d[k]), 3) if d[k] < 8 else ">8", at=Q[k].round(2).tolist(),
                               nearest={a: round(b, 3) for a, b in sorted(near.items(), key=lambda kv: kv[1])[:6]})
    print("static %-20s %s" % (name, res["static"][name]), flush=True)

# ------------------------------------------------------------------ (c) fill vs corridors / paths
FCs = P["FILL_corners"].copy(); FCs[:, 0] *= sg          # work in the left frame
# coupler cylinder r 4.5 z -43.5..-35.5 swept along +X from x 39 (slide-in) -> distance to the swept stadium
def dist_coupler_corridor(Q):
    y, z = Q[:, 1] - YA, Q[:, 2]
    # swept region: x >= 39 -> |y| <= 4.5 band ; x < 39 -> circle about (39, 3)
    dyz_band = np.where(Q[:, 0] >= XV, np.maximum(np.abs(y) - 4.5, 0.0), np.maximum(np.hypot(Q[:, 0] - XV, y) - 4.5, 0.0))
    dzz = np.maximum(0.0, np.maximum(-43.5 - z, z - (-35.5)))
    return np.hypot(dyz_band, dzz)
dc = dist_coupler_corridor(FCs)
res["fill"]["coupler_corridor_min"] = round(float(dc.min()), 3)
res["fill"]["coupler_corridor_at"] = (FCs[int(dc.argmin())] * [sg, 1, 1]).round(2).tolist()
# rotating coupler alone
dr = np.hypot(np.maximum(np.hypot(FCs[:, 0] - XV, FCs[:, 1] - YA) - 4.5, 0), np.maximum(0, np.maximum(-43.5 - FCs[:, 2], FCs[:, 2] + 35.5)))
res["fill"]["coupler_rot_min"] = round(float(dr.min()), 3)
# servo case (top -45, x 32.95..45.05, y -14.3..8.9) slid out along +X: box x >= 32.95
def box_dist(Q, lo, hi):
    d = np.maximum(np.maximum(lo - Q, Q - hi), 0.0)
    return np.linalg.norm(d, axis=1)
ds = box_dist(FCs, np.array([32.95, -14.3, -71.0]), np.array([99.0, 8.9, -45.0]))
res["fill"]["servo_slide_min"] = round(float(ds.min()), 3)
res["fill"]["servo_slide_at"] = (FCs[int(ds.argmin())] * [sg, 1, 1]).round(2).tolist()
# servo output boss r 3.5 z -45..-44 slid along +X
db = np.hypot(np.where(FCs[:, 0] >= XV, np.maximum(np.abs(FCs[:, 1] - YA) - 3.5, 0), np.maximum(np.hypot(FCs[:, 0] - XV, FCs[:, 1] - YA) - 3.5, 0)),
              np.maximum(0, np.maximum(-45.0 - FCs[:, 2], FCs[:, 2] + 44.0)))
res["fill"]["servo_boss_slide_min"] = round(float(db.min()), 3)
# lifted vertical shaft (hex r 2.31 up to z -35.1 .. -31.6, D3 above)
dl_ = np.hypot(np.maximum(np.hypot(FCs[:, 0] - XV, FCs[:, 1] - YA) - 2.887, 0), np.maximum(0, np.maximum(-38.4 - FCs[:, 2], FCs[:, 2] + 31.0)))   # FIXER: 5 AF hex z -38.4..-35.5, lift 4.5
res["fill"]["lifted_hex_min"] = round(float(dl_.min()), 3)
# T_stred lowering: T5 group withdrawn +Z
sys.path.insert(0, T4); cwd = os.getcwd(); os.chdir(T4)
import t4_assembly as A  # noqa
T5 = [s for s in A.STEPS if s["id"] == "T5"][0]["move"]
os.chdir(cwd)
S5 = np.concatenate([vlib.sample_surface(vlib.load_stl(f"{T4}/stl/{nm}.stl"), 0.12) for nm in T5])
S5 = S5[sg * S5[:, 0] > 15]
# ray sweep +Z: for every fill corner q, distance to rays {s + t e_z, t >= 0} = horizontal distance if s_z <= q_z, else 3-D distance
t2 = cKDTree(S5[:, :2])
Q = P["FILL_corners"]
best = (9.9, None)
lists = t2.query_ball_point(Q[:, :2], 1.5)
for i, li in enumerate(lists):
    if not li: continue
    s = S5[li]
    dp = np.hypot(s[:, 0] - Q[i, 0], s[:, 1] - Q[i, 1])
    ahead = Q[i, 2] - s[:, 2]
    d = np.where(ahead >= 0, dp, np.hypot(dp, ahead))
    k = int(d.argmin())
    if d[k] < best[0]: best = (float(d[k]), Q[i].round(2).tolist())
res["fill"]["T_stred_lowering_min"] = round(best[0], 3); res["fill"]["T_stred_lowering_at"] = best[1]
# cap removal (+sg X): every fill corner must be behind (inboard of) the cap's points that sweep outward
SB = vlib.sample_surface(vlib.load_stl(f"{T4}/stl/{bok}.stl"), 0.12)
notch = (sg * SB[:, 0] >= 39.0) & (sg * SB[:, 0] <= 41.2) & (np.abs(SB[:, 1] - 3.0) <= 2.0) & (SB[:, 2] >= -33.5) & (SB[:, 2] <= -27.5)
SB = SB[~notch]
tb = cKDTree(SB[:, 1:])
best = (9.9, None)
lists = tb.query_ball_point(Q[:, 1:], 1.5)
for i, li in enumerate(lists):
    if not li: continue
    s = SB[li]
    dp = np.hypot(s[:, 1] - Q[i, 1], s[:, 2] - Q[i, 2])
    ahead = sg * (s[:, 0] - Q[i, 0])           # cap point outboard of q: it moves away -> horizontal distance not relevant
    # q is swept by the cap if a cap point is INBOARD of q (it passes q while moving out)
    behind = sg * (Q[i, 0] - s[:, 0])
    d = np.where(behind >= 0, dp, np.hypot(dp, behind))
    k = int(d.argmin())
    if d[k] < best[0]: best = (float(d[k]), Q[i].round(2).tolist())
res["fill"]["cap_removal_min"] = round(best[0], 3); res["fill"]["cap_removal_at"] = best[1]
res["fill"]["n_corners"] = int(len(Q))
json.dump(res, open(f"/tmp/claude-0/gapwf/fin/R2c/oprava/v_clear_fix_{SIDE}.json", "w"), indent=1)
print(json.dumps(res["fill"], indent=1))
print("done", f"{time.time()-t0:.0f}s")
