"""NOVA mini - exterior form variant f1 "R01 moderny" (torso, base, arms) - build123d 0.13.
Run: /opt/venv/cad/bin/python exterior.py [names...]   -> cad/<name>.step, stl/<name>.stl, work/<name>.brep, parts.json
World frame (mm, Z up, floor z 0, FRONT -Y, robot RIGHT -X), every part at its assembly position, rest pose.

Surfaces: every visible surface is ONE loft of horizontal superellipse sections (form.py), sections arc-length
sampled (160 / 128 pts, periodic splines), stations every 1.5 mm (torso, base) / 1.0 mm (arms) along the profile arc.
Flat top / bottom zones are closed by 3 coplanar sections (tangent flat).  Walls = OCC offset of the outer loft
(exact normal wall).  Internal / feature cuts (holes, slots, seams) come after the shell, no fillets on the lofts."""
import sys, os, math, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build123d import (Vector, Edge, Wire, Face, Solid, Compound, Pos, Rot, Box, Cylinder, Location, Plane, Axis,
                       offset, fillet, extrude, export_step, export_brep, import_brep, Polyline, make_face, mirror,
                       revolve, Spline)
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.StlAPI import StlAPI_Writer
from OCP.BRepTools import BRepTools
import numpy as np
import form as F

OUT = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(OUT, "work")
SEC_N = 160
T_WALL, B_WALL, A_WALL = 2.2, 2.2, 2.0
SEAM = 0.45                                   # part seams (0.4 .. 0.6 on the surface)
TIMER = time.time()


def log(*a):
    print(f"[{time.time() - TIMER:6.1f}s]", *a, flush=True)


# ------------------------------------------------------------------ primitives
def wire_pts(pts, z):
    P = [Vector(x, y, z) for x, y in pts]
    n = len(P)
    return Wire([Edge.make_spline(P, periodic=True, parameters=[i / n for i in range(n + 1)])])


def one(s):
    if hasattr(s, "solids"):
        sl = s.solids()
        if len(sl) == 1:
            return Solid(sl[0].wrapped)
        if len(sl) > 1:
            return Compound(sl)
    return s


def box(x0, x1, y0, y1, z0, z1):
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Box(abs(x1 - x0), abs(y1 - y0), abs(z1 - z0))


def zcyl(r, z0, z1, x=0.0, y=0.0):
    return Pos(x, y, (z0 + z1) / 2) * Cylinder(r, z1 - z0)


def xcyl(r, x0, x1, y, z):
    x0, x1 = sorted((x0, x1))
    return Pos((x0 + x1) / 2, y, z) * Rot(0, 90, 0) * Cylinder(r, x1 - x0)


def ycyl(r, y0, y1, x, z):
    y0, y1 = sorted((y0, y1))
    return Pos(x, (y0 + y1) / 2, z) * Rot(90, 0, 0) * Cylinder(r, y1 - y0)


def se_prism(a, b, n, z0, z1, count=128):
    return Solid.make_loft([wire_pts(F.se_pts(a, b, n, count), z0), wire_pts(F.se_pts(a, b, n, count), z1)])


def capsule_y(w, h, xc, zc, y0, y1):
    """stadium (w along X, h along Z, fully rounded ends) extruded along Y from y0 to y1"""
    r = h / 2
    pts = []
    for i in range(33):
        t = -math.pi / 2 + math.pi * i / 32
        pts.append((xc + w / 2 - r + r * math.cos(t), zc + r * math.sin(t)))
    for i in range(33):
        t = math.pi / 2 + math.pi * i / 32
        pts.append((xc - w / 2 + r + r * math.cos(t), zc + r * math.sin(t)))
    return xz_prism(pts, y0, y1)


def rrect_y(w, h, r, xc, zc, y0, y1):
    """rounded rectangle (w x h, corner r) in XZ extruded along Y"""
    pts = []
    for cx, cz, a0 in ((w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90), (-w / 2 + r, -h / 2 + r, 180),
                       (w / 2 - r, -h / 2 + r, 270)):
        for i in range(13):
            t = math.radians(a0 + 90 * i / 12)
            pts.append((xc + cx + r * math.cos(t), zc + cz + r * math.sin(t)))
    return xz_prism(pts, y0, y1)


def xz_prism(pts, y0, y1):
    """closed polygon in XZ (list of (x, z)) extruded along Y from y0 to y1 (straight segments)"""
    w0 = Wire.make_polygon([Vector(x, y0, z) for x, z in pts], close=True)
    w1 = Wire.make_polygon([Vector(x, y1, z) for x, z in pts], close=True)
    return Solid.make_loft([w0, w1], ruled=True)


