"""
NOVA – INTERNAL MECHANICS & ELECTRONICS (all parts internal=True).
Run:  /opt/venv/cad/bin/python -m nova.cad.internals

Spec v7.3 (nova/spec.py CHANGELOG, docs/SPEC.md §3, docs/REVIEW_NOTES.md part numbers).  Every part is built in
final assembly position.  sub = subassembly the part lives in, joint = group it moves with
(base "", torso J1, pan stage J2, head J3, arms J4/J5).

Part numbers
  * designed parts use the REVIEW_NOTES numbers (B06 B07 B09 B10 B11, T07 T08 T09 T10 T11, N03 N04 N05,
    H07 H11 H12 H13, A06),
  * bought electronics use the SPEC.md §3 numbers E1..E13 (suffix = instance),
  * bought mechanics: M1..M6 (bearings, spring, spline insert), W1 = 7-wire bundle (3 segments, one per
    joint group so posed renders stay consistent).

Packaging (see notes of each part and the report printed by build()):
  HEAD   E2 display clamped between the H03 ledge (0.5 foam) and the H11 front plate (y -44.6); H13 ESP32-S3
         board on 4 standoffs behind the plate; E3 UVC camera pressed onto the glass by H12; H07 ear PCBs
         (Ø29 discs, LEDs + centre MEMS mic) in the ear cups; H11 cheeks bolt to the N07 hubs at |x| 30.4.
  NECK   E6-T tilt servo on the tilt axis inside N06 (top face flush at x=-18, spline in the M6 Al insert of
         N07-R); M3 6703 in the N05 plug on the hollow pin of N07-L; M5 flat spiral spring x 9..12; N03 hub in
         the M2 61805 (T01 boss), N04 wave-washer clutch; E6-P pan servo hangs from the T07 pan bracket
         (bolted to the T01 bosses at x ±27) – body toward -Y.
  TORSO  T07 frame = 2 arm-servo towers (bolted to the T02 servo bosses y ±20) + low cross plate (E10) +
         pan bracket.  E6-R/L hang from the shoulder axis, outputs toward ±X into A06 drivers that run in
         M4 6702 bearings (sleeved into the T02 Ø23 bore) and key into the A02 hex web.  E1 compute module
         carrier vertical on the T08 sled, cooler toward the rear door.
  BASE   B06 J1 hub (6808 + GT2 72T) driven by E7 GM3506 on the B07 bracket; E9 slip ring; E8 2x18650 above
         the B08 hatch; E11 base board above the cells; E11-IO rear I/O board in B09; E5 speaker in the B11
         sealed box + duct to the rear grille; B10 + E13-B LED light box behind B03.
"""
from __future__ import annotations

import math

from build123d import Compound, Edge, Face, Plane, Pos, Rot, Solid, Vector, Wire, mirror

from nova import spec
from nova.cad.common import PartRec, run_module

# ---------------------------------------------------------------------------------------------------------
# shared spec numbers
# ---------------------------------------------------------------------------------------------------------
B = spec.BASE
T = spec.TORSO
NK = spec.NECK
H = spec.HEAD
ARM = spec.ARM
AX_Y, AX_Z = spec.TILT_AXIS["y"], spec.TILT_AXIS["z"]          # tilt axis // X
PX, PY = spec.PAN_AXIS["x"], spec.PAN_AXIS["y"]                 # pan / yaw axis // Z
SH_Y, SH_Z = T["shoulder"]["y"], T["shoulder"]["z"]             # shoulder axis // X
PB = NK["pan_bearing"]                                          # 61805
TH, CP = NK["tilt_housing"], NK["caps"]
EXPLODE_HEAD = (0.0, 0.0, 150.0)                                # head subassembly explode (head.py)

# ---- interfaces copied from the shell modules (local construction values there, not in spec) ---------
L_BAR = TH["barrel_len"]                     # 36  N06 barrel x -18 .. +18
R_BAR_IN = TH["barrel_d"] / 2 - 2.0          # 19  N06 inner radius (wall 2, neck.py)
X_CAP0 = L_BAR / 2 + CP["gap"]               # 18.6 N07 inner face
X_HUB_END = X_CAP0 + CP["len"] + CP["hub_len"]   # 30.4 N07 hub end face = H11 cheek inner face
PIN_OD, PIN_ID, PIN_X_END = 17.0, 13.0, 9.0  # N07-L hollow pin (6703 bore 17, cable tunnel 13)
INSERT_D, INSERT_DEPTH = 20.0, 5.0           # N07-R pocket for the Al spline insert (M6)
SLOT_W, SLOT_H = TH["cable_slot"]            # 14 x 8 cable passage N06 spigot (long // X)
N03_TOP = NK["cone"]["z0"]                   # 149  N06 spigot sits on the N03 hub top
N03_FLANGE = (15.0, 1.5)                     # Ø30 x 1.5 (REVIEW_NOTES N03)
N03_SCREW_Y = 6.4                            # 2x M2.5 N06 -> N03 (neck.py)
N02_KEY = (12.9, 3.0)                        # N02 key tabs at ±X into the N03 flange (r0, width)
T01_PAN_BOSS = (27.0, PB["z0"] - 6.0)        # T01 bosses for the pan bracket (x = ±27, underside z 126.6)
T02_SERVO_BOSS = (41.0, 20.0)                # T02 servo-frame bosses: face |x| = 41, y = ±20, z = shoulder
TRAY_TOP = T["z0"] + T["tray"]["h"]          # 47.5
J1_PCD_R = T["tray"]["j1_screw_pcd"] / 2     # 16 – 3x M3 at 90/210/330 deg (torso.py)
H_Y_DSP_BACK = -44.6                         # display back plane = H11 front (head.py: ledge -49.1 + foam 0.5 + 4)
H_FRONT_SCREWS = ((-40.0, 248.0), (40.0, 248.0))      # 2x M2 H11 -> H03 bosses
H_FRONT_HOOK_X = (32.0, 40.0)                # |x| span of the 2 H03 bottom hooks (z 173 .. 179.5)
H_BOSSES_ROOF = ((40.0, 12.0), (-40.0, 12.0))         # H01 roof bosses (underside z 253)
H_BOSSES_FLOOR = ((44.0, 12.0), (-44.0, 12.0))        # H01 floor bosses (top z 181)
EAR_CUP_X1 = 68.0                            # ear cup ceiling (head.py), H07 sits under it
A06_WEB_X = ARM["joint_cover"]["x1"] + ARM["joint_cover"]["spigot_len"] + 0.2   # 71.7 A02 hub web face (arms.py)
A06_FLANGE = (20.0, 2.0, 16.0)               # Ø20 x 2 flange, 2x M2 on PCD 16 (REVIEW_NOTES, arms.py pocket in A04)

EPS = 0.01


# ---------------------------------------------------------------------------------------------------------
# primitives
# ---------------------------------------------------------------------------------------------------------

def bx(x0, x1, y0, y1, z0, z1) -> Solid:
    x0, x1 = sorted((x0, x1))
    y0, y1 = sorted((y0, y1))
    z0, z1 = sorted((z0, z1))
    return Solid.make_box(x1 - x0, y1 - y0, z1 - z0, Plane(origin=(x0, y0, z0)))


def cz(r, z0, z1, x=0.0, y=0.0) -> Solid:
    z0, z1 = sorted((z0, z1))
    return Solid.make_cylinder(r, z1 - z0, Plane(origin=(x, y, z0)))


def cx(r, x0, x1, y=0.0, z=0.0) -> Solid:
    x0, x1 = sorted((x0, x1))
    return Solid.make_cylinder(r, x1 - x0, Plane(origin=(x0, y, z), z_dir=(1, 0, 0)))


def cy(r, y0, y1, x=0.0, z=0.0) -> Solid:
    y0, y1 = sorted((y0, y1))
    return Solid.make_cylinder(r, y1 - y0, Plane(origin=(x, y0, z), z_dir=(0, 1, 0)))


def ring_z(ri, ro, z0, z1, x=0.0, y=0.0):
    return cz(ro, z0, z1, x, y) - cz(ri, z0 - 1, z1 + 1, x, y)


def ring_x(ri, ro, x0, x1, y=0.0, z=0.0):
    lo, hi = sorted((x0, x1))
    return cx(ro, lo, hi, y, z) - cx(ri, lo - 1, hi + 1, y, z)


def union(shapes):
    shapes = [s for s in shapes if s is not None]
    out = shapes[0]
    for s in shapes[1:]:
        out = out + s
    return out


def ebb(e):
    return e.bounding_box()


def par(axis: str, tol=0.02):
    """edge selector: straight-ish edge parallel to X/Y/Z (bounding box flat in the other two axes)."""
    def f(e):
        b = ebb(e)
        s = {"x": (b.size.Y, b.size.Z), "y": (b.size.X, b.size.Z), "z": (b.size.X, b.size.Y)}[axis]
        return s[0] < tol and s[1] < tol
    return f


def at(axis: str, value: float, tol=0.02):
    """edge selector: edge lying in the plane axis = value."""
    def f(e):
        b = ebb(e)
        lo, hi = {"x": (b.min.X, b.max.X), "y": (b.min.Y, b.max.Y), "z": (b.min.Z, b.max.Z)}[axis]
        return abs(lo - value) < tol and abs(hi - value) < tol
    return f


def fil(s, r, sel=None):
    """Fillet the edges chosen by sel (all edges if None); returns the input unchanged on failure."""
    try:
        edges = [e for e in s.edges() if sel is None or sel(e)]
        if not edges:
            return s
        out = s.fillet(r, edges)
        if out.is_valid and out.volume > 0.5 * s.volume:
            return out
    except Exception:
        pass
    return s


def rbox(x0, x1, y0, y1, z0, z1, r, axis=None):
    """Box with rounded edges (all edges, or only the edges parallel to 'axis')."""
    return fil(bx(x0, x1, y0, y1, z0, z1), r, par(axis) if axis else None)


def board(x0, x1, y0, y1, z0, z1, r=1.5):
    """PCB slab, corner radius r on the edges parallel to its thin axis."""
    d = {"x": abs(x1 - x0), "y": abs(y1 - y0), "z": abs(z1 - z0)}
    thin = min(d, key=d.get)
    return rbox(x0, x1, y0, y1, z0, z1, r, thin)


def on_plane(shape, origin, z_dir, x_dir=None):
    pl = Plane(origin=origin, z_dir=z_dir, x_dir=x_dir) if x_dir else Plane(origin=origin, z_dir=z_dir)
    return pl.location * shape


def _sweep_circle(edge, r):
    t0 = edge.tangent_at(0)
    prof = Face(Wire([Edge.make_circle(r, Plane(origin=edge.position_at(0), z_dir=t0))]))
    s = Solid.sweep(prof, Wire([edge]))
    if not s.is_valid or s.volume < 0.85 * math.pi * r * r * edge.length:
        raise ValueError("bad sweep")
    return s


def tube_path(points, r, tangents=None):
    """Circular pipe swept along a smooth spline through points (long / helical paths are swept in pieces –
    MakePipeShell fails on > ~1 turn – and fused at the coincident joint circles)."""
    pts = [Vector(*p) for p in points]
    if tangents:
        edge = Edge.make_spline(pts, tangents=[Vector(*t) for t in tangents])
    else:
        edge = Edge.make_spline(pts)
    for k in (1, 2, 3, 4, 6, 8):
        try:
            if k == 1:
                return _sweep_circle(edge, r)
            return Compound([_sweep_circle(edge.trim(i / k, (i + 1) / k), r) for i in range(k)])
        except Exception:
            continue
    raise RuntimeError("tube_path: sweep failed")


def ribbon_path(points, w, t, wdir):
    """Flat ribbon (width w along wdir, thickness t) swept along a spline in a plane normal to wdir."""
    pts = [Vector(*p) for p in points]
    edge = Edge.make_spline(pts)
    t0 = edge.tangent_at(0)
    wv = Vector(*wdir).normalized()
    nv = t0.cross(wv).normalized()
    c = pts[0]
    corners = [c + wv * (w / 2) + nv * (t / 2), c - wv * (w / 2) + nv * (t / 2),
               c - wv * (w / 2) - nv * (t / 2), c + wv * (w / 2) - nv * (t / 2)]
    prof = Face(Wire.make_polygon(corners, close=True))
    return Solid.sweep(prof, Wire([edge]), mode=wv)


def check(name, s, vmin=0.0, multi=False):
    ok = s.is_valid
    v = s.volume
    n = len(s.solids())
    if not ok or v <= vmin or (n > 1 and not multi):
        print(f"  !! {name}: valid={ok} vol={v:.1f} solids={n}")
    return s


