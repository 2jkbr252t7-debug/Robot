#!/opt/venv/cad/bin/python
"""NOVA mini - T4 torso: global checks K1 - K11 of the brief  ->  checks.json  (+ checks.log)

    /opt/venv/cad/bin/python checks.py                 run everything that is stale, write checks.json
    /opt/venv/cad/bin/python checks.py K3 K6           only these sections (the others are kept if still valid)
    /opt/venv/cad/bin/python checks.py --force [K..]   ignore the caches
    /opt/venv/cad/bin/python checks.py --no-modules    do not (re)run the module check scripts (their results are then only
                                                       used when their stamp matches the STL files on disk)

Honesty rules
* every section stores the stamp of the STL set it ran on; a section whose stamp differs from the files on disk is
  reported as NOT RUN (stale), never as PASS;
* a section that raises, or whose helper (Blender script, module check) did not produce a result, is NOT RUN;
* declared fits / thin features / exceptions are listed with their reason in the section; a value below its limit without
  a declaration is a FAIL.

Sources: parts.json + stl/ written by build_all.py; finished parts of variant B from /tmp/claude-0/gapwf/fin/B/stl.
Helpers: checks_bl.py (Blender BVH: K2, K4, K5 play, K7, K8, K9), the module check scripts of the three builders
(t4_ram_checks.py, t4_pan_checks.py, checks_obal.py + obal_work/mesh_checks.py + obal_work/slide_checks.py).
"""
from __future__ import annotations
import os, sys, json, math, time, re, ast, subprocess, hashlib, traceback

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np                                      # noqa: E402
import t4_common as C                                   # noqa: E402
import t4_mesh as TM                                    # noqa: E402

CAD, BL = "/opt/venv/cad/bin/python", "/opt/venv/bl/bin/python"
WORK = os.path.join(HERE, "integ_work")
os.makedirs(WORK, exist_ok=True)
T0 = time.time()
ARGV = sys.argv[1:]
FORCE = "--force" in ARGV
NO_MOD = "--no-modules" in ARGV
SECTIONS = ["K1", "K2", "K3", "K4", "K5", "K6", "K7", "K8", "K9", "K10", "K11"]
WANT = [a for a in ARGV if a in SECTIONS] or SECTIONS
LOG = open(os.path.join(HERE, "checks.log"), "a")


def say(*a):
    s = f"[{time.time() - T0:7.1f}] " + " ".join(str(x) for x in a)
    print(s, flush=True); LOG.write(s + "\n"); LOG.flush()


DOC = json.load(open(os.path.join(HERE, "parts.json")))
PARTS = DOC["parts"]
REC = {r["name"]: r for r in PARTS}
B_MATE = ["golier_prstenec", "golier_kotuc", "krk_predna_polovica", "krk_zadna_polovica", "kabel"]


def stl_stamp():
    """one hash of the STL files on disk (all parts of parts.json) - geometry identity of a check result"""
    h = hashlib.md5()
    for n in sorted(REC):
        h.update(n.encode()); h.update(TM.md5(os.path.join(HERE, "stl", n + ".stl")).encode())
    return h.hexdigest()[:16]


STAMP = stl_stamp()
PARTS_JSON_OK = all(REC[n]["stl"]["md5"] == TM.md5(os.path.join(HERE, "stl", n + ".stl")) for n in REC)


def rd(v, n=3):
    return None if v is None else round(float(v), n)


def res(status, summary, **details):
    return dict(status=status, summary=summary, stl_stamp=STAMP, generated=time.strftime("%Y-%m-%d %H:%M:%S"), **details)


# =====================================================================================================================
# helpers: Blender sections and module check scripts (cached by the STL stamp)
# =====================================================================================================================
def bl_section(key, opts=(), timeout=5400):
    """run checks_bl.py <key> unless integ_work/bl_<key>.json is already valid for the current STL set"""
    f = os.path.join(WORK, f"bl_{key}.json"); st = os.path.join(WORK, f"bl_{key}.stamp")
    if not FORCE and os.path.exists(f) and os.path.exists(st) and open(st).read().strip() == STAMP:
        return json.load(open(f))
    if os.path.exists(f):
        os.remove(f)
    say(f"   running checks_bl.py {key} ...")
    with open(os.path.join(WORK, f"bl_{key}.log"), "w") as lg:
        p = subprocess.run([BL, os.path.join(HERE, "checks_bl.py"), key, *opts], stdout=lg, stderr=subprocess.STDOUT, cwd=HERE, timeout=timeout)
    if p.returncode != 0 or not os.path.exists(f):
        raise RuntimeError(f"checks_bl.py {key} failed (exit {p.returncode}); see integ_work/bl_{key}.log")
    open(st, "w").write(STAMP)
    return json.load(open(f))


MODCHK = {   # module check scripts: command, result file
    "ram": ([CAD, "t4_ram_checks.py"], "ram_checks.json"),
    "pan": ([CAD, "t4_pan_checks.py", "A", "B", "C", "D", "E", "F", "G", "H"], "pan_checks.json"),
    "obal_mesh": ([BL, "obal_work/mesh_checks.py"], "obal_work/mesh_checks.json"),
    "obal_slide": ([CAD, "obal_work/slide_checks.py"], "obal_work/slide_checks.json"),
    "obal": ([CAD, "checks_obal.py"], "checks_obal.json"),
}
_MOD_NOTE = {}


def module_check(name):
    """result dict of a module check script that is valid for the STL files on disk, or None (-> the caller reports NOT RUN).
    The scripts are (re)run here unless --no-modules; a stamp file records the STL set they ran on."""
    cmd, out = MODCHK[name]
    st = os.path.join(WORK, f"mod_{name}.stamp")
    f = os.path.join(HERE, out)
    if not FORCE or NO_MOD:
        if os.path.exists(f) and os.path.exists(st) and open(st).read().strip() == STAMP:
            return json.load(open(f))
    if NO_MOD:
        _MOD_NOTE[name] = "module check result is stale for the STL files on disk and --no-modules was given"
        return None
    if name == "obal":                                   # checks_obal.py merges the two helper results
        for dep in ("obal_mesh", "obal_slide"):
            if module_check(dep) is None:
                _MOD_NOTE[name] = f"{dep} did not run"
                return None
    say(f"   running module check {name}: {' '.join(cmd)}")
    t = time.time()
    with open(os.path.join(WORK, f"mod_{name}.log"), "w") as lg:
        p = subprocess.run(cmd, stdout=lg, stderr=subprocess.STDOUT, cwd=HERE)
    say(f"   module check {name}: exit {p.returncode} in {time.time() - t:.0f} s")
    if not os.path.exists(f) or os.path.getmtime(f) < t - 1:
        _MOD_NOTE[name] = f"script produced no result (exit {p.returncode}), see integ_work/mod_{name}.log"
        return None
    if stl_stamp() != STAMP:
        _MOD_NOTE[name] = "the STL set changed while the module check ran"
        return None
    open(st, "w").write(STAMP)
    return json.load(open(f))


def decl_from(script, names):
    """top-level assignments / functions `names` of a module check script, evaluated without running the script"""
    src = open(os.path.join(HERE, script)).read()
    tree = ast.parse(src)
    ns = dict(np=np, math=math, C=C)
    for node in tree.body:
        tgt = None
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            tgt = node.targets[0].id
        elif isinstance(node, ast.FunctionDef):
            tgt = node.name
        if tgt in names:
            exec(compile(ast.Module([node], []), script, "exec"), ns)
    return {n: ns[n] for n in names if n in ns}


def rx_any(name, pats):
    return any(re.match(p, name) for p in pats)


# =====================================================================================================================
# K1  valid closed solids / watertight STL
# =====================================================================================================================
def K1():
    bad, rows, comps = [], [], {}
    for r in PARTS:
        n = r["name"]
        st = TM.mesh_stats(TM.stl(n, TM.STL_DIR))
        ok = (r["valid"] and r["n_solids"] == 1 and r["volume"] > 0 and st["open_edges"] == 0 and st["nonmanifold_edges"] == 0
              and st["flipped_edges"] == 0 and st["volume"] > 0 and st["components"] == 1 and r.get("bbox_ok", True)
              and abs(st["volume"] - r["volume_mesh"]) <= max(0.02, 2e-4 * abs(r["volume_mesh"]))
              and all(abs(a - b) <= 0.03 for a, b in zip(st["bbox"], r["bbox"])))
        rows.append(dict(name=n, module=r["module"], group=r["group"], brep_valid=r["valid"], n_solids=r["n_solids"], volume_occ=r["volume"],
                         volume_stl=rd(st["volume"], 2), tris=st["tris"], open_edges=st["open_edges"], nonmanifold_edges=st["nonmanifold_edges"],
                         flipped_edges=st["flipped_edges"], components=st["components"], bbox_stl=st["bbox"],
                         bbox_expected_ok=r.get("bbox_ok"), step=r.get("step"), ok=bool(ok)))
        if st["components"] != 1:
            comps[n] = st["component_volumes"]
        if not ok:
            bad.append(n)
    step_big = [f for f in os.listdir(os.path.join(HERE, "step")) if os.path.getsize(os.path.join(HERE, "step", f)) > C.INTEG["STEP_MAX_MB"] * 1e6]
    step_missing = [r["name"] for r in PARTS if r.get("step") and not os.path.exists(os.path.join(HERE, r["step"]))]
    stl_missing = [r["name"] for r in PARTS if not os.path.exists(os.path.join(HERE, "stl", r["name"] + ".stl"))]
    ok = not bad and not step_big and not step_missing and not stl_missing and PARTS_JSON_OK
    return res("PASS" if ok else "FAIL",
               f"{len(PARTS) - len(bad)}/{len(PARTS)} parts: valid single BREP solid, volume > 0, STL closed (0 open / non-manifold / flipped edges), "
               f"one surface component, bbox as designed; STEP null for {len(DOC['step_null'])} loft-derived parts (rule: < 12 MB), "
               f"{len(step_big)} STEP over the limit on disk",
               not_ok=bad, multi_component=comps, step_null=DOC["step_null"], step_over_limit=step_big, step_missing=step_missing,
               parts_json_matches_stl=PARTS_JSON_OK, parts=rows,
               method="BREP: is_valid / number of solids / volume from the build (parts.json, written by build_all.py); STL: re-read from disk, "
                      "welded at 1e-5, every edge used exactly twice and once per direction, signed volume > 0 and equal to parts.json, "
                      "connected surface components = 1 (no hidden inner void)")


