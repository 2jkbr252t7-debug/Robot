"""straight-line assembly of the OBAL shells against the REAL meshes of the RAM module (information for the integrator, K7)
  X2: T_stred with its front stack is lowered along -Z over the tower:  collision = tower geometry ABOVE band geometry
  X3: T_bok_L slides along -X (T_bok_P along +X) over T_stred + tower:  collision = static geometry OUTSIDE cap geometry
Method: rasters of 0.25 mm in the plane normal to the motion (extreme coordinate of the moving part / of the static part
dilated by the plan clearance) find the candidate regions; for every candidate pair the plan gap is then MEASURED on the
point samples (0.5 mm + all mesh vertices) with a KD-tree: smallest in-plane distance between a moving point and a static point that lies
further along the travel.  Usage: /opt/venv/cad/bin/python slide_checks.py  -> obal_work/slide_checks.json"""
import sys, os, json, math, time
import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree

T4 = "/tmp/claude-0/gapwf/fin/T4"
sys.path.insert(0, T4)
import t4_common as C
import t4_obal as O

T0 = time.time()
names = [r["name"] for r in O.load_parts()]
rj = json.load(open(os.path.join(T4, "parts_ram.json")))
rparts = rj["parts"] if isinstance(rj, dict) else rj
have = [r["name"] for r in rparts if r["group"] == "T" and os.path.exists(os.path.join(T4, "stl", r["name"] + ".stl"))]
H = 0.5
MESH = {}


def pts_of(n):
    if n in MESH:
        return MESH[n]
    V, T = O.read_stl(os.path.join(T4, "stl", n + ".stl"))
    a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    P = [V, (a + b + c) / 3]
    L = np.maximum.reduce([np.linalg.norm(a - b, axis=1), np.linalg.norm(b - c, axis=1), np.linalg.norm(c - a, axis=1)])
    big = L > H
    if big.any():
        a, b, c, L = a[big], b[big], c[big], L[big]
        k = np.minimum(np.ceil(L / H).astype(int), 60)
        for kk in np.unique(k):
            m = k == kk
            for i in range(kk + 1):
                for j in range(kk + 1 - i):
                    u, v = i / kk, j / kk
                    P.append(a[m] * (1 - u - v) + b[m] * u + c[m] * v)
    MESH[n] = np.concatenate(P)
    return MESH[n]


CELL, HALF = 0.25, 70.0
NG = int(2 * HALF / CELL)


def raster(P, axis, mode):
    o = [k for k in range(3) if k != axis]
    ij = np.floor((P[:, o] + HALF) / CELL).astype(int)
    m = (ij >= 0).all(1) & (ij < NG).all(1)
    A = np.full((NG, NG), 9e9 if mode == "min" else -9e9)
    if not m.any():
        return A
    flat = ij[m, 0] * NG + ij[m, 1]
    order = np.argsort(flat, kind="stable")
    f, v = flat[order], P[m, axis][order]
    idx = np.flatnonzero(np.r_[True, f[1:] != f[:-1]])
    red = (np.minimum if mode == "min" else np.maximum).reduceat(v, idx)
    A.ravel()[f[idx]] = red
    return A


def disk(rad):
    k = max(1, int(math.ceil(rad / CELL)))
    yy, xx = np.mgrid[-k:k + 1, -k:k + 1]
    return (xx * xx + yy * yy) <= (rad / CELL + 0.5) ** 2


def slide(moving, static, axis, sign, clear_of, mask=None):
    """the moving parts travel along axis * sign into place.  Returns (findings, n_pairs)."""
    o = [k for k in range(3) if k != axis]
    res = []; npairs = 0
    MOV = {}
    for b in static:
        Pb = pts_of(b).copy(); Pb[:, axis] *= -sign                   # flipped frame: collision = static ABOVE moving
        clear = clear_of(b)
        Tm = ndimage.maximum_filter(raster(Pb, axis, "max"), footprint=disk(clear + 0.3), mode="constant", cval=-9e9)
        treeb = None
        for n in moving:
            key = (n, mask(n, b) if mask else None)
            if key not in MOV:
                Pn = pts_of(n).copy()
                if key[1] is not None:
                    Pn = Pn[key[1](Pn)]
                Pn[:, axis] *= -sign
                MOV[key] = (Pn, raster(Pn, axis, "min") if len(Pn) else None)
            Pn, Bm = MOV[key]
            if Bm is None:
                continue
            npairs += 1
            hit = (Tm > Bm + 0.05) & (Bm < 1e9) & (Tm > -1e9)
            if not hit.any():
                continue
            # measure: moving points in the candidate cells against the static points
            ij = np.floor((Pn[:, o] + HALF) / CELL).astype(int)
            ok = (ij >= 0).all(1) & (ij < NG).all(1)
            cand = np.zeros(len(Pn), bool); cand[ok] = hit[ij[ok, 0], ij[ok, 1]]
            Q = Pn[cand]
            if treeb is None:
                treeb = cKDTree(Pb[:, o])
            best = (9e9, None, None)
            nb = treeb.query_ball_point(Q[:, o], clear + 0.6)
            for q, lst in zip(Q, nb):
                if not lst:
                    continue
                S = Pb[lst]
                S = S[S[:, axis] > q[axis] + 0.05]
                if not len(S):
                    continue
                d = np.hypot(S[:, o[0]] - q[o[0]], S[:, o[1]] - q[o[1]])
                i = int(np.argmin(d))
                if d[i] < best[0]:
                    best = (float(d[i]), q.copy(), S[i].copy())
            if best[1] is None:
                continue
            qm, qs = best[1], best[2]
            qm[axis] *= -sign; qs[axis] *= -sign
            res.append(dict(moving=n, static=b, plan_gap=round(best[0], 3), required=clear, ok=bool(best[0] >= clear - 0.05),
                            moving_pt=[round(float(v), 2) for v in qm], static_pt=[round(float(v), 2) for v in qs]))
    return res, npairs