def bearing_local(ri, ro, w):
    """Deep-groove ball bearing along local +Z (z 0..w): rings + recessed seals + edge breaks."""
    b = cz(ro, 0, w) - cz(ri, -1, w + 1)
    k = 0.28 * (ro - ri)
    seal = ring_z(ri + k, ro - k, -1, 0.25) + ring_z(ri + k, ro - k, w - 0.25, w + 1)
    b = b - seal
    return fil(b, min(0.3, 0.12 * (ro - ri)), lambda e: abs(ebb(e).min.Z) < 0.01 or abs(ebb(e).max.Z - w) < 0.01)


def gt2_profile(teeth, z0, h, x=0.0, y=0.0):
    """GT2 pulley tooth zone (2 mm pitch) as a prism: OD = PD - 0.508, 0.75 deep round-bottom grooves."""
    pd = teeth * 2.0 / math.pi
    ro = pd / 2 - 0.254
    rr = ro - 0.75
    pts = []
    g = 1.25 / ro                      # groove angular width at OD
    for i in range(teeth):
        a0 = 2 * math.pi * i / teeth
        for (da, r) in ((0.0, ro), (0.5 * g - 0.18 * g, ro), (0.5 * g, ro - 0.35), (0.62 * g, rr),
                        (0.75 * g, rr + 0.05), (0.88 * g, rr), (g, ro - 0.35), (g + 0.18 * g, ro)):
            a = a0 + da
            pts.append(Vector(x + r * math.cos(a), y + r * math.sin(a), z0))
    w = Wire.make_polygon(pts, close=True)
    return Solid.extrude(Face(w), Vector(0, 0, h)), ro


# ---------------------------------------------------------------------------------------------------------
# Feetech SCS0009 serial-bus micro servo (simplified but recognisable)
#   local frame: output axis +Z, origin = shaft axis on the case top face; case along +X (shaft 5.9 from
#   the -X end); ears (optional) 4.6 below the top face.
# ---------------------------------------------------------------------------------------------------------
SV_L, SV_W, SV_H = 23.2, 12.1, 25.25
SV_SHAFT = 5.9
SV_X0, SV_X1 = -SV_SHAFT, SV_L - SV_SHAFT
SV_EAR_SPAN, SV_EAR_T, SV_EAR_DROP, SV_EAR_PITCH = 32.3, 2.5, 4.6, 27.8
SV_BOSS_D, SV_BOSS_H = 7.0, 0.5
SV_SPL_D, SV_SPL_L = 4.8, 3.0


def servo_local(ears=True):
    hw = SV_W / 2
    c = bx(SV_X0, SV_X1, -hw, hw, -SV_H, 0)
    c = fil(c, 0.6, par("z"))
    c = fil(c, 0.8, at("z", -SV_H))
    c = fil(c, 0.3, at("z", 0.0))
    # case split lines + label recesses
    for zg in (-3.2, -SV_H + 4.5):
        band = bx(SV_X0 - 1, SV_X1 + 1, -hw - 1, hw + 1, zg - 0.2, zg + 0.2) - \
            bx(SV_X0 + 0.25, SV_X1 - 0.25, -hw + 0.25, hw - 0.25, zg - 1, zg + 1)
        c = c - band
    for sy in (-1, 1):
        c = c - bx(SV_X0 + 3.0, SV_X1 - 3.0, sy * (hw - 0.15), sy * (hw + 1), -SV_H + 7.0, -SV_EAR_DROP - SV_EAR_T - 1.5)
    if ears:
        xc = (SV_X0 + SV_X1) / 2
        e = bx(xc - SV_EAR_SPAN / 2, xc + SV_EAR_SPAN / 2, -hw + 0.4, hw - 0.4,
               -SV_EAR_DROP - SV_EAR_T, -SV_EAR_DROP)
        e = fil(e, 1.2, par("z"))
        for sx in (-1, 1):
            e = e - cz(1.1, -20, 5, x=xc + sx * SV_EAR_PITCH / 2)
            e = e - bx(xc + sx * SV_EAR_PITCH / 2, xc + sx * (SV_EAR_SPAN / 2 + 1), -0.55, 0.55, -20, 5)
        c = c + e
    # output boss + 25T spline (screw hole in the spline)
    c = c + cz(SV_BOSS_D / 2, -0.1, SV_BOSS_H)
    spl = cz(SV_SPL_D / 2, SV_BOSS_H - 0.05, SV_BOSS_H + SV_SPL_L)
    spl = fil(spl, 0.3, at("z", SV_BOSS_H + SV_SPL_L))
    spl = spl - cz(0.9, SV_BOSS_H + SV_SPL_L - 2.5, SV_BOSS_H + SV_SPL_L + 1)
    c = c + spl
    # cable strain relief on the shaft-side end face, low
    c = c + rbox(SV_X0 - 2.0, SV_X0 + 0.3, -1.7, 1.7, -SV_H + 1.2, -SV_H + 5.2, 0.5, "y")
    return c


def servo_at(origin, out_dir, body_dir, ears=True):
    """Place the servo: shaft/top-face point, output direction, direction the case extends (local +X)."""
    return on_plane(servo_local(ears), origin, out_dir, body_dir)


# =========================================================================================================
# HEAD (J3)
# =========================================================================================================
DSP = H["display"]
CAM = H["camera"]
EAR = H["ear"]
D_W, D_H, D_T = DSP["outline"]
D_Y0, D_Y1 = H_Y_DSP_BACK - D_T, H_Y_DSP_BACK            # -48.6 .. -44.6
D_ZC = DSP["zc"]
PL_T = 2.0                                                # H11 front plate thickness
PL_Y0, PL_Y1 = H_Y_DSP_BACK, H_Y_DSP_BACK + PL_T          # -44.6 .. -42.6
PL_X, PL_Z0, PL_Z1 = 54.0, 180.0, 256.0                   # plate half width, bottom (above the H03 hooks), top
CHEEK_X0, CHEEK_X1 = X_HUB_END, X_HUB_END + 2.5           # 30.4 .. 32.9 (REVIEW_NOTES H11)
BRD_Y0 = PL_Y1 + 3.6                                      # H13 front face (3.6 standoffs: FPC connector)
BRD_T = 1.6
BRD_X, BRD_Z0, BRD_Z1 = 29.0, 181.0, 226.0
BRD_HOLES = ((-25.0, 185.0), (25.0, 185.0), (-25.0, 222.0), (25.0, 222.0))
CAM_Y_GLASS = -52.0 + H["glass"]["t"]                     # glass back face -50.9
FOAM_T = 0.5


def display_e2():
    x0, x1 = -D_W / 2, D_W / 2
    z0, z1 = D_ZC - D_H / 2, D_ZC + D_H / 2
    d = bx(x0, x1, D_Y0, D_Y1, z0, z1)
    d = fil(d, 3.0, lambda e: par("y")(e) and ebb(e).max.Z < z0 + 0.1)       # lower corners R3 (H03 skirt R27.5)
    d = fil(d, 0.8, lambda e: par("y")(e) and ebb(e).min.Z > z1 - 0.1)
    aw, ah = DSP["active"]
    # cover glass step (front 0.7 mm smaller by 0.6) and active-area recess 0.1
    d = d - (bx(x0 - 1, x1 + 1, D_Y0 - 1, D_Y0 + 0.7, z0 - 1, z1 + 1)
             - rbox(x0 + 0.6, x1 - 0.6, D_Y0 - 2, D_Y0 + 1, z0 + 0.6, z1 - 0.6, 0.6, "y"))
    d = d - bx(-aw / 2, aw / 2, D_Y0 - 1, D_Y0 + 0.1, D_ZC - ah / 2, D_ZC + ah / 2)
    # metal back frame step + 4 mounting tabs (pressed by the H11 plate)
    d = d - (bx(x0 - 1, x1 + 1, D_Y1 - 0.8, D_Y1 + 1, z0 - 1, z1 + 1)
             - rbox(x0 + 1.2, x1 - 1.2, D_Y1 - 2, D_Y1 + 2, z0 + 1.2, z1 - 1.2, 0.8, "y"))
    # FPC tail (21 wide, 0.25) folded under the H11 plate to the H13 connector
    fw, ft = 10.5, 0.25
    zb = z0 + 1.6
    f = bx(-fw, fw, D_Y1 - ft - 0.05, D_Y1 - 0.05, z0 - 1.6, zb)                 # down along the back
    f = f + bx(-fw, fw, D_Y1 - ft - 0.05, BRD_Y0 - 2.4, z0 - 1.6 - ft, z0 - 1.6)  # under the plate
    f = f + bx(-fw, fw, BRD_Y0 - 2.4 - ft, BRD_Y0 - 2.4, z0 - 1.6 - ft, BRD_Z0 + 3.0)  # up to the connector
    return check("E2", d + f)


def camera_e3():
    zc = CAM["z"]
    mw, _, mt = CAM["module"]
    yf = CAM_Y_GLASS + FOAM_T                     # module front -50.4
    m = rbox(-mw / 2, mw / 2, yf + mt - 1.0, yf + mt, zc - mw / 2, zc + mw / 2, 0.4, "y")      # PCB
    m = m + rbox(-4.0, 4.0, yf + 0.8, yf + mt - 1.0, zc - 4.0, zc + 4.0, 0.6, "y")           # lens holder
    m = m + cy(3.0, yf, yf + 0.85, 0, zc)                                                     # lens barrel
    m = m - cy(1.3, yf - 1, yf + 0.3, 0, zc)
    m = m + (cy(4.0, CAM_Y_GLASS, yf, 0, zc) - cy(1.8, CAM_Y_GLASS - 1, yf + 1, 0, zc))      # foam ring OD8/ID3.6
    # USB cable: out of the back, through the H11 plate slot, over the H13 top edge to its connector
    yb = BRD_Y0 + BRD_T                           # H13 back face
    pts = [(0, yf + mt - 0.2, zc), (0, PL_Y1 + 1.1, zc - 0.6), (0, PL_Y1 + 1.6, zc - 5.0),
           (0, PL_Y1 + 1.6, BRD_Z1 + 5.0), (0, PL_Y1 + 2.3, BRD_Z1 + 2.9), (0, BRD_Y0 + BRD_T / 2, BRD_Z1 + 2.1),
           (0, yb + 2.1, BRD_Z1 + 2.9), (0, yb + 2.0, BRD_Z1 + 0.5), (0, yb + 1.8, BRD_Z1 - 1.7)]
    cab = tube_path(pts, 0.9)
    return check("E3", m + cab)


def holder_h12():
    """Camera holder: U-frame round the module + back pad with cable hole + 2 screw tabs on the H11 plate."""
    zc = CAM["z"]
    mw = CAM["module"][0]
    yb = CAM_Y_GLASS + FOAM_T + CAM["module"][2]   # module back -45.4
    yf = -49.0                                     # stays behind the H03 ledge (y -49.1)
    o, w = mw / 2 + 0.1, 1.0
    zt = 255.55                                    # under the H03 ledge (notch top 255.65)
    fr = bx(-o - w, o + w, yf, yb, zc - mw / 2, zt) - bx(-o, o, yf - 1, yb + 1, zc - mw / 2 - 1, zc + mw / 2 + 0.1)
    pad = bx(-o - w, o + w, yb, PL_Y0, zc - mw / 2, zt)
    tabs = bx(-o - w - 4.5, o + w + 4.5, yb, PL_Y0, zc - 2.0, zc + 2.0)
    h = fr + pad + tabs
    h = h - cy(1.4, yb - 1, PL_Y0 + 1, 0, zc)                                  # cable hole
    for sx in (-1, 1):
        h = h - cy(0.8, yb - 1, PL_Y0 + 1, sx * (o + w + 2.4), zc)
    return check("H12", fil(h, 0.3, par("y")))


