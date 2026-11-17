"""overenie_montaz - nezavisla kniznica (Blender python: mathutils BVH).  Nic z T4 sa nemeni, STL sa iba citaju.
Kolizia = PRIECNE pretnutie trojuholnikov (vrcholy oboch trojuholnikov su na oboch stranach roviny druheho o viac nez EPS),
takze dosadacie / klzne plochy (medzera 0) sa nehlasia ako kolizia."""
import os, struct, math, json, time
import numpy as np
import bpy  # noqa (sprístupní mathutils)
from mathutils import Vector
from mathutils.bvhtree import BVHTree

T4 = "/tmp/claude-0/gapwf/fin/T4"
STL = T4 + "/stl"
BSTL = "/tmp/claude-0/gapwf/fin/B/stl"
OUT = T4 + "/overenie_montaz"
EPS = 0.02
T0 = time.time()


def say(*a):
    print(f"[{time.time() - T0:6.1f}]", *a, flush=True)


def read_stl(path):
    with open(path, "rb") as f:
        f.read(80)
        n = struct.unpack("<I", f.read(4))[0]
        d = np.frombuffer(f.read(n * 50), dtype=np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")]))
    return d["v"].astype(np.float64)


class Mesh:
    def __init__(self, name):
        p = os.path.join(STL, name + ".stl")
        if not os.path.exists(p):
            p = os.path.join(BSTL, name + ".stl")
        T = read_stl(p)
        V, inv = np.unique(np.round(T.reshape(-1, 3), 5), axis=0, return_inverse=True)
        F = inv.reshape(-1, 3)
        F = F[(F[:, 0] != F[:, 1]) & (F[:, 1] != F[:, 2]) & (F[:, 0] != F[:, 2])]
        self.name, self.V, self.F = name, V, F


_M = {}


def mesh(n):
    if n not in _M:
        _M[n] = Mesh(n)
    return _M[n]


def rotz(V, deg):
    a = math.radians(deg); c, s = math.cos(a), math.sin(a)
    R = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1.0]])
    return V @ R.T


def rotx_about(V, deg, y0, z0):
    a = math.radians(deg); c, s = math.cos(a), math.sin(a)
    W = V.copy(); y = V[:, 1] - y0; z = V[:, 2] - z0
    W[:, 1] = y0 + y * c - z * s; W[:, 2] = z0 + y * s + z * c
    return W


PARTS = json.load(open(T4 + "/parts.json"))["parts"]
GROUP = {r["name"]: r["group"] for r in PARTS}
GROUP.update({"golier_prstenec": "T", "golier_kotuc": "P", "krk_predna_polovica": "L", "krk_zadna_polovica": "L", "kabel": "L"})
MAT = {r["name"]: r["mat"] for r in PARTS}
PRINTED = {r["name"]: r["printed"] for r in PARTS}
ALL = [r["name"] for r in PARTS]


def posed(name, pan=0.0, lift=0.0, xf=None):
    """vrcholy dielu v polohe (pan otoci skupiny P/L, lift zdvihne skupinu L), potom volitelna transformacia xf(V)"""
    V = mesh(name).V
    g = GROUP.get(name, "T")
    if lift and g == "L":
        V = V + np.array([0, 0, lift])
    if pan and g in ("P", "L"):
        V = rotz(V, pan)
    if xf is not None:
        V = xf(V)
    return V


class Group:
    """viac dielov v jednom BVH"""
    def __init__(self, names, pan=0.0, lift=0.0, xf=None):
        Vs, Fs, own, off = [], [], [], 0
        self.names = list(names)
        for i, n in enumerate(self.names):
            V = posed(n, pan, lift, xf); F = mesh(n).F
            Vs.append(V); Fs.append(F + off); own.append(np.full(len(F), i, np.int32)); off += len(V)
        self.V = np.concatenate(Vs) if Vs else np.zeros((0, 3)); self.F = np.concatenate(Fs) if Fs else np.zeros((0, 3), int)
        self.own = np.concatenate(own) if own else np.zeros(0, int)
        self.tree = BVHTree.FromPolygons(self.V.tolist(), self.F.tolist(), all_triangles=True, epsilon=0.0) if len(self.F) else None

    def moved(self, d):
        g = Group.__new__(Group)
        g.names, g.F, g.own = self.names, self.F, self.own
        g.V = self.V + np.asarray(d, float)
        g.tree = BVHTree.FromPolygons(g.V.tolist(), g.F.tolist(), all_triangles=True, epsilon=0.0)
        return g

    def xformed(self, fn):
        g = Group.__new__(Group)
        g.names, g.F, g.own = self.names, self.F, self.own
        g.V = fn(self.V)
        g.tree = BVHTree.FromPolygons(g.V.tolist(), g.F.tolist(), all_triangles=True, epsilon=0.0)
        return g


