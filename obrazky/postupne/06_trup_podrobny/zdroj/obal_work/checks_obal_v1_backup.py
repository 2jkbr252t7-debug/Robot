"""module-level checks of OBAL (CAD side).  Mesh-side checks: obal_work/mesh_checks.py (Blender).
  O1 valid single solids, volume > 0, bounding boxes against the spec
  O2 interference among the OBAL parts (common volume of every bbox-overlapping pair; intended fits listed)
  O3 zones: OBAL parts vs the envelopes of RAM / PAN (static clearance, pan sweep -85..85 x lift 0..20, PAN_ENV + 1.0,
     lowering of T_stred with its front stack over the tower envelopes)
  O4 seats vs bought parts (nominal / seat / clearance) + a few sizes measured on the geometry
  O5 inside the shell: every internal part against the inner surface (wall 2.2) and the exterior
Usage: /opt/venv/cad/bin/python checks_obal.py [--skip-o2]   -> checks_obal.json (merges obal_work/mesh_checks.json if present)"""
import sys, os, json, math, time, itertools
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import t4_common as C
import t4_obal as O

T0 = time.time()
bd = C._bd()
R = O.build()
names = list(R)
OUT = {}


def bbox(s):
    b = s.bounding_box()
    return np.array([b.min.X, b.max.X, b.min.Y, b.max.Y, b.min.Z, b.max.Z])


BB = {n: bbox(R[n]["shape"]) for n in names}
# ------------------------------------------------------------------------------------------------------------ O1
o1 = {}
for n in names:
    s = R[n]["shape"]
    rec = dict(valid=bool(s.is_valid), n_solids=len(s.solids()), volume_mesh=round(C.mesh_volume(s, 0.02, 0.1), 2),
               bbox=[round(float(v), 3) for v in BB[n]])
    exp = O.BBOX_EXPECT.get(n)
    rec["ok"] = rec["valid"] and rec["n_solids"] == 1 and rec["volume_mesh"] > 0
    if exp:
        rec["bbox_expected"] = exp
        rec["ok"] = bool(rec["ok"] and all(e is None or abs(a - e) <= 0.06 for a, e in zip(rec["bbox"], exp)))
    o1[n] = rec
OUT["O1_solids"] = dict(parts=o1, all_ok=all(v["ok"] for v in o1.values()))
print("O1", OUT["O1_solids"]["all_ok"], [k for k, v in o1.items() if not v["ok"]], round(time.time() - T0, 1), flush=True)

# ------------------------------------------------------------------------------------------------------------ O2
INTENDED = [   # (prefix a, prefix b, what) - pairs whose overlap / contact is a designed fit
    ("skrutka_led", "T_stred", "thread-forming M2 in pilot D1.7 (thread engagement)"),
    ("skrutka_repro", "T_stred", "thread-forming M2 in pilot D1.7 (thread engagement)"),
    ("vlozka_stred", "T_stred", "insert OD 3.5 glued in hole D3.6 (no overlap expected)"),
]


def intended(a, b):
    for pa, pb, what in INTENDED:
        if (a.startswith(pa) and b.startswith(pb)) or (b.startswith(pa) and a.startswith(pb)):
            return what
    return None


if "--skip-o2" not in sys.argv:
    pairs = []
    for a, b in itertools.combinations(names, 2):
        A, B = BB[a], BB[b]
        if all(A[2 * k] < B[2 * k + 1] - 1e-6 and B[2 * k] < A[2 * k + 1] - 1e-6 for k in range(3)):
            pairs.append((a, b))
    res = []
    for a, b in pairs:
        t = time.time()
        try:
            c = R[a]["shape"] & R[b]["shape"]
            sol = c.solids() if c is not None else []
            v = float(sum(s.volume for s in sol))
        except Exception as ex:
            v = float("nan"); print("   common failed", a, b, type(ex).__name__, flush=True)
        it = intended(a, b)
        res.append(dict(a=a, b=b, common_mm3=round(v, 4), intended=it, time_s=round(time.time() - t, 1)))
        flag = "" if (v < 0.01 or it) else "   <-- INTERFERENCE"
        if v >= 1e-4 or time.time() - t > 20:
            print(f"   {a:18s} x {b:18s} common {v:9.4f} mm3 ({time.time() - t:.1f} s) {it or ''}{flag}", flush=True)
    bad = [r for r in res if not (r["common_mm3"] < 0.01) and not r["intended"]]
    OUT["O2_interference"] = dict(pairs_tested=len(res), pairs=res, not_intended=bad, all_ok=len(bad) == 0,
                                  note="common volume of every bbox-overlapping pair; < 0.01 mm3 counts as contact")
    print("O2", len(res), "pairs, interferences:", [(r["a"], r["b"], r["common_mm3"]) for r in bad], round(time.time() - T0, 1), flush=True)