def chassis_h11():
    """Inner head frame: front plate behind the display, 2 cheeks on the N07 hubs, top deck, 4 tabs to H01."""
    # front plate
    p = bx(-PL_X, PL_X, PL_Y0, PL_Y1, PL_Z0, PL_Z1)
    p = fil(p, 18.0, lambda e: par("y")(e) and ebb(e).min.Z > 200)
    p = fil(p, 9.0, lambda e: par("y")(e) and ebb(e).max.Z < 200)
    # standoffs for H13, catch lugs for the H03 hooks, screw bosses for H03 (2x M2 from behind)
    for (x, z) in BRD_HOLES:
        p = p + cy(2.4, PL_Y1 - 0.1, BRD_Y0, x, z)
    for sx in (-1, 1):
        x0, x1 = sx * H_FRONT_HOOK_X[0], sx * H_FRONT_HOOK_X[1]
        p = p + bx(x0, x1, PL_Y1 - 0.1, PL_Y1 + 1.6, PL_Z0, PL_Z0 + 2.5)
    for (x, z) in H_FRONT_SCREWS:
        p = p + cy(3.0, PL_Y1 - 0.1, PL_Y1 + 2.0, x, z)
    # back ribs (stiffness) on the plate
    for x in (-44.0, 44.0):
        p = p + bx(x - 0.8, x + 0.8, PL_Y1 - 0.1, PL_Y1 + 2.5, PL_Z0 + 4, PL_Z1 - 14)
    p = p + bx(-PL_X + 10, -2.5, PL_Y1 - 0.1, PL_Y1 + 2.5, 238.0, 239.6)          # gap for the camera cable
    p = p + bx(2.5, PL_X - 10, PL_Y1 - 0.1, PL_Y1 + 2.5, 238.0, 239.6)

    # cheeks |x| 30.4..32.9 (YZ profile), hub interface on the tilt axis
    prof = [(-42.6, 238.0), (-42.6, 180.0), (-29.0, 180.0), (-22.0, 173.0), (17.0, 173.0), (17.0, 252.5),
            (7.5, 252.5), (7.5, 238.0)]

    def cheek(sx):
        x0 = sx * CHEEK_X0
        pts = [Vector(x0, y, z) for (y, z) in prof]
        f = Face(Wire.make_polygon(pts, close=True))
        c = Solid.extrude(f, Vector(sx * (CHEEK_X1 - CHEEK_X0), 0, 0))
        c = fil(c, 3.0, par("x"))
        # lightening windows
        c = c - fil(bx(x0 - sx, x0 + sx * 4, -24, -6, 214, 232), 3.0, par("x"))
        c = c - fil(bx(x0 - sx, x0 + sx * 4, -2, 12, 214, 232), 3.0, par("x"))
        if sx > 0:      # passive (left) side: Ø13 cable tunnel + window toward H13 + 2 key lugs into N07-L
            c = c - cx(6.6, x0 - 1, x0 + 4, AX_Y, AX_Z)
            c = c - fil(bx(x0 - 1, x0 + 4, -34.5, -28.5, 210.6, 217.4), 2.0, par("x"))
            for sy in (-1, 1):
                c = c + bx(x0 - 1.4, x0 + 0.05, sy * 6.1, sy * 9.0, AX_Z - 1.4, AX_Z + 1.4)
        else:           # servo (right) side: M2 (PCD 11) + 2 pins Ø2 into N07-R (neck.py puts the 3rd M2 pilot
            #             at 210° on top of a pin hole -> that position takes the pin, 2x M2 at 90° / 330°)
            for k in (0, 2):
                a = math.radians(90 + 120 * k)
                c = c - cx(1.15, x0 + 1, x0 - 4, AX_Y + 5.5 * math.sin(a), AX_Z + 5.5 * math.cos(a))
                c = c - cx(2.1, x0 - (CHEEK_X1 - CHEEK_X0) + 1.0, x0 - 4,
                           AX_Y + 5.5 * math.sin(a), AX_Z + 5.5 * math.cos(a))
            for k in range(2):
                a = math.radians(30 + 180 * k)
                c = c + cx(0.95, x0 + sx * 0.3, x0 - sx * 2.6, AX_Y + 5.5 * math.sin(a), AX_Z + 5.5 * math.cos(a))
        # tabs to the H01 roof boss (z 250..252.5) and floor boss (z 181.2..183.7)
        rx, ry = (40.0, 12.0)
        fx, fy = (44.0, 12.0)
        t1 = bx(x0, sx * rx, ry - 4.5, ry + 4.5, 250.0, 252.5) + cz(4.5, 250.0, 252.5, sx * rx, ry)
        t1 = t1 - cz(1.35, 249, 254, sx * rx, ry)
        t2 = bx(x0, sx * fx, fy - 4.5, fy + 4.5, 181.2, 183.7) + cz(4.5, 181.2, 183.7, sx * fx, fy)
        t2 = t2 - cz(1.35, 180, 185, sx * fx, fy)
        return c + t1 + t2

    deck = bx(-CHEEK_X1, CHEEK_X1, -29.5, 17.0, 208.0, 210.5)
    deck = deck - fil(bx(-22, 22, -22, 10, 207, 212), 5.0, par("z"))
    h = p + cheek(-1) + cheek(1) + deck
    # holes: H03 screws, H13 standoff pilots, camera cable slot
    for (x, z) in H_FRONT_SCREWS:
        h = h - cy(1.2, PL_Y0 - 1, PL_Y1 + 3, x, z)
    for (x, z) in BRD_HOLES:
        h = h - cy(0.9, PL_Y1 - 1, BRD_Y0 + 1, x, z)
    h = h - fil(bx(-2.5, 2.5, PL_Y0 - 1, PL_Y1 + 1, CAM["z"] - 1.5, CAM["z"] + 1.5), 1.0, par("y"))
    return check("H11", h)


def board_h13():
    y0, y1 = BRD_Y0, BRD_Y0 + BRD_T
    b = board(-BRD_X, BRD_X, y0, y1, BRD_Z0, BRD_Z1, 2.0)
    for (x, z) in BRD_HOLES:
        b = b - cy(1.1, y0 - 1, y1 + 1, x, z)
    comp = []
    # ESP32-S3-WROOM-1 (18 x 25.5 x 3.1): module PCB + RF can
    comp.append(bx(-17.0, 1.0, y1, y1 + 0.8, 198.0, 223.5))
    comp.append(rbox(-16.1, 0.1, y1 + 0.8, y1 + 3.1, 198.6, 216.2, 0.3, "y"))
    comp.append(bx(4.0, 10.0, y1, y1 + 1.0, 214.0, 220.0))                    # PSRAM / flash
    comp.append(bx(4.0, 9.0, y1, y1 + 1.2, 204.0, 209.0))                     # PMIC
    comp.append(rbox(-8.0, -2.0, y1, y1 + 3.0, 186.0, 192.0, 0.5, "y"))      # buck inductor
    comp.append(bx(16.0, 28.0, y1, y1 + 4.0, 211.0, 217.0))                   # W1 connector (JST-GH 8)
    comp.append(bx(-3.0, 3.0, y1, y1 + 3.0, 219.0, 223.5))                    # camera USB connector
    for sx in (-1, 1):
        comp.append(bx(sx * 22.0, sx * 27.0, y1, y1 + 2.9, 194.0, 200.0))     # ear PCB connectors (JST-SH)
    comp.append(bx(-13.0, 13.0, y0 - 2.0, y0, 182.0, 186.0))                  # display FPC connector (front)
    for (x, z) in ((12.0, 190.0), (16.0, 190.0), (20.0, 190.0), (-20.0, 200.0), (-20.0, 204.0)):
        comp.append(bx(x - 1.0, x + 1.0, y1, y1 + 0.9, z - 0.6, z + 0.6))     # passives
    return check("H13", union([b] + comp))


def ear_pcb_h07(sx):
    """Ear PCB: Ø29 disc (REVIEW: ring OD29 – centre kept for the mic), 12x WS2812B-2020, MEMS mic + gasket."""
    ey, ez = EAR["y"], EAR["z"]
    g_t = 0.3
    xm1 = EAR_CUP_X1                          # gasket touches the cup ceiling
    xm0 = xm1 - g_t - 0.98                    # mic body
    xp1 = xm0                                 # PCB outer face
    xp0 = xp1 - 1.0
    d = cx(14.5, xp0, xp1, ey, ez)
    for k in range(12):
        a = math.radians(15 + 30 * k)
        yy, zz = ey + 12.6 * math.cos(a), ez + 12.6 * math.sin(a)
        led = Pos(0, yy, zz) * Rot(a * 180 / math.pi, 0, 0) * bx(xp1 - 0.01, xp1 + 0.84, -1.0, 1.0, -1.0, 1.0)
        d = d + led
    d = d + bx(xm0 - 0.01, xm0 + 0.98, ey - 1.25, ey + 1.25, ez - 1.68, ez + 1.68)          # mic (top port)
    d = d + (cx(2.0, xm1 - g_t, xm1 - 0.005, ey, ez) - cx(0.75, xm1 - 1, xm1 + 1, ey, ez))  # gasket Ø4
    d = d + bx(xp0 - 2.9, xp0 + 0.01, ey - 9.5, ey - 5.5, ez - 3.0, ez + 3.0)                # JST-SH (inner face)
    d = d + bx(xp0 - 1.2, xp0 + 0.01, ey + 3.0, ey + 6.0, ez - 2.0, ez + 2.0)                # touch IC
    if sx < 0:
        d = mirror(d, Plane.YZ)
    return check("H07", d)


def head_cable_w1h():
    """W1 head segment (J3): H13 connector -> L cheek window -> outside the cheek -> N07-L hub tunnel."""
    yc = BRD_Y0 + BRD_T + 4.0 + 0.6                     # 0.6 off the JST-GH face
    pts = [(22.0, yc, 214.0), (22.4, yc + 1.0, 214.0), (25.0, -30.7, 214.0), (31.6, -31.0, 214.0),
           (36.5, -29.3, 212.5),
           (38.0, -20.0, 202.0), (37.8, -9.0, 189.0), (36.2, -2.6, 182.6), (33.0, AX_Y, AX_Z),
           (28.0, AX_Y, AX_Z), (PIN_X_END + 0.6, AX_Y, AX_Z)]
    return check("W1-H", tube_path(pts, 2.0), multi=True)


# =========================================================================================================
# NECK (tilt barrel J2/J3, pan stage J2, pan drive J1)
# =========================================================================================================
TILT_TOP_X = -L_BAR / 2                      # servo top face flush with the -X barrel end
B6703 = (8.5, 11.5, 4.0)                     # 17 x 23 x 4
B6703_X0 = 13.5
PLUG_X0, PLUG_X1, PLUG_R = 12.5, L_BAR / 2, 15.95
SPRING_X0, SPRING_X1 = 9.05, 12.05           # strip 3.0 x 0.4
PAN_TOP = 123.3                              # pan servo top face (moved down: cable window + clutch under 61805)
N03_Z0 = PAN_TOP + SV_BOSS_H + 0.8           # 124.6 hub bottom
N03_WIN = (127.9, 132.4)                     # cable window (toward -Y) under the bearing (z0 132.6)
N03_CH = (2.5, 9.5, 6.0)                     # cable channel x0, x1, half width (12 x 7 off-axis)
BRK_Z0, BRK_Z1 = T01_PAN_BOSS[1] - 3.0, T01_PAN_BOSS[1]   # pan bracket plate 123.6 .. 126.6
CBL_X = 4.8                                  # x of the bundle in the N06 slot (x ±7) / N03 channel (x 2.5..9.5)


def tilt_servo_e6t():
    s = servo_at((TILT_TOP_X, AX_Y, AX_Z), (-1, 0, 0), (0, 0, 1), ears=False)
    return check("E6-T", s)


def spline_insert_m6():
    x0, x1 = -X_CAP0 - INSERT_DEPTH, -X_CAP0
    s = cx(INSERT_D / 2 - 0.05, x0, x1, AX_Y, AX_Z)
    s = fil(s, 0.4, at("x", x1))
    s = s - cx(SV_SPL_D / 2 + 0.1, x1 - 3.2, x1 + 1, AX_Y, AX_Z)
    s = s - cx(1.1, x0 - 1, x1 + 1, AX_Y, AX_Z)
    for k in range(3):                                   # 3 knurl / anti-rotation flats
        a = math.radians(90 + 120 * k)
        s = s - Pos(0, AX_Y + 9.95 * math.cos(a), AX_Z + 9.95 * math.sin(a)) * Rot(math.degrees(a), 0, 0) * \
            bx(x0 - 1, x1 + 1, -0.6, 0.6, -2.0, 2.0)
    return check("M6", s)


def plug_n05():
    p = cx(PLUG_R, PLUG_X0, PLUG_X1, AX_Y, AX_Z)
    p = fil(p, 0.5, at("x", PLUG_X0))
    p = p - cx(B6703[1], PLUG_X0 - 1, B6703_X0 + B6703[2], AX_Y, AX_Z)      # bearing seat (from inside)
    p = p - cx(10.0, PLUG_X0 - 1, PLUG_X1 + 1, AX_Y, AX_Z)                   # pin / inner ring clearance
    for k in range(3):                                                      # keys into the N06 notches
        a = math.radians(90 + 120 * k)
        key = bx(16.6, PLUG_X1, -1.3, 1.3, PLUG_R - 0.5, 16.6)
        p = p + Pos(0, AX_Y, AX_Z) * Rot(math.degrees(a) - 90, 0, 0) * key
    for k in range(3):                                                      # 3x M2 (to the barrel lip)
        a = math.radians(30 + 120 * k)
        p = p - cx(1.1, PLUG_X0 - 1, PLUG_X1 + 1, AX_Y + 13.6 * math.cos(a), AX_Z + 13.6 * math.sin(a))
        p = p - cx(2.0, PLUG_X1 - 1.2, PLUG_X1 + 1, AX_Y + 13.6 * math.cos(a), AX_Z + 13.6 * math.sin(a))
    # spring anchor peg on the inner face (outer spring end)
    p = p + cx(1.0, SPRING_X0 + 0.2, PLUG_X0 + 0.5, AX_Y, AX_Z + 15.9)
    return check("N05", p)


