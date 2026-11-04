"""
NOVA mini (v8) - HEAD variant A "ako na fotke" (HA01..HA06).  CONCEPT model.
Run from the repo root:  /opt/venv/cad/bin/python -m nova_v8.head_a
Exports STL + manifest "head_a" into build_v8/ (never into build/, which holds the finished v7.3).

Scaled, refined sibling of the v7.3 / R01 head for a 3.5" 480x320 display (ESP32-S3 board).
All shared numbers come from nova_v8/concept.py (HEAD, HEAD_A, NECK); the constants in the
"local concept constants" block are only construction values (wall, gaps, fillets) of this sketch.
Concept level: clean outer surfaces, real wall thickness and seams, no bosses / snaps / screws.

Parts (sub "head_a", joint "J3" = head tilt about X through NECK.tilt_axis y=0 z=126)
  HA01     Hlavny obal hlavy     white        rounded box 106 x 66 x 74 (front-view R26, back loop R20),
                                              2.2 wall, open front, underside pocket for the Ø30 tilt barrel
  HA02     Zadny kryt hlavy      white        back cover 88 x 50 R15 projected on the rear, 0.6 seam
  HA03     Predny ram            black        frame 101 x 69 R23.5, 5 mm proud, glass seat, skirt
  HA04     Sklo displeja         glass        92 x 60 R16 x 1.0, flat, glossy black print
  HA04C    Okienko kamery        black_gloss  RENDER-ONLY camera dot in the top print band
  HA04E    Obsah displeja - oci  eye          RENDER-ONLY two warm pill eyes 10.5 x 17.5
  HA05-R/L Ucho prave / lave     black        Ø28 ear discs, 4 mm proud, slightly domed face
  HA06-R/L LED kruzok ucha       cyan_led     Ø23 / Ø17 light-guide rings
"""
from __future__ import annotations

import math
import os
import sys
import time

from build123d import (Axis, Box, BuildSketch, Compound, Cylinder, Edge, Face, Locations, Plane, Pos,
                       RectangleRounded, Rot, ShapeList, SlotOverall, Solid, Sphere, Vector, Wire, chamfer, extrude,
                       fillet, mirror, offset)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from nova.cad.common import PartRec, export_parts  # noqa: E402
from nova_v8 import concept as C  # noqa: E402

OUT_DIR = os.path.join(ROOT, "build_v8")
SUB = "head_a"

HA = C.HEAD_A
W, HH = HA["w"], HA["h"]                          # 106 x 74
Y0, Y1 = HA["y0"], HA["y1"]                       # -33 (front rim plane) .. +33 (back)
Z0, Z1, ZC = C.HEAD["z0"], C.HEAD["z1"], C.HEAD["zc"]   # 116 .. 190, centre 153
R_FV, R_BACK = HA["r_front_view"], HA["r_back"]   # 26, 20
BZ, GL, EAR, EYE = HA["bezel"], HA["glass"], HA["ear"], HA["eyes"]
TILT_Y, TILT_Z = C.NECK["tilt_axis"]["y"], C.NECK["tilt_axis"]["z"]   # 0, 126
BARREL_R, BARREL_LEN = C.NECK["barrel_d"] / 2, C.NECK["barrel_len"]   # 15, 30

# ---- local concept constants (construction values, not shared dimensions) ------------------
WALL = 2.2                 # shell wall
FRONT_GAP = 0.3            # uniform gap bezel <-> shell opening (white rim 2.2 + gap 0.3 = 2.5)
R_RIM = 1.6                # round on the outer edge of the white front rim
BZ_FRONT_FILLET = 2.4      # soft front edge of the black frame
SKIRT_END = Y0 + 9.0       # bezel skirt reaches 9 mm into the shell (y = -24)
SKIRT_WALL = 1.8
GLASS_T = 1.0
GLASS_RECESS = 0.7         # glass front sits 0.7 behind the frame face
GLASS_CLR = 0.15
LEDGE_W, LEDGE_T = 2.5, 1.4    # glass support ledge in the frame
CAM_Z, CAM_D = 179.5, 2.8      # camera window centred in the 7 mm top print band (glass top z = 183)
BC = dict(w=88.0, h=50.0, r=15.0, seam=0.6)        # back cover outline projected along Y
SEAM_BREAK = 0.25          # chamfer on the visible seam edges
LEDGE_BACK_T, LEDGE_BACK_IN, LEDGE_BACK_OUT = 1.2, 2.5, 3.0   # ledge under the back-cover seam
POCKET = dict(w=BARREL_LEN + 6.0, d=40.0, r=12.0, top=TILT_Z + BARREL_R + 2.5)   # 36 x 40 R12, ceiling z 143.5
POCKET_WALL = 2.0
EAR_R = EAR["d"] / 2                               # 14
X_SIDE = W / 2                                     # 53
X_EAR_OUT = X_SIDE + EAR["protrude"]               # 57 (dome apex)
X_EAR_IN = X_SIDE - WALL - 1.2                     # 49.6 (inner end, hidden inside the shell)
EAR_HOLE_R = EAR_R + 0.2
EAR_DOME = 0.6             # sag of the domed ear face
EAR_FILLET = 1.6           # ear outer edge round
RING_PROUD = 0.15          # LED ring stands proud of the ear face
RING_DEPTH = 1.6
MIC_R = 0.5                # centre microphone hole Ø1

