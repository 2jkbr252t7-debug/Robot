"""Arm proposal v1 - shared pure-numpy geometry (importable from the CAD venv AND from Blender's python; no scipy).
Frame B: mm, Z up, front -Y, robot LEFT = +X; shoulder axis || X through (y 3, z -17).
Arm placement = R1/geo/armgeo.py to_world (= T3 build_scene arm_xf with the T4 shoulder x 46.756) + outward shift DX.
Everything here is the LEFT arm at rest (swing 0); the right arm is the mirror x -> -x."""
import sys, math, json
import numpy as np
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T3")
import shape as S

DX = 12.0                       # proposal v1: outward shift of the white pebble (illustrative; 11-14 after measuring the servo)
SH_Y, ZS = 3.0, -17.0
AX = np.array([0.0, SH_Y, ZS])
X_SH_T4 = 46.756
SPLAY, SWING, U_ATT, INB = 12.0, 3.0, 0.22, 5.0
L = S.ARM_L
SEAM = 0.25                     # half seam gap (0.5 seam)
WALL = 2.0

# ---- frozen torso interface (T4 rev. 2/3, T_klb + column)
X_BOSS = 38.4                   # column boss face (part of T_spodok)
X_NECK0, X_NECK1 = 38.6, 40.6
X_BODY1 = 50.156                # body r 13.5 ends (chamfer to r 12.7 at 50.956)
X_STEP = 50.956                 # step face
X_J0, X_J1 = 51.556, 57.956     # journal D22
X_END = 58.756                  # T_klb end face
X_BORE0 = 44.0                  # bore D8.05 from the end face to x 44.0, recess D10.2 from 44.0 to 38.6

# ---- proposal v1 parts (numbers of the concept model)
SERVO = dict(L=23.2, W=12.1, H=21.5, s=5.9, boss_d=7.0, boss_h=1.0, spl_d=3.95, spl_h=3.0)
X_CASE0 = X_END + 0.3           # 59.056 servo case inner face
X_CASE1 = X_CASE0 + SERVO["H"]  # 80.556
BUSH = dict(x_fl0=42.0, x_fl1=44.0, d_fl=10.0, d=8.0, x_end=57.85, spl_depth=3.25)
SPRING = dict(od=10.0, id=5.2, t=0.4, h0=0.30, n=2, x0=40.85, x1=42.0)       # 2 in series, working height 1.15
SPACER = dict(od=9.9, id=5.4, x0=X_BOSS + 0.05, x1=40.85)                   # NOT in the written proposal - needed to fill the recess
HUB = dict(x0=51.2, x1=59.0, r_out=15.6, r_bore=11.06, ch_r0=12.6, ch_r1=14.2, ch_x1=57.2, sleeve_x0=52.0, oring_x=(52.5, 53.8), oring_r=11.85)
# bearing sleeve r 11.06..12.6 over the whole journal (x 51.56..57.96); cable chamber r 12.6..14.2 around the sleeve, open to the T_klb step face
ORING = dict(R=11.45, r=0.5, x=53.15)            # O-ring CS 1.0, ID 21.0 on the journal r 11.0 (squeeze 0.05)
POD = dict(x0=56.0, a0=-15.6, a1=20.0, b=8.2, rc=5.0)                      # outer outline of the servo pod (a along the arm, b fore-aft)
CAV = dict(a0=-6.2, a1=17.5, b=6.35, pa0=-14.3, pb=1.4)                     # pod cavity = case + 0.3, wire pocket above the case
BED = dict(b0=6.35, b1=7.95, a0=-5.9, a1=17.5, stop=(17.5, 19.1))           # servo bed plates in the inner shell


def Rmat():
    a, b = math.radians(-SPLAY), math.radians(-SWING)
    Ry = np.array([[math.cos(a), 0, math.sin(a)], [0, 1, 0], [-math.sin(a), 0, math.cos(a)]])
    Rx = np.array([[1, 0, 0], [0, math.cos(b), -math.sin(b)], [0, math.sin(b), math.cos(b)]])
    return Rx @ Ry


R = Rmat()


def prof(u):
    return S.arm_profile(u)


A_LOC = np.array([-float(prof(U_ATT)[1]) + INB, 0.0, -L * U_ATT])


def att(dx=DX):
    return np.array([X_SH_T4 + 9.0 + dx, SH_Y, ZS])


def to_world(P, dx=DX, sx=1):
    W = (np.asarray(P, float) - A_LOC) @ R.T + att(dx)
    W = np.array(W, copy=True)
    W[..., 0] *= sx
    return W