def bearing_6703_m3():
    b = bearing_local(*B6703)
    return check("M3", on_plane(b, (B6703_X0, AX_Y, AX_Z), (1, 0, 0)))


def spring_m5():
    """Flat spiral gravity-compensation spring (strip 3.0 x 0.4, ~1.25 turns), inner end in the pin slot."""
    n = 90
    turns = 1.25
    r0, r1 = PIN_OD / 2 + 0.55, 14.6
    pts_o, pts_i = [], []
    for i in range(n + 1):
        u = i / n
        a = 2 * math.pi * turns * u
        r = r0 + (r1 - r0) * u
        for lst, rr in ((pts_o, r + 0.2), (pts_i, r - 0.2)):
            lst.append(Vector(SPRING_X0, AX_Y + rr * math.cos(a), AX_Z + rr * math.sin(a)))
    eo = Edge.make_spline(pts_o)
    ei = Edge.make_spline(pts_i[::-1])
    w = Wire([eo, Edge.make_line(pts_o[-1], pts_i[-1]), ei, Edge.make_line(pts_i[0], pts_o[0])])
    try:
        f = Face(w)
    except Exception:
        w = Wire.make_polygon(pts_o + pts_i[::-1], close=True)
        f = Face(w)
    s = Solid.extrude(f, Vector(SPRING_X1 - SPRING_X0, 0, 0))
    # inner hook into the pin slot (radial leg at +Y)
    s = s + bx(SPRING_X0, SPRING_X1, AX_Y + 7.1, AX_Y + r0 + 0.2, AX_Z - 0.2, AX_Z + 0.2)
    return check("M5", s)


def hub_n03():
    zf0, zf1 = N03_TOP - N03_FLANGE[1], N03_TOP
    r = PB["id"] / 2
    h = cz(r, N03_Z0, zf0 + 0.1)
    h = h + cz(13.8, PB["z0"] + PB["w"], PB["z0"] + PB["w"] + 1.4)          # shoulder on the inner ring
    h = h + cz(N03_FLANGE[0], zf0, zf1)
    h = fil(h, 0.5, lambda e: at("z", zf1)(e) and ebb(e).size.X > 2 * N03_FLANGE[0] - 0.1)
    h = fil(h, 0.4, lambda e: at("z", N03_Z0)(e))
    for sx in (-1, 1):                                                       # N02 key notches
        h = h - bx(sx * (N02_KEY[0] - 0.3), sx * (N03_FLANGE[0] + 1), -N02_KEY[1] / 2 - 0.2,
                   N02_KEY[1] / 2 + 0.2, zf0 - 0.1, zf1 + 0.1)
    for sy in (-1, 1):                                                       # M2.5 tapped holes (N06 spigot)
        h = h - cz(1.05, zf1 - 7.0, zf1 + 1, 0, sy * N03_SCREW_Y)
    x0, x1, hw = N03_CH
    ch = fil(bx(x0, x1, -hw, hw, N03_WIN[0], zf1 + 1), 1.0, par("z"))
    h = h - ch                                                               # off-axis cable channel 7 x 12
    h = h - fil(bx(x0, x1, -20.0, hw - 2.0, N03_WIN[0], N03_WIN[1]), 1.0, par("y"))   # window toward -Y
    h = h - cz(9.75, N03_Z0 - 1, N03_Z0 + 3.0)                               # clutch pocket
    h = h - cz(2.6, N03_Z0 - 1, N03_WIN[0] - 0.5)                            # spline clearance
    return check("N03", h)


def clutch_n04():
    z0 = N03_Z0 + 0.1
    d = cz(9.5, z0, z0 + 1.9) - cz(SV_SPL_D / 2 + 0.05, z0 - 1, z0 + 3)       # splined friction disc (25T bore)
    for k in range(6):                                                         # friction pads
        a = math.radians(60 * k + 30)
        d = d - Pos(6.5 * math.cos(a), 6.5 * math.sin(a), z0 + 1.6) * Rot(0, 0, 60 * k + 30) * bx(-1.5, 1.5, -1.0, 1.0, 0, 1)
    # wave washer (3 waves) approximated by a ring with 6 radial relief slots
    wz0 = z0 + 1.9
    w = ring_z(5.6, 9.5, wz0, wz0 + 0.9)
    for k in range(6):
        a = 60 * k
        w = w - Rot(0, 0, a) * bx(5.0, 10.0, -0.3, 0.3, wz0 - 1, wz0 + 2)
    return check("N04", d + w)


def bearing_61805_m2():
    b = bearing_local(PB["id"] / 2, PB["od"] / 2, PB["w"])
    return check("M2", Pos(PX, PY, PB["z0"]) * b)


def pan_servo_e6p():
    return check("E6-P", servo_at((PX, PY, PAN_TOP), (0, 0, 1), (0, -1, 0), ears=True))


def neck_cable_w1n():
    """W1 neck segment (J2): flat 7-way jumper from the pin end down beside the servo end (x 7.4..8.6), then
    the round Ø4 bundle through the N06 slot and the N03 channel, out of the N03 window toward -Y."""
    rb = ribbon_path([(PIN_X_END + 0.8, AX_Y, AX_Z), (8.6, AX_Y, AX_Z - 0.2), (8.0, AX_Y, AX_Z - 1.6),
                      (8.0, AX_Y, AX_Z - 6.0), (8.0, AX_Y, 168.5), (6.8, AX_Y, 165.5), (CBL_X, AX_Y, 163.0)],
                     7.0, 1.2, (0, 1, 0))
    zc = (N03_WIN[0] + N03_WIN[1]) / 2
    rd = tube_path([(CBL_X, AX_Y, 164.0), (CBL_X, AX_Y, 150.0), (CBL_X, AX_Y, 135.0),
                    (CBL_X, -1.2, zc + 1.0), (CBL_X, -4.0, zc), (CBL_X, -8.0, zc),
                    (CBL_X, -14.5, zc - 0.6)], 2.0)
    return check("W1-N", rb + rd)


COIL = dict(hx=10.5, y0=-22.5, y1=9.0, rc=6.0)  # coil centerline round the pan servo body (x ±6.05, y -17.3..5.9)


def coil_pt(s, z):
    """Point on the rounded-rect coil centerline round the pan servo (s = arc length from the front middle, CCW)."""
    hx, y0, y1, rc = COIL["hx"], COIL["y0"], COIL["y1"], COIL["rc"]
    yc, hy = (y0 + y1) / 2, (y1 - y0) / 2
    sx, sy = hx - rc, hy - rc
    segs = [("L", (0, -hy), (1, 0), sx), ("A", (sx, -sy), -90, rc), ("L", (hx, -sy), (0, 1), 2 * sy),
            ("A", (sx, sy), 0, rc), ("L", (sx, hy), (-1, 0), 2 * sx), ("A", (-sx, sy), 90, rc),
            ("L", (-hx, sy), (0, -1), 2 * sy), ("A", (-sx, -sy), 180, rc), ("L", (-sx, -hy), (1, 0), sx)]
    per = sum(sg[3] * (math.pi / 2 if sg[0] == "A" else 1) for sg in segs)
    s = s % per
    for sg in segs:
        ln = sg[3] * (math.pi / 2 if sg[0] == "A" else 1)
        if s <= ln + 1e-9:
            if sg[0] == "L":
                p = (sg[1][0] + sg[2][0] * s, sg[1][1] + sg[2][1] * s)
            else:
                a = math.radians(sg[2]) + s / sg[3]
                p = (sg[1][0] + sg[3] * math.cos(a), sg[1][1] + sg[3] * math.sin(a))
            return (p[0], yc + p[1], z)
        s -= ln
    return (0, y0, z)


def coil_perimeter():
    hx, y0, y1, rc = COIL["hx"], COIL["y0"], COIL["y1"], COIL["rc"]
    return 2 * (2 * hx + (y1 - y0)) - (8 - 2 * math.pi) * rc


COIL_Z = (113.0, 106.0)                      # top stays 1.2 under the pan-servo ears (z 116.2)
COIL_TURNS = 1.5
E10_Z0 = 61.5
E10_T = 1.6
W1_TAIL_XY = (-10.0, -13.0)                  # tail down the coil's -X side to the E10 connector


def torso_cable_w1t():
    """W1 torso segment (J1): from the N03 window, down in front of the pan bracket, 1.5-turn coil round the
    pan servo (service loop for ±90° pan), then down to the E10 connector."""
    per = coil_perimeter()
    zc = (N03_WIN[0] + N03_WIN[1]) / 2
    pts = [(CBL_X, -14.3, zc - 0.65), (CBL_X, -19.5, zc - 2.2), (3.5, -26.8, 125.5), (0.5, -27.5, 121.0),
           (-3.0, -26.0, 116.5)]                                      # drops under the T01 boss ring (z 131.6)
    n = 44
    hy = (COIL["y1"] - COIL["y0"]) / 2
    s_end = COIL_TURNS * per + (COIL["hx"] - COIL["rc"]) + COIL["rc"] * math.pi / 2 + (hy - COIL["rc"])
    for i in range(n + 1):
        s = s_end * i / n
        z = COIL_Z[0] + (COIL_Z[1] - COIL_Z[0]) * s / (COIL_TURNS * per)       # constant pitch (no overlap)
        pts.append(coil_pt(s, z))
    z_end = pts[-1][2]
    x, y = W1_TAIL_XY
    yc = (COIL["y0"] + COIL["y1"]) / 2
    pts += [(x, yc - 3.5, z_end - 2.0), (x, yc - 6.0, z_end - 6.0), (x, y, z_end - 12.0),
            (x, y, 80.0), (x, y, E10_Z0 + E10_T + 6.0)]
    return check("W1-T", tube_path(pts, 2.0), multi=True)


# =========================================================================================================
# TORSO (J1) + arm drivers (J4/J5)
# =========================================================================================================
SV_ARM_TOP = 42.8                            # |x| of the arm-servo top face (clear of the T02 bearing tube |x|>=43)
TW_X0, TW_X1 = SV_ARM_TOP - SV_EAR_DROP - SV_EAR_T - 2.5, SV_ARM_TOP - SV_EAR_DROP - SV_EAR_T   # 33.2 .. 35.7
TW_Z0, TW_Z1 = 56.0, BRK_Z1
XP_Z0, XP_Z1 = 56.0, 58.5                    # T07 cross plate (above the T02 tray bosses z 57.5 -> holes)
SLED_Y0, SLED_Y1 = 13.3, 15.3
CAR_Y0 = 16.8                                # E1 carrier front face (just in front of the T02 tray bosses y 18.5)
CAR_W, CAR_H, CAR_Z0 = 75.0, 56.0, 55.0      # CM5 carrier 75 x 56 (REVIEW_NOTES alternative to the Pi 5)
CAR_HOLES = ((-33.5, 59.0), (33.5, 59.0), (-33.5, 105.0), (33.5, 105.0))
E10_X, E10_Y0, E10_Y1 = 32.9, -34.0, 9.5          # between the T07 towers (|x| 33.2)
E10_POSTS = ((-30.0, 5.0), (30.0, 5.0), (-18.0, -27.0), (18.0, -27.0))


def arm_servo(sx):
    s = servo_at((sx * SV_ARM_TOP, SH_Y, SH_Z), (sx, 0, 0), (0, 0, -1), ears=True)
    return check("E6-R" if sx < 0 else "E6-L", s)