def xz_spline_prism(pts, y0, y1):
    """closed smooth (periodic spline) outline in XZ extruded along Y"""
    def w(y):
        P = [Vector(x, y, z) for x, z in pts]
        n = len(P)
        return Wire([Edge.make_spline(P, periodic=True, parameters=[i / n for i in range(n + 1)])])
    return Solid.make_loft([w(y0), w(y1)], ruled=True)


def yz_spline_prism(pts, x0, x1):
    def w(x):
        P = [Vector(x, y, z) for y, z in pts]
        n = len(P)
        return Wire([Edge.make_spline(P, periodic=True, parameters=[i / n for i in range(n + 1)])])
    return Solid.make_loft([w(x0), w(x1)], ruled=True)


def mesh_volume(shape, tol=0.02):
    """reliable volume (signed tetra sum of a tessellation; GProp is unreliable on periodic B-spline lofts)"""
    if shape is None:
        return 0.0
    try:
        if not shape.solids():
            return 0.0
    except Exception:
        return 0.0
    v, t = shape.tessellate(tol, 0.2)
    if not t:
        return 0.0
    V = np.array([[p.X, p.Y, p.Z] for p in v]); T = np.array(t)
    return float(np.einsum('ij,ij->i', V[T[:, 0]], np.cross(V[T[:, 1]], V[T[:, 2]])).sum() / 6)


def fine_stl(shape, fn, tol=0.01, ang=0.1):
    BRepTools.Clean_s(shape.wrapped)
    m = BRepMesh_IncrementalMesh(shape.wrapped, tol, False, ang, True)
    m.Perform()
    w = StlAPI_Writer()
    w.ASCIIMode = False
    w.Write(shape.wrapped, fn)


# ------------------------------------------------------------------ lofts
def loft_z(abfun, n, z0, z1, ds, start, flat0=True, flat1=True, k_flat=(1.0, 2.0, 3.0)):
    """loft of superellipse sections abfun(z) -> (a, b) between the flat ends z0, z1 (coplanar tangent sections)"""
    zs = F.stations(lambda z: abfun(z)[0], z0, z1, ds)
    secs = []
    if flat0:
        a, b = abfun(z0)
        for k in reversed(k_flat):
            secs.append(wire_pts(F.se_pts(a - k, b - k, n, SEC_N, start=start), z0))
    for z in zs:
        a, b = abfun(z)
        secs.append(wire_pts(F.se_pts(a, b, n, SEC_N, start=start), z))
    if flat1:
        a, b = abfun(z1)
        for k in k_flat:
            secs.append(wire_pts(F.se_pts(a - k, b - k, n, SEC_N, start=start), z1))
    s = one(Solid.make_loft(secs))
    log(f"  loft {len(secs)} sections valid={s.is_valid}")
    return s


# ================================================================== TORSO
PANEL_K, PANEL_Z0, PANEL_Z1, PANEL_M = 0.655, 51.0, 126.5, 5.0


def panel_outline(grow=0.0, n=240):
    """front panel outline in XZ: |x / (k A(z))|^m + |(z - zm) / hz|^m = 1 (seams parallel to the silhouette,
    rounded corners); grow = in-plane enlargement (seam gap)"""
    zm, hz = (PANEL_Z0 + PANEL_Z1) / 2, (PANEL_Z1 - PANEL_Z0) / 2 + grow
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        c, s = math.cos(t), math.sin(t)
        z = zm + hz * math.copysign(abs(s) ** (2 / PANEL_M), s)
        xs = PANEL_K * F.torso_ab(min(F.TZ1, max(F.TZ0, z)))[0] + grow
        x = xs * math.copysign(abs(c) ** (2 / PANEL_M), c)
        pts.append((x, z))
    return pts


