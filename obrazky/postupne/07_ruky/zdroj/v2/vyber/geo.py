"""JUDGE (vyber): own solid point models of the K3 drive parts (LEFT, frame B; right = mirror x -> -x).
Written independently from the K3 numbers in concept.md / the K3 summary (not importing k3_parts.py).
Every part -> dense SOLID samples (surface + interior), step h.  Parameters can be overridden (variants)."""
import math
import numpy as np

YA, ZA = 3.0, -17.0          # shoulder axis || X
X_SURF = 46.756


def bevel(z1, z2, m, b, apex_x, hub=None):
    """straight bevel pair, Sigma 90, apex O=(apex_x, YA, ZA); pinion axis vertical (below O), gear axis = shoulder axis (+X side).
    returns dict with (axial, radius) envelope polygons: pinion in (z, r), gear in (x, r)"""
    d1 = math.atan2(z1, z2); d2 = math.pi / 2 - d1
    r1, r2 = m * z1 / 2, m * z2 / 2
    Re = math.hypot(r1, r2); k = (Re - b) / Re
    ha, hf = m, 1.25 * m
    # pinion: axial distance below the apex (positive down)
    heel_ax1 = r2                         # pitch circle r1 at axial r2 below O
    crown1 = (heel_ax1 - ha * math.sin(d1), r1 + ha * math.cos(d1))
    root1 = (heel_ax1 + hf * math.sin(d1), r1 - hf * math.cos(d1))
    toe_tip1 = (k * crown1[0], k * crown1[1])
    # gear: axial distance outboard of the apex (positive +X)
    heel_ax2 = r1
    crown2 = (heel_ax2 - ha * math.sin(d2), r2 + ha * math.cos(d2))
    root2 = (heel_ax2 + hf * math.sin(d2), r2 - hf * math.cos(d2))
    toe_tip2 = (k * crown2[0], k * crown2[1])
    return dict(d1=math.degrees(d1), d2=math.degrees(d2), Re=Re, r1=r1, r2=r2,
                pin=dict(toe_z=ZA - toe_tip1[0], toe_r=toe_tip1[1], crown_z=ZA - crown1[0], crown_r=crown1[1],
                         root_z=ZA - root1[0], root_r=root1[1]),
                gear=dict(toe_x=apex_x + toe_tip2[0], toe_r=toe_tip2[1], crown_x=apex_x + crown2[0], crown_r=crown2[1],
                          root_x=apex_x + root2[0], root_r=root2[1]))


def inpoly(Q, P):
    """even-odd point in polygon (numpy)"""
    x, y = Q[:, 0], Q[:, 1]; ins = np.zeros(len(Q), bool)
    for i in range(len(P)):
        x1, y1 = P[i]; x2, y2 = P[(i + 1) % len(P)]
        c = ((y1 > y) != (y2 > y))
        with np.errstate(divide="ignore", invalid="ignore"):
            xi = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
        ins ^= c & (x < xi)
    return ins


def _fill_rev(prof, h):
    """prof: closed polygon in (a, r) (r >= 0); returns (a, r, phi) sample triples of the solid of revolution"""
    P = np.asarray(prof, float)
    a0, a1 = P[:, 0].min(), P[:, 0].max(); rmax = P[:, 1].max()
    A, R = np.meshgrid(np.arange(a0, a1 + 1e-9, h), np.arange(0.0, rmax + 1e-9, h), indexing="ij")
    Q = np.c_[A.ravel(), R.ravel()]
    ok = inpoly(Q, P)
    pts = [Q[ok]]
    for i in range(len(P)):
        p, q = P[i], P[(i + 1) % len(P)]
        n = max(2, int(np.hypot(*(q - p)) / (h * 0.5)))
        t = np.linspace(0, 1, n, endpoint=False)
        pts.append(p + t[:, None] * (q - p))
    Q = np.concatenate(pts)
    out = []
    for a, r in Q:
        n = max(1, int(2 * math.pi * r / h)) if r > 1e-6 else 1
        ph = np.linspace(0, 2 * math.pi, n, endpoint=False)
        out.append(np.c_[np.full(n, a), np.full(n, r), ph])
    return np.concatenate(out)


