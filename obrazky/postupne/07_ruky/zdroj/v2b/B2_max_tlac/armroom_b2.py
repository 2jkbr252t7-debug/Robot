"""B2: do the arm-side parts fit inside the approved pebble (dx -1)?  Points on the outer surfaces of the hub tube / flange
(part of the arm body: must be inside the skin, inset 0), the clutch disc and the screw head (rotate relative to the arm only
when the clutch slips: must keep >= 0.5 from the shell inner surface, i.e. inside inset 1.2 + 0.5), and the ring end.
writes armroom_b2.json"""
import sys, json, numpy as np
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R1/geo")
from armgeo import to_local, inside_local
DX = -1.0; YA, ZA = 3.0, -17.0
th = np.linspace(0, 2 * np.pi, 360, endpoint=False)
def ring_pts(r, x0, x1, nx=12):
    return np.array([(x, YA + r * np.cos(t), ZA + r * np.sin(t)) for x in np.linspace(x0, x1, nx) for t in th])
def disc_face(x, r0, r1):
    return np.array([(x, YA + r * np.cos(t), ZA + r * np.sin(t)) for r in np.linspace(r0, r1, 8) for t in th])
items = {
    "hub tube r 8.0 x 52.6..58.5 (arm body, inset 0)": (ring_pts(8.0, 52.6, 58.5), 0.0),
    "hub flange r 14.2 x 58.5..61.0 (arm body, inset 0)": (np.r_[ring_pts(14.2, 58.5, 61.0, 6), disc_face(58.5, 8.0, 14.2)], 0.0),
    "clutch disc r 14.2 x 61.1..64.5 (inset 1.7)": (np.r_[ring_pts(14.2, 61.1, 64.5, 8), disc_face(64.5, 0.0, 14.2)], 1.7),
    "M2 screw head r 1.9 x 64.5..66.5 (inset 1.7)": (np.r_[ring_pts(1.9, 64.5, 66.5, 5), disc_face(66.5, 0, 1.9)], 1.7),
    "hub inner face / counterbore start r 7.0 at x 52.6 (inset 0)": (ring_pts(7.0, 52.6, 52.6, 1), 0.0),
}
out = {}
for k, (P, inset) in items.items():
    ins = inside_local(to_local(P, dx=DX), inset=inset)
    # margin: largest extra inset still satisfied
    m = 0.0
    for extra in np.arange(0.0, 3.01, 0.05):
        if inside_local(to_local(P, dx=DX), inset=inset + extra).all(): m = extra
        else: break
    out[k] = dict(all_inside=bool(ins.all()), frac_inside=round(float(ins.mean()), 3), extra_margin_mm=round(float(m), 2))
    print(k, out[k])
json.dump(out, open("armroom_b2.json", "w"), indent=1)
