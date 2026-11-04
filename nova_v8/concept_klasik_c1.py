"""(ARCHIVED concept model – the engineering modules use nova_v8/klasik.py)

NOVA mini – concept c1_r01  "R01, ale lepšie"
Quick concept model (solid bodies, no shells) of torso, base, neck and arms around the reused head A
(build_v8/manifest/head.json, moved up by HEAD_DZ in the render job).

Run:  cd /home/user/Robot && /opt/venv/cad/bin/python /tmp/claude-0/concepts/c1_r01/cad_c1_r01.py
Coordinates: mm, Z up, origin on the desk at the base centre, front = -Y, robot right = -X.
"""
from __future__ import annotations

import math
import os
import sys
import time

sys.path.insert(0, "/home/user/Robot")
from build123d import Axis, Box, Cylinder, Edge, Plane, Pos, Rot, Solid, Vector, Wire, fillet  # noqa: E402

from nova.cad.common import PartRec, export_parts, superellipse_pts  # noqa: E402

OUT = "/tmp/claude-0/concepts/c1_r01/build"

# ---------------------------------------------------------------- key numbers
# base slab (white) + recessed black foot with 360° underglow
BA, BB, BN = 67.0, 54.5, 3.6          # plan half sizes at the top edge, squircle exponent
BZ0, BZ1 = 8.0, 33.5                  # white slab bottom / top
B_RTOP_H, B_RTOP_V = 5.5, 4.5         # elliptical top edge round (horizontal, vertical)
B_RBOT, B_TAPER = 1.6, 1.6            # bottom edge round, draft inset at the bottom
FOOT_A, FOOT_B, FOOT_Z0 = 59.0, 46.5, 1.0
# torso
GAP = 1.5                             # shadow gap torso / base top
TZ0 = BZ1 + GAP                       # 35.0
TH = 82.0
TZ1 = TZ0 + TH                        # 114.0
TA, TB, TN = 41.5, 34.5, 3.4          # 82 x 69, squircle
T_RBOT = 7.0
T_RV = 22.0                           # vertical size of the shoulder dome
T_RTOP = 21.0                         # flat circular top under the neck collar
T_TAPER_A, T_TAPER_B = 2.6, 1.4       # top narrower than bottom
SEAM_Y = -28.0                          # one parting line in the plane y = SEAM_Y (through shoulders + collar)
# shoulders / arms
SH_Y, SH_Z = 1.0, TZ1 - 24.0          # shoulder axis (X) position
HUB_R = 12.8
ARM_SPLAY = 7.0                       # deg, bottom outward
# chest light
CHEST_Z, CHEST_W, CHEST_H = TZ1 - 35.0, 30.0, 3.6
# neck + head
COLLAR_R, COLLAR_Z1 = 22.0, TZ1 + 2.6
HEAD_Z0 = COLLAR_Z1 + 15.5            # head bottom
HEAD_DZ = HEAD_Z0 - 117.0             # move of head A (v8.1 z 117..191)


# ---------------------------------------------------------------- helpers
def se_wire(a, b, n, z, count=96, cx=0.0, cy=0.0, roll=0.25):
    raw = superellipse_pts(a, b, n, count)
    k = int(round(roll * count)) % count          # spline seam at the BACK centre (+Y), away from all cuts
    raw = raw[k:] + raw[:k]
    pts = [Vector(cx + x, cy + y, z) for x, y in raw]
    return Wire([Edge.make_spline(pts, periodic=True)])


def loft(secs, count=96):
    return Solid.make_loft([se_wire(*s, count=count) for s in secs])


def chk(name, s):
    bb = s.bounding_box()
    print(f"  {name:8s} valid={s.is_valid} vol={s.volume:9.0f}  x[{bb.min.X:6.1f},{bb.max.X:6.1f}] "
          f"y[{bb.min.Y:6.1f},{bb.max.Y:6.1f}] z[{bb.min.Z:6.1f},{bb.max.Z:6.1f}]")
    return s


# ---------------------------------------------------------------- base
def base_secs(inset=0.0):
    zb = BZ0 + B_RBOT
    zt = BZ1 - B_RTOP_V
    out = []
    for i in range(7):                                   # bottom round (even angle steps)
        th = math.pi / 2 * i / 6
        z = BZ0 + B_RBOT * (1 - math.cos(th))
        s = B_TAPER + B_RBOT * (1 - math.sin(th))
        out.append((z, s))
    k = max(2, math.ceil((zt - zb) / 3.5))
    for i in range(1, k + 1):                            # straight drafted side
        t = i / k
        out.append((zb + t * (zt - zb), B_TAPER * (1 - t)))
    for i in range(1, 13):                               # elliptical top round
        u = math.sin(math.pi / 2 * i / 12)
        g = 1 - math.sqrt(max(0.0, 1 - u * u))
        out.append((zt + B_RTOP_V * u, B_RTOP_H * g))
    return [(BA - s - inset, BB - s - inset, BN, z) for z, s in out]