Y_BEZEL_FRONT = Y0 - BZ["protrude"]                # -38
Y_GLASS_FRONT = Y_BEZEL_FRONT + GLASS_RECESS       # -37.3
Y_GLASS_BACK = Y_GLASS_FRONT + GLASS_T             # -36.3
GZ = GL["zc"]

assert abs((W - BZ["w"]) / 2 - (WALL + FRONT_GAP)) < 1e-9          # rim 2.5 = wall + gap
assert abs((HH - BZ["h"]) / 2 - (WALL + FRONT_GAP)) < 1e-9
assert abs(R_FV - BZ["r"] - (WALL + FRONT_GAP)) < 1e-9


# ===========================================================================================
# helpers
# ===========================================================================================

def plane_y(y, cx=0.0, cz=ZC):
    """Plane at y with normal +Y (u = +X), centred at (cx, cz)."""
    return Plane(origin=(cx, y, cz), x_dir=(1, 0, 0), z_dir=(0, 1, 0))


def rr_prism_y(w, h, r, y0, y1, cx=0.0, cz=ZC):
    with BuildSketch(plane_y(y0, cx, cz)) as sk:
        RectangleRounded(w, h, r)
    return extrude(sk.sketch, y1 - y0)


def rr_prism_z(w, d, r, z0, z1, cx=0.0, cy=0.0):
    with BuildSketch(Plane.XY.offset(z0)) as sk:
        with Locations((cx, cy)):
            RectangleRounded(w, d, r)
    return extrude(sk.sketch, z1 - z0)


def cyl_x(r, x0, x1, y, z):
    lo, hi = min(x0, x1), max(x0, x1)
    return Pos((lo + hi) / 2, y, z) * Rot(0, 90, 0) * Cylinder(r, hi - lo)


def cyl_y(r, y0, y1, x, z):
    lo, hi = min(y0, y1), max(y0, y1)
    return Pos(x, (lo + hi) / 2, z) * Rot(90, 0, 0) * Cylinder(r, hi - lo)


def check(name, s, vmin=None):
    if not s.is_valid:
        raise RuntimeError(f"{name}: invalid solid")
    if vmin is not None and s.volume < vmin:
        raise RuntimeError(f"{name}: volume {s.volume:.0f} < {vmin}")
    return s


def retry(fn, label, tries=4):
    """OCC booleans run in parallel mode - retry rare non-deterministic failures."""
    err = None
    for _ in range(tries):
        try:
            out = fn()
            if out is not None and out.is_valid and out.volume > 0:
                return out
        except Exception as ex:  # pragma: no cover
            err = ex
    raise RuntimeError(f"{label}: boolean failed {tries}x ({err})")


def rr_dist(x, z, w, h, r, cz=ZC):
    """Signed distance of (x, z) to a rounded rectangle w x h radius r centred at (0, cz)."""
    qx = abs(x) - (w / 2 - r)
    qz = abs(z - cz) - (h / 2 - r)
    return math.hypot(max(qx, 0.0), max(qz, 0.0)) + min(max(qx, qz), 0.0) - r


def rr_dist_xy(x, y, w, d, r, cy=0.0):
    qx = abs(x) - (w / 2 - r)
    qy = abs(y - cy) - (d / 2 - r)
    return math.hypot(max(qx, 0.0), max(qy, 0.0)) + min(max(qx, qy), 0.0) - r


