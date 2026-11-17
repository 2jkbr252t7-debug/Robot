"""NOVA mini - T4 torso: mesh checks that need a BVH (Blender python, mathutils.bvhtree).  Called by checks.py.

    /opt/venv/bl/bin/python checks_bl.py K2 [K4] [K7] [K8] [K9]      -> integ_work/bl_<section>.json

K2  interference at rest: BVH triangle overlap of every bbox-overlapping pair of ALL parts (parts.json + the finished parts
    of variant B that mate with the torso); common volume by ray-parity sampling; containment test
K4  opposing-face thickness scan of every printed part (ray from a surface sample along the inward normal)
K7  assembly: straight-line withdrawal rays of every assembly step against the parts present at that step; D4.5 tool
    channels of every screw
K8  exterior: deviation of the visible shells from the approved T3 surface, see-through rays from 26 viewpoints
K9  real head / neck (variant B STL) against the torso meshes over pan x lift x tilt
"""
import sys, os, json, math, time
import numpy as np
import bpy                                              # noqa: F401  (makes mathutils importable)
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import t4_mesh as TM                                    # noqa: E402

WORK = os.path.join(HERE, "integ2_work")              # rev. 2 (rev. 1 results stay in integ_work/)
os.makedirs(WORK, exist_ok=True)
T0 = time.time()
ARGS = [a for a in sys.argv[1:] if a.startswith("K")]
OPTS = [a for a in sys.argv[1:] if a.startswith("--")]
PARTS = json.load(open(os.path.join(HERE, "parts.json")))["parts"]
REC = {r["name"]: r for r in PARTS}
B_MATE = ["golier_prstenec", "golier_kotuc", "krk_predna_polovica", "krk_zadna_polovica", "kabel"]     # finished parts (variant B)
B_GROUP = {"golier_prstenec": "T", "golier_kotuc": "P", "krk_predna_polovica": "L", "krk_zadna_polovica": "L", "kabel": "L"}


def say(*a):
    print(f"[{time.time() - T0:6.1f}]", *a, flush=True)


class Mesh:
    def __init__(self, name, T=None):
        self.name = name
        self.T = TM.stl(name) if T is None else T
        self.V, self.F = TM.weld(self.T, 5)
        self.bb = np.concatenate([self.V.min(0), self.V.max(0)])
        self._tree = None

    @property
    def tree(self):
        if self._tree is None:
            self._tree = BVHTree.FromPolygons(self.V.tolist(), self.F.tolist(), all_triangles=True, epsilon=0.0)
        return self._tree


_M = {}


def mesh(name):
    if name not in _M:
        _M[name] = Mesh(name)
    return _M[name]


DIRS = [Vector((0.5377, 0.3181, 0.7808)).normalized(), Vector((-0.2113, 0.8712, 0.4431)).normalized(),
        Vector((0.7312, -0.6017, 0.3217)).normalized()]


def inside(tree, p, d=DIRS[0]):
    """ray parity of point p against a closed mesh (the BVH is float32: restart 2e-4 behind every hit, never count the same
    triangle twice in a row)"""
    cnt = 0
    o = Vector(p)
    last = -1
    for _ in range(400):
        hit = tree.ray_cast(o, d, 1e4)
        if hit[0] is None:
            break
        if hit[2] == last and hit[3] < 1e-3:
            o = o + d * 1e-3
            continue
        cnt += 1
        last = hit[2]
        o = hit[0] + d * 2e-4
    return cnt % 2 == 1


def inside3(tree, p):
    return sum(1 for d in DIRS if inside(tree, p, d)) >= 2


def tree_of(names, xf=None):
    """one BVH of several parts; returns (tree, face -> part index array, names)"""
    Vs, Fs, own, off = [], [], [], 0
    for i, n in enumerate(names):
        m = mesh(n)
        V = m.V if xf is None or xf.get(n) is None else xf[n](m.V)
        Vs.append(V); Fs.append(m.F + off); own.append(np.full(len(m.F), i, np.int32)); off += len(V)
    V = np.concatenate(Vs); F = np.concatenate(Fs)
    return BVHTree.FromPolygons(V.tolist(), F.tolist(), all_triangles=True, epsilon=0.0), np.concatenate(own), list(names)