def frame_t07():
    parts = []
    hw = SV_W / 2 + 0.25
    z_body0, z_body1 = SH_Z - (SV_L - SV_SHAFT) - 0.3, SH_Z + SV_SHAFT + 0.3
    for sx in (-1, 1):
        x0, x1 = sx * TW_X0, sx * TW_X1
        tw = bx(x0, x1, -12.0, SLED_Y0, TW_Z0, TW_Z1)
        tw = tw + bx(x0, x1, -T02_SERVO_BOSS[1] - 3.2, T02_SERVO_BOSS[1] + 3.2, SH_Z - 4.0, TW_Z1)
        tw = fil(tw, 2.0, par("x"))
        tw = tw - fil(bx(x0 - sx, x1 + sx, -hw, hw, z_body0, z_body1), 0.8, par("x"))     # servo window
        tw = tw - fil(bx(x0 - sx, x1 + sx, -7.0, 7.0, 64.0, 90.0), 3.0, par("x"))           # lightening
        for sy in (-1, 1):
            zc = SH_Z - (SV_X0 + SV_X1) / 2 + sy * SV_EAR_PITCH / 2         # ear screw holes (ears along Z)
            tw = tw - cx(0.8, x0 - sx, x1 + sx, 0, zc)
            # standoff block to the T02 servo boss (M2 along X)
            blk = bx(x1, sx * T02_SERVO_BOSS[0], sy * T02_SERVO_BOSS[1] - 3.2, sy * T02_SERVO_BOSS[1] + 3.2,
                     SH_Z - 3.2, SH_Z + 3.2)
            blk = fil(blk, 1.0, par("x"))
            blk = blk - cx(1.1, x0 - sx, sx * (T02_SERVO_BOSS[0] + 1), sy * T02_SERVO_BOSS[1], SH_Z)
            tw = tw + blk
        # sled screw lugs (rear edge)
        for zc in (66.0, 100.0):
            tw = tw - cy(0.8, SLED_Y0 - 6, SLED_Y0 + 1, sx * (TW_X0 + TW_X1) / 2, zc)
        parts.append(tw)
    # low cross plate (E10 carrier) with clearance holes round the front T02 tray bosses
    xp = rbox(-TW_X1, TW_X1, -29.0, 9.0, XP_Z0, XP_Z1, 4.0, "z")
    for (x, y) in T["tray"]["screw_xy"]:
        if y < 0:
            xp = xp - cz(4.6, XP_Z0 - 1, XP_Z1 + 1, x, y)
    xp = xp - fil(bx(-12, 12, -18, 0, XP_Z0 - 1, XP_Z1 + 1), 4.0, par("z"))               # slip-ring wires
    for (x, y) in E10_POSTS:
        xp = xp + cz(2.5, XP_Z1 - 0.1, E10_Z0, x, y) - cz(0.9, XP_Z0, E10_Z0 + 1, x, y)
    parts.append(xp)
    # pan bracket: H plate under the T01 bosses, front ear pad, rear yoke (stays under the N03 hub)
    br = rbox(-18.0, 18.0, -24.0, 15.0, BRK_Z0, BRK_Z1, 4.0, "z")
    br = br + bx(-TW_X0 - 0.1, TW_X0 + 0.1, -7.0, 7.0, BRK_Z0, BRK_Z1)
    br = br - cz(13.5, BRK_Z0 - 1, BRK_Z1 + 1, PX, PY)
    for sx in (-1, 1):
        br = br - cz(1.1, BRK_Z0 - 1, BRK_Z1 + 1, sx * T01_PAN_BOSS[0], 0)
    ear_top = PAN_TOP - SV_EAR_DROP
    ear_y = (-(SV_X1 + (SV_EAR_SPAN - SV_L) / 2), -(SV_X1 + 0.2))          # front ear (beyond the body)
    pad = bx(-SV_W / 2 + 0.4, SV_W / 2 - 0.4, ear_y[0], ear_y[1], ear_top, BRK_Z0 + 0.1)
    yoke_y = (SV_SHAFT + 0.2, -(SV_X0 - (SV_EAR_SPAN - SV_L) / 2))        # rear ear
    yoke = bx(-16.5, 16.5, yoke_y[0], yoke_y[1], ear_top, N03_Z0 - 1.6)
    for sx in (-1, 1):
        yoke = yoke + bx(sx * 13.0, sx * 16.5, yoke_y[0], yoke_y[1], N03_Z0 - 1.7, BRK_Z0 + 0.1)
    br = br + pad + yoke
    xc = -(SV_X0 + SV_X1) / 2
    for yy in (xc - SV_EAR_PITCH / 2, xc + SV_EAR_PITCH / 2):
        br = br - cz(0.8, ear_top - 1, ear_top + 4.0, 0, yy)
    parts.append(br)
    f = union(parts)
    return check("T07", f)


def sled_t08():
    x0, x1 = -CAR_W / 2, CAR_W / 2
    zt = CAR_Z0 + CAR_H - 2.5                           # stays under the T07 boss wings (z 109)
    s = rbox(x0, x1, SLED_Y0, SLED_Y1, CAR_Z0, zt, 3.0, "y")
    s = s - fil(bx(x0 + 7, x1 - 7, SLED_Y0 - 1, SLED_Y1 + 1, CAR_Z0 + 8, zt - 8), 4.0, par("y"))
    for (x, z) in CAR_HOLES:
        s = s + cy(2.6, SLED_Y1 - 0.1, CAR_Y0, x, z) - cy(0.9, SLED_Y0 - 1, CAR_Y0 + 1, x, z)
    # side lugs onto the T07 towers (2x M2 each side)
    for sx in (-1, 1):
        lug = bx(sx * (TW_X0 - 0.5), sx * (TW_X1 + 0.4), SLED_Y0, SLED_Y1, 60.0, 106.0)
        s = s + lug
        for zc in (66.0, 100.0):
            s = s - cy(1.1, SLED_Y0 - 1, SLED_Y1 + 1, sx * (TW_X0 + TW_X1) / 2, zc)
    return check("T08", s)


def compute_e1():
    """Raspberry Pi CM5 on a 75 x 56 carrier (REVIEW_NOTES alternative; a Pi 5 with its 16 mm USB/ETH stack
    does not fit between the T02 shoulder tubes and bosses), component side toward the rear door."""
    y0, y1 = CAR_Y0, CAR_Y0 + 1.6
    b = board(-CAR_W / 2, CAR_W / 2, y0, y1, CAR_Z0, CAR_Z0 + CAR_H, 3.0)
    for (x, z) in CAR_HOLES:
        b = b - cy(1.35, y0 - 1, y1 + 1, x, z)
    comp = []
    zc = CAR_Z0 + CAR_H / 2 + 1.0
    comp.append(bx(-17.0, -3.0, y1, y1 + 1.5, zc - 18.0, zc - 14.0))        # 2x Hirose DF40 (under the CM5)
    comp.append(bx(3.0, 17.0, y1, y1 + 1.5, zc - 18.0, zc - 14.0))
    cm = board(-27.5, 27.5, y1 + 1.5, y1 + 2.7, zc - 20.0, zc + 20.0, 1.0)  # CM5 module 55 x 40
    comp.append(cm)
    comp.append(bx(-8.0, 8.0, y1 + 2.7, y1 + 3.6, zc - 6.0, zc + 8.0))       # SoC (under the cooler pad)
    comp.append(bx(-13.0, -4.0, y1, y1 + 3.2, CAR_Z0 - 0.8, CAR_Z0 + 6.5))  # USB-C (service), bottom edge
    comp.append(bx(3.0, 16.0, y1, y1 + 6.0, CAR_Z0 + 1.0, CAR_Z0 + 6.5))    # 2x5 header to E10 (off the T02 bosses)
    comp.append(bx(-35.0, -31.0, y1, y1 + 2.5, zc + 6.0, zc + 16.0))         # FPC connector (spare CSI)
    comp.append(bx(30.0, 35.5, y1, y1 + 4.0, zc + 10.0, zc + 16.0))          # USB2 from the head bundle
    comp.append(bx(-36.0, -30.0, y1, y1 + 1.2, zc - 14.0, zc - 6.0))         # USB hub IC
    return check("E1", union([b] + comp))


def cooler_e1k():
    """CM5 active cooler: Al base + vertical fins (chimney flow from the low inlet to the top exhaust) + fan."""
    y_base = CAR_Y0 + 1.6 + 3.6
    zc = CAR_Z0 + CAR_H / 2 + 1.0
    k = rbox(-27.0, 27.0, y_base, y_base + 2.0, zc - 19.5, zc + 19.5, 1.5, "y")
    for i in range(13):
        x = -24.0 + 4.0 * i
        if -14.0 < x < 14.0:
            continue
        k = k + bx(x - 0.5, x + 0.5, y_base + 1.9, y_base + 9.5, zc - 19.0, zc + 19.0)
    fan = cy(13.5, y_base + 1.9, y_base + 9.5, 0, zc) - cy(12.4, y_base + 4.0, y_base + 10, 0, zc)
    fan = fan + cy(5.5, y_base + 1.9, y_base + 9.0, 0, zc)
    for i in range(9):
        a = 40 * i
        fan = fan + Pos(0, 0, zc) * Rot(0, a, 0) * bx(5.0, 12.4, y_base + 4.0, y_base + 8.6, -0.5, 0.5)
    return check("E1-K", k + fan)


def power_board_e10():
    z0, z1 = E10_Z0, E10_Z0 + E10_T
    b = board(-E10_X, E10_X, E10_Y0, E10_Y1, z0, z1, 3.0)
    for (x, y) in E10_POSTS:
        b = b - cz(1.35, z0 - 1, z1 + 1, x, y)
    c = []
    c.append(bx(-32.5, -14.5, -30.0, -4.5, z1, z1 + 0.8))                      # ESP32-S3-WROOM-1
    c.append(rbox(-31.6, -15.4, -29.4, -11.8, z1 + 0.8, z1 + 3.1, 0.3, "z"))
    c.append(rbox(4.0, 12.0, -28.0, -20.0, z1, z1 + 4.0, 0.8, "z"))           # 5.1 V / 5 A inductor
    c.append(rbox(16.0, 22.0, -28.0, -22.0, z1, z1 + 3.0, 0.6, "z"))          # 6.0 V / 3 A inductor
    for (x, y) in ((8.0, -12.0), (16.0, -12.0), (24.0, -12.0)):
        c.append(cz(3.15, z1, z1 + 7.7, x, y))                                 # electrolytics
    c.append(bx(-4.0, 2.0, -6.0, 0.0, z1, z1 + 1.0))                           # IMU BMI270
    for (x, y, w, d) in ((-31.5, 2.0, 5.0, 6.0), (26.5, 2.0, 5.0, 6.0), (-8.0, 4.5, 6.0, 5.0),
                         (2.0, 4.5, 6.0, 5.0)):
        c.append(bx(x, x + w, y, y + d, z1, z1 + 6.0))                          # servo bus connectors (3-pin)
    x, y = W1_TAIL_XY
    c.append(bx(x - 4.0, x + 4.0, y - 3.5, y + 3.5, z1, z1 + 5.0))            # W1 connector
    c.append(bx(-13.5, -2.5, -28.5, -21.5, z1, z1 + 6.5))                      # slip-ring power (JST-VH)
    return check("E10", union([b] + c))


def led_carrier_t09():
    L = T["led"]
    y0, y1 = -38.5, -30.5
    c = rbox(-L["w"] / 2 - 2.0, L["w"] / 2 + 2.0, y0, y1, L["z"] - 5.0, L["z"] + 5.0, 1.0, "y")
    c = c - fil(bx(-L["w"] / 2, L["w"] / 2, y0 - 1, y1 + 1, L["z"] - 2.5, L["z"] + 2.5), 2.4, par("y"))
    return check("T09", c)


def led_pcb_e13t():
    L = T["led"]
    y0 = -30.5
    p = board(-L["w"] / 2 - 1.5, L["w"] / 2 + 1.5, y0, y0 + 0.8, L["z"] - 4.5, L["z"] + 4.5, 1.0)
    for x in (-12.0, -4.0, 4.0, 12.0):
        p = p + bx(x - 1.0, x + 1.0, y0 - 0.84, y0 + 0.01, L["z"] - 1.0, L["z"] + 1.0)
    p = p + bx(-3.0, 3.0, y0 + 0.79, y0 + 3.7, L["z"] - 2.0, L["z"] + 2.0)
    return check("E13-T", p)


def torso_front_y(x, z):
    """y of the torso's outer front skin (superellipse spec.TORSO n, section at z) at |x| (negative = front)."""
    aa, bb_ = spec.torso_section(z)
    n = T["n"]
    u = min(1.0, abs(x) / aa)
    return -bb_ * (1.0 - u ** n) ** (1.0 / n)


SEN_PAD_T = T["wall"] + 1.2                  # T01 sensor backing pad: skin + 1.2 (torso.py)
SEN_WIN_T = 2.0                              # T06 window depth (torso.py SEN_DEPTH)
TOF_X, ALS_X = -6.0, 6.0                     # REVIEW_NOTES dual-zone window (polished ToF zone at x -6)
TOF_POCKET = (9.0, 3.2, 1.2)                 # T06 ToF zone thinned from the inside to 0.8 (torso.py)


def pad_back_y(x):
    return torso_front_y(x, T["sensor"]["z"]) + SEN_PAD_T


SEN_PAD_Y = pad_back_y(0.0)                  # -42.4 at the centre; the pad back face follows the curved skin
SEN_WIN_BACK = torso_front_y(TOF_X, T["sensor"]["z"]) + SEN_WIN_T
E12_Y0 = pad_back_y(13.0) + 0.05             # E12 front on the pad (its ends), sensors pass the T01 openings


