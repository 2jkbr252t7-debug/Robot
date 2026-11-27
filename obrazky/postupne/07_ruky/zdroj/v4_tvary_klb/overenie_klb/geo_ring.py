"""verifier: along lines || X at radius r around the shoulder axis: arm B inner face x, seam x, outer face x (world)."""
import sys, math
sys.dont_write_bytecode = True
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R3/tvar")
import numpy as np
import variants as VA
YA, ZA = 3.0, -17.0
xs = np.arange(40.0, 80.0, 0.01)

def line(r, az, dx=-1.0):
    t = math.radians(az)
    y, z = YA + r * math.cos(t), ZA + r * math.sin(t)
    W = np.c_[xs, np.full_like(xs, y), np.full_like(xs, z)]
    L = VA.to_local(W, "B", dx)
    ins = VA.inside_local("B", L)
    if not ins.any():
        return None
    u = np.clip(-L[:, 2] / VA.L, 0, 1)
    sx = VA.seam_x("B", u)
    inner = ins & (L[:, 0] < sx)
    outer = ins & (L[:, 0] >= sx)
    x_in = xs[ins].min(); x_out = xs[ins].max()
    x_seam = xs[inner].max() if inner.any() else float("nan")
    return x_in, x_seam, x_out, float(u[ins].mean())

for dx in (-1.0,):
  for r in (11.0, 12.2, 13.1, 13.2):
    print("r", r)
    for az in range(0, 360, 15):
        res = line(r, az, dx)
        if res is None:
            print(f"  az {az:3d}: outside arm"); continue
        x_in, x_seam, x_out, u = res
        print(f"  az {az:3d}: inner {x_in:6.2f} seam {x_seam:6.2f} outer {x_out:6.2f}  A_vnut thick along x {x_seam - x_in:5.2f}  u {u:.3f}")