def build_base():
    slab = loft(base_secs())
    # recessed black foot (rounded squircle plate) + underglow light ring
    foot = loft([(FOOT_A - 1.2 + 1.2 * math.sin(math.pi / 2 * i / 4), FOOT_B - 1.2 + 1.2 * math.sin(math.pi / 2 * i / 4),
                  BN, FOOT_Z0 + 1.2 * (1 - math.cos(math.pi / 2 * i / 4))) for i in range(5)]
                 + [(FOOT_A, FOOT_B, BN, BZ0 + 0.6)])
    ring_o = loft([(FOOT_A + 1.2, FOOT_B + 1.2, BN, 3.4), (FOOT_A + 1.2, FOOT_B + 1.2, BN, 6.2)])
    ring = ring_o - loft([(FOOT_A - 0.6, FOOT_B - 0.6, BN, 3.3), (FOOT_A - 0.6, FOOT_B - 0.6, BN, 6.3)])
    foot = foot - ring_o
    # wheel wells + wheels Ø30 (completely inside the foot outline) + 2 ball casters
    wheels, wells = [], []
    for sx in (-1, 1):
        w = Pos(sx * 44.0, 0, 15.0) * Rot(0, 90, 0) * Cylinder(15.0, 9.0)
        wells.append(Pos(sx * 44.0, 0, 0) * Box(11.5, 33.0, 6.0))
        wheels.append(w)
    for wl in wells:
        foot = foot - wl
    casters = [Pos(0, sy * 40.0, 5.0) * Solid.make_sphere(5.0) for sy in (-1, 1)]
    return slab, foot, ring, wheels, casters


# ---------------------------------------------------------------- torso
def torso_secs(inset=0.0):
    zb0, zd = TZ0 + T_RBOT, TZ1 - T_RV
    out = []
    for i in range(10):                                  # bottom round (even angle steps)
        th = math.pi / 2 * i / 9
        z = TZ0 + T_RBOT * (1 - math.cos(th))
        s = T_RBOT * (1 - math.sin(th))
        out.append((TA - s, TB - s, TN, z))
    k = max(2, math.ceil((zd - zb0) / 3.5))
    for i in range(1, k + 1):                            # body with a subtle taper (top narrower)
        t = i / k
        out.append((TA - T_TAPER_A * t * t, TB - T_TAPER_B * t * t, TN, zb0 + t * (zd - zb0)))
    ad, bd = TA - T_TAPER_A, TB - T_TAPER_B
    for i in range(1, 15):                               # shoulder dome -> flat circle under the collar
        u = math.sin(math.pi / 2 * i / 14)
        g = 1 - math.sqrt(max(0.0, 1 - u * u))
        a = ad - (ad - T_RTOP) * g
        b = bd - (bd - T_RTOP) * g
        n = TN - (TN - 2.0) * g ** 0.8
        out.append((a, b, n, zd + T_RV * u))
    if inset:
        zc = (TZ0 + TZ1) / 2
        f = (TH - 2 * inset) / TH
        out = [(a - inset, b - inset, n, zc + (z - zc) * f) for a, b, n, z in out]
    return out


def torso_half(z):
    secs = torso_secs()
    for s0, s1 in zip(secs, secs[1:]):
        if s0[3] <= z <= s1[3]:
            t = (z - s0[3]) / (s1[3] - s0[3])
            return s0[0] + t * (s1[0] - s0[0]), s0[1] + t * (s1[1] - s0[1])
    return secs[-1][0], secs[-1][1]


def pill(w, h, depth, y0):
    """Pill (stadium) prism along Y, centred x=0, from y0 to y0+depth (z centred at 0)."""
    r = h / 2
    body = Pos(0, y0 + depth / 2, 0) * Box(w - h, depth, h)
    c1 = Pos(-(w - h) / 2, y0 + depth / 2, 0) * Rot(90, 0, 0) * Cylinder(r, depth)
    c2 = Pos((w - h) / 2, y0 + depth / 2, 0) * Rot(90, 0, 0) * Cylinder(r, depth)
    return body + c1 + c2


