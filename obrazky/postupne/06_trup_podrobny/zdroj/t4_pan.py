#!/opt/venv/cad/bin/python
"""NOVA mini - T4 torso, module PAN: pan stage + neck lift.

    /opt/venv/cad/bin/python t4_pan.py            build (printed parts cached by source hash), export, parts_pan.json
    /opt/venv/cad/bin/python t4_pan.py --rebuild  ignore the cache
    /opt/venv/cad/bin/python t4_pan.py --noexport build + table only

Frame / numbers: t4_common.py (B frame = pan-stage frame at pan 0, rest pose = lift 0).  PAN-specific numbers:
t4_common.PAN ("additions by pan").  Registry: build() -> dict[name] = t4_common.part(shape, group, mat, printed, label_sk)
Poses for the checks: pose_parts(lift), fpc_lift(lift), fpc_loop(pan) (not part of the registry).

Printed parts   P_sachta (black tough resin)  well 47 x 22 with 8 guide lands (PTFE strip seats), journal D56.14 (+ tape),
                                              stage top (collar-disc seat), hub disc, back-sector floor, bracket pads,
                                              fin + apron for the lift loop, FPC groove, windows for the ear and the tongue
                P_koleso (tough resin)        pan gear m0.8 z36 (21 teeth) + FPC drum sector + lip, stop-pin hole
                P_drziak_serva (PETG)         lift servo bracket (plate, ledge with wedge lip, tab post, slotted lug)
                P_kluka (tough resin)         crank r 10, 21T serrated bore, D2 pin
                L_pata (PETG 100 %)           neck foot (bonded to the front neck half), wire slot, solder pocket
                L_jazyk (PETG)                tongue through the end window = carrier of the moving FPC leg (screwed on
                                              AFTER the neck is in the well - a tab that is part of the foot cannot be
                                              lowered through the well)
                L_ucho (POM or PETG)          yoke ear with the 2.2 x 12.2 slot and the flange
Bought parts    servo_zdvih (MG90S), pins, dowels, screws, inserts, PTFE tapes, custom FPC, micro junction, servo lead.
"""
from __future__ import annotations
import os, sys, math, time, json, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import numpy as np                                    # noqa: E402
import t4_common as C                                 # noqa: E402
import build123d as bd                                # noqa: E402
from build123d import Vector                          # noqa: E402

P = C.PAN
YL, ZL = C.Y_LIFT, C.Z_LIFT                 # lift servo shaft axis (along X): y 23.2, z -24.2
RC = C.R_CRANK                              # 10.0
ZS0 = C.Z_SLOT_REST                         # -34.2  ear slot centre line at rest
WI = C.WELL_IN                              # 47 x 22 r 1.5
WO = C.WELL_OUT                             # 50.2 x 25.2
XW, YW = WO[0] / 2, WO[1] / 2               # 25.1, 12.6  outer faces of the well
XI, YI = WI[0] / 2, WI[1] / 2               # 23.5, 11.0  inner faces
ZWB = C.Z_WALL_BOT                          # -41.3
FT = P["FPC"]["t"]                          # 0.12
TIMES = {}


# =====================================================================================================================
# helpers
# =====================================================================================================================
def one(s):
    """single Solid of a boolean result (largest solid)"""
    sol = list(s.solids()) if hasattr(s, "solids") else [q for x in s for q in x.solids()]
    return sol[0] if len(sol) == 1 else max(sol, key=lambda q: q.volume)


def fuse(shapes):
    shapes = [s for s in shapes if s is not None]
    return shapes[0] if len(shapes) == 1 else shapes[0].fuse(*shapes[1:])


def cut(base, cutters):
    cutters = [c for c in cutters if c is not None]
    return base.cut(*cutters) if cutters else base


def prism_x(pts_yz, x0, x1):
    w = bd.Wire.make_polygon([Vector(x0, y, z) for y, z in pts_yz], close=True)
    return bd.extrude(bd.Face(w), amount=x1 - x0, dir=(1, 0, 0))


def prism_y(pts_xz, y0, y1):
    w = bd.Wire.make_polygon([Vector(x, y0, z) for x, z in pts_xz], close=True)
    return bd.extrude(bd.Face(w), amount=y1 - y0, dir=(0, 1, 0))


def prism_z(pts_xy, z0, z1):
    w = bd.Wire.make_polygon([Vector(x, y, z0) for x, y in pts_xy], close=True)
    return bd.extrude(bd.Face(w), amount=z1 - z0, dir=(0, 0, 1))


def pol(r, az_deg, cx=0.0, cy=0.0):
    a = math.radians(az_deg)
    return cx + r * math.cos(a), cy + r * math.sin(a)


def wedge_z(r, a0, a1, z0, z1):
    """pie wedge (covers the arc of radius r) between the azimuths a0 < a1 (deg)"""
    n = max(2, int(math.ceil((a1 - a0) / 15.0)) + 1)
    step = (a1 - a0) / (n - 1)
    rr = r / math.cos(math.radians(step / 2)) * 1.02
    return prism_z([(0.0, 0.0)] + [pol(rr, a0 + i * step) for i in range(n)], z0, z1)


def tube_sector(ro, ri, a0, a1, z0, z1):
    t = C.cyl_z(ro, z0, z1) - C.cyl_z(ri, z0 - 0.5, z1 + 0.5)
    return one(t & wedge_z(ro, a0, a1, z0 - 1, z1 + 1))


def revolve_z(pts_rz):
    """solid of revolution about Z of a closed (r, z) polygon"""
    w = bd.Wire.make_polygon([Vector(r, 0, z) for r, z in pts_rz], close=True)
    return bd.revolve(bd.Face(w), axis=bd.Axis.Z, revolution_arc=360)


def stadium_y(r, half, x, z, y0, y1):
    """slot along X (centres x +- half) of radius r, extruded along Y"""
    return fuse([C.box(x - half, x + half, y0, y1, z - r, z + r), C.cyl_y(r, y0, y1, x - half, z), C.cyl_y(r, y0, y1, x + half, z)])


def screw_cyl(d, dk, k, length, at, axis, sign):
    """cylinder-head / pan-head screw: head seat at `at`, shank along axis*sign"""
    s = bd.Pos(0, 0, -k / 2) * bd.Cylinder(dk / 2, k) + bd.Pos(0, 0, length / 2) * bd.Cylinder(d / 2, length)
    return one(bd.Pos(*at) * C._along(s, axis, sign))


def arc_pts(c, r, a0, a1, step=10.0):
    """points of an arc (deg), a0 -> a1 inclusive"""
    n = max(2, int(math.ceil(abs(a1 - a0) / step)) + 1)
    return [(c[0] + r * math.cos(math.radians(a0 + (a1 - a0) * i / (n - 1))),
             c[1] + r * math.sin(math.radians(a0 + (a1 - a0) * i / (n - 1)))) for i in range(n)]


def strip_poly(pts, t=FT):
    """closed polygon around an open centreline (list of 2-D points): the strip of thickness t"""
    Q = [pts[0]]
    for p in pts[1:]:
        if math.hypot(p[0] - Q[-1][0], p[1] - Q[-1][1]) > 1e-6:
            Q.append(p)
    A = np.asarray(Q, float)
    T = np.zeros_like(A); T[1:-1] = A[2:] - A[:-2]; T[0] = A[1] - A[0]; T[-1] = A[-1] - A[-2]
    T /= np.linalg.norm(T, axis=1)[:, None]
    N = np.stack([-T[:, 1], T[:, 0]], 1)
    L, R = A + N * t / 2, A - N * t / 2
    return [tuple(p) for p in L] + [tuple(p) for p in R[::-1]]


