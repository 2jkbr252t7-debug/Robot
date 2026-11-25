"""STEP 2 helper - rotated servo-case placement search in the voxel map (left half x >= 12; the right half is a near mirror).
For each orientation (shaft || X, || Y or || Z, the case turned about the shaft in 7.5 deg steps) the case box is voxelised
(any touched voxel) and correlated (FFT) with the blocked mask; zero overlap = the case fits there.
Masks: 'cons_T5' = conservative free map minus the S1 lift-module path, the amp / buck paths and the side-cap (T13) insertion
paths, i.e. the case may be fitted AFTER T_stred (T5) from the open side (T_stred lowering path NOT applied);
'cons_pre' = same plus the T_stred lowering path (case fitted before T5, e.g. on T_spodok);
'opt_T5' = optimistic free map with the same assembly masks as cons_T5.
Writes search_b.json (per servo / mask: feasible orientations, centre ranges, best overlap)."""
import sys, os, json, math, time
sys.dont_write_bytecode = True
import numpy as np
from scipy import signal, ndimage as ndi
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import voxlib as V  # noqa: E402

t0 = time.time()
D = np.load(os.path.join(HERE, "map1.npz"))
lo, H = D["lo"], float(D["h"]); n = tuple(D["n"])
interior, static, moving, free = D["interior"], D["static"], D["moving"], D["free"]
lower, s1, amp, bokL, bokP = D["lower"], D["s1"], D["amp"], D["bokL"], D["bokP"]
free_opt = interior & ~static & ~moving
asm = s1 | amp | bokL | bokP
XMIN = float(os.environ.get("XMIN", "12.0"))
i0 = int((XMIN - lo[0]) / H)
MASKS = {"cons_T5": (free & ~asm)[i0:], "cons_pre": (free & ~asm & ~lower)[i0:], "opt_T5": (free_opt & ~asm)[i0:]}
LO = lo + np.array([i0 * H, 0, 0])
SERVOS = {"SCS0009 case 23.2x12.1x21.5": (23.2, 12.1, 21.5), "KST X06 20x7x16.6": (20.0, 7.0, 16.6)}
if len(sys.argv) > 1 and sys.argv[1] == "all":
    SERVOS.update({"MG90S case 22.8x12.2x22.7": (22.8, 12.2, 22.7), "STS3032 case 23.5x12.5x23": (23.5, 12.5, 23.0)})


def rot(axis, ang):
    a = math.radians(ang); c, s = math.cos(a), math.sin(a)
    if axis == 0:
        return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
    if axis == 1:
        return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def kernel(L, W, Hc, shaft_axis, psi):
    """box with Hc along the shaft axis, L / W turned by psi about it; returns kernel (bool) and its centre offset (voxels)"""
    if shaft_axis == 0:
        base = np.diag([1.0, 1.0, 1.0]); dims = np.array([Hc, L, W])
    elif shaft_axis == 1:
        dims = np.array([L, Hc, W])
    else:
        dims = np.array([L, W, Hc])
    Rm = rot(shaft_axis, psi)
    s = 0.2
    g1 = [np.arange(-d / 2, d / 2 + 1e-9, s) for d in dims]
    A, B, Cc = np.meshgrid(*g1, indexing="ij")
    P = np.stack([A.ravel(), B.ravel(), Cc.ravel()], 1) @ Rm.T
    ext = np.abs(P).max(0) + H
    nk = np.ceil(2 * ext / H).astype(int) + 1
    k = np.floor((P + ext) / H).astype(int)
    K = np.zeros(tuple(nk), np.float32)
    K[k[:, 0], k[:, 1], k[:, 2]] = 1.0
    return K, ext


out = {}
for sname, (L, W, Hc) in SERVOS.items():
    out[sname] = {}
    for mname, F in MASKS.items():
        B = (~F).astype(np.float32)
        rows = []
        for ax in (0, 1, 2):
            for psi in np.arange(0.0, 180.0, 7.5):
                K, ext = kernel(L, W, Hc, ax, psi)
                ov = signal.fftconvolve(B, K[::-1, ::-1, ::-1], mode="valid")
                okp = np.argwhere(ov < 0.5)
                best = float(ov.min())
                if len(okp):
                    c = LO + okp * H + ext          # centre of the box for kernel origin at voxel okp
                    rows.append(dict(shaft="xyz"[ax], psi=float(psi), n=int(len(okp)),
                                     centre_range=[[round(float(c[:, i].min()), 1), round(float(c[:, i].max()), 1)] for i in range(3)],
                                     example=[round(float(v), 1) for v in c[np.argmin(np.abs(c[:, 2] + 30))]]))
                else:
                    rows.append(dict(shaft="xyz"[ax], psi=float(psi), n=0, min_overlap_voxels=best))
        feas = [r for r in rows if r["n"]]
        out[sname][mname] = dict(feasible=len(feas), of=len(rows), rows=feas if feas else sorted(rows, key=lambda r: r["min_overlap_voxels"])[:5])
        print(sname, mname, "feasible orientations", len(feas), "/", len(rows),
              [(r["shaft"], r["psi"], r["centre_range"]) for r in feas[:6]], f"{time.time()-t0:.0f}s", flush=True)
json.dump(out, open(os.path.join(HERE, os.environ.get("OUT", "search_b.json")), "w"), indent=1)
print("done", f"{time.time()-t0:.0f}s")
