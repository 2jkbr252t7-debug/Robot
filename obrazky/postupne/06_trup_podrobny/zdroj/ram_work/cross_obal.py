"""RAM <-> OBAL interface check on the exported STL (Blender BVH):  /opt/venv/bl/bin/python cross_obal.py
For every (ram part, obal part) pair with overlapping bounding boxes: triangle-triangle overlap count (BVHTree.overlap),
maximum penetration depth (vertices + subdivided-triangle samples of one inside the other, ray-parity) and the minimum
distance.  Writes ram_work/cross_obal.json.  Advisory (the global K2 belongs to the integrator)."""
import bpy, bmesh, sys, os, json, struct, time
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
T4 = "/tmp/claude-0/gapwf/fin/T4"
ram = json.load(open(os.path.join(T4, "parts_ram.json")))["parts"]
obal = json.load(open(os.path.join(T4, "parts_obal.json")))
obal = obal["parts"] if isinstance(obal, dict) else obal


def read_stl(path):
    with open(path, "rb") as f:
        f.read(80); n = struct.unpack("<I", f.read(4))[0]
        d = np.frombuffer(f.read(n * 50), dtype=np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")]))
    return d["v"].astype(np.float64)


def load(name):
    tri = read_stl(os.path.join(T4, "stl", name + ".stl"))
    V = tri.reshape(-1, 3)
    u, inv = np.unique(np.round(V, 5), axis=0, return_inverse=True)
    F = inv.reshape(-1, 3)
    F = F[(F[:, 0] != F[:, 1]) & (F[:, 1] != F[:, 2]) & (F[:, 0] != F[:, 2])]
    bvh = BVHTree.FromPolygons([Vector(p) for p in u], [tuple(int(i) for i in f) for f in F], epsilon=0.0)
    # sample points: vertices + centroids of big triangles (subdivided)
    a, b, c = u[F[:, 0]], u[F[:, 1]], u[F[:, 2]]
    P = [u]
    area = 0.5 * np.linalg.norm(np.cross(b - a, c - a), axis=1)
    big = area > 0.5
    for A, B, Cc, ar in zip(a[big], b[big], c[big], area[big]):
        n = int(min(30, max(1, np.ceil(np.sqrt(2 * ar) / 1.0))))
        i, j = np.meshgrid(np.arange(n + 1), np.arange(n + 1)); m = i + j <= n
        P.append(A + np.outer(i[m] / n, B - A) + np.outer(j[m] / n, Cc - A))
    P = np.concatenate(P)
    return dict(name=name, bvh=bvh, P=P, lo=u.min(0), hi=u.max(0), ntri=len(F))


DIRS = [Vector(v).normalized() for v in ((0.577, 0.211, 0.789), (-0.331, 0.817, -0.471), (0.123, -0.642, 0.757), (-0.713, -0.299, -0.634), (0.911, 0.4012, -0.0953))]


def inside(bvh, p):
    """ray parity, majority of 5 directions (robust against edge hits / open shells seen through a gap)"""
    votes = 0
    for D in DIRS:
        o = Vector(p); n = 0
        for _ in range(200):
            hit, nrm, idx, dist = bvh.ray_cast(o, D)
            if hit is None:
                break
            n += 1; o = hit + D * 1e-4
        votes += n % 2
    return votes >= 4


def depth(A, B):
    """max depth of the sample points of A inside B, and min distance of A's points to B's surface"""
    lo, hi = B["lo"] - 0.01, B["hi"] + 0.01
    P = A["P"]
    m = np.all((P >= lo - 3.0) & (P <= hi + 3.0), axis=1)
    dmax, at, dmin, atmin = 0.0, None, 1e9, None
    for p in P[m]:
        loc, nrm, idx, dist = B["bvh"].find_nearest(Vector(p))
        if loc is None:
            continue
        if dist < dmin:
            dmin, atmin = dist, p
        if dist > 0.02 and dist > dmax and np.all((p >= lo) & (p <= hi)) and inside(B["bvh"], p):
            dmax, at = dist, p
    return dmax, at, dmin, atmin


t0 = time.time()
R = {p["name"]: load(p["name"]) for p in ram if p["group"] == "T"}
O = {}
for p in obal:
    n = p["name"]
    if os.path.exists(os.path.join(T4, "stl", n + ".stl")):
        O[n] = load(n)
print(f"loaded {len(R)} ram + {len(O)} obal meshes in {time.time() - t0:.1f} s", flush=True)
rows = []
for rn, A in R.items():
    for on, B in O.items():
        if np.any(A["hi"] < B["lo"] - 1.5) or np.any(B["hi"] < A["lo"] - 1.5):
            continue
        ov = A["bvh"].overlap(B["bvh"])
        d1, at1, m1, am1 = depth(A, B)
        d2, at2, m2, am2 = depth(B, A)
        dm = min(m1, m2); am = am1 if m1 <= m2 else am2
        if d1 >= d2:
            dp, at = d1, at1
        else:
            dp, at = d2, at2
        if not ov and dm > 1.5:
            continue
        rows.append(dict(ram=rn, obal=on, tri_overlaps=len(ov), penetration=round(dp, 3), pen_at=None if at is None else [round(float(v), 2) for v in at],
                         min_dist=round(float(dm), 3), min_at=None if am is None else [round(float(v), 2) for v in am]))
rows.sort(key=lambda r: (-r["penetration"], r["min_dist"]))
for r in rows:
    print(f"{r['ram']:18s} {r['obal']:18s} overlaps {r['tri_overlaps']:5d} penetration {r['penetration']:6.3f} at {r['pen_at']}  min dist {r['min_dist']:6.3f} at {r['min_at']}")
json.dump(dict(generated=time.strftime("%Y-%m-%d %H:%M:%S"), pairs=rows, time_s=round(time.time() - t0, 1)), open(os.path.join(T4, "ram_work", "cross_obal.json"), "w"), indent=1)
print(f"done {time.time() - t0:.1f} s")


# =====================================================================================================================
# straight-line assembly of the shells over the RAM tower (advisory K7 pre-check on the real meshes)
#   a shell that arrives along the unit vector u (its motion) collides with a tower point p iff the ray from p along -u
#   ... seen from the shell: the point travels along -u_shell = the direction the shell comes FROM.  Any hit = collision.
def sweep(moving, tower_names, came_from, tag, skip_contact=0.06, clear=0.5):
    verts, faces, off = [], [], 0
    for n in moving:
        if n not in O:
            continue
        tri = read_stl(os.path.join(T4, "stl", n + ".stl")).reshape(-1, 3)
        verts += [Vector(p) for p in tri]; faces += [(off + 3 * i, off + 3 * i + 1, off + 3 * i + 2) for i in range(len(tri) // 3)]
        off += len(tri)
    bvh = BVHTree.FromPolygons(verts, faces, epsilon=0.0)
    U = Vector(came_from).normalized()
    # two unit vectors perpendicular to U for the clearance probes
    a = Vector((1, 0, 0)) if abs(U.x) < 0.9 else Vector((0, 1, 0))
    e1 = U.cross(a).normalized(); e2 = U.cross(e1).normalized()
    res = {}
    for n in tower_names:
        P = R[n]["P"]
        hit0 = hitc = 0; worst = None; near = []
        for p in P:
            v = Vector(p)
            h, nrm, idx, dist = bvh.ray_cast(v + U * skip_contact, U)
            if h is not None:
                hit0 += 1
                if worst is None or dist < worst[0]:
                    worst = (round(dist, 2), [round(float(x), 2) for x in p])
                continue
            for k in range(8):
                ang = k * np.pi / 4
                q = v + (e1 * float(np.cos(ang)) + e2 * float(np.sin(ang))) * clear + U * skip_contact
                h, nrm, idx, dist = bvh.ray_cast(q, U)
                if h is not None:
                    hitc += 1
                    near.append([round(float(x), 2) for x in p] + [round(float(h.z), 2)])
                    break
        if hit0 or hitc:
            res[n] = dict(points=int(len(P)), colliding=hit0, closer_than_clear=hitc, first=worst, near_examples=near[:: max(1, len(near) // 12)][:14])
            if n != "T_spodok":
                print("      near (x, y, z, z of the shell feature hit):", res[n]["near_examples"])
            print(f"  {tag}: {n:18s} points {len(P):6d} colliding {hit0:5d} within {clear}: {hitc:5d} first {worst}", flush=True)
    return res


ASM = {p["name"]: p.get("assembly_step") for p in ram}
before10 = [n for n in R if (ASM.get(n) is not None and ASM[n] <= 9) or n.startswith(("skr_F2", "skr_F3", "skr_F4", "skr_F5", "skr_F7", "skr_F14", "vl_"))]
stred_set = ["T_stred", "T_svetlovod", "T_mriezka", "T_drziak_led", "T_drziak_repro", "reproduktor", "tesnenie_repro", "DPS_led", "vyvod_repro", "vyvod_led",
             "skrutka_led_1", "skrutka_led_2", "skrutka_repro_1", "skrutka_repro_2", "skrutka_repro_3", "vlozka_stred_1", "vlozka_stred_2", "vlozka_stred_3",
             "vlozka_stred_4", "magnet_zarubna_1", "magnet_zarubna_2", "magnet_zarubna_3", "magnet_zarubna_4"]
print("T_stred (+ front stack, inserts, magnets) lowered -Z over the tower of step 9:", flush=True)
out = dict(T_stred=sweep(stred_set, before10, (0, 0, -1), "stred"))
print("T_stred alone:", flush=True)
out["T_stred_alone"] = sweep(["T_stred", "vlozka_stred_1", "vlozka_stred_2", "vlozka_stred_3", "vlozka_stred_4"], before10, (0, 0, -1), "stred0")
allT = [n for n in R if n not in ("T_prichytka_fpc",)]
print("T_bok_L pushed on along -X:", flush=True)
out["T_bok_L"] = sweep(["T_bok_L"], allT, (-1, 0, 0), "bok_L")
print("T_bok_P pushed on along +X:", flush=True)
out["T_bok_P"] = sweep(["T_bok_P"], allT, (1, 0, 0), "bok_P")
d = json.load(open(os.path.join(T4, "ram_work", "cross_obal.json"))); d["straight_assembly"] = out
json.dump(d, open(os.path.join(T4, "ram_work", "cross_obal.json"), "w"), indent=1)
print(f"sweeps done {time.time() - t0:.1f} s")
