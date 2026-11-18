"""m02b: section areas of P_sachta vs z (for print peel loads and wall load paths) + sharpness probe of the window corners."""
import json, math
import numpy as np
from sb_lib import read_stl, thickness_along, OUT
d = np.load(f"{OUT}/m02_columns.npz")
LO, HI, xs, ys = d["LO"], d["HI"], d["xs"], d["ys"]
H = xs[1] - xs[0]
def area(z):
    with np.errstate(invalid="ignore"):
        m = np.nanmax(((LO <= z) & (z <= HI)).astype(float), axis=1)
    return float(np.nan_to_num(m).sum() * H * H)
prof = {round(z, 2): round(area(z), 1) for z in [-2.2, -3.0, -6.0, -9.0, -10.5, -12.0, -20.0, -30.0, -38.0, -40.0, -40.7, -41.0, -41.5, -41.8, -42.2, -44.0, -45.5]}
S = read_stl("P_sachta")
# window corner probes: material along the bisector into the window from the corner (sharp corner -> no material inside)
def probe(p, dvec):
    iv = thickness_along(S, p, dvec)
    return [(round(a, 3), round(b, 3)) for a, b in iv]
corners = {}
# back window x -20.9 .. -6.5, top z -10.9, in the back wall y 11..13 (probe at y 12.0, along the in-plane bisector)
for name, (x, z, sx, sz) in {"back_win_top_left": (-20.9, -10.9, 1, -1), "back_win_top_right": (-6.5, -10.9, -1, -1),
                             "back_win_bottom_right(floor)": (-6.5, -40.65, -1, 1)}.items():
    res = []
    for s in (0.05, 0.1, 0.2, 0.3, 0.5, 0.8):
        p = (x + sx * s, 12.0, z + sz * s)
        iv = thickness_along(S, (p[0], 12.0, 10.0), (0, 0, -1))
        inside = any(10 - b <= p[2] <= 10 - a for a, b in iv)
        res.append((s, inside))
    corners[name] = res
# +X end window y -7.0 .. 3.4, z top -15.0, wall x 23.5..25.1 (probe x 24.3)
for name, (y, z, sy, sz) in {"end_win_top_-Y": (-7.0, -15.0, 1, -1), "end_win_top_+Y": (3.4, -15.0, -1, -1)}.items():
    res = []
    for s in (0.05, 0.1, 0.2, 0.3, 0.5, 0.8):
        iv = thickness_along(S, (24.3, y + sy * s, 10.0), (0, 0, -1))
        zz = z + sz * s
        res.append((s, any(10 - b <= zz <= 10 - a for a, b in iv)))
    corners[name] = res
# shroud root: is there a fillet at the outer root r 16.7 / z -41.9 where no lip (az 15)?
a = math.radians(15.0)
root = []
for s in (0.05, 0.1, 0.2, 0.3):
    r, z = 16.7 + s, -41.9 - s
    iv = thickness_along(S, (r * math.cos(a), r * math.sin(a), 10.0), (0, 0, -1))
    root.append((s, any(10 - bb <= z <= 10 - aa for aa, bb in iv)))
out = dict(section_area_mm2=prof, window_corner_bisector_material=corners, shroud_outer_root_az15_material=root,
           note="True at offset s along the bisector = material there = fillet present; all False = sharp corner")
json.dump(out, open(f"{OUT}/m02b_sections.json", "w"), indent=1)
print(json.dumps(out, indent=1))