def edges_where(shape, pred):
    out = []
    for e in shape.edges():
        pts = [e.position_at(t) for t in (0.0, 0.25, 0.5, 0.75, 1.0)]
        if all(pred(p) for p in pts):
            out.append(e)
    return ShapeList(out)


def try_fillet(shape, edges, r, label):
    if not edges:
        print(f"  ({label}: no edges)")
        return shape
    try:
        out = fillet(edges, r)
        if out.is_valid and abs(out.volume - shape.volume) < 0.05 * shape.volume:
            return out
        print(f"  ({label}: fillet result rejected)")
    except Exception as ex:  # pragma: no cover
        print(f"  ({label}: fillet R{r} skipped: {ex})")
    return shape


def try_chamfer(shape, edges, d, label):
    if not edges:
        print(f"  ({label}: no edges)")
        return shape
    try:
        out = chamfer(edges, d)
        if out.is_valid and abs(out.volume - shape.volume) < 0.05 * shape.volume:
            return out
        print(f"  ({label}: chamfer result rejected)")
    except Exception as ex:  # pragma: no cover
        print(f"  ({label}: chamfer {d} skipped: {ex})")
    return shape


# ===========================================================================================
# HA01 / HA02 - white shell + back cover
# ===========================================================================================

def head_body():
    """Outer body without the front rim round: silhouette R26 // Y, back loop R20."""
    body = rr_prism_y(W, HH, R_FV, Y0, Y1)
    body = fillet(body.edges().group_by(Axis.Y)[-1], R_BACK)
    return body


