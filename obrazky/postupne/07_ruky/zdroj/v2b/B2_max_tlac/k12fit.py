"""JUDGE: independent check of the K1/K2 premise - can a bare SCS0009 case (21.5 along X = shaft || X, 12.1 x 23.2) sit
anywhere in the torso (K3 map: removable column / joint / amp / buck deleted; static 0.3 + moving 1.0 clearance)?"""
import numpy as np
from scipy import ndimage as ndi
M = np.load("/tmp/claude-0/gapwf/fin/R1/K3_preusporiadanie/k3map.npz")
lo, h = M["lo"], float(M["h"])
free = M["interior"] & ~M["hard"] & (M["ds"] >= 0.3 + h / 2) & (M["dm"] >= 1.0 + h / 2)
print("free cm3", free.sum() * h**3 / 1000)
for H in (21.5, 19.5, 18.0, 16.6):
    for (a, b) in ((12.1, 23.2), (23.2, 12.1)):
        size = (int(np.ceil(H / h)), int(np.ceil(a / h)), int(np.ceil(b / h)))
        er = ndi.minimum_filter(free.astype(np.uint8), size=size, mode="constant", cval=0).astype(bool)
        n = er.sum()
        msg = ""
        if n:
            I = np.argwhere(er); C = lo + (I + 0.5) * h
            msg = "centre x %.1f..%.1f y %.1f..%.1f z %.1f..%.1f" % (C[:,0].min(), C[:,0].max(), C[:,1].min(), C[:,1].max(), C[:,2].min(), C[:,2].max())
        print("case %.1f (x) x %.1f (y) x %.1f (z): %d positions %s" % (H, a, b, n, msg))