def crossings(A, B, eps=EPS):
    """priecne pretnutia medzi skupinami A, B -> {(dielA, dielB): dict(n, bod, hlbka)}; hlbka = min(presah vrcholov cez rovinu druheho)"""
    if A.tree is None or B.tree is None:
        return {}
    ov = A.tree.overlap(B.tree)
    if not ov:
        return {}
    ov = np.array(ov, int)
    ta = A.V[A.F[ov[:, 0]]]; tb = B.V[B.F[ov[:, 1]]]
    na = np.cross(ta[:, 1] - ta[:, 0], ta[:, 2] - ta[:, 0]); la = np.linalg.norm(na, axis=1); ok = la > 1e-12
    nb = np.cross(tb[:, 1] - tb[:, 0], tb[:, 2] - tb[:, 0]); lb = np.linalg.norm(nb, axis=1); ok &= lb > 1e-12
    na = na / np.maximum(la, 1e-12)[:, None]; nb = nb / np.maximum(lb, 1e-12)[:, None]
    da = np.einsum("ijk,ik->ij", ta - tb[:, :1], nb)          # vrcholy a voci rovine b
    db = np.einsum("ijk,ik->ij", tb - ta[:, :1], na)
    dep = np.minimum(np.minimum(da.max(1), -da.min(1)), np.minimum(db.max(1), -db.min(1)))
    m = ok & (dep > eps)
    out = {}
    for k in np.nonzero(m)[0]:
        key = (A.names[A.own[ov[k, 0]]], B.names[B.own[ov[k, 1]]])
        e = out.setdefault(key, dict(n=0, hlbka=0.0, bod=None))
        e["n"] += 1
        if dep[k] > e["hlbka"]:
            e["hlbka"] = float(dep[k]); e["bod"] = [round(float(q), 2) for q in ta[k].mean(0)]
    return out


def sweep(move, static, legs, step=0.5, pan=0.0, lift=0.0, pan_static=None, fits=(), t_skip=0.0, xf=None, verbose=False):
    """vytiahnutie skupiny `move` po lomenej drahe legs = [((dx,dy,dz), dlzka)], krok `step`.  Vrati zoznam kolizii
    {(pohyblivy, pevny): dict(prva_draha_mm, max_hlbka, bod, n_poloh)}.  fits = pary (prefix pohybliveho, prefix pevneho), ktore sa
    ignoruju do drahy fit_len (deklarovane lisovane / zavitove ulozenia)."""
    A0 = Group(move, pan, lift, xf)
    B = Group(static, pan if pan_static is None else pan_static, lift)
    res = {}
    off = np.zeros(3); s_tot = 0.0
    for d, L in legs:
        d = np.asarray(d, float); d = d / np.linalg.norm(d)
        n = max(1, int(round(L / step)))
        for i in range(1, n + 1):
            s = L * i / n
            A = A0.moved(off + d * s)
            cr = crossings(A, B)
            for key, e in cr.items():
                skip = False
                for fa, fb, flen in fits:
                    if key[0].startswith(fa) and key[1].startswith(fb) and s_tot + s <= flen:
                        skip = True
                if skip or s_tot + s < t_skip:
                    continue
                r = res.setdefault(key, dict(prva_draha_mm=round(s_tot + s, 2), max_hlbka=0.0, bod=None, n_poloh=0, posledna_draha_mm=0.0))
                r["n_poloh"] += 1; r["posledna_draha_mm"] = round(s_tot + s, 2)
                if e["hlbka"] > r["max_hlbka"]:
                    r["max_hlbka"] = round(e["hlbka"], 3); r["bod"] = e["bod"]; r["pri_drahe_mm"] = round(s_tot + s, 2)
            if verbose and cr:
                say("   s", round(s_tot + s, 2), {k: round(v["hlbka"], 2) for k, v in cr.items()})
        off = off + d * L; s_tot += L
    return res


