#!/opt/venv/cad/bin/python
"""rev3 documents from the COMPUTED results (no hand-typed numbers; fix-back after overenie3: + fixback3_work/fe_gap results, STL boxes):
    /opt/venv/cad/bin/python rev3_work/mk_docs.py [results.json]
writes opravy3.md, T4_spec.md section 17.17 (replaced if present), out/zmeny_rev3.txt, rev3_work/summary.json."""
import os, sys, json, math
T4 = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, T4)
import t4_common as C
R3 = C.R3; P = R3["PIVOT"]
RES = sys.argv[1] if len(sys.argv) > 1 else os.path.join(T4, "fe_sachta", "results.json")
OUTD = os.environ.get("MKDOCS_OUT", T4)        # dry runs write elsewhere
R = json.load(open(RES))
rows = [r for r in R["rows"] if r["cls"] != "failsafe"]
LEVER = 50.0            # mm: hand force at the side of the head (head shell 110 wide) for the torque limits

SIT = [("L1_lift0", "zdvihnutie robota za hlavu, krk zasunutý (ťah nahor)", "robot lifted by the head, neck parked (pull up)", "F"),
       ("L1_lift20c", "ťah za hlavu nahor, krk vysunutý", "pull up on the head, neck extended", "F"),
       ("L2_lift0_chain", "tlak na hlavu nadol, krk zasunutý (pred dosadnutím pätky)", "push down on the head, neck parked (before the foot lands)", "F"),
       ("L2_lift0_landed", "tlak na hlavu nadol, krk zasunutý (pätka dosadnutá)", "push down, neck parked (foot landed)", "F"),
       ("L2_lift10", "tlak na hlavu nadol, krk v polovici zdvihu", "push down, neck at mid lift", "F"),
       ("L2_lift20c", "tlak na hlavu nadol, krk vysunutý", "push down, neck extended", "F"),
       ("L3_twist_ccw", "otáčanie hlavy rukou proti servu (doľava)", "head turned by hand against the pan servo (ccw)", "T"),
       ("L3_twist_cw", "otáčanie hlavy rukou proti servu (doprava)", "head turned by hand against the pan servo (cw)", "T"),
       ("L8_stop_p90", "moment do dorazu +90° (servo zaseknuté / ruka)", "torque into the +90 deg hard stop (servo stall / hand)", "T"),
       ("L8_stop_m90", "moment do dorazu -90° (servo zaseknuté / ruka)", "torque into the -90 deg hard stop (servo stall / hand)", "T")]
spec = {c: R["cases"][c] for c in R["cases"]}
LOAD = {"L1_lift0": 30.0, "L1_lift20c": 30.0, "L2_lift0_chain": 30.0, "L2_lift0_landed": 30.0, "L2_lift10": 30.0, "L2_lift20c": 30.0,
        "L3_twist_ccw": 600.0, "L3_twist_cw": 600.0, "L8_stop_p90": 880.0, "L8_stop_m90": 880.0}

worst = {}                                  # per case: worst utilisation row
for r in rows:
    u = r["stress"] / r["allowable"]
    if r["case"] not in worst or u > worst[r["case"]][0]:
        worst[r["case"]] = (u, r)
limits = []; allcases = []
for c, sk, en, kind in SIT:
    if c not in worst:
        continue
    u, r = worst[c]
    cap = LOAD[c] / u
    d = dict(case=c, sk=sk, en=en, spot=f"{r['spot']} [{r['part']}]", stress=r["stress"], allowable=r["allowable"], cls=r["cls"], util=round(u, 3), fails=bool(u > 1.0))
    if kind == "F":
        d.update(capacity_N=round(cap, 1), kg=round(cap / 9.81, 1), ref=f"{LOAD[c]:.0f} N",
                 note=f"FE load {LOAD[c]:.0f} N -> {r['stress']} MPa vs {r['allowable']} ({r['cls']})")
    else:
        d.update(capacity_Nmm=round(cap), capacity_N=round(cap / LEVER, 1), kg=round(cap / LEVER / 9.81, 2), ref=f"{LOAD[c]:.0f} N.mm",
                 note=f"{cap:.0f} N.mm about the pan axis = {cap / LEVER:.1f} N at the side of the head (lever {LEVER:.0f} mm); FE load {LOAD[c]:.0f} N.mm -> "
                      f"{r['stress']} MPa vs {r['allowable']} ({r['cls']})")
    allcases.append(d)
    if u > 1.0:
        limits.append(d)

# ---- pan servo (STS3032 on the 18T pinion, stage gear 36T): stall 2 x 0.441 = 0.88 N.m at the stage; 4096 steps per servo turn
RATIO = C.R2["GEAR_PAN"]["z"][1] / C.R2["GEAR_PAN"]["z"][0]; STALL = 880.0
STEPS_85 = int(round(85.0 * RATIO / 360.0 * 4096))

# ---- TRUE reprint list: every printed STL against the rev. 2 set (rev3_backup/stl) by mesh volume + bounding box
import struct, hashlib
import numpy as np


