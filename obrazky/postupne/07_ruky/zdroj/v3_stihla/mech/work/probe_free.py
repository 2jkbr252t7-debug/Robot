import numpy as np, sys
F = np.load("/tmp/claude-0/gapwf/fin/R2c/oprava/free_L.npz")
for k in F.files: print(k, F[k].shape, F[k].dtype)
xs, ys, zs = F["xs"], F["ys"], F["zs"]
print("x", xs[0], xs[-1], "y", ys[0], ys[-1], "z", zs[0], zs[-1], "h", xs[1]-xs[0])