OUT = {}
LOWER = ["T_stred", "T_svetlovod", "T_mriezka", "T_drziak_led", "T_drziak_repro", "reproduktor", "tesnenie_repro", "DPS_led"] + \
        [n for n in names if n.startswith(("skrutka_led", "skrutka_repro", "vlozka_stred", "magnet_zarubna", "vyvod_"))]
AFTER = ("pastorok_pan", "skr_pastorok_pan", "skr_F1_", "T_prichytka_fpc", "skr_fpc", "vl_F8_")      # mounted after T_stred
tower = [n for n in have if not n.startswith(AFTER) and pts_of(n)[:, 2].max() > C.Z_WHITE + 0.3]


def deep3(P):
    return C.dist_outer(P) > 3.0


def deep44(P):
    return C.dist_outer(P) > 4.4


# cap spigot: only the add-ons of T_stred count (the lip itself is the 0.2 locating fit)
x2, n2 = slide(LOWER, tower, 2, -1, lambda b: 0.2 if b == "T_spodok" else C.TOWER_CLEAR,
               lambda n, b: deep3 if (b == "T_spodok" and n == "T_stred") else None)
x2.sort(key=lambda q: q["plan_gap"])
OUT["X2_lowering_vs_ram_meshes"] = dict(
    tower_parts=len(tower), pairs=n2, closest=x2[:25], min_plan_gap=x2[0]["plan_gap"] if x2 else None,
    ok=all(q["ok"] for q in x2),
    note="straight -Z lowering of T_stred + front stack over the RAM STLs present at the time of the run (parts mounted later excluded: "
         "pan pinion, FPC clamp, F1 screws).  Required plan clearance 0.5 (TOWER_CLEAR), 0.2 at the cap spigot (shell wall excluded "
         "there); gaps measured on 0.5 mm point samples (+ all mesh vertices), listed when below required + 0.6")
print(f"X2 lowering: {len(tower)} tower parts, {n2} pairs, {len(x2)} near pairs, min plan gap {OUT['X2_lowering_vs_ram_meshes']['min_plan_gap']}, "
      f"ok {OUT['X2_lowering_vs_ram_meshes']['ok']}  ({time.time() - T0:.1f} s)", flush=True)
for q in x2[:14]:
    print("    ", q, flush=True)

json.dump(OUT, open(os.path.join(T4, "obal_work", "slide_checks.json"), "w"), indent=1)
t = time.time()
x3 = []; n3 = 0
for tag, sgn in (("L", -1), ("P", 1)):
    stat = ["T_stred", "T_dvere"] + [n for n in have if not n.startswith(("vl_F8_", "skr_F1_", "skr_F2_", "skr_F6"))
                                     and pts_of(n)[:, 2].max() > C.Z_WHITE + 0.3]
    # declared sliding fits: seam lip under the band edge (0.15), lower edge on the cap spigot (0.2): for those partners only
    # cap points deeper than 4.4 mm below the exterior are tested (= socket tube and seat flange)
    r, k = slide(["T_bok_" + tag], stat, 0, sgn, lambda b: 0.0 if b == "T_ram" else 0.3,
                 lambda n, b: deep44 if b in ("T_stred", "T_dvere", "T_spodok") else None)
    x3 += r; n3 += k
x3.sort(key=lambda q: q["plan_gap"] - q["required"])
OUT["X3_cap_slide_vs_meshes"] = dict(
    pairs=n3, closest=x3[:25], ok=all(q["ok"] for q in x3),
    note="T_bok_L along -X / T_bok_P along +X over T_stred, T_dvere and the RAM STLs.  Required plan clearance 0.3; against T_ram 0 "
         "(the seat flange lands on the stop-ring face; a negative-gap finding there would be a real collision).  Sliding fits (seam "
         "lip, cap spigot) excluded.")
print(f"X3 cap slide: {n3} pairs, {len(x3)} near pairs, ok {OUT['X3_cap_slide_vs_meshes']['ok']}  ({time.time() - t:.1f} s)", flush=True)
for q in x3[:14]:
    print("    ", q, flush=True)
json.dump(OUT, open(os.path.join(T4, "obal_work", "slide_checks.json"), "w"), indent=1)
print("done", round(time.time() - T0, 1))
