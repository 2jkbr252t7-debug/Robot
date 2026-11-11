"""Axisymmetric head keep-out profile above the torso top from the REAL head STLs (variant B rev. E2), swept over the
tilt-vs-lift table of B/montaz.txt.  Because pan turns the head about Z, the profile z_min(r) holds for every direction.
Writes head_keepout.json: for r bins (0.5 mm) the lowest head point (world z, with Z_TT=133) over all allowed poses."""
import json, math, struct
import numpy as np

STL = "/tmp/claude-0/gapwf/fin/B/stl"
PARTS = ["hlava_skrupina", "ram_displeja", "usi", "displej"]
Z_TT = 133.0
DZ = Z_TT - 4.0
AX_REST = -3.5                       # hinge axis z (B frame) at rest, y = 0
# montaz table, t1lib lift convention (0 = rest, 20 = extended): rows (lift, tilt_down_max, tilt_up_max)
TABLE = [(0, 5, 10), (2.5, 10, 15), (5, 15, 20), (7.5, 20, 30), (10, 25, 35), (12.5, 30, 40), (16, 35, 40), (18, 40, 40)]


def read_stl(fn):
    b = open(fn, "rb").read()
    n = struct.unpack("<I", b[80:84])[0]
    a = np.frombuffer(b[84:84 + 50 * n], dtype=np.dtype([("n", "<3f4"), ("v", "<3f4", (3,)), ("att", "<u2")]))
    V = a["v"].reshape(-1, 3).astype(float)
    # add edge midpoints + centroids (denser sampling of large flat triangles)
    T = a["v"].astype(float)
    mids = np.vstack([(T[:, 0] + T[:, 1]) / 2, (T[:, 1] + T[:, 2]) / 2, (T[:, 2] + T[:, 0]) / 2, T.mean(axis=1)])
    return np.vstack([V, mids])


def poses():
    out = []
    for i, (L, dn, up) in enumerate(TABLE):
        Lmax = TABLE[i + 1][0] if i + 1 < len(TABLE) else 20.0
        for lift in sorted({L, (L + Lmax) / 2, Lmax if i + 1 == len(TABLE) else Lmax - 0.01}):
            for t in sorted(set(list(np.arange(-up, dn + 0.1, 5.0)) + [-up, dn])):
                out.append((lift, float(t)))
    return out


if __name__ == "__main__":
    P = np.vstack([read_stl(f"{STL}/{p}.stl") for p in PARTS])
    P = P[P[:, 2] < 40.0]                               # only the lower part of the head can come close to the torso
    edges = np.arange(0, 80.5, 0.5)
    zmin = np.full(len(edges) - 1, 1e9)
    worst = [None] * (len(edges) - 1)
    for lift, tilt in poses():
        ax = AX_REST + lift
        t = math.radians(tilt)
        y, z = P[:, 1], P[:, 2] + lift - ax
        y2 = y * math.cos(t) - z * math.sin(t)
        z2 = y * math.sin(t) + z * math.cos(t) + ax + DZ
        r = np.hypot(P[:, 0], y2)
        idx = np.digitize(r, edges) - 1
        ok = (idx >= 0) & (idx < len(zmin))
        for k in np.unique(idx[ok]):
            m = idx == k
            v = z2[m].min()
            if v < zmin[k]:
                zmin[k] = v
                worst[k] = (lift, tilt)
    prof = [{"r": [float(edges[k]), float(edges[k + 1])], "z_min_head": round(float(zmin[k]), 2),
             "drop_below_top": round(Z_TT - float(zmin[k]), 2), "pose_lift_tilt": worst[k]}
            for k in range(len(zmin)) if zmin[k] < 1e8]
    json.dump({"note": "lowest point of the real head (shell, display frame, glass, ears) over all (lift, tilt) of the "
                       "B tilt-vs-lift table, any pan; world z with Z_TT = 133. The torso top surface at radius r must "
                       "stay below z_min_head - 1.0 (clearance) in every direction.", "profile": prof},
              open("/tmp/claude-0/gapwf/fin/T1/k2/head_keepout.json", "w"), indent=1)
    for p in prof:
        if p["r"][0] % 2 == 0 and 20 <= p["r"][0] <= 60:
            print(p["r"][0], p["z_min_head"], p["drop_below_top"], p["pose_lift_tilt"])