def sensor_holder_t10():
    """Clip behind E12: 2 side lugs glued to the T01 pad + 2 bars pressing the PCB (connector between)."""
    S = T["sensor"]
    y0 = pad_back_y(16.6) + 0.05                         # pad back face is curved (superellipse skin)
    y1 = E12_Y0 + 4.0
    z0, z1 = S["z"] - 5.5, S["z"] + 5.5
    h = None
    for sx in (-1, 1):
        lug = bx(sx * 13.3, sx * 16.6, y0, y1, z0, z1)
        h = lug if h is None else h + lug
    yb0 = E12_Y0 + 1.0 + 0.02
    for (za, zb) in ((z0, S["z"] - 2.5), (S["z"] + 2.5, z1)):
        h = h + bx(-16.6, 16.6, yb0, y1, za, zb)
    return check("T10", fil(h, 0.5, par("y")))


def gasket_t11():
    """TPU 1.0 in the thinned ToF pocket of T06: separates the VL53L1X emitter / receiver apertures."""
    S = T["sensor"]
    w, hgt, _ = TOF_POCKET
    y1 = SEN_WIN_BACK - 0.1
    g = rbox(TOF_X - w / 2 + 0.25, TOF_X + w / 2 - 0.25, y1 - 1.0, y1, S["z"] - hgt / 2 + 0.2, S["z"] + hgt / 2 - 0.2,
             hgt / 2 - 0.25, "y")
    for dx in (-1.4, 1.4):
        g = g - bx(TOF_X + dx - 0.6, TOF_X + dx + 0.6, y1 - 2, y1 + 1, S["z"] - 0.6, S["z"] + 0.6)
    return check("T11", g)


def sensor_pcb_e12():
    S = T["sensor"]
    yf = E12_Y0
    p = board(-13.0, 13.0, yf, yf + 1.0, S["z"] - 6.0, S["z"] + 6.0, 1.0)
    p = p + bx(TOF_X - 2.45, TOF_X + 2.45, yf - 1.56, yf + 0.01, S["z"] - 1.25, S["z"] + 1.25)   # VL53L1X
    p = p + bx(ALS_X - 2.0, ALS_X + 2.0, yf - 1.0, yf + 0.01, S["z"] - 1.0, S["z"] + 1.0)         # ALS
    p = p + bx(-4.0, 4.0, yf + 0.99, yf + 3.6, S["z"] - 2.0, S["z"] + 2.0)                       # JST-SH
    return check("E12", p)


def arm_driver_a06(sx):
    """Arm driver: 25T spline socket (slip clutch) on the servo, pin Ø15 in the 6702, shaft Ø13.8 through A04,
    flange Ø20 x 2 in the A04 spigot pocket, 2x M2x5 from inside A02 through the hub web."""
    xs = SV_ARM_TOP + SV_BOSS_H + 0.1
    fd, ft, pcd = A06_FLANGE
    xf1 = A06_WEB_X - 0.1
    xf0 = xf1 - ft
    a = cx(7.5, xs, 51.6, SH_Y, SH_Z)
    a = a + cx(8.6, 51.6, 52.4, SH_Y, SH_Z)
    a = a + cx(6.9, 52.3, xf0 + 0.05, SH_Y, SH_Z)
    a = a + cx(fd / 2 - 0.1, xf0, xf1, SH_Y, SH_Z)
    a = fil(a, 0.4, at("x", xs))
    a = fil(a, 0.3, at("x", xf1))
    a = a - cx(SV_SPL_D / 2 + 0.1, xs - 1, xs + 3.2, SH_Y, SH_Z)                 # spline socket
    for sy in (-1, 1):
        a = a - cx(0.8, xf1 - 2.5, xf1 + 1, SH_Y + sy * pcd / 2, SH_Z)             # 2x M2 tapped
    a = a - cx(1.1, xs + 3.0, xf1 + 1, SH_Y, SH_Z)                              # servo horn screw access
    a = a - ring_x(5.6, 6.0, xs + 4.0, xs + 4.6, SH_Y, SH_Z)                     # clutch ring groove (visual)
    if sx < 0:
        a = mirror(a, Plane.YZ)
    return check("A06", a)


def arm_bearing_m4(sx):
    b = bearing_local(7.5, 10.5, 4.0)
    b = on_plane(b, (47.5, SH_Y, SH_Z), (1, 0, 0))
    sleeve = ring_x(10.5, 11.4, 47.0, 52.0, SH_Y, SH_Z) + ring_x(9.4, 11.4, 51.5, 52.0, SH_Y, SH_Z)
    b = b + sleeve
    if sx < 0:
        b = mirror(b, Plane.YZ)
    return check("M4", b)


# =========================================================================================================
# BASE ("" fixed, J1 hub)
# =========================================================================================================
BASE_IN_Z0 = B["plate_h"]                    # 4 (top of B02)
BASE_TOP_IN = B["z1"] - B["shell_wall"]      # 39.5 underside of the top wall
YB = B["yaw_bearing"]                        # 6808 40/52/7
YB_Z0 = BASE_TOP_IN - YB["w"]                # 32.5
YM = B["yaw_motor"]
BELT_Z0, BELT_W = 26.0, 6.0                  # GT2 6 mm belt plane z 26..32
HUB_TEETH = (25.6, 32.0)                     # 72T tooth zone
MOT_Z0 = 5.2                                 # GM3506 underside (on the 1.1 mm B07 plate)
B07_Z0 = BASE_IN_Z0 + 0.1
SR_Z0 = 18.0                                 # slip ring flange underside
CELL = B["batteries"]
CELL_ZC = BASE_IN_Z0 + 0.75 + CELL["d"] / 2  # 14.0
E11_Z0 = 27.5
E11_X0, E11_X1, E11_Y0, E11_Y1 = -70.5, -30.5, -10.0, 56.0
SPK = B["speaker"]
SPK_Z0 = 11.0                                # speaker face (down) .. +6
IO_Y1 = 55.45                                # rear I/O board back face (+Y side, USB-C 7.35 deep -> 62.8)


def hub_b06():
    r = YB["id"] / 2
    h = cz(r, YB_Z0 - 0.1, B["z1"] - B["turntable_recess"] + 0.2)            # in the 6808 + up to B05 (40.2)
    h = h + cz(22.0, HUB_TEETH[1] - 0.05, YB_Z0)                             # inner-ring shoulder
    teeth, ro = gt2_profile(72, HUB_TEETH[0], HUB_TEETH[1] - HUB_TEETH[0])
    h = h + teeth
    h = h + cz(ro + 1.9, HUB_TEETH[0] - 0.8, HUB_TEETH[0] + 0.02)            # lower flange
    h = h + cz(17.0, HUB_TEETH[0] - 1.6, HUB_TEETH[0] - 0.7)                 # screw land
    h = h - cz(7.0, 0, 50)                                                    # Ø14 slip-ring bore
    for k in range(3):                                                        # 3x M3 on the J1 PCD
        a = math.radians(90 + 120 * k)
        x, y = J1_PCD_R * math.cos(a), J1_PCD_R * math.sin(a)
        h = h - cz(1.65, 0, 50, x, y)
        h = h - cz(2.9, 0, HUB_TEETH[0] + 2.5, x, y)
    return check("B06", h)


def bearing_6808_m1():
    return check("M1", Pos(PX, PY, YB_Z0) * bearing_local(YB["id"] / 2, YB["od"] / 2, YB["w"]))


def motor_e7():
    x, y = YM["x"], YM["y"]
    z0, z1 = MOT_Z0, MOT_Z0 + YM["h"]
    st = cz(16.0, z0, z0 + 6.0, x, y)                                         # stator base
    st = st + cz(YM["d"] / 2 - 2.5, z0 + 5.0, z0 + 7.5, x, y)
    bell = cz(YM["d"] / 2, z0 + 7.0, z1, x, y)
    bell = fil(bell, 1.2, lambda e: at("z", z1)(e))
    bell = fil(bell, 0.6, lambda e: at("z", z0 + 7.0)(e))
    for k in range(12):                                                       # ventilation slots on the bell
        a = math.radians(30 * k + 15)
        bell = bell - Pos(x + 14.0 * math.cos(a), y + 14.0 * math.sin(a), z1 - 0.6) * Rot(0, 0, 30 * k + 15) * \
            bx(-3.0, 3.0, -1.0, 1.0, -1, 2)
    m = st + bell
    m = m + cz(2.0, z1, z1 + 0.6, x, y)
    m = m + bx(x + 15.0, x + 21.0, y - 2.0, y + 2.0, z0 + 1.0, z0 + 3.0)                # wire exit (+X)
    return check("E7", m)


def pulley_e7p():
    x, y = YM["x"], YM["y"]
    z1 = MOT_Z0 + YM["h"]
    t, ro = gt2_profile(16, BELT_Z0 - 0.3, BELT_W + 0.6, x, y)
    p = t + cz(7.0, z1, BELT_Z0 - 0.3 + 0.02, x, y) + cz(7.0, BELT_Z0 + BELT_W + 0.3 - 0.02, BELT_Z0 + BELT_W + 0.9, x, y)
    p = p - cz(2.1, z1 - 1, BELT_Z0 + 10, x, y)                                 # over the rotor shaft boss
    p = p - cy(1.25, y, y + 10, x, (z1 + BELT_Z0) / 2)                        # grub screw
    return check("E7-P", p)


def belt_e7r():
    """GT2 belt loop round the 72T hub (OD 45.3) and the 16T pulley (OD 9.7) at 48 mm."""
    _, r1 = gt2_profile(72, 0, 1)
    _, r2 = gt2_profile(16, 0, 1)
    d = YM["x"]

    def loop(ra, rb):
        c = (ra - rb) / d
        phi = math.acos(c)
        p1u = Vector(ra * math.cos(phi), ra * math.sin(phi), BELT_Z0)
        p1l = Vector(ra * math.cos(phi), -ra * math.sin(phi), BELT_Z0)
        p2u = Vector(d + rb * math.cos(phi), rb * math.sin(phi), BELT_Z0)
        p2l = Vector(d + rb * math.cos(phi), -rb * math.sin(phi), BELT_Z0)
        e1 = Edge.make_three_point_arc(p1u, Vector(-ra, 0, BELT_Z0), p1l)
        e2 = Edge.make_line(p1l, p2l)
        e3 = Edge.make_three_point_arc(p2l, Vector(d + rb, 0, BELT_Z0), p2u)
        e4 = Edge.make_line(p2u, p1u)
        return Face(Wire([e1, e2, e3, e4]))

    fo = loop(r1 + 1.0, r2 + 1.0)
    fi = loop(r1 + 0.05, r2 + 0.05)
    so = Solid.extrude(fo, Vector(0, 0, BELT_W))
    si = Pos(0, 0, -1) * Solid.extrude(fi, Vector(0, 0, BELT_W + 2))
    return check("E7-R", so - si)


def motor_bracket_b07():
    """1.1 mm steel bracket: plate under the motor (tension slots ±1.5), 2 legs to the top wall, slip-ring arm."""
    x, y = YM["x"], YM["y"]
    t = 1.1
    p = bx(27.0, B["screws"]["xy"][0][0] - 4.5, -24.0, 24.0, B07_Z0, B07_Z0 + t)     # clear of the B01 boss (75, 0)
    p = p - cz(6.0, 0, 20, x, y)
    p = p - cz(SPK["d"] / 2 + 3.2, 0, 20, SPK["x"], SPK["y"])               # clear the B11 speaker box
    for k in range(4):                                                       # slotted holes (belt tension)
        a = math.radians(45 + 90 * k)
        cxp, cyp = x + 9.5 * math.cos(a), y + 9.5 * math.sin(a)
        p = p - (bx(cxp - 1.5, cxp + 1.5, cyp - 1.6, cyp + 1.6, 0, 20) + cz(1.6, 0, 20, cxp - 1.5, cyp)
                 + cz(1.6, 0, 20, cxp + 1.5, cyp))
    for sy in (-1, 1):
        y0, y1 = sy * 22.0, sy * (22.0 + t)
        p = p + bx(50.0, 62.0, y0, y1, B07_Z0, BASE_TOP_IN)
        p = p + bx(50.0, 62.0, sy * 17.0, y1, BASE_TOP_IN - t, BASE_TOP_IN)
    # slip-ring arm: up at x 26..27.1 then in to the yaw axis at z SR_Z0 - t .. SR_Z0
    p = p + bx(25.9, 27.1, -5.0, 5.0, B07_Z0, SR_Z0)
    arm = bx(-8.0, 27.1, -5.0, 5.0, SR_Z0 - t, SR_Z0) - cz(4.0, 0, 30)
    p = p + arm
    for sx in (-1, 1):
        p = p - cz(0.8, 0, 30, sx * 8.5, 0)
    p = fil(p, 0.8, par("z"))
    return check("B07", p)


