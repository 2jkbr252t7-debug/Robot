"""inside-corner fillet radii at the wall / floor junctions of P_sachta, measured on 0.005 mm raster sections:
march from the ideal sharp corner along the bisector into the void; a fillet R leaves d = R (sqrt2 - 1) of material."""
import json, math, numpy as np
import sa_lib as L
S = L.part("P_sachta")


def rot(T, az):
    a = math.radians(-az); c, s = math.cos(a), math.sin(a)
    T2 = T.copy(); T2[:, :, 0] = c * T[:, :, 0] - s * T[:, :, 1]; T2[:, :, 1] = s * T[:, :, 0] + c * T[:, :, 1]
    return T2


def measure(name, T, axis, value, corner, void_dir, span=1.6, h=0.005):
    """corner (u, v) in the section plane coordinates (u, v = axes axis+1, axis+2 cyclic); void_dir (du, dv)"""
    u0, v0 = corner
    us, vs, M = L.raster_slice(T, axis, value, (u0 - span, u0 + span), (v0 - span, v0 + span), h)
    du, dv = np.array(void_dir) / np.hypot(*void_dir)
    # material at the sharp corner?  march
    d = 0.0; last_in = None
    for t in np.arange(-0.2, span, h / 2):
        u, v = u0 + du * t, v0 + dv * t
        i = int((u - us[0]) / h + 0.5); j = int((v - vs[0]) / h + 0.5)
        if 0 <= i < len(us) and 0 <= j < len(vs) and M[i, j]:
            last_in = t
    d = last_in if last_in is not None else float("nan")
    return dict(name=name, d_bisector=round(d, 3), R_equiv=round(d / (math.sqrt(2) - 1), 2) if d > 0 else 0.0)


if __name__ != '__main__':
    pass
def _main():
    res = []
    # section x = c: u = y, v = z  (axis 0 -> (1, 2))
    for xc in (0.0, -4.0, 4.0):
        res.append(measure(f"hub disc / front wall inner, x {xc}", S, 0, xc, (-11.0, -40.65), (1, 1)))
    for xc in (0.0, 8.0, 15.0, 20.0, -5.0):
        res.append(measure(f"back floor / back wall inner, x {xc}", S, 0, xc, (11.0, -40.65), (-1, 1)))
    # section y = c: axis 1 -> (u, v) = (z, x)
    for yc in (5.0, 7.0, 8.0):
        res.append(measure(f"back floor / +X pillar inner, y {yc}", S, 1, yc, (-40.65, 23.5), (1, -1)))
    # corner arcs: radial plane through the arc centre; rotate so the plane is y = 0 -> (u, v) = (z, x')
    for cx, cy in ((21, 8.5), (-21, 8.5), (21, -8.5), (-21, -8.5)):
        az = math.degrees(math.atan2(cy, cx)); rin = math.hypot(cx, cy) + 2.5
        T = rot(S, az)
        res.append(measure(f"corner ({cx},{cy}) inner arc / floor (az {az:.1f})", T, 1, 0.0, (-40.65, rin), (1, -1)))
    # drum shroud root under the back floor (outer face r 16.7 / floor underside -41.9) at az 90 -> section x = 0, (u, v) = (y, z)
    res.append(measure("drum shroud outer face / back-floor underside, az 90", S, 0, 0.0, (16.7, -41.9), (1, -1)))
    res.append(measure("drum shroud inner face / back-floor underside, az 90", S, 0, 0.0, (15.5, -41.9), (-1, -1)))
    # rail root on the back wall outer face (y 13.0, rail top z -33.9) at x 5
    res.append(measure("rail top / back wall outer face, x 5", S, 0, 5.0, (13.0, -33.9), (1, 1)))
    # pad A root (y 13.0 face, pad r 3.65 around (7, -15.8)): section z = -15.8, (u, v) = (x, y): corner at x 7 + 3.65, y 13
    res.append(measure("pad A root on the back wall (z -15.8, +x side)", S, 2, -15.8, (10.65, 13.0), (1, 1)))
    # window corners (back window x -20.9..-6.5, top z -10.9): section y = 12 -> (u, v) = (z, x): top corners
    res.append(measure("back window top corner (x -6.5, z -10.9)", S, 1, 12.0, (-10.9, -6.5), (-1, 1)))
    res.append(measure("end window top corner (y 3.4, z -15.0)", S, 0, 24.3, (3.4, -15.0), (-1, -1)))
    json.dump(res, open("g08_fillets.json", "w"), indent=1)
    for r in res:
        print(r)


if __name__ == '__main__':
    _main()