def surf_samples(name, h=0.5, pan=0.0, lift=0.0, xf=None, box=None):
    """body na povrchu dielu: vrcholy + barycentricka mriezka s krokom ~h"""
    V = posed(name, pan, lift, xf); F = mesh(name).F
    a, b, c = V[F[:, 0]], V[F[:, 1]], V[F[:, 2]]
    P = [V, (a + b + c) / 3.0]
    L = np.maximum(np.linalg.norm(b - a, axis=1), np.maximum(np.linalg.norm(c - a, axis=1), np.linalg.norm(c - b, axis=1)))
    for k in (2, 4, 8, 16, 32, 64):
        m = (L > h * k / 2) & (L <= h * k) if k < 64 else (L > h * k / 2)
        if not m.any():
            continue
        n = k
        for i in range(n + 1):
            for j in range(n + 1 - i):
                u, v = i / n, j / n
                P.append(a[m] * (1 - u - v) + b[m] * u + c[m] * v)
    P = np.concatenate(P)
    if box is not None:
        m = np.all((P > np.array(box[0::2])) & (P < np.array(box[1::2])), axis=1)
        P = P[m]
    return P


def min_dist(P, G, cap=50.0):
    """najmensia vzdialenost bodov P k skupine G -> (d, bod, diel)"""
    best = (cap, None, None)
    for p in P.tolist():
        h = G.tree.find_nearest(Vector(p), best[0])
        if h[0] is not None and h[3] < best[0]:
            best = (h[3], [round(q, 2) for q in p], G.names[G.own[h[2]]])
    return best


DIRS = [Vector((0.5377, 0.3181, 0.7808)).normalized(), Vector((-0.2113, 0.8712, 0.4431)).normalized(),
        Vector((0.7312, -0.6017, 0.3217)).normalized()]


def inside(tree, p):
    v = 0
    for d in DIRS:
        cnt = 0; o = Vector(p); last = -1
        for _ in range(300):
            h = tree.ray_cast(o, d, 1e4)
            if h[0] is None:
                break
            if h[2] == last and h[3] < 1e-3:
                o = o + d * 1e-3; continue
            cnt += 1; last = h[2]; o = h[0] + d * 2e-4
        v += cnt % 2
    return v >= 2


def ray_free(G, p, d, L):
    """True ak luc z bodu p v smere d do dlzky L nic netrafi; inak (vzdialenost, diel)"""
    h = G.tree.ray_cast(Vector(p), Vector(d), L)
    if h[0] is None:
        return None
    return (round(h[3], 2), G.names[G.own[h[2]]])


def tool_channel(G, start, d, L, r=2.25, nring=24, rings=(0.0, 0.75, 1.5, 2.25)):
    """valec naradia polomeru r z bodu start v smere d (dlzka L): vrati dict(volny, blok={diel: min vzdialenost})"""
    d = np.asarray(d, float); d /= np.linalg.norm(d)
    a = np.cross(d, [0, 0, 1.0] if abs(d[2]) < 0.9 else [1.0, 0, 0]); a /= np.linalg.norm(a); b = np.cross(d, a)
    blok = {}
    for rr in rings:
        if rr > r + 1e-9:
            continue
        for k in range(1 if rr == 0 else nring):
            p = np.asarray(start, float) + rr * (math.cos(2 * math.pi * k / nring) * a + math.sin(2 * math.pi * k / nring) * b)
            h = ray_free(G, p, d, L)
            if h:
                blok[h[1]] = min(blok.get(h[1], 1e9), h[0])
    return dict(volny=not blok, blok=blok)