# =====================================================================================================================
# K2  interference at rest
# =====================================================================================================================
def pair_test(a, b, max_pts=120000):
    """BVH overlap of two closed meshes -> dict(tri_pairs, contained, common_mm3, max_half_depth, clusters)"""
    ma, mb = mesh(a), mesh(b)
    ta, tb = ma.tree, mb.tree
    ov = ta.overlap(tb)
    if not ov:
        ca = inside3(tb, ma.V[0]); cb = inside3(ta, mb.V[0])
        if not (ca or cb):
            return dict(tri_pairs=0, contained=False, common_mm3=0.0, max_half_depth=0.0)
        inner, outer = (ma, mb) if ca else (mb, ma)
        # fully contained: common volume = volume of the inner part; depth = distance of its surface to the outer surface
        Vi = inner.V[:: max(1, len(inner.V) // 400)]
        dep = min(outer.tree.find_nearest(Vector(p))[3] for p in Vi)
        a_, b_, c_ = inner.V[inner.F[:, 0]], inner.V[inner.F[:, 1]], inner.V[inner.F[:, 2]]
        vol = float(np.einsum("ij,ij->i", a_, np.cross(b_, c_)).sum() / 6.0)
        return dict(tri_pairs=0, contained=True, inner=inner.name, common_mm3=round(vol, 3), max_half_depth=round(float(dep), 3))
    ia = sorted({i for i, _ in ov}); ib = sorted({j for _, j in ov})
    pts = np.concatenate([ma.V[ma.F[ia]].reshape(-1, 3), mb.V[mb.F[ib]].reshape(-1, 3)])
    cell = np.floor(pts / 6.0).astype(int)
    keys = {tuple(k) for k in cell.tolist()}
    clusters, seen = [], set()
    for k in keys:
        if k in seen:
            continue
        stack = [k]; grp = []
        while stack:
            q = stack.pop()
            if q in seen or q not in keys:
                continue
            seen.add(q); grp.append(q)
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    for dz in (-1, 0, 1):
                        stack.append((q[0] + dx, q[1] + dy, q[2] + dz))
        gs = set(grp)
        m = np.array([tuple(c) in gs for c in cell.tolist()])
        clusters.append(pts[m])
    tot = 0.0; cl_out = []
    budget = max(6000, max_pts // max(1, len(clusters)))
    for cp in clusters:
        lo = cp.min(0) - 0.25; hi = cp.max(0) + 0.25
        lo = np.maximum(lo, np.maximum(ma.bb[:3], mb.bb[:3]) - 0.01); hi = np.minimum(hi, np.minimum(ma.bb[3:], mb.bb[3:]) + 0.01)
        if np.any(hi <= lo):
            continue
        vol_box = float(np.prod(hi - lo))
        h = max(0.04, (vol_box / budget) ** (1 / 3))
        gx, gy, gz = (np.arange(lo[k] + h / 2, hi[k], h) for k in range(3))
        cnt = 0; cen = np.zeros(3); deep = 0.0
        for xx in gx:
            for yy in gy:
                for zz in gz:
                    p = Vector((xx, yy, zz))
                    if inside(ta, p) and inside(tb, p) and inside3(ta, p) and inside3(tb, p):
                        cnt += 1; cen += (xx, yy, zz)
                        deep = max(deep, min(ta.find_nearest(p)[3], tb.find_nearest(p)[3]))
        v = cnt * h ** 3
        tot += v
        if cnt:
            cl_out.append(dict(common_mm3=round(v, 3), centre=[round(float(q), 2) for q in cen / cnt], half_depth=round(deep, 3), grid=round(h, 3)))
    cl_out.sort(key=lambda q: -q["common_mm3"])
    return dict(tri_pairs=len(ov), contained=False, common_mm3=round(tot, 3), clusters=cl_out[:6],
                max_half_depth=max([c["half_depth"] for c in cl_out], default=0.0))


def run_K2():
    names = [r["name"] for r in PARTS] + B_MATE
    for n in names:
        mesh(n)
    say("K2: loaded", len(names), "meshes")
    pairs = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            if TM.bb_near(mesh(a).bb, mesh(b).bb, 0.0):
                pairs.append((a, b))
    say("K2: bbox-overlapping pairs", len(pairs))
    out = []
    for k, (a, b) in enumerate(pairs):
        t = time.time()
        r = pair_test(a, b)
        if r["tri_pairs"] or r["contained"]:
            r.update(a=a, b=b)
            out.append(r)
        if time.time() - t > 5:
            say(f"   slow pair {a} / {b}: {time.time() - t:.1f} s, tri pairs {r['tri_pairs']}, common {r['common_mm3']}")
    json.dump(dict(names=names, pairs_tested=len(pairs), touching=out, time_s=round(time.time() - T0, 1),
                   stl_md5={n: REC[n]["stl"]["md5"] for n in REC},
                   method="BVH triangle overlap (mathutils.bvhtree) of every bbox-overlapping pair of STL meshes (deflection 0.01); common "
                          "volume by ray-parity sampling in boxes around the intersecting triangles (grid >= 0.04 mm, 3 ray directions); "
                          "containment by a parity test of one vertex; half_depth = deepest common point's distance to either surface"),
              open(os.path.join(WORK, "bl_K2.json"), "w"), indent=1)
    say("K2 done:", len(out), "pairs touch / overlap")


if "K2" in ARGS:
    run_K2()


# =====================================================================================================================
# K9  real head / neck of variant B against the torso meshes
# =====================================================================================================================
HEAD_PARTS = ["hlava_skrupina", "ram_displeja", "displej", "pena_displeja", "drziak_displeja", "magnety", "usi", "led_kruzky",
              "led_dosky", "oci_len_vizualizacia", "usko_kryt", "usko_lozisko", "paka", "klzny_kruzok"]      # group H of B/build.py
STAGE_PARTS = ["golier_kotuc", "P_sachta", "ptfe_pas_capu", "ptfe_pasik_1", "ptfe_pasik_2", "ptfe_pasik_3", "ptfe_pasik_4",
               "ptfe_pasik_5", "ptfe_pasik_6", "ptfe_pasik_7"]                                                # turn with the head (pan), rev. 2


def run_K9():
    import t4_common as C
    I = C.INTEG
    AXZ, TOP, CRIT, CAP = I["TILT_AXIS_Z"], C.TOP, I["HEAD_CLEAR"], 3.2
    TABLE = {float(k): v for k, v in I["B_TILT_TABLE"].items()}
    PANS = [float(p) for p in range(-85, 86, 5)]
    fine = "--fine" in OPTS
    # ---- meshes
    stat_names = [r["name"] for r in PARTS if r["group"] == "T" and r["bbox"][5] > -31.0] + ["golier_prstenec"]
    st_tree, st_own, st_names = tree_of(stat_names)
    sg_tree, sg_own, sg_names = tree_of(STAGE_PARTS)
    hd_tree, hd_own, hd_names = tree_of(HEAD_PARTS)
    say("K9: static parts", len(stat_names), "| stage parts", len(STAGE_PARTS), "| head parts", len(HEAD_PARTS))
    # ---- sample points
    Hp, Hown = [], []
    for i, n in enumerate(HEAD_PARTS):
        T = mesh(n).T
        low = T[T[:, :, 2].min(1) < 20.0]
        S = TM.sample(low, 0.4)[0] if len(low) else np.zeros((0, 3))
        P = np.concatenate([mesh(n).V, S])
        Hp.append(P); Hown.append(np.full(len(P), i, np.int32))
    Hp = np.concatenate(Hp); Hown = np.concatenate(Hown)
    Sp, Sown = [], []
    for i, n in enumerate(stat_names):
        T = mesh(n).T
        hi = T[T[:, :, 2].max(1) > TOP - CAP - 0.3]
        if len(hi):
            S = TM.sample(hi, 0.4)[0]
            S = S[S[:, 2] > TOP - CAP - 0.3]
            Sp.append(S); Sown.append(np.full(len(S), i, np.int32))
    Sp = np.concatenate(Sp); Sown = np.concatenate(Sown)
    Gp, Gown = [], []
    for i, n in enumerate(STAGE_PARTS):
        S = TM.sample(mesh(n).T, 0.4)[0]
        Gp.append(S); Gown.append(np.full(len(S), i, np.int32))
    Gp = np.concatenate(Gp); Gown = np.concatenate(Gown)
    hd_bb = np.concatenate([Hp.min(0), Hp.max(0)])
    say(f"K9: head points {len(Hp)}, static top points {len(Sp)}, stage points {len(Gp)}")

    def pose(P, tilt, lift, pan):
        Q = TM.rotx(P, tilt, 0.0, AXZ)
        Q[:, 2] += lift
        return TM.rotz(Q, pan) if pan else Q

    def unpose(P, tilt, lift, pan):
        Q = TM.rotz(P, -pan) if pan else np.array(P, copy=True)
        Q[:, 2] -= lift
        return TM.rotx(Q, -tilt, 0.0, AXZ)

    def nearest(tree, own, names, Q, src_own, src_names, cap=CAP):
        best = (cap, None, None, None)
        for q, so in zip(Q.tolist(), src_own.tolist()):
            loc, nrm, idx, d = tree.find_nearest(Vector(q), best[0])
            if loc is not None and d < best[0]:
                best = (d, q, names[own[idx]], src_names[so])
        return best

    def clear_static(tilt, lift, pan):
        Q = pose(Hp, tilt, lift, pan)
        m = Q[:, 2] < TOP + CAP
        b1 = nearest(st_tree, st_own, st_names, Q[m], Hown[m], HEAD_PARTS)
        # reverse: torso top points into the head frame
        R = unpose(Sp, tilt, lift, pan)
        m2 = np.all((R > hd_bb[:3] - CAP) & (R < hd_bb[3:] + CAP), axis=1)
        b2 = nearest(hd_tree, hd_own, hd_names, R[m2], Sown[m2], st_names, cap=b1[0])
        if b2[1] is not None and b2[0] < b1[0]:
            at = pose(np.array([b2[1]]), tilt, lift, pan)[0]
            return (b2[0], [round(float(v), 2) for v in at], b2[3], b2[2])            # (d, at, torso part, head part)
        return (b1[0], None if b1[1] is None else [round(float(v), 2) for v in b1[1]], b1[2], b1[3])

    def clear_stage(tilt, lift):
        Q = pose(Hp, tilt, lift, 0.0)
        m = (Q[:, 2] < TOP + CAP) & (np.hypot(Q[:, 0], Q[:, 1]) < 28.5 + CAP)
        b1 = nearest(sg_tree, sg_own, sg_names, Q[m], Hown[m], HEAD_PARTS)
        R = unpose(Gp, tilt, lift, 0.0)
        m2 = np.all((R > hd_bb[:3] - CAP) & (R < hd_bb[3:] + CAP), axis=1)
        b2 = nearest(hd_tree, hd_own, hd_names, R[m2], Gown[m2], sg_names, cap=b1[0])
        if b2[1] is not None and b2[0] < b1[0]:
            at = pose(np.array([b2[1]]), tilt, lift, 0.0)[0]
            return (b2[0], [round(float(v), 2) for v in at], b2[3], b2[2])
        return (b1[0], None if b1[1] is None else [round(float(v), 2) for v in b1[1]], b1[2], b1[3])

    res = dict(criterion=CRIT, cap=CAP, pans=PANS, table_B=TABLE, lifts={})
    worst_all = (9.0, None)
    for lift in sorted(TABLE, reverse=True):
        dn, up = TABLE[lift]
        step = 2.5 if fine else 5.0
        tilts = [float(t) for t in np.arange(-up, dn + 1e-6, step)]
        grid = {}
        t1 = time.time()
        for tilt in tilts:
            for pan in PANS:
                grid[(tilt, pan)] = clear_static(tilt, lift, pan)
        stage = {tilt: clear_stage(tilt, lift) for tilt in tilts}
        say(f"K9: lift {lift}: {len(grid)} poses in {time.time() - t1:.0f} s")
        # limits per pan
        lim, reduced = {}, {}
        for pan in PANS:
            ok_dn = [t for t in tilts if t >= 0 and all(grid[(u, pan)][0] >= CRIT for u in tilts if 0 <= u <= t)]
            ok_up = [t for t in tilts if t <= 0 and all(grid[(u, pan)][0] >= CRIT for u in tilts if t <= u <= 0)]
            lim[pan] = (max(ok_dn) if ok_dn else None, min(ok_up) if ok_up else None)
            if lim[pan] != (dn, -up):
                reduced[pan] = lim[pan]
        wk = min(grid, key=lambda k: grid[k][0])
        w = grid[wk]
        at_lim = {"down": [round(grid[(dn, p)][0], 3) for p in PANS], "up": [round(grid[(-up, p)][0], 3) for p in PANS],
                  "zero": [round(grid[(0.0, p)][0], 3) for p in PANS]}
        sk = min(stage, key=lambda k: stage[k][0])
        res["lifts"][str(lift)] = dict(
            tilt_table_B=dict(down=dn, up=up), tilts_tested=tilts,
            min_clearance=round(w[0], 3), at=dict(tilt=wk[0], pan=wk[1], point=w[1], torso_part=w[2], head_part=w[3]),
            min_by_tilt={str(t): round(min(grid[(t, p)][0] for p in PANS), 3) for t in tilts},
            pan_spread_at_limits={k: round(max(v) - min(v), 3) for k, v in at_lim.items()},
            clearance_map_at_table_limits=at_lim,
            clearance_map={str(t): [round(grid[(t, p)][0], 3) for p in PANS] for t in tilts},
            limit_per_pan={str(int(p)): lim[p] for p in PANS}, reduced_pans={str(int(p)): v for p, v in reduced.items()},
            head_vs_stage=dict(min=round(stage[sk][0], 3), tilt=sk, point=stage[sk][1], stage_part=stage[sk][2], head_part=stage[sk][3],
                               by_tilt={str(t): round(stage[t][0], 3) for t in tilts}))
        if w[0] < worst_all[0]:
            worst_all = (w[0], dict(lift=lift, tilt=wk[0], pan=wk[1], point=w[1], torso_part=w[2], head_part=w[3]))
        say(f"   min {w[0]:.3f} at tilt {wk[0]} pan {wk[1]} {w[1]} {w[2]} / {w[3]}; reduced pans: {reduced if reduced else 'none'}; "
            f"head vs stage min {stage[sk][0]:.3f} at tilt {sk} ({stage[sk][2]} / {stage[sk][3]})")
    res.update(min_clearance=round(worst_all[0], 3), worst=worst_all[1], time_s=round(time.time() - T0, 1),
               static_parts=stat_names, stage_parts=STAGE_PARTS, head_parts=HEAD_PARTS,
               not_included="mixed-group STLs of variant B (skrutky, kabel, loziska_MR85: inside the head / neck) and the neck group N "
                            "(krk_*, servo_MG90S, capy, pena_serva: lift only, inside the well - see K3)",
               method="mathutils.bvhtree: head group H of variant B (all vertices + 0.4 mm samples of every triangle below z 20) posed by tilt "
                      "about the X axis through (y 0, z -3.5 + lift), lift, pan; nearest point on the BVH of the static torso parts "
                      f"(T group with z max > -31 + golier_prstenec) for every head point below z {TOP + CAP}; reverse direction: 0.4 mm samples "
                      "of the torso top transformed into the head frame against the head BVH; minimum of both.  Values are capped at "
                      f"{CAP}.  head_vs_stage: the same against the parts that turn with the head (collar disc, well, PTFE strips), pan 0.",
               stl_md5={n: REC[n]["stl"]["md5"] for n in stat_names + STAGE_PARTS if n in REC})
    json.dump(res, open(os.path.join(WORK, "bl_K9.json"), "w"), indent=1)
    say("K9 done: min", worst_all)


if "K9" in ARGS:
    run_K9()


# =====================================================================================================================
# K8  exterior fidelity against the approved T3 surface + see-through rays from 26 viewpoints
# =====================================================================================================================
EXT_WHITE = ["T_stred", "T_bok_L", "T_bok_P", "T_dvere", "T_svetlovod", "T_mriezka"]
EXT_BLACK = ["T_spodok", "T_klb_L", "T_klb_P"]


def run_K8():
    import t4_common as C
    sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T3")
    import shape as S3
    res = {}
    # ---------------------------------------------------------------- (a) deviation from the T3 surface
    names = EXT_WHITE + EXT_BLACK + [r["name"] for r in PARTS if r["name"].startswith(("magnet_klb", "skrutka_klb", "podlozka_klb"))]
    tree, own, nm = tree_of(names)
    H = 0.5
    ss = S3.stations(0.0, S3.S_END, H)
    P, N, DROP = [], [], []
    e = 1e-3
    for s in ss:
        drop, a, b, n = S3.prof(s)
        per = 2 * math.pi * math.sqrt((a * a + b * b) / 2)
        cnt = max(24, int(per / H))
        p0 = S3.section(s, 0.0, cnt)
        pa = S3.section(max(0.0, s - e), 0.0, cnt); pb = S3.section(min(S3.S_END, s + e), 0.0, cnt)
        ds = pb - pa                                              # along the profile (downward)
        dth = np.roll(p0, -1, 0) - np.roll(p0, 1, 0)              # along the section (counter-clockwise)
        nn = np.cross(ds, dth)                                    # down x ccw = outward
        nn /= np.maximum(np.linalg.norm(nn, axis=1), 1e-12)[:, None]
        P.append(p0); N.append(nn); DROP.append(np.full(cnt, drop))
    P = np.concatenate(P); N = np.concatenate(N); DROP = np.concatenate(DROP)
    # sanity: normals point outward
    assert float((N[:, 0] * P[:, 0] + N[:, 1] * P[:, 1]).mean()) > 0
    START = 2.0
    dev = np.full(len(P), np.nan); part = np.full(len(P), -1, np.int32)
    for i in range(len(P)):
        o = Vector(P[i] + START * N[i]); d = Vector(-N[i])
        hit = tree.ray_cast(o, d, 2 * START)
        if hit[0] is not None:
            dev[i] = START - hit[3]; part[i] = own[hit[2]]
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    dw, dh, dr = C.DOOR
    zc = C.Z_DOOR

    def rrect(xx, zz, w, h, r):
        qx = np.abs(xx) - (w / 2 - r); qz = np.abs(zz - zc) - (h / 2 - r)
        return np.hypot(np.maximum(qx, 0), np.maximum(qz, 0)) + np.minimum(np.maximum(qx, qz), 0) - r

    def pill(xx, zz, w, h, z0):
        r = h / 2
        return np.hypot(np.maximum(np.abs(xx) - (w / 2 - r), 0), zz - z0) - r

    M = 0.30                                                      # margin around the gap outlines (grid 0.5, oblique rays)
    d_door = rrect(x, z, dw, dh, dr)                              # < 0 inside the door outline
    r_sock = np.hypot(y - C.SH_Y, z - C.SH_Z)
    notch = C.OBAL["DOOR_NOTCH"]
    zone = np.full(len(P), "", dtype=object)
    back, front = y > 5.0, y < -5.0
    zone[:] = "white"
    zone[DROP < 2.6] = "D1_rim (declared: flat rim r 29.6 + blend, <= 1.5)"
    zone[(DROP >= 85.0 - M) & (DROP <= 85.5 + M)] = "D3_seam_white_black"
    zone[DROP > 85.5 + M] = "cap"
    # holes in the tucked-under part of the cap (the underside is free): F1 / F2 countersinks, drain holes
    holes = [(x0, y0, 3.4) for x0, y0 in C.SCR_STRED] + [(x0, y0, 3.2) for x0, y0 in C.RAM["SCR_RAM"]] + [(x0, y0, 1.6) for x0, y0 in C.DRAIN]
    for x0, y0, r0 in holes:
        zone[(DROP > 85.5 + M) & (np.hypot(x - x0, y - y0) < r0 + M)] = "cap_underside_holes (free: F1 / F2 countersinks, drains)"
    wh = zone == "white"
    zone[wh & (np.abs(np.abs(x) - C.XS) <= C.SEAM / 2 + M)] = "seam_x"
    zone[wh & back & (d_door > -M) & (d_door < C.SEAM / 2 + M)] = "door_seam"
    zone[wh & back & (np.abs(x) <= notch["w"] / 2 + M) & (z < zc - dh / 2 + notch["h"] + M) & (z > zc - dh / 2 - M)] = "door_notch"
    zone[wh & (np.abs(x) > C.X_CAP) & (r_sock < C.R_SOCKET + M)] = "shoulder_socket (joint)"
    zone[wh & front & (np.abs(pill(x, z, C.BAR[0], C.BAR[1], C.Z_BAR)) <= M)] = "bar_gap"
    zone[wh & front & (np.abs(pill(x, z, C.SLOT[0], C.SLOT[1], C.Z_SLOT)) <= M)] = "grille_gap"
    zone[wh & front & (pill(x, z, C.SLOT[0], C.SLOT[1], C.Z_SLOT) < -M)] = "grille_plug (slots)"
    # cap: the black skirt disc (declared deviation D2) stands 0.7 below the cap inside the ray start distance -> measure the cap
    # with the nearest-point distance to T_spodok instead of a ray (unsigned)
    cap_tree = mesh("T_spodok").tree
    for i in np.where(zone == "cap")[0]:
        dev[i] = cap_tree.find_nearest(Vector(P[i]))[3]
    zs = {}
    for zn in sorted(set(zone.tolist())):
        m = zone == zn
        cov = m & np.isfinite(dev)
        zs[zn] = dict(points=int(m.sum()), covered=int(cov.sum()), dev_min=round(float(np.nanmin(dev[m])), 4) if cov.any() else None,
                      dev_max=round(float(np.nanmax(dev[m])), 4) if cov.any() else None,
                      n_abs_over_0p05=int((np.abs(dev[cov]) > 0.05).sum()))
    strict = np.isin(zone, ["white", "cap"])
    bad = strict & (~np.isfinite(dev) | (np.abs(dev) > 0.05))
    res["exterior_vs_T3"] = dict(
        reference="/tmp/claude-0/gapwf/fin/T3/shape.py: prof / section (the approved visual model), grid 0.5 mm, outward normals from finite differences",
        points=int(len(P)), zones=zs, strict_zones=["white", "cap"], n_bad_strict=int(bad.sum()),
        bad_samples=[dict(p=[round(float(v), 2) for v in P[i]], dev=None if not np.isfinite(dev[i]) else round(float(dev[i]), 3),
                          part=None if part[i] < 0 else nm[part[i]]) for i in np.where(bad)[0][:40]],
        dev_strict_min=round(float(np.nanmin(dev[strict])), 4), dev_strict_max=round(float(np.nanmax(dev[strict])), 4),
        ok=bool(bad.sum() == 0),
        note="dev = signed distance of the STL surface from the T3 surface along the T3 normal (+ = outside); in the cap zone the "
             "unsigned nearest distance to T_spodok (the skirt disc D2 hangs below it).  Strict zones must be "
             "covered within 0.05 mm; the other zones are the declared deviations D1 - D3, the seams, the door notch, the "
             "shoulder joints, the plug gaps / grille slots and the underside")
    say("K8a:", json.dumps({k: (v["points"], v["covered"], v["dev_min"], v["dev_max"], v["n_abs_over_0p05"]) for k, v in zs.items()}))
    say("K8a: bad strict", int(bad.sum()), res["exterior_vs_T3"]["bad_samples"][:5])
    # ---------------------------------------------------------------- (b) see-through from 26 viewpoints
    scene = [r["name"] for r in PARTS if r["group"] != "Z"] + ["golier_prstenec", "golier_kotuc", "krk_predna_polovica", "krk_zadna_polovica"]
    tree, own, nm = tree_of(scene)
    lo = np.min([mesh(n).bb[:3] for n in scene], axis=0); hi = np.max([mesh(n).bb[3:] for n in scene], axis=0)
    corners = np.array([[a, b, c] for a in (lo[0], hi[0]) for b in (lo[1], hi[1]) for c in (lo[2], hi[2])])
    PITCH = 0.25
    DEPTH = 3.0            # a missed ray is a see-through when its line runs deeper than this below the exterior (wall 2.2 + lip gap)
    # analytic exterior as a BVH (sections every 0.25 mm of drop, 360 points) for exact depths
    drops = np.arange(0.0, C.DROP_END + 1e-6, 0.25)
    secs = [C.outer_section(float(dd), 360) for dd in drops]
    EV = np.concatenate(secs + [np.array([[0.0, 0.0, C.TOP], [0.0, 0.0, C.Z_BOT]])])
    EF = []
    ns, nc = len(secs), 360
    for a_ in range(ns - 1):
        for b_ in range(nc):
            p0_, p1_ = a_ * nc + b_, a_ * nc + (b_ + 1) % nc
            EF.append((p0_, p1_, p1_ + nc)); EF.append((p0_, p1_ + nc, p0_ + nc))
    for b_ in range(nc):
        EF.append((ns * nc, b_, (b_ + 1) % nc)); EF.append((ns * nc + 1, (ns - 1) * nc + b_, (ns - 1) * nc + (b_ + 1) % nc))
    ext_tree = BVHTree.FromPolygons(EV.tolist(), EF, all_triangles=True, epsilon=0.0)
    views = []
    tot_rays = tot_through = 0
    for i in (-1, 0, 1):
        for j in (-1, 0, 1):
            for k in (-1, 0, 1):
                if (i, j, k) == (0, 0, 0):
                    continue
                d = np.array([i, j, k], float); d /= np.linalg.norm(d)
                up = np.array([0.0, 0.0, 1.0]) if abs(d[2]) < 0.9 else np.array([0.0, 1.0, 0.0])
                u = np.cross(up, d); u /= np.linalg.norm(u); v = np.cross(d, u)
                cu, cv, cd = corners @ u, corners @ v, corners @ d
                gu = np.arange(cu.min() - 0.5, cu.max() + 0.5, PITCH); gv = np.arange(cv.min() - 0.5, cv.max() + 0.5, PITCH)
                L = cd.max() - cd.min() + 20.0
                o0 = d * (cd.max() + 10.0)
                dv = Vector(-d)
                miss = []
                n_hit = 0
                for a in gu:
                    oa = o0 + u * a
                    for b in gv:
                        o = oa + v * b
                        if tree.ray_cast(Vector(o), dv, L)[0] is None:
                            miss.append(o)
                        else:
                            n_hit += 1
                miss = np.array(miss)
                # a missed ray is a see-through when its line crosses the CAVITY (radial depth > 4 inside the exterior, 3 below the
                # top / above the lower edge): light would pass through the torso
                through = []
                if len(miss):
                    cand = []
                    t = np.arange(0.0, L, 0.5)
                    for blk in range(0, len(miss), 4000):
                        O = miss[blk:blk + 4000]
                        Q = O[:, None, :] - d[None, None, :] * t[None, :, None]
                        Qf = Q.reshape(-1, 3)
                        r = np.hypot(Qf[:, 0], Qf[:, 1]); th = np.arctan2(Qf[:, 1], Qf[:, 0])
                        zz = Qf[:, 2]
                        g = C.outer_r(np.clip(zz, C.Z_BOT, C.TOP), th) - r
                        inside_cav = (g > 4.0) & (zz < C.TOP - 3.0) & (zz > C.Z_WHITE + 3.0)
                        any_in = inside_cav.reshape(len(O), len(t)).any(1)
                        cand += [o for o in O[any_in]]
                    # exact depth below the exterior for the candidates (the radial proxy overestimates it on the shoulder shelf)
                    for o in cand:
                        dmax = 0.0
                        for tt in t:
                            q = o - d * tt
                            if C.Z_BOT < q[2] < C.TOP and math.hypot(q[0], q[1]) < float(C.outer_r(q[2], math.atan2(q[1], q[0]))):
                                dmax = max(dmax, ext_tree.find_nearest(Vector(q))[3])
                        if dmax > DEPTH:
                            through.append(o)
                views.append(dict(dir=[i, j, k], rays=int(len(gu) * len(gv)), hits=n_hit, see_through=len(through),
                                  samples=[[round(float(q), 2) for q in (o - d * (o @ d))] for o in through[:6]]))
                tot_rays += len(gu) * len(gv); tot_through += len(through)
                say(f"K8b: view {i:2d} {j:2d} {k:2d}: rays {len(gu) * len(gv)}, hits {n_hit}, see-through {len(through)}")
    res["see_through_26"] = dict(views=views, rays=int(tot_rays), see_through=int(tot_through), pitch=PITCH, ok=bool(tot_through == 0),
                                 scene="all T / P / L parts at rest + collar ring, collar disc and neck of variant B (no head, no base dummy)",
                                 note="orthographic ray grid 0.25 mm from the 26 directions (+-1, +-1, +-1 combinations); a ray that meets no part "
                                      "while its line runs more than 3.0 mm below the exterior surface (true distance; wall 2.2, seam groove floor at 2.35) "
                                      "is a see-through")
    res["time_s"] = round(time.time() - T0, 1)
    res["stl_md5"] = {n: REC[n]["stl"]["md5"] for n in scene if n in REC}
    json.dump(res, open(os.path.join(WORK, "bl_K8.json"), "w"), indent=1)
    say("K8 done: exterior ok", res["exterior_vs_T3"]["ok"], "| see-through", tot_through)


if "K8" in ARGS:
    run_K8()


# =====================================================================================================================
# K4  opposing-face thickness scan of every printed part
# =====================================================================================================================
def run_K4():
    out = {}
    for r in PARTS:
        if not r["printed"]:
            continue
        n = r["name"]
        m = mesh(n)
        T = m.V[m.F]
        nrm, area = TM.tri_normals(T)
        h = float(np.clip(math.sqrt(area.sum() / 60000.0), 0.25, 0.8))
        S, I = TM.pulled_samples(T, h, 0.05)                  # no sample exactly on an edge (grazing rays along a neighbour face)
        N = nrm[I]
        tree = m.tree
        th = np.full(len(S), np.nan); anti = np.zeros(len(S))
        for i in range(len(S)):
            nv = Vector(N[i])
            hit = tree.ray_cast(Vector(S[i]) - nv * 2e-3, -nv, 80.0)
            if hit[0] is not None:
                th[i] = hit[3] + 2e-3
                hn = nrm[hit[2]]
                anti[i] = float(N[i] @ hn)
        opp = np.isfinite(th) & (anti < -0.9)                    # opposing (near-parallel) faces = walls / plates / webs / floors
        t = th[opp]; P = S[opp]
        if len(t) == 0:
            out[n] = dict(samples=int(len(S)), opposing=0)
            continue
        # thinnest reading per 2.5 mm cell AND per 0.1 mm thickness class (so a declared thin floor cannot hide a different thin
        # wall in the same cell); EVERY cell below 1.62 is reported (the largest material limit is 1.6) - no truncation
        cells = {}
        for q, tt in zip(P[t < 2.0], t[t < 2.0]):
            key = tuple(np.floor(q / 2.5).astype(int).tolist()) + (int(tt / 0.1 + 1e-6),)
            if key not in cells or tt < cells[key][0]:
                cells[key] = (float(tt), [round(float(v), 2) for v in q])
        thin = sorted(cells.values())
        n_lim = sum(1 for c in thin if c[0] < 1.62)
        thin = thin[:max(n_lim, 400)]
        hist = {f"<{b}": int((t < b).sum()) for b in (0.4, 0.6, 0.8, 1.0, 1.2, 1.6, 2.0)}
        out[n] = dict(mat=r["mat"], samples=int(len(S)), pitch=round(h, 3), opposing=int(opp.sum()), min=round(float(t.min()), 3),
                      p001=round(float(np.percentile(t, 0.1)), 3), p01=round(float(np.percentile(t, 1)), 3), median=round(float(np.median(t)), 3),
                      hist=hist, thin_cells=[dict(t=round(a, 3), at=b) for a, b in thin],
                      wedge_min=round(float(np.nanmin(th[np.isfinite(th) & ~opp])), 3) if (np.isfinite(th) & ~opp).any() else None)
        say(f"K4 {n:18s} {r['mat']:11s} samples {len(S):6d} opposing {int(opp.sum()):6d} min {out[n]['min']:.3f} p01 {out[n]['p01']:.3f} median {out[n]['median']:.3f} {hist}")
    json.dump(dict(parts=out, time_s=round(time.time() - T0, 1),
                   method="every printed part: surface samples (grid on every triangle, pulled 0.05 off the edges, about 60 000 per part); ray along the inward normal to the next "
                          "face of the same part; a reading counts as a thickness when the two faces are opposed (normals within 26 deg of "
                          "anti-parallel); thin_cells = thinnest reading per 2.5 mm cell and 0.1 mm thickness class, all of them below 1.62"),
              open(os.path.join(WORK, "bl_K4.json"), "w"), indent=1)
    say("K4 done")


if "K4" in ARGS:
    run_K4()


# =====================================================================================================================
# K5  free play of the bought parts in their seats (how much oversize / shift the seat accepts)
# =====================================================================================================================
K5_SEATS = {   # bought part: (neighbours that form the seat, what)  - rev. 2
    "servo_J1": (["T_spodok", "T_paluba", "T_most"], "STS3215 (corner pads + window, cradle, shims under T_most)"),
    "servo_pan": (["T_spodok", "T_paluba", "T_stred"], "STS3032 on its 2 posts"),
    "servo_zdvih": (["P_drziak_serva", "P_sachta"], "MG90S in the closed pocket"),
    "lozisko_6805": (["T_spodok"], "6805-2RS in the D37.15 seat"),
    "reproduktor": (["T_stred", "T_drziak_repro", "T_mriezka"], "speaker D28 x 5"),
    "DPS_riadenie": (["T_spodok", "T_paluba"], "carrier on its standoffs + rest pad"),
    "menic": (["T_spodok", "T_bok_P"], "buck converter"),
    "zosilnovac": (["T_spodok", "T_bok_L"], "MAX98357A"),
    "kondenzator": (["T_spodok"], "470 uF D8 x 11.5 on its pedestal"),
    "DPS_led": (["T_drziak_led", "T_stred"], "LED strip"),
    "pastorok_J1": (["T_spodok", "lozisko_6805"], "J1 pinion in its passage"),
    "pastorok_pan": (["T_paluba", "T_spodok", "T_stred", "T_most"], "pan pinion"),
    "koleso_pan": (["T_cap", "ptfe_cap", "ptfe_podlozka", "T_paluba", "T_most"], "36T gear on the taped boss / PTFE washer"),
    "DPS_krk": (["L_pata"], "neck board in the foot slot"),
}


def run_K5():
    out = {}
    axes = {"-x": (-1, 0, 0), "+x": (1, 0, 0), "-y": (0, -1, 0), "+y": (0, 1, 0), "-z": (0, 0, -1), "+z": (0, 0, 1)}
    for n, (nb, what) in K5_SEATS.items():
        m = mesh(n)
        T = m.V[m.F]
        nrm, _ = TM.tri_normals(T)
        S, I = TM.sample(T, 0.4)
        N = nrm[I]
        tree, own, nm = tree_of(nb)
        play = {}
        for key, d in axes.items():
            dv = Vector(d); da = np.array(d, float)
            best = (20.0, None, None)
            sel = np.where(N @ da > 0.3)[0]
            for i in sel:
                hit = tree.ray_cast(Vector(S[i]) - dv * 1e-3, dv, best[0])
                if hit[0] is not None and hit[3] - 1e-3 < best[0]:
                    best = (max(0.0, hit[3] - 1e-3), nm[own[hit[2]]], [round(float(v), 2) for v in S[i]])
            play[key] = dict(free=round(best[0], 3) if best[1] else None, against=best[1], at=best[2])
        out[n] = dict(what=what, bbox=[round(float(v), 3) for v in m.bb], seat_parts=nb, play=play)
        say(f"K5 {n:14s} " + "  ".join(f"{k} {v['free']} ({v['against']})" for k, v in play.items()))
    json.dump(dict(parts=out, time_s=round(time.time() - T0, 1),
                   method="free play: rays from the surface samples (0.4 mm) of the bought part along +-x / +-y / +-z (faces looking that way) "
                          "to the first face of its seat parts; None = nothing within 20 mm.  Foam pads, tapes and the part's own screws "
                          "are not in the seat list, so the play is the space the seat leaves for tolerance / compliance"),
              open(os.path.join(WORK, "bl_K5.json"), "w"), indent=1)
    say("K5 done")


if "K5" in ARGS:
    run_K5()


# =====================================================================================================================
# K7  assembly: withdrawal sweeps, tool channels, hardware access
# =====================================================================================================================
def run_K7():
    import re
    import t4_assembly as A
    import t4_common as C
    GRP = {r["name"]: r["group"] for r in PARTS}
    GRP.update(B_GROUP)
    AX = {"+x": (1, 0, 0), "-x": (-1, 0, 0), "+y": (0, 1, 0), "-y": (0, -1, 0), "+z": (0, 0, 1), "-z": (0, 0, -1)}
    SHR = 0.05
    _pv, _smp = {}, {}

    def turns(name):
        return GRP.get(name) in ("P", "L") or name in A.TURNS_WITH_PAN

    def posed(name, pan):
        key = (name, pan if turns(name) else 0.0)
        if key not in _pv:
            _pv[key] = TM.rotz(mesh(name).V, pan) if (pan and turns(name)) else mesh(name).V
        return _pv[key]

    def smp(name, pan, h):
        key = (name, pan if turns(name) else 0.0, h)
        if key not in _smp:
            _smp[key] = TM.inset_samples(posed(name, pan), mesh(name).F, h, SHR)
        return _smp[key]

    def build(names, pan):
        Vs, Fs, own, off = [], [], [], 0
        for i, n in enumerate(names):
            V = posed(n, pan); F = mesh(n).F
            Vs.append(V); Fs.append(F + off); own.append(np.full(len(F), i, np.int32)); off += len(V)
        if not Vs:
            return None, None, []
        return (BVHTree.FromPolygons(np.concatenate(Vs).tolist(), np.concatenate(Fs).tolist(), all_triangles=True, epsilon=0.0),
                np.concatenate(own), list(names))

    def dirvec(d, frame, pan):
        v = np.array(AX[d], float)
        return TM.rotz(v[None], pan)[0] if (frame == "stage" and pan) else v

    def sweep(move, legs, ctx, pan, frame, fits, skip=None, only=None):
        """skip: {part: (box, reason)} samples of that part inside the box are not swept (flexible lead / plug);
        only: (part, box) sweep ONLY the samples of that part inside the box (path of the flexible piece itself)"""
        skip = skip or {}
        tree, own, nm = build(ctx, pan)
        if tree is None:
            return []
        col = {}
        segs, offs = [], np.zeros(3)
        for d, L in legs:
            v = dirvec(d, frame, pan); segs.append((offs.copy(), v, float(L))); offs = offs + v * L

        def rec(a, b, t, p, way):
            e = col.setdefault((a, b), dict(n=0, t_min=1e9, at=None, way=way))
            e["n"] += 1
            if t < e["t_min"]:
                e["t_min"] = t; e["at"] = [round(float(q), 2) for q in p]

        def inbox(Q, bx):
            return (Q[:, 0] > bx[0]) & (Q[:, 0] < bx[1]) & (Q[:, 1] > bx[2]) & (Q[:, 1] < bx[3]) & (Q[:, 2] > bx[4]) & (Q[:, 2] < bx[5])

        for name in move:
            O = smp(name, pan, 0.6)
            if name in skip:
                O = O[~inbox(O, skip[name][0])]
            if only is not None:
                if name != only[0]:
                    continue
                O = O[inbox(O, only[1])]
            for o0, v, L in segs:
                dv = Vector(v)
                for p in (O + o0).tolist():
                    hit = tree.ray_cast(Vector(p), dv, L)
                    if hit[0] is not None:
                        rec(name, nm[own[hit[2]]], hit[3], p, "moving -> static")
        if only is not None or skip:
            mtree = None                                     # the reverse test needs the whole rigid mesh: not valid with a clipped part
        else:
            mtree, mown, mnm = build(move, pan)
        mbb = np.concatenate([np.min([posed(n, pan).min(0) for n in move], 0), np.max([posed(n, pan).max(0) for n in move], 0)])
        for o0, v, L in segs:
            lo = mbb[:3] + o0 + np.minimum(v * L, 0) - 0.3; hi = mbb[3:] + o0 + np.maximum(v * L, 0) + 0.3
            dv = Vector(-v)
            for b in ([] if mtree is None else ctx):
                Vb = posed(b, pan)
                if np.any(Vb.min(0) > hi) or np.any(Vb.max(0) < lo):
                    continue
                Sb = smp(b, pan, 0.8)
                m = np.all((Sb > lo) & (Sb < hi), axis=1)
                for p in (Sb[m] - o0).tolist():
                    hit = mtree.ray_cast(Vector(p), dv, L)
                    if hit[0] is not None:
                        rec(mnm[mown[hit[2]]], b, hit[3], np.array(p) + o0, "static -> moving")
        out = []
        for (a, b), e in sorted(col.items(), key=lambda kv: -kv[1]["n"]):
            decl = any(re.match(pa, a) and re.match(pb, b) for pa, pb in fits)
            out.append(dict(moving=a, static=b, rays=e["n"], first_at_mm=round(e["t_min"], 3), at=e["at"], way=e["way"], declared_fit=bool(decl)))
        return out

    def hardware_open(h, d, ctx, pan):
        V = posed(h, pan); c = V.mean(0)
        if d.startswith("axis:"):
            w, U = np.linalg.eigh(np.cov((V - c).T))
            v = U[:, 0]
            hint = np.array(AX[d[5:]], float)
            v = v if v @ hint > 0 else -v
        else:
            v = np.array(AX[d], float)
        a = np.cross(v, [0.0, 0.0, 1.0] if abs(v[2]) < 0.9 else [1.0, 0.0, 0.0]); a /= np.linalg.norm(a); b = np.cross(v, a)
        R = 0.5 * min(np.ptp(V @ a), np.ptp(V @ b))
        tree, own, nm = build([n for n in ctx if n != h], pan)
        hits = {}
        for k in range(7):
            p = c if k == 0 else c + 0.3 * R * (math.cos(k * math.pi / 3) * a + math.sin(k * math.pi / 3) * b)
            hit = tree.ray_cast(Vector(p), Vector(v), 120.0) if tree is not None else (None,)
            if hit[0] is not None:
                hits[nm[own[hit[2]]]] = round(min(hits.get(nm[own[hit[2]]], 1e9), hit[3]), 2)
        return dict(part=h, dir=[round(float(q), 3) for q in v], open=not hits, blocked_by=hits)

    def tool_channel(s, d, ctx, pan, frame, tool_d=4.5):
        v = dirvec(d, frame, pan)
        Vs = posed(s, pan); c = Vs.mean(0)
        start = c + v * (float((Vs @ v).max()) - float(c @ v) + 0.05)
        a = np.cross(v, [0.0, 0.0, 1.0] if abs(v[2]) < 0.9 else [1.0, 0.0, 0.0]); a /= np.linalg.norm(a); b = np.cross(v, a)
        names = [n for n in ctx if n != s]
        tree, own, nm = build(names, pan)
        rings = tuple(r for r in (0.0, 0.5, 0.65, 1.0, 1.5, 2.0, 2.25) if r <= tool_d / 2 + 1e-9)
        ring_hits = {}
        for r in rings:
            hh = {}
            for k in range(1 if r == 0 else 24):
                p = start + r * (math.cos(k * math.pi / 12) * a + math.sin(k * math.pi / 12) * b)
                hit = tree.ray_cast(Vector(p), Vector(v), 150.0) if tree is not None else (None,)
                if hit[0] is not None:
                    n_ = nm[own[hit[2]]]
                    hh[n_] = round(min(hh.get(n_, 1e9), hit[3]), 2)
            ring_hits[r] = hh
        free_r = 0.0
        for r in rings:
            if ring_hits[r]:
                break
            free_r = r
        blockers = ring_hits[rings[-1]]
        own_seat = {}
        for n_, dist in blockers.items():
            t = mesh(n_).tree if not (pan and turns(n_)) else build([n_], pan)[0]
            dmin = min(t.find_nearest(Vector(q))[3] for q in Vs[:: max(1, len(Vs) // 200)].tolist())
            own_seat[n_] = bool(dmin < 0.3 and dist < 16.0)
        full = not blockers and all(not ring_hits[r] for r in rings)
        recess = (not full) and all(own_seat.get(n_, False) for n_ in blockers) and all(
            all(own_seat.get(n_, False) for n_ in ring_hits[r]) for r in rings) and not ring_hits[0.0] and not ring_hits[1.0]
        return dict(screw=s, tool_dir=[round(float(q), 3) for q in v], pan=pan, tool_d=tool_d, free_D4p5=bool(full), own_recess_only=bool(recess),
                    free_ring_radius=free_r, blocked_by={str(r): h for r, h in ring_hits.items() if h}, ok=bool(full or recess))

    def door_swing(move, ctx, pan, sw):
        tree, own, nm = build(ctx, pan)
        V = np.concatenate([mesh(n).V for n in move]); F = []
        off = 0; pown = []
        for i, n in enumerate(move):
            F.append(mesh(n).F + off); off += len(mesh(n).V); pown.append(np.full(len(mesh(n).F), i, np.int32))
        F = np.concatenate(F).tolist(); pown = np.concatenate(pown)
        z_top = C.Z_DOOR + C.DOOR[1] / 2
        xh = C.OBAL["DOOR_HOOK"]["x"]
        y_out = C.y_surface(xh, z_top, 1)
        best = None
        y_mid = C.y_surface(0.0, z_top, 1)                  # the top edge bulges out in plan: the door pivots on its centre
        for za in (z_top, z_top + 0.2):
            for ya in (y_mid + 0.25, y_mid, y_mid - 0.5, y_out, y_out - 1.0, y_out - 2.2):
                def hit(t, s, q):
                    a = math.radians(t); ca, sa = math.cos(a), math.sin(a)
                    W = V.copy()
                    y, z = V[:, 1] - ya, V[:, 2] - za
                    W[:, 1] = ya + y * ca - z * sa + s * sa + q
                    W[:, 2] = za + y * sa + z * ca - s * ca
                    ov = BVHTree.FromPolygons(W.tolist(), F, all_triangles=True, epsilon=0.0).overlap(tree)
                    if not ov:
                        return None
                    return dict(deg=t, slide=s, pull=q, pairs=[list(p) for p in sorted({(move[pown[i]], nm[own[j]]) for i, j in ov})[:6]], tri_pairs=len(ov))

                # free swing range of this hinge line
                th_free, first = 0.0, hit(0.0, 0.0, 0.0)
                if first is None:
                    for t in np.arange(sw["step_deg"], sw["max_deg"] + 1e-6, sw["step_deg"]):
                        first = hit(float(t), 0.0, 0.0)
                        if first is not None:
                            break
                        th_free = float(t)
                cand = dict(hinge_y=round(ya, 2), hinge_z=round(za, 2), free_swing_deg=th_free, swing_stopped_by=first)
                # from any open angle: slide along the door plane (hooks out from behind the wall), then pull out
                for t_open in [t for t in (40.0, 35.0, 30.0, 25.0, 20.0, 14.0, 10.0, 6.0) if t <= th_free + 1e-6]:
                    for slide in (0.0, 2.5, sw["slide"]):
                        bad = None
                        for s_ in np.arange(0.5, slide + 1e-6, 0.5):
                            bad = hit(t_open, float(s_), 0.0)
                            if bad:
                                break
                        if bad is None:
                            for q_ in np.arange(0.5, sw["pull"] + 1e-6, 0.5):
                                bad = hit(t_open, slide, float(q_))
                                if bad:
                                    break
                        if bad is None:
                            cand.update(open_deg=t_open, slide=slide, pull=sw["pull"])
                            return dict(ok=True, hinge=cand, note="discrete poses: swing in 0.5 deg steps about an X-parallel axis through the centre "
                                                                  "of the door's top edge, then (optional slide along the door plane and) pull +Y "
                                                                  "in 0.5 mm steps; BVH triangle overlap = 0 in every pose; mounting = the reverse")
                        cand.setdefault("failed_open_angles", []).append(dict(open_deg=t_open, slide=slide, first_collision=bad))
                if best is None or th_free > best[0]:
                    best = (th_free, cand)
        return dict(ok=False, hinge=best[1], note="no hinge axis among the candidates gives a collision-free swing")

    present, steps, problems = [], [], []
    names_all = [r["name"] for r in PARTS] + B_MATE
    for st in A.STEPS:
        pan = float(st.get("pan", 0.0)); bench = bool(st.get("bench", False)); frame = st.get("frame")
        move = list(st.get("move", []))
        ctx0 = list(st["ctx"]) if isinstance(st.get("ctx"), list) else list(present)
        if st.get("remove"):
            ctx0 = [n for n in ctx0 if n not in st["remove"]]
        if st.get("base"):
            ctx0 += [b for b in st["base"] if b not in ctx0]
        ctx = [n for n in ctx0 if n not in A.FLEX and n not in move]
        r = dict(id=st["id"], text=st["text"], bench=bench, pan=pan, move=move, n_ctx=len(ctx))
        t1 = time.time()
        if move and "legs" in st:
            used, col = None, None
            for legs in [st["legs"]] + list(st.get("alt_legs", [])):
                col = sweep(move, legs, ctx, pan, frame, st.get("fits", []), st.get("skip_box"))
                used = legs
                if not [c for c in col if not c["declared_fit"]]:
                    break
            r["legs"] = [[d, L] for d, L in used]; r["frame"] = frame or "B"
            r["collisions"] = [c for c in col if not c["declared_fit"]]
            r["declared_fits_met"] = [c for c in col if c["declared_fit"]]
            if st.get("skip_box"):
                r["not_swept"] = {k: v[1] for k, v in st["skip_box"].items()}
            if st.get("snap"):
                r["snap_fit"] = True
            if r["collisions"]:
                problems.append(f"step {st['id']}: " + "; ".join(f"{c['moving']} x {c['static']} ({c['rays']} rays, first at {c['first_at_mm']} mm)" for c in r["collisions"][:6]))
        for part, bx, d, L, why in st.get("flex_sweep", []):
            col = [c for c in sweep([part], [(d, L)], ctx, pan, frame, [], None, (part, bx))]
            r.setdefault("flex_sweeps", []).append(dict(part=part, what=why, dir=d, dist=L, collisions=col))
            if col:
                problems.append(f"step {st['id']}: {why}: " + "; ".join(f"{c['moving']} x {c['static']} at {c['first_at_mm']} mm" for c in col[:4]))
        if "swing" in st:                                    # rev. 2: no hooks, the door goes straight in (legs) - kept for rev. 1 data
            r["swing"] = door_swing(move, ctx, pan, st["swing"])
            if not r["swing"]["ok"]:
                problems.append(f"step {st['id']}: door swing / slide collides: {json.dumps(r['swing']['hinge'])[:700]}")
        r["hardware"] = [hardware_open(h, d, ctx, pan) for h, d in st.get("hardware", [])]
        for h in r["hardware"]:
            if not h["open"]:
                problems.append(f"step {st['id']}: {h['part']} is not accessible along {h['dir']}: {h['blocked_by']}")
        sc_ctx = ctx + move + [h for h, _ in st.get("hardware", [])] + [x[0] for x in st.get("screws", [])] + list(st.get("hardware_with", []))
        r["screws"] = [tool_channel(x[0], x[1], [n for n in sc_ctx if n not in A.FLEX], pan, frame, x[2] if len(x) > 2 else 4.5)
                       for x in st.get("screws", [])]
        for s in r["screws"]:
            if not s["ok"]:
                problems.append(f"step {st['id']}: no tool channel for {s['screw']}: {s['blocked_by']}")
        r["time_s"] = round(time.time() - t1, 1)
        steps.append(r)
        say(f"K7 step {st['id']:4s} move {len(move):2d} ctx {len(ctx):3d} collisions {len(r.get('collisions', []))} "
            f"hardware {sum(1 for h in r['hardware'] if not h['open'])}/{len(r['hardware'])} blocked, screws "
            f"{sum(1 for s in r['screws'] if not s['ok'])}/{len(r['screws'])} blocked  ({r['time_s']} s)")
        r["service"] = bool(st.get("service"))
        arrive = st.get("base", []) + move + st.get("with_parts", []) + [x[0] for x in st.get("screws", [])] + [h for h, _ in st.get("hardware", [])] \
            + list(st.get("hardware_with", []))
        if st.get("service"):
            pass                                             # service rows do not change the main sequence
        elif not bench:
            for n in arrive:
                if n not in present:
                    present.append(n)
        else:
            r["bench_parts"] = arrive
    bench_parts = {n for s in steps if s["bench"] for n in s.get("bench_parts", [])}
    never = [n for n in names_all if n not in present]
    not_swept = [n for n in present if n not in {m for s in steps for m in s["move"]} and n not in bench_parts
                 and n not in {x["screw"] for s in steps for x in s["screws"]} and n not in {h["part"] for s in steps for h in s["hardware"]}]
    json.dump(dict(steps=steps, problems=problems, parts_never_mounted=never, parts_arriving_without_a_path_test=not_swept, flexible=A.FLEX,
                   time_s=round(time.time() - T0, 1), stl_md5={n: REC[n]["stl"]["md5"] for n in REC},
                   method="every step: surface samples of the moving parts (vertices + 0.6 mm grid, moved 0.05 mm inside the solid) are cast along "
                          "the withdrawal legs against one BVH of all parts present at that step, and samples (0.8 mm) of the present parts "
                          "inside the swept box are cast back against the moving parts; any hit is a collision unless the pair is a declared "
                          "fit of the step.  Screws: 24 rays on the D4.5 circle + rings r 2.0 / 1.5 / 1.0 + axis from the head top along "
                          "the tool direction for 150 mm; 'own_recess_only' = the only obstacle is the screw's own counterbore in the part it "
                          "clamps (hex key / bit instead of the D4.5 shaft).  Hardware: 7 rays from the part centre along its withdrawal "
                          "direction with only the host present.  Door: discrete swing / slide / pull poses with BVH overlap."),
              open(os.path.join(WORK, "bl_K7.json"), "w"), indent=1)
    say("K7 done:", len(problems), "problems")
    for p in problems:
        say("   ", p)
    say("   never mounted:", never, "| no path test:", not_swept)


if "K7" in ARGS:
    run_K7()