# =====================================================================================================================
# K2  no interference at rest
# =====================================================================================================================
K2_FITS = [   # (regex a, regex b, max common volume mm3, reason)  - designed overlaps (press / thread / heat-set / serration / clamp)
    (r"servo_J1$", r"skr_F6$", 35.0, "F6 M3 screw in the thread of the STS3215 output shaft (the shaft is modelled solid)"),
    (r"servo_pan$", r"skr_pastorok_pan$", 12.0, "pinion screw M2 in the thread of the STS3032 output shaft (modelled solid)"),
    (r"T_ram$", r"vl_F(2|3|5)", 7.5, "heat-set insert M2.5 (OD 3.5 in a D3.2 hole, PETG)"),
    (r"T_ram$", r"vl_F8_", 5.5, "heat-set insert M2 (OD 3.2 in a D2.9 hole, PETG)"),
    (r"T_ram$", r"skr_F(4|7|14)_", 3.6, "thread-forming M2 screw in a D1.7 pilot"),
    (r"T_paluba$", r"skr_fpc$", 2.6, "thread-forming M2 countersunk screw in the D1.6 pilot of the deck"),
    (r"T_paluba$", r"cap_pan$", 2.5, "pivot pin D6.00 pressed in D5.95 x 3.5"),
    (r"T_stred$", r"skrutka_(led|repro)_", 4.5, "thread-forming M2 x 6 in the D1.7 pilot of a front-stack boss"),
    (r"L_pata$", r"skr_F12$", 6.0, "thread-forming M2 x 8 in the D1.7 pilot of the foot"),
    (r"L_pata$", r"skr_jazyka$", 5.0, "M1.6 screw self-tapping in the D1.3 pilot of the foot"),
    (r"L_pata$", r"kolik_ucha$", 0.3, "ear dowel D1.50 pressed in D1.48"),
    (r"P_kluka$", r"servo_zdvih$", 4.0, "21T serration of the crank (D4.44 / 4.84) on the MG90S spline D4.8"),
    (r"P_kluka$", r"cap_kluky$", 0.5, "crank pin D2.00 pressed in D1.98"),
    (r"P_kluka$", r"skr_kluky$", 1.0, "countersunk head seat of the crank screw"),
    (r"servo_zdvih$", r"skr_kluky$", 12.0, "crank screw M2.5 in the servo shaft thread"),
    (r"P_drziak_serva$", r"skr_F11$", 5.0, "thread-forming M2 x 6 in the D1.7 pilot of the tab post"),
    (r"P_koleso$", r"kolik_dorazu$", 0.5, "stop pin D2.00 pressed in D1.98"),
    (r"P_(koleso|sachta)$", r"kolik_kolesa_", 0.5, "gear dowel D2 in its bonded hole"),
    (r"spoj_zdvih$", r"kabel_zdvih$", 8.0, "servo lead crimped in the 1 x 3 socket (flexible lead, reserved space)"),
    (r"servo_zdvih$", r"kabel_zdvih$", 16.0, "lead leaves the servo inside the reserved exit block"),
    (r"fpc_pan$", r"spoj_zdvih$", 0.5, "FR4 stiffener bonded on the FPC branch"),
    (r"T_prichytka_fpc$", r"fpc_pan$", 0.5, "static FPC end (0.12) pinched in the 0.10 clamp gap"),
    (r"(skr_F2_|skr_F3_|skr_F5|skr_F1_|skr_F10_|skrutka_klb_)", r"(vl_F2_|vl_F3_|vl_F5|vlozka_stred_|vl_F10_|vl_F8_)", 9.0, "machine screw in the thread of its brass insert"),
    (r"krk_predna_polovica$", r"krk_zadna_polovica$", 1e9, "the two neck halves of variant B (finished parts, checked in B)"),
    (r"kabel$", r"krk_(predna|zadna)_polovica$", 1e9, "wires of variant B inside their neck channels (finished parts, checked in B)"),
]
K2_CONTACT_DEPTH = 0.02        # overlaps shallower than this are coincident (glued / seated) faces, i.e. contact


def K2():
    d = bl_section("K2")
    rows, bad, fits, contacts = [], [], [], 0
    for r in d["touching"]:
        a, b = r["a"], r["b"]
        vol, dep = r.get("common_mm3") or 0.0, r.get("max_half_depth") or 0.0
        decl = None
        for pa, pb, vmax, why in K2_FITS:
            if (re.match(pa, a) and re.match(pb, b)) or (re.match(pa, b) and re.match(pb, a)):
                decl = (vmax, why); break
        real = bool(r.get("contained")) or (vol > 0.05 and dep >= K2_CONTACT_DEPTH)
        if not real:
            contacts += 1
            continue
        row = dict(a=a, b=b, modules=[REC.get(a, {}).get("module", "B"), REC.get(b, {}).get("module", "B")], common_mm3=vol, half_depth=dep,
                   contained=bool(r.get("contained")), at=(r.get("clusters") or [{}])[0].get("centre"))
        if decl and vol <= decl[0]:
            row.update(intended=decl[1], limit_mm3=decl[0]); fits.append(row)
        else:
            row.update(intended=None if not decl else decl[1] + f" - but volume over the declared {decl[0]} mm3"); bad.append(row)
        rows.append(row)
    cross = [r for r in fits if r["modules"][0] != r["modules"][1]]
    return res("PASS" if not bad else "FAIL",
               f"{len(d['names'])} parts ({len(PARTS)} torso + {len(B_MATE)} finished parts of variant B), {d['pairs_tested']} bbox-overlapping pairs: "
               f"{len(bad)} unintended interference(s); {len(fits)} declared press / thread / insert fits ({len(cross)} across modules); "
               f"{contacts} pairs only touch (coincident faces, depth < {K2_CONTACT_DEPTH})",
               unintended=bad, intended_fits=fits, n_contacts=contacts, pairs_tested=d["pairs_tested"], method=d["method"],
               declared_fit_rules=[dict(a=a, b=b, max_mm3=v, why=w) for a, b, v, w in K2_FITS])


# =====================================================================================================================
# K8  exterior fidelity, seams, see-through
# =====================================================================================================================
def K8():
    d = bl_section("K8")
    ext, see = d["exterior_vs_T3"], d["see_through_26"]
    om = module_check("obal")
    notes, fail = [], []
    if not ext["ok"]:
        fail.append(f"exterior: {ext['n_bad_strict']} grid points off the T3 surface by more than 0.05 outside the declared zones")
    if not see["ok"]:
        fail.append(f"see-through: {see['see_through']} rays pass through the torso")
    # T4 analytic profile against T3 (independent of the meshes)
    dd = np.arange(2.6, 88.5, 0.05)
    da = max(abs(C.prof(float(x))[0] - C.prof_t3(float(x))[0]) for x in dd); db = max(abs(C.prof(float(x))[1] - C.prof_t3(float(x))[1]) for x in dd)
    rim = np.arange(0.0, 2.6, 0.02)
    rim_dev = max(max(abs(C.prof(float(x))[0] - C.prof_t3(float(x))[0]), abs(C.prof(float(x))[1] - C.prof_t3(float(x))[1])) for x in rim)
    if max(da, db) > 0.01:
        fail.append(f"analytic T4 profile differs from T3 below the rim zone by {max(da, db):.3f}")
    # seams: nominal 0.5 +- 0.1 (x seams, white / black), door 0.25
    bb = {n: REC[n]["bbox"] for n in ("T_stred", "T_bok_L", "T_bok_P", "T_spodok", "T_dvere")}
    seam_x = (bb["T_bok_L"][0] - bb["T_stred"][1], bb["T_stred"][0] - bb["T_bok_P"][1])       # lip tip is inside: use the cap edge planes below
    seams = dict(white_black=dict(white_lower_edge_z=bb["T_stred"][4], black_visible_edge_z=C.Z_CAP_TOP, width=rd(bb["T_stred"][4] - C.Z_CAP_TOP)))
    mod = {}
    if om is not None:
        m3, s1 = om.get("M3_exterior", {}), om.get("S1_seam_backing", {})
        mod = dict(M3_exterior=dict(ok=m3.get("ok"), grid_points=m3.get("grid_points"), dev_min=m3.get("dev_min"), dev_max=m3.get("dev_max"),
                                    n_over_0p05=m3.get("n_dev_over_0p05_outside_declared"), uncovered_unexplained=m3.get("uncovered_unexplained"),
                                    seam_widths_measured=m3.get("seam_widths_measured")),
                   S1_seam_backing=dict(ok=s1.get("ok"), see_through_total=s1.get("see_through_total"), declared_open=s1.get("declared_open")))
        seams["measured_on_mesh"] = m3.get("seam_widths_measured")
        sw = m3.get("seam_widths_measured") or {}
        for k, v in sw.items():
            nominal = 0.25 if "door" in k else 0.5
            if not (nominal - 0.1 - 1e-6 <= min(v) and max(v) <= nominal + 0.1 + 1e-6):
                fail.append(f"seam width {k}: {v} outside {nominal} +- 0.1")
        if not m3.get("ok"):
            fail.append("OBAL M3 (exterior against the analytic T4 surface) not ok")
        if s1.get("see_through_total", 1) != 0:
            fail.append("OBAL S1: a seam line of sight leaves the torso again")
        for k, v in (s1.get("declared_open") or {}).items():
            notes.append(f"seam not backed (dark interior visible, no see-through): {k}: {v['open']} of {v['rays']} lines of sight - {v['reason']}")
    else:
        return res("NOT RUN", "module check OBAL (M3 exterior grid, S1 seam backing, seam widths) has no valid result for the STL files on disk: "
                   + _MOD_NOTE.get("obal", ""), exterior_vs_T3=ext, see_through_26=see)
    if abs(seams["white_black"]["width"] - 0.5) > 0.1:
        fail.append(f"white / black seam {seams['white_black']['width']}")
    zs = ext["zones"]
    return res("PASS" if not fail else "FAIL",
               f"white shells + plugs: {zs['white']['points']} T3 grid points, deviation {ext['dev_strict_min']} .. {ext['dev_strict_max']} mm, "
               f"{ext['n_bad_strict']} over 0.05 or uncovered outside the declared zones; rim zone D1 max {max(abs(zs[k]['dev_min']), abs(zs[k]['dev_max'])) if (k := [q for q in zs if q.startswith('D1')][0]) else None} "
               f"(declared <= 1.5); analytic T4 vs T3 profile below drop 2.6: {max(da, db):.4f}; seams x {((om or {}).get('M3_exterior', {}).get('seam_widths_measured') or {}).get('seam_x, width along x (16 stations)')}, "
               f"white / black {seams['white_black']['width']}; see-through from 26 viewpoints: {see['see_through']} of {see['rays']} rays; "
               f"seam lines of sight leaving the torso: {mod['S1_seam_backing']['see_through_total']}",
               failures=fail, notes=notes, exterior_vs_T3=ext, see_through_26=dict(rays=see["rays"], see_through=see["see_through"], pitch=see["pitch"],
                                                                                    scene=see["scene"], note=see["note"], views=see["views"]),
               analytic_profile_vs_T3=dict(max_da_below_rim=rd(da, 5), max_db_below_rim=rd(db, 5), max_dev_in_rim_zone_drop_lt_2p6=rd(rim_dev, 3)),
               seams=seams, module_obal=mod,
               declared_deviations=["D1 top rim: flat rim r 28.4 -> 29.6 + blend (drop < 2.6): <= 1.2 horizontal / 0.5 normal",
                                    "D2 black skirt disc r 28.5 under the cap (z -86.2 .. -85.2), C-shaped (open at the pinion passage)",
                                    "D3 white / black seam 0.5 (cap edge at z -81.5)", "shoulder joints, light guide, grille (T3 features)",
                                    "door: finger-nail notch 12 x 1.2 x 0.85 in the bottom edge",
                                    "underside of the cap: F1 / F2 countersinks, 2 drain holes D3, pinion passage (underside is free)"])


