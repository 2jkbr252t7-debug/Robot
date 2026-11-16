"""module-level checks of OBAL.  Works on the exported STLs (absolute deflection 0.01) + parts_obal.json; the BREP side
(is_valid, one solid, bounding boxes) is recorded by t4_obal.py at export time and only summarised here.
  O1 valid single solids, watertight STL, volume > 0, bounding boxes against the spec        (parts_obal.json)
  O2 interference among the OBAL parts                                                        (obal_work/mesh_checks.py, BVH)
  O3 zones: OBAL parts vs the envelopes of RAM / PAN (static clearance, pan sweep -85..85 x lift 0..20, PAN_ENV + 1.0,
     lowering of T_stred with its front stack over the tower envelopes)
  O4 seats vs bought parts (nominal / seat / clearance) + sizes measured on the meshes
  O5 inside the shell: every internal part against the inner surface (wall 2.2); shells against the exterior
  M1 M2 M3 S1 F1 X1  mesh checks (Blender), merged from obal_work/mesh_checks.json
  X2 X3  straight-line assembly against the real RAM meshes, merged from obal_work/slide_checks.json (slide_checks.py)
Usage: /opt/venv/cad/bin/python checks_obal.py   -> checks_obal.json"""
import sys, os, json, math, time
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import t4_common as C
import t4_obal as O

T0 = time.time()
recs = O.load_parts()
names = [r["name"] for r in recs]
REC = {r["name"]: r for r in recs}
OUT = dict(module="obal", generated=time.strftime("%Y-%m-%d %H:%M:%S"), stl_deflection_mm=O.STL_LIN)

# ------------------------------------------------------------------------------------------------------------ O1
o1 = {}
for r in recs:
    ok = bool(r["valid"] and r["n_solids"] == 1 and r["volume_mesh"] > 0 and r.get("watertight") and r.get("bbox_ok", True))
    o1[r["name"]] = dict(valid=r["valid"], n_solids=r["n_solids"], watertight=r.get("watertight"), volume_mesh=r["volume_mesh"],
                         bbox=r["bbox"], bbox_expected=r.get("bbox_expected"), stl_tris=r.get("stl", {}).get("tris"), step=r.get("step"), ok=ok)
OUT["O1_solids"] = dict(parts=o1, all_ok=all(v["ok"] for v in o1.values()), n_parts=len(o1),
                        step_skipped=[r["name"] for r in recs if not r.get("step")])
print("O1", OUT["O1_solids"]["all_ok"], [k for k, v in o1.items() if not v["ok"]], round(time.time() - T0, 1), flush=True)

# ------------------------------------------------------------------------------------------------------------ meshes
MESH = {}


def pts_of(n, h=0.7):
    """STL vertices + centroids of a part, refined so that no triangle edge is longer than about h"""
    if (n, h) in MESH:
        return MESH[(n, h)]
    V, T = O.read_stl(os.path.join(HERE, "stl", n + ".stl"))
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
    MESH[(n, h)] = np.concatenate(P)
    return MESH[(n, h)]


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


def radial_excess(V):
    zz = np.clip(V[:, 2], C.Z_BOT, C.TOP)
    a = np.interp(C.TOP - zz, C.PD, C.PA); b_ = np.interp(C.TOP - zz, C.PD, C.PB); n_ = np.interp(C.TOP - zz, C.PD, C.PN)
    f = (np.abs(V[:, 0]) / a) ** n_ + (np.abs(V[:, 1]) / b_) ** n_
    rad = np.hypot(V[:, 0], V[:, 1]) * (1 - f ** (-1 / n_))
    return np.where(V[:, 2] > C.TOP + 1e-6, np.maximum(rad, V[:, 2] - C.TOP), rad)


ENV = C.envelopes()
mc_path = os.path.join(HERE, "obal_work", "mesh_checks.json")
MC = json.load(open(mc_path)) if os.path.exists(mc_path) else {}
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
BOXNOTE = ("ENVELOPE boxes overlap by the spec itself: the socket tube r <= 16 (|x| >= 39.1) and the joint body r 13.5 are OBAL zones, "
           "the column box stlp_* reaches x 42 / z -30.  The real column ribs of T_ram stand at y <= -7.4 and y >= 13.4, where the "
           "tube (r 16 about y 3, z -17) is above z -29.2; measured on the meshes in X1 (ram_column_gap)")
