"""zjednodusenie - measurement helpers (numpy only, read-only on the T4 / B STL files).
Nothing in the design is changed; every script writes only into this directory."""
import os, struct, math, json, time
import numpy as np

T4 = "/tmp/claude-0/gapwf/fin/T4"
STL = T4 + "/stl"
BSTL = "/tmp/claude-0/gapwf/fin/B/stl"
OUT = T4 + "/zjednodusenie"
T0 = time.time()


def say(*a):
    print(f"[{time.time() - T0:6.1f}]", *a, flush=True)


def read_stl(name):
    p = name if name.endswith(".stl") else os.path.join(STL, name + ".stl")
    if not os.path.exists(p):
        p = os.path.join(BSTL, os.path.basename(p))
    with open(p, "rb") as f:
        f.read(80)
        n = struct.unpack("<I", f.read(4))[0]
        d = np.frombuffer(f.read(n * 50), dtype=np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")]))
    return d["v"].astype(np.float64)          # (n, 3, 3) triangles


def sample(T, h=0.3):
    """surface points: vertices + barycentric grid on every triangle with spacing ~h"""
    P = [T.reshape(-1, 3)]
    a, b, c = T[:, 0], T[:, 1], T[:, 2]
    L = np.maximum(np.linalg.norm(b - a, axis=1), np.linalg.norm(c - a, axis=1))
    L = np.maximum(L, np.linalg.norm(c - b, axis=1))
    k = np.clip(np.ceil(L / h).astype(int), 1, 60)
    for kk in np.unique(k):
        if kk <= 1:
            continue
        sel = k == kk
        A, B, C = a[sel], b[sel], c[sel]
        uv = [(i / kk, j / kk) for i in range(kk + 1) for j in range(kk + 1 - i)]
        uv = np.array(uv)
        u = uv[:, 0][None, :, None]; v = uv[:, 1][None, :, None]
        Q = A[:, None, :] + u * (B - A)[:, None, :] + v * (C - A)[:, None, :]
        P.append(Q.reshape(-1, 3))
    return np.concatenate(P)


def rotz(P, deg):
    a = math.radians(deg); c, s = math.cos(a), math.sin(a)
    R = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1.0]])
    return P @ R.T


def rprof(P, z0, z1, dz=0.5):
    """max radius about Z per z band"""
    r = np.hypot(P[:, 0], P[:, 1])
    out = []
    zz = np.arange(z0, z1 + 1e-9, dz)
    for za, zb in zip(zz[:-1], zz[1:]):
        m = (P[:, 2] >= za) & (P[:, 2] < zb)
        out.append((round(za, 2), round(zb, 2), round(float(r[m].max()), 3) if m.any() else None))
    return out


def bbox(P):
    return [round(float(v), 3) for v in (*P.min(0), *P.max(0))]


def dump(name, obj):
    p = os.path.join(OUT, name)
    with open(p, "w") as f:
        json.dump(obj, f, indent=1)
    say("wrote", p)
