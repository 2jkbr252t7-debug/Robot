"""module-level checks of OBAL, REV. 2 (T4_spec.md section 17, t4_common.R2, resin rules T4_zivica.md Z0-Z5).
Works on the exported STLs (absolute deflection 0.01) + parts_obal.json; real meshes of RAM / PAN from parts_ram.json /
parts_pan.json (whatever is on disk at the time of the run - stamped in the output).
  O1 valid single solids, watertight STL, volume > 0, bounding boxes, deleted parts gone          (parts_obal.json)
  O3 zones on REAL meshes: (a) static clearance to every RAM part (+ PAN group T), declared contacts;
     (b) pan sweep -90..+90 of the PAN group P meshes and pan x lift 0..20 of the group L meshes + B collar disc / neck halves
     against every static OBAL point (exact swept distance in (r, z) inside the pan window), >= 1.0 hard / 1.3 preferred;
     (c) formal PAN_ENV2 table + sectors (information); (d) lowering of T_stred + front stack over the tower present at T5
  O4 seats and rev. 2 dimensions measured on the meshes (bore r 26.65, shoulder, chamfer, tube wall, F1 insert walls, tongue,
     door step, T_klb neck / undercut / fillet / key / F8 / magnets, ring 2.0, spot faces, bought-part seats)
  O5 inside the shell (inner surface inset 2.2), shells vs the analytic exterior
  R  resin rules (K10 / K13): material, print orientation + build volume (Saturn 4 Ultra 16K, 5 mm margin), support faces on
     visible / fit faces, suction cups (voxel flood fill per layer), drains >= D2.5, inserts, thread-forming engagement,
     washers, countersunk heads, slide fits + epoxy, loaded roots
  S  strength rows of overenie_pevnost.md that concern OBAL parts, recomputed on the rev. 2 geometry with the Z2 allowables
  M1 M2 M3 O2 S1 F1 X1  Blender mesh checks merged from obal2_work/mesh_checks2.json; K8 from obal2_work/k8_obal.json
Usage: /opt/venv/cad/bin/python checks_obal.py [--skip-cups]   -> checks_obal.json"""
import sys, os, json, math, time
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "obal2_work"))
import t4_common as C
import t4_obal as O
import meshlib as ML
import t4_mesh as TM
from scipy.spatial import cKDTree

T0 = time.time()
ARGS = sys.argv[1:]
recs = O.load_parts()
names = [r["name"] for r in recs]
REC = {r["name"]: r for r in recs}
OUT = dict(module="obal", revision=2, generated=time.strftime("%Y-%m-%d %H:%M:%S"), stl_deflection_mm=O.STL_LIN)
Z2 = dict(normal=8.5, sustained=4.3, abuse=12.9, epoxy=2.7, resin_tensile_low=25.8)
OUT["allowables_Z2"] = Z2


def say(*a):
    print(f"[{time.time() - T0:6.1f}]", *a, flush=True)


def other_parts(pj, groups):
    d = json.load(open(os.path.join(HERE, pj)))
    ps = d["parts"] if isinstance(d, dict) else d
    return [p for p in ps if p.get("group") in groups and os.path.exists(os.path.join(HERE, "stl", p["name"] + ".stl"))], d.get("generated")


RAM_T, ram_gen = other_parts("parts_ram.json", ("T",))
PAN_ALL, pan_gen = other_parts("parts_pan.json", ("P", "L", "T"))
OUT["inputs"] = dict(parts_ram_generated=ram_gen, parts_pan_generated=pan_gen, n_ram_T=len(RAM_T), n_pan=len(PAN_ALL),
                     stl_mtime={p["name"]: time.strftime("%H:%M:%S", time.localtime(os.path.getmtime(os.path.join(HERE, "stl", p["name"] + ".stl"))))
                                for p in RAM_T + PAN_ALL if p["name"] in ("T_spodok", "T_paluba", "P_sachta", "P_drziak_serva", "L_pata", "L_ucho")})

# ------------------------------------------------------------------------------------------------------------ O1
o1 = {}
for r in recs:
    ok = bool(r["valid"] and r["n_solids"] == 1 and r["volume_mesh"] > 0 and r.get("watertight") and r.get("bbox_ok", True))
    o1[r["name"]] = dict(valid=r["valid"], n_solids=r["n_solids"], watertight=r.get("watertight"), volume_mesh=r["volume_mesh"],
                         bbox=r["bbox"], bbox_expected=r.get("bbox_expected"), stl_tris=r.get("stl", {}).get("tris"), step=r.get("step"), ok=ok)
gone = [n for n in O.REMOVED if os.path.exists(os.path.join(HERE, "stl", n + ".stl")) or n in REC]
OUT["O1_solids"] = dict(parts=o1, all_ok=all(v["ok"] for v in o1.values()) and not gone, n_parts=len(o1), deleted_parts_still_present=gone,
                        step_skipped=[r["name"] for r in recs if not r.get("step")])
say("O1", OUT["O1_solids"]["all_ok"], [k for k, v in o1.items() if not v["ok"]], "deleted still present:", gone)

# ------------------------------------------------------------------------------------------------------------ samples
H = 0.3
PTS = {}


def P_of(n, h=H):
    if (n, h) not in PTS:
        PTS[(n, h)] = ML.samples(n, h)
    return PTS[(n, h)]


def bb(n):
    P = P_of(n)
    return np.concatenate([P.min(0), P.max(0)])


def bb_near(a, b, g):
    return all(a[k] < b[k + 3] + g and b[k] < a[k + 3] + g for k in range(3))


# ------------------------------------------------------------------------------------------------------------ O3a static
DECL_STATIC = {   # (obal prefix, other prefix): reason (designed contact / fit)
    ("T_klb", "T_spodok"): "key 1.4 in the column slot 3.0 (0.05 per side), neck face 0.2 from the boss face 38.4",
    ("T_bok", "T_spodok"): "seat flange clamped on the stop ring face x +-39.1; seam lip / lower edge on the cap spigot",
    ("T_stred", "T_spodok"): "white lip over the cap spigot (fit 0.21..0.28 radial); F1 bosses on the F1 pads (contact)",
    ("vlozka_stred", "T_spodok"): "insert end flush with the boss face on the F1 pad",
    ("vlozka_stred", "skr_F1"): "F1 screw in the insert",
    ("T_stred", "skr_F1"): "F1 screw tip in the D2.8 pilot",
    ("skrutka_klb", "vl_F8"): "F8 screw in the column insert",
    ("skrutka_klb", "T_spodok"): "F8 screw in the D2.3 hole behind the insert",
    ("T_dvere", "T_spodok"): "door bottom edge above the cap (seam)",
    ("T_klb", "vl_F8"): "neck face x 38.6 is 0.2 in front of the column boss face / insert ends x 38.4 (m18: the flange is always clamped)",
}


def decl_static(a, b):
    for (pa, pb), why in DECL_STATIC.items():
        if a.startswith(pa) and b.startswith(pb):
            return why
    return None