def gear_profile(m, z, phase_deg=0.0, backlash=0.04, n_inv=7):
    """involute spur gear outline (20 deg) as (r, angle rad) points per tooth; tooth k centred at phase + k * 360 / z.
    Same construction as t4_ram.gear_profile (the pinion).  Returns list[k] = list of (r, a)."""
    rp = m * z / 2; rb = rp * math.cos(math.radians(20.0)); ra = rp + m; rf = rp - 1.25 * m
    s = math.pi * m / 2 - backlash
    ap = math.radians(20.0)

    def inv(a):
        return math.tan(a) - a

    def half(r):
        return s / (2 * rp) + inv(ap) - inv(math.acos(min(1.0, rb / r)))
    r0 = max(rb, rf)
    rs = [r0 + (ra - r0) * i / (n_inv - 1) for i in range(n_inv)]
    pitch = 2 * math.pi / z
    teeth = []
    for k in range(z):
        c = math.radians(phase_deg) + k * pitch
        t = []
        if rf < rb:
            t.append((rf, c - half(r0)))
        t += [(r, c - half(r)) for r in rs] + [(r, c + half(r)) for r in reversed(rs)]
        if rf < rb:
            t.append((rf, c + half(r0)))
        t.append((rf, c + pitch / 2))
        teeth.append(t)
    return teeth


def crank_angle(lift):
    """servo angle (deg) for a lift 0 .. 20: lift = R (1 - cos theta)"""
    return math.degrees(math.acos(max(-1.0, min(1.0, 1.0 - lift / RC))))


def pin_pos(theta_deg):
    """crank-pin centre (y, z) in the stage frame: bottom (theta 0) -> front (90) -> top (180)"""
    a = math.radians(theta_deg)
    return YL - RC * math.sin(a), ZL - RC * math.cos(a)


# =====================================================================================================================
# P_sachta - well + journal + stage top + hub / floor
# =====================================================================================================================
def _land_y(x0, x1, side, z0, z1):
    """guide land on a long wall (side -1 front / +1 back), trapezoid with 45 deg lead-ins"""
    L = P["LAND"]; yf = side * (YI - L["h"]); yb = side * (YI + 0.15); d = L["h"] + 0.15
    return prism_x([(yb, z0 - d), (yf, z0), (yf, z1 - L["lead"]), (yb, z1 + 0.15)], x0, x1)


def _land_x(y0, y1, side, z0, z1):
    L = P["LAND"]; xf = side * (XI - L["h"]); xb = side * (XI + 0.15); d = L["h"] + 0.15
    return prism_y([(xb, z0 - d), (xf, z0), (xf, z1 - L["lead"]), (xb, z1 + 0.15)], y0, y1)


def _under_floor(grow=0.0, z0=None, z1=None):
    """footprint of the FPC run bonded under the floor (trunk + landing under the apron + junction branch) as a prism"""
    F = P["FPC"]; zc = F["z_fix"]
    z0 = zc - FT / 2 if z0 is None else z0; z1 = zc + FT / 2 if z1 is None else z1
    hw = F["w"] / 2 + grow
    tr = bd.Rot(0, 0, F["trunk"]["az"]) * C.box(F["trunk"]["r"][0] - grow, F["trunk"]["r"][1] + grow, -hw, hw, z0, z1)
    wp = C.box(F["lift_x"][0] - grow, F["lift_x"][1] + grow, F["w_piece"]["y"][0] - grow, F["w_piece"]["y"][1] + grow, z0, z1)
    bx = F["branch"]["x"]
    br = C.box(bx[0] - grow, bx[1] + grow, F["branch"]["y0"] - grow, YW - 0.5 + (0.6 if grow else 0.0), z0, z1)
    return fuse([tr, wp, br])


def mk_sachta():
    J = P["JOURNAL"]; rj, ri = J["r_resin"], J["r_in"]
    zj0, zj1 = C.Z_JOURNAL; zc0, zc1 = J["cone_z"]; zp0, zp1 = J["plate_z"]
    rt = C.R_STAGE_TOP
    # ---- top: journal ring with lower chamfer, cone, plate
    top = revolve_z([(0, zp0), (ri, zp0), (ri, zj0), (rj - J["chamfer"], zj0), (rj, zj0 + J["chamfer"]), (rj, zc0), (rt, zc1),
                     (rt, zp1), (0, zp1)])
    fx = J["fill_x"]
    fill = [one(C.cyl_z(ri + 0.1, zj0, zp0 + 0.1) & C.box(s * fx if s > 0 else -40, 40 if s > 0 else -fx, -30, 30, zj0 - 1, 0))
            for s in (1, -1)]
    ribs = []
    for x in J["ribs_x"]:
        for s in (1, -1):
            ya, yb = sorted((s * (YW - 0.2), s * 24.2))
            ribs.append(C.box(x - J["rib_t"] / 2, x + J["rib_t"] / 2, ya, yb, zj0, zp0 + 0.1))
    # ---- well prism, clipped by the cone above z -4.5
    well = C.rbox(-XW, XW, -YW, YW, ZWB, zp1, P["WELL_CORNER_OUT"], "z")
    well = one(well - revolve_z([(rt, zc1), (rj, zc0), (31.0, zc0), (31.0, zp1 + 0.1), (rt, zp1 + 0.1)]))
    body = one(fuse([well, top] + fill + ribs))
    body = one(body - C.rbox(-XI, XI, -YI, YI, ZWB - 0.5, zp1 + 0.5, WI[2], "z"))
    # ---- guide lands = PTFE strip seats
    L = P["LAND"]; lz0, lz1 = L["z"]
    lands = [_land_y(a, b, -1, lz0, lz1) for a, b in L["front_x"]] + [_land_y(a, b, 1, lz0, lz1) for a, b in L["back_x"]]
    lands.append(_land_y(*L["back_up"]["x"], 1, *L["back_up"]["z"]))
    for s in (1, -1):
        lands += [_land_x(a, b, s, lz0, lz1) for a, b in L["end_y"]]
    body = one(fuse([body] + lands))
    # ---- windows (ear at the back, tongue / FPC at the +X end)
    wb, we = C.WIN_BACK, C.WIN_END
    body = one(cut(body, [C.box(*wb["x"], *wb["y"], ZWB - 0.5, wb["z"][1]),
                          C.box(we["x"][0], we["x"][1], *P["WIN_END_Y"], ZWB - 0.5, we["z"][1])]))
    # ---- hub disc, back-sector floor, fin + apron, bracket pads
    fz0, fz1 = P["FLOOR"]["z"]
    hub = C.cyl_z(C.R_HUB, C.Z_WELL_FLOOR[0], C.Z_WELL_FLOOR[1])
    floor = one(C.rbox(-XW, XW, -YW, YW, fz0, fz1, P["WELL_CORNER_OUT"], "z") & wedge_z(40.0, *P["FLOOR"]["az"], fz0 - 1, fz1 + 1))
    Fn, Ap = P["FIN"], P["APRON"]
    fin = fuse([C.box(*Fn["x"], *Fn["y"], *Fn["z"]), C.box(*Ap["x"], *Ap["y"], fz0, fz1)])
    fin = one(fin & C.cyl_z(Fn["r_max"], fz0 - 1, 0.0))
    Pd = P["PAD"]
    pads = [C.cyl_y(Pd["r"], YW - 0.2, Pd["face_y"], b["x"], b["z"]) for b in P["PADS"]]
    body = one(fuse([body, hub, floor, fin] + pads))
    # ---- cuts
    N = [C.cyl_z(C.PIVOT["pin_d"] / 2 + 0.025, C.Z_WELL_FLOOR[0] - 0.5, C.Z_WELL_FLOOR[1] + 0.5)]            # pivot bore D6.05
    N += [C.cyl_z(C.GEAR_JOINT["d"] / 2, C.Z_WELL_FLOOR[0] - 0.5, C.Z_WELL_FLOOR[1] + 0.5, *pol(r, az)) for r, az in C.GEAR_JOINT["dowels"]]
    do = C.INSERTS["M2"][2]
    N += [C.cyl_y(do / 2, Pd["face_y"] - Pd["seat_depth"], Pd["face_y"] + 0.5, b["x"], b["z"]) for b in P["PADS"]]
    G = P["FPC_GROOVE"]
    N.append(_under_floor(G["grow"], fz0 - 0.2, fz0 + G["depth"]))
    # integrator: the groove runs out to the apron edge y 8.2 (it left a 0.3 x 0.2 rim and a 14 deg feather edge there)
    N.append(C.box(Ap["x"][0], Ap["x"][1] + 1.0, P["FPC"]["w_piece"]["y"][1], Ap["y"][1] + 0.1, fz0 - 0.2, fz0 + G["depth"]))
    er = Fn["edge_r"]; yf = Fn["y"][0]; zg = fz0 + G["depth"]
    N.append(prism_x([(yf - 0.02, zg - 0.02), (yf + er, zg - 0.02)] + arc_pts((yf + er, zg + er), er, -90, -180) + [(yf - 0.02, zg + er)],
                     Fn["x"][0] - 0.3, Fn["x"][1] + 0.6))                                                     # round the fin edge
    bx = P["FPC"]["branch"]["x"]
    N.append(prism_x([(YW + 0.02, zg - 0.02), (YW + 0.02, zg + er)] + arc_pts((YW - er, zg + er), er, 0, -90) + [(YW - er, zg - 0.02)],
                     bx[0] - 0.3, bx[1] + 0.3))                                                               # round the floor edge
    Gg = P["GLUE_GROOVE"]
    N += [tube_sector(Gg["r"][1], Gg["r"][0], a0, a1, zp1 - Gg["depth"], zp1 + 0.2) for a0, a1 in Gg["az"]]
    Th = P["TOOL_HOLE"]
    N.append(C.cyl_z(Th["d"] / 2, zp0 - 0.5, zp1 + 0.5, *Th["at"]))
    return one(cut(body, N)).clean()


