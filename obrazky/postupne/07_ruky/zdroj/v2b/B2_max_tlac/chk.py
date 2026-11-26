"""JUDGE (vyber): independent re-check of the K3 drive (or a variant) - usage:  chk.py <variant> <L|R>
 (a) clearance to the pan/lift/neck sweep: exact cylindrical method.  A static point q and a moving sample m (stage frame)
     at azimuth difference D: reachable at equal azimuth if |D| <= 90.3 (distance in the (r, z) half plane, lift: z..z+20),
     otherwise distance to the end position of the arc.  Evaluated with a KD-tree on (r, z) + exact angular test.
 (b) clearance to the KEPT static T4 parts (surface samples 0.15, KD-tree) + voxel overlap test (map1 static labels)
 (c) assembly paths: T_stred lowering (map1 'lower'), lift-module service S1 ('s1'), side cap removal (+X, exact column test)
     servo insertion from the side (-X, exact column test against the kept static parts)
writes chk_<variant>_<side>.json"""
import sys, os, json, math, time
sys.dont_write_bytecode = True
import numpy as np
from scipy.spatial import cKDTree
from scipy import ndimage as ndi
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import geo as G
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T4/overenie3")
import vlib  # noqa
T4 = "/tmp/claude-0/gapwf/fin/T4"; BST = "/tmp/claude-0/gapwf/fin/B/stl"
var = sys.argv[1] if len(sys.argv) > 1 else "K3"
side = sys.argv[2] if len(sys.argv) > 2 else "L"
sg = 1.0 if side == "L" else -1.0
t0 = time.time()
if var.startswith("B2"):
    import geo_b2 as GB  # noqa
    import intern_boss as IB  # noqa
    PARTS, BV = GB.parts()
    PARTS["STAT_boss"] = IB.boss_b2()
    if var == "B2col":
        PARTS = {"STAT_colfill": np.load(os.path.join(HERE, "colfill_%s.npz" % side))["P"].astype(float) * np.array([1.0 if side == "L" else -1.0, 1, 1])}
    if var == "B2lift":      # pinion-shaft lifted for servo service (plug out): only the lifted rotating parts
        PARTS = {k + "_lift": GB.lifted(v, GB.B2["lift"]) for k, v in PARTS.items() if k.startswith("ROT_V")}
else:
    import variants  # noqa
    PRM, EXTRA = variants.get(var)
    PARTS, BV = G.parts(PRM)
    PARTS.update(EXTRA(PRM) if EXTRA else {})
if sg < 0:
    PARTS = G.mirror(PARTS)
res = dict(variant=var, side=side, bevel={k: v for k, v in BV.items()}, sweep={}, static={}, paths={})

# ------------------------------------------------------------------ (a) sweep
D = np.load(os.path.join(HERE, "mov.npz"))
R, L, LOOP = D["R"].astype(float), D["L"].astype(float), D["LOOP"].astype(float)
Rt, Lt = D["Rt"], D["Lt"]
PAN = 90.3


def cyl(P):
    return np.hypot(P[:, 0], P[:, 1]), np.degrees(np.arctan2(P[:, 1], P[:, 0])), P[:, 2]


rR, tR, zR = cyl(R); rL, tL, zL = cyl(L)
# z-expand lifted samples (0.25 steps) for the (r, z) tree; exact z handled by dense replication (error <= 0.125 in z)
lifts = np.arange(0.0, 20.001, 0.25)
LrE = np.repeat(rL, len(lifts)); LtE = np.repeat(tL, len(lifts)); LzE = (zL[:, None] + lifts[None, :]).ravel()
LnE = np.repeat(np.arange(len(L)), len(lifts))
MR = np.r_[rR, LrE]; MT = np.r_[tR, LtE]; MZ = np.r_[zR, LzE]
MTAG = np.r_[np.arange(len(R)), -1 - LnE]
RCUT = float(os.environ.get("RCUT", "26.0"))
sel = MR > RCUT                                    # nothing new comes inside r RCUT
MR, MT, MZ, MTAG = MR[sel], MT[sel], MZ[sel], MTAG[sel]
tree = cKDTree(np.c_[MR, MZ])
loop_tree = cKDTree(LOOP)
print("sweep model", len(MR), f"{time.time()-t0:.0f}s", flush=True)


def tag(i):
    return str(Rt[i]) if i >= 0 else str(Lt[-1 - i])