# =====================================================================================================================
# K9  real head / neck against the torso
# =====================================================================================================================
def K9():
    d = bl_section("K9", ["--fine"])
    crit = d["criterion"]
    rows, table_needed, fail = [], {}, []
    for lift, v in sorted(d["lifts"].items(), key=lambda kv: -float(kv[0])):
        rows.append(dict(lift=float(lift), tilt_down_max=v["tilt_table_B"]["down"], tilt_up_max=v["tilt_table_B"]["up"], min_clearance=v["min_clearance"],
                         at=v["at"], min_by_tilt=v["min_by_tilt"], pan_spread_at_limits=v["pan_spread_at_limits"],
                         head_vs_stage_min=v["head_vs_stage"]["min"], head_vs_stage_at=dict(tilt=v["head_vs_stage"]["tilt"], part=v["head_vs_stage"]["stage_part"],
                                                                                         head_part=v["head_vs_stage"]["head_part"])))
        if v["reduced_pans"]:
            table_needed[lift] = v["limit_per_pan"]
        if v["min_clearance"] <= 0.02:
            fail.append(f"lift {lift}: the head touches the torso inside the B tilt table ({v['at']})")
    worst = d["worst"]
    margin = d["min_clearance"] - crit
    stage_min = min(r["head_vs_stage_min"] for r in rows)
    # collision at pan 0 inside the B table would require reshaping (brief 5.3); anything below 0.5 gets a tilt limit table
    status = "FAIL" if fail else "PASS"
    return res(status,
               f"head (variant B STL, {len(d['head_parts'])} parts) vs torso meshes, pan -85..85 step 5 x lift 20 / 12.5 / 7.5 / 0 x tilt inside the B table "
               f"(2.5 deg steps): min clearance {d['min_clearance']} mm at lift {worst['lift']}, tilt {worst['tilt']}, pan {worst['pan']} "
               f"({worst['torso_part']} / {worst['head_part']}); criterion {crit}; "
               + ("NO pose below the criterion - no pan-dependent tilt table is needed" if not table_needed else
                  f"poses below the criterion at lifts {sorted(table_needed)} - pan-dependent tilt limit table attached")
               + f"; margin {margin:.3f} mm; head vs the parts turning with it (collar disc, well): min {stage_min} (declared guide fits)",
               failures=fail, criterion=crit, per_lift=rows, pan_dependent_tilt_limit_table=table_needed or None,
               clearance_map={lift: dict(pans=d["pans"], by_tilt=v["clearance_map"]) for lift, v in d["lifts"].items()},
               recommendation=("lift 10 .. 15: limit the tilt down to 27.5 deg in the firmware (all pans): the 0.5 criterion is met at 30 deg with "
                               f"only {margin:.3f} mm of margin (print tolerance of the rim is larger)") if margin < 0.1 else None,
               declared=["head hinge lugs (usko_kryt / usko_lozisko) run with the neck on the PTFE strips of the well: 0.17 (0.30 bare) - guide fit",
                         "hinge lugs in the collar-disc slot 0.25 (variant B, unchanged)"],
               static_parts=d["static_parts"], not_included=d["not_included"], method=d["method"])


# =====================================================================================================================
# K11  mass + centre of gravity
# =====================================================================================================================
def K11():
    groups, no_mass = {}, []
    for r in PARTS:
        if r["mass_g"] is None:
            no_mass.append(r["name"]); continue
        g = groups.setdefault(r["group"], dict(mass=0.0, mom=np.zeros(3), printed=0.0, bought=0.0, n=0))
        g["mass"] += r["mass_g"]; g["mom"] += r["mass_g"] * np.array(r["cog"]); g["n"] += 1
        g["printed" if r["printed"] else "bought"] += r["mass_g"]
    out = {}
    for k, g in groups.items():
        out[k] = dict(mass_g=rd(g["mass"], 2), printed_g=rd(g["printed"], 2), bought_g=rd(g["bought"], 2), parts=g["n"],
                      cog=[rd(v, 2) for v in g["mom"] / g["mass"]])
    tor = [groups[k] for k in ("T", "P", "L") if k in groups]
    m = sum(g["mass"] for g in tor); cog = sum(g["mom"] for g in tor) / m
    off = float(np.hypot(cog[0], cog[1]))
    heavy = sorted([(r["mass_g"], r["name"]) for r in PARTS if r["mass_g"] and r["group"] != "Z"], reverse=True)[:10]
    ok = not no_mass and off < 12.5
    return res("PASS" if ok else "FAIL",
               f"torso (groups T + P + L, {sum(g['n'] for g in tor)} parts, without head / neck / arms / base): {m:.1f} g, centre of gravity "
               f"({cog[0]:.1f}, {cog[1]:.1f}, {cog[2]:.1f}) in the B frame = {off:.1f} mm from the J1 axis, {cog[2] - C.Z_BRG[1]:.1f} mm above the 6805 bearing "
               f"(criterion: every part has a mass, offset < 12.5 = bearing bore radius); dummy stand {out.get('Z', {}).get('mass_g')} g",
               torso_mass_g=rd(m, 2), torso_cog=[rd(v, 2) for v in cog], cog_offset_from_J1_axis=rd(off, 2), groups=out, parts_without_mass=no_mass,
               heaviest=[dict(name=n, mass_g=q) for q, n in heavy], densities_g_cm3=DOC["densities_g_cm3"],
               method="mass: printed parts = STL volume x density (resin 1.15, PETG 1.27, POM 1.41); bought parts = datasheet mass given by the "
                      "module, otherwise volume x density (brass 8.5, steel 7.85, magnet 7.5, PTFE 2.2); centre of gravity of each part = "
                      "volume centroid of its STL (uniform density)")


# =====================================================================================================================
RUN = {"K1": K1, "K2": K2, "K8": K8, "K9": K9, "K11": K11}


# =====================================================================================================================
# K3  moving clearances
# =====================================================================================================================
K3_RULES_PL = [   # lift / crank parts against the parts of the pan stage: (regex moving, regex stage part, min allowed, reason)
    (r"(krk_(predna|zadna)_polovica|L_pata|L_jazyk|L_ucho)$", r"ptfe_pasik_", 0.15, "neck / foot run on the PTFE strips of the guide lands: 0.17 (neck), 0.37 (foot)"),
    (r"L_pata$", r"kolik_kolesa_", 0.5, "foot 0.5 above the hub disc at rest (end position); the gear dowels end 0.05 below the hub top"),
    (r"kabel$", r"(P_sachta|ptfe_pasik_)", 0.25, "neck wires of variant B inside the neck / foot slot, beside the lands"),
    (r"skr_kluky$", r"servo_zdvih$", 0.0, "crank screw M2.5 in the thread of the MG90S output shaft (turns with the shaft)"),
    (r"L_ucho$", r"skr_kluky$", 0.38, "countersunk head of the crank screw, flush in the crank face: the same 0.40 side gap as crank <-> ear"),
    (r"(skr_F12|kolik_ucha|skr_jazyka)$", r"(P_sachta|ptfe_pasik_)", 0.45, "fastener of the ear / tongue, moves with the foot: 0.5 above the well floor "
                                                                          "at rest (end position), inside the window"),
]
K3_RULES_T = [    # additional rules against the static torso (the rules of t4_pan_checks.RULES_E are loaded too)
    (r"fpc_lift$", r"T_paluba$", 1.0, None),
]
K3_RULES_J1 = [   # J1 sweep: (regex torso part, regex dummy part, min allowed, reason)
    (r"lozisko_6805$", r"Z_naboj_test$", 0.0, "6805 inner ring D25 on the hub post D24.96 and on its shoulder (bearing seat)"),
    (r"T_spodok$", r"Z_naboj_test$", 0.28, "foot ring 0.30 above the stop block (spec 5.5); the stop lug meets the block only at the hard stops"),
]


def _rule(rules, a, b):
    for pa, pb, dmin, why in rules:
        if re.match(pa, a) and re.match(pb, b):
            return dmin, why
    return None


_PAN_MODEL = {}


def pan_model():
    """static torso + pan stage / lift parts with sampling, shared by K3 (firmware range) and K6 (hard-stop poses).
    Returns a dict with scan(pans, lifts) -> {(moving, static, rule index): (distance, pan, lift, point)} and the part lists."""
    if _PAN_MODEL:
        return _PAN_MODEL
    import t4_pan as MP
    decl = decl_from("t4_pan_checks.py", ["_r", "RULES_E", "DECL_NEAR"])
    RULES_E = decl["RULES_E"]
    grp = {n: r["group"] for n, r in REC.items()}

    def tris_of(shape):
        V, T = C.mesh_of(shape, 0.01, 0.1)
        return V[T]

    TRI = {n: TM.stl(n, TM.STL_DIR) for n in REC}
    for n in B_MATE:
        TRI[n] = TM.stl(n, TM.B_STL)
    TRI["fpc_stage"] = tris_of(MP.fpc_stage())
    CRANK = ("P_kluka", "cap_kluky", "skr_kluky")
    P_rigid = [n for n in REC if grp[n] == "P" and n not in CRANK and n != "fpc_pan"] + ["golier_kotuc", "fpc_stage"]
    L_set = [n for n in REC if grp[n] == "L"] + ["krk_predna_polovica", "krk_zadna_polovica", "kabel"]
    static = [n for n in REC if grp[n] == "T"] + ["golier_prstenec"]

    def crank_x(T, theta):
        a = math.radians(-theta); c, s = math.cos(a), math.sin(a)
        R = T.copy(); y, z = T[..., 1] - MP.YL, T[..., 2] - MP.ZL
        R[..., 1] = MP.YL + c * y - s * z; R[..., 2] = MP.ZL + s * y + c * z
        return R

    _fl = {}

    def moving(name, lift):
        if name in CRANK:                                   # the crank screw sits on the shaft axis and turns with the crank
            return crank_x(TRI[name], MP.crank_angle(lift))
        if name == "fpc_lift":
            if lift not in _fl:
                _fl[lift] = tris_of(MP.fpc_lift(lift))
            return _fl[lift]
        T = TRI[name].copy(); T[..., 2] += lift
        return T

    sp = {}
    for n in static:
        T = TRI[n]
        lo, hi = T.min(1), T.max(1)
        rmin = np.minimum(np.hypot(T[:, :, 0], T[:, :, 1]).min(1), np.hypot(T[:, :, 0].mean(1), T[:, :, 1].mean(1)))
        m = (hi[:, 2] > -53.0) & (lo[:, 2] < 8.0) & ((rmin < 39.5) | (np.linalg.norm(hi - lo, axis=1) > 6.0))
        if m.sum():
            sp[n] = T[m]
    MS = TM.Multi(sp, 0.4)
    say(f"   pan model: {len(sp)} static parts near the pan stage, {len(MS.T)} triangles, {len(MS.S)} samples")
    rule_of = {}
    for i, (a, b, zone, dmin, txt) in enumerate(RULES_E):
        rule_of.setdefault((a, b), []).append(i)
    SMP = {n: TM.sample(TRI[n], 0.3)[0] for n in P_rigid}
    SMP["golier_kotuc"] = SMP["golier_kotuc"][np.hypot(SMP["golier_kotuc"][:, 0], SMP["golier_kotuc"][:, 1]) > 25.5]   # rim (the slot is B's)
    LM = list(CRANK) + L_set + ["fpc_lift"]
    _sl = {}

    def smpl(n, lf):
        if (n, lf) not in _sl:
            _sl[(n, lf)] = TM.sample(moving(n, lf), 0.3)[0]
        return _sl[(n, lf)]

    def scan(pans, lifts, fpc_loop=True):
        store = {}

        def run(name, Q, pan, lift, skip=()):
            rows, e, pid = MS.query(Q)
            if len(rows) == 0:
                return
            for p_ in np.unique(pid):
                b = MS.names[p_]
                if b in skip:
                    continue
                m = pid == p_
                r_, e_ = rows[m], e[m]
                cat = np.full(len(r_), -1)
                for i in rule_of.get((name, b), []):
                    zone = RULES_E[i][2]
                    zm = np.ones(len(r_), bool) if zone is None else zone(Q[r_])
                    cat[zm & (cat < 0)] = i
                for c in np.unique(cat):
                    mm = cat == c
                    k = int(np.argmin(e_[mm])); d = float(e_[mm][k])
                    key = (name, b, int(c))
                    if key not in store or d < store[key][0]:
                        store[key] = (d, pan, lift, [round(float(x), 2) for x in Q[r_[mm][k]]])

        for pan in pans:
            for n in P_rigid:
                run(n, TM.rotz(SMP[n], pan), pan, 0.0, skip=("pastorok_pan",) if n == "P_koleso" else ())
            for lf in lifts:
                for n in LM:
                    run(n, TM.rotz(smpl(n, lf), pan), pan, lf)
            if fpc_loop:
                run("fpc_loop", TM.sample(tris_of(MP.fpc_loop(pan)), 0.3)[0], pan, 0.0)
        return store

    _PAN_MODEL.update(scan=scan, TRI=TRI, P_rigid=P_rigid, L_set=L_set, LM=LM, CRANK=CRANK, static=list(sp), RULES_E=RULES_E, NEAR=decl["DECL_NEAR"],
                      moving=moving, grp=grp)
    return _PAN_MODEL


