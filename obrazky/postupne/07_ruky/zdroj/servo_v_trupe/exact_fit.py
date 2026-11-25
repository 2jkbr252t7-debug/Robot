"""STEP 2 helper - EXACT check of the closest voxel pose(s) of a servo case in the front-left torso pocket and a local 6-DOF
optimisation of the case pose (maximise the worst margin).  Margin of a case-surface point:
    static : exact distance to the STL triangles of every static T part near the pocket - 0.3   (negative inside a part)
    moving : r - (PAN_ENV2 radius of the z band, incl. the stop-lug / lift-module-bottom sectors, +-1.0 in z) - 1.0
             and the pan-FFC duct annulus (r 15.2..25.1, z -46.2..-41.9)
    shell  : covered by T_stred / T_bok_L / T_dvere in the static set
Case = box L x W x H (no shaft, no ears, no cable).  Usage: exact_fit.py <L> <W> <H> <cx> <cy> <cz> <rotvec_x> <rotvec_y> <rotvec_z>
Prints the worst margin before / after optimisation and the limiting parts.  Writes exact_fit_<tag>.json."""
import sys, os, json, math
sys.dont_write_bytecode = True
import numpy as np
from scipy.optimize import minimize
from scipy.spatial.transform import Rotation as Rot
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import voxlib as V  # noqa: E402

PJ = json.load(open(os.path.join(V.T4, "parts.json")))
REG = dict(x=(5.0, 53.0), y=(-41.0, 0.0), z=(-86.0, -25.0))
NEAR = []
for p in PJ["parts"]:
    if p["group"] != "T":
        continue
    b = p["bbox"]
    if b[1] < REG["x"][0] or b[0] > REG["x"][1] or b[3] < REG["y"][0] or b[2] > REG["y"][1] or b[5] < REG["z"][0] or b[4] > REG["z"][1]:
        continue
    NEAR.append(p["name"])
MESH = {n: V.vlib.Mesh(V.load(n)) for n in NEAR}
ENV = [(-47.20, -41.90, 17.50), (-41.90, -40.90, 26.50), (-40.90, -17.00, 33.40), (-17.00, -11.50, 32.20), (-11.50, 4.00, 26.50)]
SECT = [((-47.20, -39.90), 31.60, (16.5, 222.0)), ((-41.90, -40.90), 33.40, (-55.0, 230.0))]


def r_env(z, az):
    r = np.zeros_like(z)
    for z0, z1, rr in ENV:
        m = (z >= z0 - 1.0) & (z <= z1 + 1.0); r[m] = np.maximum(r[m], rr)
    for (z0, z1), rr, (a0, a1) in SECT:
        a = (az - a0) % 360.0
        m = (z >= z0 - 1.0) & (z <= z1 + 1.0) & (a <= (a1 - a0) % 360.0 + 1e-9)
        r[m] = np.maximum(r[m], rr)
    return r


def box_surface(L, W, Hh, h=0.6):
    P = []
    for ax in range(3):
        d = np.array([L, W, Hh]); o = [k for k in range(3) if k != ax]
        u = np.arange(-d[o[0]] / 2, d[o[0]] / 2 + 1e-9, h); v = np.arange(-d[o[1]] / 2, d[o[1]] / 2 + 1e-9, h)
        U, Vv = np.meshgrid(u, v, indexing="ij")
        for s in (-1, 1):
            Q = np.zeros((U.size, 3)); Q[:, ax] = s * d[ax] / 2; Q[:, o[0]] = U.ravel(); Q[:, o[1]] = Vv.ravel()
            P.append(Q)
    return np.concatenate(P)


def margins(Pw, detail=False):
    worst = {}
    m_all = np.full(len(Pw), 1e9)
    for n, M in MESH.items():
        bb = M.bb
        near = np.all((Pw >= bb[:3] - 3.0) & (Pw <= bb[3:] + 3.0), axis=1)
        if not near.any():
            continue
        d, _ = M.dist(Pw[near], dmax=3.5)
        d = np.where(np.isfinite(d), d, 3.5)
        ins = M.inside(Pw[near])
        s = np.where(ins, -d, d) - 0.3
        m_all[near] = np.minimum(m_all[near], s)
        worst[n] = float(s.min())
    r = np.hypot(Pw[:, 0], Pw[:, 1]); az = np.degrees(np.arctan2(Pw[:, 1], Pw[:, 0]))
    mv = r - r_env(Pw[:, 2], az) - 1.0
    duct = (r > 15.2 - 1) & (r < 25.1 + 1) & (Pw[:, 2] > -47.2) & (Pw[:, 2] < -40.9)
    mv = np.where(duct, np.minimum(mv, -1.0), mv)
    worst["<pan/lift sweep>"] = float(mv.min())
    m_all = np.minimum(m_all, mv)
    return (m_all, worst) if detail else m_all


def contained_parts(c, R, dims):
    """static parts with vertices INSIDE the case box (small parts the surface samples could miss)"""
    out = []
    for n, M in MESH.items():
        v = M.tr.reshape(-1, 3)
        q = (v - c) @ R
        if np.any(np.all(np.abs(q) < np.array(dims) / 2, axis=1)):
            out.append(n)
    return out


def pose_pts(x, S):
    c = x[:3]; R = Rot.from_rotvec(x[3:]).as_matrix()
    return S @ R.T + c, c, R


def run(L, W, Hh, x0, tag):
    S = box_surface(L, W, Hh)
    Pw, c, R = pose_pts(np.array(x0, float), S)
    m0, w0 = margins(Pw, True)
    print("start worst", round(float(m0.min()), 2), sorted(w0.items(), key=lambda kv: kv[1])[:5])

    def f(x):
        Pw, _, _ = pose_pts(x, S)
        m = margins(Pw)
        # soft-min: maximise the worst margin (with a smooth tail so the optimiser sees the second worst too)
        return -float(m.min()) - 0.05 * float(np.mean(np.minimum(m, 0.0)))

    best = minimize(f, np.array(x0, float), method="Nelder-Mead",
                    options=dict(xatol=0.05, fatol=0.01, maxiter=500, initial_simplex=None))
    Pw, c, R = pose_pts(best.x, S)
    m1, w1 = margins(Pw, True)
    inside = contained_parts(c, R, (L, W, Hh))
    res = dict(case=[L, W, Hh], start=list(map(float, x0)), start_worst=round(float(m0.min()), 2),
               opt_pose=dict(centre=[round(float(v), 2) for v in c], rotvec=[round(float(v), 4) for v in best.x[3:]],
                             axes_world={"L": [round(float(v), 3) for v in R[:, 0]], "W": [round(float(v), 3) for v in R[:, 1]],
                                         "H (shaft)": [round(float(v), 3) for v in R[:, 2]]}),
               opt_worst_margin=round(float(m1.min()), 2), per_part=dict(sorted(((k, round(v, 2)) for k, v in w1.items()), key=lambda kv: kv[1])[:8]),
               parts_with_vertices_inside_case=inside, n_eval=int(best.nfev),
               note="margin = clearance minus the required 0.3 (static) / 1.0 (moving); >= 0 means the case fits")
    print(json.dumps(res, indent=1))
    json.dump(res, open(os.path.join(HERE, f"exact_fit_{tag}.json"), "w"), indent=1)
    return res


if __name__ == "__main__":
    a = [float(v) for v in sys.argv[1:10]]
    run(a[0], a[1], a[2], a[3:9], sys.argv[10] if len(sys.argv) > 10 else "x")
