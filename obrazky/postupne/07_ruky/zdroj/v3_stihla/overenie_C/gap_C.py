"""overenie_C/gap_C.py - verifier's OWN arm-torso gap of shape variant C (and 0 for validation).
Method (different from the designer's / judge's armgap_top.py, which samples the TORSO on a y-z grid and queries an arm SDF):
  * torso = approved T4 exterior (t4_common PD/PA/PB/PN superellipse loft), sampled in (drop, azimuth) with ~0.07 mm
    spacing on the left side (x > 36); socket model 'rec1' as the judge: side cap kept for r >= 14 about the shoulder axis,
    cap edge r 14 densely sampled, plug face r <= 13.5 recessed 1.0, annulus 13.5..14 void;
  * arm = own geomC surface cloud (adaptive rows <= 0.06 mm, theta 0.05 mm), world placement armgeo kt 1 dx -1;
  * for every swing angle: arm cloud rotated about the shoulder axis; coarse torso tree (0.35 mm) picks the candidate arm
    points, the fine torso tree gives the distance; sign from the analytic torso inside test.
usage: /opt/venv/cad/bin/python gap_C.py [C|0]"""
import sys, os, math, json, time
sys.dont_write_bytecode = True
import numpy as np
from scipy.spatial import cKDTree
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T4")
import geomC as G
import t4_common as T

YA, ZA = 3.0, -17.0
TOP = T.TOP


def torso_cloud(h):
    PD, PA, PB, PN = T.PD, T.PA, T.PB, T.PN
    arc = np.concatenate([[0.0], np.cumsum(np.hypot(np.diff(PD), np.maximum(np.abs(np.diff(PA)), np.abs(np.diff(PB)))))])
    t = np.linspace(0, arc[-1], int(arc[-1] / h) + 1)
    d = np.interp(t, arc, PD)
    out = []
    for dd in d:
        a, b, n = T.prof(dd)
        per = 4 * (a + b)
        N = int(per / h)
        th = np.linspace(-np.pi / 2, np.pi / 2, N // 2)          # right half of the section (x >= 0)
        r = T.se_r(a, b, n, th)
        x, y = r * np.cos(th), r * np.sin(th)
        k = x > 36.0
        out.append(np.c_[x[k], y[k], np.full(k.sum(), TOP - dd)])
    return np.concatenate(out)


def x_surf(y, z):
    """approved exterior |x| at (y, z) (vectorised)"""
    drop = TOP - np.asarray(z, float)
    a = np.interp(drop, T.PD, T.PA); b = np.interp(drop, T.PD, T.PB); n = np.interp(drop, T.PD, T.PN)
    q = np.clip(np.abs(y) / b, 0, 1)
    return a * (1 - q ** n) ** (1 / n)


def build_torso(h):
    S0 = torso_cloud(h)
    ra = np.hypot(S0[:, 1] - YA, S0[:, 2] - ZA)
    cap = S0[ra >= 14.0]
    disc = S0[ra <= 13.5].copy(); disc[:, 0] -= 1.0
    th = np.linspace(0, 2 * np.pi, int(2 * np.pi * 14 / (h / 2)), endpoint=False)
    ry, rz = YA + 14 * np.cos(th), ZA + 14 * np.sin(th)
    rim = np.c_[x_surf(ry, rz), ry, rz]
    lab = np.r_[np.zeros(len(cap), int), np.ones(len(rim), int), np.full(len(disc), 2)]
    return np.r_[cap, rim, disc], lab


def torso_inside(Q):
    ra = np.hypot(Q[:, 1] - YA, Q[:, 2] - ZA)
    xs = x_surf(Q[:, 1], Q[:, 2])
    lim = np.where(ra >= 14.0, xs, np.where(ra <= 13.5, xs - 1.0, xs - 50.0))
    return (Q[:, 0] < lim) & (Q[:, 2] < TOP) & (Q[:, 2] > T.Z_BOT)


def main(vid="C"):
    t0 = time.time()
    shp = G.SHAPE_C if vid == "C" else G.SHAPE_0
    TS, lab = build_torso(0.07)
    TM, _ = build_torso(0.15)
    TC, _ = build_torso(0.35)
    tf, tm, tc = cKDTree(TS), cKDTree(TM), cKDTree(TC)
    A = shp.cloud(0.0, 1.0, 0.06, 0.05)
    W = G.to_world(A)
    keep = W[:, 0] < 60.0                     # x is invariant under the swing; the torso is at |x| <= 52.5
    Al, W = A[keep], W[keep]
    print(f"torso {len(TS)} pts, arm {len(W)} pts ({time.time() - t0:.0f} s)", flush=True)
    angs = np.unique(np.r_[np.arange(-51.0, 125.0, 1.0), np.arange(125.0, 142.01, 0.5), 140.5])
    res = {}
    for a in angs:
        Q = G.swing(W, a)
        dc, _ = tc.query(Q, distance_upper_bound=10.0, workers=3)
        c1 = np.nonzero(dc < dc.min() + 0.45)[0]
        dm, _ = tm.query(Q[c1], distance_upper_bound=float(dc.min()) + 0.5, workers=3)
        c2 = c1[dm < dm.min() + 0.15]
        df, idx = tf.query(Q[c2], distance_upper_bound=float(dm.min()) + 0.2, workers=3)
        ins = torso_inside(Q[c2])
        sd = np.where(ins, -df, df)
        k = int(np.argmin(sd))
        ci = c2[k]
        u = float(-Al[ci, 2] / G.L)
        c, ti, to, w = (float(v) for v in shp.sec(u))
        res[float(a)] = dict(gap=round(float(sd[k]), 3), n_cand=[len(c1), len(c2)], arm_pt_world_rest=W[ci].round(2).tolist(),
                             arm_u=round(u, 3), arm_y_over_w=round(float(Al[ci, 1] / w), 2),
                             arm_side="inner" if Al[ci, 0] < c else "outer",
                             torso_pt=TS[idx[k]].round(2).tolist(), torso_part=["cap", "rim", "plug face"][lab[idx[k]]])
        if a % 10 == 0 or a >= 130:
            print(a, res[float(a)]["gap"], res[float(a)]["n_cand"], f"{time.time() - t0:.0f}s", flush=True)
    g = {a: v["gap"] for a, v in res.items()}
    sw = {a: v for a, v in g.items() if -45.0 <= a <= 135.0}
    amin = min(sw, key=sw.get)
    out = dict(variant=vid, rest=g[0.0], rest_detail=res[0.0], min_m45_135=sw[amin], min_angle=amin, min_detail=res[amin],
               at_135=g[135.0], at_140p5=g[140.5], at_m51=g[-51.0], min_m51_142=min(g.values()),
               per_10deg={str(int(a)): g[a] for a in g if a % 10 == 0}, all=g, time_s=round(time.time() - t0, 1))
    print(json.dumps({k: v for k, v in out.items() if k != "all"}, indent=1))
    json.dump(out, open(os.path.join(HERE, f"gap_{vid}.json"), "w"), indent=1)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "C")
