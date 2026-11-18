"""post-processing: true-surface stresses of P_sachta (sampled STL points), region maxima (raw + 0.4 mm averaged), bond tractions
gear <-> well, pocket <-> well interface forces.  Usage: python post.py case [case ...] -> res/<case>_post.json"""
import sys, json, math, numpy as np
from scipy.spatial import cKDTree
import os
import fe3d, fe_build as FB
VAR = os.environ.get("VARIANT", "")
RES = "res" if not VAR else "res_" + VAR
if VAR == "v2":
    src = open("fe_cases_v2.py").read().split("FB.build = build")[0]
    exec(compile(src, "v2", "exec"))
    m = build(assemble=False)
else:
    m = FB.build(assemble=False)
X = m.X; nb = m.node_body
SP = np.load("surf_pts.npz"); P, N = SP["P"], SP["N"]
x, y, z = P[:, 0], P[:, 1], P[:, 2]; R = np.hypot(x, y)
# ---- regions (priority order)
reg = np.full(len(P), "", dtype=object)
def put(name, cond):
    free = reg == ""
    reg[free & cond] = name
put("drum shroud / lip", z < -41.88)
put("journal band / ring / top plate", z > -10.6)
put("rail (lips, groove)", (y > 13.0) & (z < -33.6) & (x > -6.6) & (x < 16.6))
put("F10 pads", (y > 13.0) & (z >= -33.6) | ((y > 13.0) & (x > 15.9)))
put("floor-wall junction (inside, z<-39)", (z < -39.0) & (z > -40.9) & ((np.abs(y) > 9.4) & (np.abs(y) <= 11.05) | (np.abs(x) > 21.9) & (np.abs(x) <= 23.55)))
put("hub disc ring", (z <= -40.5) & (R >= 6.3) & (R <= 12.75) & (np.abs(y) < 11.0))
put("back floor", (z <= -40.5) & (y >= 3.0))
put("corner arcs (1.34)", (np.abs(x) > 20.9) & (np.abs(y) > 8.4) & (R > 22.5))
put("+X end wall / pillar", x > 22.9)
put("-X end wall", x < -22.9)
put("front wall", y < -10.9)
put("back wall", y > 10.9)
put("other", np.ones(len(P), bool))
REG = sorted(set(reg.tolist()))
tree = cKDTree(P)
nbrs = tree.query_ball_point(P[::1], r=0.4) if False else None


def smooth(v, r=0.4, idx=None):
    """average of v over points within r (only for the candidate points idx)"""
    out = np.full(len(idx), np.nan)
    for k, i in enumerate(idx):
        nn = tree.query_ball_point(P[i], r)
        out[k] = np.nanmean(v[nn])
    return out


def internal_forces(U, body):
    b = m.bodies[[q["name"] for q in m.bodies].index(body)]
    K0, _, _ = fe3d.element(m.h, b["nu"])
    en = b["enodes"]
    ue = np.stack([U[3 * en], U[3 * en + 1], U[3 * en + 2]], 2).reshape(len(en), 24)
    fe = ue @ K0.T
    if len(b.get("part", [])):
        fe[b["part"]] = np.einsum("nij,nj->ni", b["Kpart"], ue[b["part"]])
    fe *= b["E"]
    f = np.zeros((m.nn, 3))
    for a in range(8):
        for c in range(3):
            np.add.at(f[:, c], en[:, a], fe[:, 3 * a + c])
    return f


def pair_forces(U):
    key = lambda P: np.round(P / FB.H).astype(np.int64) @ np.array([1 << 40, 1 << 20, 1])
    w_ids = np.flatnonzero(nb == 0); p_ids = np.flatnonzero(nb == 2)
    common, iw, ip = np.intersect1d(key(X[w_ids] - FB.O), key(X[p_ids] - FB.O), return_indices=True)
    A, B = w_ids[iw], p_ids[ip]; P = X[A]
    face = FB.pocket_face_fn(P)
    dow = (np.hypot(P[:, 0] - 18.4, P[:, 2] + 38.0) <= 1.45) & (P[:, 1] >= 11.9) & (P[:, 1] <= 17.3)
    tong = (P[:, 0] >= -4.3) & (P[:, 0] <= 14.3) & (P[:, 1] >= 13.4) & (P[:, 1] <= 15.2) & ((np.abs(P[:, 2] + 36.4) <= 0.25) | (np.abs(P[:, 2] + 39.4) <= 0.25))
    k = 20.0 * FB.E_RESIN * FB.H
    du = U.reshape(-1, 3)[B] - U.reshape(-1, 3)[A]           # pocket minus well: force on the pocket = -k du.d d
    out = {}
    padA = face & (np.hypot(P[:, 0] - 7.0, P[:, 2] + 15.8) < 4.0); padB = face & (P[:, 0] > 14.0) & (P[:, 2] > -39.5); rail = face & ~padA & ~padB
    for nm, msk, d in (("padA_y", padA, 1), ("padB_y", padB, 1), ("rail_face_y", rail, 1), ("dowel_x", dow, 0), ("dowel_z", dow, 2), ("tongue_z", tong, 2)):
        f = -k * du[msk, d]
        out[nm] = dict(sum=round(float(f.sum()), 2), tension=round(float(f[f > 0].sum()), 2) if d == 1 else None, n=int(msk.sum()))
    return out