t3 = time.time()
static = []
OTHER_STATIC = RAM_T + [p for p in PAN_ALL if p["group"] == "T"]
for r in recs:
    a = r["name"]; Pa = P_of(a); Ba = bb(a)
    for p in OTHER_STATIC:
        b = p["name"]
        Tb = ML.tris(b)
        Bb = np.concatenate([Tb.reshape(-1, 3).min(0), Tb.reshape(-1, 3).max(0)])
        if not bb_near(Ba, Bb, 2.0):
            continue
        m = np.all((Pa >= Bb[:3] - 2.0) & (Pa <= Bb[3:] + 2.0), axis=1)
        if not m.any():
            continue
        d, at = ML.min_dist(Pa[m], Tb)
        if d < 2.0:
            static.append(dict(obal=a, other=b, clearance=round(d, 3), at=None if at is None else [round(float(v), 2) for v in at],
                               declared=decl_static(a, b)))
static.sort(key=lambda q: q["clearance"])
undecl = [s for s in static if not s["declared"]]
o3 = dict(static=static, static_min_not_declared=min([s["clearance"] for s in undecl], default=None),
          static_below_0p5_not_declared=[s for s in undecl if s["clearance"] < 0.5])
say(f"O3a static: {len(static)} pairs < 2 mm, min not declared {o3['static_min_not_declared']} ({time.time() - t3:.0f} s)")
for s in static[:14]:
    say("    ", s)

# ------------------------------------------------------------------------------------------------------------ O3b pan sweep
t3 = time.time()
HANGING = {"pigtail_zdvih"}     # hanging wire loop (one end on the foot, one on the bracket post): not a rigid lift body -> swept
#                                without lift; PAN reserves it inside z -41 .. -14 (R2 PIGTAIL)
MOV_P = [p["name"] for p in PAN_ALL if p["group"] == "P" or p["name"] in HANGING] + ["golier_kotuc"]
MOV_L = [p["name"] for p in PAN_ALL if p["group"] == "L" and p["name"] not in HANGING] + ["krk_predna_polovica", "krk_zadna_polovica"]


def label_point(q):
    """moving part nearest to the static point q over pan -90..90 (1 deg) x lift 0..20 (2.5) - brute force, for the report"""
    best = (9e9, None, None, None)
    for n in MOV_P + MOV_L:
        M = ML.samples(n, 0.4)
        if len(M) == 0:
            continue
        lifts = np.arange(0, 20.01, 2.5) if n in MOV_L else [0.0]
        rm = np.hypot(M[:, 0], M[:, 1])
        if rm.min() > math.hypot(q[0], q[1]) + 6 or rm.max() < math.hypot(q[0], q[1]) - 6:
            continue
        for pan in np.arange(-90, 90.01, 1.0):
            Q = ML.rotz(M, pan)
            for lf in lifts:
                d = np.linalg.norm(Q + np.array([0, 0, lf]) - q, axis=1).min()
                if d < best[0]:
                    best = (float(d), n, float(pan), float(lf))
    return best


def cloud(nms, h):
    Ps, lab = [], []
    for i, n in enumerate(nms):
        try:
            P = ML.samples(n, h)
        except FileNotFoundError:
            continue
        Ps.append(P); lab += [n] * len(P)
    return np.concatenate(Ps), np.array(lab)


BORE_DECL, sweep = [], []
CP, LP = cloud(MOV_P, 0.4)
CL, LL = cloud(MOV_L, 0.6)
# all static OBAL points that can come near the stage (r < 41, z -50 .. 8) in ONE pass (per-azimuth trees built once)
QS, QN = [], []
for r in recs:
    P = P_of(r["name"])
    rr = np.hypot(P[:, 0], P[:, 1])
    m = (rr < 41.0) & (P[:, 2] > -50.0) & (P[:, 2] < 8.0)
    if m.any():
        QS.append(P[m]); QN += [r["name"]] * int(m.sum())
QS = np.concatenate(QS); QN = np.array(QN)
say(f"O3b: {len(QS)} static points, moving P {len(CP)}, L {len(CL)}")
dp = ML.swept_dist(QS, CP, pan=(-90.0, 90.0), az_bin=3.0)
say("O3b: P sweep done")
dl = ML.swept_dist(QS, CL, pan=(-90.0, 90.0), lift=(0.0, 20.0), lift_step=1.0, az_bin=3.0)
say("O3b: L sweep done")
d_all = np.minimum(dp, dl)
rq = np.hypot(QS[:, 0], QS[:, 1])
jour = (QN == "T_stred") & (rq < C.R_BORE + 0.05) & (QS[:, 2] > O.BORE2["z"][0] - 0.1) & (QS[:, 2] < O.BORE2["z"][1] + 0.05)
#   journal fit zone: bore r 26.65, lead-in chamfer, tube bottom face and shoulder up to r 28.4 face the stage cylinder r 26.5 at
#   0.15 .. 1.9 - the declared running fit of the upper bearing (Z3.12 1.0 rule does not apply to the bearing itself)
if jour.any():
    BORE_DECL.append(dict(min=round(float(d_all[jour].min()), 3), note="journal bore r 26.65 vs the stage band r 26.50 incl. PTFE tape (running fit 0.15)"))
ring = (QN == "T_stred") & (rq < C.R_BORE + 0.1) & (QS[:, 2] >= O.BORE2["z"][1] - 0.05)       # ring seat: the glued collar ring sits there
excl = jour | ring
trP = cKDTree(np.stack([np.hypot(CP[:, 0], CP[:, 1]), CP[:, 2]], 1))
trL = cKDTree(np.stack([np.hypot(CL[:, 0], CL[:, 1]), CL[:, 2]], 1))
for a in sorted(set(QN.tolist())):
    m = (QN == a) & ~excl
    if not m.any():
        continue
    dd = np.where(m, d_all, np.inf)
    i = int(np.argmin(dd))
    q = QS[i]
    src = "P" if dp[i] <= dl[i] else "L"
    lb = label_point(q) if dd[i] < 3.0 else (None, None, None, None)
    sweep.append(dict(obal=a, min_swept=round(float(dd[i]), 3), at=[round(float(v), 2) for v in q], group=src,
                      nearest_moving=lb[1], pose=None if lb[1] is None else dict(pan=lb[2], lift=lb[3], d_bruteforce_1deg=round(lb[0], 3)),
                      ok_hard=bool(dd[i] >= 1.0 - 0.02), ok_pref=bool(dd[i] >= 1.3)))
sweep.sort(key=lambda q: q["min_swept"])
o3["pan_sweep"] = dict(method="PAN group P meshes (+ golier_kotuc) swept pan -90..+90, group L meshes (+ B neck halves) swept pan -90..+90 x "
                              "lift 0..20 (0.5 steps); static OBAL surface samples (0.3 mm) with r < 41, z -50..8; inside the pan window the "
                              "distance is taken in (r, z) (any azimuth reachable, 3 deg bins widened by one bin = conservative), outside it at the "
                              "extreme poses; lift in 1.0 steps; moving samples 0.4 (P) / 0.6 (L) mm -> accuracy about +-0.3 (conservative side)", parts=sweep, journal_bore_declared=BORE_DECL,
                     min=min([s["min_swept"] for s in sweep], default=None), moving_P=MOV_P, moving_L=MOV_L)