def slip_ring_e9():
    z0 = SR_Z0
    s = cz(11.0, z0, z0 + 1.5) - cz(0.8, z0 - 1, z0 + 3, 8.5, 0) - cz(0.8, z0 - 1, z0 + 3, -8.5, 0)
    s = s + cz(6.25, z0 + 1.4, z0 + 21.4)
    s = fil(s, 0.5, at("z", z0 + 21.4))
    s = s + cz(2.5, z0 + 21.3, B["z1"] - B["turntable_recess"] + 0.1)        # rotor wire exit (B05 hole)
    s = s + cz(2.6, z0 - 6.0, z0 + 0.1)                                       # stator wire bundle
    return check("E9", s)


def cell_e8(i):
    x = CELL["x"][i]
    r, L = CELL["d"] / 2, CELL["len"]
    c = cy(r, -L / 2, L / 2, x, CELL_ZC)
    c = fil(c, 0.8)
    c = c + cy(3.0, L / 2 - 0.05, L / 2 + 0.6, x, CELL_ZC)                     # + terminal button
    c = c - (cy(r + 1, -L / 2 + 1.0, -L / 2 + 1.6, x, CELL_ZC) - cy(r - 0.25, -L / 2, L / 2, x, CELL_ZC))
    return check(f"E8-{i + 1}", c)


def cell_holder_e8h():
    xs = CELL["x"]
    L = CELL["len"]
    x0, x1 = min(xs) - CELL["d"] / 2 - 2.2, max(xs) + CELL["d"] / 2 + 2.2
    ye = L / 2 + 0.7
    z0, z1 = BASE_IN_Z0 + 0.6, CELL_ZC + CELL["d"] / 2 + 2.2
    h = None
    for sy in (-1, 1):
        end = bx(x0, x1, sy * ye, sy * (ye + 2.6), z0, z1)
        for x in xs:                                                         # contact springs (pocketed)
            end = end - cy(5.5, sy * ye - 1, sy * (ye + 1.2), x, CELL_ZC)
        h = end if h is None else h + end
    for xx in (x0, x1 - 2.0):                                                # side rails
        h = h + bx(xx, xx + 2.0, -ye, ye, CELL_ZC - 3.0, z1)
    for yy in (-16.0, 16.0):                                                 # top straps
        h = h + bx(x0, x1, yy - 3.0, yy + 3.0, z1 - 2.0, z1)
    for sy in (-1, 1):                                                       # posts to the top wall (pass E11)
        h = h + cz(3.0, z1 - 0.5, BASE_TOP_IN, (xs[0] + xs[1]) / 2, sy * (ye + 1.3))
        h = h - cz(1.1, z1, BASE_TOP_IN + 1, (xs[0] + xs[1]) / 2, sy * (ye + 1.3))
    for (x, y) in ((xs[0], 16.0), (xs[1], 16.0)):                            # E11 support bosses (on the straps)
        h = h + cz(2.5, z1 - 0.5, E11_Z0, x, y)
    # spring contacts (nickel strip look) inside the pockets
    for sy in (-1, 1):
        for x in xs:
            h = h + cy(4.5, sy * (ye - 0.05), sy * (ye + 1.25), x, CELL_ZC)
    h = fil(h, 0.5, par("z"))
    return check("E8-H", h)


def base_board_e11():
    z0, z1 = E11_Z0, E11_Z0 + 1.6
    b = board(E11_X0, E11_X1, E11_Y0, E11_Y1, z0, z1, 3.0)
    xs = CELL["x"]
    ye = CELL["len"] / 2 + 0.7 + 1.3
    b = b - cz(3.3, z0 - 1, z1 + 1, (xs[0] + xs[1]) / 2, ye)
    c = []
    c.append(bx(-66.0, -52.8, 20.0, 36.6, z1, z1 + 2.4))                       # ESP32-C3 module
    c.append(bx(-48.0, -41.0, 22.0, 29.0, z1, z1 + 0.9))                       # RP2040
    c.append(bx(-48.0, -40.0, 4.0, 10.0, z1, z1 + 1.2))                        # FOC driver
    c.append(rbox(-64.0, -57.0, 2.0, 9.0, z1, z1 + 4.0, 0.6, "z"))             # inductor
    c.append(bx(-40.0, -34.0, 40.0, 46.0, z1, z1 + 1.0))                       # USB-PD controller
    c.append(bx(-66.0, -60.0, 44.0, 50.0, z1, z1 + 1.0))                       # BMS / fuel gauge
    c.append(bx(-52.0, -46.0, 44.0, 49.0, z1, z1 + 1.0))                       # MAX98357A
    c.append(cz(3.15, z1, z1 + 7.7, -36.0, -4.0))                              # bulk cap
    c.append(bx(-69.0, -61.0, -9.0, -3.0, z1, z1 + 6.0))                       # battery JST-XH
    return check("E11", union([b] + c))


def io_board_e11io():
    y0, y1 = IO_Y1 - 1.6, IO_Y1
    b = board(-46.0, -14.0, y0, y1, 10.0, 26.0, 1.5)
    for x in (-44.0, -16.0):
        b = b - cy(1.0, y0 - 1, y1 + 1, x, 13.0)                              # B09 locating holes
    u = B["usb_c"]
    rec = rbox(u["x"] - 4.47, u["x"] + 4.47, y1, y1 + 7.35, u["z"] - 1.63, u["z"] + 1.63, 1.5, "y")
    rec = rec - rbox(u["x"] - 4.1, u["x"] + 4.1, y1 + 1.0, y1 + 8, u["z"] - 1.28, u["z"] + 1.28, 1.2, "y")
    rec = rec + bx(u["x"] - 3.3, u["x"] + 3.3, y1 + 1.0, y1 + 6.8, u["z"] - 0.35, u["z"] + 0.35)
    bt = B["button"]
    sw = bx(bt["x"] - 3.0, bt["x"] + 3.0, y1, y1 + 3.5, bt["z"] - 3.0, bt["z"] + 3.0) + \
        cy(1.75, y1 + 3.4, y1 + 4.4, bt["x"], bt["z"])
    cap = cy(bt["d"] / 2 - 0.3, y1 + 4.4, B["d"] / 2 - 0.4, bt["x"], bt["z"]) + \
        cy(bt["d"] / 2 + 1.0, y1 + 4.4, y1 + 5.4, bt["x"], bt["z"])
    return check("E11-IO", b + rec + sw + cap)


def io_holder_b09():
    y0, y1 = IO_Y1 - 1.6 - 3.0, IO_Y1 - 1.6
    h = bx(-48.0, -4.6, y0, y1, 8.0, 27.2)
    h = h - fil(bx(-42.0, -18.0, y0 - 1, y1 + 1, 12.0, 24.0), 2.0, par("y"))
    sx0, sy0 = 0.0, 52.0                                                      # B01 screw boss (0, 52) r 4
    h = h + (cz(5.6, 8.0, 27.2, sx0, sy0) - cz(4.05, 0, 40, sx0, sy0))
    h = h - bx(4.0, 7.0, sy0 - 1.2, sy0 + 1.2, 0, 40)                         # clamp slit
    for x in (-44.0, -16.0):
        h = h + cy(0.9, y1 - 0.1, y1 + 1.9, x, 13.0)                          # locating pins
    return check("B09", fil(h, 0.5, par("y")))


def speaker_e5():
    x, y = SPK["x"], SPK["y"]
    r, z0 = SPK["d"] / 2, SPK_Z0
    s = cz(r, z0, z0 + 1.0, x, y) - cz(r - 2.0, z0 - 1, z0 + 0.6, x, y)       # frame rim (face down)
    s = s + (cz(r - 2.0, z0 + 0.6, z0 + 1.6, x, y) - cz(r - 3.5, z0, z0 + 1.2, x, y))
    s = s + cz(r - 3.5, z0 + 1.2, z0 + 1.6, x, y)                             # cone / membrane
    s = s + cz(10.0, z0 + 1.5, z0 + SPK["h"], x, y)                           # magnet cup
    s = fil(s, 0.6, lambda e: at("z", z0 + SPK["h"])(e))
    s = s + bx(x + 9.0, x + 14.0, y - 1.5, y + 1.5, z0 + 1.5, z0 + 3.0)       # solder tabs
    return check("E5", s)


def speaker_box_b11():
    """Sealed back box (>= 15 cm3) above the face-down speaker + front chamber + 30 x 6 duct to the grille."""
    x, y = SPK["x"], SPK["y"]
    r = SPK["d"] / 2
    w = 1.5
    zb, zt = BASE_IN_Z0 + 0.05, 29.0                                          # stands on B02
    g = B["grille"]
    gx0 = g["xc"] - (g["cols"] - 1) / 2 * g["pitch"] - g["hole_d"] / 2 - 1.5
    gx1 = g["xc"] + (g["cols"] - 1) / 2 * g["pitch"] + g["hole_d"] / 2 + 1.5
    gz0, gz1 = min(g["z"]) - g["hole_d"] / 2 - 1.5, max(g["z"]) + g["hole_d"] / 2 + 1.5
    yw = B["d"] / 2 - B["shell_wall"]                                           # 61.5 mouth bonded to the wall
    outer = cz(r + 1.0 + w, zb, zt, x, y)
    outer = fil(outer, 2.0, lambda e: at("z", zt)(e))
    duct_o = bx(x - 15.0 - w, x + 15.0 + w, y, yw - 3.0, zb, SPK_Z0)
    flare_o = bx(gx0 - w, gx1 + w, yw - 3.0, yw, gz0 - w, gz1 + w)
    flare_o = flare_o + bx(x - 15.0 - w, x + 15.0 + w, yw - 3.0 - 2.0, yw, zb, gz1 + w)
    s = outer + duct_o + flare_o
    # cavities: back box above the speaker ledge, front chamber below, duct, flare mouth (open to the wall)
    s = s - cz(r + 1.0, SPK_Z0 + 1.0, zt - w, x, y)                           # back box (sealed by the speaker)
    s = s - cz(r - 2.5, zb + w, SPK_Z0 + 0.05, x, y)                          # front chamber
    s = s - cz(r + 0.2, SPK_Z0, SPK_Z0 + 1.05, x, y)                          # speaker seat
    s = s - bx(x - 15.0, x + 15.0, y, yw - 2.0, zb + w, SPK_Z0 - 0.4)          # duct 30 x 6
    s = s - bx(gx0, gx1, yw - 2.0, yw + 1, gz0, gz1)                          # mouth
    s = s - bx(x - 15.0, x + 15.0, yw - 3.5, yw + 1, zb + w, gz1)             # duct -> mouth riser
    s = s - cz(4.6, 0, 50, 0.0, B["screws"]["xy"][2][1])                      # clear the B01 boss (0, 52)
    return check("B11", s)


def led_carrier_b10():
    L = B["led"]
    yw = -(B["d"] / 2 - B["shell_wall"])                                      # -61.5 inner front wall
    c = rbox(-25.0, 25.0, yw, yw + 8.0, L["z"] - 5.0, L["z"] + 5.0, 1.0, "y")
    c = c - fil(bx(-23.0, 23.0, yw - 1, yw + 9, L["z"] - 2.5, L["z"] + 2.5), 2.4, par("y"))
    bxy = B["screws"]["xy"][3]                                                  # B01 boss (0, -52) r 4
    c = c - cz(4.6, 0, 50, bxy[0], bxy[1])
    return check("B10", c)


def led_pcb_e13b():
    L = B["led"]
    y0 = -(B["d"] / 2 - B["shell_wall"]) + 8.0                                # -53.5
    # two halves left/right of the B01 screw boss (0, -52): 2 x 2 LEDs at x ±6.5, ±15.5
    halves = []
    for sx in (-1, 1):
        h = board(sx * 5.0, sx * 24.0, y0, y0 + 0.8, L["z"] - 4.5, L["z"] + 4.5, 1.0)
        for x in (6.5, 15.5):
            h = h + bx(sx * x - 1.0, sx * x + 1.0, y0 - 0.84, y0 + 0.01, L["z"] - 1.0, L["z"] + 1.0)
        h = h + bx(sx * 18.0, sx * 23.0, y0 + 0.79, y0 + 3.7, L["z"] - 2.0, L["z"] + 2.0)
        halves.append(h)
    return check("E13-B", Compound(halves), multi=True)