for tag in ("L", "P"):
    DECL[(f"T_bok_{tag}", f"stlp_{tag}")] = BOXNOTE
    DECL[(f"T_klb_{tag}", f"stlp_{tag}")] = BOXNOTE
    for i in (1, 2, 3):
        DECL[(f"skrutka_klb_{tag}{i}", f"stlp_{tag}_naboj")] = "F8 screw into the insert of the column boss"
        DECL[(f"skrutka_klb_{tag}{i}", f"stlp_{tag}_doraz")] = "F8 screw passes inside the stop ring"
    for i in (1, 2):
        DECL[(f"pruzina_klb_{tag}{i}", f"stlp_{tag}_doraz")] = "springs sit on the column spigot inside the ring"
        DECL[(f"pruzina_klb_{tag}{i}", f"stlp_{tag}_naboj")] = "springs sit on the column spigot (x 41.0 .. 42.0)"
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
# pan stage / lift envelopes swept.  Declared fit: the bore of T_stred (r 28.35, z >= -10.5 incl. the 0.5 lead-in) is the
# bearing of the journal r 28.20 and the passage of the stage (well corners r 28.09) - those points are skipped.
pans = np.arange(-85, 86, 5.0); lifts = np.arange(0, 20.01, 2.5)
BORE_ENV = ("sachta", "cap_otocny", "vrch_stola", "golier_kotuc")
sweep_min = {}


def _sweep():
    pan_list = []
    for n in names:
        P = pts_of(n)
        rr = np.hypot(P[:, 0], P[:, 1])
        m = (rr < 37.0) & (P[:, 2] > -47.0) & (radial_excess(P) < -1.0)      # the outer skin (2.2 further out) is skipped
        if not m.any():
            continue
        Q0 = P[m]; r0 = rr[m]
        bore = (r0 <= C.R_BORE + 0.62) & (Q0[:, 2] >= C.Z_BORE_BOT - 0.01) if n == "T_stred" else np.zeros(len(Q0), bool)
        for e in ENV:
            if e["owner"] != "pan":
                continue
            Q = Q0[~bore] if e["name"] in BORE_ENV else Q0
            best = (9e9, None, None, None)
            for pan in pans:
                Qr = C.np_rot_z(Q, -pan)                      # rotate the static points into the stage frame
                for lf in (lifts if e["group"] == "L" else [0.0]):
                    Qs = Qr.copy(); Qs[:, 2] -= lf
                    d = env_dist(e, Qs)
                    if e["name"] == "kluka_obalka":
                        d = np.where(Qs[:, 1] > C.Y_LIFT + C.CRANK["tip_r"], np.maximum(d, Qs[:, 1] - C.Y_LIFT - C.CRANK["tip_r"]), d)
                    i = int(np.argmin(d))
                    if d[i] < best[0]:
                        best = (float(d[i]), float(pan), float(lf), Q[i])
            sweep_min[n] = min(sweep_min.get(n, 9e9), best[0])
            if best[0] < 3.0:
                pan_list.append(dict(part=n, env=e["name"], group=e["group"], clearance=round(best[0], 3), pan=best[1], lift=best[2],
                                      at=[round(float(v), 2) for v in best[3]]))
    return pan_list


# the sweep is the slow part (about 3 min): its result is cached against the time stamps of the STL files and of t4_common.py
SWC = os.path.join(HERE, "obal_work", "o3_sweep_cache.json")
stamp = [round(max(os.path.getmtime(os.path.join(HERE, "stl", n + ".stl")) for n in names), 3), round(os.path.getmtime(os.path.join(HERE, "t4_common.py")), 3), len(names)]
if os.path.exists(SWC) and json.load(open(SWC)).get("stamp") == stamp:
    _c = json.load(open(SWC)); o3["pan"] = _c["pan"]; sweep_min = _c["sweep_min"]
    print("   (pan sweep taken from obal_work/o3_sweep_cache.json - STL files unchanged)", flush=True)
else:
    o3["pan"] = _sweep()
    json.dump(dict(stamp=stamp, pan=o3["pan"], sweep_min=sweep_min), open(SWC, "w"), default=float)