# =====================================================================================================================
# P_koleso - pan gear sector + FPC drum
# =====================================================================================================================
def gear_outline():
    """2-D outline of P_koleso: 21 teeth centred 154.3 .. 354.3, root arcs, smooth drum r 15.7 over drum_az"""
    G = P["GEAR"]
    teeth = gear_profile(C.M_PAN, C.T_PAN[1], G["phase"], G["backlash"])
    rf = G["r_root"]; d0, d1 = G["drum_az"]
    pts = [pol(C.R_DRUM, a) for a in np.arange(d0, d1 + 1e-6, 1.0)]
    k0 = int(round((G["teeth_az"][0] + 5.0 - G["phase"]) / 10.0)); k1 = k0 + G["n_teeth"] - 1
    a_first = math.degrees(teeth[k0][0][1])
    pts += [pol(rf, a) for a in np.linspace(d1, a_first, 5)[:-1]]
    for k in range(k0, k1 + 1):
        pts += [(r * math.cos(a), r * math.sin(a)) for r, a in teeth[k]]
    a_last = math.degrees(teeth[k1][-1][1])
    pts += [pol(rf, a) for a in np.linspace(a_last, 360.0 + d0, 5)[1:]]
    return pts


def mk_koleso():
    G = P["GEAR"]; z0, z1 = C.Z_GEAR_PAN
    body = prism_z(gear_outline(), z0, z1)
    Lp = G["lip"]
    body = one(fuse([body, tube_sector(Lp["r"], C.R_DRUM - 0.4, *Lp["az"], *Lp["z"])]))
    sp = G["stop_pin"]
    N = [C.cyl_z(G["recess"][0], z0 - 0.5, G["recess"][1]), C.cyl_z(C.PIVOT["pin_d"] / 2 + 0.025, z0 - 0.5, z1 + 0.5),
         C.cyl_z(sp["d"] / 2 - 0.01, z0 - 0.5, z1 + 0.5, *pol(sp["r"], sp["az"]))]
    # integrator: 0.05 under the dowels (was 0.15) -> floor 0.6 under the blind holes (K10 min feature)
    N += [C.cyl_z(C.GEAR_JOINT["d"] / 2, G["dowel_z"][0] - 0.05, z1 + 0.5, *pol(r, az)) for r, az in C.GEAR_JOINT["dowels"]]
    return one(cut(body, N)).clean()


# =====================================================================================================================
# lift servo (bought) + bracket + crank
# =====================================================================================================================
def mk_servo():
    """MG90S, E2 model of the neck (user drawing): case 22.5 (X: gear face -6.5 .. bottom cover 16.0) x 12.2 x 22.8,
    keyhole turret (boss r 5.9 + lobe r 2.9 at 5.6) 6.0 high, spline D4.8 x 3.0 with the horn-screw hole, the TOP tab kept
    (2.5 thick, 16.0 .. 18.5 above the bottom, hole D2.2 at 2.45), lower tab cut off.  The block above the top end face
    near the bottom cover is the reserved exit / first bend of the lead."""
    S = C.MG90S; xt, xb = C.LIFT_X; Lc = C.LIFT_CASE
    case = C.box(xt, xb, *Lc["y"], *Lc["z"])
    lr, ld = S["lobe"]
    tur = [C.cyl_x(S["boss_r"], xt - S["turret"], xt + 0.2, YL, ZL), C.cyl_x(lr, xt - S["turret"], xt + 0.2, YL, ZL - ld),
           C.box(xt - S["turret"], xt + 0.2, YL - lr, YL + lr, ZL - ld, ZL)]
    spl = C.cyl_x(S["spline"][0] / 2, xt - S["turret"] - S["spline"][1], xt - S["turret"] + 0.2, YL, ZL)
    T = S["tab"]; zt = Lc["z"][1]
    tab = C.box(xb - T["from_bottom"][1], xb - T["from_bottom"][0], *Lc["y"], zt - 0.2, zt + T["ext"])
    lead = C.box(xb - 4.6, xb - 0.1, YL - 2.5, YL + 2.5, zt - 0.2, zt + 5.0)
    s = one(fuse([case] + tur + [spl, tab, lead]))
    N = [C.cyl_x(T["hole_d"] / 2, xb - T["from_bottom"][1] - 0.5, xb - T["from_bottom"][0] + 0.5, YL, zt + T["hole"]),
         C.cyl_x(1.3, xt - S["turret"] - S["spline"][1] - 0.5, xt - S["turret"] + 2.0, YL, ZL)]     # horn-screw hole (M2.5)
    return one(cut(s, N))


def mk_drziak():
    B = P["BRKT"]; px, py, pz = B["plate_x"], B["plate_y"], B["plate_z"]
    Lg, Rs, Ld, Po = B["lug"], B["rest"], B["ledge"], B["post"]
    b2 = P["PADS"][1]
    S = [C.box(*px, *py, *pz),
         C.box(b2["x"] - B["tab2"]["half"], b2["x"] + B["tab2"]["half"], *py, pz[1] - 0.2, B["tab2"]["z_top"]),   # tab around the upper screw
         C.box(Lg["x"][0] - 0.2, Lg["x"][1], *py, *Lg["z"]),
         C.box(*Rs["x"], Rs["y"], py[0] + 0.1, *Rs["z"]),
         C.box(*Ld["x"], py[1] - 0.1, Ld["y"][1], *Ld["z"]),
         C.box(*Ld["lip_x"], Ld["y"][1] - 0.1, Ld["lip_y"][1], *Ld["z"]),
         prism_x([(Ld["lip_y"][0], Ld["z"][1] - 0.05), (Ld["lip_y"][1], Ld["z"][1] - 0.05), (Ld["lip_y"][1], Ld["z"][1] + Ld["lip_h"])],
                 *Ld["lip_x"]),
         C.box(*Po["x"], py[1] - 0.1, Po["y"][1], *Po["z"])]
    body = one(fuse(S))
    Pd = P["PAD"]; N = []
    for b in P["PADS"]:
        N.append(stadium_y(Pd["r"] + 0.25, B["slot"], b["x"], b["z"], py[0] - 0.5, Pd["face_y"]))     # pocket over the pad
        N.append(stadium_y(C.SCREWS["M2"][1] / 2, B["slot"], b["x"], b["z"], Pd["face_y"] - 0.2, py[1] + 0.5))   # slot 2.3 x 4.3
    T = C.MG90S["tab"]; xb = C.LIFT_X[1]; zt = C.LIFT_CASE["z"][1]
    N.append(C.cyl_x(Po["pilot_d"] / 2, Po["x"][0] - 0.2, Po["x"][0] + Po["pilot_depth"], YL, zt + T["hole"]))
    return one(cut(body, N)).clean()