# ------------------------------------------------------------------------------------------------------------ meshes
MESH = {}


def pts_of(n, h=0.6):
    """mesh vertices + centroids of a part, refined so that no triangle edge is longer than about h"""
    if n in MESH:
        return MESH[n]
    V, T = C.mesh_of(R[n]["shape"], 0.03, 0.15)
    a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    P = [V, (a + b + c) / 3]
    L = np.maximum.reduce([np.linalg.norm(a - b, axis=1), np.linalg.norm(b - c, axis=1), np.linalg.norm(c - a, axis=1)])
    big = L > h
    if big.any():
        a, b, c, L = a[big], b[big], c[big], L[big]
        k = np.minimum(np.ceil(L / h).astype(int), 40)
        for kk in np.unique(k):
            m = k == kk
            for i in range(kk + 1):
                for j in range(kk + 1 - i):
                    u, v = i / kk, j / kk
                    P.append(a[m] * (1 - u - v) + b[m] * u + c[m] * v)
    MESH[n] = np.concatenate(P)
    return MESH[n]


def env_dist(e, P):
    """signed distance of points to an envelope (- inside)"""
    if e["kind"] == "box":
        lo = np.array([e["x"][0], e["y"][0], e["z"][0]]); hi = np.array([e["x"][1], e["y"][1], e["z"][1]])
        q = np.maximum(lo - P, P - hi)
        return np.linalg.norm(np.maximum(q, 0), axis=1) + np.minimum(q.max(1), 0)
    ax = "xyz".index(e["axis"]); o = [i for i in range(3) if i != ax]
    c = e["c"]
    rr = np.hypot(P[:, o[0]] - c[0], P[:, o[1]] - c[1])
    u = P[:, ax]
    qa = np.maximum(e["rng"][0] - u, u - e["rng"][1])
    qr = rr - e["r"]
    d = np.hypot(np.maximum(qa, 0), np.maximum(qr, 0)) + np.minimum(np.maximum(qa, qr), 0)
    if e.get("ri", 0) > 0:                              # hollow: distance to the wall material only
        qi = e["ri"] - rr
        d2 = np.maximum.reduce([qa, qr, qi])
        d = np.where(qi > 0, np.hypot(np.maximum(qa, 0), qi), d)
        d = np.where((qa <= 0) & (qr <= 0) & (qi <= 0), d2, d)
    if e["name"] in ("kanal_fpc_pan", "fpc_pan", "paluba_zad"):     # only the back half exists
        d = np.where(P[:, 1] < 0, np.maximum(d, -P[:, 1]), d)
    return d


ENV = C.envelopes()
INTERIOR = [n for n in names]
# ------------------------------------------------------------------------------------------------------------ O3
t3 = time.time()
o3 = dict(static=[], pan=[], pan_env=[], lowering=[])
# declared interfaces (contact or designed overlap with a RAM envelope)
DECL = {("T_klb_L", "stlp_L_naboj"): "joint neck seats on the boss face x 38.4; key 1.4 into the boss slot",
        ("T_klb_P", "stlp_P_naboj"): "joint neck seats on the boss face x -38.4; key 1.4 into the boss slot",
        ("T_klb_L", "stlp_L_doraz"): "neck r 11.0 inside the stop ring r 11.6",
        ("T_klb_P", "stlp_P_doraz"): "neck r 11.0 inside the stop ring r 11.6",
        ("T_bok_L", "stlp_L_doraz"): "seat flange rests on the stop ring face x 39.1",
        ("T_bok_P", "stlp_P_doraz"): "seat flange rests on the stop ring face x -39.1",
        ("T_stred", "pastorok_pan"): "pinion is mounted after T_stred (lowering only)"}