def K3():
    need = C.INTEG["MOVE_CLEAR"]
    PANS = [float(p) for p in np.arange(-85.0, 85.1, 5.0)]
    LIFTS = [float(v) for v in np.arange(0.0, 20.1, 2.5)]
    M = pan_model()
    TRI, P_rigid, L_set, LM, CRANK, RULES_E, NEAR, moving, grp = (M[k] for k in ("TRI", "P_rigid", "L_set", "LM", "CRANK", "RULES_E", "NEAR", "moving", "grp"))
    sp = M["static"]
    # ------------------------------------------------------------ (a) P / L against the static torso, pan x lift
    store = M["scan"](PANS, LIFTS)
    n_pose = len(PANS) * len(LIFTS)
    say(f"   K3a: {n_pose} pan x lift poses done")
    rows_a, bad = [], []
    for (a, b, c), (d, pan, lf, at) in sorted(store.items(), key=lambda kv: kv[1][0]):
        lim, why = (RULES_E[c][3], RULES_E[c][4]) if c >= 0 else (need, None)
        if c < 0:
            r2 = _rule(K3_RULES_T, a, b)
            if r2:
                lim, why = r2
        ok = d >= lim - 1e-3
        if d < 1.5 or not ok:
            rows_a.append(dict(moving=a, static=b, min_mm=rd(d), pan=pan, lift=lf, at=at, required=lim, declared=why, ok=bool(ok)))
        if not ok:
            bad.append(f"{a} <-> {b}: {d:.3f} < {lim} (pan {pan}, lift {lf})")
    # gear against the ROTATING pinion (ratio 2 : 1)
    pin_T = TRI["pastorok_pan"]
    Sg = TM.sample(TRI["P_koleso"], 0.15)[0]
    gmin = (9.0, None)
    for pan in list(np.arange(-85.0, 85.01, 2.5)):
        Tp = TM.rotz(pin_T, -2.0 * pan, *C.PAN_AX)
        Q = TM.rotz(Sg, pan)
        m = np.hypot(Q[:, 0] - C.PAN_AX[0], Q[:, 1] - C.PAN_AX[1]) < 8.6
        mm = TM.Multi({"pinion": Tp}, 0.15).min_by_part(Q[m], 1.0)
        if "pinion" in mm and mm["pinion"][0] < gmin[0]:
            gmin = (mm["pinion"][0], float(pan))
    if gmin[0] < 0.005:
        bad.append(f"pan gear <-> rotating pinion: flank gap {gmin[0]:.4f}")
    free_a = [r for r in rows_a if r["declared"] is None]
    # ------------------------------------------------------------ (b) lift / crank parts against the stage, lift 0..20
    MP_ = TM.Multi({n: TRI[n] for n in P_rigid}, 0.35)
    near = {}

    def upd(a, b, d, lift, q):
        if (a, b) not in near or d < near[(a, b)][0]:
            near[(a, b)] = (d, lift, [round(float(x), 2) for x in q])

    for lf in LIFTS:
        mt = {n: moving(n, lf) for n in LM}
        mc = TM.Multi({n: mt[n] for n in CRANK}, 0.2)
        for a in LM:
            Sa = TM.sample(mt[a], 0.3)[0]
            for b, (d, q) in MP_.min_by_part(Sa, 1.3).items():
                upd(a, b, d, lf, q)
            if a not in CRANK:
                for b, (d, q) in mc.min_by_part(Sa, 1.3).items():
                    upd(a, b, d, lf, q)
    rows_b = []
    FPC_OK = "FPC: bonded / anchored on this part (flexible strip between its anchors)"
    for (a, b), (d, lift, at) in sorted(near.items(), key=lambda kv: kv[1][0]):
        if d >= need - 1e-3:
            continue
        dec = NEAR.get((a, b)) or NEAR.get((b, a))
        lim, why = (dec[0], dec[2]) if dec else (need, None)
        if dec is None:
            r2 = _rule(K3_RULES_PL, a, b)
            if r2:
                lim, why = r2
            elif "fpc" in a or "fpc" in b:
                lim, why = 0.0, FPC_OK
        ok = d >= lim - 1e-3
        rows_b.append(dict(moving=a, stage_part=b, min_mm=rd(d), lift=lift, at=at, required=lim, declared=why, ok=bool(ok)))
        if not ok:
            bad.append(f"{a} <-> {b} (stage): {d:.3f} < {lim} at lift {lift}")
    # ------------------------------------------------------------ (c) J1 sweep against the dummy hub
    rot = [n for n in REC if grp[n] in ("T", "P", "L") and REC[n]["bbox"][4] < -84.4]
    zn = [n for n in REC if grp[n] == "Z"]
    MZ = TM.Multi({n: TRI[n] for n in zn}, 0.35)
    j1 = {}
    PHIS = [float(v) for v in np.arange(-155.0, 155.1, 5.0)]
    for n in rot:
        S0 = TM.sample(TRI[n], 0.35)[0]
        S0 = S0[S0[:, 2] < -84.0]
        for phi in PHIS:
            if n in ("pastorok_J1", "skr_F6"):
                S = TM.rotz(TM.rotz(S0, phi, *C.J1_AX), phi)          # rolls on the fixed sun gear 18 : 18 -> turns 2 x phi in space
            else:
                S = TM.rotz(S0, phi)
            for b, (d, q) in MZ.min_by_part(S, 1.6).items():
                fw = abs(phi) <= 150.0
                key = (n, b, "firmware +-150" if fw else "to the hard stop +-155")
                if key not in j1 or d < j1[key][0]:
                    j1[key] = (d, phi, [round(float(x), 2) for x in q])
    rows_c = []
    for (a, b, rng), (d, phi, at) in sorted(j1.items(), key=lambda kv: kv[1][0]):
        lim, why = need, None
        r2 = _rule(K3_RULES_J1, a, b)
        if r2:
            lim, why = r2
        if (a, b) == ("pastorok_J1", "Z_koleso_J1"):
            lim, why = 0.005, "J1 gear mesh m1 18 / 18, C 18.00: flank gap (pinion rolled 2 x phi)"
        if (a, b) == ("T_spodok", "Z_naboj_test") and rng.startswith("to the hard"):
            lim, why = 0.0, "stop lug against the stop block = the hard stop (+-154.7)"
        ok = d >= lim - 1e-3
        if d < 1.5 or not ok:
            rows_c.append(dict(torso_part=a, dummy_part=b, range=rng, min_mm=rd(d), phi=phi, at=at, required=lim, declared=why, ok=bool(ok)))
        if not ok:
            bad.append(f"J1: {a} <-> {b}: {d:.3f} < {lim} at phi {phi} ({rng})")
    free_c = [r for r in rows_c if r["declared"] is None]
    mins = dict(P_L_vs_static_undeclared=min((r["min_mm"] for r in free_a), default=None),
                stage_internal_undeclared=min((r["min_mm"] for r in rows_b if r["declared"] is None), default=None),
                J1_undeclared=min((r["min_mm"] for r in free_c), default=None), pan_gear_flank_gap=rd(gmin[0], 4))
    return res("PASS" if not bad else "FAIL",
               f"pan -85..85 step 5 x lift 0..20 step 2.5 ({n_pose} poses), {len(P_rigid) + len(LM) + 1} moving bodies (pan stage, lift servo, crank at its "
               f"angle, foot / ear / tongue, neck, FPC lift loop and FPC pan loop in their posed shapes) against {len(sp)} static parts: smallest "
               f"undeclared clearance {mins['P_L_vs_static_undeclared']} (need {need}); inside the stage over the stroke: every pair below 1.0 is a "
               f"declared running fit ({len(rows_b)} pairs); pan gear <-> rotating pinion flank gap {mins['pan_gear_flank_gap']}; "
               f"J1 -155..155 vs the dummy: smallest undeclared {mins['J1_undeclared']}; failures: {len(bad)}",
               failures=bad, minima=mins, pan_lift_vs_static_below_1p5=rows_a, stage_internal_below_1p0=rows_b, J1_sweep_below_1p5=rows_c,
               rotating_parts_below_the_cap=rot,
               method="exact point-to-triangle distances from surface samples (all vertices + 0.3 mm grid) of the moving parts to the STL "
                      "triangles of the static parts (KD-tree of 0.4 mm samples names the 8 candidate triangles).  Declared sub-1.0 gaps: "
                      "RULES_E / DECL_NEAR of t4_pan_checks.py (journal in the bore, collar seam, pivot, gear on the washer, stop pin in the "
                      "groove, FPC on its anchors, crank pin in the slot, neck on the lands) + the rules listed in checks.py (K3_RULES_*)")


RUN["K3"] = K3


