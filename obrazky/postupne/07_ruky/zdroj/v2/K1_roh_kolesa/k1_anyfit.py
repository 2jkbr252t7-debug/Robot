"""Does a bare SCS0009 case (23.2 x 12.1 x 21.5 box) fit ANYWHERE in the K1 obstacle model in any axis-aligned orientation
(all 6 permutations) and in 45-degree rolls about each axis?  FFT erosion, clearances 0.3 / 1.0 (+0.25).  usage: k1_anyfit.py <VAR>"""
import sys, os, itertools, math
import numpy as np
from scipy.signal import fftconvolve
from scipy.spatial.transform import Rotation as Rot
HERE = "/tmp/claude-0/gapwf/fin/R1/K1_roh_kolesa"
VAR = sys.argv[1] if len(sys.argv) > 1 else ""
D = np.load(os.path.join(HERE, f"k1_hard{VAR}.npz")); lo, h = D["lo"], float(D["h"]); n = np.array(D["n"])
bad = ((D["ds"] < 0.55) | (D["dm"] < 1.25)).astype(np.float32)
dims = np.array([23.2, 12.1, 21.5])
g = np.stack(np.meshgrid(*[np.arange(-d / 2, d / 2 + 1e-9, 0.25) for d in dims], indexing="ij"), -1).reshape(-1, 3)
rots = []
for ax in "xyz":
    for a in (0, 45, 90, 135):
        rots.append((ax, a))
rots += [("xy", (45, 45)), ("xz", (45, 45)), ("yz", (45, 45))]
best = None
for ax, a in rots:
    R = Rot.from_euler(ax, a, degrees=True)
    P = R.apply(g)
    I = np.unique(np.round(P / h).astype(int), axis=0); mn = I.min(0); mx = I.max(0)
    ker = np.zeros(mx - mn + 1, np.float32); ker[tuple((I - mn).T)] = 1
    c = fftconvolve(bad, ker[::-1, ::-1, ::-1], mode="full")
    sh = np.array(ker.shape); idx0 = -mn - (sh - 1); j0 = np.maximum(-idx0, 0)
    sub = c[j0[0]:j0[0] + n[0], j0[1]:j0[1] + n[1], j0[2]:j0[2] + n[2]]
    o = np.argwhere(sub < 0.5) + j0 + idx0
    o = o[np.all((o + mn >= 0) & (o + mx < n), axis=1)]
    mnv = float(sub.min())
    print(ax, a, "feasible centres", len(o), "least overlap (voxels)", round(mnv, 1),
          (lo + (o[0] + .5) * h).round(1).tolist() if len(o) else "", flush=True)
