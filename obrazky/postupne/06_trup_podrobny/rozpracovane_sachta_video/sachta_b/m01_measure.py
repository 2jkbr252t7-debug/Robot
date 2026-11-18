"""m01: exact-ish thickness measurements on the P_sachta / T_cap / F15 STLs (deflection 0.01 mm) by ray casting.
Writes m01_measure.json. Read-only on the design files."""
import json, math
import numpy as np
from sb_lib import read_stl, thickness_along, interval_at, OUT

S = read_stl("P_sachta")
res = {}


def wall_y(x, z, y_probe):
    a, b = interval_at(S, (x, -60, z), (0, 1, 0), y_probe + 60)
    return dict(y0=round(a - 60, 3), y1=round(b - 60, 3), t=round(b - a, 3))


def wall_x(y, z, x_probe):
    a, b = interval_at(S, (-60, y, z), (1, 0, 0), x_probe + 60)
    return dict(x0=round(a - 60, 3), x1=round(b - 60, 3), t=round(b - a, 3))


def vert(x, y, z_probe):
    iv = interval_at(S, (x, y, 10), (0, 0, -1), 10 - z_probe)
    if iv is None:
        return None
    a, b = iv
    return dict(z_top=round(10 - a, 3), z_bot=round(10 - b, 3), t=round(b - a, 3))


# ---- plain walls
res["front_wall"] = {f"x{x}_z{z}": wall_y(x, z, -11.8) for x in (-15, 0, 15) for z in (-35, -20)}
res["back_wall"] = {f"x{x}_z{z}": wall_y(x, z, 12.0) for x in (-23, 0, 12, 20) for z in (-35, -20)}
res["end_wall_+X"] = {f"y{y}_z{z}": wall_x(y, z, 24.3) for y in (-9, 6, 9) for z in (-35, -12)}
res["end_wall_-X"] = {f"y{y}_z{z}": wall_x(y, z, -24.3) for y in (-6, 0, 6) for z in (-35, -20)}

# ---- slim corners: radial rays from the axis, scan azimuth around each corner, several z; keep the min wall
corners = {}
for name, (cx, cy) in {"+X+Y": (21.0, 8.5), "-X+Y": (-21.0, 8.5), "+X-Y": (21.0, -8.5), "-X-Y": (-21.0, -8.5)}.items():
    az0 = math.degrees(math.atan2(cy, cx))
    best = {}
    for z in (-3.0, -6.0, -9.0, -10.5, -12.0, -20.0, -30.0, -38.0, -40.5):
        mins = []
        for daz in np.arange(-12.0, 12.01, 0.25):
            a = math.radians(az0 + daz)
            d = (math.cos(a), math.sin(a), 0.0)
            iv = thickness_along(S, (0, 0, z), d)
            iv = [(p, q) for p, q in iv if p > 20.0]          # the wall (outer) interval
            if iv:
                p, q = iv[-1]
                mins.append((q - p, az0 + daz, p, q))
        if mins:
            m = min(mins)
            best[f"z{z}"] = dict(t_min=round(m[0], 3), az=round(m[1], 2), r_in=round(m[2], 3), r_out=round(m[3], 3))
    corners[name] = best
res["slim_corners_radial_min"] = corners

# ---- hub disc ring + back floor (vertical rays)
res["hub_disc"] = {f"({x},{y})": vert(x, y, -41.3) for x, y in ((0, -9.5), (9.5, 0), (-9.5, 0), (0, 9.5), (-7, -7), (7, -7))}
res["back_floor"] = {f"({x},{y})": vert(x, y, -41.3) for x, y in ((14, 8), (20, 5), (20, 9), (17, 5.5), (22.5, 5), (-5, 9), (0, 5))}
# floor over the FFC groove (y 3.3..7.2, x 15..25.6, 0.3 deep from the underside)
res["floor_over_groove"] = {f"({x},{y})": vert(x, y, -41.3) for x, y in ((16.5, 5.0), (19, 5.0), (21, 4.0))}

# ---- hub ring <-> front wall junction: material in the plane y = -11.0 (inner face of the front wall) below z -40.0
xs = np.arange(-8.0, 8.01, 0.05)
jun = []
for x in xs:
    iv = thickness_along(S, (x, -11.05, 10), (0, 0, -1))
    seg = [(10 - b, 10 - a) for a, b in iv if 10 - a > -42.5 and 10 - b < -39.0]
    if seg:
        jun.append((x, seg))
xj = [x for x, s in jun if any(lo <= -41.0 for lo, hi in s)]
res["hub_front_junction_plane_y-11.05"] = dict(x_from=round(min(xj), 2) if xj else None, x_to=round(max(xj), 2) if xj else None,
                                               sample_x0=[(round(x, 2), [(round(a, 3), round(b, 3)) for a, b in s]) for x, s in jun if abs(x) < 0.03])