def sweep_min(Q, cap=2.0, thr=1.6):
    """exact min distance of static points Q to the pan/lift sweep: conservative (r, z) raster EDT over the moving samples
    that can reach Q's azimuth range, then exact angular evaluation for the points below thr"""
    r, t, z = cyl(Q)
    keep = r < 46.0
    Q, r, t, z = Q[keep], r[keep], t[keep], z[keep]
    if not len(Q):
        return (1e9, None, None)
    ta, tb = t.min(), t.max()
    if tb - ta > 180:  # wrap
        t2 = t % 360.0; ta, tb = t2.min(), t2.max()
    lo, hi = ta - PAN - 0.5, tb + PAN + 0.5
    reach = ((MT - lo) % 360.0) <= (hi - lo)
    cell = 0.05
    r0, z0 = RCUT, -90.0
    nr, nz = int((46.0 - RCUT) / cell), int(100.0 / cell)
    img = np.zeros((nr, nz), bool)
    ir = np.floor((MR[reach] - r0) / cell).astype(int); iz = np.floor((MZ[reach] - z0) / cell).astype(int)
    ok = (ir >= 0) & (ir < nr) & (iz >= 0) & (iz < nz)
    img[ir[ok], iz[ok]] = True
    edt = ndi.distance_transform_edt(~img, sampling=cell)
    jr = np.clip(np.floor((r - r0) / cell).astype(int), 0, nr - 1); jz = np.clip(np.floor((z - z0) / cell).astype(int), 0, nz - 1)
    dlb = edt[jr, jz] - 0.036
    best = (float(dlb.min()), Q[int(dlb.argmin())].round(2).tolist(), "lower bound")
    cand = np.nonzero(dlb < thr)[0]
    if len(cand):
        best = (1e9, None, None)
        sub = np.nonzero(reach)[0]
        stree = cKDTree(np.c_[MR[sub], MZ[sub]])
        for i in cand:
            li = stree.query_ball_point([r[i], z[i]], cap)
            if not li: continue
            li = sub[np.asarray(li)]
            dth = (t[i] - MT[li] + 180.0) % 360.0 - 180.0
            a = np.maximum(np.abs(dth) - PAN, 0.0)
            d = np.sqrt(np.maximum(r[i] ** 2 + MR[li] ** 2 - 2 * r[i] * MR[li] * np.cos(np.radians(a)), 0) + (z[i] - MZ[li]) ** 2)
            k = int(np.argmin(d))
            if d[k] < best[0]:
                best = (float(d[k]), Q[i].round(2).tolist(), tag(int(MTAG[li[k]])))
        if best[0] > 1e8:
            best = (float(dlb.min()), Q[int(dlb.argmin())].round(2).tolist(), "lower bound (no candidate within cap)")
    dl, _ = loop_tree.query(Q)
    if dl.min() < best[0]:
        best = (float(dl.min()), Q[int(dl.argmin())].round(2).tolist(), "fpc_loop")
    return best


for name, P in PARTS.items():
    if name.startswith("PATH"): continue
    b = sweep_min(P)
    res["sweep"][name] = dict(min=round(b[0], 2) if b[0] < 1e8 else ">4", at=b[1], by=b[2])
    print("sweep  %-16s %s" % (name, res["sweep"][name]), f"{time.time()-t0:.0f}s", flush=True)

# ------------------------------------------------------------------ (b) kept static parts
PJ = json.load(open(os.path.join(T4, "parts.json")))
REM = {"T_klb_L", "T_klb_P", "zosilnovac", "menic"}
REMP = ("magnet_klb", "podlozka_klb", "skrutka_klb", "vl_F8", "skr_F14", "pd_F14", "skr_F3a_2", "pd_F3a_2", "vl_F3a_2")
SP, ST = [], []
TR = {}
for p in PJ["parts"]:
    n = p["name"]
    if p["group"] != "T" or n in REM or n.startswith(REMP): continue
    bb = p["bbox"]
    if sg * (bb[3] if sg > 0 else bb[0]) < 18.0: continue
    tr = vlib.load_stl(f"{T4}/stl/{n}.stl"); TR[n] = tr
    S = vlib.sample_surface(tr, 0.15)
    if n == "T_spodok":
        X, Y, Z = S[:, 0], S[:, 1], S[:, 2]
        pin = (np.hypot(X - 27.09, Y - 12.89) <= 4.0) | (np.hypot(X + 21.37, Y + 21.06) <= 4.0)
        tub = (np.abs(X) / 39.55) ** 2.66 + (np.abs(Y) / 25.49) ** 2.66 < 1.0
        col = (Z >= -82.3) & ((Z >= -78.0) | tub) & ((X >= 26.0) | (X <= -32.4)) & ~pin
        S = S[~col]
    if n == "T_paluba":
        S = S[np.abs(S[:, 0]) <= 31.0]
    S = S[sg * S[:, 0] > 15.0]
    SP.append(S); ST += [n] * len(S)
for extra in ("golier_prstenec",):
    E = vlib.sample_surface(vlib.load_stl(f"{BST}/{extra}.stl"), 0.15); E = E[sg * E[:, 0] > 15.0]
    SP.append(E); ST += [extra] * len(E)