def rev(prof, axis, c1, c2, h=0.2):
    S = _fill_rev(prof, h)
    a, r, ph = S[:, 0], S[:, 1], S[:, 2]
    if axis == "x":      # c1 = y, c2 = z
        return np.c_[a, c1 + r * np.cos(ph), c2 + r * np.sin(ph)]
    return np.c_[c1 + r * np.cos(ph), c2 + r * np.sin(ph), a]     # axis z: c1 = x, c2 = y


def tube(axis, c1, c2, ri, ro, a0, a1, h=0.2):
    return rev([(a0, ri), (a1, ri), (a1, ro), (a0, ro)], axis, c1, c2, h)


def box(x0, x1, y0, y1, z0, z1, h=0.25):
    xs = np.r_[np.arange(x0, x1, h), x1]; ys = np.r_[np.arange(y0, y1, h), y1]; zs = np.r_[np.arange(z0, z1, h), z1]
    X, Y, Z = np.meshgrid(xs, ys, zs, indexing="ij")
    return np.c_[X.ravel(), Y.ravel(), Z.ravel()]


# ------------------------------------------------------------------ K3 parameters (concept.md, numbers as published)
K3 = dict(XV=39.0, z1=16, z2=24, m=0.5, b=2.4,
          servo=dict(L=23.2, W=12.1, H=21.5, sh=5.9, z_top=-45.0, ear_span=32.3, ear_z=(-51.8, -49.3),
                     boss_r=3.5, boss_h=1.0, spl_r=2.0, spl_top=-40.25, front=True),
          coupler=dict(r=4.0, z=(-44.0, -37.0)), shaft_v=dict(r=1.5, z0=-41.0),
          B1=dict(ri=1.5, ro=3.0, z=(-26.35, -23.85)), tongue=dict(ri=3.0, ro=4.4, z=(-26.85, -24.05)),
          shaft_a=dict(r=2.0, x1=61.5), A1=dict(x=(44.55, 47.05)), A2=dict(x=(48.55, 51.05)),
          boss=dict(ri=8.3, ro=12.8, x=(34.4, 38.4), stop=(11.6, 12.8, 38.4, 39.1)),
          gear_web=0.5)