o3["pan_sweep"]["ok_hard"] = all(s["ok_hard"] for s in sweep)
say(f"O3b pan sweep ({time.time() - t3:.0f} s):", [(s["obal"], s["min_swept"], s["nearest_moving"]) for s in sweep[:10]], "bore", BORE_DECL)

# ------------------------------------------------------------------------------------------------------------ O3c PAN_ENV2 formal
penv = []
for r in recs:
    P = P_of(r["name"])
    rr = np.hypot(P[:, 0], P[:, 1]); az = np.degrees(np.arctan2(P[:, 1], P[:, 0])) % 360
    worst = (9e9, None)
    for z0, z1, rm in C.PAN_ENV2:
        m = (P[:, 2] > z0 + 0.02) & (P[:, 2] < z1 - 0.02)
        if r["name"] == "T_stred":
            m &= ~((rr <= O.BORE2["r"] + 0.62) & (P[:, 2] >= O.BORE2["z"][0] - 0.01))
        if not m.any():
            continue
        lim = np.full(m.sum(), rm)
        for sct in C.PAN_ENV2_SECTORS:          # stage-frame sector swept +-90 -> B azimuth window
            a0, a1 = sct["az"][0] - 90.0, sct["az"][1] + 90.0
            inz = (P[m, 2] > sct["z"][0]) & (P[m, 2] < sct["z"][1])
            ina = ((az[m] - a0) % 360.0) <= (a1 - a0)
            lim = np.where(inz & ina, np.maximum(lim, sct["r"]), lim)
        d = rr[m] - lim
        i = int(np.argmin(d))
        if d[i] < worst[0]:
            worst = (float(d[i]), P[m][i])
    if worst[1] is not None and worst[0] < 3.0:
        penv.append(dict(part=r["name"], margin=round(worst[0], 3), at=[round(float(v), 2) for v in worst[1]],
                         az=round(float(math.degrees(math.atan2(worst[1][1], worst[1][0])) % 360), 1)))
penv.sort(key=lambda q: q["margin"])
o3["pan_env2_formal"] = dict(note="radial table PAN_ENV2 + sectors (lug, back floor, lift-module bottom) swept +-90; the table is a "
                                  "conservative cylinder (the lift module spans only stage az 35..140): information - the real-mesh "
                                  "sweep (pan_sweep) is the verdict", rows=penv)
say("O3c PAN_ENV2 formal:", penv[:8])

# ------------------------------------------------------------------------------------------------------------ O3d lowering
t3 = time.time()
LOWER = ["T_stred", "T_svetlovod", "T_mriezka", "T_drziak_led", "T_drziak_repro", "reproduktor", "tesnenie_repro", "DPS_led"] + \
        [n for n in names if n.startswith(("skrutka_led", "skrutka_repro", "podlozka_led", "podlozka_repro", "vlozka_stred",
                                           "magnet_zarubna", "vyvod_"))]
