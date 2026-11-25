"""K2: where can a servo with its shaft parallel to X (pointing OUT of the torso) sit in the 'hard' free map?
envelope (servo local: a along the shaft, s along the case length L, w along the width W; shaft at s = w = 0, a = 0 at the
output face of the case): case a in [-Hc, 0] x s in [-e, L - e] x w in [-W/2, W/2]; boss + drum cylinder r_d for a in [0, a_d]
usage: place.py side Hc r_d a_d"""
import sys, json, numpy as np
from scipy.signal import fftconvolve
side = sys.argv[1] if len(sys.argv) > 1 else "L"
Hc = float(sys.argv[2]) if len(sys.argv) > 2 else 21.5
r_d = float(sys.argv[3]) if len(sys.argv) > 3 else 5.0
a_d = float(sys.argv[4]) if len(sys.argv) > 4 else 5.5
L, W, e = 23.2, 12.1, 5.9
D = np.load("/tmp/claude-0/gapwf/fin/R1/trup_servo/map1.npz"); lo, H, n = D["lo"], float(D["h"]), D["n"]
F = np.load("/tmp/claude-0/gapwf/fin/R1/K2_dole_remen/hard.npz")["free_h"]
lower = D["lower"]
X = lo[0] + (np.arange(n[0]) + 0.5) * H
if side == "L":
    i0 = np.searchsorted(X, 0.0); Fs = F[i0:]; Ls = lower[i0:]; Xs = X[i0:]; sgn = 1
else:
    i1 = np.searchsorted(X, 0.0); Fs = F[:i1][::-1]; Ls = lower[:i1][::-1]; Xs = -X[:i1][::-1]; sgn = -1   # mirrored: x -> -x
Y = lo[1] + (np.arange(n[1]) + 0.5) * H; Z = lo[2] + (np.arange(n[2]) + 0.5) * H
blocked = (~Fs).astype(np.float32)
res = []
for orient in ("sY+", "sY-", "sZ+", "sZ-"):
    # stencil in (a, s, w) -> grid (x, y, z) offsets relative to the shaft point on the output face
    A = np.arange(-Hc, a_d + 1e-9, H / 1.0)
    pts = []
    ag = np.arange(-Hc + H / 2, a_d, H)
    sg = np.arange(-e + H / 2, L - e, H); wg = np.arange(-W / 2 + H / 2, W / 2, H)
    AA, SS, WW = np.meshgrid(ag, sg, wg, indexing="ij")
    case = (AA <= 0)
    rr = np.hypot(SS, WW)
    cyl = (AA > 0) & (rr <= r_d)
    sg2 = np.arange(-r_d + H / 2, r_d, H)
    AA2, SS2, WW2 = np.meshgrid(ag[ag > 0], sg2, sg2, indexing="ij")
    cyl2 = np.hypot(SS2, WW2) <= r_d
    P = np.concatenate([np.stack([AA[case], SS[case], WW[case]], 1), np.stack([AA2[cyl2], SS2[cyl2], WW2[cyl2]], 1)])
    # map to (x, y, z)
    if orient[1] == "Y":
        dy = P[:, 1] * (1 if orient[2] == "+" else -1); dz = P[:, 2]
    else:
        dz = P[:, 1] * (1 if orient[2] == "+" else -1); dy = P[:, 2]
    dx = P[:, 0]
    I = np.round(np.stack([dx, dy, dz], 1) / H).astype(int)
    mn = I.min(0); mx = I.max(0)
    K = np.zeros(tuple(mx - mn + 1), np.float32); K[tuple((I - mn).T)] = 1.0
    # count blocked voxels under the stencil placed with its origin at each voxel: correlation
    Kf = K[::-1, ::-1, ::-1]
    cnt = fftconvolve(blocked, Kf, mode="full")
    # origin (stencil index -mn) at voxel v: sum_k blocked[v + I_k] ; full conv index = v + (mx - mn) - (-mn) ... compute directly
    off = mx  # for 'full' mode with flipped kernel: out[v + mx] = sum blocked[v + I]
    sl = tuple(slice(off[i], off[i] + Fs.shape[i]) for i in range(3))
    c = cnt[sl]
    ok = c < 0.5
    # also report: does the case overlap the T5 lowering path (servo must then go in after T_stred, from the side)
    idx = np.argwhere(ok)
    for (ix, iy, iz) in idx:
        res.append((orient, float(Xs[ix]), float(Y[iy]), float(Z[iz])))
print(side, "Hc", Hc, "r_d", r_d, "a_d", a_d, "feasible placements:", len(res))
import collections
by = collections.defaultdict(list)
for o, x, y, z in res: by[o].append((x, y, z))
for o, v in by.items():
    v = np.array(v)
    print(o, len(v), "x_face range %.1f..%.1f" % (v[:, 0].min(), v[:, 0].max()))
    # max x_face placements
    for xf in sorted(set(np.round(v[:, 0], 2)))[-6:]:
        q = v[np.abs(v[:, 0] - xf) < 1e-6]
        print("   x_face %.2f: y %.1f..%.1f  z %.1f..%.1f  (%d)" % (xf, q[:, 1].min(), q[:, 1].max(), q[:, 2].min(), q[:, 2].max(), len(q)))
json.dump([dict(o=o, x=x * sgn, y=y, z=z) for o, x, y, z in res], open(f"/tmp/claude-0/gapwf/fin/R1/K2_dole_remen/place_{side}_{Hc}_{r_d}.json", "w"))