# =====================================================================================================================
# K4  wall thickness
# =====================================================================================================================
K4_LIMIT = {"resin_white": 1.2, "resin_black": 1.2, "resin_clear": 1.2, "resin_grey": 1.2, "petg": 1.6, "pom": 1.2}
K4_MIN_FEATURE = 0.6
K4_TOL = 0.012                     # numeric tolerance of the scan (STL deflection 0.01)
# declared LOCAL features thinner than the wall limit of their material: part regex -> [(box (x0, x1, y0, y1, z0, z1) on |x|, min, text)]
# (walls proper stay at / above the limit; every entry is a web at a hole, a lip, a rim, a blind-hole floor or a snap arm)
_ALL = (0.0, 99.0, -99.0, 99.0, -120.0, 20.0)
K4_DECL = {
    r"T_stred$": [((19.0, 27.0, 26.0, 32.5, -63.0, -20.0), 0.6, "floor 0.6 behind the 4 frame magnet pockets and the pocket wall beside the PAN_ENV trim"),
                  ((31.5, 33.1, -20.0, 20.0, -1.0, 3.0), 1.0, "relief step (0.35 high) for the cap seam lip under the band edge at the crown; the wall above it is >= 2.2")],
    r"T_bok_[LP]$": [((33.4, 34.4, -34.0, 34.0, -79.0, 4.0), 0.7, "root ridge of the seam lip, 0.75 wide x 0.4 high, all along the seam")],
    r"T_dvere$": [((11.0, 21.0, 28.0, 32.5, -12.5, -9.0), 0.8, "2 hook tabs 0.85 thick (8 x 4.8), inset 2.75 .. 3.6")],
    r"T_mriezka$": [(_ALL, 0.6, "grille plug: webs 0.6 between / around the 5 slots 0.8 x 1.6, flange 1.2")],
    r"T_drziak_repro$": [(_ALL, 1.4, "speaker clamp ring 1.6 thick; radial ring width 3.0, 1.45 beside the screw holes / flat (PETG local)")],
    r"T_spodok$": [((0.0, 29.0, -29.0, 29.0, -86.3, -85.1), 1.0, "black skirt disc 1.0 thick (spec deviation D2)")],
    r"T_ram$": [((33.0, 36.0, -6.0, 12.0, -23.0, -7.0), 0.65, "0.7 floor behind the 3 F8 inserts of each shoulder boss (boss 4.0, hole 3.3)"),
                ((36.0, 39.2, -10.0, 15.0, -30.0, -4.0), 0.65, "stop ring 0.7 x 1.2 on its backing flange, key slot rim"),
                ((29.5, 31.5, -2.5, 2.5, -76.5, -71.5), 0.85, "0.9 shoulder behind the F5 insert in the cradle end wall"),
                ((17.0, 26.5, -21.0, 21.0, -78.6, -77.0), 0.65, "0.7 stop collar above the 4 cradle F2 insert seats (seat D3.2 -> through pilot D2.8)"),
                ((33.0, 44.0, -10.0, 16.0, -78.5, -30.0), 0.95, "board standoffs 1.0 high, capacitor clip arms 1.2, column ribs 1.6 run-out"),
                ((0.0, 33.0, -21.5, 19.5, -78.5, -46.0), 1.15, "walls 1.2 .. 1.4 beside insert / pilot holes of the cradle bosses and pan-servo posts (bosses r 2.9 .. 3.0)"),
                ((33.0, 44.0, -10.0, 16.0, -30.0, -3.0), 0.95, "shoulder boss: spigot D10 wall, flange step 1.0, key slot walls")],
    r"T_paluba$": [((0.0, 16.5, -3.0, 16.5, -47.9, -46.5), 0.6, "0.6 of deck under the stop groove (spec 6.2: groove 1.2 in the 1.8 deck, backed by the foam pad)"),
                   ((0.0, 27.0, -19.5, 26.0, -47.9, -42.8), 1.35, "1.4 wall around the F3 clearance holes in the 4 lugs; FPC channel wall 1.6")],
    r"T_prichytka_fpc$": [(_ALL, 1.1, "FPC clamp: 1.13 beside the countersunk clamp screw (clamp 4.6 x 2.2)")],
    r"P_sachta$": [((0.0, 28.5, -1.0, 13.0, -42.0, -40.9), 0.68, "back-sector floor 0.9 (spec 7.1), 0.7 in the 0.2 FPC groove"),
                   ((0.0, 27.0, -27.0, 27.0, -3.6, -1.9), 0.95, "glue groove 0.3 deep in the 1.5 top plate, rim 1.1"),
                   ((0.0, 27.0, -13.0, 13.0, -39.0, -3.0), 1.0, "guide lands 0.7 high on the 1.6 wall (reading from a land flank)")],
    r"P_koleso$": [((0.0, 17.0, 5.0, 17.0, -42.7, -41.9), 0.6, "FPC retaining lip 0.6 x 0.8 (spec 7.2: 0.4; thickened by the integrator)"),
                   ((0.0, 11.0, -2.0, 2.0, -45.8, -44.9), 0.6, "floor 0.6 under the two blind dowel holes")],
    r"P_drziak_serva$": [(_ALL, 0.8, "ledge 0.8 under the servo end (spec 7.3), lands 0.85 / 1.05 above the F10 slots, webs 1.25 / 1.3 (module list)")],
    r"P_kluka$": [(_ALL, 1.17, "hub wall 1.2 around the 21T serration")],
    r"L_pata$": [(_ALL, 0.8, "webs 0.81 under the ear dowel hole, 0.85 around the D1.3 pilot, skins 1.05 / 1.15 at the tongue key slot")],
    r"L_jazyk$": [(_ALL, 1.05, "key prongs 1.5, recess floor, countersink rim 1.1")],
    r"L_ucho$": [(_ALL, 0.77, "webs 0.78 at the D1.5 dowel hole (flange 3.1 high), slot closing web 0.8, 0.85 at the M2 hole")],
    r"T_svetlovod$": [(_ALL, 1.19, "flange 1.2")],
    r"T_klb_[LP]$": [(_ALL, 1.2, "walls 1.25 between counterbores / pockets (spec 13)")],
}


def _k4_decl(name, at, t):
    for pat, lst in K4_DECL.items():
        if re.match(pat, name):
            for bx, tmin, text in lst:
                if (bx[0] <= abs(at[0]) <= bx[1] and bx[2] <= at[1] <= bx[3] and bx[4] <= at[2] <= bx[5] and t >= tmin - K4_TOL):
                    return text
    return None


def K4():
    d = bl_section("K4")["parts"]
    om = module_check("obal"); rm = module_check("ram"); pm = module_check("pan")
    if om is None or rm is None or pm is None:
        miss = [k for k, v in (("obal", om), ("ram", rm), ("pan", pm)) if v is None]
        return res("NOT RUN", f"module wall checks without a valid result for the STL files on disk: {miss} {[_MOD_NOTE.get(k) for k in miss]}")
    fail, rows, decl_used = [], [], {}
    for n, v in d.items():
        lim = K4_LIMIT[v["mat"]]
        und, below = [], 0
        for c in v.get("thin_cells", []):
            if c["t"] >= lim - K4_TOL:
                continue
            below += 1
            txt = _k4_decl(n, c["at"], c["t"])
            if txt is None or c["t"] < K4_MIN_FEATURE - K4_TOL:
                und.append(c)
            else:
                decl_used.setdefault(n, {}).setdefault(txt, [9.0, 0])
                decl_used[n][txt][0] = min(decl_used[n][txt][0], c["t"]); decl_used[n][txt][1] += 1
        rows.append(dict(part=n, mat=v["mat"], limit=lim, min=v.get("min"), p01=v.get("p01"), median=v.get("median"), samples=v.get("opposing"),
                         cells_below_limit=below, undeclared=und[:12], hist=v.get("hist")))
        if und:
            fail.append(f"{n}: {len(und)} thin spots below {lim} without a declaration (min {min(c['t'] for c in und)} at {min(und, key=lambda c: c['t'])['at']})")
    # shells: through-wall rays of the OBAL module (exterior -> inner face)
    m2 = om.get("M2_wall", {})
    if not m2.get("ok"):
        fail.append("OBAL M2 (through-wall rays of the white shells) not ok")
    if m2.get("n_below_2p0_not_declared", 1) or m2.get("n_below_1p2", 1):
        fail.append(f"white shells: {m2.get('n_below_2p0_not_declared')} rays below 2.0 outside declared spots, {m2.get('n_below_1p2')} below 1.2")
    # designed walls of RAM, wall scan of PAN
    rw = rm.get("E", {}).get("designed_walls", [])
    if not rm.get("verdicts", {}).get("E_designed_walls", {}).get("ok"):
        fail.append("RAM E (designed walls) not ok")
    if pm.get("checks", {}).get("G_walls", {}).get("status") != "PASS":
        fail.append("PAN G (walls) not PASS")
    n_decl = sum(len(v) for v in decl_used.values())
    return res("PASS" if not fail else "FAIL",
               f"white shells (T_stred, T_bok_L/P, T_dvere), {m2.get('points')} through-wall rays: median {m2.get('median')}, 1st percentile {m2.get('p01')}, "
               f"min {m2.get('min')} (declared local spots >= 1.2: {list((m2.get('declared_thin') or {}).keys())}), {m2.get('n_below_2p0_not_declared')} below 2.0 "
               f"undeclared; all {len(rows)} printed parts, opposing-face scan: {sum(r['cells_below_limit'] for r in rows)} thin spots below the material "
               f"limit (resin 1.2, PETG 1.6, POM 1.2), all inside {n_decl} declared local features (webs at holes, lips, rims, blind-hole floors, "
               f"snap arms; each >= 0.6), {sum(len(r['undeclared']) for r in rows)} undeclared; RAM designed walls {sum(1 for w in rw if w['ok'])}/{len(rw)}; "
               f"smallest reading {min(r['min'] for r in rows if r['min'] is not None)}",
               failures=fail, parts=rows,
               declared_local_features={n: [dict(feature=t, min_measured=v[0], cells=v[1]) for t, v in dd.items()] for n, dd in decl_used.items()},
               shells_through_wall=dict(points=m2.get("points"), min=m2.get("min"), p001=m2.get("p001"), p01=m2.get("p01"), median=m2.get("median"),
                                        declared_thin=m2.get("declared_thin"), top_rim=m2.get("top_rim"), socket_rim_wedge=m2.get("socket_rim_wedge")),
               ram_designed_walls=rw, pan_walls=[dict(part=q["part"], min=q["min"], limit=q["limit"], declared=q["declared_thin"])
                                                 for q in pm["checks"]["G_walls"]["parts"]],
               limits=dict(shell_nominal=2.0, local=1.2, chassis_petg=1.6, min_feature=K4_MIN_FEATURE),
               method="(1) white shells: rays from the analytic exterior through the wall (obal_work/mesh_checks.py M2); (2) every printed part: "
                      "opposing-face thickness scan in Blender (checks_bl.py K4), each reading below the material limit must lie in a declared "
                      "local feature (K4_DECL in checks.py: box, minimum, reason) and none may be below 0.6; (3) designed walls measured on the "
                      "solids by the RAM and PAN module checks")


RUN["K4"] = K4


# =====================================================================================================================
# K5  bought-part seats with tolerance ranges, centre distances
# =====================================================================================================================
K5_PLAY = [   # (part, axis keys summed, minimum total free play, why)   - what the seat must leave for the part's tolerance
    ("servo_J1", ("-y", "+y"), 0.3, "STS3215 width 24.7 +-0.3: cradle +0.2 per side"),
    ("servo_J1", ("-x",), 0.3, "STS3215 slides +-0.3 in x for the centre distance (set screw F5 side)"),
    ("servo_J1", ("+x",), 0.3, "STS3215 slides +-0.3 in x (foam pad 1.0 + bumper side)"),
    ("servo_J1", ("+z",), 0.3, "STS3215 height 35.0 +-0.3 taken by the 0.5 foam under the deck"),
    ("servo_pan", ("-x", "+x"), 0.3, "STS3032 length 23.5 +-0.3 between the posts"),
    ("servo_pan", ("-y", "+y"), 0.3, "STS3032 width 12.5 +-0.3 / slop of the D2.2 tab holes"),
    ("servo_zdvih", ("-y", "+y"), 0.15, "MG90S width 12.2: 0.20 to the wedge lip; a wider case (to +0.3) rides up the 45 deg wedge (declared compliance)"),
    ("servo_zdvih", ("+z",), 0.2, "MG90S length 22.8: 0.25 .. 0.30 to the tab post; the tab seat is slotted +-1.0 in x"),
    ("reproduktor", ("-x", "+x"), 0.3, "speaker D28 +-0.3 between the 3 boss scallops (seat D28.3)"),
    ("lozisko_6805", ("-x", "+x"), 0.0, "6805 outer ring D37 in the seat D37.00 +0.05 / 0 (CA)"),
    ("DPS_led", ("-x", "+x"), 0.2, "LED strip 30.0 +-0.2 in the rebate 30.3"),
    ("kondenzator", ("-z", "+z"), 0.3, "capacitor length 11.5 .. 13 in the 13.6 clip window"),
]