def mk_kluka(theta=0.0):
    """crank at servo angle theta (deg); theta 0 = rest (pin at the bottom dead centre)"""
    K = C.CRANK; S = P["CRANK"]["spline"]
    al = math.degrees(math.asin((K["hub_r"] - K["tip_r"]) / RC))
    prof = arc_pts((YL, ZL), K["hub_r"], -al, 180.0 + al, 8.0) + arc_pts((YL, ZL - RC), K["tip_r"], 180.0 + al, 360.0 - al, 12.0)
    arm = prism_x(prof, *K["arm_x"])
    hub = C.cyl_x(K["hub_r"], *K["hub_x"], YL, ZL)
    body = one(fuse([arm, hub]))
    n = S["n"]
    ser = [(YL + (S["d_major"] if i % 2 == 0 else S["d_minor"]) / 2 * math.cos(math.pi * i / n),
            ZL + (S["d_major"] if i % 2 == 0 else S["d_minor"]) / 2 * math.sin(math.pi * i / n)) for i in range(2 * n)]
    N = [prism_x(ser, S["x"][0], S["x"][1] + 0.3),
         C.screw_hole("M2.5c", 3.0, (K["hub_x"][0], YL, ZL), "x", 1, head_len=0.3),
         C.cyl_x(P["CRANK"]["pin_hole_d"] / 2, K["arm_x"][0] - 0.3, K["arm_x"][1] + 0.3, YL, ZL - RC)]
    s = one(cut(body, N)).clean()
    return s if theta == 0 else one(bd.Pos(0, YL, ZL) * bd.Rot(-theta, 0, 0) * bd.Pos(0, -YL, -ZL) * s)


def mk_cap_kluky(theta=0.0):
    y, z = pin_pos(theta)
    return C.cyl_x(C.CRANK["pin_d"] / 2, *C.CRANK["pin_x"], y, z)


# =====================================================================================================================
# lift group: foot, tongue, ear
# =====================================================================================================================
def mk_pata():
    F = P["FOOT"]; sx, sy, sz = C.FOOT["size"]; z0, z1 = C.Z_FOOT
    body = C.rbox(-sx / 2, sx / 2, -sy / 2, sy / 2, z0, z1, F["corner_r"], "z")
    pk, ch, ky, tp = F["pocket"], F["channel"], F["key"], F["tongue_pilot"]
    E = P["EAR"]; zs = ZS0
    N = [C.box(*F["slot"]["x"], *F["slot"]["y"], z0 - 0.5, z1 + 0.5),
         C.box(*pk["x"], *pk["y"], z0 - 0.5, z0 + pk["depth"]),
         C.box(pk["x"][1] - 0.2, sx / 2 + 0.5, *ch["y"], z0 - 0.5, z0 + ch["depth"]),
         C.box(ky["x"][0], sx / 2 + 0.5, ky["y"][0] - 0.05, ky["y"][1] + 0.05, ky["z"][0] - 0.05, ky["z"][1] + 0.05),
         C.cyl_x(tp["d"] / 2, tp["x_end"], sx / 2 + 0.5, tp["y"], tp["z"]),
         C.cyl_y(F["ear_pilot"]["d"] / 2, sy / 2 - F["ear_pilot"]["depth"], sy / 2 + 0.5, E["screw"]["x"], zs + E["screw"]["zrel"]),
         C.cyl_y(F["ear_dowel"]["d"] / 2, sy / 2 - F["ear_dowel"]["depth"], sy / 2 + 0.5, E["dowel"]["x"], zs + E["dowel"]["zrel"])]
    N += [C.screw_hole("M2c", sz + 0.4, (x, y, z0), "z", 1, head_len=0.3) for x, y in F["opt_screws"]]
    return one(cut(body, N)).clean()


def _csk16(at_x, y, z, length):
    """cutter for the M1.6 countersunk tongue screw (DIN 965: dk 3.0, k 0.96), head flush at at_x, shank along -X"""
    s = bd.Pos(0, 0, 0.4) * bd.Cone(1.7, 0.9, 0.8) + bd.Pos(0, 0, length / 2) * bd.Cylinder(0.9, length) + \
        bd.Pos(0, 0, -0.15) * bd.Cylinder(1.7, 0.3)
    return bd.Pos(at_x, y, z) * C._along(s, "x", -1)


def mk_jazyk():
    T = P["TONGUE"]; F = P["FOOT"]; B = T["block"]; ky = F["key"]; ch = F["channel"]; rc = T["recess"]
    c = B["chamfer"]; zb = T["z"][1]
    S = [C.box(*T["x"], *T["y"], *T["z"]),
         prism_x([(B["y"][0], zb - 0.1), (B["y"][1], zb - 0.1), (B["y"][1], B["z_top"] - c), (B["y"][1] - c, B["z_top"]),
                  (B["y"][0] + c, B["z_top"]), (B["y"][0], B["z_top"] - c)], *B["x"]),
         C.box(ky["x"][0], T["x"][0] + 0.1, ky["gap_y"], ky["y"][1], *ky["z"]),          # key = 2 prongs beside the screw hole
         C.box(ky["x"][0], T["x"][0] + 0.1, ky["y"][0], -ky["gap_y"], *ky["z"])]
    body = one(one(fuse(S)) & C.cyl_z(T["r_max"], -60, 0))
    z0 = T["z"][0]; zc = z0 + ch["depth"]; tp = F["tongue_pilot"]
    N = [_csk16(T["x"][1], tp["y"], tp["z"], T["x"][1] - ky["x"][0] + 0.5),
         C.box(T["x"][0] - 0.2, rc["x"][0] + 0.2, *ch["y"], z0 - 0.5, zc),
         C.box(rc["x"][0], T["x"][1] + 0.5, rc["y"][0] - 0.2, rc["y"][1], z0 - 0.5, zc),
         prism_x([(T["y"][0] - 0.02, zc - 0.02), (T["y"][0] + 0.3, zc - 0.02), (T["y"][0] - 0.02, zc + 0.3)], rc["x"][0], T["x"][1] + 0.5)]
    return one(cut(body, N)).clean()


def mk_ucho():
    E = C.EAR; Q = P["EAR"]; x0, x1 = E["x"]; f0, f1 = Q["flange_y"]; zr0, zr1 = E["zrel"]; ch = E["chamfer"]; yp = Q["plate_y0"]
    Fz = E["flange"]["zrel"]; y1 = E["y"][1]
    plate = prism_x([(yp, zr1), (y1 - ch, zr1), (y1, zr1 - ch), (y1, zr0), (f0, zr0), (f0, Fz[1]), (yp, Fz[1])], x0, x1)
    flange = C.box(x0, E["flange"]["x"][1], f0, f1, *Fz)
    body = one(fuse([plate, flange]))
    hw = E["slot_w"] / 2; sy0, sy1 = Q["slot_y"]
    nt = E["flange"]["notch"]
    N = [C.box(x0 - 0.5, x1 + 0.5, sy0 + hw, sy1 - hw, -hw, hw), C.cyl_x(hw, x0 - 0.5, x1 + 0.5, sy0 + hw, 0.0),
         C.cyl_x(hw, x0 - 0.5, x1 + 0.5, sy1 - hw, 0.0),
         C.box(x1, nt["x"][1], f0 - 0.5, f1 + 0.5, nt["zrel"], Fz[1] + 0.5),
         C.cyl_y(C.SCREWS["M2"][1] / 2, f0 - 0.5, f1 + 0.5, Q["screw"]["x"], Q["screw"]["zrel"]),
         C.cyl_y(Q["dowel"]["d"] / 2 + 0.025, f0 - 0.5, f1 + 0.5, Q["dowel"]["x"], Q["dowel"]["zrel"])]
    return one(bd.Pos(0, 0, ZS0) * one(cut(body, N)).clean())