SP = np.concatenate(SP); ST = np.array(ST)
stree = cKDTree(SP)
print("static model", len(SP), f"{time.time()-t0:.0f}s", flush=True)
for name, P in PARTS.items():
    if name.startswith("PATH"): continue
    d, j = stree.query(P, distance_upper_bound=6.0)
    near = {}
    for kk in np.argsort(d)[:20000]:
        if d[kk] > 6: break
        t = str(ST[j[kk]]); near[t] = min(near.get(t, 99.0), float(d[kk]))
    k = int(np.argmin(d))
    res["static"][name] = dict(min=round(float(d[k]), 2) if d[k] < 6 else ">6", at=P[k].round(2).tolist(),
                               nearest={a: round(b, 2) for a, b in sorted(near.items(), key=lambda kv: kv[1])[:5]})
    print("static %-16s %s" % (name, res["static"][name]), flush=True)

# ------------------------------------------------------------------ (c) assembly paths
M = np.load("/tmp/claude-0/gapwf/fin/R1/trup_servo/map1.npz")
lo, h, n = M["lo"], float(M["h"]), M["n"]
for key in ("lower", "s1"):
    mask = M[key]
    dist = ndi.distance_transform_edt(~mask, sampling=h)
    out = {}
    for name, P in PARTS.items():
        if name.startswith("PATH"): continue
        I = np.floor((P - lo) / h).astype(int)
        ok = np.all((I >= 0) & (I < n), axis=1)
        dd = dist[I[ok, 0], I[ok, 1], I[ok, 2]]
        out[name] = round(float(dd.min()) - h / 2, 2) if len(dd) else None
    res["paths"][key] = out
    print(key, out, flush=True)


def column_min_x(S, cell=0.25, sense=+1):
    """(y, z) cell -> min (sense +1) / max (sense -1) x of point set S"""
    iy = np.floor(S[:, 1] / cell).astype(int); iz = np.floor(S[:, 2] / cell).astype(int)
    key = iy * 100000 + iz
    val = S[:, 0] * sense
    order = np.lexsort((val, key))
    k2 = key[order]; first = np.r_[True, k2[1:] != k2[:-1]]
    return dict(zip(k2[first].tolist(), (val[order][first] * sense).tolist()))


def path_margin(P, S, sense, cell=0.25, clr=0.3):
    """P moves (or S moves) along X so that S sweeps over [x_S, +inf) (sense +1, left side); margin = x_S - x_P (worst) over
    cells within clr in y/z"""
    col = column_min_x(S, cell, sense)
    iy = np.floor(P[:, 1] / cell).astype(int); iz = np.floor(P[:, 2] / cell).astype(int)
    r = int(math.ceil(clr / cell))
    worst = (1e9, None)
    for dy in range(-r, r + 1):
        for dz in range(-r, r + 1):
            keys = (iy + dy) * 100000 + (iz + dz)
            xs = np.array([col.get(k, np.nan) for k in keys.tolist()])
            m = sense * (xs - P[:, 0])
            if np.all(np.isnan(m)): continue
            k = int(np.nanargmin(m))
            if m[k] < worst[0]: worst = (float(m[k]), P[k].round(2).tolist())
    return worst


# side cap removal along +sg X: the cap's own points sweep from their position outward; new parts must stay inboard
bok = "T_bok_L" if sg > 0 else "T_bok_P"
SB = vlib.sample_surface(vlib.load_stl(f"{T4}/stl/{bok}.stl"), 0.15)
out = {}
for name, P in PARTS.items():
    if name.startswith(("ROT_A", "BRG_A", "PATH", "STAT_keeper", "STAT_post")): continue      # plug cartridge parts go in after the cap
    Q = P[::2]
    w = path_margin(Q, SB, sense=sg)
    out[name] = dict(margin=round(w[0], 2) if w[0] < 1e8 else None, at=w[1])
res["paths"]["side_cap_removal"] = out
print("cap removal", out, flush=True)
# servo insertion from the open side: the servo (+ coupler) sweeps from its place outward; kept static parts (cap off)
SS = SP[ST != bok]
out = {}
for name in [n for n in ("SERVO", "SERVO_cable", "ROT_V_coupler") if n in PARTS and not (var.startswith("B2") and n == "ROT_V_coupler")]:
    P = PARTS[name]
    lo_, hi_ = P.min(0) - 1.0, P.max(0) + 1.0
    m_ = (SS[:, 1] > lo_[1]) & (SS[:, 1] < hi_[1]) & (SS[:, 2] > lo_[2]) & (SS[:, 2] < hi_[2]) & (sg * SS[:, 0] > sg * (lo_[0] if sg > 0 else hi_[0]) - 30)
    w = path_margin(SS[m_], P[::2], sense=sg)          # servo sweeps outward from its place; static points must stay inboard
    out[name] = dict(margin=round(w[0], 2) if w[0] < 1e8 else None, at=w[1])
res["paths"]["servo_insert_side"] = out
print("servo insertion", out, flush=True)
json.dump(res, open(os.path.join(HERE, f"chk_{var}_{side}.json"), "w"), indent=1)
print("done", f"{time.time()-t0:.0f}s")