def build_torso():
    t = loft(torso_secs())
    chk("torso0", t)
    # single parting line: 0.6 x 0.8 mm groove in the plane y = SEAM_Y
    inner = loft(torso_secs(0.8))
    band = t - inner
    t = t - (Pos(0, SEAM_Y, (TZ0 + TZ1) / 2) * Box(200, 0.6, 200) & band)
    # shoulder recesses (dark ring around the black hubs)
    ah, _ = torso_half(SH_Z)
    for sx in (-1, 1):
        rc = Pos(sx * (ah - 1.3 + 15.0), SH_Y, SH_Z) * Rot(0, 90, 0) * Cylinder(HUB_R + 1.6, 30.0)
        t = t - rc
    # chest light pocket
    _, bh = torso_half(CHEST_Z)
    pocket = Pos(0, 0, CHEST_Z) * pill(CHEST_W, CHEST_H, 6.0, -bh - 2.0)
    t = t - pocket
    light = Pos(0, 0, CHEST_Z) * pill(CHEST_W - 0.3, CHEST_H - 0.3, 3.0, -bh + 0.25)
    # turntable plinth (hidden, circular – the J1 interface)
    plinth = Pos(0, 0, BZ1 + 0.5 + 1.25) * Cylinder(25.0, 2.5)
    plinth = plinth + Pos(0, 0, TZ0 + 0.5) * Cylinder(25.0, 1.0)
    return t, light, plinth, ah


# ---------------------------------------------------------------- neck
def build_neck():
    collar = Pos(0, 0, TZ1 - 1.0 + (COLLAR_Z1 - TZ1 + 1.0) / 2) * Cylinder(COLLAR_R, COLLAR_Z1 - TZ1 + 1.0)
    collar = fillet(collar.edges().sort_by(Axis.Z)[-1:], 1.4)
    col_z0, col_z1 = COLLAR_Z1 - 0.5, HEAD_Z0 - 6.0
    column = Solid.make_cone(12.8, 11.6, col_z1 - col_z0, Plane.XY.offset(col_z0))
    yz = HEAD_Z0 - 4.0
    yoke = Pos(0, 0, yz) * Rot(0, 90, 0) * Cylinder(8.0, 32.0)
    yoke = fillet(yoke.edges(), 3.0)
    return collar, column, yoke


# ---------------------------------------------------------------- arms
# R01-style paddles: flat oval, white outer shell + black inner shell that shows as a crescent at the tip,
# yawed (front edge in, back edge out -> the broad face greets the viewer) and splayed (bottom outward).
ARM_L, ARM_US = 72.0, 0.77            # length, shoulder position along the length (from the bottom)
ARM_A, ARM_B, ARM_N = 6.8, 17.5, 2.6  # half thickness, half width, section exponent
ARM_YAW = 22.0
ARM_IF = 49.0                         # inner face x at the shoulder


def arm_profile(u):
    u0, p, p2 = 0.40, 2.3, 2.8
    v = u / (2 * u0) if u < u0 else 0.5 + (u - u0) / (2 * (1 - u0))
    e = max(0.0, 1 - abs(2 * v - 1) ** p) ** (1 / p)
    e2 = max(0.0, 1 - abs(2 * v - 1) ** p2) ** (1 / p2)
    b = ARM_B * e * (1 - 0.16 * u ** 1.5)
    a = ARM_A * e2 * (1 - 0.12 * u)
    return a, b


def arm_secs(inset=0.0):
    m = 36
    out = []
    for i in range(m + 1):
        u = 0.003 + 0.994 * (0.5 - 0.5 * math.cos(math.pi * i / m))   # dense near the rounded ends
        a, b = arm_profile(u)
        out.append((max(a - inset, 0.25), max(b - inset, 0.35), ARM_N, (u - ARM_US) * ARM_L))
    return out


