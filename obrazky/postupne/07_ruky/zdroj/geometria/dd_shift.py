"""Direct drive (servo shaft ON the shoulder axis, case turns with the arm) with the white pebble shifted outward by dx.
Case: L (along the arm, shaft s from the upper end), W (fore-aft), H (along X, case only).  Inner case face at x0 = 59.056
(frozen T_klb end face 58.756 + 0.3).  The part of the case inboard of the pebble's inner skin sits in a black rotating collar
(no check); every case point that is inside the pebble's x-range must be inside the 2.0 inset (wall).  We sample the case
surface and require: for points with x >= inner-skin x at that (y,z): inside_local(inset 2.0).  Find the minimum dx (0.05 steps)."""
import sys, math, numpy as np
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R1/geo")
import armgeo as G

def case_pts(Lc, Wc, Hc, s, x0, n=14):
    # arm long axis in world (rest pose): direction of local -z
    d_down = (G.R @ np.array([0, 0, -1.0])); d_down[0] = 0; d_down /= np.linalg.norm(d_down)   # projected into the y-z plane
    d_fa = np.array([0, 1.0, 0]); d_fa -= d_fa.dot(d_down) * d_down; d_fa /= np.linalg.norm(d_fa)
    c = G.AX.copy()
    us = np.linspace(-s, Lc - s, n); ws = np.linspace(-Wc / 2, Wc / 2, max(4, n // 2)); hs = np.linspace(0, Hc, n)
    P = []
    for a in us:
        for b in ws:
            for h in hs:
                if a in (us[0], us[-1]) or b in (ws[0], ws[-1]) or h in (hs[0], hs[-1]):
                    P.append(c + a * d_down + b * d_fa + np.array([x0 + h, 0, 0]))
    return np.array(P)

def skin_x(yz, dx):
    # inner-skin x of the shifted pebble on the line parallel to X through (y, z)
    xs = np.linspace(40, 100, 6001)
    Q = np.stack([xs, np.full_like(xs, yz[0]), np.full_like(xs, yz[1])], 1)
    ins = G.inside_local(G.to_local(Q, dx=dx))
    if not ins.any(): return None
    return xs[np.argmax(ins)]

def need(Lc, Wc, Hc, s, x0=59.056, wall=2.0):
    P = case_pts(Lc, Wc, Hc, s, x0)
    for dx in np.arange(0.0, 20.01, 0.25):
        loc = G.to_local(P, dx=dx)
        ok_wall = G.inside_local(loc, inset=wall)
        bad = 0
        for p, okw in zip(P, ok_wall):
            if okw: continue
            sx = skin_x(p[1:], dx)
            if sx is None or p[0] >= sx - 1e-6:   # point within/after the skin region but not inside the wall
                # allow points inboard of the skin (they are in the black collar)
                if sx is not None and p[0] < sx + wall: 
                    pass
                bad += 1
        if bad == 0:
            return dx
    return None

cases = {"KST X06 (20 x 7 x 16.6, shaft ~5)": (20.0, 7.0, 16.6, 5.0),
         "KST X08 (23.5 x 8 x 16.8, shaft ~5.5)": (23.5, 8.0, 16.8, 5.5),
         "ES9052MD (19.9 x 8.8 x 23.1, shaft 4.7)": (19.9, 8.8, 23.1, 4.7),
         "SCS0009 if 25.25 incl. spline (case ~21.5)": (23.2, 12.1, 21.5, 5.9),
         "SCS0009 case 25.25": (23.2, 12.1, 25.25, 5.9),
         "MG90S (22.8 x 12.2 x 22.7, shaft 5.9)": (22.8, 12.2, 22.7, 5.9)}
for k, v in cases.items():
    print(f"{k:45s} min outward shift dx = {need(*v)}")