def K5():
    rm = module_check("ram"); pm = module_check("pan"); om = module_check("obal")
    miss = [k for k, v in (("ram", rm), ("pan", pm), ("obal", om)) if v is None]
    if miss:
        return res("NOT RUN", f"module seat checks without a valid result for the STL files on disk: {miss} {[_MOD_NOTE.get(k) for k in miss]}")
    play = bl_section("K5")["parts"]
    fail = []
    # ---- centre distances measured on the STL files (axis = centroid of the gear / pin / bearing vertices)
    def axis_xy(n):
        V = TM.stl(n).reshape(-1, 3)
        return (V[:, 0].min() + V[:, 0].max()) / 2, (V[:, 1].min() + V[:, 1].max()) / 2

    def rmax(n, c):
        V = TM.stl(n).reshape(-1, 3)
        return float(np.hypot(V[:, 0] - c[0], V[:, 1] - c[1]).max())
    cj, cs, cb = axis_xy("pastorok_J1"), axis_xy("Z_koleso_J1"), axis_xy("lozisko_6805")
    cp, cpin = axis_xy("pastorok_pan"), axis_xy("cap_pan")
    CJ = float(np.hypot(cj[0] - cb[0], cj[1] - cb[1])); CP = float(np.hypot(cp[0] - cpin[0], cp[1] - cpin[1]))
    gears = dict(
        C_J1=dict(measured=rd(CJ, 4), nominal=18.0, allowed=[17.98, 18.02], adjust="+-0.3 by the set screw F5", sun_on_axis=rd(float(np.hypot(*cs)), 4),
                  tip_r_pinion=rd(rmax("pastorok_J1", cj)), tip_r_sun=rd(rmax("Z_koleso_J1", cs)), ok=bool(17.98 <= CJ <= 18.02 and np.hypot(*cs) < 0.02)),
        C_pan=dict(measured=rd(CP, 4), nominal=21.6, allowed=[21.6 - 1e-3, 21.65], tip_r_pinion=rd(rmax("pastorok_pan", cp)),
                   tip_r_gear=15.2, ok=bool(21.6 - 1e-3 <= CP <= 21.65)))
    for k, g in gears.items():
        if not g["ok"]:
            fail.append(f"{k}: {g['measured']} outside {g['allowed']}")
    # ---- bore / journal / bearing fits measured on the STL files
    def r_of(n, z0, z1, rlo, rhi, c=(0.0, 0.0)):
        V = TM.stl(n).reshape(-1, 3)
        r = np.hypot(V[:, 0] - c[0], V[:, 1] - c[1])
        m = (V[:, 2] > z0) & (V[:, 2] < z1) & (r > rlo) & (r < rhi)
        return (float(r[m].min()), float(r[m].max())) if m.any() else (None, None)
    bore = r_of("T_stred", -10.05, 3.5, 27.0, 28.6)[0]              # cylinders only have vertices on their end rings: inclusive z ranges
    jour = r_of("P_sachta", -10.05, -4.45, 27.8, 29.0)[1]
    tape = r_of("ptfe_pas_capu", -10.05, -4.95, 27.5, 29.0)[1]
    ring = r_of("golier_prstenec", -2.05, 3.0, 27.5, 29.0)[1]
    seat = r_of("T_spodok", -97.65, -90.95, 17.5, 19.0)[0]
    brg_o = r_of("lozisko_6805", -98.05, -90.95, 17.5, 19.0)[1]
    brg_i = r_of("lozisko_6805", -98.05, -90.95, 11.0, 13.5)[0]
    post = r_of("Z_naboj_test", -97.95, -91.5, 11.0, 13.4)[1]
    if any(v is None for v in (bore, jour, tape, ring, seat, brg_o, brg_i, post)):
        raise RuntimeError(f"fit radii could not be measured on the STL: {dict(bore=bore, jour=jour, tape=tape, ring=ring, seat=seat, brg_o=brg_o, brg_i=brg_i, post=post)}")
    fits = [
        dict(fit="pan journal + PTFE band in the bore of T_stred (radial running clearance)", measured=rd(bore - tape), allowed=[0.10, 0.20], bore_r=rd(bore), shaft_r=rd(tape)),
        dict(fit="pan journal bare in the bore (if the print is tight: no tape)", measured=rd(bore - jour), allowed=[0.20, 0.35], bore_r=rd(bore), shaft_r=rd(jour)),
        dict(fit="collar ring in the bore (glue seam)", measured=rd(bore - ring), allowed=[0.05, 0.15], bore_r=rd(bore), shaft_r=rd(ring)),
        dict(fit="6805 outer ring in the seat D37.00 +0.05 / 0 (radial)", measured=rd(seat - brg_o), allowed=[-0.005, 0.03], bore_r=rd(seat), shaft_r=rd(brg_o)),
        dict(fit="6805 inner ring on the dummy post D24.96 (radial)", measured=rd(brg_i - post), allowed=[0.005, 0.035], bore_r=rd(brg_i), shaft_r=rd(post)),
    ]
    for f in fits:
        f["ok"] = bool(f["allowed"][0] - 1e-3 <= f["measured"] <= f["allowed"][1] + 1e-3)
        if not f["ok"]:
            fail.append(f"{f['fit']}: {f['measured']} outside {f['allowed']}")
    # ---- free play of the bought parts in their seats
    prow = []
    for part, keys, need, why in K5_PLAY:
        vals = [play[part]["play"][k]["free"] for k in keys]
        tot = None if any(v is None for v in vals) else float(sum(vals))
        ok = tot is None or tot >= need - 0.01
        prow.append(dict(part=part, what=play[part]["what"], axes=list(keys), free_play=None if tot is None else rd(tot), open=tot is None, required=need, why=why, ok=bool(ok)))
        if not ok:
            fail.append(f"seat of {part} {keys}: free play {tot:.3f} < {need} ({why})")
    # ---- seat tables measured on the solids by the module checks
    rd_ = rm.get("D", []); pf = pm["checks"]["F_seats"]["seats"]; os_ = om["O4_seats"]["seats"]
    bad_mod = [e["name"] for e in rd_ if not e["ok"]] + [e["seat"] for e in pf if not e["ok"]] + [e["feature"] for e in os_ if not e["ok"]]
    if bad_mod:
        fail.append(f"module seat tables: not ok {bad_mod}")
    return res("PASS" if not fail else "FAIL",
               f"centre distances on the STL: J1 C {gears['C_J1']['measured']} (18.00, adjustable +-0.3), pan C {gears['C_pan']['measured']} (21.600 +0.05 / 0); "
               f"journal in the bore {fits[0]['measured']} with tape / {fits[1]['measured']} bare; 6805 seat {fits[3]['measured']}, post {fits[4]['measured']}; "
               f"free play of the seats: {sum(1 for r in prow if r['ok'])}/{len(prow)} rows accept the part tolerance (STS3215 +-0.3: y {prow[0]['free_play']}, "
               f"x {prow[1]['free_play']} / {prow[2]['free_play']}, z {prow[3]['free_play']}; STS3032 x {prow[4]['free_play']}; MG90S y {prow[6]['free_play']} + wedge, "
               f"z {prow[7]['free_play']}); seat tables measured on the solids by the module checks: RAM {sum(1 for e in rd_ if e['ok'])}/{len(rd_)}, "
               f"PAN {sum(1 for e in pf if e['ok'])}/{len(pf)}, OBAL {sum(1 for e in os_ if e['ok'])}/{len(os_)}",
               failures=fail, centre_distances=gears, fits_on_stl=fits, seat_free_play=prow, all_free_play=play,
               module_seat_tables=dict(ram=rd_, pan=pf, obal=os_),
               notes=["STS3215 spline length (2.2 usable) and STS3032 tab height / hole pattern are listing values - measure the purchased servos (seats slotted +-0.3)",
                      "MG90S: the seat takes +0.2 in width flat; up to +0.3 the case rides up the 45 deg wedge lip (shaft 0.1 higher)"])


RUN["K5"] = K5


