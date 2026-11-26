"""Independent verifier (R3/overenie_B): arm - torso gap at rest and over the swing for shape variant(s), two torso models:
  ana : approved analytic torso exterior t4_common.x_surface (h 0.15), socket cap edge r 14, plug face r <= 13.5 recessed 1.0
        (final_B1plus: plug body r 13.5, face = approved surface - 1.0)  -> same physical model as the judge's 'rec1'
  stl : the REAL side-cover mesh T4/stl/T_bok_L.stl (barycentric samples h 0.15) + the same recessed plug face
Arm = own analytic surface sampling of variants.section (spacing 0.12, whole arm u 0..1) + analytic inside test (sign).
Swing -45..+135 in 1 deg steps (0.5 deg from 128), plus the stop angles -51 and +140.5 for information.
usage: own_gap.py <vids comma> -> gap_<vids>.json"""
import sys, os, math, json, time
sys.dont_write_bytecode = True
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import armsurf as AS  # noqa: E402
VA = AS.VA
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T4"); sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T4/overenie3")
import t4_common as C  # noqa: E402
import vlib  # noqa: E402

t0 = time.time()
vids = sys.argv[1].split(",") if len(sys.argv) > 1 else ["0", "B"]
YA, ZA = 3.0, -17.0
# ---------------------------------------------------------------- torso models
h = 0.15
ys = np.arange(-36.0, 38.0, h); zs = np.arange(-84.0, 3.95, h)
Y, Z = np.meshgrid(ys, zs, indexing="ij"); Y = Y.ravel(); Z = Z.ravel()
X = np.array([C.x_surface(y, z) for y, z in zip(Y, Z)])
ok = np.isfinite(X) & (X > 36.0)
S0 = np.c_[X[ok], Y[ok], Z[ok]]
ra = np.hypot(S0[:, 1] - YA, S0[:, 2] - ZA)
th = np.linspace(0, 2 * np.pi, 900, endpoint=False)
rim = np.c_[np.zeros_like(th), YA + 14.0 * np.cos(th), ZA + 14.0 * np.sin(th)]
rim[:, 0] = [C.x_surface(y, z) for y, z in rim[:, 1:]]
disc = S0[ra <= 13.5].copy(); disc[:, 0] -= 1.0
TOR = {"ana": np.r_[S0[ra >= 14.0], rim, disc]}
T = vlib.load_stl("/tmp/claude-0/gapwf/fin/T4/stl/T_bok_L.stl")
SB = vlib.sample_surface(T, 0.15)
SB = SB[SB[:, 0] > 36.0]
TOR["stl"] = np.r_[SB, disc]
# how well does the STL follow the analytic surface near the arm?
m = (np.abs(SB[:, 1] - YA) < 30) & (SB[:, 2] > -75) & (SB[:, 2] < 0) & (np.hypot(SB[:, 1] - YA, SB[:, 2] - ZA) > 14.5)
xa = np.array([C.x_surface(y, z) for y, z in SB[m][:, 1:]])
outer = SB[m][:, 0] > xa - 0.5
dev = SB[m][outer, 0] - xa[outer]
print("torso samples ana", len(TOR["ana"]), "stl", len(TOR["stl"]), "STL outer skin - analytic: max", round(float(dev.max()), 3),
      "min", round(float(dev.min()), 3), f"{time.time() - t0:.0f}s", flush=True)
ANG = np.unique(np.r_[np.arange(-45.0, 128.0, 1.0), np.arange(128.0, 135.01, 0.5), -51.0, 140.5])
OUT = dict(note=__doc__, stl_minus_analytic=[round(float(dev.min()), 3), round(float(dev.max()), 3)])
for vid in vids:
    arm = AS.ArmSurf(vid, 0.0, 1.0, 0.12)
    print(vid, "arm samples", len(arm.P), flush=True)
    Wloc_bb = (arm.P.min(0) - 6.0, arm.P.max(0) + 6.0)
    for tk, TQ in TOR.items():
        per = []
        for a in ANG:
            Ql = VA.to_local(VA.swing(TQ, -a), vid, -1.0)
            mm = np.all((Ql >= Wloc_bb[0]) & (Ql <= Wloc_bb[1]), axis=1)
            Pq = Ql[mm]
            if not len(Pq):
                per.append((a, 6.0, None)); continue
            ins = arm.inside(Pq)
            dc, kc = arm.dist(Pq, "cover", dmax=6.0)
            di, ki = arm.dist(Pq, "inner", dmax=6.0)
            d = np.minimum(dc, di)
            sd = np.where(ins, -d, d)
            j = int(np.argmin(sd))
            q = TQ[mm][j]
            per.append((float(a), float(sd[j]), dict(torso_pt=q.round(2).tolist(), arm_u=round(float(-Pq[j, 2] / VA.L), 3),
                                                     arm_side="cover" if dc[j] < di[j] else "inner")))
        aa = np.array([p[0] for p in per]); gg = np.array([p[1] for p in per])
        rng = (aa >= -45) & (aa <= 135)
        k = int(np.argmin(np.where(rng, gg, 1e9)))
        r = dict(rest=round(float(gg[aa == 0][0]), 3), rest_at=per[int(np.nonzero(aa == 0)[0][0])][2],
                 min_m45_135=round(float(gg[k]), 3), min_angle=float(aa[k]), min_at=per[k][2],
                 at_m45=round(float(gg[aa == -45][0]), 3), at_135=round(float(gg[aa == 135][0]), 3),
                 at_stop_m51=round(float(gg[aa == -51][0]), 3), at_stop_140p5=round(float(gg[aa == 140.5][0]), 3),
                 per_10deg={str(int(x)): round(float(v), 3) for x, v in zip(aa, gg) if abs(x % 10) < 1e-9})
        OUT[f"{vid} {tk}"] = r
        print(vid, tk, json.dumps({kk: vv for kk, vv in r.items() if kk != "per_10deg"}), f"{time.time() - t0:.0f}s", flush=True)
json.dump(OUT, open(os.path.join(HERE, "gap_%s.json" % "".join(vids)), "w"), indent=1)
print("done", f"{time.time() - t0:.0f}s")