LATER = {"pastorok_pan", "skr_F1_1", "skr_F1_2", "skr_F1_3", "skr_F1_4", "pd_F1_1", "pd_F1_2", "pd_F1_3", "pd_F1_4"}
#   pan pinion bonded after T_stred (RAM finding); F1 screws + washers are driven from below after T_stred is seated
tower_names = [p["name"] for p in RAM_T if p["name"] not in LATER] + [p["name"] for p in PAN_ALL if p["group"] == "T"]
TW = np.concatenate([ML.samples(n, 0.4) for n in tower_names])
TW = TW[TW[:, 2] > C.Z_WHITE + 0.01]          # nothing of T_stred goes below its lower edge
low = []
for n in LOWER:
    if n not in REC:
        continue
    P = P_of(n)
    d = ML.lowering_clear(P, TW)
    if n == "T_stred":
        # the lip below the spigot top (-78.0) slides over the spigot (fit 0.21..0.28): declared
        rx = (P[:, 2] < -77.9)
        d = np.where(rx, np.inf, d)
    i = int(np.argmin(d))
    rowl = dict(part=n, plan_clearance=round(float(d[i]), 3), at=[round(float(v), 2) for v in P[i]], ok=bool(d[i] >= C.TOWER_CLEAR - 0.02))
    if d[i] < C.TOWER_CLEAR:                       # name the blocking tower part(s): every tower part above a blocked point
        blk = {}
        bad_pts = P[d < C.TOWER_CLEAR - 0.02]
        for tn in tower_names:
            TP = ML.samples(tn, 0.4)
            for q in bad_pts[:: max(1, len(bad_pts) // 300)]:
                m = TP[:, 2] >= q[2]
                if m.any():
                    dd2 = np.hypot(TP[m, 0] - q[0], TP[m, 1] - q[1])
                    j = int(np.argmin(dd2))
                    if dd2[j] < C.TOWER_CLEAR - 0.02 and (tn not in blk or dd2[j] < blk[tn]["plan"]):
                        blk[tn] = dict(plan=round(float(dd2[j]), 3), obal_point=[round(float(v), 2) for v in q],
                                       tower_point=[round(float(v), 2) for v in TP[m][j]])
        rowl["blocked_by"] = blk
    low.append(rowl)
low.sort(key=lambda q: q["plan_clearance"])
o3["lowering"] = dict(note="T_stred with its front stack lowered straight down (-Z) over the tower present at assembly step T5 "
                           "(all RAM group-T meshes except the pan pinion, bonded after T5, + PAN static FFC ends); plan clearance of every "
                           "point to the tower points at or above it; T_stred lip below z -77.9 = spigot fit (declared)",
                      tower=tower_names, rows=low, min=min([q["plan_clearance"] for q in low], default=None), ok=all(q["ok"] for q in low))
say(f"O3d lowering ({time.time() - t3:.0f} s):", low[:6])
o3["ok"] = bool((o3["static_min_not_declared"] is None or o3["static_min_not_declared"] >= 0.2) and o3["pan_sweep"]["ok_hard"] and o3["lowering"]["ok"])
OUT["O3_zones"] = o3

# ------------------------------------------------------------------------------------------------------------ O4 seats
seats = []


def seat(what, nominal, measured, ok, note=""):
    seats.append(dict(feature=what, nominal=nominal, measured=measured, ok=bool(ok), note=note))


V = P_of("T_stred", 0.25)
rr = np.hypot(V[:, 0], V[:, 1])
mb = (V[:, 2] > -9.9) & (V[:, 2] < -2.1) & (rr < 27.0)
seat("journal bore r (z -9.9 .. -2.1; the 0.5 lead-in below)", 26.65, dict(r_min=round(float(rr[mb].min()), 4), r_max=round(float(rr[mb].max()), 4), n=int(mb.sum())),
     abs(rr[mb].min() - 26.65) <= 0.01 and abs(rr[mb].max() - 26.65) <= 0.01, "tol +0.05/0: sand to fit with the PTFE-taped stage")
ms = (np.abs(V[:, 2] + 2.0) < 0.01) & (rr > 26.7) & (rr < 28.3)
seat("shoulder face z -2.00 (flat annulus r 26.65 .. 28.35)", -2.0, dict(points=int(ms.sum()), r_range=[round(float(rr[ms].min()), 3), round(float(rr[ms].max()), 3)] if ms.any() else None),
     ms.sum() > 50)
mr = (V[:, 2] > -1.9) & (V[:, 2] < 3.9) & (rr < 28.6)
seat("ring seat r 28.35 (z -1.9 .. 3.9) unchanged", 28.35, dict(r_min=round(float(rr[mr].min()), 4), r_max=round(float(rr[mr].max()), 4)),
     abs(rr[mr].min() - 28.35) <= 0.01)
mc = (np.abs(V[:, 2] + 10.5) < 0.01) & (rr < 28.0)
seat("lead-in chamfer 0.5 x 45 at z -10.5", 27.15, dict(r_min_at_bottom=round(float(rr[mc].min()), 3) if mc.any() else None),
     mc.any() and abs(rr[mc].min() - 27.15) <= 0.03)
# tube outer surface: free azimuths (no gusset: |az| < 40 about +-X), z -10 .. -3
azd = np.degrees(np.arctan2(V[:, 1], V[:, 0])) % 180
mt = (V[:, 2] > -10.0) & (V[:, 2] < -3.0) & (rr > 29.0) & (rr < 31.5) & ((azd < 40) | (azd > 140))
tube_out = float(rr[mt].min()) if mt.any() else None
seat("tube wall (outer r - bore r) >= 3.9", 3.95, dict(tube_outer_r_min=round(tube_out, 3) if tube_out else None,
                                                       wall=round(tube_out - float(rr[mb].max()), 3) if tube_out else None),
     tube_out is not None and tube_out - rr[mb].max() >= 3.9)
# F1 insert walls
for (x0, y0) in C.SCR_STRED:
    d2 = np.hypot(V[:, 0] - x0, V[:, 1] - y0)
    mz = (V[:, 2] > -80.5) & (V[:, 2] < -77.2)
    hole = d2[mz & (d2 < 2.5)]
    boss = d2[mz & (d2 > 2.5) & (d2 < 3.6)]
    wall = float(boss.min() - hole.max()) if len(hole) and len(boss) else None
    seat(f"F1 boss ({x0:+.0f}, {y0:+.0f}): insert hole D3.6, boss r 3.4 -> wall >= 1.6", 1.6,
         dict(hole_r=round(float(hole.max()), 3) if len(hole) else None, boss_r_min=round(float(boss.min()), 3) if len(boss) else None,
              wall=round(wall, 3) if wall else None), wall is not None and wall >= 1.6 - 0.01)
# tongue
dz = C.dist_outer(V)
mtg = (np.abs(V[:, 0]) < 17.9) & (V[:, 1] > 25) & (V[:, 2] < -11.8) & (V[:, 2] > -12.8)     # |x| > 18: the wall above the corner arc
seat(f"door tongue: inset {O.TONGUE['inset'][0]} .. 2.2, z -12.75 .. -11.75, |x| <= 20.6", f"inset {O.TONGUE['inset'][0]}..2.2",
     dict(inset_min=round(float(dz[mtg].min()), 3) if mtg.any() else None, inset_max=round(float(dz[mtg].max()), 3) if mtg.any() else None,
          z_min=round(float(V[mtg, 2].min()), 3) if mtg.any() else None,
          x_extent=round(float(np.abs(V[(np.abs(V[:, 0]) < 21) & (V[:, 1] > 25) & (V[:, 2] < -12.6) & (V[:, 2] > -12.76), 0]).max()), 3)),
     mtg.any() and abs(dz[mtg].min() - O.TONGUE["inset"][0]) < 0.06 and abs(V[mtg, 2].min() + 12.75) < 0.03)
Vd = P_of("T_dvere", 0.25)
dd_ = C.dist_outer(Vd)
mlip = (np.abs(Vd[:, 0]) < 20.0) & (Vd[:, 2] > -12.95)
minr = (np.abs(Vd[:, 0]) < 20.0) & (dd_ > O.DOOR_LIP + 0.08)
seat(f"door top: lip inset 0 .. {O.DOOR_LIP} up to z -12.0, inner half stops at z -13.0 (|x| <= 20.85)", f"lip {O.DOOR_LIP} / -13.0",
     dict(lip_inset_max=round(float(dd_[mlip].max()), 3), lip_z_max=round(float(Vd[mlip, 2].max()), 3),
          inner_half_z_max=round(float(Vd[minr, 2].max()), 3), hooks_left=int((Vd[:, 2] > -11.99).sum())),
     dd_[mlip].max() >= 1.2 and abs(dd_[mlip].max() - O.DOOR_LIP) < 0.06 and abs(Vd[minr, 2].max() + 13.0) < 0.03 and (Vd[:, 2] > -11.99).sum() == 0)
# T_klb
Vk = P_of("T_klb_L", 0.15)
sy, sz = C.SH_Y, C.SH_Z
rk = np.hypot(Vk[:, 1] - sy, Vk[:, 2] - sz); ak = np.degrees(np.arctan2(Vk[:, 2] - sz, Vk[:, 1] - sy)) % 360
nokey = ~((np.abs(Vk[:, 2] - sz) < 2.0) & (Vk[:, 1] > sy))
seat("T_klb neck face x 38.6 (key excluded), key tip x 37.0", (38.6, 37.0),
     dict(neck_face_x=round(float(Vk[nokey, 0].min()), 3), key_tip_x=round(float(Vk[:, 0].min()), 3)),
     abs(Vk[nokey, 0].min() - 38.6) < 0.01 and abs(Vk[:, 0].min() - 37.0) < 0.01)
mu = (Vk[:, 0] > 40.62) & (Vk[:, 0] < 41.2) & (rk > 11.02) & (rk < 11.98) & (np.abs(ak - 270) > 20)          # wire groove at az 270
du = np.hypot(Vk[mu, 0] - C.X_SEAT, rk[mu] - 11.5)
seat("T_klb neck/body step x 40.6: R0.5 undercut (points on the arc, distance to its centre)", 0.5,
     dict(points=int(mu.sum()), r_min=round(float(du.min()), 3) if mu.any() else None, r_max=round(float(du.max()), 3) if mu.any() else None,
          depth_x_max=round(float(Vk[mu, 0].max()), 3) if mu.any() else None), mu.sum() > 20 and abs(du.min() - 0.5) < 0.03 and abs(du.max() - 0.5) < 0.03)
xst = C.X_SH + 4.2
mf = (Vk[:, 0] > xst + 0.02) & (Vk[:, 0] < xst + 0.48) & (rk > 11.02) & (rk < 11.48) & (np.abs(ak - 270) > 15)
dfl = np.hypot(Vk[mf, 0] - (xst + 0.5), rk[mf] - 11.5)
seat("T_klb body/end step x 50.956: R0.5 fillet (distance of the surface to the arc centre)", 0.5,
     dict(points=int(mf.sum()), r_min=round(float(dfl.min()), 3) if mf.any() else None, r_max=round(float(dfl.max()), 3) if mf.any() else None),
     mf.sum() > 20 and abs(dfl.min() - 0.5) < 0.03 and abs(dfl.max() - 0.5) < 0.03)
mkr = (np.abs(Vk[:, 0] - 38.45) < 0.05) & (Vk[:, 1] > sy + 6.0) & (Vk[:, 1] < sy + 10.2) & (np.abs(Vk[:, 2] - sz) < 2.5)
ext = np.abs(Vk[mkr, 2] - sz).max() if mkr.any() else None
seat("T_klb key root R0.2 (key half width 1.45 + fillet at x 38.45 = 0.15 above the neck face)", "1.45 .. 1.65",
     dict(half_width_at_x38p45=round(float(ext), 3) if ext is not None else None), ext is not None and 1.47 < ext < 1.66)
for az in O.KLB2["f8_az"]:
    y, z = O.klb_yz(az, C.KLB_SCREWS["pcd_r"])
    d2 = np.hypot(Vk[:, 1] - y, Vk[:, 2] - z)
    cb = d2[(Vk[:, 0] > 46) & (Vk[:, 0] < 56) & (d2 < 3.0)]
    hl = d2[(Vk[:, 0] > 39.2) & (Vk[:, 0] < 44.8) & (d2 < 1.8)]
    rb_ = np.hypot(Vk[:, 1] - sy, Vk[:, 2] - sz)
    wall_bore = None
    if len(cb):
        mw = (Vk[:, 0] > 46) & (Vk[:, 0] < 57.9) & (np.abs(d2 - O.KLB2["cbore_d"] / 2) < 0.03)
        wall_bore = float((np.hypot(Vk[mw, 1] - sy, Vk[mw, 2] - sz) - C.KLB_BUSH["bore_d"] / 2).min()) if mw.any() else None
        wall_out = float((11.0 - np.hypot(Vk[mw, 1] - sy, Vk[mw, 2] - sz)).min()) if mw.any() else None
    seat(f"F8 az {az:.0f}: counterbore D4.7 (x 45 -> end), hole D2.3", (2.35, 1.15),
         dict(cbore_r=round(float(cb.min()), 3) if len(cb) else None, hole_r=round(float(hl.min()), 3) if len(hl) else None,
              wall_to_bush_bore=round(wall_bore, 3) if wall_bore is not None else None, wall_to_journal_r11=round(wall_out, 3) if len(cb) else None),
         len(cb) and abs(cb.min() - 2.35) < 0.02 and len(hl) and abs(hl.min() - 1.15) < 0.02,
         "web to the bush bore 1.13 and to the D22 journal 1.15 (declared local walls >= 1.0, not loaded by the screw)")
for az in O.KLB2["magnet_az"]:
    y, z = O.klb_yz(az, C.KLB_MAGNETS["pcd_r"])
    d2 = np.hypot(Vk[:, 1] - y, Vk[:, 2] - z)
    mm = (Vk[:, 0] > C.X_KLB_END - 2.05) & (Vk[:, 0] < C.X_KLB_END - 0.05) & (d2 < 1.8)
    seat(f"magnet pocket az {az:.0f}: D3.1 x 2.1", 1.55, dict(r=round(float(d2[mm].min()), 3) if mm.any() else None,
                                                              depth=round(float(C.X_KLB_END - Vk[mm & (d2 < 1.5), 0].min()), 3) if (mm & (d2 < 1.5)).any() else None),
         mm.any() and abs(d2[mm].min() - 1.55) < 0.02)
for az, nm in ((0.0, "key az 0"),):
    pass
bo = Vk[(Vk[:, 0] > 46) & (Vk[:, 0] < 56)]
rbo = np.hypot(bo[:, 1] - sy, bo[:, 2] - sz)
seat("bush bore D8.05 (frozen)", 4.025, dict(r_min=round(float(rbo[rbo < 4.5].min()), 3)), abs(rbo[rbo < 4.5].min() - 4.025) < 0.01)
re_ = Vk[(Vk[:, 0] > 39.0) & (Vk[:, 0] < 43.8)]
rre = np.hypot(re_[:, 1] - sy, re_[:, 2] - sz)
seat("recess D10.2 to x 44.0 (frozen)", 5.1, dict(r_min=round(float(rre[rre < 5.5].min()), 3)), abs(rre[rre < 5.5].min() - 5.1) < 0.01)
# ring + spot faces
Vr = P_of("T_drziak_repro", 0.2)
seat("speaker ring thickness 2.0 (y -31.6 .. -29.6), open 0.3 steps under the washers", (2.0, 0.3),
     dict(y=[round(float(Vr[:, 1].min()), 3), round(float(Vr[:, 1].max()), 3)],
          spot_floor_y=sorted({round(float(v), 2) for v in Vr[(np.abs(Vr[:, 1] + 29.9) < 0.01), 1]})),
     abs(Vr[:, 1].max() + 29.6) < 0.01 and (np.abs(Vr[:, 1] + 29.9) < 0.01).any())
Vl = P_of("T_drziak_led", 0.2)
seat("LED holder ear steps 0.3 (y -29.7) at x +-16.8 .. 22.3", -29.7, dict(points=int((np.abs(Vl[:, 1] + 29.7) < 0.01).sum())),
     (np.abs(Vl[:, 1] + 29.7) < 0.01).sum() > 10)
# engagement of thread-forming screws (F13): boss face -> screw tip
eng = {}
for n in names:
    if n.startswith(("skrutka_led", "skrutka_repro")):
        Ps = P_of(n, 0.2)
        tip = float(Ps[:, 1].min())
        face = O.BOSS_FACE_LED if "led" in n else C.SPEAKER["y"][1]
        eng[n] = round(face - tip, 3)
seat("F13 thread-forming engagement >= 2 d = 4.0 (boss face -> screw tip)", 4.0, eng, all(v >= 4.0 - 0.01 for v in eng.values()))
# bought-part seats (nominal; tolerance taken by the seat)
seat("collar ring golier_prstenec D56.50 in the ring seat D56.70 on the shoulder z -2.0", "0.10 radial glue seam", None, True, "B part (finished)")
seat("speaker D28 x 5 between 3 boss scallops D28.3", "0.15 radial", None, True)
seat("door magnets D5 x 2 in pockets D5.1 x 2.1, shoulder magnets D3 x 2 in D3.1 x 2.1", "0.05 radial, epoxy", None, True)
seat("insert M2.5 OD 3.5 x 4.0 in D3.6 x 4.3 + D2.8 pilot (F1)", "0.05 radial, epoxy", None, True)
seat("ISO 7092 M2 washer D4.5 (tolerance 4.2..4.5) in the F8 counterbore D4.7", "0.10 radial", None, True)
seat("DIN 125 M2 washer D5.0 in the D5.4 spot faces (F13)", "0.20 radial", None, True)
OUT["O4_seats"] = dict(seats=seats, all_ok=all(s["ok"] for s in seats))
say("O4", OUT["O4_seats"]["all_ok"], [(s["feature"][:50], s["measured"]) for s in seats if not s["ok"]])
for s in seats:
    if s["measured"] is not None:
        say("    ", s["feature"][:70], s["measured"], s["ok"])

# ------------------------------------------------------------------------------------------------------------ O5 inside
o5 = {}
OUTSIDE_OK = ("T_klb_", "skrutka_klb_", "magnet_klb_", "podlozka_klb_")
SHELLS = ("T_stred", "T_bok_L", "T_bok_P", "T_dvere", "T_svetlovod", "T_mriezka")
D5 = {"skrutka_led_1": "screw tip in the pilot of the LED boss (pilot 0.7 into the wall, skin 1.5)",
      "skrutka_led_2": "screw tip in the pilot of the LED boss (pilot 0.7 into the wall, skin 1.5)",
      "tesnenie_repro": "foam gasket lies on the inner wall (cut with the inner surface)"}


def radial_excess(Vv):
    zz = np.clip(Vv[:, 2], C.Z_BOT, C.TOP)
    a = np.interp(C.TOP - zz, C.PD, C.PA); b_ = np.interp(C.TOP - zz, C.PD, C.PB); n_ = np.interp(C.TOP - zz, C.PD, C.PN)
    f = (np.abs(Vv[:, 0]) / a) ** n_ + (np.abs(Vv[:, 1]) / b_) ** n_
    rad = np.hypot(Vv[:, 0], Vv[:, 1]) * (1 - f ** (-1 / n_))
    return np.where(Vv[:, 2] > C.TOP + 1e-6, np.maximum(rad, Vv[:, 2] - C.TOP), rad)


for n in names:
    P = P_of(n)
    if n in SHELLS:
        ex = float(radial_excess(ML.tris(n).reshape(-1, 3)).max())
        o5[n] = dict(max_radial_excess_over_exterior=round(ex, 4), ok=bool(ex <= 0.03))
        continue
    ins = C.inside_outer(P); d = C.dist_outer(P)
    sd = np.where(ins, d, -d)
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
say("O5", OUT["O5_inside"]["all_ok"], {k: v for k, v in o5.items() if not v["ok"] or v.get("declared")})

# ------------------------------------------------------------------------------------------------------------ R resin rules
t3 = time.time()
VOL = (211.68, 118.37, 220.0); MARGIN = 5.0; SUPPORT_H = 5.0
rrows = {}
for r in recs:
    if not r["printed"]:
        continue
    n = r["name"]
    pr = r.get("print") or {}
    T = ML.tris(n)
    b = np.array(pr.get("plate_dir", (0, 0, -1)), float)
    pb = ML.print_bbox(T, b)
    fits = (pb["xy"][0] <= VOL[0] - 2 * MARGIN and pb["xy"][1] <= VOL[1] - 2 * MARGIN and pb["z"] + SUPPORT_H <= VOL[2] - MARGIN)
    cen = T.mean(1)
    if n in SHELLS:
        vis = np.abs(radial_excess(cen)) < 0.06
    elif n.startswith("T_klb"):
        rk_ = np.hypot(cen[:, 1] - C.SH_Y, cen[:, 2] - C.SH_Z)
        vis = (np.abs(cen[:, 0]) > C.X_SEAT + 0.6) & (rk_ > 10.15)             # body, journal, end chamfer (shoulder face + undercut excluded)
    else:
        vis = np.zeros(len(T), bool)
    fit = np.zeros(len(T), bool)
    if n == "T_stred":
        rc = np.hypot(cen[:, 0], cen[:, 1])
        fit = (np.abs(rc - O.BORE2["r"]) < 0.05) & (cen[:, 2] > -10.4) & (cen[:, 2] < -2.0)       # journal bore
    tot, sup_vis, msk = ML.support_faces(T, b, vis | fit)
    sup_fit = float(TM.tri_normals(T)[1][msk & fit].sum()) if fit.any() else 0.0
    row = dict(mat=r["mat"], process="MSLA resin (Elegoo Tough, Saturn 4 Ultra 16K)", orientation=pr.get("orientation"), plate_dir=list(b),
               print_bbox_xy=pb["xy"], print_height=pb["z"], fits_with_margin=bool(fits), supports=pr.get("supports"), drains=pr.get("drains"),
               warp=pr.get("warp"), plate_facing_area_mm2=round(tot, 1), plate_facing_on_visible_mm2=round(sup_vis, 1),
               plate_facing_on_fit_faces_mm2=round(sup_fit, 1))
    if "--skip-cups" not in ARGS:
        pitch = 0.5 if max(pb["xy"] + [pb["z"]]) > 40 else 0.25
        row["cups"] = ML.cups(T, b, pitch=pitch)
    rrows[n] = row
    say("R", n, {k: row[k] for k in ("print_bbox_xy", "print_height", "fits_with_margin", "plate_facing_area_mm2", "plate_facing_on_visible_mm2",
                                     "plate_facing_on_fit_faces_mm2")}, row.get("cups"))
k13 = dict(
    materials=dict(ok=all(r["mat"].startswith("resin") for r in recs if r["printed"]), note="all printed OBAL parts are the one tough resin "
                   "(mat key = finish / density only); no PETG / POM part left (T_puzdro deleted, T_drziak_repro resin)"),
    heat_set_inserts=dict(ok=True, note="none: F1 = bonded brass inserts M2.5 OD 3.5 x 4.0 in D3.6 x 4.3 + D2.8 pilot (epoxy)"),
    countersunk_heads_on_resin=dict(ok=True, note="none: F8 ISO 7380 button head on an ISO 7092 washer, F13 pan-head thread-forming on DIN 125"),
    insert_bosses=dict(ok=all(s["ok"] for s in seats if s["feature"].startswith("F1 boss")), note="F1 boss r 3.4 -> wall 1.6 around the D3.6 hole (Z3.4a), engagement 4.0"),
    thread_forming=dict(ok=all(v >= 3.99 for v in eng.values()), engagement=eng, note="F13 M2 x 6: bosses D5.0 (= 2.5 d), pilots D1.7, skin "
                        "behind the pilots 1.5 (LED) / 1.74..2.2 (speaker), engagement 4.0 via 0.3 spot faces; one-time joints, seat + 1/8 turn"),
    washers=dict(ok=all(any(n.startswith(p) for n in names) for p in ("podlozka_klb", "podlozka_led", "podlozka_repro")),
                 note="F8: ISO 7092 M2 2.2 x 4.5 x 0.3 (DIN 125 M2 D5 does not fit: 0.88 wall to the bush bore); F13: DIN 125 M2; F1 heads are "
                      "on RAM's pad (DIN 125 M2.5, RAM)"),
    slide_fits_epoxy=dict(ok=True, note="magnets D5 / D3 in D5.1 / D3.1 (+0.1), inserts OD 3.5 in D3.6, collar ring 0.10 radial seam, light guide "
                          "and grille plugs 0.2 all round, speaker 0.15: all bonded or clamped, no press fit; fit holes drilled / reamed after curing"),
    flexing_features=dict(ok=True, note="door hook tabs deleted; no clip, no snap; the door is held by 4 magnet pairs + ledge"),
    loaded_roots=dict(ok=True, list=[
        "T_klb shoulder x 40.6: R0.5 undercut (measured O4)", "T_klb step x 50.956: R0.5 fillet (measured O4)",
        "T_klb key roots R0.2 (declared: 0.2 gap to the boss face is all the room outside the slot; key stress row S2 with Kt 1.8)",
        "F1 bosses: clamp is self-contained (insert -> boss -> pad), boss / web roots not loaded",
        "door-frame magnet pads: 6 N magnet pull, not a structural root (rev. 1 geometry)",
        "T_drziak_repro / T_drziak_led ears: clamped flat on their bosses (compression only)"]),
    drains=dict(ok=True, vents="T_stred 2 x D2.5 through the collar tube at z 0.4 (rev. 1 D1.6)", blind_pockets=[
        "T_stred / T_dvere magnet pockets D5.1 x 2.1 (8)", "T_klb magnet pockets D3.1 x 2.1 (6)", "F1 insert holes D3.6 x 4.3 + D2.8 pilot "
        "(blind, open toward the plate in the print orientation; drilled after curing)", "LED / speaker boss pilots D1.7 (blind, drilled)"]),
)
OUT["R_resin"] = dict(parts=rrows, k13=k13, volume=dict(printer="Elegoo Saturn 4 Ultra 16K", build=VOL, margin=MARGIN, support_height=SUPPORT_H),
                      cups_note="max sealed area of one layer against the FEP (voxel flood fill); the first layers on supports are open; "
                                "<= 10 mm2 is negligible (blind pockets)",
                      ok=bool(all(v["fits_with_margin"] for v in rrows.values()) and all(v.get("ok", True) for v in k13.values())))
say(f"R done ({time.time() - t3:.0f} s)")

# ------------------------------------------------------------------------------------------------------------ S strength
S = []


def row(id_, what, load, cls, stress, note="", allow=None, role="check"):
    """role: 'check' (counts for the verdict), 'spec torque' (value of T4_spec 17.9: a failure is a documentation finding),
    'recommended torque' (counts), 'info' (hypothetical case, does not count)"""
    lim = allow if allow is not None else Z2[cls]
    ok = bool(stress <= lim + 1e-9)
    S.append(dict(id=id_, feature=what, load=load, class_=cls, stress_MPa=round(stress, 2), allowable_MPa=lim,
                  ratio=round(lim / stress, 2) if stress > 0 else None, ok=ok if role != "info" else None, role=role, note=note))


# S1 T_klb shoulder section (rows 39 / 41): annulus r 5.1 .. 11.0 minus 3 x D2.3 at r 7.5 (outer ring r 12..13.5 beyond the undercut ignored)
ro, ri = 11.0, C.KLB_BUSH["recess_d"] / 2
I = math.pi / 4 * (ro ** 4 - ri ** 4) - 3 * (math.pi * 1.15 ** 2) * 7.5 ** 2 * 0.5
Zs = I / ro
Kt_u = 2.1      # shaft shoulder, r/d 0.5/22 = 0.023, D/d 1.23, relief-groove form (Peterson, approximate)
row("S1a", "T_klb section at the shoulder x 40.6 (R0.5 undercut), Z %.0f mm3" % Zs, "L5 10 N along X at the arm tip, 72 mm: 0.72 N.m",
    "normal", 720.0 / Zs * Kt_u, "Kt 2.1 (rev. 1 sharp: 2.5); neck x 38.6..40.6 carries no bending (0.2 gap to the boss, 0.25 in the flange hole)")
row("S1b", "same section", "lifted by one arm 15 N (lever 16.4 mm, row 39)", "normal", 15.0 * 16.4 / Zs * Kt_u)
F_cap = Z2["abuse"] * Zs / (Kt_u * 16.4)
S.append(dict(id="S1c", feature="T_klb + F8, sideways topple (row 41, ESTIMATE)", load="L6 impact 229..686 N (rev. 1 assumption, lever 16.4)",
              class_="abuse", capacity_N=round(F_cap, 0), allowable_MPa=Z2["abuse"], ratio=round(F_cap / 686.0, 2), ok=None,
              note="capacity %.0f N at 12.9 MPa with Kt 2.1 (rev. 1: 282 N); the impact force is an assumption - K12 / bench test" % F_cap))
# S2 key: torque 0.25 N.m (arm friction collar slips first, L5)
kr0, kr1 = O.KLB2["key_r"]; kw = O.KEY["w"]
rc = (kr0 + kr1) / 2; F = 250.0 / rc
Zk = (kr1 - kr0) * kw ** 2 / 6.0
lev = (O.KLB2["neck_x0"] - C.X_COL_BOSS) + (C.X_COL_BOSS - O.KLB2["key_x0"]) / 2
row("S2a", f"T_klb key root bending ({kw} x {kr1 - kr0:.1f}, lever {lev:.2f}, R0.2 -> Kt 1.8)", "L5 arm torque 0.25 N.m (collar slip)",
    "normal", F * lev / Zk * 1.8, "friction of the F8 clamp not counted (Z3.7)")
row("S2b", "T_klb key flank bearing (1.4 engaged)", "L5 0.25 N.m", "normal", F / ((kr1 - kr0) * 1.4))
row("S2c", "T_klb key root bending", "hypothetical: hand 0.6 N.m with the arm collar locked", "abuse", 600.0 / rc * lev / Zk * 1.8,
    "does not occur by Z4 L5 (the friction collar slips at 0.25 N.m first) - the collar is a safety element of the arm round", role="info")
# S3 F8 washer bearing on the counterbore floor (sustained preload)
A_w = math.pi / 4 * (4.2 ** 2 - 2.3 ** 2)         # washer OD at its lower tolerance 4.2
for tq, role in ((0.05, "spec torque"), (0.03, "spec torque"), (0.015, "recommended torque")):
    Pp = tq / (0.2 * 0.002)
    row(f"S3 {tq}", f"F8 ISO 7092 washer on the T_klb counterbore floor (A {A_w:.1f} mm2, OD 4.2 worst)", f"preload at {tq} N.m (K 0.2): {Pp:.0f} N",
        "sustained", Pp / A_w, "0.05 = T4_spec 17.9, 0.03 = RAM recommendation (insert bond)" if role != "recommended torque" else "+ Loctite 222", role=role)
# S4 F13 washers on the ring / holder ears
A_13 = math.pi / 4 * (5.0 ** 2 - 2.3 ** 2)
for tq, role in ((0.04, "spec torque"), (0.03, "recommended torque")):
    Pp = tq / (0.3 * 0.002)
    row(f"S4 {tq}", f"F13 DIN 125 washer on the ring / LED-holder ear (A {A_13:.1f} mm2)", f"thread-forming seat + 1/8 turn {tq} N.m (K 0.3): {Pp:.0f} N",
        "sustained", Pp / A_13, role=role)
strip = math.pi * 2.0 * 4.0 * 0.5 * Z2["resin_tensile_low"] * 0.6        # thread shear: pi d L 0.5 x tau (0.6 x UTS)
S.append(dict(id="S4c", feature="F13 thread strip-out, 4.0 engaged in D5 bosses", load="0.04 N.m -> 67 N", class_="assembly",
              capacity_N=round(strip, 0), ratio=round(strip / 67.0, 2), ok=bool(strip / 67.0 >= 2.0), note="tau = 0.6 x 25.8 MPa on half the thread cylinder"))
# S5 F1 inserts in T_stred (epoxy) and boss bearing
A_b = math.pi * 3.5 * 4.0
for tq, role in ((0.09, "spec torque"), (0.045, "recommended torque")):
    Pp = tq / (0.2 * 0.0025)
    row(f"S5a {tq}", "F1 insert M2.5 OD 3.5 x 4.0 bond (epoxy)", f"preload at {tq} N.m: {Pp:.0f} N", "epoxy", Pp / A_b, role=role)
    row(f"S5b {tq}", "F1 boss annulus r 1.8 .. 3.4 on the pad (compression)", f"preload {Pp:.0f} N", "sustained", Pp / (math.pi * (3.4 ** 2 - 1.8 ** 2)),
        role=role)
row("S5c", "F1 when the torso is carried by the shell (4 inserts)", "L1-like 15 N on T_stred", "epoxy", 15.0 / 4 / A_b)
# S6 upper journal (bore r 26.65): side load from the head reacted between the journal (z -6.5) and the pivot (z -44)
for lab_, Fh, h in (("L2 30 N at 30 deg off-axis on the head, 60 mm above the bore", 15.0, 60.0), ("L6 knock 100 N on the head", 100.0, 60.0)):
    Fj = Fh * (h + 37.5) / 37.5
    row(f"S6 {lab_[:2]}", "journal bore bearing (projected 53.3 x 7.0)", f"{lab_}: {Fj:.0f} N at the journal", "normal" if "L2" in lab_ else "abuse",
        Fj / (53.3 * 7.0), "PTFE tape on the stage band (Z3.8 <= 5 MPa projected)")
row("S6c", "collar tube in bending (tube r 26.65..30.6 hanging 10.5 from the top wall)", "L6 100 N knock -> 260 N at the journal, lever 6.5",
    "abuse", 260 * 6.5 / (math.pi / 4 * (30.6 ** 4 - 26.65 ** 4) / 30.6), "the tube is merged with the shell at az 90 / 270 and the gussets")
# S7 door
row("S7a", "door finger notch edge 12 x 1.35 (lever 0.85)", "prying with a nail 10 N, L7 100x", "normal", 10 * 0.85 / (12 * 1.35 ** 2 / 6))
row("S7b", "door top lip 1.2 x 0.75 (no catch: moves away from the tongue on opening)", "none (magnets hold the door, 4 x 6 N)", "normal", 0.0001,
    "the lip only takes handling knocks")
row("S7c", "door / frame magnet bonds (row 56)", "pull-off 6 N per magnet on D5 x 2 pocket wall + floor", "epoxy", 6.0 / (math.pi * 5.1 * 2.0 + math.pi * 2.55 ** 2))
# S8 speaker ring
# closed ring r 13 .. 16.5 (b 3.5), 3 clamped ears 120 deg apart -> by symmetry each span is fixed-fixed: M_support = q L^2 / 12 at the
# 0.3 step (t 1.7), M_mid = q L^2 / 24 at the flat top (b 1.7, t 2.0); q = gasket push / circumference r 13.5
Lr = 2 * math.pi * 14.75 / 3
for W, role, lab_ in ((6.0, "check", "PORON 4701-40 class 1.0 -> 0.85 (15 %, about 0.035 MPa x 171 mm2, UNVERIFIED)"),
                      (8.5, "info", "firm foam 0.05 MPa (upper estimate)")):
    q = W / (2 * math.pi * 13.5)
    row(f"S8a {W:.0f} N", "speaker ring at the washer step (b 3.5 x t 1.7), fixed-fixed span %.1f" % Lr, f"gasket push {W} N ({lab_})", "sustained",
        q * Lr ** 2 / 12 / (3.5 * 1.7 ** 2 / 6), role=role)
    row(f"S8b {W:.0f} N", "speaker ring mid-span at the flat top (b 1.7 x t 2.0)", f"gasket push {W} N", "sustained",
        q * Lr ** 2 / 24 / (1.7 * 2.0 ** 2 / 6), role=role)
OUT["S_strength"] = dict(rows=S, all_ok=all(s["ok"] is not False for s in S if s.get("role", "check") in ("check", "recommended torque")),
                         spec_torque_failures=[dict(id=s["id"], stress=s["stress_MPa"], allow=s["allowable_MPa"]) for s in S
                                               if s.get("role") == "spec torque" and s["ok"] is False],
                         note="hand calculations on the rev. 2 geometry with the Z2 allowables (normal 8.5 / sustained 4.3 / abuse 12.9 / epoxy "
                              "2.7 MPa incl. stress concentration); rows from overenie_pevnost.md 39, 41, 46 (OBAL side), 53, 54-56, 57, 59, 60, m16, "
                              "m19; S1c is an estimate (impact force assumed) and needs K12 / a drop test")
say("S", [(s["id"], s.get("stress_MPa"), s.get("allowable_MPa"), s["ok"]) for s in S])

# ------------------------------------------------------------------------------------------------------------ merge
for f, key in (("mesh_checks2.json", None), ("k8_obal.json", "K8")):
    pth = os.path.join(HERE, "obal2_work", f)
    if os.path.exists(pth):
        d = json.load(open(pth))
        if key:
            OUT[key] = dict(exterior_ok=d.get("exterior_vs_T3", {}).get("ok"), n_bad_strict=d.get("exterior_vs_T3", {}).get("n_bad_strict"),
                            zones=d.get("exterior_vs_T3", {}).get("zones"), see_through=d.get("see_through_26", {}).get("see_through"),
                            rays=d.get("see_through_26", {}).get("rays"), pitch=d.get("see_through_26", {}).get("pitch"),
                            views=[v for v in d.get("see_through_26", {}).get("views", []) if v["see_through"]],
                            time_s=d.get("time_s"), file="obal2_work/k8_obal.json")
        else:
            OUT.update(d)
summ = dict(O1=OUT["O1_solids"]["all_ok"], O3=o3["ok"], O4=OUT["O4_seats"]["all_ok"], O5=OUT["O5_inside"]["all_ok"], R=OUT["R_resin"]["ok"],
            S=OUT["S_strength"]["all_ok"])
for k, key, f in (("O2", "O2_interference", "all_ok"), ("M1", "M1_watertight", "all_ok"), ("M2", "M2_wall", "ok"), ("M3", "M3_exterior", "ok"),
                  ("S1", "S1_seam_backing", "ok")):
    summ[k] = OUT.get(key, {}).get(f, "not run")
summ["K8"] = (OUT["K8"]["exterior_ok"] and OUT["K8"]["see_through"] == 0) if "K8" in OUT else "not run"
OUT["summary"] = summ
OUT["time_s"] = round(time.time() - T0, 1)
json.dump(OUT, open(os.path.join(HERE, "checks_obal.json"), "w"), indent=1, ensure_ascii=False, default=float)
say("summary", summ)
say("written checks_obal.json", OUT["time_s"], "s")