def torso_parts():
    log("torso: outer loft")
    outer = loft_z(F.torso_ab, F.TN, F.TZ0, F.TZ1, 1.5, start=math.pi / 2)
    inner = offset(outer, amount=-T_WALL)
    log("torso: offset valid", inner.is_valid)
    shell = one(outer - inner)
    # collar seat ring (glue seat for the static B collar ring) under the top wall, shoulder cup collars
    seat = zcyl(31.0, 128.0, F.TZ1 - 0.6) - zcyl(28.35, 120, 140)
    cups = []
    for sg in (-1, 1):
        cup = xcyl(15.5, sg * 41.2, sg * 46.0, 2.0, 112.0) - xcyl(13.5, sg * 30, sg * 50, 2.0, 112.0)
        cups.append(cup & outer)
    shell = one(shell + seat + cups[0] + cups[1])
    log("torso: seat + cups fused")
    # holes: collar recess, shoulder pockets, J1 spline hole (in the bottom plate)
    shell = one(shell - zcyl(28.35, 125.0, 140.0))
    for sg in (-1, 1):
        shell = one(shell - xcyl(13.5, sg * 37.5, sg * 50.0, 2.0, 112.0))
    log("torso: shell valid", shell.is_valid)
    # ------------- front panel (seam follows the silhouette), light bar + grille slots
    log("torso: panel split")
    cut_in = xz_spline_prism(panel_outline(0.0), -60.0, 0.0)
    cut_out = xz_spline_prism(panel_outline(SEAM), -60.0, 0.0)
    panel = one(shell & cut_in)
    rear = one(shell - cut_out)
    bar = capsule_y(36.0, 4.5, 0.0, 101.5, -60, -20)
    grille = capsule_y(30.0, 3.0, 0.0, 83.5, -60, -20)
    panel = one(panel - bar - grille)
    log("torso: guides")
    # light guide: flush (0.1 under the skin), fills the slot through the wall + 1.0 mm lip inside (LED flex strip
    # behind it follows the crowned panel); grille insert recessed 0.8, 1.8 thick
    guide = one((capsule_y(35.6, 4.1, 0.0, 101.5, -60, -20) & offset(outer, amount=-0.1)) - inner)
    mesh = one((capsule_y(29.6, 2.6, 0.0, 83.5, -60, -20) & offset(outer, amount=-0.8)) - inner)
    log("torso: bottom plate")
    # ------------- bottom plate (seam on the flat underside, invisible)
    a0, b0 = F.torso_ab(F.TZ0)
    plate_cut = se_prism(a0 - 2.0, b0 - 2.0, F.TN, F.TZ0 - 1, F.TZ0 + T_WALL + 0.5)
    plate_gap = se_prism(a0 - 2.0 + SEAM, b0 - 2.0 + SEAM, F.TN, F.TZ0 - 1, F.TZ0 + T_WALL + 0.5)
    plate = one((rear & plate_cut) - zcyl(7.0, 40, 50, -18.0, 0.0))
    rear = one(rear - plate_gap)
    log("torso: parts valid", rear.is_valid, panel.is_valid, plate.is_valid, guide.is_valid, mesh.is_valid)
    return {"T_trup_zadny": (rear, "white", "T"), "T_predny_panel": (panel, "white", "T"),
            "T_dno": (plate, "white", "T"), "T_svetlovod": (guide, "glow", "T"),
            "T_mriezka": (mesh, "grey", "T")}, {"T_outer": outer, "T_inner": inner}