def build_arm_left():
    """Left arm (+X) in rest pose.  Built in local coords (shoulder at origin, length along Z), then placed."""
    arm = Solid.make_loft([se_wire(a, b, n, z, count=72) for a, b, n, z in arm_secs()])
    arm_in = Solid.make_loft([se_wire(a, b, n, z, count=72) for a, b, n, z in arm_secs(0.35)])
    zt, zb = (1 - ARM_US) * ARM_L, -ARM_US * ARM_L
    p0 = (-1.55 * ARM_A, 0.0, zt)
    beta = -math.degrees(math.atan2(2.15 * ARM_A, zt - zb))
    H = Pos(-60, 0, 0) * Box(120, 200, 300)
    H = H.rotate(Axis.Y, beta)
    H = Pos(*p0) * H
    shell = arm - H
    inner = arm_in & H
    a_s, _ = arm_profile(ARM_US)
    xc = ARM_IF + a_s / math.cos(math.radians(ARM_YAW))
    out = []
    for s in (shell, inner):
        s = s.rotate(Axis.Z, -ARM_YAW).rotate(Axis.Y, -ARM_SPLAY)
        out.append(Pos(xc, SH_Y, SH_Z) * s)
    hub_x0 = torso_half(SH_Z)[0] - 1.4
    hub_x1 = ARM_IF + 3.0
    # black 'bead' joint: slice of an ellipsoid (barrel) between the torso recess and the paddle
    xm = (torso_half(SH_Z)[0] + ARM_IF) / 2
    from build123d import scale as b3d_scale
    bead = b3d_scale(Solid.make_sphere(1.0), (9.5, HUB_R + 1.2, HUB_R + 1.2))
    bead = Pos(xm, SH_Y, SH_Z) * bead
    hub = bead & (Pos((hub_x0 + hub_x1) / 2, SH_Y, SH_Z) * Box(hub_x1 - hub_x0, 40, 40))
    return out[0], out[1], hub


# ---------------------------------------------------------------- assemble
def build():
    t0 = time.time()
    P = []
    slab, foot, ring, wheels, casters = build_base()
    P += [PartRec("C1-B01", "Podstavec – biela doska", chk("slab", slab), "white", "base"),
          PartRec("C1-B02", "Podstavec – čierna päta", chk("foot", foot), "black", "base"),
          PartRec("C1-B03", "Podsvietenie 360°", chk("ring", ring), "cyan_led", "base")]
    for i, w in enumerate(wheels):
        P.append(PartRec(f"C1-B04-{'RL'[i]}", "Koleso Ø30", chk("wheel", w), "rubber", "base"))
    for i, c in enumerate(casters):
        P.append(PartRec(f"C1-B05-{i+1}", "Guľôčka", chk("caster", c), "black_gloss", "base"))
    torso, light, plinth, ah = build_torso()
    P += [PartRec("C1-T01", "Trup", chk("torso", torso), "white", "torso", "J1"),
          PartRec("C1-T02", "Svetelná linka hrude", chk("light", light), "cyan_led", "torso", "J1"),
          PartRec("C1-T03", "Otočný tanier", chk("plinth", plinth), "black", "torso", "J1")]
    collar, column, yoke = build_neck()
    P += [PartRec("C1-N01", "Golier krku", chk("collar", collar), "black", "neck", "J1"),
          PartRec("C1-N02", "Stĺpik krku", chk("column", column), "black", "neck", "J2"),
          PartRec("C1-N03", "Kĺb náklonu", chk("yoke", yoke), "black", "neck", "J2")]
    shell, tip, hub = build_arm_left()
    for side, sx in (("L", 1), ("R", -1)):
        sub, j = ("arm_L", "J5") if side == "L" else ("arm_R", "J4")
        s, tp, hb = (shell, tip, hub) if sx > 0 else (shell.mirror(Plane.YZ), tip.mirror(Plane.YZ), hub.mirror(Plane.YZ))
        P += [PartRec(f"C1-A01-{side}", "Ruka", chk("arm", s), "white", sub, j),
              PartRec(f"C1-A02-{side}", "Vnútorná škrupina ruky", chk("inner", tp), "black", sub, j),
              PartRec(f"C1-A03-{side}", "Rameno – náboj", chk("hub", hb), "black_gloss", sub, j)]
    for nm, a in (("arm", shell), ("inner", tip), ("hub", hub)):
        ov = a & torso
        print(f"  overlap torso/{nm}: {0.0 if ov is None else ov.volume:.1f} mm3")
    print(f"built in {time.time() - t0:.1f}s; HEAD_Z0={HEAD_Z0:.1f} HEAD_DZ={HEAD_DZ:.1f} top={HEAD_Z0 + 74:.1f}")
    return P


if __name__ == "__main__":
    parts = build()
    export_parts(parts, "c1_r01", step=False, out_dir=OUT)
    import json
    with open(os.path.join(OUT, "params.json"), "w") as f:
        json.dump(dict(HEAD_DZ=HEAD_DZ, HEAD_Z0=HEAD_Z0, TZ0=TZ0, TZ1=TZ1, SH_Y=SH_Y, SH_Z=SH_Z), f)
    print("exported ->", OUT)
