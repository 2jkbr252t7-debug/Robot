"""K2 minimum interior envelope -> envelope.json
Torso slices (torso frame, J1 = 0): T parts + P parts swept pan -85..85 + L parts swept pan x lift 0..20.
Base slices (base frame): B parts + T parts below the torso floor swept J1 -155..155.
Each slice [z, z+5]: bbox of all internal parts + 1.0 mm, r_max about Z + 1.0, convex hull (+1.0 mm, simplified),
and the minimum interior superellipse half-axes a for n = 2.2 / 2.35 / 2.5 / 3.0 with the placeholder aspect b/a."""
import sys, json, math
import numpy as np
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T1")
import t1lib as T

K2 = "/tmp/claude-0/gapwf/fin/T1/k2"
L = T.Layout(f"{K2}/layout.json")
CL = 1.0


def tess(name):
    s = L.raw(name)
    v, t = s.tessellate(0.15, 0.25)
    V = np.array([[p.X, p.Y, p.Z] for p in v])
    Tr = np.array(t, dtype=int)
    E = np.vstack([Tr[:, [0, 1]], Tr[:, [1, 2]], Tr[:, [2, 0]]])
    E = np.unique(np.sort(E, axis=1), axis=0)
    return V, E


def rotz(V, deg, dz=0.0):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    R = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
    W = V @ R.T
    W[:, 2] += dz
    return W


def slab_pts(V, E, z0, z1):
    P, Q = V[E[:, 0]], V[E[:, 1]]
    out = []
    pz, qz = P[:, 2], Q[:, 2]
    inP = (pz >= z0) & (pz <= z1)
    inQ = (qz >= z0) & (qz <= z1)
    out.append(P[inP][:, :2]); out.append(Q[inQ][:, :2])
    for zz in (z0, z1):
        m = (pz - zz) * (qz - zz) < 0
        if m.any():
            t = (zz - pz[m]) / (qz[m] - pz[m])
            out.append((P[m] + (Q[m] - P[m]) * t[:, None])[:, :2])
    return np.vstack(out) if out else np.zeros((0, 2))


def hull2(pts):
    pts = sorted(set(map(tuple, np.round(pts, 2))))
    if len(pts) < 3:
        return pts
    cr = lambda o, a, b: (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cr(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cr(up[-2], up[-1], p) <= 0:
            up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]


def offset_hull(h, d):
    pts = [(x + d * math.cos(a), y + d * math.sin(a)) for x, y in h for a in np.linspace(0, 2 * math.pi, 16, endpoint=False)]
    hh = hull2(np.array(pts))
    # simplify: drop points closer than 1.5 mm to the previous kept one
    out = []
    for p in hh:
        if not out or math.dist(p, out[-1]) > 1.5:
            out.append(p)
    return [[round(x, 1), round(y, 1)] for x, y in out]


def se_a(pts, n, k):
    """minimal superellipse half axis a (b = k a) containing pts"""
    if len(pts) == 0:
        return 0.0
    x, y = np.abs(pts[:, 0]), np.abs(pts[:, 1]) / k
    return float(np.max((x ** n + y ** n) ** (1 / n)))


def slices(sets, z_from, z_to, k):
    res = []
    z = z_from
    while z < z_to - 1e-6:
        z1 = min(z + 5.0, z_to)
        allp, who = [], []
        for nm, VV in sets:
            for V, E in VV:
                p = slab_pts(V, E, z, z1)
                if len(p):
                    allp.append(p)
                    who.append(nm)
        if allp:
            P = np.vstack(allp)
            h = hull2(P)
            oh = offset_hull(h, CL)
            OH = np.array(oh)
            rec = {"z": [round(z, 1), round(z1, 1)],
                   "x": [round(P[:, 0].min() - CL, 1), round(P[:, 0].max() + CL, 1)],
                   "y": [round(P[:, 1].min() - CL, 1), round(P[:, 1].max() + CL, 1)],
                   "r_max": round(float(np.max(np.hypot(P[:, 0], P[:, 1]))) + CL, 1),
                   "min_interior_superellipse_a": {str(n): round(se_a(OH, n, k), 1) for n in (2.2, 2.35, 2.5, 3.0)},
                   "b_over_a": k,
                   "hull_plus_1mm": oh, "parts": sorted(set(who))}
        else:
            rec = {"z": [round(z, 1), round(z1, 1)], "empty": True}
        res.append(rec)
        z = z1
    return res


if __name__ == "__main__":
    comps = {c["name"]: c for c in L.comps}
    # parts that pass through the shell by design are reported as fixed interfaces, not as interior envelope
    THROUGH = {"T_paka_L", "T_paka_R", "T_kabel_ramena_L", "T_kabel_ramena_R", "T_svetlo", "Z_svetlo", "Z_USB_C",
               "Z_vypinac"}
    comps = {k: v for k, v in comps.items() if k not in THROUGH}
    # ---------------- torso
    tset = []
    for nm, c in comps.items():
        g = c["group"]
        if nm in ("T_shell",) or g in ("H", "AR", "AL", "B"):
            continue
        V, E = tess(nm)
        if g == "T":
            if V[:, 2].max() <= 43.0 + 1e-6:  # entirely below the torso floor -> base set only
                continue
            tset.append((nm, [(V, E)]))
        elif g == "P":
            tset.append((nm, [(rotz(V, a), E) for a in range(-85, 86, 10)] + [(rotz(V, 85), E)]))
        elif g == "L":
            tset.append((nm, [(rotz(V, a, dz), E) for a in range(-85, 86, 10) for dz in (0, 5, 10, 15, 20)]))
    torso = slices(tset, 43.0, 133.0, 40.0 / 44.5)
    SHELL_MOUNTED = {"T_stlpik_L", "T_stlpik_R", "T_horny_kruh", "T_reproduktor", "B_golier_prstenec"}
    torso_free = slices([t for t in tset if t[0] not in SHELL_MOUNTED], 43.0, 133.0, 40.0 / 44.5)
    # ---------------- base
    bset = []
    for nm, c in comps.items():
        g = c["group"]
        if nm == "Z_shell":
            continue
        if g == "B":
            V, E = tess(nm)
            bset.append((nm, [(V, E)]))
        elif g == "T":
            V, E = tess(nm)
            if V[:, 2].min() < 43.0 - 1e-6 and nm != "T_shell":
                bset.append((nm, [(rotz(V, a), E) for a in range(-155, 156, 10)]))
    base = slices(bset, 0.0, 43.0, 55.0 / 71.0)
    # ---------------- arm (arm frame = right arm at 0 deg; mirror x for the left arm)
    arm = {}
    for nm in ("A_R_servo", "A_R_kabel", "A_R_kryt"):
        bb = L.raw(nm).bounding_box()
        arm[nm] = {"x": [round(bb.min.X, 2), round(bb.max.X, 2)], "y": [round(bb.min.Y, 2), round(bb.max.Y, 2)],
                   "z": [round(bb.min.Z, 2), round(bb.max.Z, 2)]}
    json.dump({"torso_slices": torso, "torso_slices_without_shell_mounted_parts": torso_free,
               "base_slices": base, "arm_parts_bbox_rest": arm},
              open(f"{K2}/envelope_slices.json", "w"), indent=1)
    for s in torso_free:
        if not s.get("empty"):
            print("free", s["z"], s["x"], s["y"], s["r_max"], s["min_interior_superellipse_a"]["2.35"])
    for s in torso + base:
        if not s.get("empty"):
            print(s["z"], s["x"], s["y"], s["r_max"], s["min_interior_superellipse_a"]["2.35"], len(s["hull_plus_1mm"]))