# ================================================================== BASE
def base_parts():
    log("base: outer loft")
    outer = loft_z(F.base_ab, F.BN, F.BZ0, F.BZ1, 1.5, start=0.0)
    inner = offset(outer, amount=-B_WALL)
    log("base: offset valid", inner.is_valid)
    shell = one(outer - inner)
    # bottom opening = foot outline (cell groups drop out when a bay cover = half of the foot is removed)
    shell = one(shell - se_prism(F.FOOT_A, F.FOOT_B, F.BN, F.BZ0 - 2, F.BZ0 + B_WALL + 0.5))
    # top: J1 opening r 29 + plinth seat (step r 35.5..37.5 at z 39)
    shell = one(shell - zcyl(35.5, 36.0, 42.0) - zcyl(37.5, 39.0, 42.0))
    # front: light bar slot 44 x 4 @ z 20, ToF window 16 x 7 R3 @ z 28.5; back: USB-C 9.5 x 3.8, switch D7, LED D2
    shell = one(shell - capsule_y(44.0, 4.0, 0.0, 20.0, -70, -40) - rrect_y(16.0, 7.0, 3.0, 0.0, 28.5, -70, -40))
    shell = one(shell - capsule_y(9.5, 3.8, 0.0, 33.2, 40, 70) - ycyl(3.5, 40, 70, 18.0, 27.5)
                - ycyl(1.0, 40, 70, -10.0, 33.2))
    log("base: shell valid", shell.is_valid)
    o01 = offset(outer, amount=-0.1)
    guide = one((capsule_y(43.6, 3.6, 0.0, 20.0, -70, -40) & o01) - inner)
    tof = one((rrect_y(15.6, 6.6, 2.8, 0.0, 28.5, -70, -40) & o01) - inner)
    led = one((ycyl(0.95, 40, 70, -10.0, 33.2) & o01) - inner)
    btn = one(ycyl(3.3, 51.1, 70, 18.0, 27.5) & offset(outer, amount=-0.4))
    # ------------- plinth ring (dark, static): flush r 29.2..35.4 @ z 40, soft raised lip r 35.4..37.4 up to z 41.2
    prof = [(29.2, 37.9), (35.4, 37.9), (35.4, 39.05), (37.4, 39.05), (37.4, 40.0)]
    for i in range(1, 24):                        # lip: smooth bump (raised cosine) r 37.4 -> 35.0, height 1.2
        t = i / 24
        r = 37.4 - 2.4 * t
        prof.append((r, 40.0 + 1.2 * math.sin(math.pi * t) ** 2))
    prof += [(35.0, 40.0), (29.2, 40.0)]
    from build123d import Plane as _P
    w = Wire.make_polygon([Vector(r, 0, z) for r, z in prof], close=True)
    plinth = one(revolve(Face(w), Axis.Z, 360))
    # ------------- dark foot: centre strip + 2 battery-bay covers (= half feet), z 6.0 .. 10.5
    foot = se_prism(F.FOOT_A, F.FOOT_B, F.BN, F.FOOT_Z0, F.FOOT_Z1)
    try:
        lo = [e for e in foot.edges() if abs(e.center().Z - F.FOOT_Z0) < 1e-3]
        foot = one(fillet(lo, 1.5))
    except Exception as ex:
        log("foot fillet failed", ex)
    foot = one(foot - se_prism(F.FOOT_A - 2.0, F.FOOT_B - 2.0, F.BN, F.FOOT_Z0 + 2.2, F.FOOT_Z1 + 1))
    for sx in (-1, 1):
        foot = one(foot - box(sx * 54 - 5.5, sx * 54 + 5.5, -17, 17, 0, 12))               # wheel slots
        for sy in (-1, 1):
            foot = one(foot - box(sx * 40 - 4.5, sx * 40 + 4.5, sy * 31 - 3.5, sy * 31 + 3.5, 0, 12))  # cliff windows
    for sy in (-1, 1):
        foot = one(foot - zcyl(7.0, 0, 12, 0.0, sy * 34.0))                                 # caster holes
    mid = one(foot & box(-80, 80, -6.5 + SEAM / 2, 6.5 - SEAM / 2, 0, 12))
    cov_f = one(foot & box(-80, 80, -80, -6.5 - SEAM / 2, 0, 12))
    cov_b = one(foot & box(-80, 80, 6.5 + SEAM / 2, 80, 0, 12))
    log("base: parts valid", shell.is_valid, plinth.is_valid, mid.is_valid, cov_f.is_valid, guide.is_valid)
    return {"Z_skrupina": (shell, "white", "B"), "Z_plint": (plinth, "black", "B"),
            "Z_noha_stred": (mid, "black", "B"), "Z_kryt_baterie_P": (cov_f, "black", "B"),
            "Z_kryt_baterie_Z": (cov_b, "black", "B"), "Z_svetlovod": (guide, "glow", "B"),
            "Z_okno_ToF": (tof, "glass", "B"), "Z_led_nabijania": (led, "glow", "B"),
            "Z_tlacidlo": (btn, "black", "B")}, {"Z_outer": outer, "Z_inner": inner}


# ================================================================== ARMS
def arm_stations(z0, z1, ds, n=40000, w=0.0):
    zz = np.linspace(z0, z1, n + 1)
    G = np.array([F.arm_sec(z, w) for z in zz])       # xi_c, a_in, a_out, b
    pts = np.column_stack([zz, G[:, 0] - G[:, 1], G[:, 0] + G[:, 2], G[:, 3]])
    S = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))])
    m = int(math.ceil(S[-1] / ds))
    return list(np.interp(S[-1] * np.arange(m + 1) / m, S, zz))


def arm_wire(z, scale=1.0, sign=-1, w=0.0):
    xc, ai, ao, b = F.arm_sec(z, w)
    P = F.arm_pts(xc, ai, ao, b, 128, start=0.8 * math.pi)   # loft seam on the inner face at y ~ +13 (away from
    #                                                          the servo window, the boss hole and the half seam)
    pts = [(sign * (xc + scale * (u - xc)), F.AY_C + scale * (v - F.AY_C)) for u, v in P]
    if sign > 0:
        pts = pts[::-1]
    return wire_pts(pts, z)


def _end_z(w, top):
    """z where the side-view closure factor is 0.14 (last section, then 2 coplanar closing sections)"""
    s = (1 - 0.14 ** 2.4) ** (1 / 2.4)
    if top:
        return F.AZ_AX + s * ((F.AZ_TOP - w) - F.AZ_AX)
    return (F.AZ_TIP + 13.0) - s * ((F.AZ_TIP + 13.0) - (F.AZ_TIP + w))