# =====================================================================================================================
# FPC (custom, 3.0 x 0.12): solids for any lift / pan
# =====================================================================================================================
def zc_loop(lift):
    """height of the centre of the U-turn of the lift loop"""
    return P["FPC"]["zc0"] + lift / 2.0


def _lift_profile(lift):
    """centreline (y, z) of the lift loop: tongue recess -> moving leg -> U -> fixed leg on the fin -> under the apron"""
    F = P["FPC"]; zt = F["z_tail"] + lift; ym = F["y_move"] - FT / 2; yf = F["y_fix"]
    rb = 0.3 + FT / 2; zc = zc_loop(lift); R = (yf - ym) / 2; yc = (yf + ym) / 2
    er = P["FIN"]["edge_r"] + FT / 2; zf = F["z_fix"]
    pts = [(F["w"] / 2, zt), (ym + rb, zt)] + arc_pts((ym + rb, zt + rb), rb, -90, -180, 15)
    pts += [(ym, zc)] + arc_pts((yc, zc), R, 180, 0, 6) + [(yf, zf + er)]
    pts += arc_pts((yf + er, zf + er), er, 180, 270, 15) + [(F["w_piece"]["y"][1], zf)]
    return pts


def fpc_lift(lift=0.0):
    """moving part + lift loop (stage frame): paddle and tail under the foot, corner piece under the tongue, loop"""
    F = P["FPC"]; pd = F["paddle"]; zp = pd["z"] + lift; zt = F["z_tail"] + lift
    loop = prism_x(strip_poly(_lift_profile(lift)), *F["lift_x"])
    tail = prism_y(strip_poly([(pd["x"][0], zp), (pd["ramp_x"][0], zp), (pd["ramp_x"][1], zt), (F["lift_x"][0] + 0.2, zt)]),
                   -F["w"] / 2, F["w"] / 2)
    wings = C.box(pd["x"][0], pd["x"][1], pd["y"][0], pd["y"][1], zp - FT / 2, zp + FT / 2)
    return one(fuse([loop, tail, wings]))


def fpc_stage():
    """stage-fixed part between the lift loop and the drum: run under the floor, junction branch up the back wall"""
    F = P["FPC"]; zf = F["z_fix"]; er = P["FIN"]["edge_r"] + FT / 2; bx = F["branch"]["x"]
    yv = YW + FT / 2
    wrap = prism_x(strip_poly([(YW - 2.0, zf), (YW - er + FT / 2, zf)] + arc_pts((YW - er + FT / 2, zf + er), er, -90, 0, 15) +
                              [(yv, F["branch"]["z_top"])]), *bx)
    return one(fuse([_under_floor(), wrap]))


def _riser(pan=0.0):
    """fold from the run under the floor down onto the drum (plane tangent to the drum at the trunk azimuth)"""
    F = P["FPC"]; zf = F["z_fix"]; rho = F["riser"]["rho"]; rb = F["riser"]["bend_r"]
    prof = [(F["trunk"]["r"][0] + 1.3, zf), (rho + rb, zf)] + arc_pts((rho + rb, zf - rb), rb, 90, 180, 15) + [(rho, F["pan"]["z"][1] - 0.1)]
    return bd.Rot(0, 0, F["trunk"]["az"] + pan) * prism_y(strip_poly(prof), -F["w"] / 2, F["w"] / 2)


def loop_centreline(pan=0.0):
    """centreline (x, y) of the pan strip in the B frame: flat on the drum under the riser -> inner run on the drum ->
    U-turn -> outer run on the static wall -> static end behind the clamp"""
    F = P["FPC"]; Q = F["pan"]; ri, ro = Q["r_in"], Q["r_out"]; a0 = F["trunk"]["az"] + pan
    u = Q["u0"] + Q["k"] * pan
    er, et = (math.cos(math.radians(a0)), math.sin(math.radians(a0))), (-math.sin(math.radians(a0)), math.cos(math.radians(a0)))
    hw = F["w"] / 2
    pts = [(ri * er[0] + t * et[0], ri * er[1] + t * et[1]) for t in (-hw, 0.0, hw)]
    r1 = math.hypot(ri, hw); a1 = a0 + math.degrees(math.atan2(hw, ri))
    pts += [pol(r1 + (ri - r1) * i / 6.0, a1 + 3.0 * i / 6.0) for i in range(1, 7)]
    pts += [pol(ri, a) for a in np.arange(a1 + 4.0, u - 0.5, 1.0)] + [pol(ri, u)]
    rm, Ru = (ri + ro) / 2, (ro - ri) / 2
    c = pol(rm, u); ur = (math.cos(math.radians(u)), math.sin(math.radians(u))); ut = (-ur[1], ur[0])
    for ph in np.arange(170.0, 5.0, -10.0):
        cs, sn = math.cos(math.radians(ph)), math.sin(math.radians(ph))
        pts.append((c[0] + Ru * (cs * ur[0] + sn * ut[0]), c[1] + Ru * (cs * ur[1] + sn * ut[1])))
    pts += [pol(ro, a) for a in np.arange(u, Q["static_end_az"], -1.0)] + [pol(ro, Q["static_end_az"])]
    return pts


def fpc_loop(pan=0.0):
    """pan rolling loop in the B frame at head pan `pan` (deg): riser on the drum (rotates) ... static tail through the deck"""
    Q = P["FPC"]["pan"]; z0, z1 = Q["z"]
    strip = prism_z(strip_poly(loop_centreline(pan)), z0, z1)
    tl = Q["tail"]
    tail = tube_sector(Q["r_out"] + FT / 2, Q["r_out"] - FT / 2, *tl["az"], tl["z_bot"], z0 + 0.1)
    return one(fuse([strip, _riser(pan), tail]))


def loop_lengths(pan=0.0):
    """(inner run on the drum, outer run on the wall) in mm, free part only, and the U-turn azimuth"""
    Q = P["FPC"]["pan"]; u = Q["u0"] + Q["k"] * pan
    a_b = P["FPC"]["trunk"]["az"] + pan + math.degrees(math.atan2(P["FPC"]["w"] / 2, Q["r_in"])) + 4.0
    return math.radians(u - a_b) * Q["r_in"], math.radians(u - C.RAM["FPC_ANCHOR"]["slot_az"][1]) * Q["r_out"], u


def mk_fpc():
    """complete FPC in the rest pose (lift 0, pan 0) as ONE solid"""
    return one(fuse([fpc_lift(0.0), fpc_stage(), fpc_loop(0.0)]))


def mk_spoj():
    """micro junction of the lift servo lead: FR4 stiffener 5.4 x 5.8 x 0.6 on the FPC branch, 1 x 3 pin header 1.27 mm
    (pins 0.4 sq.) and the mating 1 x 3 socket crimped on the shortened servo lead"""
    J = P["JUNCTION"]; b, s = J["board"], J["socket"]
    S = [C.box(*b["x"], *b["y"], *b["z"])]
    S += [C.box(x - 0.2, x + 0.2, J["pin_y"][0] - 0.1, J["pin_y"][1], J["pin_z"] - 0.2, J["pin_z"] + 0.2) for x in J["pins_x"]]
    S.append(C.box(*s["x"], *s["y"], *s["z"]))
    return one(fuse(S))


def mk_kabel():
    """lift servo lead 3 x AWG30 (bundle D1.8), 60 mm: servo top end -> down beside the bottom cover -> junction socket"""
    s = P["JUNCTION"]["socket"]; xb = C.LIFT_X[1]; zt = C.LIFT_CASE["z"][1]
    pts = [(xb - 0.3, YL, zt + 2.6), (xb + 1.4, YL, zt + 2.6), (xb + 1.4, YL, s["z"][0] + 3.6), ((s["x"][0] + s["x"][1]) / 2, 21.5, J_Z),
           ((s["x"][0] + s["x"][1]) / 2, s["y"][1] - 0.3, J_Z)]
    r = 0.9; S = []
    for a, b in zip(pts[:-1], pts[1:]):
        v = Vector(*b) - Vector(*a)
        cyl = bd.Cylinder(r, v.length, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))
        S.append(bd.Location(bd.Plane(origin=a, z_dir=(v.X, v.Y, v.Z))) * cyl)
    S += [bd.Pos(*p) * bd.Sphere(r) for p in pts[1:-1]]
    return one(fuse(S))


