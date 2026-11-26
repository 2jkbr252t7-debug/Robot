"""Verifier: shell strength sanity (hand-level) for the variant-A arm vs the current arm (variant 0).
Sections are rasterised (0.02 mm) from my own geomA section; the 1.6 wall is a TRUE inward offset (Euclidean distance
transform), the seam gap 0.25 per side is removed.  Members:
  A_vnut  : inner half alone (open trough) - the cover sits on magnets, so the inner half carries the arm loads
  A_vonk  : outer cover alone
  closed  : both halves acting together (upper bound, only if the seam were bonded / interlocked)
Loads: 10 N at the arm tip (local (0, 0, -72)), lateral (X, bending about local y) and fore-aft (Y, bending about local x,
only reached when the arm sits on its stop - otherwise the clutch slips at ~0.017 N m)."""
import sys, os, json, math
sys.dont_write_bytecode = True
import numpy as np
from scipy import ndimage
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import geomA as G  # noqa

H = 0.02
WALL = 1.6
F = 10.0


def section_masks(u, ko, kw):
    ti, to, w = (float(v) for v in G.sec(u, ko, kw))
    xs = np.arange(-ti - 0.5, to + 0.5, H); ys = np.arange(-w - 0.5, w + 0.5, H)
    X, Y = np.meshgrid(xs, ys, indexing="ij")
    t = np.where(X >= 0, to, ti)
    solid = (np.abs(X) / t) ** 2.3 + (np.abs(Y) / w) ** 2.3 < 1.0
    dist = ndimage.distance_transform_edt(solid) * H
    shell = solid & (dist <= WALL)
    inner = shell & (X <= -0.25)
    outer = shell & (X >= 0.25)
    closed = shell
    return X, Y, dict(A_vnut=inner, A_vonk=outer, closed=closed), (ti, to, w)


def props(X, Y, m):
    A = m.sum() * H * H
    xc, yc = X[m].mean(), Y[m].mean()
    Iyy = ((X[m] - xc) ** 2).sum() * H * H          # bending about local y (lateral load along x)
    Ixx = ((Y[m] - yc) ** 2).sum() * H * H          # bending about local x (fore-aft load along y)
    cx = np.abs(X[m] - xc).max(); cy = np.abs(Y[m] - yc).max()
    return dict(area=A, xc=xc, Iyy=Iyy, Ixx=Ixx, Zy=Iyy / cx, Zx=Ixx / cy, cx=cx, cy=cy)


out = {}
for vid, ko, kw in (("0", 1.0, 1.0), ("A", 0.62, 0.95)):
    out[vid] = {}
    for u in (0.355, 0.5, 0.7):
        X, Y, M, dims = section_masks(u, ko, kw)
        lever = G.L * (1 - u)
        Mb = F * lever                                       # N mm
        row = dict(u=u, lever_mm=round(lever, 1), ti=round(dims[0], 2), to=round(dims[1], 2), w=round(dims[2], 2))
        for k, m in M.items():
            p = props(X, Y, m)
            row[k] = dict(area_mm2=round(p["area"], 1), Iyy=round(p["Iyy"], 0), Ixx=round(p["Ixx"], 0),
                          sigma_lateral_MPa=round(Mb / p["Zy"], 2), sigma_foreaft_MPa=round(Mb / p["Zx"], 2))
        out[vid][str(u)] = row
        print(vid, row)

# arm mass estimate (shell 1.6, both halves, density 1.15 g/cm3) - for the drop estimate
for vid, ko, kw in (("0", 1.0, 1.0), ("A", 0.62, 0.95)):
    vol = 0.0
    for u in np.linspace(0.005, 0.995, 40):
        X, Y, M, _ = section_masks(u, ko, kw)
        vol += M["closed"].sum() * H * H * (G.L / 40)
    out[vid]["shell_volume_cm3"] = round(vol / 1000, 2)
    out[vid]["shell_mass_g"] = round(vol / 1000 * 1.15, 1)
    print(vid, "shell volume", out[vid]["shell_volume_cm3"], "cm3, mass", out[vid]["shell_mass_g"], "g")
json.dump(out, open(os.path.join(HERE, "strength_A.json"), "w"), indent=1)