# =====================================================================================================================
# K6  crank kinematics, pan stop, J1 stop
# =====================================================================================================================
def K6():
    import t4_pan as MP
    fail = []
    TRI = {n: TM.stl(n) for n in ("cap_kluky", "servo_zdvih", "L_ucho", "P_kluka", "kolik_dorazu", "T_paluba", "T_spodok", "Z_naboj_test", "P_koleso", "pastorok_pan")}
    V = TRI["cap_kluky"].reshape(-1, 3)
    pin = np.array([(V[:, 1].min() + V[:, 1].max()) / 2, (V[:, 2].min() + V[:, 2].max()) / 2])
    S = TRI["servo_zdvih"].reshape(-1, 3); spl = S[S[:, 0] < S[:, 0].min() + 2.5]                 # spline end of the MG90S
    ax = np.array([(spl[:, 1].min() + spl[:, 1].max()) / 2, (spl[:, 2].min() + spl[:, 2].max()) / 2])
    R = float(np.hypot(*(pin - ax)))
    stroke = 2 * R
    dc = dict(pin_rest_yz=[rd(v) for v in pin], shaft_axis_yz=[rd(v) for v in ax], dy_at_bottom_dead_centre=rd(pin[0] - ax[0], 4))
    if abs(stroke - 20.0) > 0.05:
        fail.append(f"stroke {stroke:.3f} != 20.0")
    if abs(pin[0] - ax[0]) > 0.02 or pin[1] > ax[1]:
        fail.append("the crank pin is not straight below the shaft at rest (no dead centre at lift 0)")
    # pin in the ear slot over the stroke (meshes): crank turned by theta, ear lifted by R (1 - cos theta)
    def crank_x(T, theta):
        a = math.radians(-theta); c, s = math.cos(a), math.sin(a)
        Q = T.copy(); y, z = T[..., 1] - ax[0], T[..., 2] - ax[1]
        Q[..., 1] = ax[0] + c * y - s * z; Q[..., 2] = ax[1] + s * y + c * z
        return Q
    tab, gmin, gmax, amin = [], 9.0, 0.0, 9.0
    for th in range(0, 181, 5):
        lift = R * (1 - math.cos(math.radians(th)))
        ear = TRI["L_ucho"].copy(); ear[..., 2] += lift
        me = TM.Multi({"ear": ear}, 0.15)
        dpin = me.min_by_part(TM.sample(crank_x(TRI["cap_kluky"], th), 0.15)[0], 1.5).get("ear", (9.0, None))[0]
        darm = me.min_by_part(TM.sample(crank_x(TRI["P_kluka"], th), 0.2)[0], 1.5).get("ear", (9.0, None))[0]
        # where the pin centre sits in the slot (y of the pin; the slot is horizontal)
        py = ax[0] - R * math.sin(math.radians(th))
        tab.append(dict(theta=th, lift=rd(lift), pin_to_ear=rd(dpin), crank_arm_to_ear=rd(darm), pin_y=rd(py)))
        gmin, gmax, amin = min(gmin, dpin), max(gmax, dpin), min(amin, darm)
    if gmin < 0.05:
        fail.append(f"crank pin <-> ear slot: {gmin:.3f} (binding)")
    if amin < 0.3:
        fail.append(f"crank arm <-> ear: {amin:.3f}")
    # lift law: lift(theta) = R (1 - cos theta): slope 0 at both ends = dead centres; top dead centre geometry
    top = dict(pin_top_yz=[rd(ax[0]), rd(ax[1] + R)], dlift_dtheta_at_0_and_180=[0.0, rd(R * math.sin(math.pi), 6)])
    # ---- pan hard stops: stop pin in the deck groove
    mp = TM.Multi({"deck": TRI["T_paluba"]}, 0.2)
    Sp = TM.sample(TRI["kolik_dorazu"], 0.12)[0]
    stops = {}
    for sgn in (1, -1):
        ang, dprev = None, None
        for a in np.arange(80.0, 96.0, 0.05):
            dd = mp.min_by_part(TM.rotz(Sp, sgn * a), 1.0).get("deck", (9.0, None))[0]
            if dd < 0.01:
                ang = float(a); break
        stops["+" if sgn > 0 else "-"] = ang
    free = min(mp.min_by_part(TM.rotz(Sp, float(a)), 1.0).get("deck", (9.0, None))[0] for a in np.arange(-85.0, 85.1, 2.5))
    for k, a in stops.items():
        if a is None or not (89.0 <= a <= 91.5):
            fail.append(f"pan hard stop {k}: {a} (expected 90 +- 1)")
    # nothing but the stop pin may touch at the hard stops: stage + lift parts against the static torso at +-stop
    hs_rows, hs_min = [], None
    if all(a is not None for a in stops.values()):
        M = pan_model()
        st = M["scan"]([stops["+"] - 0.05, -(stops["-"] - 0.05)], [0.0, 10.0, 20.0], fpc_loop=False)
        for (a, b, c), (dd, pan, lf, at) in sorted(st.items(), key=lambda kv: kv[1][0]):
            decl_ = M["RULES_E"][c][4] if c >= 0 else None
            lim_ = 0.0 if c >= 0 else 0.1
            if dd < 1.0:
                hs_rows.append(dict(moving=a, static=b, min_mm=rd(dd), pan=rd(pan, 2), lift=lf, at=at, declared=decl_, ok=bool(dd >= lim_ - 1e-3)))
            if c < 0:
                hs_min = dd if hs_min is None else min(hs_min, dd)
                if dd < lim_:
                    fail.append(f"hard stop pose pan {pan:.2f}: {a} <-> {b} {dd:.3f} (something else than the stop pin touches)")
    # teeth still in mesh at the hard stops
    G = C.PAN["GEAR"]; paz = math.degrees(math.atan2(C.PAN_AX[1], C.PAN_AX[0])) % 360.0
    t0, t1 = G["teeth_az"]
    margin = [rd(min((paz - s_ * 90.0) - t0, t1 - (paz - s_ * 90.0))) for s_ in (1, -1)]
    if min(margin) < 5.0:
        fail.append(f"pan gear teeth end {min(margin)} deg from the pinion at a hard stop")
    # ---- J1 hard stops: stop lug of T_spodok against the stop block of the dummy
    mz = TM.Multi({"stand": TRI["Z_naboj_test"]}, 0.3)
    Tl = TRI["T_spodok"]; Tl = Tl[Tl[:, :, 2].max(1) < -97.9]                                       # the lug below the foot ring
    Sl = TM.sample(Tl, 0.15)[0]; Sl = Sl[Sl[:, 2] < -98.05]
    j1 = {}
    for sgn in (1, -1):
        ang = None
        for a in np.arange(148.0, 162.0, 0.05):
            dd = mz.min_by_part(TM.rotz(Sl, sgn * a), 1.0).get("stand", (9.0, None))[0]
            if dd < 0.01:
                ang = float(a); break
        j1["+" if sgn > 0 else "-"] = ang
    for k, a in j1.items():
        if a is None or not (153.0 <= a <= 157.0):
            fail.append(f"J1 hard stop {k}: {a} (expected 155 +- 2)")
    torque = dict(mass_kg_assumed=0.17, peak_Nm=rd(0.17 * 9.81 * R / 1000.0, 4), MG90S_stall_Nm=0.18, factor=rd(0.18 / (0.17 * 9.81 * R / 1000.0), 1),
                  note="peak at mid stroke (theta 90); 0 at the dead centres (self-holding)")
    fw = (pm_ := json.load(open(os.path.join(HERE, "parts_pan.json")))).get("firmware", {})
    return res("PASS" if not fail else "FAIL",
               f"crank radius {R:.3f} measured on the STL (pin axis to MG90S spline axis) -> stroke {stroke:.3f} (20.0); pin straight below the shaft at "
               f"rest (dy {pin[0] - ax[0]:.4f}) and above it at 180 deg = dead centres at lift 0 and 20; pin in the ear slot over 0..180 deg: "
               f"{gmin:.3f} .. {gmax:.3f} per side (37 poses), crank arm <-> ear {amin:.3f}; pan hard stops (stop pin D2 on the groove ends of "
               f"T_paluba) at +{stops['+']:.2f} / -{stops['-']:.2f} deg, pin free ({free:.3f}) over the firmware range +-85; at the stops nothing else touches "
               f"(smallest undeclared clearance {rd(hs_min)}); gear teeth {min(margin)} deg beyond the pinion at the stops; J1 hard stops (lug on the stop block) at +{j1['+']} / -{j1['-']} deg (firmware +-150)",
               failures=fail, crank=dict(radius=rd(R, 4), stroke=rd(stroke, 4), **dc, **top, law="lift = R (1 - cos theta), theta 0 .. 180 deg",
                                         pin_slot_table=tab, pin_to_slot_min=rd(gmin), pin_to_slot_max=rd(gmax), crank_arm_to_ear_min=rd(amin)),
               pan_stop=dict(hard_stop_deg=stops, firmware_deg=[-85.0, 85.0], stop_pin_clearance_in_firmware_range=rd(free), teeth_margin_deg_at_stops=margin,
                             smallest_undeclared_clearance_at_the_hard_stops=rd(hs_min), pairs_below_1p0_at_the_hard_stops=hs_rows),
               J1_stop=dict(hard_stop_deg=j1, firmware_deg=[-150.0, 150.0]), lift_torque=torque, firmware=fw,
               notes=["at the exact dead centres the pin is 0.10 from the closed back end of the slot: firmware keeps the crank at 3 .. 177 deg (stroke 19.97)"],
               method="measured on the exported STL files: crank radius from the vertex extents of cap_kluky and of the MG90S spline end; pin / crank "
                      "against the lifted ear by exact point-to-triangle distances at 37 crank angles; hard stops = first angle (0.05 deg steps) at "
                      "which the rotated stop pin / stop lug touches the groove end / stop block (< 0.01 mm)")


RUN["K6"] = K6


# =====================================================================================================================
# K7  assembly
# =====================================================================================================================
def K7():
    d = bl_section("K7")
    fail = list(d["problems"])
    if d["parts_never_mounted"]:
        fail.append(f"parts that no assembly step mounts: {d['parts_never_mounted']}")
    steps, recess, n_sc, n_hw, n_sweep = [], [], 0, 0, 0
    for s in d["steps"]:
        row = dict(id=s["id"], bench=s["bench"], text=s["text"], pan=s["pan"], move=s["move"], parts_present=s["n_ctx"])
        if "legs" in s:
            n_sweep += 1
            row.update(withdrawal_legs=s["legs"], frame=s["frame"], collisions=s["collisions"], declared_fits=[f"{c['moving']} x {c['static']}" for c in s["declared_fits_met"]])
            for k in ("not_swept", "snap_fit", "flex_sweeps"):
                if k in s:
                    row[k] = s[k]
        if "swing" in s:
            n_sweep += 1
            row["swing"] = s["swing"]
        if s["hardware"]:
            row["hardware"] = [dict(part=h["part"], dir=h["dir"], open=h["open"], blocked_by=h["blocked_by"]) for h in s["hardware"]]
            n_hw += len(s["hardware"])
        if s["screws"]:
            row["screws"] = [dict(screw=x["screw"], tool_dir=x["tool_dir"], free_D4p5=x["free_D4p5"], own_recess_only=x["own_recess_only"],
                                  free_ring_radius=x["free_ring_radius"], ok=x["ok"], blocked_by=x["blocked_by"]) for x in s["screws"]]
            n_sc += len(s["screws"])
            recess += [x["screw"] for x in s["screws"] if x["own_recess_only"]]
        steps.append(row)
    mod = {}
    for name, key in (("ram", None), ("pan", None), ("obal", None)):
        m = module_check(name)
        if m is None:
            mod[name] = "no valid module result (" + _MOD_NOTE.get(name, "") + ")"
            continue
        if name == "ram":
            ok = m["verdicts"]["F_tool_channels"]["ok"] and m["verdicts"]["C2_T_stred_can_be_lowered"]["ok"]
            mod[name] = dict(F_tool_channels=m["verdicts"]["F_tool_channels"], C2_T_stred_can_be_lowered=m["verdicts"]["C2_T_stred_can_be_lowered"])
        elif name == "pan":
            h = m["checks"]["H_assembly"]; ok = h["status"] == "PASS"
            mod[name] = dict(H_assembly=h["status"], H2_tool_channels=h.get("H2_tool_channels", {}).get("status"),
                             H3=h.get("H3_bracket_unit_through_door", {}).get("status"))
        else:
            ok = m["X2_lowering_vs_ram_meshes"]["ok"] and m["X3_cap_slide_vs_meshes"]["ok"]
            mod[name] = dict(X2_lowering_min_plan_gap=m["X2_lowering_vs_ram_meshes"]["min_plan_gap"], X3_cap_slide_ok=m["X3_cap_slide_vs_meshes"]["ok"])
        if not ok:
            fail.append(f"module assembly check of {name} not ok")
    main = [s for s in steps if not s["bench"]]
    return res("PASS" if not fail else "FAIL",
               f"{len(steps)} steps ({len(steps) - len(main)} bench sub-assemblies, {len(main)} torso steps): {n_sweep} straight-line / swing paths swept "
               f"against the parts present at that step - {sum(len(s.get('collisions', [])) for s in steps)} collisions; {n_sc} screws with a D4.5 tool "
               f"channel ({len(recess)} of them limited only by their own counterbore: {recess}); {n_hw} inserts / magnets / pins with an open mouth; "
               f"every part of parts.json is mounted by a step; problems: {len(fail)}",
               failures=fail, steps=steps, screws_in_own_recess=recess,
               rule_for_recessed_screws="the D4.5 channel is required from the mouth of the screw's own counterbore outward; inside it the driver is "
                                        "the hex key / bit of the screw (F8: M2 socket head in a D4.2 x 13.7 counterbore of T_klb -> 1.5 mm hex key)",
               not_path_tested=d["parts_arriving_without_a_path_test"], flexible_parts=d["flexible"], module_checks=mod,
               findings=["pan pinion: its tip circle (r 29.6 from the torso axis at its seat) is larger than the collar bore r 28.35 -> it goes through the "
                         "bore 2 mm off its axis and is moved onto the shaft below the collar tube (3-leg path, collision-free)",
                         "ear dowel D1.5: pressed into the foot through the door AFTER the neck is in the well (2.0 proud it cannot pass the well wall)",
                         "door: no straight path - it pivots about the centre of its top edge; hooks engage at about 35 deg, magnets close it",
                         "STS3032 bus plug and the MG90S lead are plugged / dressed after the servo is seated (flexible, reserved space)",
                         "FPC, servo leads, foam pads, disc springs: not path-tested (flexible or loose)"],
               method=d["method"])


RUN["K7"] = K7