# ---- drum shroud: radial thickness and height, lip
shr = {}
for az in (15, 40, 70, 100, 130):
    a = math.radians(az); d = (math.cos(a), math.sin(a), 0)
    for z in (-42.2, -44.0, -45.4):
        iv = [(p, q) for p, q in thickness_along(S, (0, 0, z), d) if 14.0 < p < 18.5]
        shr[f"az{az}_z{z}"] = [(round(p, 3), round(q, 3), round(q - p, 3)) for p, q in iv]
    # vertical extent at r 16.1
    v = vert(16.1 * math.cos(a), 16.1 * math.sin(a), -44.0)
    shr[f"az{az}_vertical_r16.1"] = v
res["drum_shroud"] = shr
# shroud azimuth extent at z -44
azs = []
for az in np.arange(0, 180, 0.5):
    a = math.radians(az)
    iv = [(p, q) for p, q in thickness_along(S, (0, 0, -44.0), (math.cos(a), math.sin(a), 0)) if 14.0 < p < 18.5]
    if iv:
        azs.append(az)
res["drum_shroud_az_extent_z-44"] = (min(azs), max(azs)) if azs else None

# ---- F10 pads: wall around the D4.1 insert holes in the pad plane (y 14.0) - rays in x-z from the hole axis
pads = {}
for name, (x0, z0) in {"F10_A": (7.0, -15.8), "F10_B": (18.0, -33.3)}.items():
    out = []
    for ang in np.arange(0, 360, 2.0):
        a = math.radians(ang); d = (math.cos(a), 0.0, math.sin(a))
        for yy in (13.5, 14.5):
            iv = thickness_along(S, (x0, yy, z0), d)
            iv = [(p, q) for p, q in iv if q > 0 and p > 1.5]
            if iv:
                p, q = iv[0]
                out.append((round(q - p, 3), ang, yy, round(p, 3)))
    out.sort()
    pads[name] = dict(min_ligament=out[0], hole_r_seen=round(min(o[3] for o in out), 3), n=len(out))
    # depth of material along the hole axis (y) just outside the hole
    pads[name]["axial_y_at_r2.6"] = [(round(a, 3), round(b, 3)) for a, b in thickness_along(S, (x0 + 2.6, 0, z0), (0, 1, 0))]
res["F10_pads"] = pads
# dowel hole D2.05 depth
res["F10_dowel_axis"] = [(round(a, 3), round(b, 3)) for a, b in thickness_along(S, (18.4, 0, -38.0), (0, 1, 0))]

# ---- journal ring / top plate
res["journal_ring_az45_z-6"] = [(round(p, 3), round(q, 3)) for p, q in thickness_along(S, (0, 0, -6.0), (math.cos(math.radians(45)), math.sin(math.radians(45)), 0))]
res["top_plate_(0,17)"] = vert(0, 17.5, -2.8)

# ---- windows: back window and +X end window extents (z where the back wall is absent at y 12)
def gap_z(x, y):
    iv = thickness_along(S, (x, y, 10), (0, 0, -1))
    return [(round(10 - b, 3), round(10 - a, 3)) for a, b in iv]
res["back_wall_column_x-13.7_y12"] = gap_z(-13.7, 12.0)
res["end_wall_column_x24.3_y-2"] = gap_z(24.3, -2.0)

# ---- T_cap, F15 screw, T_most, washer
cap = read_stl("T_cap"); scr = read_stl("skr_F15"); most = read_stl("T_most"); wsh = read_stl("pd_F15"); gear = read_stl("koleso_pan")
res["T_cap_bbox"] = [round(float(v), 3) for v in (cap[..., 0].min(), cap[..., 0].max(), cap[..., 2].min(), cap[..., 2].max())]
res["T_cap_radial_z-44"] = [(round(a, 3), round(b, 3)) for a, b in thickness_along(cap, (0, 0, -44.0), (1, 0, 0))]
res["T_cap_radial_z-46.1"] = [(round(a, 3), round(b, 3)) for a, b in thickness_along(cap, (0, 0, -46.1), (1, 0, 0))]
res["F15_screw_z"] = [round(float(scr[..., 2].min()), 3), round(float(scr[..., 2].max()), 3)]
res["T_most_z"] = [round(float(most[..., 2].min()), 3), round(float(most[..., 2].max()), 3)]
res["washer_z_r"] = [round(float(wsh[..., 2].min()), 3), round(float(wsh[..., 2].max()), 3), round(float(np.abs(wsh[..., 0]).max()), 3)]
res["F15_engagement_in_T_most"] = round(res["T_most_z"][1] - res["F15_screw_z"][0], 3)
res["gear_z"] = [round(float(gear[..., 2].min()), 3), round(float(gear[..., 2].max()), 3)]
res["gear_bore_r"] = round(float(interval_at(gear, (0, 0, -43.9), (1, 0, 0), 5.0)[0]), 3)
res["gear_tip_r"] = round(float(np.hypot(gear[..., 0], gear[..., 1]).max()), 3)
res["washer_overlap_on_gear"] = round(res["washer_z_r"][2] - res["gear_bore_r"], 3)
res["P_sachta_bbox_z"] = [round(float(S[..., 2].min()), 3), round(float(S[..., 2].max()), 3)]
res["P_sachta_rmax"] = round(float(np.hypot(S[..., 0], S[..., 1]).max()), 3)

json.dump(res, open(f"{OUT}/m01_measure.json", "w"), indent=1, default=float)
print(json.dumps(res, indent=1, default=float)[:12000])