def to_local(Q, dx=DX):
    return (np.asarray(Q, float) - att(dx)) @ R + A_LOC


def dir_world(v, sx=1):
    w = R @ np.asarray(v, float)
    w = np.array(w); w[0] *= sx
    return w


# case frame: d_down = arm long axis projected on the y-z plane, d_fa = fore-aft
D_DOWN = R @ np.array([0, 0, -1.0]); D_DOWN[0] = 0; D_DOWN /= np.linalg.norm(D_DOWN)
D_FA = np.array([0, 1.0, 0]); D_FA -= D_FA.dot(D_DOWN) * D_DOWN; D_FA /= np.linalg.norm(D_FA)


def ab_to_yz(a, b):
    """(a along the arm-down direction, b fore-aft) -> (y, z) of a point in the plane x = const"""
    p = AX + np.multiply.outer(np.asarray(a, float), D_DOWN) + np.multiply.outer(np.asarray(b, float), D_FA)
    return p[..., 1], p[..., 2]


def inside_local(P, inset=0.0):
    P = np.atleast_2d(P)
    u = -P[:, 2] / L
    ok = (u > 0) & (u < 1)
    hw, ht = prof(np.clip(u, 1e-9, 1 - 1e-9))
    hw = np.maximum(hw - inset, 1e-9); ht = np.maximum(ht - inset, 1e-9)
    return ok & ((np.abs(P[:, 0]) / ht) ** 2.3 + (np.abs(P[:, 1]) / hw) ** 2.3 < 1.0)


_XS = np.linspace(40, 115, 7501)


def skins(y, z, inset=0.0, dx=DX):
    """x where the line || X through (y, z) enters / leaves the pebble (inset = analytic wall inset)"""
    Q = np.stack([_XS, np.full_like(_XS, y), np.full_like(_XS, z)], 1)
    ins = inside_local(to_local(Q, dx), inset)
    if not ins.any():
        return None, None
    i = np.where(ins)[0]
    return float(_XS[i[0]]), float(_XS[i[-1]])


def x_at_local_x(y, z, lx, dx=DX):
    """world x on the line || X through (y, z) where the local x coordinate equals lx (seam plane: lx = 0)"""
    # local_x = (Q - att) . R[:, 0] + A_LOC[0]   (linear in x)
    c = R[:, 0]
    rest = (0 - att(dx)[0]) * c[0] + (y - att(dx)[1]) * c[1] + (z - att(dx)[2]) * c[2] + A_LOC[0]
    return (lx - rest) / c[0]


def swing_matrix(deg):
    """4x4 rigid rotation about the shoulder axis; + = forward / up (tip moves to -Y)  (= armgeo.swing)"""
    a = math.radians(-deg); c, s = math.cos(a), math.sin(a)
    M = np.eye(4)
    M[1, 1], M[1, 2], M[2, 1], M[2, 2] = c, -s, s, c
    T = np.eye(4); T[:3, 3] = AX
    Ti = np.eye(4); Ti[:3, 3] = -AX
    return T @ M @ Ti


def pebble_rows(nu=150, nth=200, inset=0.0):
    rows, top, bot = S.arm_points(nu, nth, inset)
    return rows, np.array(top), np.array(bot)


def tip_plane_local():
    pt = np.array([0.0, 0.0, -L * 0.86])
    q = np.array([-0.50, -0.35, -L * 0.86 - 0.79])
    n = q - pt
    return pt, n / np.linalg.norm(n)


def magnet_spots_local():
    """4 magnet positions on the seam rim (local; y-z plane at the seam), 3.5 inside the outline (boss r 2.2 stays 0.7 inside)"""
    out = []
    for u, sgn in ((0.16, -1), (0.16, 1), (0.66, -1), (0.66, 1)):
        hw, ht = prof(u)
        out.append(np.array([0.0, sgn * (float(hw) - 3.5), -L * u]))
    return out


if __name__ == "__main__":
    print("A_LOC", A_LOC, "att", att(), "D_DOWN", D_DOWN, "D_FA", D_FA)
    for dx in (0.0, DX):
        si, so = skins(SH_Y, ZS, 0.0, dx); wi, wo = skins(SH_Y, ZS, WALL, dx)
        print(f"dx {dx}: axis skin {si:.2f}..{so:.2f}, wall inner side {wi:.2f}..{wo:.2f}, room {wo - X_END:.2f}")
    print("seam x on the axis:", x_at_local_x(SH_Y, ZS, 0.0))
    for m in magnet_spots_local():
        print("magnet local", m.round(2), "world", to_world(m).round(2))
