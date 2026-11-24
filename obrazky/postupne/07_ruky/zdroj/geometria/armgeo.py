"""Common numeric model of the approved T3 arm pebble in frame B (left arm, +X).  Pure numpy.  Nothing is written to T3 / T4 / B."""
import sys, math, os
sys.dont_write_bytecode = True
import numpy as np
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T3")
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T4/overenie3")
import shape as S
import vlib

T4 = "/tmp/claude-0/gapwf/fin/T4"
BST = "/tmp/claude-0/gapwf/fin/B/stl"
TOP = S.TOP
SH_DROP, SH_Y = 21.0, 3.0
ZS = TOP - SH_DROP
_, a_sh, b_sh, n_sh = S.prof(S.s_of_drop(SH_DROP))
x_sh_T3 = a_sh * (1 - (abs(SH_Y) / b_sh) ** n_sh) ** (1 / n_sh)
X_SH_T4 = 46.756
Z_BOT = TOP - float(S.CP[-1, 0]); Z_BASE_TOP = Z_BOT - 1.5; Z_DESK = Z_BASE_TOP - S.BASE_H - S.FOOT_H
SPLAY, SWING, U_ATT, INB = 12.0, 3.0, 0.22, 5.0
L = S.ARM_L
AX = np.array([0.0, SH_Y, ZS])          # shoulder axis: line parallel to X through (y 3, z -17)


def prof(u, kt=1.0, kw=1.0):
    hw, ht = S.arm_profile(u)
    return hw * kw, ht * kt


def Rmat():
    a, b = math.radians(-SPLAY), math.radians(-SWING)
    Ry = np.array([[math.cos(a), 0, math.sin(a)], [0, 1, 0], [-math.sin(a), 0, math.cos(a)]])
    Rx = np.array([[1, 0, 0], [0, math.cos(b), -math.sin(b)], [0, math.sin(b), math.cos(b)]])
    return Rx @ Ry                       # world = R @ local  (row vectors: q @ Ry.T @ Rx.T)


R = Rmat()


def a_loc(kt=1.0):
    return np.array([-float(prof(U_ATT, kt)[1]) + INB, 0.0, -L * U_ATT])


def att_world(x_sh=None, dx=0.0):
    return np.array([(X_SH_T4 if x_sh is None else x_sh) + 9.0 + dx, SH_Y, ZS])


def to_world(P, kt=1.0, dx=0.0):
    """arm local -> frame B (left arm at rest, exactly arm_xf of T3 build_scene with sx = +1)"""
    return (np.asarray(P, float) - a_loc(kt)) @ R.T + att_world(dx=dx)


def to_local(Q, kt=1.0, dx=0.0):
    return (np.asarray(Q, float) - att_world(dx=dx)) @ R + a_loc(kt)


def swing(Q, deg):
    """rigid rotation about the shoulder axis; + = forward / up (tip moves to -Y)"""
    a = math.radians(-deg); c, s = math.cos(a), math.sin(a)
    Q = np.array(Q, float, copy=True)
    y, z = Q[..., 1] - SH_Y, Q[..., 2] - ZS
    Q[..., 1] = c * y - s * z + SH_Y; Q[..., 2] = s * y + c * z + ZS
    return Q


def inside_local(P, kt=1.0, kw=1.0, inset=0.0):
    """analytic point-in-pebble (local frame)"""
    P = np.atleast_2d(P)
    u = -P[:, 2] / L
    ok = (u > 0) & (u < 1)
    hw, ht = prof(np.clip(u, 1e-9, 1 - 1e-9), kt, kw)
    hw = np.maximum(hw - inset, 1e-9); ht = np.maximum(ht - inset, 1e-9)
    return ok & ((np.abs(P[:, 0]) / ht) ** 2.3 + (np.abs(P[:, 1]) / hw) ** 2.3 < 1.0)


def pebble_rows(nu=500, nth=480, kt=1.0, kw=1.0):
    us = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, nu))[1:-1]
    hw, ht = prof(us, kt, kw)
    th = np.linspace(0, 2 * np.pi, nth, endpoint=False)
    c, s = np.cos(th), np.sin(th)
    rows = np.empty((len(us), nth, 3))
    for i, (u, w, t) in enumerate(zip(us, hw, ht)):
        r = S.se_r(t, w, 2.3, th)
        rows[i, :, 0] = r * c; rows[i, :, 1] = r * s; rows[i, :, 2] = -L * u
    return rows


def pebble_tris(nu=500, nth=480, kt=1.0, kw=1.0):
    """closed triangle mesh of the pebble in the LOCAL frame (outward normals)"""
    rows = pebble_rows(nu, nth, kt, kw)
    K, N = rows.shape[:2]
    a = rows[:-1, :, :]; b = rows[1:, :, :]
    a1 = np.roll(a, -1, axis=1); b1 = np.roll(b, -1, axis=1)
    t1 = np.stack([a, b, b1], axis=2).reshape(-1, 3, 3)
    t2 = np.stack([a, b1, a1], axis=2).reshape(-1, 3, 3)
    top = np.array([0.0, 0, 0]); bot = np.array([0.0, 0, -L])
    r0 = rows[0]; rN = rows[-1]
    ct = np.stack([np.broadcast_to(top, r0.shape), r0, np.roll(r0, -1, axis=0)], axis=1)
    cb = np.stack([np.broadcast_to(bot, rN.shape), np.roll(rN, -1, axis=0), rN], axis=1)
    T = np.concatenate([t1, t2, ct, cb])
    if vlib.volume(T) < 0:
        T = T[:, ::-1, :]
    return T


def pebble_cloud(du=0.2, kt=1.0, kw=1.0):
    """dense surface point cloud (local), spacing about du"""
    rows = pebble_rows(int(1.6 * L / du), int(110 / du), kt, kw)
    return np.concatenate([rows.reshape(-1, 3), [[0, 0, 0], [0, 0, -L]]])


def load(name, d=None):
    return vlib.load_stl(os.path.join(d or (T4 + "/stl"), name + ".stl"))


# ---- signed distance to the pebble (local frame): dense analytic surface cloud + KD-tree, sign from the analytic inside test
_SDF = {}


def sdf_local(P, kt=1.0, kw=1.0, h=0.15, dmax=8.0):
    """signed distance (negative inside) of local points to the pebble surface; accuracy about 0.01 mm.
    |sd| is capped at dmax (points farther than dmax from the surface return +-dmax) - keeps the KD search fast"""
    from scipy.spatial import cKDTree
    key = (round(kt, 6), round(kw, 6), h)
    if key not in _SDF:
        rows = pebble_rows(int(2.2 * L / h), int(2 * math.pi * 17.5 / h), kt, kw)
        C = np.concatenate([rows.reshape(-1, 3), [[0, 0, 0], [0, 0, -L]]])
        if len(_SDF) > 60: _SDF.clear()
        _SDF[key] = cKDTree(C)
    d, _ = _SDF[key].query(np.atleast_2d(P), distance_upper_bound=dmax)
    d = np.minimum(d, dmax)
    ins = inside_local(P, kt, kw)
    return np.where(ins, -d, d)


def sdf_world(Q, kt=1.0, kw=1.0, dx=0.0, dmax=8.0, h=0.15):
    return sdf_local(to_local(Q, kt, dx), kt, kw, h=h, dmax=dmax)