# PAN_ENV table + 1.0.  Front sector (azimuth 236..336): only the well (r 28.09) and the FPC lift loop (r 28.7) sweep there,
# static parts may come in to r 29.7.  The spec states this for z -40.5 .. -2; the well walls end at -41.3 and the back floor
# (r <= 28.1) at -41.9, so the same limit is applied down to z -41.9 (below it PAN_ENV is r 15.9).
Z_FRONT = (-41.9, -2.0)
TOLF = 0.02                     # tolerance of the formal check = 2 x STL deflection (cut faces lying exactly on PAN_ENV + 1.0)
for n in names:
    P = pts_of(n)
    r = np.hypot(P[:, 0], P[:, 1]); az = np.degrees(np.arctan2(P[:, 1], P[:, 0])) % 360
    worst = (9e9, None, None); bad_az = []
    for z0, z1, rm in C.PAN_ENV:
        m = (P[:, 2] > z0 + 0.02) & (P[:, 2] < z1 - 0.02)     # faces lying exactly in a row boundary belong to the row they bound
        if n == "T_stred":
            m &= ~((r <= C.R_BORE + 0.62) & (P[:, 2] >= C.Z_BORE_BOT - 0.01))        # the bore itself (declared fit)
        if not m.any():
            continue
        lim = np.full(m.sum(), rm)
        front = (az[m] > C.PAN_FRONT[0]) & (az[m] < C.PAN_FRONT[1]) & (P[m, 2] > Z_FRONT[0]) & (P[m, 2] < Z_FRONT[1])
        lim = np.where(front, np.minimum(lim, C.PAN_FRONT_R), lim)
        d = r[m] - lim
        i = int(np.argmin(d))
        bad_az += list(az[m][d < 1.0 - TOLF])
        if d[i] < worst[0]:
            worst = (float(d[i]), P[m][i], float(az[m][i]))
    if worst[1] is not None and worst[0] < 3.0:
        rec = dict(part=n, margin_to_PAN_ENV=round(worst[0], 3), at=[round(float(v), 2) for v in worst[1]], azimuth=round(worst[2], 1),
                   ok=bool(worst[0] >= 1.0 - TOLF))
        if not rec["ok"]:
            rec["sweep_clearance_to_PAN_envelopes"] = round(sweep_min.get(n, 9e9), 3)
            rec["azimuth_span_of_the_points_inside"] = [round(float(min(bad_az)), 1), round(float(max(bad_az)), 1)]
            rec["declared"] = (f"points at azimuth {min(bad_az):.1f} .. {max(bad_az):.1f} deg, just outside the formal front sector {C.PAN_FRONT} "
                               f"(where r >= 29.7 is allowed); nothing of the lift module reaches these azimuths (ear end r 32.0 up to azimuth "
                               f"213.4, servo corner r 33.4 beyond 336.4); direct sweep against every PAN / LIFT envelope: "
                               f"{rec['sweep_clearance_to_PAN_envelopes']} mm")
            rec["ok_by_sweep"] = bool(sweep_min.get(n, 9e9) >= 1.0 - 1e-3)
        o3["pan_env"].append(rec)
# lowering of T_stred (+ front stack) straight down over the tower envelopes (all RAM group-T envelopes of the tower,
# without the parts mounted later: pan pinion + hub)
LOWER = ["T_stred", "T_svetlovod", "T_mriezka", "T_drziak_led", "T_drziak_repro", "reproduktor", "tesnenie_repro", "DPS_led"] + \
        [n for n in names if n.startswith(("skrutka_led", "skrutka_repro", "vlozka_stred", "magnet_zarubna", "vyvod_"))]
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
o3["static_declared"] = sorted({(s["part"], s["env"], s["clearance"]) for s in o3["static"] if s["declared"] and s["clearance"] < 0.05})
o3["pan_min"] = min([s["clearance"] for s in o3["pan"]], default=None)
o3["pan_env_min_formal"] = min([s["margin_to_PAN_ENV"] for s in o3["pan_env"]], default=None)
o3["pan_env_exceptions"] = [dict(part=s["part"], margin=s["margin_to_PAN_ENV"], azimuth=s.get("azimuth_span_of_the_points_inside"), sweep=s.get("sweep_clearance_to_PAN_envelopes"))
                            for s in o3["pan_env"] if not s["ok"]]