def shells():
    body = head_body()
    # open-front shell (the opening face borders no fillet -> offset with openings is reliable)
    front = body.faces().sort_by(Axis.Y)[0]
    shell = offset(body, amount=-WALL, openings=[front])
    if shell.volume > 0.5 * body.volume:          # offset silently returned the unchanged solid
        # fallback documented in CLAUDE.md: body - inner, then open the front with a prism
        inner = offset(body, amount=-WALL)
        shell = body - inner
        shell = retry(lambda: shell - rr_prism_y(W - 2 * WALL, HH - 2 * WALL, R_FV - WALL, Y0 - 2, Y0 + WALL + 0.5),
                      "front opening")
    shell = check("shell", shell)
    # white rim: soft outer edge, tiny break on the inner edge
    rim_out = edges_where(shell, lambda p: abs(p.Y - Y0) < 0.02 and abs(rr_dist(p.X, p.Z, W, HH, R_FV)) < 0.02)
    shell = try_fillet(shell, rim_out, R_RIM, "rim outer")
    iw, ih, ir = W - 2 * WALL, HH - 2 * WALL, R_FV - WALL
    rim_in = edges_where(shell, lambda p: abs(p.Y - Y0) < 0.02 and abs(rr_dist(p.X, p.Z, iw, ih, ir)) < 0.02)
    shell = try_fillet(shell, rim_in, 0.2, "rim inner")
    shell = check("shell", shell)

    # ---- split off the back cover (projected rounded rectangle along Y) ----
    yb = 0.0
    h02 = shell & rr_prism_y(BC["w"], BC["h"], BC["r"], yb, Y1 + 5)
    s = BC["seam"]
    h01 = shell - rr_prism_y(BC["w"] + 2 * s, BC["h"] + 2 * s, BC["r"] + s, yb, Y1 + 5)
    h02 = h02.solids()[0] if len(h02.solids()) == 1 else h02
    h01 = h01.solids()[0] if len(h01.solids()) == 1 else h01
    skin = Compound(body.faces())

    def seam_edges(shape, w, h, r):
        return edges_where(shape, lambda p: p.Y > 10 and abs(rr_dist(p.X, p.Z, w, h, r)) < 0.03
                           and skin.distance_to(Vector(p.X, p.Y, p.Z)) < 0.03)

    h02 = try_chamfer(h02, seam_edges(h02, BC["w"], BC["h"], BC["r"]), SEAM_BREAK, "HA02 seam")
    h01 = try_chamfer(h01, seam_edges(h01, BC["w"] + 2 * s, BC["h"] + 2 * s, BC["r"] + s), SEAM_BREAK, "HA01 seam")

    # ---- seam backing ledge: the cover edge rests on it and the 0.6 seam never shows the hollow inside ----
    inner = offset(body, amount=-WALL)
    inner2 = offset(body, amount=-(WALL + LEDGE_BACK_T))
    slab = Pos(0, (yb + Y1 + 5) / 2, ZC) * Box(2 * W, Y1 + 5 - yb, 2 * HH)
    band = retry(lambda: (inner & slab) - (inner2 & slab), "ledge band")
    lo = s + LEDGE_BACK_OUT
    ring = (rr_prism_y(BC["w"] + 2 * lo, BC["h"] + 2 * lo, BC["r"] + lo, yb, Y1 + 5)
            - rr_prism_y(BC["w"] - 2 * LEDGE_BACK_IN, BC["h"] - 2 * LEDGE_BACK_IN, BC["r"] - LEDGE_BACK_IN,
                         yb - 1, Y1 + 6))
    h01 = retry(lambda: h01 + (band & ring), "ledge")

    # ---- underside pocket for the Ø30 tilt barrel (closed, 2 mm walls) ----
    pw, pd, pr, ptop = POCKET["w"], POCKET["d"], POCKET["r"], POCKET["top"]
    pocket_out = rr_prism_z(pw + 2 * POCKET_WALL, pd + 2 * POCKET_WALL, pr + POCKET_WALL,
                            Z0 - 1, ptop + POCKET_WALL, cy=TILT_Y)
    pocket_out = fillet(pocket_out.edges().group_by(Axis.Z)[-1], 4.0)
    pocket_in = rr_prism_z(pw, pd, pr, Z0 - 5, ptop, cy=TILT_Y)
    pocket_in = fillet(pocket_in.edges().group_by(Axis.Z)[-1], 3.0)
    h01 = retry(lambda: h01 + (pocket_out & body), "pocket walls")
    h01 = retry(lambda: h01 - pocket_in, "pocket")
    e_pk = edges_where(h01, lambda p: abs(p.Z - Z0) < 0.02 and abs(rr_dist_xy(p.X, p.Y, pw, pd, pr, TILT_Y)) < 0.02)
    h01 = try_fillet(h01, e_pk, 1.0, "pocket rim")

    # ---- ear holes ----
    for sx in (-1, 1):
        h01 = retry(lambda: h01 - cyl_x(EAR_HOLE_R, sx * (X_SIDE - WALL - 1.0), sx * (X_SIDE + 3.0),
                                        EAR["y"], EAR["z"]), "ear hole")
    e_ear = edges_where(h01, lambda p: abs(abs(p.X) - X_SIDE) < 1.5
                        and abs(math.hypot(p.Y - EAR["y"], p.Z - EAR["z"]) - EAR_HOLE_R) < 0.02
                        and skin.distance_to(Vector(p.X, p.Y, p.Z)) < 0.03)
    h01 = try_fillet(h01, e_ear, 0.3, "ear hole edge")
    return check("HA01", h01, vmin=20000), check("HA02", h02, vmin=3000)


# ===========================================================================================
# HA03 bezel, HA04 glass, HA04C camera window, HA04E eyes
# ===========================================================================================

def bezel():
    bw, bh, br = BZ["w"], BZ["h"], BZ["r"]
    b = rr_prism_y(bw, bh, br, Y_BEZEL_FRONT, SKIRT_END)
    b = fillet(b.edges().group_by(Axis.Y)[0], BZ_FRONT_FILLET)
    gw, gh, gr = GL["w"] + 2 * GLASS_CLR, GL["h"] + 2 * GLASS_CLR, GL["r"] + GLASS_CLR
    y_ledge0 = Y_GLASS_BACK + 0.1                     # adhesive
    y_ledge1 = y_ledge0 + LEDGE_T
    b = b - rr_prism_y(gw, gh, gr, Y_BEZEL_FRONT - 1, y_ledge0, cz=GZ)
    b = b - rr_prism_y(GL["w"] - 2 * LEDGE_W, GL["h"] - 2 * LEDGE_W, GL["r"] - LEDGE_W,
                       y_ledge0 - 0.5, y_ledge1 + 0.01, cz=GZ)
    b = b - rr_prism_y(bw - 2 * SKIRT_WALL, bh - 2 * SKIRT_WALL, br - SKIRT_WALL, y_ledge1, SKIRT_END + 1)
    e_in = edges_where(b, lambda p: abs(p.Y - Y_BEZEL_FRONT) < 0.02 and abs(rr_dist(p.X, p.Z, gw, gh, gr, GZ)) < 0.02)
    b = try_fillet(b, e_in, 0.4, "HA03 seat edge")
    return check("HA03", b, vmin=3000)


