"""Extent of the feasible region for an UPRIGHT SCS0009 (shaft along Z, long side along Y, width along X) in the K1 model,
with the case alone (23.2 x 12.1 x 21.5) and with the case + 1.2 pocket wall on the 4 sides + 3.75 above for boss/spline.
Prints the feasible centre box and the shaft candidates (shaft 5.9 from either Y end, on the X centre line)."""
import sys, os
import numpy as np
from scipy.signal import fftconvolve
HERE = "/tmp/claude-0/gapwf/fin/R1/K1_roh_kolesa"
VAR = sys.argv[1] if len(sys.argv) > 1 else ""
D = np.load(os.path.join(HERE, f"k1_hard{VAR}.npz")); lo, h = D["lo"], float(D["h"]); n = np.array(D["n"])
bad = ((D["ds"] < 0.55) | (D["dm"] < 1.25)).astype(np.float32)
for tag, (dx, dy, dz, ztop) in {"bare case": (12.1, 23.2, 21.5, 0.0), "case+wall1.2+spline": (14.5, 25.6, 21.5, 3.75)}.items():
    g = np.stack(np.meshgrid(np.arange(-dx / 2, dx / 2 + 1e-9, .25), np.arange(-dy / 2, dy / 2 + 1e-9, .25),
                             np.arange(-dz / 2, dz / 2 + ztop + 1e-9, .25), indexing="ij"), -1).reshape(-1, 3)
    I = np.unique(np.round(g / h).astype(int), axis=0); mn = I.min(0); mx = I.max(0)
    ker = np.zeros(mx - mn + 1, np.float32); ker[tuple((I - mn).T)] = 1
    c = fftconvolve(bad, ker[::-1, ::-1, ::-1], mode="full")
    sh = np.array(ker.shape); idx0 = -mn - (sh - 1); j0 = np.maximum(-idx0, 0)
    sub = c[j0[0]:j0[0] + n[0], j0[1]:j0[1] + n[1], j0[2]:j0[2] + n[2]]
    o = np.argwhere(sub < 0.5) + j0 + idx0
    o = o[np.all((o + mn >= 0) & (o + mx < n), axis=1)]
    P = lo + (o + .5) * h
    print(tag, "feasible centres", len(P))
    if len(P):
        print("  centre x %.1f..%.1f  y %.1f..%.1f  z %.1f..%.1f" % (P[:, 0].min(), P[:, 0].max(), P[:, 1].min(), P[:, 1].max(), P[:, 2].min(), P[:, 2].max()))
        for s in (+1, -1):
            sy = P[:, 1] + s * (dy / 2 - 5.9 - (1.2 if "wall" in tag else 0))
            top = P[:, 2] + 10.75
            d = np.hypot(sy - 3.0, top + 17.0)
            k = d.argmin()
            print("  shaft at the %s end: closest to the shoulder axis: shaft (x %.1f, y %.1f), case top z %.1f, |dy| %.1f, dz %.1f; shaft x range %.1f..%.1f"
                  % ("+Y" if s > 0 else "-Y", P[k, 0], sy[k], top[k], abs(sy[k] - 3), top[k] + 17, P[:, 0].min(), P[:, 0].max()))