J_Z = P["JUNCTION"]["pin_z"]


# =====================================================================================================================
# small bought parts
# =====================================================================================================================
def ptfe_parts():
    """PTFE tape 0.13: band 5 x 177 on the journal + one strip on each of the 8 guide lands"""
    J = P["JOURNAL"]; L = P["LAND"]; t = L["tape"]; out = {}
    out["ptfe_pas_capu"] = one(C.cyl_z(J["r_resin"] + J["tape"]["t"], *J["tape"]["z"]) - C.cyl_z(J["r_resin"], J["tape"]["z"][0] - 1, J["tape"]["z"][1] + 1))
    yl, xl = YI - L["h"], XI - L["h"]; z0, z1 = L["z"][0] + 1.0, L["z"][1] - 2.0
    i = 1
    for a, b in L["front_x"]:
        out[f"ptfe_pasik_{i}"] = C.box(a + 0.5, b - 0.5, -yl, -yl + t, z0, z1); i += 1
    for a, b in L["back_x"]:
        out[f"ptfe_pasik_{i}"] = C.box(a + 0.5, b - 0.5, yl - t, yl, z0, z1); i += 1
    a, b = L["back_up"]["x"]
    out[f"ptfe_pasik_{i}"] = C.box(a + 0.5, b - 0.5, yl - t, yl, L["back_up"]["z"][0] + 0.2, z1); i += 1
    for s in (1, -1):
        for a, b in L["end_y"]:
            xa, xb = sorted((s * xl, s * (xl - t)))
            out[f"ptfe_pasik_{i}"] = C.box(xa, xb, a + 0.25, b - 0.25, z0, z1); i += 1
    return out


def fasteners(lift=0.0):
    """dict name -> (solid, group, material, label, record) of every screw / insert / dowel of the PAN module"""
    F = {}

    def add(name, solid, grp, mat, label, **rec):
        F[name] = (solid, grp, mat, label, rec)
    G = P["GEAR"]
    for i, (r, az) in enumerate(C.GEAR_JOINT["dowels"], 1):
        x, y = pol(r, az)
        add(f"kolik_kolesa_{i}", C.cyl_z(C.GEAR_JOINT["d"] / 2, *G["dowel_z"], x, y), "P", "steel", "kolík Ø2 x 4 (koleso pan – šachta)",
            joint="F9", size="dowel D2 x 4 ISO 2338", at=(round(x, 3), round(y, 3), G["dowel_z"][1]), dir="-Z", bench=True)
    sp = G["stop_pin"]; x, y = pol(sp["r"], sp["az"])
    add("kolik_dorazu", C.cyl_z(sp["d"] / 2, *sp["z"], x, y), "P", "steel", "kolík dorazu pan Ø2 x 4,5", joint="stop",
        size="dowel D2 x 4.5 (cut from x5)", at=(round(x, 3), round(y, 3), sp["z"][0]), dir="+Z", bench=True)
    Pd = P["PAD"]; py1 = P["BRKT"]["plate_y"][1]
    for i, b in enumerate(P["PADS"], 1):
        add(f"skr_F10_{i}", C.screw("M2", 4, (b["x"], py1, b["z"]), "y", -1), "P", "steel", "skrutka M2x4 s valcovou hlavou (držiak serva)",
            joint="F10", size="M2x4 ISO 4762", head=(b["x"], py1, b["z"]), dir="-Y", tool_from="+Y (door)")
        add(f"vl_F10_{i}", C.insert("M2", (b["x"], Pd["face_y"], b["z"]), "y", -1), "P", "brass", "závitová vložka M2x3 (šachta)",
            joint="F10", at=(b["x"], Pd["face_y"], b["z"]))
    T = C.MG90S["tab"]; xb = C.LIFT_X[1]; zt = C.LIFT_CASE["z"][1]; xh = xb - T["from_bottom"][1]
    add("skr_F11", screw_cyl(2.0, 3.8, 1.6, 6, (xh, YL, zt + T["hole"]), "x", 1), "P", "steel", "skrutka M2x6 do plastu (úchyt serva zdvihu)",
        joint="F11", size="M2x6 thread-forming pan head", head=(xh, YL, zt + T["hole"]), dir="+X", tool_from="-X (bench / door at pan -85)")
    K = C.CRANK
    add("skr_kluky", C.screw("M2.5c", 6, (K["hub_x"][0], YL, ZL), "x", 1), "P", "steel", "skrutka M2,5x6 zápustná (kľuka)",
        joint="crank", size="M2.5x6 countersunk ISO 10642", head=(K["hub_x"][0], YL, ZL), dir="+X", tool_from="-X (bench / door at pan -85)")
    E = P["EAR"]; zs = ZS0 + lift
    add("skr_F12", bd.Pos(0, 0, lift) * screw_cyl(2.0, 3.8, 1.6, 8, (E["screw"]["x"], E["flange_y"][1], ZS0 + E["screw"]["zrel"]), "y", -1),
        "L", "steel", "skrutka M2x8 do plastu (ucho – pätka)", joint="F12", size="M2x8 thread-forming pan head",
        head=(E["screw"]["x"], E["flange_y"][1], ZS0 + E["screw"]["zrel"]), dir="-Y", tool_from="+Y (door, lift 0, pan 0)")
    d = E["dowel"]
    add("kolik_ucha", C.cyl_y(d["d"] / 2, E["flange_y"][0] - 3.0, E["flange_y"][0] + 2.0, d["x"], zs + d["zrel"]), "L", "steel",
        "kolík Ø1,5 x 5 (poloha ucha)", joint="F12", size="dowel D1.5 x 5 ISO 2338", at=(d["x"], E["flange_y"][0], ZS0 + d["zrel"]), dir="-Y")
    Tn = P["TONGUE"]; tp = P["FOOT"]["tongue_pilot"]
    s = bd.Pos(0, 0, 0.4) * bd.Cone(1.5, 0.8, 0.8) + bd.Pos(0, 0, 5.0) * bd.Cylinder(0.8, 10.0)
    add("skr_jazyka", one(bd.Pos(Tn["x"][1], tp["y"], tp["z"] + lift) * C._along(s, "x", -1)), "L", "steel", "skrutka M1,6x10 zápustná (jazýček – pätka)",
        joint="tongue", size="M1.6x10 countersunk DIN 965, self-tapping in the D1.3 pilot", head=(Tn["x"][1], tp["y"], tp["z"]), dir="-X",
        tool_from="+X (bench / door at pan +90)")
    return F


# =====================================================================================================================
# registry
# =====================================================================================================================
PRINTED = {   # name: (builder, group, material, Slovak label)
    "P_sachta": (mk_sachta, "P", "resin_black", "šachta krku s otočným čapom Ø56,4 a stolom goliera"),
    "P_koleso": (mk_koleso, "P", "resin_black", "ozubené koleso pan m0,8 z36 (sektor) s bubnom FPC"),
    "P_drziak_serva": (mk_drziak, "P", "petg", "držiak serva zdvihu"),
    "P_kluka": (mk_kluka, "P", "resin_black", "kľuka zdvihu r 10"),
    "L_pata": (mk_pata, "L", "petg", "pätka krku (lepená na prednú polovicu krku)"),
    "L_jazyk": (mk_jazyk, "L", "petg", "jazýček pätky – unášač pohyblivej vetvy FPC"),
    "L_ucho": (mk_ucho, "L", "pom", "ucho pätky s drážkou 2,2 x 12,2"),
}


def _src_hash():
    src = open(os.path.abspath(__file__)).read() + json.dumps(P, sort_keys=True, default=str)
    src += open(os.path.join(HERE, "t4_common.py")).read().split("# >>> additions by")[0]
    return hashlib.md5(src.encode()).hexdigest()[:10]