def parts(p=K3, h=0.2):
    """dict name -> solid samples, LEFT side.  ROT_* rotate (must clear everything), STAT_* static new parts, SERVO"""
    XV = p["XV"]; bv = bevel(p["z1"], p["z2"], p["m"], p["b"], XV)
    pi, ge = bv["pin"], bv["gear"]
    out = {}
    s = p["servo"]
    # servo standing, shaft +Z on (XV, YA); long side toward -Y (front) if s["front"]
    if s["front"]:
        y0, y1 = YA - (s["L"] - s["sh"]), YA + s["sh"]
    else:
        y0, y1 = YA - s["sh"], YA + (s["L"] - s["sh"])
    x0, x1 = XV - s["W"] / 2, XV + s["W"] / 2
    zt = s["z_top"]; zb = zt - s["H"]
    e = (s["ear_span"] - s["L"]) / 2
    sv = [box(x0, x1, y0, y1, zb, zt, 0.3),
          box(x0, x1, y0 - e, y0, s["ear_z"][0], s["ear_z"][1], 0.3), box(x0, x1, y1, y1 + e, s["ear_z"][0], s["ear_z"][1], 0.3),
          tube("z", XV, YA, 0, s["boss_r"], zt, zt + s["boss_h"], h), tube("z", XV, YA, 0, s["spl_r"], zt + s["boss_h"], s["spl_top"], h)]
    SV = np.concatenate(sv)
    ch = s.get("ear_ch", 0.0)
    if ch > 0:      # 45 deg chamfer (leg ch) on the outboard (+x) corners of both ear tips
        eo = (SV[:, 1] < y0) | (SV[:, 1] > y1)
        tipd = np.minimum(SV[:, 1] - (y0 - e), (y1 + e) - SV[:, 1])     # distance from the ear tip (along y)
        cut = eo & ((x1 - SV[:, 0]) + tipd < ch)
        SV = SV[~cut]
        # add the chamfer face samples
        tt = np.linspace(0, ch, 12)
        zz = np.arange(s["ear_z"][0], s["ear_z"][1] + 1e-6, 0.25)
        for ytip, sgn in ((y0 - e, +1), (y1 + e, -1)):
            F = np.array([(x1 - (ch - t), ytip + sgn * t, z) for t in tt for z in zz])
            SV = np.r_[SV, F]
    out["SERVO"] = SV
    # cable exit (assumed at the far end, bottom), 3 long
    yc = y0 - 3.0 if s["front"] else y1 + 3.0
    out["SERVO_cable"] = box(XV - 2.0, XV + 2.0, min(yc, y0 if s["front"] else y1), max(yc, y0 if s["front"] else y1), zb, zb + 3.0, 0.25)
    c = p["coupler"]
    out["ROT_V_coupler"] = tube("z", XV, YA, 0, c["r"], c["z"][0], c["z"][1], h)
    out["ROT_V_shaft"] = tube("z", XV, YA, 0, p["shaft_v"]["r"], p["shaft_v"]["z0"], pi["toe_z"], h)
    # pinion envelope (hubless): toe face -> tip cone -> heel crown -> back face at root height
    prof = [(pi["toe_z"], 0.0), (pi["toe_z"], pi["toe_r"]), (pi["crown_z"], pi["crown_r"]), (pi["root_z"], pi["crown_r"]),
            (pi["root_z"], 0.0)]
    out["ROT_V_pinion"] = rev([(a, r) for a, r in prof], "z", XV, YA, h)
    gb = ge["root_x"] + p["gear_web"]
    prof = [(ge["toe_x"], 0.0), (ge["toe_x"], ge["toe_r"]), (ge["crown_x"], ge["crown_r"]), (ge["root_x"], ge["crown_r"]),
            (ge["root_x"], ge["root_r"]), (gb, ge["root_r"]), (gb, 0.0)]
    out["ROT_A_gear"] = rev(prof, "x", YA, ZA, h)
    out["ROT_A_shaft"] = tube("x", YA, ZA, 0, p["shaft_a"]["r"], ge["toe_x"], p["shaft_a"]["x1"], h)
    out["BRG_B1"] = tube("z", XV, YA, p["B1"]["ri"], p["B1"]["ro"], *p["B1"]["z"], h=h)
    out["BRG_A1"] = tube("x", YA, ZA, 2.0, 3.5, *p["A1"]["x"], h=h)
    out["BRG_A2"] = tube("x", YA, ZA, 2.0, 3.5, *p["A2"]["x"], h=h)
    b = p["boss"]
    out["STAT_boss"] = np.concatenate([tube("x", YA, ZA, b["ri"], b["ro"], *b["x"], h=h),
                                       tube("x", YA, ZA, b["stop"][0], b["stop"][1], b["stop"][2], b["stop"][3], h=h)])
    t = p["tongue"]
    out["STAT_tongue"] = tube("z", XV, YA, t["ri"], t["ro"], *t["z"], h=h)
    return out, bv


def mirror(P):
    return {k: v * np.array([-1.0, 1.0, 1.0]) for k, v in P.items()}


if __name__ == "__main__":
    P, bv = parts()
    print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in bv.items()})
    for k, v in P.items():
        print("%-15s n %7d bbox %s" % (k, len(v), np.round(np.r_[v.min(0), v.max(0)], 2)))
