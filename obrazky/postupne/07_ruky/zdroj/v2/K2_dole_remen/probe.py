import sys, numpy as np, collections
D = np.load("/tmp/claude-0/gapwf/fin/R1/trup_servo/map1.npz"); lo, H, n = D["lo"], float(D["h"]), D["n"]
Hd = np.load("hard.npz"); hard = Hd["hard"]; ds_h = Hd["ds_h"]; dm = D["dm"]; interior = D["interior"]; label = D["label"]
names = [str(s) for s in D["lab_names"]]
def probe(x0, x1, y0, y1, z0, z1, cyl=None):
    X = lo[0] + (np.arange(n[0]) + 0.5) * H; Y = lo[1] + (np.arange(n[1]) + 0.5) * H; Z = lo[2] + (np.arange(n[2]) + 0.5) * H
    ix = (X >= x0) & (X <= x1); iy = (Y >= y0) & (Y <= y1); iz = (Z >= z0) & (Z <= z1)
    m = np.zeros(hard.shape, bool); m[np.ix_(ix, iy, iz)] = True
    if cyl is not None:
        (xa, xb, yc, zc, r) = cyl
        XX, YY, ZZ = np.meshgrid(X, Y, Z, indexing="ij")
        m |= (XX >= xa) & (XX <= xb) & (np.hypot(YY - yc, ZZ - zc) <= r)
    bad_s = m & (ds_h < 0.55); bad_m = m & (dm < 1.25); bad_i = m & ~interior
    print("voxels", m.sum(), "near hard", bad_s.sum(), "near moving", bad_m.sum(), "outside", bad_i.sum())
    # which hard labels are near: nearest hard voxel labels via a dilation search
    from scipy import ndimage as ndi
    _, ind = ndi.distance_transform_edt(~hard, return_indices=True, sampling=H) if False else (None, None)
    for msk, nm in ((bad_s, "static"), (bad_i, "outside")):
        if msk.any():
            idx = np.argwhere(msk)
            P = lo + (idx + 0.5) * H
            print(" ", nm, "x %.1f..%.1f y %.1f..%.1f z %.1f..%.1f" % (P[:,0].min(), P[:,0].max(), P[:,1].min(), P[:,1].max(), P[:,2].min(), P[:,2].max()))
    # list hard labels within 0.6 of the region
    from scipy.ndimage import binary_dilation
    md = binary_dilation(m, iterations=2)
    c = collections.Counter(names[l] for l in label[md & hard])
    print("  hard labels touching:", c.most_common(12))
if __name__ == "__main__":
    a = [float(v) for v in sys.argv[1:7]]
    cyl = tuple(float(v) for v in sys.argv[7:12]) if len(sys.argv) > 7 else None
    probe(*a, cyl=cyl)