def arm_outer(sign=-1, w=0.0):
    z_lo, z_hi = _end_z(w, False), _end_z(w, True)
    zs = arm_stations(z_lo, z_hi, 1.0, w=w)
    secs = [arm_wire(z_lo, f, sign, w) for f in (0.4, 0.7)] + [arm_wire(z, 1.0, sign, w) for z in zs] + \
           [arm_wire(z_hi, f, sign, w) for f in (0.7, 0.4)]
    s = one(Solid.make_loft(secs))
    log(f"  arm loft (w {w}) {len(secs)} sections valid={s.is_valid} z {z_lo:.3f}..{z_hi:.3f}")
    return s


def arm_parts(sign=-1):
    tag = "R" if sign < 0 else "L"
    log(f"arm {tag}: outer loft")
    outer = arm_outer(sign)
    inner = arm_outer(sign, A_WALL)                    # cavity loft (offset() fails on the small closing caps)
    # cavity ends trimmed flat (z 48.5 / 124): the tiny closing caps of the cavity loft break the half split
    inner = one(inner & box(sign * 20, sign * 90, -30, 35, 48.5, 124.0))
    log(f"arm {tag}: cavity valid", inner.is_valid, round(mesh_volume(inner)))
    shell = one(outer - inner)
    # servo window in the inner face (case flush with the inner face), spline boss hole on the axis
    x_in = sign * 46.5
    win = box(x_in - sign * 1.5, x_in + sign * 3.0, -2.8, 6.8, 96.65, 117.35)
    seat = box(sign * 49.0, sign * 67.6, -2.8, 6.8, 96.65, 117.35)   # case seat: the domed outer wall would cut the
    #                                         case corners by 0.42 -> local pocket, wall >= 1.5 at the 4 case edges
    holes = [win, seat, xcyl(5.6, sign * 40, sign * 49, 2.0, 112.0)]
    # ONE-PIECE paddle (no clamshell seam): the servo slides in through its own window in the inner face (case
    # 20.5 x 9.4 footprint, shaft along X) and is bonded to the outer wall; the window is the resin drain opening
    paddle = shell
    for h in holes:
        paddle = one(paddle - h)
    cap = xcyl(12.5, sign * 44.2, sign * 46.5, 2.0, 112.0)
    try:
        cap = one(fillet(cap.edges(), 0.8))
    except Exception:
        pass
    cap = one(cap - xcyl(6.0, sign * 40, sign * 50, 2.0, 112.0))
    log(f"arm {tag}: parts valid", paddle.is_valid, cap.is_valid, round(mesh_volume(paddle)))
    g = "AR" if sign < 0 else "AL"
    return {f"A_{tag}_ruka": (paddle, "white", g), f"A_{tag}_kryt": (cap, "black", g)}, {f"A_{tag}_outer": outer, f"A_{tag}_inner": inner}


# ================================================================== main
def save(parts, aux):
    meta = json.load(open(os.path.join(OUT, "parts.json"))) if os.path.exists(os.path.join(OUT, "parts.json")) else {}
    for nm, (s, col, g) in parts.items():
        export_brep(s, os.path.join(WORK, nm + ".brep"))
        export_step(s, os.path.join(OUT, "cad", nm + ".step"))
        fine_stl(s, os.path.join(OUT, "stl", nm + ".stl"))
        bb = s.bounding_box()
        meta[nm] = {"color": col, "group": g, "valid": bool(s.is_valid), "volume_mm3": round(mesh_volume(s), 1),
                    "bbox": [[round(bb.min.X, 2), round(bb.min.Y, 2), round(bb.min.Z, 2)],
                             [round(bb.max.X, 2), round(bb.max.Y, 2), round(bb.max.Z, 2)]],
                    "stl": os.path.join(OUT, "stl", nm + ".stl"), "step": os.path.join(OUT, "cad", nm + ".step")}
        log("saved", nm, meta[nm]["valid"], meta[nm]["volume_mm3"], meta[nm]["bbox"])
    for nm, s in aux.items():
        export_brep(s, os.path.join(WORK, nm + ".brep"))
        fine_stl(s, os.path.join(WORK, nm + ".stl"))
    json.dump(meta, open(os.path.join(OUT, "parts.json"), "w"), indent=1)


if __name__ == "__main__":
    want = sys.argv[1:] or ["torso", "base", "arms"]
    if "torso" in want:
        save(*torso_parts())
    if "base" in want:
        save(*base_parts())
    if "arms" in want:
        for sg in (-1, 1):
            save(*arm_parts(sg))
    log("DONE")