def run(case):
    U = np.load(f"{RES}/{case}.npz")["U"].astype(np.float64)
    sig, ok, el = fe3d.point_stress_fc(m, U, "well", P, N)
    s1, s2, s3, vm = fe3d.principal(np.nan_to_num(sig))
    s1[~ok] = np.nan; s3[~ok] = np.nan; vm[~ok] = np.nan
    out = dict(case=case, n_points=int(len(P)), n_ok=int(ok.sum()), regions={})
    for rn in REG:
        msk = (reg == rn) & ok
        if not msk.any():
            continue
        ii = np.flatnonzero(msk)
        top = ii[np.argsort(-s1[ii])[:60]]
        sm = smooth(s1, 0.4, top)
        k = int(np.nanargmax(sm)); i_raw = ii[np.nanargmax(s1[ii])]
        topc = ii[np.argsort(s3[ii])[:60]]; smc = smooth(s3, 0.4, topc); kc = int(np.nanargmin(smc))
        out["regions"][rn] = dict(s1_raw=round(float(s1[i_raw]), 3), at_raw=[round(float(v), 2) for v in P[i_raw]],
                                  s1_avg04=round(float(sm[k]), 3), at=[round(float(v), 2) for v in P[top[k]]],
                                  s3_avg04=round(float(smc[kc]), 3), at_s3=[round(float(v), 2) for v in P[topc[kc]]],
                                  vm_max=round(float(np.nanmax(vm[ii])), 3), n=int(len(ii)))
    # bond tractions: force of the well on the gear at the merged nodes (gear internal force)
    fg = internal_forces(U, "gear")
    bond = np.flatnonzero((nb == 0) & (np.abs(X[:, 2] + 41.9) < 1e-6) & (np.linalg.norm(fg, axis=1) > 0) & (np.hypot(X[:, 0], X[:, 1]) > 5.0))
    fb = fg[bond]; Ab = m.h ** 2
    tz = fb[:, 2] / Ab; ts = np.hypot(fb[:, 0], fb[:, 1]) / Ab
    # smoothed over 0.8 mm (3 x 3 nodes)
    bt = cKDTree(X[bond, :2])
    tz_s = np.array([tz[bt.query_ball_point(X[i, :2], 0.6)].mean() for i in bond])
    ts_s = np.array([ts[bt.query_ball_point(X[i, :2], 0.6)].mean() for i in bond])
    out["bond"] = dict(n_nodes=int(len(bond)), F_total=[round(float(v), 2) for v in fb.sum(0)],
                       peel_max_node=round(float(tz.max()), 3), peel_max_avg=round(float(tz_s.max()), 3), at_peel=[round(float(v), 2) for v in X[bond[np.argmax(tz_s)]]],
                       comp_max_avg=round(float(-tz_s.min()), 3), shear_max_node=round(float(ts.max()), 3), shear_max_avg=round(float(ts_s.max()), 3),
                       at_shear=[round(float(v), 2) for v in X[bond[np.argmax(ts_s)]]],
                       torque_about_z=round(float((X[bond, 0] * fb[:, 1] - X[bond, 1] * fb[:, 0]).sum()), 1))
    # pocket <-> well interface (force of the well on the pocket at merged nodes on y 15.1)
    if VAR == "v2":
        out["pocket_if"] = pair_forces(U)
        out["max_disp"] = round(float(np.abs(U).max()), 4)
        json.dump(out, open(f"{RES}/{case}_post.json", "w"), indent=1)
        np.savez_compressed(f"{RES}/{case}_surf.npz", s1=s1.astype(np.float32), s3=s3.astype(np.float32), vm=vm.astype(np.float32))
        print(case, json.dumps(out)[:3000], flush=True)
        return
    fp = internal_forces(U, "pocket")
    pi = np.flatnonzero((nb == 0) & (np.abs(X[:, 1] - 15.1) < 1e-6) & (np.linalg.norm(fp, axis=1) > 0))
    groups = dict(padA=np.hypot(X[pi, 0] - 7.0, X[pi, 2] + 15.8) < 4.0, padB=(X[pi, 0] > 14.0) & (X[pi, 2] > -39.5),
                  rail=(X[pi, 2] < -33.8) & ~((X[pi, 0] > 14.0) & (X[pi, 2] > -39.5)))
    out["pocket_if"] = {k: [round(float(v), 2) for v in fp[pi[g]].sum(0)] for k, g in groups.items()}
    out["max_disp"] = round(float(np.abs(U).max()), 4)
    json.dump(out, open(f"{RES}/{case}_post.json", "w"), indent=1)
    np.savez_compressed(f"{RES}/{case}_surf.npz", s1=s1.astype(np.float32), s3=s3.astype(np.float32), vm=vm.astype(np.float32))
    print(case, json.dumps(out)[:4000], flush=True)


if __name__ == "__main__":
    for c in sys.argv[1:]:
        run(c)
