"""cover-magnet posts (v1/v2 design: D3x2 magnet in a printed post r 2.2, 2.4 deep each side of the 0.5 seam, post axis 3.5
inside the section outline, front + back) in the R4 arm variants with M2b:
  clear  = min distance post -> moving joint parts (drive / static, exact (x, r) profile distance, parts are revolved)
  back   = min Euclidean distance magnet pocket (r 1.6 = D3 + 0.2, depth 0.25 .. 2.35 from the seam centre) -> arm skin of
           its own half (own dense skin), required >= 1.2 (cover) / 1.6 (inner)
  inside = min distance post cylinder (r 2.2, 0.25 .. 2.65) -> skin (negative = breaks through)
post axis y = +-(w_half - 3.5) with that half's width (cover wo / inner wi), and also a common axis at the narrower half"""
import sys, json, math
sys.dont_write_bytecode = True
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R4/overenie_tvar"); import armsurf_own as AS
VB = AS.VB
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R3/mech"); import parts as PT
YA, ZA = 3.0, -17.0
mov = [p for p in PT.options()["M2b"]["parts"] if p.pebble and p.role in ("drive", "static")]


def sd2(X, P_):
    P_ = np.asarray(P_, float); ins = PT._inpoly(X, P_); d = np.full(len(X), 1e9)
    for i in range(len(P_)):
        A, B = P_[i], P_[(i + 1) % len(P_)]; AB = B - A
        t = np.clip(((X - A) @ AB) / max(AB @ AB, 1e-12), 0, 1); d = np.minimum(d, np.linalg.norm(X - (A + t[:, None] * AB), axis=1))
    return np.where(ins, -d, d)


def cyl(c, side, yax, z, r, s0, s1, n=40):
    th = np.linspace(0, 2 * np.pi, n, endpoint=False)
    out = []
    for s in np.linspace(s0, s1, 12):
        for rr in np.linspace(0, r, 5):
            out.append(np.c_[np.full(n, c + side * s), yax + rr * np.cos(th), z + rr * np.sin(th)])
    return np.concatenate(out)


OUT = {}
for vid in ["B0", "B1", "B2", "B3"]:
    S, lab, U = AS.cloud(vid, 0.05, 0.25, 0.6)
    trees = {1: cKDTree(S[lab >= 1]), -1: cKDTree(S[lab != 1])}
    rows = []
    for u in np.round(np.arange(0.34, 0.505, 0.01), 2):
        c, ti, to, wi, wo, ni, no = [float(np.ravel(v)[0]) for v in AS.secf(vid, np.array([u]))]
        z = -72 * u
        rec = dict(u=float(u))
        for mode in ("own", "common"):
            clear, back, inside = 1e9, {}, {}
            for side in (1, -1):
                wh = (wo if side == 1 else wi) if mode == "own" else min(wi, wo)
                for sy in (1, -1):
                    yax = sy * (wh - 3.5)
                    post = cyl(c, side, yax, z, 2.2, 0.25, 2.65)
                    W = VB.to_world(post, vid)
                    X = np.c_[W[:, 0], np.hypot(W[:, 1] - YA, W[:, 2] - ZA)]
                    for p in mov:
                        clear = min(clear, float(sd2(X, p.outline_xr()).min()))
                    pocket = cyl(c, side, yax, z, 1.6, 0.25, 2.35)
                    d, _ = trees[side].query(pocket)
                    ins = VB.inside_local(vid, pocket)
                    dd = np.where(ins, d, -d).min()
                    back[side] = min(back.get(side, 1e9), float(dd))
                    d2, _ = trees[side].query(post)
                    ins2 = VB.inside_local(vid, post)
                    inside[side] = min(inside.get(side, 1e9), float(np.where(ins2, d2, -d2).min()))
            rec[mode] = dict(clear_moving=round(clear, 3), back_cover=round(back[1], 3), back_inner=round(back[-1], 3),
                             post_in_skin_cover=round(inside[1], 3), post_in_skin_inner=round(inside[-1], 3))
        rows.append(rec)
    ok = [r["u"] for r in rows if r["own"]["clear_moving"] >= 0.3]
    OUT[vid] = dict(rows=rows, first_u_clear=min(ok) if ok else None)
    print(vid, "first u with clearance >= 0.3:", OUT[vid]["first_u_clear"])
    for r in rows:
        if 0.36 <= r["u"] <= 0.45:
            print("   ", r["u"], r["own"], "| common axis clear", r["common"]["clear_moving"])
json.dump(OUT, open("out/posts.json", "w"), indent=1)