for tag in ("L", "P"):
    for i in (1, 2, 3):
        DECL[(f"skrutka_klb_{tag}{i}", f"stlp_{tag}_naboj")] = "F8 screw into the insert of the column boss"
        DECL[(f"skrutka_klb_{tag}{i}", f"stlp_{tag}_doraz")] = "F8 screw passes inside the stop ring"
    for i in (1, 2):
        DECL[(f"pruzina_klb_{tag}{i}", f"stlp_{tag}_doraz")] = "springs sit on the column spigot inside the ring"
# static envelopes of RAM
for n in names:
    P = pts_of(n)
    for e in ENV:
        if e["owner"] != "ram" or e["group"] != "T":
            continue
        d = env_dist(e, P)
        i = int(np.argmin(d))
        if d[i] < 2.0:
            o3["static"].append(dict(part=n, env=e["name"], clearance=round(float(d[i]), 3), at=[round(float(v), 2) for v in P[i]],
                                     declared=DECL.get((n, e["name"]))))
# pan stage / lift envelopes swept
pans = np.arange(-85, 86, 5.0); lifts = np.arange(0, 20.01, 2.5)
for n in names:
    P = pts_of(n)
    # only points that can be reached: r <= 36.5 and z >= -47 (everything else is far from the pan stage)
    m = (np.hypot(P[:, 0], P[:, 1]) < 37.0) & (P[:, 2] > -47.0)
    if not m.any():
        continue
    Q = P[m]
    for e in ENV:
        if e["owner"] != "pan":
            continue
        best = (9e9, None, None, None)
        for pan in pans:
            Qr = C.np_rot_z(Q, -pan)                      # rotate the static points into the stage frame
            for lf in (lifts if e["group"] == "L" else [0.0]):
                Qs = Qr.copy(); Qs[:, 2] -= lf
                if e["name"] == "kluka_obalka":
                    d = env_dist(e, Qs); d = np.where(Qs[:, 1] > C.Y_LIFT + C.CRANK["tip_r"], np.maximum(d, Qs[:, 1] - C.Y_LIFT - C.CRANK["tip_r"]), d)
                else:
                    d = env_dist(e, Qs)
                i = int(np.argmin(d))
                if d[i] < best[0]:
                    best = (float(d[i]), pan, lf, Q[i])
        if best[0] < 3.0:
            o3["pan"].append(dict(part=n, env=e["name"], group=e["group"], clearance=round(best[0], 3), pan=best[1], lift=best[2],
                                  at=[round(float(v), 2) for v in best[3]]))
# PAN_ENV table + 1.0 (front sector: r >= 29.7 for z -40.5 .. -2)
for n in names:
    P = pts_of(n)
    r = np.hypot(P[:, 0], P[:, 1]); az = np.degrees(np.arctan2(P[:, 1], P[:, 0])) % 360
    worst = (9e9, None)
    for z0, z1, rm in C.PAN_ENV:
        m = (P[:, 2] >= z0) & (P[:, 2] <= z1)
        if not m.any():
            continue
        lim = np.full(m.sum(), rm)
        front = (az[m] > C.PAN_FRONT[0]) & (az[m] < C.PAN_FRONT[1]) & (P[m, 2] > -40.5) & (P[m, 2] < -2.0)
        lim = np.where(front, np.minimum(lim, C.PAN_FRONT_R), lim)
        d = r[m] - lim
        i = int(np.argmin(d))
        if d[i] < worst[0]:
            worst = (float(d[i]), P[m][i])
    if worst[1] is not None and worst[0] < 3.0:
        o3["pan_env"].append(dict(part=n, margin_to_PAN_ENV=round(worst[0], 3), at=[round(float(v), 2) for v in worst[1]], ok=bool(worst[0] >= 1.0 - 1e-3)))
# lowering of T_stred (+ front stack) straight down over the tower envelopes (all RAM group-T envelopes of the tower,
# without the parts mounted later: pan pinion + hub)
LOWER = ["T_stred", "T_svetlovod", "T_mriezka", "T_drziak_led", "T_drziak_repro", "reproduktor", "tesnenie_repro", "DPS_led"] + \
        [n for n in names if n.startswith(("skrutka_led", "skrutka_repro", "vlozka_stred", "magnet_zarubna"))]
