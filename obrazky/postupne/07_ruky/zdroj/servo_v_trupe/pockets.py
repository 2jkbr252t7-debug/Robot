"""STEP 1d - the named free pockets near the left shoulder and in the lower torso (bounds, volume, thickest, largest boxes),
conservative / optimistic, with and without the T_stred lowering path.  Right side: same boxes mirrored in x.  Writes pockets.json."""
import sys, os, json, time
sys.dont_write_bytecode = True
import numpy as np
from scipy import ndimage as ndi
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import voxlib as V  # noqa: E402
D = np.load(os.path.join(HERE, "map1.npz"))
lo, H = D["lo"], float(D["h"]); n = tuple(D["n"])
g = V.Grid(lo, lo + np.array(n) * H, H)
interior, static, moving, free = D["interior"], D["static"], D["moving"], D["free"]
lower, s1, amp = D["lower"], D["s1"], D["amp"]
asm = s1 | amp | D["bokL"] | D["bokP"]
opt = interior & ~static & ~moving
X, Y, Z = np.meshgrid(g.axis(0), g.axis(1), g.axis(2), indexing="ij")
POCKETS = {
    "A front-left, inside the side cap (x>=33)": dict(x=(33, 53), y=(-41, -14), z=(-86, 4)),
    "B back-left, inside the side cap (x>=33)": dict(x=(33, 53), y=(15, 41), z=(-86, 4)),
    "C front-left corner inside the T_stred band (x 15..33)": dict(x=(15, 33), y=(-41, -12), z=(-86, 4)),
    "D back-left corner inside the T_stred band (x 15..33)": dict(x=(15, 33), y=(12, 41), z=(-86, 4)),
    "E front-left A+C joined (servo fitted after T5 from the side)": dict(x=(15, 53), y=(-41, -12), z=(-86, 4)),
    "F T_klb centre bore (x 38..48 around the axis)": dict(x=(38, 48), y=(-3, 9), z=(-23, -11)),
    "G above the shoulder joint (z > -6)": dict(x=(28, 53), y=(-20, 25), z=(-6, 4)),
    "H lower torso next to the J1 servo +X end": dict(x=(15, 34), y=(-12.5, 12.5), z=(-84, -48)),
    "I lower torso behind the carrier (door zone)": dict(x=(-25, 25), y=(24, 41), z=(-84, -12)),
    "J side cap below the shoulder, beside the column (x>=37.4, |y|<15)": dict(x=(37.4, 53), y=(-14, 15), z=(-86, -31)),
}
out = {}
t0 = time.time()
for name, b in POCKETS.items():
    R = (X >= b["x"][0]) & (X <= b["x"][1]) & (Y >= b["y"][0]) & (Y <= b["y"][1]) & (Z >= b["z"][0]) & (Z <= b["z"][1])
    row = {}
    for vname, F in (("cons", free & ~asm), ("cons_preT5", free & ~asm & ~lower), ("opt", opt & ~asm), ("opt_preT5", opt & ~asm & ~lower)):
        M = F & R
        if not M.any():
            row[vname] = None; continue
        I = np.argwhere(M); a = I.min(0); c = I.max(0) + 1
        S = M[a[0]:c[0], a[1]:c[1], a[2]:c[2]]
        bnd = [[round(float(lo[i] + a[i] * H), 1), round(float(lo[i] + c[i] * H), 1)] for i in range(3)]
        v0, p0, d0 = V.max_box(S, H, step=2, min_dim=0)
        v7, p7, d7 = V.max_box(S, H, step=2, min_dim=14)
        def bx(p, d_):
            if p is None:
                return None
            q = lo + (a + np.array(p)) * H; dd = np.array(d_) * H
            return dict(size=[round(float(v), 1) for v in dd], at=[[round(float(q[i]), 1), round(float(q[i] + dd[i]), 1)] for i in range(3)])
        row[vname] = dict(volume_mm3=round(float(M.sum()) * H ** 3), bounds=bnd,
                          thickest_mm=round(2 * float(ndi.distance_transform_edt(np.pad(S, 1), sampling=H).max()), 1),
                          largest_box=bx(p0, d0), largest_box_min7=bx(p7, d7))
    out[name] = row
    print(name, {k: (v["volume_mm3"], v["thickest_mm"], v["largest_box"]["size"] if v and v["largest_box"] else None,
                     v["largest_box_min7"]["size"] if v and v["largest_box_min7"] else None) if v else None for k, v in row.items()},
          f"{time.time()-t0:.0f}s", flush=True)
# right/left difference: mirror test of the conservative free map
Fm = free[::-1, :, :]
both = (free & Fm).sum(); diff = (free ^ Fm).sum()
out["mirror_check"] = dict(free_voxels=int(free.sum()), mirror_symmetric_voxels=int(both), asymmetric_voxels=int(diff),
                           note="asymmetric voxels / free voxels; the right side carries the buck (menic) and stop pin 2, the left the amp and stop pin 1")
json.dump(out, open(os.path.join(HERE, "pockets.json"), "w"), indent=1)
print("done")