o3["pan_env_ok"] = all(s["ok"] or s.get("ok_by_sweep") for s in o3["pan_env"])
o3["lowering_min"] = min([s["plan_clearance"] for s in o3["lowering"]], default=None)
o3["declared_bore_fit"] = "T_stred bore r 28.35 (z >= -10.5): journal r 28.20 (0.15 running), well corners r 28.09 pass it during assembly"
o3["front_rule_z"] = Z_FRONT
o3["ok"] = bool((o3["static_min_not_declared"] is None or o3["static_min_not_declared"] >= 0.0) and
                (o3["pan_min"] is None or o3["pan_min"] >= 1.0 - 1e-3) and o3["pan_env_ok"] and
                (o3["lowering_min"] is None or o3["lowering_min"] >= C.TOWER_CLEAR - 1e-3))
OUT["O3_zones"] = o3
print(f"O3 ok {o3['ok']}: static min (not declared) {o3['static_min_not_declared']}, pan sweep min {o3['pan_min']}, PAN_ENV formal min "
      f"{o3['pan_env_min_formal']} (exceptions {len(o3['pan_env_exceptions'])}, ok {o3['pan_env_ok']}), lowering min {o3['lowering_min']}  "
      f"({time.time() - t3:.1f} s)", flush=True)
for key in ("static", "pan", "pan_env", "lowering"):
    for s in sorted(o3[key], key=lambda q: list(q.values())[2] if key != "pan_env" else q["margin_to_PAN_ENV"])[:8]:
        print("    ", key, {k: v for k, v in s.items() if k != "declared"}, "DECL" if s.get("declared") else "", flush=True)


# ------------------------------------------------------------------------------------------------------------ O4 seats
def meas_r(n, axis_pt, ax, rng, pick="min", rmax=None, rmin=None):
    """min / max radius of the mesh points of part n about an axis within a range along it"""
    P = pts_of(n)
    k = "xyz".index(ax); o = [i for i in range(3) if i != k]
    m = (P[:, k] >= rng[0]) & (P[:, k] <= rng[1])
    rr = np.hypot(P[m, o[0]] - axis_pt[0], P[m, o[1]] - axis_pt[1])
    if rmax is not None:
        rr = rr[rr < rmax]
    if rmin is not None:
        rr = rr[rr > rmin]
    return round(float(rr.min() if pick == "min" else rr.max()), 3)


seats = []


def seat(what, part_size, seat_size, clear, tol, measured=None, ok=True):
    seats.append(dict(feature=what, part=part_size, seat=seat_size, clearance=clear, tolerance=tol, measured=measured, ok=bool(ok)))


SH = (C.SH_Y, C.SH_Z)
b = meas_r("T_stred", (0, 0), "z", (-9.5, 3.5), "min")
seat("collar ring golier_prstenec in the T_stred bore (z -2..4)", "D56.50", "D56.70 +0.10/0", "0.10 radial glue seam", "ring B (finished)",
     dict(bore_r_min=b, nominal=C.R_BORE), abs(b - C.R_BORE) <= 0.02)
seat("pan journal in the bore (z -10.5..-4.5)", "D56.40 (resin D56.14 + PTFE tape 0.13)", "D56.70", "0.15 radial running", "0.10..0.20; ream / sand "
     "the bore after curing, the tape is left off if the print is tight", dict(bore_r_min=b), abs(b - C.R_BORE) <= 0.02)
s_ = meas_r("T_stred", (0, C.SPEAKER["z"]), "y", (-36.4, -31.7), "min", rmax=15.5)
seat("speaker D28 x 5.0 between the 3 boss scallops", "D28.0 +-0.3 x 5.0", f"D{O.SPK_SEAT_D} x 5.0 (y -36.6 .. -31.6), foam gasket 0.85 behind",
     "0.15 radial", "scallops can be filed; gasket takes +-0.3 in depth", dict(seat_r_min=s_, speaker_r=C.SPEAKER["d"] / 2), s_ >= C.SPEAKER["d"] / 2 + 0.1)
seat("LED PCB in the holder rebate", "30.0 x 4.0 x 0.8 (+-0.2)", f"{2 * O.HOLDER['rebate'][0]} x {2 * O.HOLDER['rebate'][1]} x {O.HOLDER['rebate'][2]}",
     "0.15 / 0.10 per side", "+-0.2",
     dict(pcb_bbox=REC["DPS_led"]["bbox"], holder_bbox=REC["T_drziak_led"]["bbox"]))
