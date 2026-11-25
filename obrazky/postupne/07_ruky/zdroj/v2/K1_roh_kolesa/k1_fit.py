"""K1 - where can an SCS0009 sit with its shaft parallel to X (output toward +X), given the K1 obstacle model (k1_hard.npz)?
Voxel erosion (FFT convolution) of the 'bad' set (closer than 0.3 to HARD or 1.0 to MOVE, + half voxel) with the servo
envelope for every roll angle phi about X.  Envelope (local: l along the case from the shaft, w across, h along the shaft,
origin = shaft on the case top face):
   case      l -5.9..17.3, w +-6.05, h -21.5..0
   reserve   same footprint, h -25.25..-21.5   (case height unverified: room for a 25.25 case)
   ears      l -10.6..22.0, w +-6.05, h -8.0..-3.5 (existence unverified - reserved)
   cable     l 17.3..20.5, w +-3.0, h -21.5..-15.0
   boss      r 4.0, h 0..0.6
   pinion    r_tip + 0.2 (moving part: 0.5 to static in total), h 0.5..3.5        (optional, PIN=r_tip)
usage: k1_fit.py [PIN_r_tip] [mode]   mode 'all' (default) or 'pre5' (also avoid the T_stred lowering sweep)
Writes k1_fit_<pin>_<mode>.json: per phi the feasible origins closest to the shoulder axis (y 3, z -17)."""
import sys, os, json, time, math
sys.dont_write_bytecode = True
import numpy as np
from scipy.signal import fftconvolve
HERE = "/tmp/claude-0/gapwf/fin/R1/K1_roh_kolesa"
PIN = float(sys.argv[1]) if len(sys.argv) > 1 else 0.0
MODE = sys.argv[2] if len(sys.argv) > 2 else "all"
PARTS = sys.argv[3] if len(sys.argv) > 3 else "crec"   # c case r reserve e ears k cable
HC = float(sys.argv[4]) if len(sys.argv) > 4 else 21.5
VAR = sys.argv[5] if len(sys.argv) > 5 else ""
D = np.load(os.path.join(HERE, f"k1_hard{VAR}.npz"))
lo, h, n = D["lo"], float(D["h"]), tuple(D["n"])
bad = (D["ds"] < 0.3 + 0.25) | (D["dm"] < 1.0 + 0.25)
if MODE == "pre5":
    bad |= D["lower"]
AX = np.array([3.0, -17.0])


def env_pts(phi, step=0.25):
    el = np.array([math.cos(phi), math.sin(phi)]); ew = np.array([-math.sin(phi), math.cos(phi)])
    P = []

    def box(l0, l1, w0, w1, h0, h1):
        L, W, H = np.meshgrid(np.arange(l0, l1 + 1e-9, step), np.arange(w0, w1 + 1e-9, step), np.arange(h0, h1 + 1e-9, step),
                              indexing="ij")
        P.append(np.stack([L.ravel(), W.ravel(), H.ravel()], 1))

    def cyl(r, h0, h1):
        L, W, H = np.meshgrid(np.arange(-r, r + 1e-9, step), np.arange(-r, r + 1e-9, step), np.arange(h0, h1 + 1e-9, step),
                              indexing="ij")
        m = (L ** 2 + W ** 2 <= r * r)
        P.append(np.stack([L[m], W[m], H[m]], 1))
    if "K" in PARTS:      # KST X06: 20 x 7 x 16.6, shaft ~5 from one end (offset unverified)
        box(-5.0, 15.0, -3.5, 3.5, -16.6, 0.0); cyl(2.5, 0.0, 0.6)
    else:
        box(-5.9, 17.3, -6.05, 6.05, (-25.25 if "r" in PARTS else -HC), 0.0)
    if "e" in PARTS: box(-10.6, 22.0, -6.05, 6.05, -8.0, -3.5)
    if "k" in PARTS: box(17.3, 20.5, -3.0, 3.0, -HC, -HC + 6.5)
    cyl(4.0, 0.0, 0.6)
    if PIN > 0:
        cyl(PIN + 0.2, 0.5, 3.5)
    Q = np.concatenate(P)
    yz = Q[:, :1] * el + Q[:, 1:2] * ew
    return np.stack([Q[:, 2], yz[:, 0], yz[:, 1]], 1)       # (dx, dy, dz) from the origin


res = {}
t0 = time.time()
for phd in range(0, 360, 15):
    E = env_pts(math.radians(phd))
    I = np.round(E / h).astype(int)
    I = np.unique(I, axis=0)
    mn = I.min(0); mx = I.max(0)
    ker = np.zeros(mx - mn + 1, np.float32)
    ker[tuple((I - mn).T)] = 1.0
    # feasible origin o: for all k in kernel, bad[o + k] == 0  ->  correlation of bad with ker
    c = fftconvolve(bad.astype(np.float32), ker[::-1, ::-1, ::-1], mode="full")
    # index: full conv output index j corresponds to origin o = j + mn - (ker.shape-1) ... (correlation)
    sh = np.array(ker.shape)
    # correlation value at origin o = sum_k bad[o + mn + k'] ker[k'] ; full-conv index j = o + mn + sh - 1
    O = []
    idx0 = -mn - (sh - 1)          # o = j + idx0  ->  j = o - idx0
    j0 = np.maximum(-idx0, 0)
    sub = c[j0[0]:j0[0] + n[0], j0[1]:j0[1] + n[1], j0[2]:j0[2] + n[2]]
    # sub[a,b,c] is origin o = (a,b,c) + j0 + idx0
    feas = np.argwhere(sub < 0.5)
    o = feas + j0 + idx0
    ok = np.all((o + mn >= 0) & (o + mx < np.array(n)), axis=1)
    o = o[ok]
    P = lo + (o + 0.5) * h
    # keep origins whose shaft is not hopelessly far
    d = np.hypot(P[:, 1] - AX[0], P[:, 2] - AX[1])
    rec = dict(n_feasible=int(len(P)))
    if len(P):
        order = np.argsort(d)[:400]
        best = P[order]
        rec["best_d"] = round(float(d[order[0]]), 2)
        rec["best"] = [[round(float(v), 2) for v in p] + [round(float(dd), 2)] for p, dd in zip(best[:12], d[order[:12]])]
        # per case-top x: best d
        bx = {}
        for p, dd in zip(P, d):
            k = round(float(p[0]) * 2) / 2
            if k not in bx or dd < bx[k][0]:
                bx[k] = (round(float(dd), 2), round(float(p[1]), 2), round(float(p[2]), 2))
        rec["best_by_x"] = {str(k): v for k, v in sorted(bx.items()) if k >= 30}
    res[phd] = rec
    print(phd, rec.get("n_feasible"), rec.get("best_d"), rec.get("best", [None])[0], f"{time.time()-t0:.0f}s", flush=True)
json.dump(res, open(os.path.join(HERE, f"k1_fit_{PIN:g}_{MODE}_{PARTS}_{HC:g}_{VAR}.json"), "w"), indent=1)