LATER = ("pastorok_pan", "pastorok_pan_naboj")
for n in LOWER:
    P = pts_of(n)
    for e in ENV:
        if e["owner"] != "ram" or e["group"] != "T" or e["name"] in LATER:
            continue
        zmax = e["z"][1] if e["kind"] == "box" else (e["rng"][1] if e["axis"] == "z" else e["c"][1] + e["r"])
        zmin = e["z"][0] if e["kind"] == "box" else (e["rng"][0] if e["axis"] == "z" else e["c"][1] - e["r"])
        if zmax < C.Z_BOT + 0.5:
            continue                                  # under the cap: not passed
        m = P[:, 2] < zmax - 1e-6
        if not m.any():
            continue
        Q = P[m].copy()
        Q[:, 2] = np.clip(Q[:, 2], zmin, zmax)        # plan-view distance = 3-D distance with z moved into the envelope range
        d = env_dist(e, Q)
        i = int(np.argmin(d))
        if d[i] < 3.0:
            o3["lowering"].append(dict(part=n, env=e["name"], plan_clearance=round(float(d[i]), 3), at=[round(float(v), 2) for v in P[m][i]],
                                       ok=bool(d[i] >= C.TOWER_CLEAR - 1e-3)))
o3["static_min_not_declared"] = min([s["clearance"] for s in o3["static"] if not s["declared"]], default=None)
o3["pan_min"] = min([s["clearance"] for s in o3["pan"]], default=None)
o3["pan_env_min"] = min([s["margin_to_PAN_ENV"] for s in o3["pan_env"]], default=None)
o3["lowering_min"] = min([s["plan_clearance"] for s in o3["lowering"]], default=None)
o3["ok"] = bool((o3["static_min_not_declared"] is None or o3["static_min_not_declared"] >= 0.0) and
                (o3["pan_min"] is None or o3["pan_min"] >= 1.0 - 1e-3) and
                (o3["pan_env_min"] is None or o3["pan_env_min"] >= 1.0 - 1e-3) and
                (o3["lowering_min"] is None or o3["lowering_min"] >= C.TOWER_CLEAR - 1e-3))
OUT["O3_zones"] = o3
print(f"O3 ok {o3['ok']}: static min {o3['static_min_not_declared']}, pan sweep min {o3['pan_min']}, PAN_ENV margin min {o3['pan_env_min']}, "
      f"lowering min {o3['lowering_min']}  ({time.time() - t3:.1f} s)", flush=True)
for key in ("static", "pan", "pan_env", "lowering"):
    for s in sorted(o3[key], key=lambda q: list(q.values())[2] if key != "pan_env" else q["margin_to_PAN_ENV"])[:8]:
        print("    ", key, s, flush=True)

# ------------------------------------------------------------------------------------------------------------ O4 seats
def meas_r(n, axis_pt, ax, rng, pick="min", rmax=None):
    """min / max radius of the mesh points of part n about an axis within a range along it"""
    P = pts_of(n)
    k = "xyz".index(ax); o = [i for i in range(3) if i != k]
    m = (P[:, k] >= rng[0]) & (P[:, k] <= rng[1])
    rr = np.hypot(P[m, o[0]] - axis_pt[0], P[m, o[1]] - axis_pt[1])
    if rmax is not None:
        rr = rr[rr < rmax]
    return round(float(rr.min() if pick == "min" else rr.max()), 3)


seats = []


def seat(what, part_size, seat_size, clear, tol, measured=None):
    seats.append(dict(feature=what, part=part_size, seat=seat_size, clearance=clear, tolerance=tol, measured=measured))


seat("collar ring golier_prstenec in the T_stred bore (z -2..4)", "D56.50", "D56.70 +0.10/0", "0.10 radial glue seam", "ring B (finished)",
     dict(bore_r_min=meas_r("T_stred", (0, 0), "z", (-9.5, 3.5), "min")))
seat("pan journal in the bore (z -10.5..-4.5)", "D56.40 (resin D56.14 + PTFE tape)", "D56.70", "0.15 radial running", "0.10..0.20")
seat("speaker in the 3-boss seat", "D28.0 x 5.0", f"D{O.SPK_SEAT_D} between 3 bosses, depth 5.0 (y -36.6..-31.6)", "0.15 radial", "speaker +-0.3 -> seat scallops can be filed",
     dict(seat_r_min=min(meas_r("T_stred", (0, C.SPEAKER["z"]), "y", (-36.4, -31.7), "min", rmax=15.5), 99)))