def glass():
    g = rr_prism_y(GL["w"], GL["h"], GL["r"], Y_GLASS_FRONT, Y_GLASS_BACK, cz=GZ)
    g = try_fillet(g, g.edges().group_by(Axis.Y)[0], 0.3, "HA04 C-cut")
    return check("HA04", g)


def camera_window():
    """Render-only lens: a very low spherical cap (catches a highlight like the lens in R01)."""
    r, sag = CAM_D / 2, 0.2
    rs = (r * r + sag * sag) / (2 * sag)
    sph = Pos(0, Y_GLASS_FRONT - sag + rs, CAM_Z) * Sphere(rs)
    lens = sph & cyl_y(r, Y_GLASS_FRONT - 1.0, Y_GLASS_FRONT, 0.0, CAM_Z)
    return check("HA04C", lens)


def eyes():
    t = 0.15
    out = None
    for sx in (-1, 1):
        with BuildSketch(plane_y(Y_GLASS_FRONT - t, sx * EYE["x"], EYE["z"])) as sk:
            SlotOverall(EYE["h"], EYE["w"], rotation=90)        # stadium, R = w/2
        e = extrude(sk.sketch, t)
        out = e if out is None else out + e
    return check("HA04E", out)


# ===========================================================================================
# HA05 ears + HA06 LED rings (built for the LEFT ear, +X, revolved about the ear axis)
# ===========================================================================================

EAR_RS = (EAR_R ** 2 + EAR_DOME ** 2) / (2 * EAR_DOME)    # dome sphere radius
EAR_SC = X_EAR_OUT - EAR_RS                               # dome sphere centre on the ear axis


def dome_x(r, extra=0.0):
    rr = EAR_RS + extra
    return EAR_SC + math.sqrt(rr * rr - r * r)


def dome_pt(r, extra=0.0):
    return (dome_x(r, extra), r)


def dome_arc(r0, r1, extra=0.0):
    return ("A", dome_pt((r0 + r1) / 2, extra), dome_pt(r1, extra))


def revolve_x(segs, start):
    def v(p):
        return Vector(p[0], 0.0, p[1])
    edges, cur = [], start
    for sg in segs:
        if sg[0] == "L":
            edges.append(Edge.make_line(v(cur), v(sg[1])))
            cur = sg[1]
        else:
            edges.append(Edge.make_three_point_arc(v(cur), v(sg[1]), v(sg[2])))
            cur = sg[2]
    if math.dist(cur, start) > 1e-6:
        edges.append(Edge.make_line(v(cur), v(start)))
    return Solid.revolve(Face(Wire(edges)), 360, Axis.X)


def ear_left():
    R = EAR_R
    ro, ri = EAR["ring_od"] / 2, EAR["ring_id"] / 2
    g_o, g_i = ro + 0.1, ri - 0.1
    ring_bot = dome_x(ri) - RING_DEPTH
    f = EAR_FILLET                                            # exact tangent fillet cylinder -> dome
    fc_r = R - f
    fc_x = EAR_SC + math.sqrt((EAR_RS - f) ** 2 - fc_r ** 2)
    k = EAR_RS / (EAR_RS - f)
    t_dome = (EAR_SC + (fc_x - EAR_SC) * k, fc_r * k)
    t_cyl = (fc_x, R)
    a_mid = math.atan2(t_dome[1] - fc_r, t_dome[0] - fc_x) / 2 + math.pi / 4
    f_mid = (fc_x + f * math.cos(a_mid), fc_r + f * math.sin(a_mid))
    segs = [
        ("L", (X_EAR_IN, R)),
        ("L", t_cyl),
        ("A", f_mid, t_dome),
        dome_arc(t_dome[1], g_o),
        ("L", (ring_bot, g_o)),
        ("L", (ring_bot, g_i)),
        ("L", dome_pt(g_i)),
        dome_arc(g_i, MIC_R),
        ("L", (X_EAR_IN, MIC_R)),
    ]
    disc = revolve_x(segs, (X_EAR_IN, MIC_R))
    e = 0.15
    rsegs = [
        ("L", (ring_bot, ro)),
        ("L", (dome_x(ro, RING_PROUD) - e, ro)),
        ("L", dome_pt(ro - e, RING_PROUD)),
        dome_arc(ro - e, ri + e, RING_PROUD),
        ("L", (dome_x(ri, RING_PROUD) - e, ri)),
    ]
    ring = revolve_x(rsegs, (ring_bot, ri))
    ey, ez = EAR["y"], EAR["z"]
    return check("HA05", Pos(0, ey, ez) * disc, vmin=1000), check("HA06", Pos(0, ey, ez) * ring, vmin=50)