seat("door magnets (8) in pockets", "D5.0 x 2.0", "D5.1 x 2.1", "0.05 radial, 0.1 glue", "N52 +-0.05; air gap door / frame 0.2")
seat("shoulder magnets (6) in pockets", "D3.0 x 2.0", "D3.1 x 2.1", "0.05 radial, 0.1 glue", "+-0.05")
seat("insert M2.5 x 4 (OD 3.5) in the 4 T_stred bosses", "D3.5 x 4.0", "D3.6 x 4.3 + pilot D2.8 x 2.6", "0.05 radial (glued)", "-")
seat("light guide plug in the bar opening", "30.6 x 3.8", "31.0 x 4.2", "0.20 all round", "-")
seat("grille plug in the slot", "20.6 x 2.8", "21.0 x 3.2", "0.20 all round", "-")
sw = MC.get("M3_exterior", {}).get("seam_widths_measured")
seat("door in the opening", "56.0 x 60.0 r10", "56.5 x 60.5 r10.25", "0.25 all round", "0.25 +-0.1", dict(measured_on_mesh=sw))
so = meas_r("T_bok_L", SH, "x", (41.0, 44.0), "min"); jo = meas_r("T_klb_L", SH, "x", (41.0, 49.0), "max")
seat("joint body in the socket bore", "D27.0", "D28.0", "0.50 radial (visible seam)", "+-0.1", dict(socket_r_min=so, joint_r_max=jo, gap=round(so - jo, 3)),
     0.4 <= so - jo <= 0.6)
ho = meas_r("T_bok_L", SH, "x", (39.2, 40.5), "min"); ne = meas_r("T_klb_L", SH, "x", (38.6, 40.5), "max", rmax=11.6)
seat("joint neck in the seat-flange hole", "D22.0", "D22.5", "0.25 radial", "-", dict(hole_r_min=ho, neck_r_max=ne, gap=round(ho - ne, 3)), 0.2 <= ho - ne <= 0.3)
bo = meas_r("T_klb_L", SH, "x", (46.0, 56.0), "min"); bs = meas_r("T_puzdro_L", SH, "x", (46.0, 56.0), "max")
seat("bush in the joint", "D8.0 f7 x 14.75, flange D10 x 2", "D8.05 / recess D10.2", "0.025 / 0.10 radial", "f7 / H8: ream D8 after printing",
     dict(bore_r_min=bo, bush_r_max=bs), bo >= bs)
seat("disc springs 2 x DIN 2093 10 x 5.2 x 0.4 on the column spigot", "OD 10.0, ID 5.2, 2 x 0.5 working height", "recess D10.2, x 41.0 .. 42.0",
     "0.10 radial", "0.1 shims to tune the 0.25 N.m slip torque")
seat("M2 x 10 (F8) through the joint", "D2.0, head D3.8", "D2.3 clearance, counterbore D4.2 to x 45.0", "0.15 / 0.20 radial", "-")
seat("M2 x 6 thread-forming (F13)", "D2.0", f"pilot D1.7 x {O.PILOT_LED} (LED bosses) / 5.0 (speaker bosses)", "thread forming", "skin behind the pilot >= 1.3")
# front lip relief (LIP_RELIEF, pan-servo tabs): remaining wall at the lower edge z -81, worst at |x| = 16.75
xr = C.LIP_RELIEF["x"][1]
yo = abs(C.y_surface(xr, C.Z_WHITE, -1)); ny = abs(float(O.normal(np.array([[xr, -yo, C.Z_WHITE]]))[0][1]))
Pb_ = pts_of("T_stred"); mb_ = (np.abs(Pb_[:, 2] - C.Z_WHITE) < 0.01) & (Pb_[:, 1] < 0) & (np.abs(Pb_[:, 0]) <= xr - 0.15)
yi_meas = float(np.abs(Pb_[mb_, 1]).min())
seat("front lip relief for the pan-servo tab corners (lowering of T_stred)", "tab corner y -27.04, x +-16.25", f"lip inner face cut to y -{C.LIP_RELIEF['y_min']} "
     f"for |x| <= {xr}, z < -79.5", "0.5 in plan (TOWER_CLEAR)", "servo +-0.3 by its slotted tab holes",
     dict(inner_y_measured_at_z_m81=round(yi_meas, 3), outer_y_at_x_16p75=round(yo, 3), remaining_wall_horizontal=round(yo - C.LIP_RELIEF["y_min"], 3),
          remaining_wall_normal_approx=round((yo - C.LIP_RELIEF["y_min"]) * ny, 3), spec_estimate=1.5, local_minimum_allowed=C.WALL_LOCAL),
     abs(yi_meas - C.LIP_RELIEF["y_min"]) < 0.02 and (yo - C.LIP_RELIEF["y_min"]) * ny >= C.WALL_LOCAL)