def cached_part(name, fn, rebuild=False):
    h = _src_hash()
    p = os.path.join(C.CACHE, f"pan_{name}_{h}.brep")
    if os.path.exists(p) and not rebuild:
        TIMES[name] = 0.0
        return one(bd.import_brep(p))
    t = time.time(); s = fn(); TIMES[name] = round(time.time() - t, 1)
    for old in os.listdir(C.CACHE):
        if old.startswith(f"pan_{name}_") and old.endswith(".brep"):
            os.remove(os.path.join(C.CACHE, old))
    bd.export_brep(s, p)
    return s


def build(rebuild=False, verbose=False):
    """registry of the PAN module: dict[name] = t4_common.part(...) - everything in the rest pose (lift 0, pan 0)"""
    parts = {}
    for name, (fn, grp, mat, label) in PRINTED.items():
        s = cached_part(name, fn, rebuild)
        parts[name] = C.part(s, grp, mat, True, label)
        if verbose:
            print(f"  built {name} ({TIMES.get(name, 0)} s)", flush=True)
    B = [  # name, builder, group, material, mass g (None = volume x density), label
        ("servo_zdvih", mk_servo, "P", "bought", 13.4, "servo zdvihu MG90S (spodný úchyt odrezaný)"),
        ("cap_kluky", mk_cap_kluky, "P", "steel", None, "čap kľuky Ø2 m6 x 5,4 (oceľ)"),
        ("fpc_pan", mk_fpc, "P", "fpc", None, "FPC pan + zdvih 3,0 x 0,12 (zákazkový, 8 vodičov)"),
        ("spoj_zdvih", mk_spoj, "P", "bought", 0.25, "mikrospoj 1x3 (1,27 mm) vodičov serva zdvihu na FPC"),
        ("kabel_zdvih", mk_kabel, "P", "bought", 0.4, "vodiče serva zdvihu 3x AWG30, 60 mm"),
    ]
    for name, fn, grp, mat, mass, label in B:
        t = time.time(); s = cached_part(name, fn, rebuild) if name == "fpc_pan" else fn()
        TIMES[name] = TIMES.get(name) if name == "fpc_pan" else round(time.time() - t, 2)
        extra = dict(mass=mass) if mass is not None else {}
        parts[name] = C.part(s, grp, mat, False, label, **extra)
    for name, s in ptfe_parts().items():
        parts[name] = C.part(s, "P", "ptfe", False, "PTFE páska 0,13 (klzná plocha)")
    for name, (s, grp, mat, label, rec) in fasteners().items():
        parts[name] = C.part(s, grp, mat, False, label, fastener=rec)
    return parts


def pose_parts(lift=0.0):
    """solids of everything that moves with the lift, at `lift` (stage frame): for the kinematic / sweep checks"""
    th = crank_angle(lift)
    mv = bd.Pos(0, 0, lift)
    out = {"P_kluka": mk_kluka(th), "cap_kluky": mk_cap_kluky(th), "L_pata": mv * mk_pata(), "L_jazyk": mv * mk_jazyk(),
           "L_ucho": mv * mk_ucho()}
    F = fasteners(lift)
    for n in ("skr_F12", "kolik_ucha", "skr_jazyka"):
        out[n] = F[n][0]
    K = C.CRANK
    out["skr_kluky"] = F["skr_kluky"][0]
    return out


def _koleso_bbox():
    """bbox of the gear from its 2-D outline (21 teeth do not reach -X / -Y exactly, the lip only spans 22 .. 145 deg)"""
    G = P["GEAR"]; Lp = G["lip"]
    A = np.array(gear_outline() + [pol(Lp["r"], a) for a in np.arange(Lp["az"][0], Lp["az"][1] + 1e-6, 0.5)])
    return (A[:, 0].min(), A[:, 0].max(), A[:, 1].min(), A[:, 1].max(), C.Z_GEAR_PAN[0], max(C.Z_GEAR_PAN[1], Lp["z"][1]))


# expected bounding boxes (x0, x1, y0, y1, z0, z1) of the printed parts - checked in main
def expected_bbox():
    J = P["JOURNAL"]; Fn = P["FIN"]; B = P["BRKT"]; E = C.EAR; T = P["TONGUE"]; K = C.CRANK
    rj = J["r_resin"]
    return {
        "P_sachta": (-rj, rj, -rj, rj, C.Z_WELL_FLOOR[0], C.Z_COLLAR[0]),
        "P_koleso": _koleso_bbox(),
        "P_drziak_serva": (B["ledge"]["x"][0], B["lug"]["x"][1], B["rest"]["y"], B["ledge"]["lip_y"][1], B["plate_z"][0], B["tab2"]["z_top"]),
        "P_kluka": (K["hub_x"][0], K["hub_x"][1], YL - K["hub_r"], YL + K["hub_r"], ZL - RC - K["tip_r"], ZL + K["hub_r"]),
        "L_pata": (-22.3, 22.3, -9.8, 9.8, C.Z_FOOT[0], C.Z_FOOT[1]),
        "L_jazyk": (P["FOOT"]["key"]["x"][0], T["x"][1], T["y"][0], T["y"][1], T["z"][0], T["block"]["z_top"]),
        "L_ucho": (E["x"][0], E["flange"]["x"][1], P["EAR"]["flange_y"][0], E["y"][1], ZS0 + E["zrel"][0], ZS0 + E["zrel"][1]),
    }


SOURCES = {
    "servo_zdvih": "MG90S, E2 model of the neck (user drawing ref_MG90S + electronics_dims.md): case 22.5 x 12.2 x 22.8, shaft 5.9 from the end, "
                   "turret D11.8 x 6.0 + lobe r 2.9 at 5.6, spline 21T D4.8 x 3.0, tab 2.5 thick 16.0..18.5 above the bottom, hole D2.2 at 2.45; "
                   "+-0.3 (tab height +-1: the bracket is slotted +-1.0 in X).  Lead block 4.5 x 5 x 5 = reserved exit / first bend.",
    "cap_kluky": "dowel pin ISO 2338 D2 m6 x 5.4 (cut from x6), pressed 2.5 into the crank arm (hole D1.98)",
    "fpc_pan": "custom 2-layer polyimide FPC 3.0 x 0.12, 8 traces (pack par. 2); developed outline with 3 creased folds (tongue edge, fin edge, "
               "riser on the drum) and 2 T-branches (junction, static tail); bend radii: lift loop R 4.0 (33 x t), pan U-turn R 3.84 (32 x t)",
    "spoj_zdvih": "FR4 stiffener 5.4 x 5.8 x 0.6 bonded on the FPC branch + 1x3 pin header 1.27 mm (pin 0.4 sq., 3.0 long) + 1x3 socket 1.27 mm "
                  "(3.95 x 4.3 x 2.2) on the servo lead",
    "kabel_zdvih": "3 x AWG30 silicone (D0.8 each), bundle D1.8, about 60 mm; modelled as a tube along the planned route",
    "ptfe_pas_capu": "PTFE tape 0.13 x 5 x 177 around the journal (z -10 .. -5)",
}
for _i in range(1, 9):
    SOURCES[f"ptfe_pasik_{_i}"] = "PTFE tape 0.13: 3.0 (2.5 / 3.0) x 30 on the guide land (5 x 3 on the short land above the ear window)"