# =====================================================================================================================
# K10  printability
# =====================================================================================================================
K10_RESIN_VOLUME = (218.0, 123.0, 220.0)
K10_OVERHANG_DEG = 50.0
K10_FDM = {   # FDM part: (print orientation = B-frame direction pointing AWAY from the bed, supports declared or None)
    "T_ram": ("+z", "tree supports under the two shoulder bosses / flanges (horizontal cylinders r 11.6 .. 12.8), under the pan-servo post shelf "
                    "and window top, under the bridges and deck-boss corbels; all reachable from outside"),
    "T_paluba": ("+z", None),
    "T_prichytka_fpc": ("+z", None),
    "Z_naboj_test": ("+z", "bench stand standing on its 4 feet: the whole plate underside (93 cm2, 4.5 above the bed) is printed on supports - or "
                           "print the plate without feet and stick 4 bumpers on; a jig, not a robot part"),
    "P_drziak_serva": ("+z", "standing on the ledge: supports under the tab post and under the lug (about 0.9 cm2), reachable from outside"),
    "L_pata": ("-z", None),            # underside (FPC pocket, channel, countersinks) up: no overhang
    "L_jazyk": ("-x", None),           # standing on its outer end face
    "T_drziak_repro": ("+y", None),
}
K10_VENTS = [   # (part, what, origin, direction, length): the line must NOT meet the part = open vent / drain path
    ("T_spodok", "drain / vent hole D3 (+x)", (33.0, -8.0, -78.0), (0, 0, -1), 12.0),
    ("T_spodok", "drain / vent hole D3 (-x)", (-33.0, -8.0, -78.0), (0, 0, -1), 12.0),
    ("T_spodok", "pinion passage through floor, skirt and plinth", (-18.0, 0.0, -78.0), (0, 0, -1), 25.0),
    ("T_stred", "collar bore (open top of the arch)", (0.0, 0.0, 12.0), (0, 0, -1), 30.0),
    ("T_stred", "vent hole D1.6 through the collar tube (+x)", (27.9, 0.0, 0.4), (1, 0, 0), 3.3),
    ("T_stred", "vent hole D1.6 through the collar tube (-x)", (-27.9, 0.0, 0.4), (-1, 0, 0), 3.3),
    ("T_bok_L", "socket bore (open side of the cap)", (36.0, 3.0, -17.0), (1, 0, 0), 30.0),
    ("T_bok_P", "socket bore (open side of the cap)", (-36.0, 3.0, -17.0), (-1, 0, 0), 30.0),
    ("P_sachta", "well open at the bottom outside the back-sector floor", (-15.0, -5.0, 5.0), (0, 0, -1), 60.0),
    ("T_klb_L", "bush bore through the joint", (36.0, 3.0, -17.0), (1, 0, 0), 30.0),
]
K10_RESIN_ORIENT = {
    "T_stred": "top down, tilted 20 deg about X, supports only inside (spec 4.7)", "T_bok_L": "open side up, tilted 25 deg", "T_bok_P": "open side up, tilted 25 deg",
    "T_dvere": "inner face to the plate", "T_spodok": "underside up, tilted 15 deg", "T_klb_L": "arm interface face up", "T_klb_P": "arm interface face up",
    "T_svetlovod": "flange to the plate", "T_mriezka": "flange to the plate", "T_drziak_led": "open side up", "P_sachta": "stage top to the plate (well axis vertical)",
    "P_koleso": "flat, gear face to the plate", "P_kluka": "flat",
}


def K10():
    k4 = bl_section("K4")["parts"]
    AXV = {"+x": (1, 0, 0), "-x": (-1, 0, 0), "+y": (0, 1, 0), "-y": (0, -1, 0), "+z": (0, 0, 1), "-z": (0, 0, -1)}
    cosl = -math.cos(math.radians(90.0 - K10_OVERHANG_DEG))           # normal more than 50 deg below the horizontal plane's edge
    fail, rows = [], []
    vol_sorted = sorted(K10_RESIN_VOLUME)
    for r in PARTS:
        if not r["printed"]:
            continue
        n = r["name"]; T = TM.stl(n)
        st = TM.mesh_stats(T)
        b = st["bbox"]; dims = [round(b[1] - b[0], 2), round(b[3] - b[2], 2), round(b[5] - b[4], 2)]
        row = dict(part=n, mat=r["mat"], size=dims, components=st["components"], min_thickness=k4.get(n, {}).get("min"),
                   sharpest_wedge_reading=k4.get(n, {}).get("wedge_min"))
        resin = r["mat"].startswith("resin")
        if resin or r["mat"] == "pom":
            row["process"] = "MSLA resin" if resin else "POM turned / milled (or tough resin)"
            row["fits_build_volume"] = bool(all(a <= v for a, v in zip(sorted(dims), vol_sorted)))
            row["orientation"] = K10_RESIN_ORIENT.get(n, "any")
            if not row["fits_build_volume"]:
                fail.append(f"{n}: {dims} does not fit {K10_RESIN_VOLUME}")
        else:
            nrm, area = TM.tri_normals(T)
            ov = {}
            for key, up in AXV.items():
                up = np.array(up, float)
                h = T.reshape(-1, 3) @ up
                bed = h.min()
                on_bed = (T @ up).max(1) < bed + 0.05
                m = (nrm @ up < cosl) & ~on_bed
                flat = (nrm @ up < -0.985) & ~on_bed
                ov[key] = dict(overhang_mm2=round(float(area[m].sum()), 1), of_it_horizontal_ceilings=round(float(area[flat].sum()), 1),
                               bed_contact_mm2=round(float(area[on_bed & (nrm @ up < -0.985)].sum()), 1), height=round(float(h.max() - bed), 1))
            key, sup = K10_FDM.get(n, (None, None))
            best = min(ov, key=lambda k: ov[k]["overhang_mm2"])
            row.update(process="FDM PETG", orientation_up=key, overhang_mm2=ov[key]["overhang_mm2"] if key else None,
                       horizontal_ceilings_mm2=ov[key]["of_it_horizontal_ceilings"] if key else None, bed_contact_mm2=ov[key]["bed_contact_mm2"] if key else None,
                       supports_declared=sup, least_overhang_orientation=best, overhang_by_orientation={k: v["overhang_mm2"] for k, v in ov.items()})
            if key is None:
                fail.append(f"{n}: FDM part without a declared print orientation")
            elif ov[key]["overhang_mm2"] > 40.0 and sup is None:
                fail.append(f"{n}: {ov[key]['overhang_mm2']} mm2 of overhang > {K10_OVERHANG_DEG} deg in orientation {key} and no supports declared")
        if st["components"] != 1:
            fail.append(f"{n}: {st['components']} surface components (closed inner void = trapped resin / unprintable)")
        mt = row["min_thickness"]
        if mt is None:
            fail.append(f"{n}: no thickness scan")
        elif mt < K4_MIN_FEATURE - K4_TOL:
            fail.append(f"{n}: feature {mt} mm thick (< {K4_MIN_FEATURE})")
        rows.append(row)
    vents = []
    for part, what, o, dvec, L in K10_VENTS:
        t = TM.ray_tris(TM.stl(part), o, dvec, L)
        vents.append(dict(part=part, what=what, open=t is None, blocked_at=None if t is None else rd(t)))
        if t is not None:
            fail.append(f"{part}: {what} is not open (hit after {t:.2f} mm)")
    fdm = [r_ for r_ in rows if r_["process"] == "FDM PETG"]
    return res("PASS" if not fail else "FAIL",
               f"{len(rows)} printed parts: all resin / POM parts fit {K10_RESIN_VOLUME} (largest {max((r_ for r_ in rows if r_['process'] != 'FDM PETG'), key=lambda q: max(q['size']))['part']}); "
               f"one closed surface each (no trapped void); smallest opposing-face thickness {min(r_['min_thickness'] for r_ in rows)} (rule 0.6); "
               f"{sum(1 for v in vents if v['open'])}/{len(vents)} vent / drain paths open; FDM: {len(fdm)} parts, overhang > {K10_OVERHANG_DEG:.0f} deg in the declared "
               f"orientation: " + ", ".join(f"{r_['part']} {r_['overhang_mm2']} mm2" + (" (supports declared)" if r_["supports_declared"] else "") for r_ in fdm)
               + f"; failures: {len(fail)}",
               failures=fail, parts=rows, vents=vents, resin_build_volume=K10_RESIN_VOLUME,
               not_covered=["no slicer run: per-layer islands, suction forces and support placement of the resin parts are not simulated; the "
                            "orientations are those of spec 4.7 / the builders", "FDM overhang = area of faces whose normal points more than 50 deg "
                            "below the horizon, bed contact excluded; short bridges (hole tops, slots) are counted as overhang too",
                            "knife edges below 26 deg included angle are reported as 'sharpest_wedge_reading' only (socket rim of the caps: 51 deg, approved look)"],
               method="size: STL bounding box against the MSLA volume (any axis order); trapped volumes: connected surface components of the STL; "
                      "min feature: opposing-face thickness scan of checks_bl.py K4; vents: straight probe lines through the named openings "
                      "(Moeller-Trumbore against the part's STL); FDM: overhang area for the 6 axis orientations, the declared one judged")


RUN["K10"] = K10


# =====================================================================================================================
# main: run the wanted sections, merge with still-valid earlier results, write checks.json
# =====================================================================================================================
TITLES = {
    "K1": "valid closed solids / watertight STL", "K2": "no interference at rest (intended fits listed)",
    "K3": "moving clearances >= 1.0 (pan -85..85 x lift 0..20; J1 -155..155 vs the dummy hub)",
    "K4": "wall thickness (shells >= 2.0, local >= 1.2, chassis >= 1.6)", "K5": "bought-part seats with tolerance ranges, centre distances",
    "K6": "crank kinematics (stroke 20.0, dead centres), pan stop +-90", "K7": "assembly order / directions, tool paths D4.5, inserts accessible",
    "K8": "exterior fidelity (T3 shape, seams, no see-through from 26 viewpoints)", "K9": "real head / neck vs torso (Blender BVH), tilt table",
    "K10": "printability (size, min feature 0.6, drains, FDM overhangs)", "K11": "mass + centre of gravity of the torso",
}


def main():
    say(f"== checks.py {time.strftime('%Y-%m-%d %H:%M:%S')}  sections {' '.join(WANT)}  STL stamp {STAMP}  force {FORCE} ==")
    if "--modules" in ARGV:
        i = ARGV.index("--modules")
        sel = ARGV[i + 1].split(",") if len(ARGV) > i + 1 and not ARGV[i + 1].startswith("-") and ARGV[i + 1] not in SECTIONS else list(MODCHK)
        for k in sel:
            r = module_check(k)
            say(f"module check {k}: {'ok' if r is not None else 'NO RESULT: ' + _MOD_NOTE.get(k, '')}")
        return 0
    f = os.path.join(HERE, "checks.json")
    old = json.load(open(f)).get("checks", {}) if os.path.exists(f) else {}
    out = {}
    for k in SECTIONS:
        if k in WANT and k in RUN:
            t = time.time()
            try:
                out[k] = RUN[k]()
            except Exception as e:                                   # a check that cannot be computed is NOT RUN, never PASS
                out[k] = res("NOT RUN", f"the check raised {type(e).__name__}: {e}", traceback=traceback.format_exc()[-1800:])
            out[k]["time_s"] = round(time.time() - t, 1)
            say(f"{k} {out[k]['status']:8s} {out[k]['summary'][:400]}")
        elif k in old and old[k].get("stl_stamp") == STAMP and old[k].get("status") in ("PASS", "FAIL"):
            out[k] = old[k]
            say(f"{k} {out[k]['status']:8s} (kept from {old[k].get('generated')}, same STL set)")
        elif k in old:
            out[k] = res("NOT RUN", "stale: the STL set changed after this check last ran (" + str(old[k].get("generated")) + ", was " + str(old[k].get("status")) + ")")
            say(f"{k} NOT RUN  stale")
        else:
            out[k] = res("NOT RUN", "not implemented / not run yet")
            say(f"{k} NOT RUN")
        out[k]["title"] = TITLES[k]
    table = [dict(id=k, title=TITLES[k], status=out[k]["status"], summary=out[k]["summary"]) for k in SECTIONS]
    doc = dict(project="NOVA mini - T4 torso", generated=time.strftime("%Y-%m-%d %H:%M:%S"), stl_stamp=STAMP, n_parts=len(PARTS),
               all_pass=all(out[k]["status"] == "PASS" for k in SECTIONS), table=table,
               module_check_notes=_MOD_NOTE, checks=out)
    json.dump(doc, open(f, "w"), indent=1, ensure_ascii=False, default=float)
    say("== " + "  ".join(f"{k}:{out[k]['status']}" for k in SECTIONS) + f"  ({time.time() - T0:.0f} s) ==")
    return 0 if doc["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