OUT["O4_seats"] = dict(seats=seats, all_ok=all(s["ok"] for s in seats))
print("O4 seats", len(seats), OUT["O4_seats"]["all_ok"], [(s["feature"][:28], s["measured"]) for s in seats if s["measured"] and not s["ok"]], flush=True)


# ------------------------------------------------------------------------------------------------------------ O5 inside
o5 = {}
OUTSIDE_OK = ("T_klb_", "T_puzdro_", "skrutka_klb_", "magnet_klb_", "pruzina_klb_")
SHELLS = ("T_stred", "T_bok_L", "T_bok_P", "T_dvere", "T_svetlovod", "T_mriezka")
D5 = {"skrutka_led_1": "screw tip sits in the pilot of the LED boss, which runs 0.7 into the wall (skin 1.3 left)",
      "skrutka_led_2": "screw tip sits in the pilot of the LED boss, which runs 0.7 into the wall (skin 1.3 left)",
      "tesnenie_repro": "foam gasket lies on the inner wall (cut with the inner surface)"}
for n in names:
    P = pts_of(n)
    if n in SHELLS:
        V, _ = O.read_stl(os.path.join(HERE, "stl", n + ".stl"))
        ex = float(radial_excess(V).max())
        o5[n] = dict(max_radial_excess_over_exterior=round(ex, 4), ok=bool(ex <= 0.03))
        continue
    ins = C.inside_outer(P)
    d = C.dist_outer(P)
    sd = np.where(ins, d, -d)                      # signed depth below the exterior (+ inside)
    rec = dict(min_depth_below_exterior=round(float(sd.min()), 3))
    if n.startswith(OUTSIDE_OK):
        rec["ok"] = True; rec["note"] = "declared: shoulder joint, passes through the socket"
    else:
        rec["min_clearance_to_inner_surface"] = round(float(sd.min() - C.WALL), 3)
        rec["ok"] = bool(sd.min() - C.WALL >= -0.02)
        if not rec["ok"] and n in D5:
            rec["declared"] = D5[n]; rec["ok"] = bool(sd.min() >= C.WALL_LOCAL)
    o5[n] = rec
OUT["O5_inside"] = dict(parts=o5, all_ok=all(v["ok"] for v in o5.values()))
print("O5", OUT["O5_inside"]["all_ok"], {k: v for k, v in o5.items() if not v["ok"] or v.get("declared")}, flush=True)

SL = os.path.join(HERE, "obal_work", "slide_checks.json")
if os.path.exists(SL):
    OUT.update(json.load(open(SL)))            # X2 / X3: straight-line assembly against the real RAM meshes (slide_checks.py)

OUT.update(MC)
summ = dict(O1=OUT["O1_solids"]["all_ok"], O3=o3["ok"], O4=OUT["O4_seats"]["all_ok"], O5=OUT["O5_inside"]["all_ok"])
for k, key, f in (("O2", "O2_interference", "all_ok"), ("M1", "M1_watertight", "all_ok"), ("M2", "M2_wall", "ok"), ("M3", "M3_exterior", "ok"),
                  ("S1", "S1_seam_backing", "ok")):
    summ[k] = MC.get(key, {}).get(f, "not run")
for k, key in (("X2_info", "X2_lowering_vs_ram_meshes"), ("X3_info", "X3_cap_slide_vs_meshes")):
    summ[k] = OUT.get(key, {}).get("ok", "not run")
OUT["summary"] = summ
OUT["time_s"] = round(time.time() - T0, 1)
json.dump(OUT, open(os.path.join(HERE, "checks_obal.json"), "w"), indent=1, ensure_ascii=False, default=float)
print("summary", summ)
print("written checks_obal.json", OUT["time_s"], "s")