# =========================================================================================================
def build():
    eh = EXPLODE_HEAD
    P = PartRec
    parts = [
        # ---------------- HEAD (J3) ----------------
        P("H11", "Vnútorná kostra hlavy", chassis_h11(), "grey", "head", "J3", eh, True,
          "MJF PA12 2–2.5 mm: predná doska za displejom, 2 lícnice na nábojoch N07 (x ±30.4), horný most, 4 úchyty do H01"),
        P("E2", "Displej 4.3\" 800×480 RGB", display_e2(), "display", "head", "J3", eh, True,
          "105.5×67.2×4, zovretý medzi osadením H03 (pena 0.5) a H11; FPC 40 pin zahnutý pod H11 k H13"),
        P("H13", "Doska hlavy ESP32-S3", board_h13(), "pcb", "head", "J3", eh, True,
          "58×45: ESP32-S3-WROOM-1 + PSRAM, RGB displej, LED uší, I2S mikrofóny, dotyk, USB kamera, konektor W1"),
        P("E3", "Kamera USB UVC", camera_e3(), "black", "head", "J3", eh, True,
          "modul 8.5×8.5×5 za okienkom (z 250.5), penový krúžok OD8/ID3.6×0.5 na skle"),
        P("H12", "Držiak kamery", holder_h12(), "grey", "head", "J3", eh, True,
          "U-rámik na H11, tlačí kameru na sklo, 2× M1.6"),
        P("H07-R", "DPS ucha pravá", ear_pcb_h07(-1), "pcb", "head", "J3", eh, True,
          "Ø29: 12× WS2812B-2020, dotyková plôška, MEMS mikrofón s tesnením Ø4×0.3 k otvoru Ø1"),
        P("H07-L", "DPS ucha ľavá", ear_pcb_h07(1), "pcb", "head", "J3", eh, True,
          "Ø29: 12× WS2812B-2020, dotyková plôška, MEMS mikrofón s tesnením Ø4×0.3 k otvoru Ø1"),
        P("W1-H", "Kábelový zväzok – hlava", head_cable_w1h(), "black", "head", "J3", eh, True,
          "7 vodičov Ø4 (USB2, 2×5 V, 2×GND, zbernica serv): H13 → okno lícnice → dutý čap N07-L"),
        # ---------------- NECK ----------------
        P("E6-T", "Servo náklonu SCS0009", tilt_servo_e6t(), "servo", "neck", "J2", (0, 0, 0), True,
          "na osi náklonu v N06, bez uší, čelo zarovno s koncom valca (x −18), drážkovanie v M6"),
        P("M6", "Al vložka drážkovania", spline_insert_m6(), "metal", "neck", "J3", (0, 0, 0), True,
          "Al Ø20×5 v N07-R, drážkovanie 25T (záber 2.9)"),
        P("N05", "Zátka náklonu", plug_n05(), "grey", "neck", "J2", (0, 0, 0), True,
          "čap Ø32 v otvore N06 (3 kľúče, 3× M2), nesie vonkajší krúžok ložiska 6703 a kotvu pružiny"),
        P("M3", "Ložisko 6703-2RS", bearing_6703_m3(), "metal", "neck", "J2", (0, 0, 0), True,
          "17×23×4 na dutom čape N07-L (prechod káblov Ø13)"),
        P("M5", "Špirálová pružina náklonu", spring_m5(), "metal", "neck", "J2", (0, 0, 0), True,
          "pásik 3.0×0.4, ~1.25 závitu, vnútorný koniec v drážke čapu N07-L, vonkajší na kolíku N05"),
        P("N03", "Náboj otáčania hlavy", hub_n03(), "metal", "neck", "J2", (0, 0, 0), True,
          "Ø25 h6 v 61805, príruba Ø30×1.5 (z 147.5–149, 2 drážky pre N02), 2× M2.5 pre N06, kanál 7×12 + okno"),
        P("N04", "Preklzová spojka J2", clutch_n04(), "metal", "neck", "J2", (0, 0, 0), True,
          "drážkovaný trecí kotúč + vlnová podložka v náboji N03, ~0.15 N·m"),
        P("W1-N", "Kábelový zväzok – krk", neck_cable_w1n(), "black", "neck", "J2", (0, 0, 0), True,
          "plochý 7-žilový prepoj 7×1.2 pri konci serva (medzera 1.75), potom Ø4 cez N06 a N03"),
        P("M2", "Ložisko 61805-2RS", bearing_61805_m2(), "metal", "torso", "J1", (0, 0, 0), True,
          "25×37×7 v náboji T01 pod vrchom trupu (z 132.6–139.6)"),
        P("E6-P", "Servo otáčania hlavy SCS0009", pan_servo_e6p(), "servo", "torso", "J1", (0, 0, 0), True,
          "zvislo pod ložiskom, výstup na osi otáčania, telo smerom −Y, visí na držiaku T07"),
        P("W1-T", "Kábelový zväzok – trup", torso_cable_w1t(), "black", "torso", "J1", (0, 0, 0), True,
          "1.5 závitu okolo serva otáčania (±90°) → konektor na E10"),
        # ---------------- TORSO (J1) ----------------
        P("T07", "Vnútorná kostra trupu", frame_t07(), "grey", "torso", "J1", (0, 0, 0), True,
          "PA12-GF: 2 veže serv ramien (M2 do nálitkov T02 y ±20), priečna doska pre E10, držiak serva hlavy"),
        P("E6-R", "Servo pravého ramena SCS0009", arm_servo(-1), "servo", "torso", "J1", (0, 0, 0), True,
          "visí z osi ramena (y 0, z 115), výstup −X do A06"),
        P("E6-L", "Servo ľavého ramena SCS0009", arm_servo(1), "servo", "torso", "J1", (0, 0, 0), True,
          "visí z osi ramena (y 0, z 115), výstup +X do A06"),
        P("M4-R", "Ložisko 6702-2RS pravé", arm_bearing_m4(-1), "metal", "torso", "J1", (0, 0, 0), True,
          "15×21×4 v puzdre zalisovanom do otvoru Ø23 T02-R"),
        P("M4-L", "Ložisko 6702-2RS ľavé", arm_bearing_m4(1), "metal", "torso", "J1", (0, 0, 0), True,
          "15×21×4 v puzdre zalisovanom do otvoru Ø23 T02-L"),
        P("A06-R", "Unášač pravého ramena", arm_driver_a06(-1), "metal", "arm_R", "J4", (-35, 0, 0), True,
          "Al: drážkovaná zásuvka 25T s preklzom, čap Ø15 v 6702, driek Ø13.8 cez A04, príruba Ø20×2 + 2× M2 do A02"),
        P("A06-L", "Unášač ľavého ramena", arm_driver_a06(1), "metal", "arm_L", "J5", (35, 0, 0), True,
          "Al: drážkovaná zásuvka 25T s preklzom, čap Ø15 v 6702, driek Ø13.8 cez A04, príruba Ø20×2 + 2× M2 do A02"),
        P("T08", "Sánky výpočtového modulu", sled_t08(), "grey", "torso", "J1", (0, 0, 0), True,
          "MJF PA12 2 mm na vežiach T07, 4 dištančné stĺpiky"),
        P("E1", "Raspberry Pi CM5 + nosná doska 75×56", compute_e1(), "pcb", "torso", "J1", (0, 0, 0), True,
          "zvislo pri dvierkach (y 16.8), CM5 smerom dozadu; Pi 5 (85+2.5 s USB/ETH 16 mm) sa nezmestí"),
        P("E1-K", "Aktívny chladič CM5", cooler_e1k(), "metal", "torso", "J1", (0, 0, 0), True,
          "zvislé rebrá + ventilátor, nasáva zdola (nasávacie štrbiny T03) a fúka hore (výfuk T03)"),
        P("E10", "Doska trupu", power_board_e10(), "pcb", "torso", "J1", (0, 0, 0), True,
          "68×43.5: ESP32-S3, zbernica serv, 5.1 V/5 A, 6.0 V/3 A, IMU BMI270; na priečnej doske T07"),
        P("T09", "Nosič LED hrude", led_carrier_t09(), "grey", "torso", "J1", (0, 0, 0), True,
          "biely PC 38×10×8 (vnútri 34×5) za T05, ≥ 6 mm na zmiešanie svetla"),
        P("E13-T", "LED DPS hrude", led_pcb_e13t(), "pcb", "torso", "J1", (0, 0, 0), True,
          "4× WS2812B-2020, rozostup 8 mm"),
        P("T10", "Držiak senzorov", sensor_holder_t10(), "grey", "torso", "J1", (0, 0, 0), True,
          "spona za E12: 2 bočné nálitky lepené na podložku pásu za T06 (z 83.5), 2 priečky tlačia DPS"),
        P("T11", "Tesnenie ToF", gasket_t11(), "black", "torso", "J1", (0, 0, 0), True,
          "čierne TPU 1.0 v zoslabenom ToF okne T06 (x −6), oddelené otvory vysielača a prijímača"),
        P("E12", "DPS ToF + ALS", sensor_pcb_e12(), "pcb", "torso", "J1", (0, 0, 0), True,
          "VL53L1X (x −6, 1.2 mm za oknom cez otvor T01) + ALS (x +6); DPS na podložke pásu"),
        # ---------------- BASE ----------------
        P("B06", "Náboj J1 s remenicou", hub_b06(), "metal", "base", "J1", (0, 0, 0), True,
          "Ø40 k6 v 6808, remenica GT2 72T (PD 45.8), 3× M3 na PCD 32 do vaničky T04, otvor Ø14"),
        P("M1", "Ložisko 6808-2RS", bearing_6808_m1(), "metal", "base", "", (0, 0, 0), True,
          "40×52×7 v nálitku pod vrchom B01"),
        P("E7", "Motor GM3506", motor_e7(), "metal", "base", "", (0, 0, 0), True,
          "gimbal BLDC Ø40×20 mimo osi (x 48), SimpleFOC + AS5048A"),
        P("E7-P", "Remenica GT2 16T", pulley_e7p(), "metal", "base", "", (0, 0, 0), True,
          "na rotore motora, príruby"),
        P("E7-R", "Remeň GT2 6 mm", belt_e7r(), "black", "base", "", (0, 0, 0), True,
          "16T → 72T (4.5 : 1), osová vzdialenosť 48 (napínanie v drážkach B07)"),
        P("B07", "Držiak motora GM3506", motor_bracket_b07(), "metal", "base", "", (0, 0, 0), True,
          "oceľ 1.1 mm: doska s drážkami ±1.5, 2 nohy k vrchu B01, rameno zberacieho krúžku"),
        P("E9", "Zberací krúžok 6 okruhov", slip_ring_e9(), "metal", "base", "", (0, 0, 0), True,
          "Ø12.5×20 v osi, statorová príruba na ramene B07, rotor v otvore B06"),
        P("E8-1", "Článok 18650 č.1", cell_e8(0), "battery", "base", "", (0, 0, 0), True, "3500 mAh, x −38"),
        P("E8-2", "Článok 18650 č.2", cell_e8(1), "battery", "base", "", (0, 0, 0), True, "3500 mAh, x −58"),
        P("E8-H", "Držiak článkov 2S", cell_holder_e8h(), "black", "base", "", (0, 0, 0), True,
          "otvorený zdola (výmena cez B08), pružinové kontakty, 2 stĺpiky k vrchu B01"),
        P("E11", "Doska základne", base_board_e11(), "pcb", "base", "", (0, 0, 0), True,
          "40×66 nad článkami: ESP32-C3 + RP2040 (SimpleFOC), BMS, USB-C PD, merač, MAX98357A"),
        P("E11-IO", "Zadná I/O doska", io_board_e11io(), "pcb", "base", "", (0, 0, 0), True,
          "USB-C (zapustený 1.2 mm) + tlačidlo s hmatníkom Ø6.4"),
        P("B09", "Držiak zadnej I/O dosky", io_holder_b09(), "grey", "base", "", (0, 0, 0), True,
          "2 stredovacie kolíky, objímka na nálitku (0, 52)"),
        P("E5", "Reproduktor Ø36", speaker_e5(), "black", "base", "", (0, 0, 0), True,
          "plochý Ø36×6 ležiaci (membránou dole) na (26, 40)"),
        P("B11", "Box a kanál reproduktora", speaker_box_b11(), "grey", "base", "", (0, 0, 0), True,
          "uzavretý objem ~16 cm³, predná komôrka + kanál 30×6 k zadnej mriežke"),
        P("B10", "Nosič LED základne", led_carrier_b10(), "grey", "base", "", (0, 0, 0), True,
          "biely PC 50×10×8 (vnútri 46×5) za B03, výrez okolo nálitku B01 (0, −52)"),
        P("E13-B", "LED DPS základne", led_pcb_e13b(), "pcb", "base", "", (0, 0, 0), True,
          "2 polovice okolo nálitku B01 (0, −52): 4× WS2812B-2020 na x ±6.5 / ±15.5, ≥ 6 mm na zmiešanie"),
    ]
    return parts


if __name__ == "__main__":
    run_module(build, "internals")