ASSEMBLY = {   # (bench step, direction / note) - order inside the module, see parts_pan.json["assembly"]
    "P_koleso": ("A1", "bonded (epoxy) + 2 dowels to the hub disc of P_sachta, stop pin pressed from below"),
    "P_sachta": ("A1", "vl_F10 inserts glued, PTFE tapes on the lands and the journal"),
    "L_pata": ("A2", "bonded to the FRONT neck half (wires through the slot), optional 2 x M2 from below"),
    "fpc_pan": ("A3", "7 neck wires soldered to the paddle (FPC loose), paddle into the foot pocket"),
    "L_jazyk": ("A5", "-X through the end window after the neck is in the well, M1.6x10"),
    "servo_zdvih": ("B1", "+X into the bracket, F11"), "P_kluka": ("B1", "+X onto the spline at servo zero, skr_kluky"),
    "P_drziak_serva": ("C2", "-Y through the door onto the pads, 2 x F10 (M2x4), set the crank / ear side gap 0.4 in the slots"),
    "L_ucho": ("C3", "+X onto the crank pin, then -Y onto the dowel, F12 through the door"),
}
DEVIATIONS = []          # filled from STATUS text in main (kept in parts_pan.json)
STEP_MAX = 12_000_000


def export_step_limited(name, shape):
    path = os.path.join(HERE, "step", name + ".step")
    bd.export_step(shape, path)
    n = os.path.getsize(path)
    if n > STEP_MAX:
        os.remove(path)
        return None, n, f"deleted: {n / 1e6:.1f} MB > {STEP_MAX / 1e6:.0f} MB"
    return f"step/{name}.step", n, ""


def export_stl_abs(shape, path, lin=0.01, ang=0.1):
    """STL with ABSOLUTE deflection (same convention as t4_obal.export_abs)"""
    from OCP.BRepMesh import BRepMesh_IncrementalMesh
    from OCP.StlAPI import StlAPI_Writer
    from OCP.BRepTools import BRepTools
    BRepTools.Clean_s(shape.wrapped)
    BRepMesh_IncrementalMesh(shape.wrapped, lin, False, ang, True)
    w = StlAPI_Writer(); w.ASCIIMode = False
    w.Write(shape.wrapped, path)


def read_stl(path):
    import struct
    with open(path, "rb") as f:
        f.read(80); n = struct.unpack("<I", f.read(4))[0]
        d = np.frombuffer(f.read(n * 50), dtype=np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")]))
    return d["v"].astype(float)


def mesh_stats(T):
    """volume, centre of gravity and edge statistics of a triangle soup (n, 3, 3) after welding the vertices"""
    V, inv = np.unique(np.round(T.reshape(-1, 3), 5), axis=0, return_inverse=True)
    Fi = inv.reshape(-1, 3)
    Fi = Fi[(Fi[:, 0] != Fi[:, 1]) & (Fi[:, 1] != Fi[:, 2]) & (Fi[:, 0] != Fi[:, 2])]
    a, b, c = V[Fi[:, 0]], V[Fi[:, 1]], V[Fi[:, 2]]
    v6 = np.einsum("ij,ij->i", a, np.cross(b, c))
    vol = v6.sum() / 6.0
    cog = ((a + b + c) * v6[:, None]).sum(0) / (24.0 * vol) if abs(vol) > 1e-9 else np.zeros(3)
    E = np.concatenate([Fi[:, [0, 1]], Fi[:, [1, 2]], Fi[:, [2, 0]]])
    key = np.sort(E, axis=1); key = key[:, 0].astype(np.int64) * (len(V) + 1) + key[:, 1]
    _, cnt = np.unique(key, return_counts=True)
    dkey = E[:, 0].astype(np.int64) * (len(V) + 1) + E[:, 1]
    _, dcnt = np.unique(dkey, return_counts=True)
    return dict(tris=int(len(Fi)), volume=float(vol), cog=[round(float(x), 3) for x in cog], open_edges=int((cnt == 1).sum()),
                nonmanifold_edges=int((cnt > 2).sum()), flipped_edges=int((dcnt > 1).sum()))


def main(argv):
    rebuild = "--rebuild" in argv
    T0 = time.time()
    print("== t4_pan: build ==", flush=True)
    parts = build(rebuild, verbose=True)
    print(f"build {time.time() - T0:.1f} s, {len(parts)} parts", flush=True)
    exp = expected_bbox()
    recs, bad = [], []
    print(f"{'part':18s} {'grp':3s} {'mat':11s} valid sol {'volume':>9s}  bbox x / y / z{'':36s} build s")
    for name, p in parts.items():
        r = C.check_part(name, p)
        if name in exp:
            r["bbox_expected"] = [round(v, 3) for v in exp[name]]
            r["bbox_ok"] = all(abs(u - v) <= 0.06 for u, v in zip(r["bbox"], exp[name]))
            r["ok"] = r["ok"] and r["bbox_ok"]
        r["build_s"] = TIMES.get(name, 0.0) or 0.0
        b = r["bbox"]
        print(f"{name:18s} {p['group']:3s} {p['mat']:11s} {str(r['valid'])[0]}     {r['n_solids']}  {r['volume']:9.2f}  "
              f"{b[0]:7.2f}..{b[1]:7.2f} / {b[2]:7.2f}..{b[3]:7.2f} / {b[4]:7.2f}..{b[5]:7.2f}  {r['build_s']:5.1f}"
              + ("" if r["ok"] else "   <-- NOT OK" + (f" (bbox expected {r.get('bbox_expected')})" if not r.get("bbox_ok", True) else "")), flush=True)
        if not r["ok"]:
            bad.append(name)
        recs.append((name, p, r))
    if "--noexport" in argv:
        print("not exported; NOT OK:", bad)
        return 1 if bad else 0
    t = time.time()
    pj = os.path.join(HERE, "parts_pan.json")
    old_names = [e["name"] for e in json.load(open(pj))["parts"]] if os.path.exists(pj) else []
    os.makedirs(os.path.join(HERE, "stl"), exist_ok=True); os.makedirs(os.path.join(HERE, "step"), exist_ok=True)
    out, n_step = [], 0
    import t4_obal as O                               # export_abs: STL with ABSOLUTE deflection 0.01, STEP only below 12 MB
    for name, p, r in recs:
        e = O.export_abs(name, p)                     # valid / n_solids / volume / bbox / volume_mesh / cog / stl{} / watertight / step
        for k in ("bbox_expected", "bbox_ok", "build_s"):
            if k in r:
                e[k] = r[k]
        n_step += e["step"] is not None
        e["ok"] = bool(r["ok"] and e["watertight"])
        if not e["ok"] and name not in bad:
            bad.append(name)
        if "fastener" in p:
            e["fastener"] = p["fastener"]
        if name in SOURCES:
            e["source"] = SOURCES[name]
        if name in ASSEMBLY:
            e["assembly_step"], e["assembly_dir"] = ASSEMBLY[name]
        out.append(e)
    stale = [n for n in old_names if n not in parts]
    for n in stale:
        for sub, ext in (("stl", ".stl"), ("step", ".step")):
            f = os.path.join(HERE, sub, n + ext)
            if os.path.exists(f):
                os.remove(f)
    extra = {}
    fx = os.path.join(HERE, "pan_work", "parts_pan_extra.json")
    if os.path.exists(fx):
        extra = json.load(open(fx))
    doc = dict(module="pan", generated=time.strftime("%Y-%m-%d %H:%M:%S"), frame="B frame = pan-stage frame at pan 0, mm, rest pose (lift 0)",
               n_parts=len(out), all_ok=not bad, not_ok=bad, step_limit_bytes=STEP_MAX, removed_parts=stale,
               finished_parts_used=["golier_kotuc (P, glued on the stage top z -2)", "krk_predna_polovica / krk_zadna_polovica (L)"],
               parts=out, additions=json.loads(json.dumps(P, default=str)))
    doc.update(extra)
    json.dump(doc, open(pj, "w"), indent=1, ensure_ascii=False)
    mass = {}
    for e in out:
        if e.get("mass_g") is not None:
            mass[e["group"]] = mass.get(e["group"], 0.0) + e["mass_g"]
    print(f"exported {len(out)} STL + {n_step} STEP (no STEP: {[e['name'] for e in out if e['step'] is None]}) in {time.time() - t:.1f} s "
          f"-> parts_pan.json; removed stale exports {stale}; mass by group (g): " + ", ".join(f"{g} {m:.2f}" for g, m in mass.items()))
    print("NOT OK:", bad if bad else "none", f"| total {time.time() - T0:.1f} s")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
