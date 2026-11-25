"""STEP 2 helper (complete orientation set) - like search_b.py but every case dimension (L, W, H) is put along each global axis
(9 families) and turned about it in 15 deg steps (108 orientations) + 120 random rotations (seed 1): 228 orientations.
Masks: opt_T5 (optimistic free map, case fitted after T5 from the open side; S1 / amp / buck / side-cap paths kept clear) and
cons_T5 (conservative).  Region x >= XMIN (default 12: left half; the right half is a near mirror).
Output: search_c.json - per servo / mask the number of feasible orientations and the smallest overlap (mm3) if none."""
import sys, os, json, math, time
sys.dont_write_bytecode = True
import numpy as np
from scipy import signal
from scipy.spatial.transform import Rotation as Rot
HERE = os.path.dirname(os.path.abspath(__file__))
D = np.load(os.path.join(HERE, "map1.npz"))
lo, H = D["lo"], float(D["h"])
interior, static, moving, free = D["interior"], D["static"], D["moving"], D["free"]
asm = D["s1"] | D["amp"] | D["bokL"] | D["bokP"]
XMIN = float(os.environ.get("XMIN", "12.0"))
i0 = int((XMIN - lo[0]) / H)
MASKS = {"opt_T5": ((interior & ~static & ~moving) & ~asm)[i0:], "cons_T5": (free & ~asm)[i0:]}
LO = lo + np.array([i0 * H, 0, 0])
SERVOS = {"SCS0009 case 23.2x12.1x21.5": (23.2, 12.1, 21.5)}
if os.environ.get("ALL"):
    SERVOS = {"MG90S case 22.8x12.2x22.7": (22.8, 12.2, 22.7), "STS3032 case 23.5x12.5x23": (23.5, 12.5, 23.0),
              "KST X06 20x7x16.6": (20.0, 7.0, 16.6)}
t0 = time.time()


def orientations():
    out = []
    for fixed in range(3):                 # which case dimension (0 L, 1 W, 2 H) lies along the global axis
        for ax in range(3):
            perm = [None] * 3
            others = [k for k in range(3) if k != fixed]
            gl = [k for k in range(3) if k != ax]
            perm[ax] = fixed; perm[gl[0]] = others[0]; perm[gl[1]] = others[1]
            for psi in np.arange(0.0, 180.0, 15.0):
                R = Rot.from_euler("xyz"[ax], psi, degrees=True).as_matrix()
                out.append((f"dim{'LWH'[fixed]}||{'xyz'[ax]} psi{psi:.0f}", perm, R))
    rr = Rot.random(120, random_state=1).as_matrix()
    for i, R in enumerate(rr):
        out.append((f"random{i}", [0, 1, 2], R))
    return out


def kernel(dims, perm, R):
    d = np.array([dims[p] for p in perm])
    g1 = [np.arange(-v / 2, v / 2 + 1e-9, 0.2) for v in d]
    A, B, Cc = np.meshgrid(*g1, indexing="ij")
    P = np.stack([A.ravel(), B.ravel(), Cc.ravel()], 1) @ R.T
    ext = np.abs(P).max(0) + H
    nk = np.ceil(2 * ext / H).astype(int) + 1
    k = np.floor((P + ext) / H).astype(int)
    K = np.zeros(tuple(nk), np.float32); K[k[:, 0], k[:, 1], k[:, 2]] = 1.0
    return K, ext


OR = orientations()
res = {}
for sname, dims in SERVOS.items():
    res[sname] = {}
    for mname, F in MASKS.items():
        Bm = (~F).astype(np.float32)
        feas, best = [], (1e9, None)
        for name, perm, R in OR:
            K, ext = kernel(dims, perm, R)
            ov = signal.fftconvolve(Bm, K[::-1, ::-1, ::-1], mode="valid")
            m = float(ov.min())
            if m < 0.5:
                P = np.argwhere(ov < 0.5); c = LO + P * H + ext
                feas.append(dict(orient=name, n=int(len(P)), centre_range=[[round(float(c[:, i].min()), 1), round(float(c[:, i].max()), 1)] for i in range(3)]))
            if m < best[0]:
                p = np.unravel_index(int(np.argmin(ov)), ov.shape)
                best = (m, name, [round(float(v), 1) for v in (LO + np.array(p) * H + ext)])
        res[sname][mname] = dict(orientations=len(OR), feasible=len(feas), rows=feas[:40],
                                 least_overlap_mm3=round(best[0] * H ** 3, 1), least_overlap_orient=best[1], least_overlap_centre=best[2])
        print(sname, mname, len(feas), "/", len(OR), "least overlap mm3", round(best[0] * H ** 3, 1), best[1], best[2],
              [(f["orient"], f["centre_range"]) for f in feas[:5]], f"{time.time()-t0:.0f}s", flush=True)
json.dump(res, open(os.path.join(HERE, os.environ.get("OUT", "search_c.json")), "w"), indent=1)
print("done", f"{time.time()-t0:.0f}s")