seat("LED PCB in the holder rebate", "30.0 x 4.0 x 0.8", f"{2 * O.HOLDER['rebate'][0]} x {2 * O.HOLDER['rebate'][1]} x {O.HOLDER['rebate'][2]}", "0.15 / 0.10 per side", "+-0.2")
seat("door magnets (8) in pockets", "D5.0 x 2.0", "D5.1 x 2.1", "0.05 radial, 0.1 glue", "N52 +-0.05")
seat("shoulder magnets (6) in pockets", "D3.0 x 2.0", "D3.1 x 2.1", "0.05 radial, 0.1 glue", "+-0.05")
seat("insert M2.5 x 4 (OD 3.5) in T_stred bosses", "D3.5 x 4.0", "D3.6 x 4.3 + pilot D2.8", "0.05 radial (glued)", "-")
seat("light guide plug in the bar opening", "30.6 x 3.8", "31.0 x 4.2", "0.20 all round", "-")
seat("grille plug in the slot", "20.6 x 2.8", "21.0 x 3.2", "0.20 all round", "-")
seat("door in the opening", "56.0 x 60.0 r10", "56.5 x 60.5 r10.25", "0.25 all round", "seam 0.5 +-0.1 visually = 0.25")
seat("joint body in the socket bore", "D27.0", "D28.0", "0.50 radial (seam)", "-",
     dict(socket_r_min=meas_r("T_bok_L", (C.SH_Y, C.SH_Z), "x", (41.0, 44.0), "min"), joint_r_max=meas_r("T_klb_L", (C.SH_Y, C.SH_Z), "x", (41.0, 49.0), "max")))
seat("joint neck in the seat-flange hole", "D22.0", "D22.5", "0.25 radial", "-",
     dict(hole_r_min=meas_r("T_bok_L", (C.SH_Y, C.SH_Z), "x", (39.2, 40.5), "min")))
seat("bush in the joint", "D8.0 f7 x 14.75, flange D10 x 2", "D8.05 / recess D10.2", "0.025 / 0.10 radial", "f7 / H8 reamed after printing")
seat("disc springs 2x DIN 2093 10 x 5.2 x 0.4 on the column spigot", "OD 10.0, ID 5.2, 2 x 0.5 working", "recess D10.2, x 41.0..42.0", "0.10 radial", "shim 0.1 to tune 0.25 N.m")
seat("M2 x 10 (F8) through the joint", "D2.0, head D3.8", "D2.3 clearance, counterbore D4.2 to x 45.0", "0.15 / 0.20 radial", "-")
seat("M2 x 6 thread-forming (F13)", "D2.0", f"pilot D1.7 x {O.PILOT_LED} (LED) / 5.0 (speaker)", "thread forming", "-")
OUT["O4_seats"] = seats
print("O4 seats", len(seats), [s["measured"] for s in seats if s["measured"]], flush=True)

# ------------------------------------------------------------------------------------------------------------ O5 inside
o5 = {}
OUTSIDE_OK = ("T_klb_", "T_puzdro_", "skrutka_klb_", "magnet_klb_", "pruzina_klb_")
SHELLS = ("T_stred", "T_bok_L", "T_bok_P", "T_dvere", "T_svetlovod", "T_mriezka")
for n in names:
    P = pts_of(n)
    ins = C.inside_outer(P)
    d = C.dist_outer(P)
    sd = np.where(ins, d, -d)                      # signed depth below the exterior (+ inside)
    rec = dict(min_depth_below_exterior=round(float(sd.min()), 3))
    if n not in SHELLS and not n.startswith(OUTSIDE_OK):
        rec["min_clearance_to_inner_surface"] = round(float(sd.min() - C.WALL), 3)
        rec["ok"] = bool(sd.min() - C.WALL >= -0.02)
    elif n in SHELLS:
        rec["ok"] = bool(sd.min() >= -0.03)
    else:
        rec["ok"] = True; rec["note"] = "declared: passes through the socket"
    o5[n] = rec
OUT["O5_inside"] = dict(parts=o5, all_ok=all(v["ok"] for v in o5.values()))
print("O5", OUT["O5_inside"]["all_ok"], {k: v for k, v in o5.items() if not v["ok"]}, flush=True)

mc = os.path.join(HERE, "obal_work", "mesh_checks.json")
if os.path.exists(mc):
    OUT.update(json.load(open(mc)))
OUT["time_s"] = round(time.time() - T0, 1)
json.dump(OUT, open(os.path.join(HERE, "checks_obal.json"), "w"), indent=1, ensure_ascii=False, default=float)
print("written checks_obal.json", OUT["time_s"], "s")