def _stl(pth):
    bb = open(pth, "rb").read(); n = struct.unpack("<I", bb[80:84])[0]
    a = np.frombuffer(bb, dtype=np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")]), count=n, offset=84)["v"].astype(float)
    return float(np.einsum("ij,ij->i", a[:, 0], np.cross(a[:, 1], a[:, 2])).sum() / 6), np.r_[a.reshape(-1, 3).min(0), a.reshape(-1, 3).max(0)]


PJ = json.load(open(os.path.join(T4, "parts.json")))["parts"]
PJ = list(PJ.values()) if isinstance(PJ, dict) else PJ
reprint, same, other = [], [], []
for pr in PJ:
    n = pr["name"]; fa = os.path.join(T4, "stl", n + ".stl"); fb = os.path.join(T4, "rev3_backup", "stl", n + ".stl")
    if not os.path.exists(fa):
        continue
    if not os.path.exists(fb):
        (reprint if pr.get("printed") else other).append(dict(name=n, new=True)); continue
    if hashlib.md5(open(fa, "rb").read()).hexdigest() == hashlib.md5(open(fb, "rb").read()).hexdigest():
        if pr.get("printed"):
            same.append(n)
        continue
    (va, ba), (vb, bb_) = _stl(fa), _stl(fb); dv = va - vb; db = float(np.abs(ba - bb_).max())
    if abs(dv) > 0.05 or db > 0.005:
        (reprint if pr.get("printed") else other).append(dict(name=n, dvol=round(dv, 2), dbbox=round(db, 3), vol=round(va, 1)))
    elif pr.get("printed"):
        same.append(n)
RP = [x["name"] for x in reprint]

# per spot: worst case (all kinds)
spots = {}
for r in rows:
    k = (r["part"], r["spot"]); u = r["stress"] / r["allowable"]
    if k not in spots or u > spots[k][0]:
        spots[k] = (u, r)
fe_rows = [dict(spot=f"{r['spot']} [{r['part']}]", case=f"{r['case']} ({r['cls']})", kind=r.get("kind", "structure"), stress=r["stress"], allowable=r["allowable"], ok=bool(r["ok"]))
           for u, r in sorted(spots.values(), key=lambda t: -t[0])]
nfail_rows = sum(not r["ok"] for r in rows); nfail_spots = sum(not f["ok"] for f in fe_rows)
fs = R.get("failsafe_worst", [])

# checks
ck = {}
f = os.path.join(T4, "checks.json")
if os.path.exists(f):
    cj = json.load(open(f))
    res_ = cj.get("results") or cj.get("checks") or cj
    for k in [f"K{i}" for i in range(1, 14)]:
        v = res_.get(k) if isinstance(res_, dict) else None
        if isinstance(v, dict):
            ck[k] = dict(status=v.get("status"), text=str(v.get("value", v.get("summary", v.get("text", ""))))[:300])
hand = {}
f = os.path.join(T4, "pan_checks.json")
if os.path.exists(f):
    pj = json.load(open(f)); H = (pj.get("H_strength") or pj.get("results", {}).get("H_strength") or {})
    for r in H.get("rows", []):
        hand.setdefault(r["n"], []).append(r)


def hrow(n, key=""):
    out = [r for r in hand.get(n, []) if key in r["feature"]]
    return "; ".join(f"{r['load_case']}: {r['stress']} / {r['limit']} {r['verdict']}" for r in out) or "n/a (pan_checks.json H missing)"


def md_fe(nmax=60):
    L = ["| spot | worst case (class) | kind | stress MPa | allowable | ok |", "|---|---|---|---|---|---|"]
    for r in fe_rows[:nmax]:
        L.append(f"| {r['spot']} | {r['case']} | {r['kind']} | {r['stress']} | {r['allowable']} | {'ok' if r['ok'] else '**FAIL**'} |")
    return "\n".join(L)


stop_all = {l["case"]: l for l in allcases if l["case"].startswith("L8")}
stop_caps = [l for l in limits if l["case"].startswith("L8")]
stop_min = min((l["capacity_Nmm"] for l in stop_all.values()), default=None)          # abuse capacity of the weaker stop (N.mm at the stage)
stop_weak = min(stop_all.values(), key=lambda l: l["capacity_Nmm"]) if stop_all else None
pct = round(100.0 * stop_min / STALL) if stop_min else None
# lead: "2 x servo torque <= the abuse capacity of the weaker stop" -> torque limit (per cent of the stall), rounded DOWN to 5 %
tq_pct = (min(100, max(5, int(math.floor(100.0 * stop_min / (2.0 * STALL) / 5.0)) * 5)) if stop_min else None)
tq_Nmm = round(tq_pct / 100.0 * STALL) if tq_pct else None


Ld, Sh, Rl = R3["RAIL"]["ledge"], R3["RAIL"]["shelf"], R3["RAIL"]
Cb, Cw = R3["CURB"], R3["STOP"]["cw_face"]
a_curb = json.load(open(os.path.join(T4, "fe_sachta", "design.json")))["bearing"]["curb_y"]      # engaged seat area (t4_pan.fe_bearing)
F_cw = STALL / Cw["lever"]

# ================================================================================================ fix-back after overenie3 (2026-11-23)
# V1: the -90 deg stop of the final set assumes a CLOSED sole / curb seat (pair 'curb_y', gap 0).  fixback3_work/fe_gap.py re-runs the same
#     case (same STL stamp, design.json, h, harness) with a clearance at that pair; <tag>/L8_stop_m90_curb.json + _rows.json.  Nothing is typed:
#     a variant that is missing / belongs to another STL set / is not converged is reported as "not computed".
GAPD = os.path.join(T4, "fixback3_work", "fe_gap")


def _gapcase(tag):
    f = os.path.join(GAPD, tag, "L8_stop_m90_curb.json"); fr = os.path.join(GAPD, tag, "L8_stop_m90_rows.json")
    if not (os.path.exists(f) and os.path.exists(fr)):
        return None
    d = json.load(open(f))
    if d.get("stl_stamp") != R["stl_stamp"] or abs(d["h"] - R["h"]) > 1e-9 or not d["solver"]["converged"] or not d["equilibrated"]:
        return None
    rr = [r for r in json.load(open(fr)) if r["cls"] != "failsafe"]
    w = max(rr, key=lambda r: r["stress"] / r["allowable"])          # the same rule as the usage limits: worst utilisation of all rows
    d.update(worst=w, util=w["stress"] / w["allowable"], sig=w["stress"], allow=w["allowable"], cap=STALL * w["allowable"] / w["stress"],
             curb_N=d["pair_forces"]["curb_y"]["sum"], curb_active=d["pair_forces"]["curb_y"]["n_active"], closing=-d["rel_min"])
    return d


G_OPEN = _gapcase("open_h05")                    # curb contact switched off (clearance 5 mm): the seat never closes
G_VAR = {}                                       # other clearances at the full 880 N.mm, by gap
if os.path.isdir(GAPD):
    for _t in sorted(os.listdir(GAPD)):
        _g = _gapcase(_t) if os.path.isdir(os.path.join(GAPD, _t)) and _t != "open_h05" else None
        if _g:
            G_VAR[round(_g["gap"], 4)] = _g
U0 = stop_all["L8_stop_m90"]["stress"] / stop_all["L8_stop_m90"]["allowable"] if "L8_stop_m90" in stop_all else None            # closed seat (final set): utilisation of the governing row
ALLOW_M90 = stop_all["L8_stop_m90"]["allowable"] if "L8_stop_m90" in stop_all else 12.9
LB = 25.8                                        # lower-bound strength (T4_zivica); abuse allowable = LB / 2


def u880(G):
    """utilisation of the governing row at 880 N.mm with a seat clearance G (mm): linear interpolation between the computed FE points
    (G = 0 closed = final set, the clearance variants, G >= the closing travel of the open model = open); None when the open model is missing"""
    if G_OPEN is None or U0 is None:
        return None
    pts = sorted([(0.0, U0)] + [(g, v["util"]) for g, v in G_VAR.items() if g < G_OPEN["closing"]] + [(G_OPEN["closing"], G_OPEN["util"])])
    if G >= pts[-1][0]:
        return pts[-1][1]
    for (g0, s0), (g1, s1) in zip(pts, pts[1:]):
        if g0 <= G <= g1:
            return s0 + (s1 - s0) * (G - g0) / max(g1 - g0, 1e-12)


def u_at(T, g):
    """linear elasticity + contact: the state at torque T with clearance g is (T / 880) x the state at 880 N.mm with clearance g x 880 / T"""
    u = u880(g * STALL / T) if g > 0 else U0
    return None if u is None else u * T / STALL


def cap_gap(g, factor=1.0):
    """torque at which the governing row reaches factor x its allowable with a seat clearance g (bisection on u_at; factor 2 = lower bound)"""
    if u_at(STALL, g) is None:
        return None
    lo, hi = 1.0, 20000.0
    for _ in range(70):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if u_at(mid, g) < factor else (lo, mid)
    return 0.5 * (lo + hi)


GAP_OK = 0.05                                    # bench acceptance of the seat: "no light, the 0.05 feeler does not enter"
GAP_OLD = 0.10                                   # acceptance of the first rev. 3 text ("the 0.10 feeler must not enter")
GAP_INF = 99.0                                   # seat open at every load
V1 = None
if G_OPEN is not None and stop_min:
    cap_open = G_OPEN["cap"]; cap_closed = STALL / U0
    # torque limit when the seat was not closed / not checked: 2 x limit <= the capacity with the seat open, rounded DOWN to 5 %
    tq_open_pct = max(5, int(math.floor(100.0 * cap_open / (2.0 * STALL) / 5.0)) * 5)
    GS = (GAP_OK, GAP_OLD)
    V1 = dict(cap_open=cap_open, cap_closed=cap_closed, sig_open=G_OPEN["sig"], allow_open=G_OPEN["allow"], spot_open=f"{G_OPEN['worst']['spot']} at {G_OPEN['worst'].get('at')}",
              closing_880=G_OPEN["closing"], T_close={g: STALL * g / G_OPEN["closing"] for g in GS},
              # governing stress of the OPEN model at the torque at which a clearance g closes (the seat is still unloaded up to there)
              sig_close={g: G_OPEN["sig"] * g / G_OPEN["closing"] for g in GS},
              # clearance above which the open model reaches its allowable BEFORE the seat closes: the capacity is then the open-seat value
              g_crit=G_OPEN["closing"] * G_OPEN["allow"] / G_OPEN["sig"],
              cap={g: cap_gap(g) for g in GS}, cap_break={g: cap_gap(g, LB / ALLOW_M90) for g in (0.0, GAP_OK, GAP_OLD, GAP_INF)},
              sig_tq={g: u_at(tq_Nmm, g) * ALLOW_M90 for g in (0.0, GAP_OK, GAP_OLD, GAP_INF)},
              sig_2tq={g: u_at(2.0 * tq_Nmm, g) * ALLOW_M90 for g in (0.0, GAP_OK, GAP_OLD, GAP_INF)},
              tq_open_pct=tq_open_pct, tq_open_Nmm=tq_open_pct / 100.0 * STALL,
              variants={g: dict(sig=v["sig"], allow=v["allow"], curb_N=v["curb_N"], curb_active=v["curb_active"], spot=f"{v['worst']['spot']} at {v['worst'].get('at')}",
                                equivalent=f"= clearance {GAP_OLD:.2f} at {STALL * GAP_OLD / g:.0f} N.mm, {GAP_OK:.2f} at {STALL * GAP_OK / g:.0f} N.mm")
                        for g, v in sorted(G_VAR.items())},
              pair_open={k: G_OPEN["pair_forces"][k]["sum"] for k in ("curb_y", "padC_y", "padD_y", "padA_y", "padB_y", "dowel_x") if k in G_OPEN["pair_forces"]})
    # verdict on the verifier's claim "the capacity and the factor 2 hold only with zero gap": is the capacity lower / is twice the torque limit above the allowable
    # with a clearance up to the 0.10 that the first rev. 3 text of T9 accepted?
    V1["lower_with_gap"] = {g: bool(V1["cap"][g] < 0.98 * cap_closed) for g in GS}
    V1["twice_limit_over_allowable"] = {g: bool(V1["sig_2tq"][g] > ALLOW_M90 + 1e-9) for g in GS}
    V1["confirmed_as_stated"] = bool(any(V1["lower_with_gap"].values()) or any(V1["twice_limit_over_allowable"].values()))
# V6 / V7: numbers of two builder notes, from the STL sets and R3
_zz = lambda n, d="stl": _stl(os.path.join(T4, d, n + ".stl"))[1]
PT_NEW, PT_OLD, CAPBB = _zz("ptfe_cap"), _zz("ptfe_cap", os.path.join("rev3_backup", "stl")), _zz("T_cap")
ptfe_h, ptfe_h_old, ptfe_lo = PT_NEW[5] - PT_NEW[2], PT_OLD[5] - PT_OLD[2], PT_NEW[2] - CAPBB[2]
SPL_TIP = _zz("servo_pan")[5]; SPL_BOSS = C.R2["PAN_SERVO"]["boss_top"]
SPL_LEN = SPL_TIP - SPL_BOSS                                                            # modelled spline length above the boss face (UNVERIFIED)
SPL_ROOF = R3["FLOOR"]["z"][0] + R3["FLOOR"]["spline_relief"]["depth"]                  # underside of the relieved floor over the spline tip
SPL_CLR = SPL_ROOF - SPL_TIP
# V2: F12 screw / ear flange / module face (STL bounding boxes)
F12BB, EARBB, MODBB = _zz("skr_F12_1"), _zz("L_ucho"), _zz("P_drziak_serva")
F12_LEN = F12BB[4] - F12BB[1]; F12_PLAY = MODBB[1] - F12BB[4]; F12_BEHIND = MODBB[1] - EARBB[1] - 1.5      # ear flange 1.5 thick (y 9.9 .. 11.4)
F12_ENG = _zz("L_pata")[4] - F12BB[1]                                                 # thread length inside the foot when seated
F12_START = F12_ENG - F12_PLAY                                                        # module travel left when the tip of the backed-off screw meets the foot face
F12_PITCH = 0.4                                                                       # M2
# V11: every fail-safe row above the lower bound, with the load at which it reaches it
fs_rows = sorted([r for r in R["rows"] if r["cls"] == "failsafe" and not r["ok"]], key=lambda r: -r["stress"])
k7_status = (ck.get('K7') or dict()).get('status')
fs_all_txt = "; ".join(f"{r['spot']} {r['stress']} / {r['allowable']} in {r['case']} (reaches {r['allowable']} at {30.0 * r['allowable'] / r['stress']:.1f} N; at {r['at']})"
                       for r in fs_rows) or "none"
SIG_M90 = stop_all["L8_stop_m90"]["stress"] if "L8_stop_m90" in stop_all else None
_capN = {l["case"]: l["capacity_N"] for l in allcases if "capacity_Nmm" not in l}          # usage limit (or the 30 N plan load capacity) of the bonded case
fs_scaled = "; ".join(f"{r['stress'] * min(30.0, _capN.get(r['case'].replace('_nobond', ''), 30.0)) / 30.0:.1f} MPa at "
                      f"{min(30.0, _capN.get(r['case'].replace('_nobond', ''), 30.0)):.1f} N ({r['case']})" for r in fs_rows) or "n/a"
if V1:
    _v = V1; _c0 = stop_all["L8_stop_m90"]["capacity_Nmm"]
    _var = "; ".join(f"clearance {g:.2f} at {STALL:.0f} N.mm ({v['equivalent']}): {v['sig']} / {v['allow']} MPa ({v['spot']}), curb force {v['curb_N']} N on {v['curb_active']} nodes"
                     for g, v in _v["variants"].items()) or "no intermediate clearance computed"
    if _v["confirmed_as_stated"]:
        _verdict = (f"Verdict: REAL as stated - with a clearance of {GAP_OK:.2f} / {GAP_OLD:.2f} mm the capacity is {_v['cap'][GAP_OK]:.0f} / {_v['cap'][GAP_OLD]:.0f} N.mm (closed {_c0}) and twice the "
                    f"{tq_pct} % limit gives {_v['sig_2tq'][GAP_OK]:.1f} / {_v['sig_2tq'][GAP_OLD]:.1f} MPa (allowable {ALLOW_M90})")
    else:
        _verdict = (f"Verdict: the seat IS needed and cannot be checked in the assembled torso (real), but the claim 'only with zero gap' is NOT confirmed: a clearance up to "
                    f"{GAP_OLD:.2f} mm closes at {_v['T_close'][GAP_OLD]:.0f} N.mm, where the governing stress is {_v['sig_close'][GAP_OLD]:.1f} MPa (< {ALLOW_M90}), and the capacity at the "
                    f"allowable stays {_v['cap'][GAP_OK]:.0f} / {_v['cap'][GAP_OLD]:.0f} N.mm for {GAP_OK:.2f} / {GAP_OLD:.2f} mm (closed {_c0}); twice the {tq_pct} % limit gives "
                    f"{_v['sig_2tq'][GAP_OK]:.1f} / {_v['sig_2tq'][GAP_OLD]:.1f} MPa (<= {ALLOW_M90}).  The verifier's hand estimate (12.9 MPa at about 100 - 160 N.mm with a 0.1 gap) "
                    f"is not confirmed.  The CLIFF is at {_v['g_crit']:.2f} mm: from there the allowable is reached before the seat closes and the capacity is the open-seat value")
    v1_en = (f"FE of the final L8_stop_m90 case with a clearance at the pair curb_y (fixback3_work/fe_gap.py; same STL stamp, design.json, h {R['h']}, harness unchanged).  "
             f"Seat OPEN: governing row {_v['sig_open']} / {_v['allow_open']} MPa at {STALL:.0f} N.mm ({_v['spot_open']}) = capacity {_v['cap_open']:.0f} N.mm "
             f"(closed seat: {SIG_M90} MPa, {_c0} N.mm); pair forces open: pad A {_v['pair_open'].get('padA_y')} N, pad C {_v['pair_open'].get('padC_y')}, pad D {_v['pair_open'].get('padD_y')}, "
             f"dowel x {_v['pair_open'].get('dowel_x')}; the sole travels {_v['closing_880']:.3f} mm toward the curb at {STALL:.0f} N.mm, i.e. a clearance of {GAP_OK:.2f} / {GAP_OLD:.2f} mm closes at "
             f"{_v['T_close'][GAP_OK]:.0f} / {_v['T_close'][GAP_OLD]:.0f} N.mm.  {_var}.  By load scaling (state at T with clearance g = T / 880 x state at 880 N.mm with g x 880 / T; "
             f"linear interpolation of the governing utilisation between the computed clearances): governing stress at the {tq_pct} % torque limit ({tq_Nmm} N.mm) / at twice that: "
             f"closed {_v['sig_tq'][0.0]:.1f} / {_v['sig_2tq'][0.0]:.1f}, {GAP_OK:.2f}: {_v['sig_tq'][GAP_OK]:.1f} / {_v['sig_2tq'][GAP_OK]:.1f}, {GAP_OLD:.2f}: {_v['sig_tq'][GAP_OLD]:.1f} / "
             f"{_v['sig_2tq'][GAP_OLD]:.1f}, open: {_v['sig_tq'][GAP_INF]:.1f} / {_v['sig_2tq'][GAP_INF]:.1f} MPa (allowable {ALLOW_M90}, lower bound {LB}); the lower bound {LB} is reached at "
             f"{_v['cap_break'][0.0]:.0f} (closed) / {_v['cap_break'][GAP_OK]:.0f} ({GAP_OK:.2f}) / {_v['cap_break'][GAP_OLD]:.0f} ({GAP_OLD:.2f}) / {_v['cap_break'][GAP_INF]:.0f} (open) N.mm.  {_verdict}")
    v1_short = (f"with the seat OPEN the -90 deg stop reaches its allowable at {_v['cap_open']:.0f} N.mm ({_v['cap_open'] / LEVER:.1f} N at the side of the head) instead of {_c0}; the "
                f"{tq_pct} % limit ({tq_Nmm} N.mm) then gives {_v['sig_tq'][GAP_INF]:.1f} MPa and twice the limit {_v['sig_2tq'][GAP_INF]:.1f} MPa (allowable {ALLOW_M90}, lower bound {LB}).  "
                f"A residual clearance of {GAP_OK:.2f} / {GAP_OLD:.2f} mm closes at {_v['T_close'][GAP_OK]:.0f} / {_v['T_close'][GAP_OLD]:.0f} N.mm ({_v['sig_close'][GAP_OK]:.1f} / "
                f"{_v['sig_close'][GAP_OLD]:.1f} MPa there): capacity {_v['cap'][GAP_OK]:.0f} / {_v['cap'][GAP_OLD]:.0f} N.mm, twice the limit {_v['sig_2tq'][GAP_OK]:.1f} / "
                f"{_v['sig_2tq'][GAP_OLD]:.1f} MPa; from a clearance of {_v['g_crit']:.2f} mm on the capacity is the open-seat value.  Bench acceptance {GAP_OK:.2f} mm.  "
                f"If the seat was not checked / bedded: EEPROM torque limit {_v['tq_open_pct']} % (= {_v['tq_open_Nmm']:.0f} N.mm, 2 x that <= {_v['cap_open']:.0f}).")
else:
    v1_en = ("NOT COMPUTED: fixback3_work/fe_gap/open_h05 has no converged result for the current STL stamp - run "
             "'/opt/venv/cad/bin/python fixback3_work/fe_gap.py 5.0 0.5 open_h05' and this script again")
    v1_short = "the capacity with an open seat is not computed (see the fix-back section)."


def cap_txt(l):
    if "capacity_Nmm" in l:
        return "%d N.mm = %.1f N (about %.1f kg) at the side of the head" % (l["capacity_Nmm"], l["capacity_N"], l["kg"])
    return "%.1f N (about %.1f kg)" % (l["capacity_N"], l["kg"])


lim_md = "\n".join(f"| {l['en']} | {cap_txt(l)} | {l['spot']} | {l['note']} |" for l in limits) or "| none | | | |"
ok_md = "; ".join(f"{l['en']} ({l['ref']}): worst row {l['stress']} / {l['allowable']}" for l in allcases if not l["fails"]) or "none"
fs_txt = "; ".join(f"{x['spot']} {x['stress']} / {x['allowable']} {'ok' if x['ok'] else 'ABOVE'} ({x['case']})" for x in fs[:4]) or "n/a"
fs_bad = [x for x in fs if not x["ok"]]
cs = R["cases"]
dsp = {c: (cs[c].get("disp") or {}) for c in ("L1_lift20c_nobond", "L1_lift0_nobond") if c in cs}
fs_lift = "; ".join(f"{c}: rise of the well {P['axial_play']} play + {d.get('uz_well_max')} = {P['axial_play'] + max(0.0, d.get('uz_well_max') or 0.0):.3f} mm (limit 0.3)" for c, d in dsp.items()) or "n/a"
pf = lambda c, k: (cs.get(c, {}).get("pair_forces_on_pocket", {}).get(k) or {}).get("sum") if isinstance(cs.get(c, {}).get("pair_forces_on_pocket", {}).get(k), dict) else cs.get(c, {}).get("pair_forces_on_pocket", {}).get(k)
pfm = {k: pf("L8_stop_m90", k) for k in ("curb_y", "padD_y", "padA_y", "padB_y", "dowel_x")}
ckline = "  ".join(f"{k}:{v['status']}" for k, v in ck.items()) or "checks.json missing"
rp_md = ", ".join(f"{x['name']} ({'new' if x.get('new') else 'dV %+.1f mm3, bbox %.3f' % (x['dvol'], x['dbbox'])})" for x in reprint)
oth_md = ", ".join(x["name"] for x in other)

OPR = f"""# T4 rev. 3 - strengthening of the rotating well (opravy3)

Fixer rounds 1 (2026-11-22), 1b / 1c / 1d (2026-11-23; three interruptions - STATUS_rev3_fixer.md).  Inputs: T4_rev3_sachta_plan.md (R3-1 .. R3-9),
lead decisions LD1 - LD7.  Numbers: `t4_common.R3`; text: T4_spec.md 17.17; FE: `fe_sachta/run_fe.py` -> `fe_sachta/results.json`
(STL stamp {R['stl_stamp']}, h {R['h']}, {R['n_rows']} rows, generated {R['generated']}).  Backups: `rev3_backup/` (*.bak = rev. 2, *.v6 / *.v9 / *.v10a / *.v10c; *.v10d / *.pre_fixback3 = state before the fix-back after overenie3, last section).
Generated by `rev3_work/mk_docs.py` from the computed results (no hand-typed result numbers).

## Result
{nfail_spots} spots ({nfail_rows} rows) of the final FE set exceed their allowable at the plan loads; none is hidden - each is a usage limit below.
Cases within their allowables: {ok_md}.
Checks: {ckline}.

## Findings -> change -> number
| finding | change (rev. 3) | number |
|---|---|---|
| S1 / B1 F15 thread 0.8 mm | ISO 7380 M3x{P['screw_len']:.0f} + 2 x DIN 125 M3 under the DIN 9021 (no screw cutting); bench step B2b (one more DIN 125 under the head if the tip stands proud) | engagement in T_most {P['engagement_nominal']} nominal / {P['engagement_min']} min (>= 1.5) |
| S2 lens hub ring <-> front wall | R3-3 option (b): real floor z {R3['FLOOR']['z'][0]} .. {R3['FLOOR']['z'][1]} over the whole well, R{R3['FLOOR']['root_r']} roots; pan pinion face 3.0 (top {R3['FLOOR']['pinion_top']}) | FE rows 'lens' / 'hub ring'; option (a) failed L3 with 39.6 - 40.6 MPa (res/var_lens_h06) |
| S3 retention through the bond only | R3-2 positive: the DIN 9021 (r {P['washer_r']}) overlaps the hub lip of the WELL (lip top {R3['LIP']['z_top']}, overlap {R3['LIP']['overlap_nominal']} / {R3['LIP']['overlap_min']} min); axial play {P['axial_play']} ({P['axial_play_range'][0]} - {P['axial_play_range'][1]}) | fail-safe FE (bond failed): {fs_lift} |
| S4 / B11 sharp window corners | R{R3['WIN']['corner_r']} on every window corner and sill / jamb, R{R3['WIN']['end']['top_r']} at the top corners of the +X end window, lintel 2.3, end-window top -16.9; curb z {R3['WIN']['end']['sill_z']} (y >= {R3['WIN']['end']['sill_y0']}) at the +X pillar foot | FE rows 'window corners', '+X pillar' |
| S5 slim corners / journal band | inner corners R{R3['CORNER_RI']}, guide band 2.3 from z -17.5 up, journal ring down to z {R3['RING_EXT']['z'][0]} over the front half | FE rows 'slim corner arcs' |
| S6 / B8 rail of the lift module | UP: block top under the ledge rib x {Ld['x'][0]} .. {Ld['x'][1]}; DOWN: ceiling of a closed plate window on a shelf z {Sh['z_bot']} .. {Sh['z_top']}; x / z: F10 dowel D2 x {Rl['dowel']['len']:.0f}; y: pads A - E + 2 x F10 (F10_A at x {R3['F10_A'][0]}) + sill curb (LD7) | hand: ledge {hrow(12, 'bearing')}; shelf {hrow(13, 'down stop')}; FE contact rows |
| S7 rest gap vs MG90S toggle | gap {R3['REST_GAP']['nominal_bdc']} at BDC, feeler {R3['REST_GAP']['feeler_ok'][0]} / {R3['REST_GAP']['feeler_ok'][1]}; firmware never below PARK_DEG ({R3['REST_GAP']['park_deg_ok']:.0f} deg calibrated, {R3['REST_GAP']['park_deg_default']:.0f} deg default) | step T11 |
| S8 T_cap root | root R{P['cap_root_r']}, hole drilled D{P['cap_hole']}, axial play >= {P['axial_play']} | t4_ram_checks C6 / S |
| S9 washer on a chamfered gear bore | the washer holds the WELL lip, not the gear; lower gear-bore edge chamfered {P['gear_bore_chamfer']} x 45 deg | overlap {R3['LIP']['overlap_min']} min |
| S10 / B2 free-hanging shroud arch | roof at floor level over the shroud top (r <= {R3['SHROUD']['roof_r']}), R{R3['SHROUD']['root_r']} root | FE row 'drum shroud' |
| S11 thin skins | dowel hole 2.9 deep (skin 1.2); floor 0.95 over the FFC groove and 1.05 over the spline relief declared | FE row 'thin floor' |
| S16 K12 rows | bond area, H3 / A7d / S06b / TQ rows corrected; FE rows of every critical spot from results.json | checks.json K12 |
| B3 landing face | supports allowed on the inner floor face (tips 0.3 - 0.4, pitch <= 3), sanded flat | builder note |
| B4 / B5 bonds | T_cap hole D{P['cap_hole']} drilled after curing; toughened 2K epoxy 0.1 - 0.2 on abraded + IPA-cleaned faces | FE bond rows (nominal, LD1) |
| B7 F10 over-torque | fingertip case 0.10 N.m kept; Loctite 222 | pan H rows 15 / 27 |
| B10 / B12 / B13 | towel under the bare stage; PTFE-compatible grease, play check at service; no long holds at mid lift | documents |

## Lead decisions
* **LD1 contact zones** - post.py: structure rows use only surface points >= 1.0 mm (+ h / 2) from every ACTIVE contact (pair nodes, true patches of
  the vertical stops, clamped F10 pads incl. the washer disc r 2.25 on both plate faces (round 1d), dowel, stop line, servo load patches); the peak inside is
  information.  Every contact has a row nominal pressure = pair force / engaged area; supporting sections by hand: ledge web {hrow(12, 'web')}; shelf root {hrow(13, 'high on the plateau')}.
  Gear bond: nominal average shear / tension vs 2.7 / 4.0; edge peak = information.
* **LD2 load classes** - L1 (2 x 15 N) / L2 (30 N) at lift 0 normal 8.5; at lift > 2, L3 and L8 into a stop abuse 12.9 (normal use at the extended neck
  = one third, covered by scaling).
* **LD3 stop lug** - roots R{R3['LUG']['root_in']} (inner) / R{R3['LUG']['root_face']} (both pin faces, tangent at the pin top), step R{R3['LUG']['step_r']}; hand: {hrow(4, 'lug root')}; low bridge {hrow(4, 'low bridge')}.
* **LD4 lift-module joint** - scheme kept (ledge up / shelf down / dowel / 2 x F10 / pads); no third screw fits (servo behind the plate, window at the -X end).
* **LD5 iteration budget** - v7 .. v9 (round 1c); final set once at h {R['h']} on the frozen geometry; open spots = usage limits.
* **LD6 scope** - STL / STEP, checks.py --force, this file, spec 17.17, out/zmeny_rev3.txt, 3 previews, STATUS.
* **LD7 pan stops** - v9 at -90: 110 MPa at the sole / plate corner (880 N.mm).  Done (only the stop load path):
  1. v10a: SILL CURB on P_sachta = the floor continued to the plateau plane y 15.1 under the back window, x {Cb['x'][0]} .. {Cb['x'][1]}, z {Cb['z'][0]} .. {Cb['z'][1]},
     R{Cb['root_r']} root; the sole of P_drziak_serva bears on it ({a_curb:.1f} mm2, compression only, nominal gap 0).  It is NOT higher than the sill: the ear
     flange (bottom -40.5 at lift 0, x -19.4 .. -7.5) and the F12 head enter along -y just above the sill (K7).  FE h 0.6: 74 MPa (v8 at the same h: 83) -
     the curb alone took 11 N, the couple still went through the 2.0 plate (F10_A -24.5 N, pad D 20 N).
  2. v10b / v10c = the one correction: (a) the cw stop face of the lug is the plane tangent to pin 1 at -90.0 with its normal turned {Cw['phi']:.0f} deg from +x
     toward +y: pin force at the stall {F_cw:.1f} N = {F_cw * Cw['n'][0]:.1f} along -x + {F_cw * Cw['n'][1]:.1f} along -y, the y part presses the sole onto the curb
     (45 deg would be better but brings the lug nose closer than 1.0 to the deck trim wall; pin 1 and the deck are unchanged, the stop stays at -90.0);
     (b) sole + curb continued to x {Cb['x'][0]} (under the crank arm, top {R3['SOLE_EXT']['z_top']}); (c) the plate relief over the shroud roof is cut obliquely, the
     plate root at the sole keeps its back 1.4 mm down to z -41.9 (blunt end at x -5.0, R1.5 run-out = v10c; the feather end of v10b gave 44.6);
     (d) sole root R{R3['SOLE_ROOT_R']} (was R1.0).  FE h 0.6 (v10b): every row of both stop cases <= 23.5 MPa except the feather end (44.6 / 28.9).
     v10d (found by K2 of checks.py --force): the module bottom is relieved to z {R3['LIP_RELIEF']['z']} inside r {R3['LIP_RELIEF']['r']} - the new fin stood 0.05 into the FFC
     retaining lip of the shroud (the rev. 2 finding m1 again).
  Final set (h {R['h']}): -90: worst {stop_all['L8_stop_m90']['stress'] if 'L8_stop_m90' in stop_all else 'n/a'} MPa ({stop_all['L8_stop_m90']['spot'] if 'L8_stop_m90' in stop_all else ''}) = capacity {stop_all['L8_stop_m90']['capacity_Nmm'] if 'L8_stop_m90' in stop_all else 'n/a'} N.mm;
  +90: worst {stop_all['L8_stop_p90']['stress'] if 'L8_stop_p90' in stop_all else 'n/a'} MPa ({stop_all['L8_stop_p90']['spot'] if 'L8_stop_p90' in stop_all else ''}) = capacity {stop_all['L8_stop_p90']['capacity_Nmm'] if 'L8_stop_p90' in stop_all else 'n/a'} N.mm.
  Pair forces at -90: curb {pfm['curb_y']} N, pad D {pfm['padD_y']}, F10_A {pfm['padA_y']}, F10_B {pfm['padB_y']}, dowel x {pfm['dowel_x']} (v9: no curb, 26.2, -33.6, -7.9, 32.7).
  Target of LD7 (<= 30 MPa at 880 N.mm = capacity >= 378 N.mm): {'MET' if stop_min and stop_min >= 378 else 'NOT met'} (weaker stop {stop_min} N.mm).

## Criteria corrected in round 1c / 1d (each with its reason - nothing loosened silently)
* pan C1: FFC tails <-> R{R3['WIN']['end']['top_r']} top corners of the +X end window at lift 20: 0.82 / 0.89 measured, declared (cable in a window at top dead centre only; the radius is FE-driven).
* pan C2: two pairs designed at exactly 1.00 are measured 0.999x on the 0.01 STL - declared at 0.99.
* pan F3 (ZIF line of sight): with the closed floor the door points below the floor underside cannot see the ZIF; the >= 0.8 rule counts the door points above z -41.9.
* RAM C5: the swept lug was modelled as an annular sector with ONE azimuth at every radius; the cw face is a plane - the model now follows it (real meshes: pan C2).
* RAM C6: "r <= 4.5" of T_cap is evaluated above its R{P['cap_root_r']} root fillet; the fillet is checked against the {P['gear_bore_chamfer']} x 45 deg chamfer of the gear bore.
* FE (LD1): washer disc of the clamped F10 joints added to the contact zone (a hole-edge point of the plate under the washer was rated as structure).
* K2: declared thread overlap skr_F15 <-> T_most 3.0 -> 4.6 mm3 (M3x8, engagement 1.80 instead of 0.8); the lintel PTFE strip (no. 8) shortened to
  y -6.0 .. 4.9 - it overlapped strip 7 on the same face (round-1 slip, a real double tape layer).

## Usage limits (rows of the final FE set above their allowable; capacity = load at which the spot reaches the allowable)
| situation | capacity | governing spot | basis |
|---|---|---|---|
{lim_md}

The allowables keep a factor 3 (normal) / 2 (abuse) on the lower-bound strength 25.8 MPa: at the capacity nothing breaks.
Pan stops: weaker stop {stop_min} N.mm ({pct} % of the {STALL:.0f} N.mm stall at the stage) = {stop_min / LEVER if stop_min else 0:.1f} N by hand at the side of the head.  Servo EEPROM: angle limits
+-85 deg at the head = +-{STEPS_85} steps about the centre (gear {RATIO:.0f} : 1, 4096 steps / turn); torque limit {tq_pct} % (= {tq_Nmm} N.mm at the stage, 2 x that <= {stop_min}).
Bench test that {tq_pct} % still turns the head (UNVERIFIED).  Never turn the head by hand against an end stop.
CONDITION (fix-back after overenie3, V1): the -90 deg capacity and the factor 2 of the torque limit need a working sole / curb seat of the lift module
(bench step B4c of out/zmeny_rev3.txt; it cannot be checked in the assembled torso) - {v1_short}

## Final FE set - worst case per spot (h {R['h']}, {len(fe_rows)} spots)
{md_fe()}

Fail-safe (gear bond failed completely; against the lower-bound strength 25.8): {fs_txt}.
Fail-safe rows ABOVE 25.8 at the 30 N plan load (every case, not only the worst per spot - overenie3 V11): {fs_all_txt}.  Judgement of the lead (STATUS_rev3_fixer.md):
a double fault outside the stated limits - at the usage limit of each situation the rows scale to {fs_scaled}.
Reprint vs rev. 2 (computed from the STL sets): {rp_md}.  Bought / made parts changed: {oth_md}.

## Fix-back after overenie3 (2026-11-23, one round; verifier scripts in overenie3/, mine in fixback3_work/)
No geometry change: stl/ and step/ are the frozen v10d set (FE stamp {R['stl_stamp']}), the final FE set and K1 - K13 are those above.
| finding | reproduced (own measurement) | what was done |
|---|---|---|
| V1 major: -90 deg stop capacity needs a closed sole / curb seat; the T9 feeler test accepted up to 0.09 | {v1_en} | text: seat check moved to the bench (new step B4c before T7: bare P_drziak_serva on the stage, F10 tight, the sole / curb line is looked at from below the stage with a lamp inside the well (fixback3_work/v1_view.py: nothing of the module or the gear below the line for x -16.9 .. -10.5): the {GAP_OK:.2f} feeler must not enter (no light = closed); else the sole is bedded on the curb face with toughened 2K epoxy, release agent on the sole - the 0.13 PTFE tape of the first text is dropped: it does not fit a 0.10 .. 0.13 gap and creeps); zmeny 3 / 4 / 5, spec 17.17 item 6 and the usage-limit text state the condition and the capacity with an open seat |
| V2 major: F12 cannot be inserted / removed with the lift module seated | STEP solids (fixback3_work/v2_f12b.py): skr_F12_1 moved along +y overlaps P_drziak_serva from {F12_PLAY:.1f} to 19.9 mm of travel (head D3.5 against the D2.4 key hole, 6.63 mm3 = the head annulus); {F12_BEHIND:.1f} mm between the ear flange and the module face for a {F12_LEN:.1f} long screw; K7 passes because it tests the 1.3 key channel only | text only (t4_assembly B5e / T9 / T11 / S1, zmeny 3): F12 is pre-loaded in the ear flange before the ear is hung on the crank pin (captive, play {F12_PLAY:.1f}); at T9 it is started with the 1.3 key about 3 mm before the seat (its tip meets the foot at {F12_ENG:.1f} - {F12_START:.1f} mm, the last {F12_START:.1f} mm = {F12_START / F12_PITCH:.0f} turns are screwed while the module is pushed home); tightened at T11; S1: F10 out first, F12 unscrewed while the module is pulled back.  The screw travels inside the x-z projection of the ear flange that K7 already sweeps (head {F12BB[0]:.2f} .. {F12BB[3]:.2f} / {F12BB[2]:.2f} .. {F12BB[5]:.2f} inside {EARBB[0]:.1f} .. {EARBB[3]:.1f} / {EARBB[2]:.1f} .. {EARBB[5]:.1f}; 0.40 over the sill); K7 re-run with the edited step texts: {k7_status} (the step data - move / legs / screws - are unchanged) |
| V3 minor: F10_A insert hole is a through hole | STEP: no well material inside r 1.95 on the F10_A axis from y 15.1 to the inner wall face y 10.3; insert y 11.1 .. 15.1, M2x6 tip y 11.4 | builder note B4a (insert set flush with the pad face on a screw + flat piece, wipe the inside of the well, M2x6 only); geometry kept (a blind hole changes P_sachta = FE stamp) |
| V4 minor: knife-edge fins at the keyhole scallop / F10_A hole mouth | not re-measured (K4 declares the scallop feather as a run-out, 30 cells) | print note in zmeny 6 (cut the two fins, break the hole mouth, do not chamfer the stop faces) |
| V5 minor: ear 0.14 over the sill / curb that print as supported overhang | STEP: min distance L_ucho <-> P_sachta 0.140 | print note in zmeny 6 + check in B4c (sill and curb top sanded level with the floor, straight edge) |
| V6 minor: PTFE strip on T_cap changed | STL: strip {ptfe_h_old:.1f} -> {ptfe_h:.1f} high, lower edge {ptfe_lo:.1f} above the T_cap base | line in zmeny 2 |
| V7 minor: unverified STS3032 spline length under the new floor | STEP (fixback3_work/v7_spline.py): floor underside over the pinion axis at {SPL_ROOF:.2f} for every pan angle -90 .. +90 where there is floor; modelled tip {SPL_TIP:.2f} = {SPL_LEN:.1f} above the boss face, clearance {SPL_CLR:.1f} | line in zmeny 2: measure before printing P_sachta, at most {SPL_LEN + SPL_CLR - 0.5:.1f} ({SPL_LEN + SPL_CLR - 0.2:.1f} leaves 0.2) |
| V8 note: over-travel with a stop pin missing | not re-measured (verifier: 2.2 deg beyond -90 until the lug nose meets the T_paluba wall, 8.6 deg beyond +90 until the shroud edge meets the pinion) | recorded here only |
| V9 note: stale K4 declaration / T_cap print string | checks.json K4: the declaration 'F10 A insert seat floor 0.8' is not in declared_used | removed from K4_DECL (checks.py K4 re-run: see STATUS); t4_ram.py + parts.json / parts_ram.json string 'through hole D3.1' |
| V10 note: foot perimeter 0.13 over the floor root fillets | not re-measured | none (T11 calibration) |
| V11 note: second fail-safe row above 25.8 | results.json: {fs_all_txt} | both rows named above |
"""
open(os.path.join(OUTD, "opravy3.md"), "w").write(OPR)

# ---------------------------------------------------------------------------------------------------------------- spec 17.17
lim_spec = "\n".join(f"  * {l['en']}: {('%.1f N' % l['capacity_N']) if 'capacity_Nmm' not in l else ('%d N.mm (%.1f N at the side of the head)' % (l['capacity_Nmm'], l['capacity_N']))} - {l['spot']}"
                     for l in limits) or "  * none"
S17 = f"""### 17.17 Rev. 3 - strengthening of the rotating well (fixer, 2026-11-22/23) - supersedes 17.0-17.16 where different
Numbers: `t4_common.R3`; record: opravy3.md; FE: fe_sachta/results.json (h {R['h']}, STL stamp {R['stl_stamp']}).
1. **Pivot / retention (R3-1, R3-2).** F15 = ISO 7380 M3x{P['screw_len']:.0f} + DIN 9021 M3 + 2 x DIN 125 M3 (spacers on the T_cap top {P['cap_top']}); the DIN 9021
   overlaps the hub LIP of the well (lip top {R3['LIP']['z_top']}, r_in {R3['LIP']['r_in']}): the stage is captive without the gear bond.  Thread engagement in T_most
   {P['engagement_nominal']} / {P['engagement_min']} min; axial play {P['axial_play']} ({P['axial_play_range'][0]}-{P['axial_play_range'][1]}, feeler).  T_cap: root R{P['cap_root_r']}, hole drilled D{P['cap_hole']}.
2. **Floor (R3-3 b).** P_sachta has a floor z {R3['FLOOR']['z'][0]} .. {R3['FLOOR']['z'][1]} over the whole well with R{R3['FLOOR']['root_r']} roots; the pan pinion face is 3.0
   (bought 4.0 pinion shortened at its top face; top {R3['FLOOR']['pinion_top']}); 0.2 relief over the spline-tip annulus (floor 1.05 there, declared).
3. **Windows / corners (R3-4, R3-6).** Window corners R{R3['WIN']['corner_r']} (end-window top R{R3['WIN']['end']['top_r']}); +X lintel 2.3 = 8th PTFE land; end-window top -16.9;
   curb z {R3['WIN']['end']['sill_z']} for y >= {R3['WIN']['end']['sill_y0']} at the +X pillar foot; inner corners R{R3['CORNER_RI']}; guide band 2.3 above z -17.5; journal ring down to
   z {R3['RING_EXT']['z'][0]} over the front half.
4. **Lift-module joint (R3-5).** No tongue / groove.  UP: pocket block top (chamfer {Ld['block_chamfer']}) under the ledge rib x {Ld['x'][0]} .. {Ld['x'][1]}, gap {Ld['gap']}.
   DOWN: closed window of the plate (x {Sh['notch_x'][0]} .. {Sh['notch_x'][1]}, z {Sh['window_z'][0]} .. {Sh['window_z'][1]}) on the shelf z {Sh['z_bot']} .. {Sh['z_top']}, gap {Sh['gap']}.
   x / z: F10 dowel ISO 8734 D2 x {Rl['dowel']['len']:.0f} at ({Rl['dowel']['xz'][0]}, {Rl['dowel']['xz'][1]}), 2.9 bonded in the well pad, {Rl['dowel']['proud']} proud behind the plate (servo end stop).
   y: F10_A at ({R3['F10_A'][0]}, {R3['F10_A'][1]}), F10_B, contact pads A, B, mid band, C, D, E and the sill curb (item 6).
5. **P_drziak_serva.** Turret wall {R3['TURRET']['x'][1] - R3['TURRET']['x'][0]:.1f} (inner face {R3['WALL_PAD']['recess']} back except the corner pad); F11 nut slot closed at +Y (nut from above);
   sole root R{R3['SOLE_ROOT_R']}; R{R3['BLOCK_ROOT_R']} under the block; lug roots R{R3['LUG']['root_in']} / R{R3['LUG']['root_face']}, bridge step R{R3['LUG']['step_r']}.  MG90S seat = couple along x (L1: F11 tension +
   case corner on the wall pad; L2: tab on the block + case end on the proud dowel end, gap {R3['SERVO_SEAT']['end_gap']}).  A roof beam over the servo is NOT possible (door lintel, K7).
6. **Pan stops (LD7).** Stops at exactly +-90.0, pins D3 in the deck unchanged.  ccw face of the lug = plane x {R3['STOP']['face_x_ccw']}; cw face = plane tangent to pin 1
   through ({Cw['p'][0]}, {Cw['p'][1]}) with its normal {Cw['phi']:.0f} deg from +x toward +y (lever {Cw['lever']} mm): the pin force presses the SOLE of the module (x {Cb['x'][0]} .. -6.5,
   down to z -41.9) onto the SILL CURB of P_sachta (floor continued to y 15.1 under the back window, x {Cb['x'][0]} .. {Cb['x'][1]}, top = sill {Cb['z'][1]}; seat {a_curb:.1f} mm2,
   compression only, gap 0 nominal).  Plate relief over the shroud roof cut obliquely (plate root whole at the sole).
   Fix-back after overenie3 (V1): the seat is checked on the BENCH before T7 (step B4c: bare P_drziak_serva on the stage, F10 tight; the sole / curb line is
   looked at from below the stage with a lamp inside the well: the {GAP_OK:.2f} feeler must not enter (no light = closed); otherwise the sole is bedded on the curb
   face with toughened 2K epoxy, release agent on the sole) - {v1_short}
7. **Shroud (R3-7).** Roof at floor level over the shroud top (r <= {R3['SHROUD']['roof_r']}), R{R3['SHROUD']['root_r']} root; plate relief of the pocket 0.30 over it.
8. **Rest gap (R3-8).** {R3['REST_GAP']['nominal_bdc']} at BDC; calibration T11 (feeler {R3['REST_GAP']['feeler_ok'][0]} / {R3['REST_GAP']['feeler_ok'][1]}) -> PARK_DEG; the lift servo is never commanded below PARK_DEG.
9. **Acceptance method (LD1 / LD2).** Structure rows >= 1.0 mm from active contacts; contacts by nominal bearing pressure + hand calc of the supporting
   section; bond by nominal average (2.7 normal / 4.0 abuse).  Classes: L1 / L2 at lift 0 normal 8.5; at the extended neck, L3 and L8 into a stop abuse 12.9.
10. **Final FE set:** {len(fe_rows)} spots, {nfail_spots} above their allowable ({nfail_rows} rows) -> USAGE LIMITS (capacity = load at the allowable):
{lim_spec}
    Rules: carry the robot by the torso; the firmware parks the neck when idle and before power-off; pan range +-85 deg (+-{STEPS_85} servo steps); pan-servo
    torque limit in EEPROM {tq_pct} % (2 x {tq_Nmm} N.mm <= {stop_min} N.mm; bench test that the head still turns - UNVERIFIED); never turn the head by hand against an end stop.
11. **Print.** P_sachta: top plate toward the build plate, raised >= 3 mm; with the closed floor it is a bucket open toward the plate - it drains through the
    back window, the -Y part of the +X end window (sills at floor level; the sill curb is flush) and the D7.6 hub bore; not a suction cup (the neck opening and the
    windows vent it).  P_drziak_serva: plate face on the build plate.  Reprint vs rev. 2 (STL comparison): {', '.join(RP)}.
12. **Bought / made parts changed:** ISO 7380 M3x8 (was M3x6); 2 x DIN 125 M3 (+ 1 spare for B2b); dowel ISO 8734 D2 x 6 (was 2 x 5); pan pinion shortened to 3.0;
    8th PTFE strip; L_ucho flange end chamfer {R3['EAR']['end_chamfer']}; 36T gear lower bore edge chamfer {P['gear_bore_chamfer']}; PTFE strip on T_cap {ptfe_h:.1f} high
    (was {ptfe_h_old:.1f}), lower edge {ptfe_lo:.1f} above the base (above the R{P['cap_root_r']} root).
13. **Fix-back after overenie3 (2026-11-23; no geometry change, record in opravy3.md).**  (a) F12 (ear -> foot) cannot be inserted with the lift module
    seated ({F12_BEHIND:.1f} behind the ear flange for a {F12_LEN:.1f} long screw, head D3.5 / key hole D2.4): it is pre-loaded in the ear flange on the bench (B5e),
    started through the key hole about 3 mm before the module seats (T9), tightened at T11; service S1 in the reverse order.  (b) The F10_A insert hole is a
    THROUGH hole into the well (insert y 11.1 .. 15.1, inner wall face 10.3): insert set flush with the pad face, M2x6 only.  (c) STS3032 spline: modelled
    {SPL_LEN:.1f} above the boss face (UNVERIFIED), {SPL_CLR:.1f} under the relieved floor ({SPL_ROOF:.2f}): measure the servo before P_sachta is printed (<= {SPL_LEN + SPL_CLR - 0.5:.1f}).
    (d) Sill + curb top print as supported overhang: sanded level with the floor (ear flange {R3['REST_GAP']['nominal_bdc']} above them).  (e) P_drziak_serva: two knife-edge fins of
    the keyhole scallop and the edge at the F10_A hole mouth are deburred; the stop faces are not touched.
"""
sp = os.path.join(T4, "T4_spec.md"); s = open(sp).read()
i = s.find("### 17.17 ")
s = (s[:i].rstrip("\n") if i >= 0 else s.rstrip("\n")) + "\n\n" + S17
open(os.path.join(OUTD, "T4_spec.md"), "w").write(s)

# ---------------------------------------------------------------------------------------------------------------- zmeny_rev3.txt (Slovak)
skn = lambda x, nd=2: f"{x:.{nd}f}".replace(".", ",")          # Slovak decimal comma


def lim_sk(l):
    if "capacity_Nmm" in l:
        return (f"  - {l['sk']}: najviac {skn(l['capacity_Nmm'] / 1000.0)} N·m, t. j. asi {skn(l['capacity_N'], 1)} N (≈ {skn(l['kg'], 1)} kg) rukou na boku hlavy "
                f"(rameno {LEVER:.0f} mm)")
    return f"  - {l['sk']}: najviac {l['capacity_N']:.0f} N (≈ {skn(l['kg'], 1)} kg)"


RP_SK = {"P_sachta": "šachta: plné dno, zaoblené rohy okien, hrubší preklad nad oknom +X, rebro a polica pre modul zdvihu, prah pod zadným oknom (opora pätky držiaka)",
         "P_drziak_serva": "držiak serva zdvihu: stena pri serve 4 mm, okno pre policu, pätka dosadajúca na prah šachty, šikmá plocha dorazu −90°",
         "T_cap": "čap: zaoblený koreň R1; otvor sa VŔTA na Ø3,1 až po vytvrdení",
         "T_paluba": "paluba: posunutý výrez pre dorazový výstupok (iný rozsah otáčania výstupku)"}
rp_sk = "\n".join(f"  - {n}.stl – {RP_SK.get(n, 'zmenená geometria')}" for n in RP) or "  - nič"
strips = []
for x in other:
    if x["name"].startswith("ptfe_pasik"):
        _, bb = _stl(os.path.join(T4, "stl", x["name"] + ".stl"))
        dims = sorted((float(bb[3 + i] - bb[i]) for i in range(3)), reverse=True)
        strips.append(f"č. {x['name'].split('_')[-1]}: {skn(dims[0], 1)}×{skn(dims[1], 1)} mm")
sw = stop_weak
lim_lines = [lim_sk(l) for l in limits if not l["case"].startswith("L8")]
stop_lines = [f"  - doraz {'+90°' if c.endswith('p90') else '−90°'}: {skn(l['capacity_Nmm'] / 1000.0)} N·m = asi {skn(l['capacity_N'], 1)} N (≈ {skn(l['kg'])} kg) rukou na boku hlavy (rameno {LEVER:.0f} mm)"
              for c, l in sorted(stop_all.items())]

# fix-back after overenie3 (V1): the condition of the -90 deg capacity in the user's text (numbers computed above; nothing typed)
if V1:
    _a, _b = V1["sig_tq"][GAP_INF], V1["sig_2tq"][GAP_INF]
    if V1["confirmed_as_stated"]:
        _mid = (f"    So zvyškovou škárou {skn(GAP_OK)} / {skn(GAP_OLD)} mm znesie doraz {skn(V1['cap'][GAP_OK] / 1000.0)} / {skn(V1['cap'][GAP_OLD] / 1000.0)} N·m "
                f"(pri {tq_pct} % je rezerva {skn(V1['cap'][GAP_OK] / tq_Nmm, 1)}- / {skn(V1['cap'][GAP_OLD] / tq_Nmm, 1)}-násobná); plnú rezervu dáva len pätka dosadnutá bez škáry.\n")
    else:
        _mid = (f"    Malá škára neprekáža: so škárou do {skn(GAP_OLD)} mm pätka dosadne už pri {skn(V1['T_close'][GAP_OLD] / 1000.0)} N·m a únosnosť dorazu sa nemení "
                f"(pri {tq_pct} % {skn(V1['sig_tq'][GAP_OLD], 1)} MPa, pri dvojnásobku {skn(V1['sig_2tq'][GAP_OLD], 1)} MPa).\n"
                f"    Od škáry {skn(V1['g_crit'])} mm však pätka nedosadne včas a platia hodnoty pre otvorenú škáru – preto sa v kroku B4c pripúšťa najviac {skn(GAP_OK)} mm.\n")
    v1_sk4 = (f"    POZOR – platí to LEN vtedy, keď spodná pätka držiaka serva zdvihu dosadá na prah šachty (skúška na stole, krok B4c v časti 3).\n"
              f"    Výpočet toho istého prípadu s otvorenou škárou: doraz −90° znesie len {skn(V1['cap_open'] / 1000.0)} N·m (asi {skn(V1['cap_open'] / LEVER, 1)} N rukou na boku hlavy); "
              f"pri {tq_pct} % je namáhanie {skn(_a, 1)} MPa\n"
              f"    (dovolené {skn(ALLOW_M90, 1)}) a pri dvojnásobku {skn(_b, 1)} MPa (pevnosť živice najmenej {skn(LB, 1)} MPa)"
              f"{' – držiak môže prasknúť' if _b > LB else ''}.\n"
              + _mid +
              f"    Ak sa skúška B4c nerobila alebo škára ostala väčšia: pätku podliať epoxidom podľa B4c (modul zdvihu sa dá vybrať aj z hotového trupu – servis S1).\n"
              f"    Dovtedy nastaviť Max Torque {V1['tq_open_pct']} % (= {V1['tq_open_pct'] * 10} z 1000) – hlava sa pri ňom možno nepohne – a na doraz −90° ju nikdy netlačiť.")
    v1_sk5 = (f"  Hodnota pre doraz −90° platí pri dosadnutej pätke držiaka na prah šachty (krok B4c); s otvorenou škárou je to len {skn(V1['cap_open'] / 1000.0)} N·m "
              f"= asi {skn(V1['cap_open'] / LEVER, 1)} N (≈ {skn(V1['cap_open'] / LEVER / 9.81)} kg) rukou.")
else:
    v1_sk4 = ("    POZOR – platí to LEN vtedy, keď spodná pätka držiaka serva zdvihu dosadá na prah šachty (skúška na stole, krok B4c v časti 3); "
              "únosnosť dorazu −90° bez dosadnutia nie je vypočítaná.")
    v1_sk5 = "  Hodnota pre doraz −90° platí pri dosadnutej pätke držiaka na prah šachty (krok B4c)."

ZM = f"""NOVA mini – trup, zmeny rev. 3 (spevnenie otočnej šachty)
=========================================================
Prečo: kontrola pevnosti ukázala, že samotné dno šachty (disk nad kolesom) vydrží, slabé boli jeho SPOJE
(skrutka čapu, prechod dna do stien, rohy okien, uloženie modulu zdvihu, dorazy otáčania). Rev. 3 to opravuje.

1. ČO TREBA VYTLAČIŤ ZNOVA (oproti rev. 2; zistené porovnaním objemu a rozmerov každého STL)
{rp_sk}
  Ostatné tlačené diely sú bez zmeny ({len(same)} dielov – netreba tlačiť).

2. ČO KÚPIŤ / PRIPRAVIŤ INAK
  - skrutka ISO 7380 M3×8 (namiesto M3×6) – 1 ks (čap otáčania, spoj F15)
  - podložka DIN 125 M3 (3,2×7×0,5) – 2 ks + 1 ks rezerva; veľká podložka DIN 9021 M3 (3,2×9×0,8) ostáva – 1 ks
  - kolík ISO 8734 Ø2×6 (namiesto Ø2×5) – 1 ks (kolík F10 v šachte)
  - pastorok otáčania (m0,8, 18 zubov): kúpený so šírkou 4 mm SKRÁTIŤ na 3,0 mm (zbrúsiť 1 mm z vrchnej strany na pilníku / papieri P120)
  - koleso 36 zubov: spodnú hranu otvoru zraziť 0,4 mm (záhlbníkom v ruke), ak ju nemá
  - PTFE páska 0,13: pribudol 8. pásik (na preklad nad oknom +X); nové rozmery pásikov: {'; '.join(strips) if strips else 'podľa plôšok'} – strihať podľa plôšok na novej šachte
  - L_ucho (nerez): na konci príruby zraziť spodný roh 1,2 mm pilníkom
  - PTFE pásik na čap T_cap: široký {skn(ptfe_h, 1)} mm (bolo {skn(ptfe_h_old, 1)}), spodný okraj {skn(ptfe_lo, 1)} mm nad základňou čapu – nelepiť ho na zaoblenie R1 pri koreni
  - servo otáčania STS3032 – ZMERAŤ EŠTE PRED TLAČOU P_sachta: výška drážkovaného hriadeľa nad čelom nákružku Ø12,4 (posuvné meradlo).
    Model počíta s {skn(SPL_LEN, 1)} mm (údaj z ponúk predajcov, neoverený); koniec hriadeľa je potom {skn(SPL_CLR, 1)} mm pod novým dnom šachty.
    Musí byť najviac {skn(SPL_LEN + SPL_CLR - 0.5, 1)} mm (pri {skn(SPL_LEN + SPL_CLR - 0.2, 1)} mm ostáva pod dnom už len 0,2 mm). Ak je hriadeľ dlhší: P_sachta netlačiť, koniec hriadeľa
    skrátiť jemným pilníkom (servo držať hriadeľom nadol, piliny nesmú do prevodovky) alebo si vyžiadať úpravu modelu dna.
  - momentový skrutkovač netreba – všetko sa doťahuje končekmi prstov presným skrutkovačom

3. ZMENENÉ KROKY MONTÁŽE A KALIBRÁCIE
  (B = príprava na stole, T = montáž trupu, S = servis; v zátvorke číslo kroku v montaz_trup.txt rev. 2, ktorý sa tým mení alebo dopĺňa)
  B2  (krok 2) T_cap: po vytvrdení prevŕtať otvor Ø3,1; nalepiť na T_most húževnatým 2K epoxidom (hliník zdrsniť P120, odmastiť IPA), 24 h.
  B2b (nový, po kroku 2) SKLADBA F15 (skúška nasucho na stole): cez T_cap do T_most zaskrutkovať M3×8 s podložkou DIN 9021 a pod ňou 2× DIN 125.
      Po dosadnutí hlavy skrutky NESMIE jej špička vyčnievať pod T_most (priložiť pravítko). Ak vyčnieva, dať tretiu DIN 125 POD HLAVU skrutky.
      Túto skladbu si zapísať – použije sa v kroku T7.
  B4a (krok 4) Do šachty vlepiť 2 závitové vložky M2 a kolík Ø2×6 (2,9 mm v šachte, 3,1 mm trčí von).
      POZOR – otvor pre vložku F10_A (horná z dvoch vložiek) je PRIECHODZÍ až dovnútra šachty, vložka v ňom nemá doraz. Vložku naskrutkovať
      na skrutku M2 (závit skrutky natrieť voskom) cez rovný pliešok s otvorom Ø2–2,5 (alebo podložku s vonkajším priemerom aspoň 6 mm) priložený
      na čelo plôšky a pritiahnuť: vložka ostane zarovno s plôškou, nie hlbšie. Lepidlo vytlačené dovnútra šachty hneď zotrieť (je tam vodiaca
      plocha krku, vôľa 0,2–0,3 mm).
      Do F10_A patrí LEN skrutka M2×6 – dlhšia by vyčnievala do dráhy krku.
  B4b (krok 14) Koleso 36T sa lepí pod plné dno šachty: mosadz aj živicu zdrsniť P120–240 a odmastiť, húževnatý 2K epoxid 0,1–0,2 mm,
      vytlačené lepidlo pri strednom otvore zotrieť. Dno vnútri šachty, kde boli podpery, zarovnať brúsnym papierom na hranolčeku
      (cez otvor pre krk); medzera pätky sa potom kontroluje v kroku T11.
  B4c (NOVÝ krok na stole – po vytvrdení B4a, PRED krokom T7; šachta je ešte mimo trupu) DOSADNUTIE PÄTKY DRŽIAKA NA PRAH ŠACHTY.
      Od tohto dosadnutia závisí pevnosť dorazu −90° (pozri časť 4 a 5); v zloženom trupe sa už skontrolovať nedá.
      Holý P_drziak_serva (bez serva) nasadiť na šachtu ako v kroku T9 a dotiahnuť obe skrutky F10. Spodná pätka držiaka (koniec −X, pod zadným
      oknom šachty) sa má čelom opierať o prah šachty – styčná plôška je dlhá {skn(Cb['pad_x'][1] - Cb['pad_x'][0], 1)} mm a vysoká {skn(Cb['z'][1] - Cb['z'][0])} mm.
      Šachtu otočiť dnom k sebe, dovnútra šachty (otvorom pre krk) zasvietiť a pozrieť sa zospodu na škáru medzi čelom pätky a čelom prahu:
      lístok {skn(GAP_OK)} mm do nej NESMIE vojsť (ak cez škáru nevidno svetlo, je zatvorená a merať netreba).
      Ak lístok vojde: čelo pätky natrieť separátorom (vosk alebo tenký film vazelíny), na čelo prahu naniesť tenký film
      húževnatého 2K epoxidu, držiak nasadiť a dotiahnuť F10, vytlačené lepidlo zotrieť – hlavne z VRCHU prahu a z dna okna (nad nimi prechádza
      príruba ucha s vôľou 0,15 mm). Po 24 h držiak zložiť a skontrolovať, že vrch prahu je čistý a rovný. PTFE pásku sem NEDÁVAŤ.
      Pri tej istej skúške priložiť oceľové pravítko hranou na dno šachty cez zadné okno až na prah: prah nesmie byť vyššie ako dno
      (pravítko sa na ňom nesmie hojdať) – inak vrch prahu zbrúsiť do roviny s dnom.
  B5b (krok 5) Maticu F11 vhodiť do drážky bloku ZHORA (drážka je zozadu zatvorená). Pri doťahovaní F11 tlačiť servo k stene s otvorom.
  B5e (krok 5, DOPLNENIE – platí aj pre rev. 2) SKRUTKA F12 SA VKLADÁ UŽ TERAZ: skrutku F12 (M2×6) prestrčiť otvorom Ø2,3 v prírube ucha L_ucho
      ZOZADU (hlava na strane držiaka, závit trčí dopredu k pätke) ešte PRED zavesením ucha na čap kľuky. Po zavesení ucha a po zasunutí modulu
      sa už vložiť nedá: za prírubou je len {skn(F12_BEHIND, 1)} mm miesta na skrutku dlhú {skn(F12_LEN, 1)} mm a hlava Ø3,5 neprejde otvorom Ø2,4 v držiaku.
      Skrutka potom v module voľne drží (vôľa {skn(F12_PLAY, 1)} mm medzi prírubou a držiakom), nevypadne.
  B7b (krok 7) Pastorok skrátený na 3,0 mm nasadiť na servo otáčania (Loctite 638), ako doteraz.
  T7  (krok 19) Šachtu spustiť na čap. Cez prázdnu šachtu položiť na vrch čapu 2× DIN 125, na ne DIN 9021 (prekrýva golier dna šachty – drží šachtu,
      aj keby sa lepený spoj kolesa uvoľnil), skrutka M3×8 + Loctite 222, dotiahnuť končekmi prstov.
      KONTROLA VÔLE: lístok 0,10 mm medzi podložku DIN 9021 a golier vojde, lístok 0,25 mm nevojde.
  T9  (krok 21) Modul zdvihu zasunúť dverami rovno dopredu (smer −Y): blok držiaka pod rebro šachty, okno v doske držiaka na policu,
      otvor v doske na kolík Ø2×6 (koniec kolíka ostane trčať 1,1 mm za doskou pri konci serva – to je zámer, opierka serva).
      Príruba ucha sa pritom má voľne posúvať nad prahom zadného okna; ak drhne, modul vybrať a vrch prahu zbrúsiť (krok B4c), netlačiť nasilu.
      SKRUTKA F12 IDE DNU SPOLU S MODULOM (je vložená v uchu, krok B5e): na jej závit dať kvapku Loctite 222 a modul zasúvať, kým mu do dosadnutia
      nechýbajú asi 3 mm. Imbusom 1,3 cez otvor Ø2,4 v mostíku dorazu pritlačiť skrutku do závitu pätky a otáčať, kým sa nechytí. Potom ďalej
      otáčať a zároveň modul rukou dotláčať, až doska držiaka dosadne na plôšky šachty (posledné {skn(F12_START, 1)} mm = asi {F12_START / F12_PITCH:.0f} otáčok; hlava skrutky sa
      pritom opiera o držiak, preto sa modul bez otáčania skrutky nedá dotlačiť). F12 zatiaľ NEDOŤAHOVAŤ.
      Potom 2 skrutky F10 (M2×6 + Loctite 222); skrutka F10_A je o 2,8 mm bližšie k servu ako v rev. 2.
      Dosadnutie spodnej pätky držiaka na prah šachty je vyskúšané už v kroku B4c (tu v trupe sa k nemu lístkom nedá dostať).
  T11 (krok 23) F12 už len DOTIAHNUŤ imbusom 1,3 cez mostík dorazu (skrutka je v závite od kroku T9; vložiť sa teraz nedá).
      KALIBRÁCIA MEDZERY PÄTKY KRKU / PARK_DEG: kľuku dať do dolnej úvrate (0°). Medzi pätku krku a dno šachty (cez okno +X) musí vojsť lístok
      0,10 mm a nesmie vojsť 0,25 mm → vo firmvéri PARK_DEG = {R3['REST_GAP']['park_deg_ok']:.0f}. Ak 0,10 nevojde, NETLAČIŤ: dvíhať kľuku po 1°, kým lístok vojde, pripočítať {R3['REST_GAP']['margin_deg']:.0f}°
      a túto hodnotu uložiť ako PARK_DEG. Servo zdvihu sa nikdy nesmie poslať pod PARK_DEG (nekalibrovaný firmvér: {R3['REST_GAP']['park_deg_default']:.0f}°).
  S1  (servis 1 – výmena serva zdvihu; ZMENA PORADIA, platí aj pre rev. 2) Najprv von obe skrutky F10. Potom F12 povoľovať imbusom 1,3 cez mostík:
      po asi {F12_PLAY / F12_PITCH:.0f} otáčkach ({skn(F12_PLAY, 1)} mm) sa jej hlava oprie o držiak – ďalej povoľovať a zároveň modul ťahať von (ešte {skn(F12_START, 1)} mm, asi {F12_START / F12_PITCH:.0f} otáčok),
      kým skrutka nevyjde zo závitu pätky. Skrutka ostane v uchu a vyjde von s modulom. Späť: kroky T9 a T11.

4. PRAVIDLÁ PRE FIRMVÉR A NASTAVENIE SERVA OTÁČANIA
  - krk v pokoji a pred vypnutím vždy zasunúť (zdvih 0–2 mm); žiadne dlhé státie v polovici zdvihu (teplo serva)
  - servo zdvihu nikdy pod PARK_DEG
  - otáčanie hlavy len v rozsahu ±85° (dorazy sú na ±90° a sú iba poistka pre kábel)
  - servo otáčania STS3032 – uložiť do EEPROM (program Feetech FD alebo knižnica; čísla adries overiť v tabuľke pamäte svojho serva):
      uhlové limity: stred ± {STEPS_85} krokov (= ±85° hlavy; prevod {RATIO:.0f} : 1, 4096 krokov na otáčku) – položky „Min / Max Angle Limit“ (adresy 9 a 11)
      obmedzenie momentu: {tq_pct} % – položka „Max Torque“ (adresa 16) = {tq_pct * 10 if tq_pct else '?'} z 1000
    Dôvod: slabší doraz znesie {skn(stop_min / 1000.0 if stop_min else 0)} N·m; servo má pri zablokovaní 0,88 N·m na hlave. Pri {tq_pct} % je to {skn(tq_Nmm / 1000.0 if tq_Nmm else 0)} N·m, teda s dvojnásobnou rezervou.
{v1_sk4}
    Po nastavení vyskúšať na stole, že hlava sa ešte spoľahlivo otáča (neoverené výpočtom).

5. LIMITY POUŽÍVANIA (výpočet MKP na finálnych modeloch; pri týchto silách je v materiáli ešte 2–3-násobná rezerva do zlomenia)
{chr(10).join(lim_lines) or '  - sily na hlavu: všetky kontrolované prípady vyhoveli'}
  Dorazy otáčania (hlava otočená až na doraz a tlačí sa ďalej):
{chr(10).join(stop_lines)}
{v1_sk5}
  Prakticky: robota prenášať za TRUP, nie za hlavu. Hlavu NIKDY nedotáčať rukou nasilu do krajnej polohy – vypnuté servo sa dá rukou
  pretočiť už pri 0,1–0,2 N·m, takže na doraz sa dá ľahko naraziť; pri ručnom otáčaní zastať, keď cítiť odpor.
  S vysunutým krkom na hlavu netlačiť a neťahať – najprv krk zasunúť.

6. TLAČ ZMENENÝCH DIELOV (Elegoo Tough, Saturn 4 Ultra)
  - P_sachta: vrchnou doskou (strana s veľkým otvorom pre krk) k platforme, os zvislo, zdvihnutá na podperách aspoň 3 mm.
    Podpery: na vrchnej doske a na vnútornej ploche dna (hroty 0,3–0,4 mm, rozstup do 3 mm) – stopy po nich na dne potom zarovnať.
    Nikdy nie na vonkajšom prstenci Ø52,7, na vodiacich plôškach a na plášti bubna.
    Šachta má teraz ZATVORENÉ dno: pri tlači je to „vedierko“ otvorené k platforme, NIE prísavka (prísavka by bola otvorená k fólii vane).
    Živica z neho vytečie zadným oknom, spodnou časťou okna +X (prahy sú v úrovni dna, aj nový prah pod zadným oknom je zarovno s dnom)
    a stredným otvorom Ø7,6; vzduch ide otvorom pre krk (diel je zdvihnutý 3 mm). Otvory Ø2,5 vo vrchnej doske nechať voľné (vrecká prstenca).
  - P_drziak_serva: plochou doskou (strana k šachte) priamo na platforme; ľahké podpery len pod mostíkom dorazu, NIE na plochách dorazu
    a nie na čele pätky. Otvory Ø2,05 (kolík) a Ø2,3 po vytvrdení prečistiť vrtákom.
    Po vytvrdení odrezať skalpelom dve tenké „pierka“ (hrubé 0–0,5 mm, dlhé asi 4 mm) na zadnej strane dosky pri okrúhlom otvore pre nákružok serva
    (nad a pod stredom otvoru, kde vybranie r 6,65 prechádza do otvoru r 6,05) – inak sa odlomia pri zasúvaní serva. Ostrú hranu na ústí otvoru
    F10_A (pretína ju zrazenie hornej hrany dosky) zľahka zraziť. Obe plochy dorazu na spodnom výstupku NEBRÚSIŤ a nezrážať.
  - P_sachta, prah zadného okna (aj nový prah pod ním): tlačí sa ako previs na podperách. Jeho VRCH po tlači zarovnať brúsnym papierom na hranolčeku
    do roviny s dnom, rovnako ako dno (smie ubudnúť najviac 0,2 mm); nad ním prechádza príruba ucha s vôľou len 0,15 mm. Kontrola: krok B4c.
    ČELO prahu (plôška, o ktorú sa opiera pätka držiaka) nebrúsiť.
  - T_cap: otvor vŕtať Ø3,1 až po vytvrdení. T_paluba: ako v rev. 2.

Podrobnosti a čísla: opravy3.md, T4_spec.md kap. 17.17.
"""
os.makedirs(os.path.join(OUTD, "out"), exist_ok=True)
open(os.path.join(OUTD, "out", "zmeny_rev3.txt"), "w").write(ZM)
json.dump(dict(limits=limits, all_cases=allcases, fe=fe_rows, n_fail_rows=nfail_rows, n_fail_spots=nfail_spots, failsafe=fs, checks=ck, stop_min_Nmm=stop_min, tq_pct=tq_pct,
               tq_Nmm=tq_Nmm, steps_85=STEPS_85, reprint=reprint, unchanged_printed=same, other_changed=other, pair_forces_m90=pfm,
               fixback=dict(V1=V1, gap_variants_computed=sorted(G_VAR), failsafe_above=fs_rows, f12=dict(len=F12_LEN, play=F12_PLAY, behind_flange=F12_BEHIND, engagement=F12_ENG,
                                                                                                    start_before_seat=F12_START),
                            ptfe_cap=dict(h=ptfe_h, h_rev2=ptfe_h_old, above_base=ptfe_lo), spline=dict(tip=SPL_TIP, boss=SPL_BOSS, len=SPL_LEN, floor_underside=SPL_ROOF, clearance=SPL_CLR)),
               stl_stamp=R["stl_stamp"], h=R["h"], missing=R["cases_missing"], all_converged=R["all_converged"]),
          open(os.path.join(OUTD, "rev3_work", "summary.json") if OUTD == T4 else os.path.join(OUTD, "summary.json"), "w"), indent=1, default=str)
print(f"docs written: {len(fe_rows)} spots, {nfail_spots} fail, limits {[(l['case'], l.get('capacity_Nmm', l['capacity_N'])) for l in limits]}; "
      f"stops {[(c, l['capacity_Nmm']) for c, l in stop_all.items()]} tq {tq_pct} %; reprint {RP}; spec 17.17 lines {S17.count(chr(10))}")
