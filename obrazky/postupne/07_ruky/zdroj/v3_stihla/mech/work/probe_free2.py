import numpy as np, math
F = np.load("/tmp/claude-0/gapwf/fin/R2c/oprava/free_L.npz")
xs, ys, zs = F["xs"], F["ys"], F["zs"]; h = 0.5
ds, dm, dl, capmin = F["ds"], F["dm"], F["dl"], F["capmin"]
X, Y = np.meshgrid(xs, ys, indexing="ij")
def free_slice(kz):
    z = zs[kz]
    fr = (ds[:, :, kz] >= 0.30 + h/2) & (dm[:, :, kz] >= 1.0 + h/2) & (dl[:, :, kz] >= 0.5 + h/2)
    fr &= X <= (capmin[:, kz][None, :] - 0.3 - h/2)
    return fr
print("free radius about the vertical axis (39,3) per z: largest r such that the whole circle r is free (ignoring the existing drive parts which are not 'hard')")
for z in np.arange(-48, -18, 1.0):
    kz = int(np.argmin(abs(zs - z))); fr = free_slice(kz)
    rv = np.hypot(X - 39.0, Y - 3.0)
    best = 0
    for r in np.arange(0.5, 15, 0.5):
        ring = (rv >= r - 0.25) & (rv < r + 0.25)
        if fr[ring].all(): best = r
        else: break
    # fraction free at r 6, 8
    fracs = []
    for r in (5, 6, 7, 8, 10):
        ring = (rv >= r - 0.25) & (rv < r + 0.25); fracs.append(round(float(fr[ring].mean()), 2))
    print(f"z {zs[kz]:6.2f}: full-circle free r {best:4.1f}; free fraction at r 5/6/7/8/10: {fracs}")