# ===========================================================================================

def build():
    h01, h02 = shells()
    ear_l, ring_l = ear_left()
    ear_r, ring_r = mirror(ear_l, Plane.YZ), mirror(ring_l, Plane.YZ)
    up, fy, ex = 90.0, 35.0, 28.0
    J = "J3"
    return [
        PartRec("HA01", "Hlavný obal hlavy", h01, "white", SUB, J, (0, 0, up),
                note="koncept: biely obal 106×66×74, rohy spredu R26, zadná hrana R20, stena 2.2, vybranie zdola pre valec náklonu Ø30"),
        PartRec("HA02", "Zadný kryt hlavy", h02, "white", SUB, J, (0, fy, up),
                note="servisný kryt 88×50 R15 premietnutý na zadnú plochu, škára 0.6"),
        PartRec("HA03", "Predný rám", bezel(), "black", SUB, J, (0, -fy, up),
                note="čierny rám 101×69 R23.5, vystupuje 5 mm, biely lem 2.5 mm"),
        PartRec("HA04", "Sklo displeja", glass(), "glass", SUB, J, (0, -fy - 8, up),
                note="ploché sklo 92×60 R16, čierna potlač, displej 3.5\" 480×320"),
        PartRec("HA04C", "Okienko kamery", camera_window(), "black_gloss", SUB, J, (0, -fy - 8, up),
                note="len objekt pre render: okienko kamery v hornom páse potlače"),
        PartRec("HA04E", "Obsah displeja – oči", eyes(), "eye", SUB, J, (0, -fy - 8, up),
                note="len objekt pre render: dve teplé pilulky 10.5×17.5"),
        PartRec("HA05-R", "Ucho pravé", ear_r, "black", SUB, J, (-ex, 0, up),
                note="čierny disk Ø28, vystupuje 4 mm, dotyk + mikrofón"),
        PartRec("HA05-L", "Ucho ľavé", ear_l, "black", SUB, J, (ex, 0, up),
                note="čierny disk Ø28, vystupuje 4 mm, dotyk + mikrofón"),
        PartRec("HA06-R", "LED krúžok ucha pravý", ring_r, "cyan_led", SUB, J, (-ex, 0, up),
                note="svetlovod Ø23/Ø17, tyrkysová LED"),
        PartRec("HA06-L", "LED krúžok ucha ľavý", ring_l, "cyan_led", SUB, J, (ex, 0, up),
                note="svetlovod Ø23/Ø17, tyrkysová LED"),
    ]


def overlaps(parts, tol=1.0):
    """Report volume intersections between parts (> tol mm3)."""
    bad = []
    for i, a in enumerate(parts):
        for b in parts[i + 1:]:
            ba, bb = a.shape.bounding_box(), b.shape.bounding_box()
            if (ba.min.X > bb.max.X or bb.min.X > ba.max.X or ba.min.Y > bb.max.Y or bb.min.Y > ba.max.Y
                    or ba.min.Z > bb.max.Z or bb.min.Z > ba.max.Z):
                continue
            try:
                common = a.shape & b.shape
                v = 0.0 if common is None else common.volume      # None = empty (parts only touch)
            except Exception:
                v = -1
            if v > tol or v < 0:
                bad.append((a.id, b.id, round(v, 2)))
    return bad


if __name__ == "__main__":
    t = time.time()
    parts = build()
    recs = export_parts(parts, SUB, step=False, out_dir=OUT_DIR)
    for p, r in zip(parts, recs):
        print(f"  {r['id']:8s} {r['mat']:11s} valid={p.shape.is_valid} size={r['bbox']['size']} "
              f"min={r['bbox']['min']} vol={r['volume_mm3']}")
    print("  overlaps:", overlaps(parts) or "none")
    print(f"[{SUB}] {len(recs)} parts exported in {time.time() - t:.1f}s -> {OUT_DIR}")
