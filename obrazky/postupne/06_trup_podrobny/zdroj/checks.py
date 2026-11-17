#!/opt/venv/cad/bin/python
"""NOVA mini - T4 torso REV. 2: global checks K1 - K13  ->  checks.json  (+ checks.log)
(rev. 1 copy: rev2_backup/checks.py.integrator.bak)

    /opt/venv/cad/bin/python checks.py                 run everything that is stale, write checks.json
    /opt/venv/cad/bin/python checks.py K3 K12          only these sections (the others are kept if still valid)
    /opt/venv/cad/bin/python checks.py --force [K..]   ignore the caches (helpers and module checks are re-run once)
    /opt/venv/cad/bin/python checks.py --no-modules    do not (re)run the module check scripts (their results are then only
                                                       used when their stamp matches the STL files on disk)

Honesty rules
* every section stores the stamp of the STL set it ran on; a section whose stamp differs from the files on disk is
  reported as NOT RUN (stale), never as PASS;
* a section that raises, or whose helper (Blender script, module check) did not produce a result, is NOT RUN;
* a section with a row that cannot be computed (e.g. a bought-part rating that is not published) is NOT RUN unless the
  row is explicitly outside the criterion, and the row is named;
* declared fits / thin features / exceptions are listed with their reason; a value below its limit without a declaration
  is a FAIL.

K1-K11 as in rev. 1 on the rev. 2 geometry; K7 with the new rows of T4_rev2_plan D6 (service rows S1..S6 of t4_assembly.py,
the straight lowering of T_stred at T5, FFC into the ZIFs, USB-C plug, pivot screw path); K12 STRENGTH (every row of the
strength table under L1-L8 with the Z2 allowables: resin normal 8.5 / sustained 4.3 / abuse 12.9 MPa incl. Kt, epoxy 2.7, metal
against its own material); K13 RESIN RULES (Z1, Z3).

Sources: parts.json + stl/ written by build_all.py; finished parts of variant B from /tmp/claude-0/gapwf/fin/B/stl.
Helpers: checks_bl.py (Blender BVH: K2, K4, K5 play, K7, K8, K9) -> integ2_work/bl_<K>.json; the module check scripts of the
three builders (t4_ram_checks.py, t4_pan_checks.py, checks_obal.py + obal2_work/mesh_checks2.py + obal2_work/k8_obal.py).
"""
from __future__ import annotations
import os, sys, json, math, time, re, ast, subprocess, hashlib, traceback, threading

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np                                      # noqa: E402
import t4_common as C                                   # noqa: E402
import t4_mesh as TM                                    # noqa: E402

CAD, BL = "/opt/venv/cad/bin/python", "/opt/venv/bl/bin/python"
WORK = os.path.join(HERE, "integ2_work")
os.makedirs(WORK, exist_ok=True)
T0 = time.time()
ARGV = sys.argv[1:]
FORCE = "--force" in ARGV
NO_MOD = "--no-modules" in ARGV
SECTIONS = ["K1", "K2", "K3", "K4", "K5", "K6", "K7", "K8", "K9", "K10", "K11", "K12", "K13"]
WANT = [a for a in ARGV if a in SECTIONS] or SECTIONS
LOG = open(os.path.join(HERE, "checks.log"), "a")
A_N, A_S, A_A, A_EP = 8.5, 4.3, 12.9, 2.7               # Z2 allowables (MPa): normal / sustained + unfilleted notch / abuse / epoxy
BUILD = (211.68, 118.37, 220.0)                         # Elegoo Saturn 4 Ultra 16K (Z0)


def say(*a):
    s = f"[{time.time() - T0:7.1f}] " + " ".join(str(x) for x in a)
    print(s, flush=True); LOG.write(s + "\n"); LOG.flush()


DOC = json.load(open(os.path.join(HERE, "parts.json")))
PARTS = DOC["parts"]
REC = {r["name"]: r for r in PARTS}
B_MATE = ["golier_prstenec", "golier_kotuc", "krk_predna_polovica", "krk_zadna_polovica", "kabel"]


def stl_stamp():
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
_BL_DONE, _MOD_DONE = {}, {}
_BL_LOCK = threading.Lock()


def bl_section(key, opts=(), timeout=5400):
    with _BL_LOCK:
        if key not in _BL_DONE:
            _BL_DONE[key] = _bl_section(key, opts, timeout)
    return _BL_DONE[key]


def _bl_section(key, opts=(), timeout=5400):
    f = os.path.join(WORK, f"bl_{key}.json"); st = os.path.join(WORK, f"bl_{key}.stamp")
    if not FORCE and os.path.exists(f) and os.path.exists(st) and open(st).read().strip() == STAMP:
        return json.load(open(f))
    for q in (st, f):
        if os.path.exists(q):
            os.remove(q)
    say(f"   running checks_bl.py {key} ...")
    with open(os.path.join(WORK, f"bl_{key}.log"), "w") as lg:
        p = subprocess.run([BL, os.path.join(HERE, "checks_bl.py"), key, *opts], stdout=lg, stderr=subprocess.STDOUT, cwd=HERE, timeout=timeout)
    if p.returncode != 0 or not os.path.exists(f):
        raise RuntimeError(f"checks_bl.py {key} failed (exit {p.returncode}); see integ2_work/bl_{key}.log")
    open(st, "w").write(STAMP)
    return json.load(open(f))


MODCHK = {   # module check scripts: command, result file, dependencies
    "ram": ([CAD, "t4_ram_checks.py"], "ram_checks.json", ()),
    "pan": ([CAD, "t4_pan_checks.py"], "pan_checks.json", ()),
    "obal_mesh": ([BL, "obal2_work/mesh_checks2.py"], "obal2_work/mesh_checks2.json", ()),
    "obal_k8": ([BL, "obal2_work/k8_obal.py", "--", "--pitch", "0.25"], "obal2_work/k8_obal.json", ()),
    "obal": ([CAD, "checks_obal.py"], "checks_obal.json", ("obal_mesh", "obal_k8")),
}
_MOD_NOTE = {}
_MOD_LOCK = {k: threading.RLock() for k in MODCHK}


def module_check(name):
    with _MOD_LOCK[name]:
        if name not in _MOD_DONE:
            _MOD_DONE[name] = _module_check(name)
    return _MOD_DONE[name]


def start_module_checks():
    ths = [threading.Thread(target=module_check, args=(n,), daemon=True) for n in ("pan", "obal", "ram")]
    for t in ths:
        t.start()
    return ths


def _module_check(name):
    cmd, out, deps = MODCHK[name]
    st = os.path.join(WORK, f"mod_{name}.stamp")
    f = os.path.join(HERE, out)
    if not FORCE or NO_MOD:
        if os.path.exists(f) and os.path.exists(st) and open(st).read().strip() == STAMP:
            return json.load(open(f))
    if NO_MOD:
        _MOD_NOTE[name] = "module check result is stale for the STL files on disk and --no-modules was given"
        return None
    for dep in deps:
        if module_check(dep) is None:
            _MOD_NOTE[name] = f"{dep} did not run"
            return None
    say(f"   running module check {name}: {' '.join(cmd)}")
    t = time.time()
    with open(os.path.join(WORK, f"mod_{name}.log"), "w") as lg:
        p = subprocess.run(cmd, stdout=lg, stderr=subprocess.STDOUT, cwd=HERE)
    say(f"   module check {name}: exit {p.returncode} in {time.time() - t:.0f} s")
    if not os.path.exists(f) or os.path.getmtime(f) < t - 1:
        _MOD_NOTE[name] = f"script produced no result (exit {p.returncode}), see integ2_work/mod_{name}.log"
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
        elif isinstance(node, ast.For):
            # loops that extend a dict declared above (DECL1[...] = ...)
            if any(n in ast.unparse(node) for n in names) and all(n in ns for n in names if n in ast.unparse(node)):
                exec(compile(ast.Module([node], []), script, "exec"), ns)
            continue
        if tgt in names:
            exec(compile(ast.Module([node], []), script, "exec"), ns)
    return {n: ns[n] for n in names if n in ns}


def rx_any(name, pats):
    return any(re.match(p, name) for p in pats)


def mod_verdicts(name, m):
    """normalised {verdict: ok?} of a module result"""
    if m is None:
        return {}
    if name == "ram":
        return {k: bool(q.get("ok")) for k, q in m.get("verdicts", {}).items()}
    if name == "pan":
        return {k: str(q.get("status", "")).startswith("PASS") for k, q in m.items() if isinstance(q, dict) and "status" in q}
    if name == "obal":
        return {k: bool(q) for k, q in (m.get("summary") or {}).items()}
    return {}


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
    vol_note = [dict(name=q["name"], volume_occ_default=q["volume_occ"], volume_stl=q["volume_stl"],
                     diff_percent=rd(100.0 * (q["volume_occ"] - q["volume_stl"]) / q["volume_stl"], 2))
                for q in rows if abs(q["volume_occ"] - q["volume_stl"]) > max(0.5, 0.004 * abs(q["volume_stl"]))]
    step_big = [f for f in os.listdir(os.path.join(HERE, "step")) if os.path.getsize(os.path.join(HERE, "step", f)) > C.INTEG["STEP_MAX_MB"] * 1e6]
    step_missing = [r["name"] for r in PARTS if r.get("step") and not os.path.exists(os.path.join(HERE, r["step"]))]
    stl_missing = [r["name"] for r in PARTS if not os.path.exists(os.path.join(HERE, "stl", r["name"] + ".stl"))]
    names = set(REC)
    orphans = [f"{sub}/{f}" for sub, ext in (("stl", ".stl"), ("step", ".step")) for f in os.listdir(os.path.join(HERE, sub))
               if f.endswith(ext) and f[:-len(ext)] not in names]
    deleted_rev2 = ["T_ram", "T_prichytka_fpc", "P_koleso", "P_kluka", "L_jazyk", "fpc_pan", "T_puzdro_L", "T_puzdro_P", "cap_pan",
                    "skr_fpc", "skr_F5", "pena_J1", "kolik_dorazu", "kolik_ucha", "skr_kluky", "skr_jazyka", "spoj_zdvih", "pd_F7_1", "pd_F7_2"]
    still = [n for n in deleted_rev2 if n in names or os.path.exists(os.path.join(HERE, "stl", n + ".stl"))]
    ok = not bad and not step_big and not step_missing and not stl_missing and PARTS_JSON_OK and not orphans and not still
    return res("PASS" if ok else "FAIL",
               f"{len(PARTS) - len(bad)}/{len(PARTS)} parts: valid single BREP solid, volume > 0, STL closed (0 open / non-manifold / flipped edges), "
               f"one surface component, bbox as designed; STEP null for {len(DOC['step_null'])} loft-derived parts (rule: < 12 MB), "
               f"{len(step_big)} STEP over the limit; {len(orphans)} orphan exports; deleted rev. 1 parts still present: {still}",
               not_ok=bad, multi_component=comps, step_null=DOC["step_null"], step_over_limit=step_big, step_missing=step_missing,
               parts_json_matches_stl=PARTS_JSON_OK, orphan_exports=orphans, deleted_parts_still_present=still, parts=rows,
               brep_volume_differs_from_stl=dict(parts=vol_note, explanation="OCC volume integration is unreliable on trimmed loft faces; "
                                                 "masses use the STL volume (absolute chord deflection 0.01)"),
               method="BREP: is_valid / number of solids / volume from the build (parts.json, written by build_all.py); STL: re-read from disk, "
                      "welded at 1e-5, every edge used exactly twice and once per direction, signed volume > 0 and equal to parts.json, "
                      "connected surface components = 1 (no hidden inner void)")


# =====================================================================================================================
# K2  no interference at rest
# =====================================================================================================================
K2_FITS = [   # (regex a, regex b, max common volume mm3, reason)  - designed overlaps (thread / bonded slide fit / FFC in ZIF / crimp)
    (r"(skr_F1_|skr_F3a_|skr_F3b_|skr_F7_|skrutka_klb_|skr_F10_)", r"(vlozka_stred_|vl_F3a_|vl_F3b_|vl_F7_|vl_F8_|vl_F10_)", 9.0,
     "machine screw in the thread of its bonded brass insert"),
    (r"skr_F4_", r"mat_F4_", 4.5, "M2 screw in its DIN 562 nut"), (r"skr_F11$", r"matica_F11$", 4.5, "M2 screw in its DIN 562 nut"),
    (r"skr_F15$", r"T_most$", 3.0, "M3 screw in the tapped aluminium bridge (metal)"),
    (r"skr_F12_1$", r"L_pata$", 6.0, "M2 screw in the tapped aluminium foot (metal)"),
    (r"skr_ramena$", r"(servo_zdvih|rameno_zdvih)$", 12.0, "arm screw M2.5 in the MG90S output thread / countersink of the Al arm (metal)"),
    (r"skrutka_(led|repro)_", r"T_stred$", 4.5, "thread-forming M2 x 6 (F13) in the D1.7 pilot of a front-stack boss"),
    (r"skr_F14_", r"T_spodok$", 4.5, "thread-forming M2 x 6 (F14, one-time) in the D1.7 pilot"),
    (r"skr_F16_", r"servo_J1$", 6.0, "M2 x 6 screw in the STS3215 case thread (thread modelled solid)"),
    (r"cap_kluky$", r"rameno_zdvih$", 0.6, "crank pin pressed + Loctite 638 in the Al arm (metal-metal)"),
    (r"pastorok_J1$", r"servo_J1$", 30.0, "J1 pinion bore over the STS3215 spline (slide fit + Loctite 638; spline modelled solid)"),
    (r"pastorok_pan$", r"servo_pan$", 30.0, "pan pinion bore over the STS3032 spline (slide fit + Loctite 638; spline modelled solid)"),
    (r"pastorok_J1$", r"Z_koleso_J1$", 0.5, "J1 gear mesh (dummy sun gear)"), (r"koleso_pan$", r"pastorok_pan$", 0.5, "pan gear mesh"),
    (r"ffc_(A|B)_nosic$", r"DPS_riadenie$", 6.0, "FFC end inside the FH12 ZIF of the carrier"),
    (r"ffc_(A|B)_krk$", r"DPS_krk$", 6.0, "FFC end inside the FH19C ZIF of DPS_krk"),
    (r"(pigtail_zdvih|kabel_zdvih)$", r"konektor_zdvih$", 8.0, "lead crimped in the PicoBlade housing (flexible)"),
    (r"kabel_zdvih$", r"servo_zdvih$", 16.0, "lead leaves the MG90S inside its exit block"),
    (r"pigtail_zdvih$", r"DPS_krk$", 3.0, "pigtail soldered to the DPS_krk pads"),
    (r"ffc_par$", r"(ffc_A_krk|ffc_B_krk|ffc_A_nosic|ffc_B_nosic)$", 6.0, "same FFC strip (stacked pair -> single tails)"),
    (r"ptfe_cap$", r"T_cap$", 2.0, "PTFE tape wrapped on the pivot boss"),
    (r"ptfe_pas", r"P_sachta$", 45.0, "PTFE tape 0.13 wrapped on the journal ring / guide land (film on its land, STL chord 0.01)"),
    (r"ffc_par$", r"P_sachta$", 1.5, "FFC riser bonded in the 0.3 groove under the back floor / on the drum shroud (cable on its land)"),
    (r"(vyvod_led|vyvod_repro)$", r"(DPS_led|reproduktor|T_drziak_repro|T_drziak_led|T_stred)$", 6.0, "soldered lead in its exit (flexible)"),
    (r"krk_predna_polovica$", r"krk_zadna_polovica$", 1e9, "the two neck halves of variant B (finished parts, checked in B)"),
    (r"kabel$", r"(krk_predna_polovica|krk_zadna_polovica|DPS_krk|L_pata)$", 1e9, "neck wires of variant B in their channels / on the DPS_krk pads"),
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
               f"{len(bad)} unintended interference(s); {len(fits)} declared thread / bonded / ZIF / crimp fits ({len(cross)} across modules); "
               f"{contacts} pairs only touch (coincident faces, depth < {K2_CONTACT_DEPTH})",
               unintended=bad, intended_fits=fits, n_contacts=contacts, pairs_tested=d["pairs_tested"], method=d["method"],
               declared_fit_rules=[dict(a=a, b=b, max_mm3=v, why=w) for a, b, v, w in K2_FITS])


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
    resin = sorted({r["mat"] for r in PARTS if r["printed"]})
    dens_ok = all(abs(C.DENS[mt] - 1.15e-3) < 1e-9 for mt in resin)
    ok = not no_mass and off < 12.5 and dens_ok
    return res("PASS" if ok else "FAIL",
               f"torso (groups T + P + L, {sum(g['n'] for g in tor)} parts, without head / neck / arms / base): {m:.1f} g, centre of gravity "
               f"({cog[0]:.1f}, {cog[1]:.1f}, {cog[2]:.1f}) = {off:.1f} mm from the J1 axis, {cog[2] - C.Z_BRG[1]:.1f} mm above the 6805 "
               f"(criterion: every part has a mass, offset < 12.5 = bearing bore radius, every printed part 1.15 g/cm3: {dens_ok}); "
               f"dummy stand {out.get('Z', {}).get('mass_g')} g",
               torso_mass_g=rd(m, 2), torso_cog=[rd(v, 2) for v in cog], cog_offset_from_J1_axis=rd(off, 2), groups=out, parts_without_mass=no_mass,
               heaviest=[dict(name=n, mass_g=q) for q, n in heavy], densities_g_cm3=DOC["densities_g_cm3"], printed_materials=resin,
               method="mass: printed parts = STL volume x 1.15 g/cm3 (Elegoo Tough); bought parts = datasheet mass given by the module, otherwise "
                      "volume x density (brass 8.5, steel 7.85, 304 7.93, Al 2.70, magnet 7.5, PTFE 2.2, FR4 1.9); centre of gravity of each part = "
                      "volume centroid of its STL (uniform density)")


RUN = {"K1": K1, "K2": K2, "K11": K11}


# =====================================================================================================================
# K3  moving clearances: pan stage + lift module + neck (pan -90.3..90.3 x lift 0..20) vs the static torso; J1 vs the dummy
# =====================================================================================================================
K3_RULES_J1 = [   # J1 sweep: (regex torso part, regex dummy part, min allowed, reason)
    (r"lozisko_6805$", r"Z_naboj_test$", 0.0, "6805 inner ring D25 on the hub post and its shoulder (bearing seat)"),
    (r"T_spodok$", r"Z_naboj_test$", 0.3, "J1 lug R1 roots 0.316 over the stop-block top -99.3 (RAM G2); lug on the block = the hard stop +-153.4"),
]
K3_EXTRA = {   # integrator declarations for pairs the module lists do not name: frozenset -> (min, reason)
    frozenset(("fpc_lift", "ffc_riser")): (0.0, "same FFC strip (fixed leg -> crease block CF)"),
    frozenset(("fpc_lift", "pigtail_zdvih")): (0.0, "cable on cable (the pigtail passes under the crease block CM)"),
    frozenset(("skr_ramena", "servo_zdvih")): (0.0, "arm screw threaded into the MG90S output spline (thread fit)"),
}
_PAN_MODEL = {}


def pan_model():
    """static torso + pan stage / lift parts with sampling; scan(pans, lifts) -> {(moving, static): (distance, pan, lift, point)}"""
    if _PAN_MODEL:
        return _PAN_MODEL
    import t4_pan as MP
    decl = decl_from("t4_pan_checks.py", ["DECL1", "DECL2"])
    D1, D2 = dict(decl["DECL1"]), dict(decl["DECL2"])
    D1.update(K3_EXTRA)
    grp = {n: r["group"] for n, r in REC.items()}

    def tris_of(shape):
        V, T = C.mesh_of(shape, 0.01, 0.1)
        return V[T]

    TRI = {n: TM.stl(n, TM.STL_DIR) for n in REC}
    for n in B_MATE:
        TRI[n] = TM.stl(n, TM.B_STL)
    TRI["ffc_riser"] = tris_of(MP.ffc_riser())
    TRI["ffc_static"] = tris_of(MP.ffc_static())
    CRANK = ("rameno_zdvih", "cap_kluky", "skr_ramena")
    CABLE = ("ffc_par", "pigtail_zdvih")
    P_rigid = [n for n in REC if grp[n] == "P" and n not in CRANK + CABLE] + ["golier_kotuc", "ffc_riser"]
    L_set = [n for n in REC if grp[n] == "L" and n not in CABLE] + ["krk_predna_polovica", "krk_zadna_polovica", "kabel"]
    static = [n for n in REC if grp[n] == "T"] + ["golier_prstenec", "ffc_static"]

    def crank_x(T, theta):
        a = math.radians(-theta); c, s = math.cos(a), math.sin(a)
        R = T.copy(); y, z = T[..., 1] - MP.YL, T[..., 2] - MP.ZL
        R[..., 1] = MP.YL + c * y - s * z; R[..., 2] = MP.ZL + s * y + c * z
        return R

    _pose = {}

    def moving(name, lift):
        if name in CRANK:
            return crank_x(TRI[name], MP.crank_angle(lift))
        if name in ("fpc_lift", "pigtail_zdvih"):
            if (name, lift) not in _pose:
                _pose[(name, lift)] = tris_of(MP.fpc_lift(lift)) if name == "fpc_lift" else MP.pigtail_tris(lift)
            return _pose[(name, lift)]
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
    say(f"   K3 model: {len(sp)} static parts near the stage, {len(MS.T)} triangles")
    SMP = {n: TM.sample(TRI[n], 0.3)[0] for n in P_rigid}
    LM = list(CRANK) + L_set + ["fpc_lift", "pigtail_zdvih"]
    _sl = {}

    def smpl(n, lf):
        if (n, lf) not in _sl:
            _sl[(n, lf)] = TM.sample(moving(n, lf), 0.3)[0]
        return _sl[(n, lf)]

    def scan(pans, lifts):
        store = {}

        def run(name, Q, pan, lift):
            rows, e, pid = MS.query(Q)
            if len(rows) == 0:
                return
            for p_ in np.unique(pid):
                b = MS.names[p_]
                m = pid == p_
                k = int(np.argmin(e[m])); d = float(e[m][k])
                key = (name, b)
                if key not in store or d < store[key][0]:
                    store[key] = (d, pan, lift, [round(float(x), 2) for x in Q[rows[m][k]]])

        for pan in pans:
            for n in P_rigid:
                run(n, TM.rotz(SMP[n], pan), pan, 0.0)
            for lf in lifts:
                for n in LM:
                    run(n, TM.rotz(smpl(n, lf), pan), pan, lf)
            run("fpc_loop", TM.sample(tris_of(MP.fpc_loop(pan)), 0.3)[0], pan, 0.0)
        return store

    _PAN_MODEL.update(scan=scan, TRI=TRI, P_rigid=P_rigid, L_set=L_set, LM=LM, CRANK=CRANK, static=list(sp), D1=D1, D2=D2,
                      moving=moving, grp=grp)
    return _PAN_MODEL


def K3():
    need = C.INTEG["MOVE_CLEAR"]                                         # 1.0
    PANS = [-90.3, -90.0] + [float(p) for p in np.arange(-85.0, 85.1, 5.0)] + [90.0, 90.3]
    LIFTS = [float(v) for v in np.arange(0.0, 20.1, 2.5)]
    M = pan_model()
    TRI, P_rigid, L_set, LM, CRANK, D1, D2, moving, grp = (M[k] for k in ("TRI", "P_rigid", "L_set", "LM", "CRANK", "D1", "D2", "moving", "grp"))
    sp = M["static"]
    store = M["scan"](PANS, LIFTS)
    say(f"   K3a: {len(PANS) * len(LIFTS)} pan x lift poses done")
    rows_a, bad = [], []
    for (a, b), (d, pan, lf, at) in sorted(store.items(), key=lambda kv: kv[1][0]):
        key = frozenset((a, b))
        lim, why = (D2[key][0], D2[key][1]) if key in D2 else (need, None)
        if abs(abs(pan) - 90.0) < 0.35 and key in (frozenset(("P_drziak_serva", "kolik_dorazu_1")), frozenset(("P_drziak_serva", "kolik_dorazu_2"))):
            lim, why = 0.0, "lug on the stop pin (hard stop)"
        ok = d >= lim - 1e-3
        if d < 1.5 or not ok:
            rows_a.append(dict(moving=a, static=b, min_mm=rd(d), pan=pan, lift=lf, at=at, required=lim, declared=why, ok=bool(ok)))
        if not ok:
            bad.append(f"{a} <-> {b}: {d:.3f} < {lim} (pan {pan}, lift {lf}) at {at}")
    # front stack: every moving body vs the OBAL front stack (the rev. 2 PAN_ENV2 blocker), reported on its own
    FRONT = ("T_drziak_led", "DPS_led", "T_drziak_repro", "reproduktor", "tesnenie_repro", "skrutka_led_1", "skrutka_led_2",
             "podlozka_led_1", "podlozka_led_2", "skrutka_repro_1", "skrutka_repro_2", "skrutka_repro_3", "podlozka_repro_1",
             "podlozka_repro_2", "podlozka_repro_3", "T_svetlovod", "T_mriezka", "vyvod_led", "vyvod_repro")
    fs = [r for r in rows_a if r["static"] in FRONT]
    fs_min = min((v[0] for (a, b), v in store.items() if b in FRONT), default=None)
    # gear against the ROTATING pinion (ratio 2 : 1)
    pin_T = TRI["pastorok_pan"]
    Sg = TM.sample(TRI["koleso_pan"], 0.15)[0]
    gmin = (9.0, None)
    for pan in list(np.arange(-90.0, 90.01, 2.5)):
        Tp = TM.rotz(pin_T, -2.0 * pan, *C.R2["GEAR_PAN"]["ax"])
        Q = TM.rotz(Sg, pan)
        m = np.hypot(Q[:, 0] - C.R2["GEAR_PAN"]["ax"][0], Q[:, 1] - C.R2["GEAR_PAN"]["ax"][1]) < 8.6
        mm = TM.Multi({"pinion": Tp}, 0.15).min_by_part(Q[m], 1.0)
        if "pinion" in mm and mm["pinion"][0] < gmin[0]:
            gmin = (mm["pinion"][0], float(pan))
    if gmin[0] < 0.005:
        bad.append(f"pan gear <-> rotating pinion: flank gap {gmin[0]:.4f}")
    # (b) lift / crank parts against the stage, lift 0..20
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
    for (a, b), (d, lift, at) in sorted(near.items(), key=lambda kv: kv[1][0]):
        if d >= need - 1e-3:
            continue
        dec = D1.get(frozenset((a, b)))
        lim, why = (dec[0], dec[1]) if dec else (need, None)
        ok = d >= lim - 1e-3
        rows_b.append(dict(moving=a, stage_part=b, min_mm=rd(d), lift=lift, at=at, required=lim, declared=why, ok=bool(ok)))
        if not ok:
            bad.append(f"{a} <-> {b} (stage): {d:.3f} < {lim} at lift {lift}")
    # (c) J1 sweep against the dummy hub
    rot = [n for n in REC if grp[n] in ("T", "P", "L") and REC[n]["bbox"][4] < -84.4]
    zn = [n for n in REC if grp[n] == "Z"]
    MZ = TM.Multi({n: TRI[n] for n in zn}, 0.35)
    j1 = {}
    PHIS = [float(v) for v in np.arange(-155.0, 155.1, 5.0)] + [-153.4, 153.4]
    for n in rot:
        S0 = TM.sample(TRI[n], 0.35)[0]
        S0 = S0[S0[:, 2] < -84.0]
        for phi in PHIS:
            S = TM.rotz(TM.rotz(S0, phi, *C.J1_AX), phi) if n == "pastorok_J1" else TM.rotz(S0, phi)
            for b, (d, q) in MZ.min_by_part(S, 1.6).items():
                fw = abs(phi) <= 150.0
                key = (n, b, "firmware +-150" if fw else "to the hard stop +-153.4")
                if key not in j1 or d < j1[key][0]:
                    j1[key] = (d, phi, [round(float(x), 2) for x in q])
    rows_c = []
    for (a, b, rng), (d, phi, at) in sorted(j1.items(), key=lambda kv: kv[1][0]):
        lim, why = need, None
        for pa, pb, dm, w in K3_RULES_J1:
            if re.match(pa, a) and re.match(pb, b):
                lim, why = dm, w
        if (a, b) == ("pastorok_J1", "Z_koleso_J1"):
            lim, why = 0.005, "J1 gear mesh m1 18 / 18, C 18.00: flank gap (pinion rolled 2 x phi)"
        if (a, b) == ("T_spodok", "Z_naboj_test") and rng.startswith("to the hard"):
            lim, why = 0.0, "stop lug against the stop block = the hard stop (+-153.4)"
        ok = d >= lim - 1e-3
        if d < 1.5 or not ok:
            rows_c.append(dict(torso_part=a, dummy_part=b, range=rng, min_mm=rd(d), phi=phi, at=at, required=lim, declared=why, ok=bool(ok)))
        if not ok:
            bad.append(f"J1: {a} <-> {b}: {d:.3f} < {lim} at phi {phi} ({rng})")
    free_a = [r for r in rows_a if r["declared"] is None]
    mins = dict(P_L_vs_static_undeclared=min((r["min_mm"] for r in free_a), default=None),
                front_stack_min=rd(fs_min), stage_internal_undeclared=min((r["min_mm"] for r in rows_b if r["declared"] is None), default=None),
                J1_undeclared=min((r["min_mm"] for r in rows_c if r["declared"] is None), default=None), pan_gear_flank_gap=rd(gmin[0], 4))
    pm = module_check("pan")
    c3 = (pm or {}).get("C3_mesh", {}).get("status")
    return res("PASS" if not bad else "FAIL",
               f"pan {PANS[0]}..{PANS[-1]} (firmware +-85 step 5, hard stops +-90.0, tolerance +-90.3) x lift 0..20 step 2.5 "
               f"({len(PANS) * len(LIFTS)} poses), {len(P_rigid) + len(LM) + 1} moving bodies (stage, lift module, crank at its angle, foot / ear "
               f"/ DPS_krk / neck, FFC lift loop and pigtail in their posed shapes, FFC pan loop) against {len(sp)} static parts: smallest "
               f"undeclared clearance {mins['P_L_vs_static_undeclared']} (need {need}); OBAL front stack min {mins['front_stack_min']}; inside "
               f"the stage every pair below 1.0 is a declared running fit ({len(rows_b)} pairs); pan gear <-> rotating pinion flank gap "
               f"{mins['pan_gear_flank_gap']} (PAN C3: {c3}); J1 -155..155 vs the dummy: smallest undeclared {mins['J1_undeclared']}; "
               f"failures: {len(bad)}",
               failures=bad, minima=mins, front_stack_rows=fs, pan_lift_vs_static_below_1p5=rows_a, stage_internal_below_1p0=rows_b,
               J1_sweep_below_1p5=rows_c, rotating_parts_below_the_cap=rot, pan_module_C3=c3,
               method="exact point-to-triangle distances from surface samples (vertices + 0.3 mm grid) of the moving parts to the STL "
                      "triangles of the static parts (KD-tree of 0.4 mm samples names the candidate triangles).  Declared sub-1.0 gaps: "
                      "DECL1 / DECL2 of t4_pan_checks.py (journal, collar seam, pivot, gear stack 17.1, stop contact, FFC on its anchors, "
                      "crank pin in the slot, neck on the lands) + K3_EXTRA / K3_RULES_J1 of checks.py")


RUN["K3"] = K3


# =====================================================================================================================
# K4  wall thickness (Z3.1: structural >= 2.0, ribs >= 1.5, local skin >= 1.2; thinner only unloaded AND not handled)
# =====================================================================================================================
K4_LOCAL = 1.2                     # every reading below this must lie in a declared feature
K4_MIN_FEATURE = 0.6               # resin printability (rev. 1 criterion); tangent run-out edges are listed separately
K4_TOL = 0.012
K4_DECL = {   # part regex -> [(box (|x|0, |x|1, y0, y1, z0, z1), min, kind, text)]   kind: "local" | "runout" (tangent edge artefact)
    r"T_stred$": [((20.5, 26.0, 26.5, 31.5, -62.5, -22.0), 0.6, "local", "floor 0.6 behind the 4 door-frame magnet pockets (rev. 1 declared; magnet bonded, unloaded)"),
                  ((0.0, 21.0, 30.8, 34.8, -13.0, -11.5), 0.84, "local", "door top-seam tongue 0.85 (OBAL rev. 2: unloaded, not handled, Z3.1)")],
    r"T_bok_(L|P)$": [((33.4, 34.45, -30.5, 30.5, -78.5, 0.5), 0.75, "local", "seam-lip root ridge 0.75 (rev. 1 declared; hidden lap, unloaded)")],
    r"T_klb_(L|P)$": [((44.5, 59.5, -8.5, 9.0, -27.0, -7.0), 1.12, "local", "1.13 / 1.15 between the F8 counterbores D4.7 and the bush bore / D22 "
                                                                         "journal (OBAL rev. 2 declared local >= 1.0, not in the screw load path)")],
    r"T_mriezka$": [((0.0, 11.5, -40.5, -36.3, -51.0, -45.0), 0.6, "local", "grille webs 0.6 (rev. 1 declared; no load)")],
    r"T_spodok$": [((3.0, 3.8, 20.4, 21.2, -98.3, -97.7), 0.0, "runout", "J1 lug side root fillet R1 ending on the foot-ring bottom (tangent run-out)"),
                   ((11.9, 13.2, -21.8, -19.8, -64.8, -56.2), 0.7, "local", "pan-post web beside the slotted D2.3 F4 hole (the DIN 562 nut carries the load; RAM rev. 2)"),
                   ((2.0, 6.0, 12.4, 13.4, -64.2, -60.8), 0.64, "local", "F7 insert seat floor 0.65 (annulus behind the bonded insert, unloaded)"),
                   ((16.0, 20.0, 12.4, 13.4, -64.2, -60.8), 0.64, "local", "F7 insert seat floor 0.65 (annulus behind the bonded insert, unloaded)"),
                   ((34.3, 35.2, -6.5, 12.5, -27.0, -7.0), 0.65, "local", "F8 insert seat floors 0.7 behind the bonded M2 inserts of the shoulder boss (D2.3 pilot through; the insert pull acts outward, toward the T_klb screw head)"),
                   ((33.9, 38.0, 9.0, 15.3, -54.2, -48.0), 0.6, "local", "column web / bridge top around the D4.5 arm-wire hole (RAM rev. 2; ring "
                                                                           "around the wire hole, the web carries the load beside it)"),
                   ((29.3, 31.6, 20.8, 22.4, -82.8, -81.3), 1.09, "local", "F1 pad rim beside the D6.5 counterbore (1.6 under the washer, RAM E1)"),
                   ((29.3, 31.6, -22.4, -20.8, -82.8, -81.3), 1.09, "local", "F1 pad rim beside the D6.5 counterbore (1.6 under the washer, RAM E1)"),
                   ((24.3, 29.8, 7.9, 10.6, -84.7, -83.3), 0.94, "local", "J1 corner pad 1.2 edge at the window (compression only; RAM declared)"),
                   ((24.3, 29.8, -10.6, -7.9, -84.7, -83.3), 0.94, "local", "J1 corner pad 1.2 edge at the window (compression only; RAM declared)")],
    r"T_paluba$": [((19.7, 21.0, 15.5, 17.0, -46.4, -46.0), 0.0, "runout", "outer R1 cove of the static FFC wall ending at az 40 (tangent run-out)")],
    r"T_cap$": [((1.0, 4.6, -4.5, 4.5, -46.4, -46.0), 0.0, "runout", "root flare R0.6 ending on the bonded face (tangent run-out on the epoxy joint)")],
    r"P_sachta$": [((5.8, 8.4, 10.8, 12.0, -17.1, -14.5), 0.8, "local", "F10 A insert seat floor 0.8 (PAN declared)"),
                   ((0.4, 13.1, 10.9, 17.5, -42.7, -41.6), 0.64, "local", "drum FFC retaining lip 0.6..0.65 (PAN declared; cable guide)"),
                   ((16.9, 19.9, 10.8, 12.3, -38.8, -32.9), 0.8, "local", "F10 B insert / dowel seat floors 0.8 (PAN declared)"),
                   ((16.0, 23.7, 3.2, 7.1, -41.8, -40.3), 0.94, "local", "FFC riser groove 0.3 in the back floor (PAN declared)")],
    r"P_drziak_serva$": [((2.3, 6.2, 22.6, 23.9, -18.2, -16.7), 1.0, "local", "F11 block wall beside the DIN 562 nut slot 1.0 (PAN declared)"),
                         ((9.4, 10.3, 24.3, 30.3, -37.6, -35.9), 1.1, "local", "stop bridge around the D2.4 F12 key hole (PAN declared)")],
}


def _k4_decl(name, at, t):
    for pat, lst in K4_DECL.items():
        if re.match(pat, name):
            for bx, mn, kind, txt in lst:
                if bx[0] <= abs(at[0]) <= bx[1] and bx[2] <= at[1] <= bx[3] and bx[4] <= at[2] <= bx[5]:
                    return mn, kind, txt
    return None


def K4():
    d = bl_section("K4")
    rows, bad, used = [], [], {}
    for n, v in d["parts"].items():
        cells = [c for c in v.get("thin_cells", []) if c["t"] < K4_LOCAL - K4_TOL]
        und = []
        for c in cells:
            dc = _k4_decl(n, c["at"], c["t"])
            if dc is None or c["t"] < dc[0] - K4_TOL:
                und.append(c)
            else:
                used.setdefault(f"{n}: {dc[2]}", dict(kind=dc[1], min=99.0, n=0))
                u = used[f"{n}: {dc[2]}"]; u["min"] = min(u["min"], c["t"]); u["n"] += 1
        below_feature = [c for c in v.get("thin_cells", []) if c["t"] < K4_MIN_FEATURE - K4_TOL
                         and (_k4_decl(n, c["at"], c["t"]) or (0, "", ""))[1] != "runout"]
        rows.append(dict(part=n, mat=v.get("mat"), min=v.get("min"), p01=v.get("p01"), median=v.get("median"), cells_below_1p2=len(cells),
                         undeclared=und[:20], n_undeclared=len(und), below_0p6_not_runout=below_feature[:10]))
        if und or below_feature:
            bad.append(f"{n}: {len(und)} undeclared cell(s) < {K4_LOCAL} (first {und[:3]}), {len(below_feature)} < {K4_MIN_FEATURE}")
    mods = {}
    for name, keys in (("obal", ["M2"]), ("ram", ["E1_walls", "E2_insert_walls"]), ("pan", ["G_resin"])):
        m = module_check(name)
        if m is None:
            mods[name] = "NO RESULT: " + _MOD_NOTE.get(name, "")
            bad.append(f"module {name} wall check has no valid result")
            continue
        v = mod_verdicts(name, m)
        mods[name] = {k: v.get(k) for k in keys}
        if not all(v.get(k) for k in keys):
            bad.append(f"module {name} wall verdicts {mods[name]}")
    return res("PASS" if not bad else "FAIL",
               f"{len(rows)} printed parts scanned (opposing-face rays): every reading below {K4_LOCAL} lies in a declared local feature "
               f"({len(used)} declared features, {sum(1 for k in used.values() if k['kind'] == 'runout')} of them tangent run-out edges of "
               f"fillets / coves); nothing below {K4_MIN_FEATURE} except run-out edges; structural walls by the module checks: OBAL M2 "
               f"{mods.get('obal')}, RAM {mods.get('ram')}, PAN {mods.get('pan')}; failures {len(bad)}",
               failures=bad, parts=rows, declared_used=used, module_walls=mods, method=d.get("method"),
               declared=[dict(part=p, box_abs_x=b, min=m, kind=k, text=t) for p, l in K4_DECL.items() for b, m, k, t in l])


# =====================================================================================================================
# K5  bought-part seats, centre distances, coaxial fasteners
# =====================================================================================================================
def _axis_centre(name, axis):
    T = TM.stl(name).reshape(-1, 3); lo, hi = T.min(0), T.max(0); c = (lo + hi) / 2
    k = "xyz".index(axis)
    return np.delete(c, k)


COAX = [   # (screw, insert / nut / hole part, axis, tolerance)
    *[(f"skr_F1_{i}", f"vlozka_stred_{i}", "z", 0.05) for i in range(1, 5)],
    ("skr_F3a_1", "vl_F3a_1", "z", 0.05), ("skr_F3a_2", "vl_F3a_2", "z", 0.05), ("skr_F3b_1", "vl_F3b_1", "z", 0.05), ("skr_F3b_2", "vl_F3b_2", "z", 0.05),
    ("skr_F7_1", "vl_F7_1", "y", 0.05), ("skr_F7_2", "vl_F7_2", "y", 0.05),
    *[(f"skrutka_klb_{s}{i}", f"vl_F8_{s}{i}", "x", 0.05) for s in "LP" for i in (1, 2, 3)],
    ("skr_F10_A", "vl_F10_A", "y", 0.05), ("skr_F10_B", "vl_F10_B", "y", 0.05), ("skr_F11", "matica_F11", "x", 0.05),
    ("skr_F4_1", "mat_F4_1", "z", 0.35), ("skr_F4_2", "mat_F4_2", "z", 0.35),
]


def K5():
    fail, rows = [], []
    for s, h, ax, tol in COAX:
        if s not in REC or h not in REC:
            fail.append(f"{s} / {h}: part missing"); continue
        dlt = float(np.linalg.norm(_axis_centre(s, ax) - _axis_centre(h, ax)))
        ok = dlt <= tol
        rows.append(dict(screw=s, host=h, axis=ax, offset=rd(dlt), tol=tol, ok=bool(ok)))
        if not ok:
            fail.append(f"{s} not coaxial with {h}: {dlt:.3f} > {tol}")
    nums = dict(C_pan=rd(math.hypot(*C.R2["GEAR_PAN"]["ax"]), 4), C_J1=rd(math.hypot(*C.J1_AX), 4))
    if abs(nums["C_pan"] - 21.6) > 1e-3 or abs(nums["C_J1"] - 18.0) > 1e-3:
        fail.append(f"centre distances {nums}")
    mods = {}
    for name, keys in (("ram", ["D_seats", "C6_pivot_interface", "C8_stop_pins"]), ("obal", ["O4"]), ("pan", ["A_solids_slim"])):
        m = module_check(name)
        if m is None:
            mods[name] = "NO RESULT: " + _MOD_NOTE.get(name, ""); fail.append(f"module {name} has no valid result"); continue
        v = mod_verdicts(name, m); mods[name] = {k: v.get(k) for k in keys}
        if not all(v.get(k) for k in keys):
            fail.append(f"module {name} seat verdicts {mods[name]}")
    pm = module_check("pan") or {}
    a = pm.get("A_solids_slim", {})
    nums.update(stage_r_max=a.get("worst") or a.get("r_max"), ring_clear=a.get("ring_clear"), bore_clear=a.get("bore_clear"))
    play = bl_section("K5")
    return res("PASS" if not fail else "FAIL",
               f"{len(rows)} fasteners coaxial with their insert / nut (max offset {max((r['offset'] for r in rows), default=None)}; F4 slotted "
               f"+-0.3 for the backlash); C(pan) {nums['C_pan']}, C(J1) {nums['C_J1']}; stage ring {nums.get('ring_clear')} / bore "
               f"{nums.get('bore_clear')}; module seat tables RAM {mods.get('ram')}, OBAL {mods.get('obal')}, PAN {mods.get('pan')}",
               failures=fail, coaxial=rows, numbers=nums, module_seats=mods, free_play=play["parts"],
               method="coaxiality: bbox centres of screw and insert / nut perpendicular to the screw axis (STL); seats: the module seat "
                      "tables (RAM D 54 measurements on the solids, OBAL O4, PAN A); free play of every bought part in its seat: checks_bl.py K5")


# =====================================================================================================================
# K6  crank kinematics, pan / J1 hard stops
# =====================================================================================================================
def K6():
    import t4_pan as MP
    fail = []
    z = {th: MP.pin_pos(th)[1] if len(MP.pin_pos(th)) == 2 else MP.pin_pos(th)[2] for th in (0.0, 3.0, 90.0, 177.0, 180.0)}
    stroke = z[180.0] - z[0.0]
    lifts = {L: rd(MP.crank_angle(L), 3) for L in (0.0, 10.0, 20.0)}
    if abs(abs(stroke) - 20.0) > 0.01:
        fail.append(f"crank stroke {stroke:.3f}")
    pm = module_check("pan") or {}
    rm = module_check("ram") or {}
    D = pm.get("D_stop", {}); E = pm.get("E_crank", {})
    G1 = (rm.get("verdicts", {}) or {}).get("G1_J1_stop_angle", {})
    for k, v in (("PAN D_stop", D.get("status")), ("PAN E_crank", E.get("status")), ("RAM G1", G1.get("ok"))):
        if v not in ("PASS", True):
            fail.append(f"{k}: {v}")
    return res("PASS" if not fail else "FAIL",
               f"crank r {C.R2['CRANK']['r']}: pin z at theta 0 / 180 = {rd(z[0.0])} / {rd(z[180.0])} -> stroke {abs(stroke):.3f} (dead centres at "
               f"0 / 180, firmware 3..177: {rd(z[3.0])} .. {rd(z[177.0])}); crank angle at lift 0 / 10 / 20: {lifts}; pan hard stop "
               f"{D.get('pin_1', {}).get('contact_pan') if isinstance(D.get('pin_1'), dict) else D.get('summary', '')} / "
               f"{D.get('pin_2', {}).get('contact_pan') if isinstance(D.get('pin_2'), dict) else ''} (PAN D {D.get('status')}); crank module "
               f"PAN E {E.get('status')}; J1 stop {G1.get('note', '')[:90]} (RAM G1 {G1.get('ok')})",
               failures=fail, crank=dict(z=z, stroke=rd(abs(stroke), 4), crank_angle=lifts), pan_stop=D, crank_module=E, J1_stop=G1)


RUN.update(K4=K4, K5=K5, K6=K6)


# =====================================================================================================================
# K7  assembly + service (T4_rev2_plan D6 rows)
# =====================================================================================================================
K7_LOWER_MIN = C.TOWER_CLEAR - 0.01   # plan clearance while T_stred is lowered (keep-out r 3.65 = boss r 3.40 + 0.25)


def K7():
    import importlib
    sys.path.insert(0, WORK)
    d = bl_section("K7")
    fail = list(d["problems"])
    if d["parts_never_mounted"]:
        fail.append(f"parts that no assembly step mounts: {d['parts_never_mounted']}")
    steps, n_sc, n_hw, n_sweep, keys = [], 0, 0, 0, []
    for s in d["steps"]:
        row = dict(id=s["id"], bench=s["bench"], service=s.get("service", False), text=s["text"], pan=s["pan"], move=s["move"], parts_present=s["n_ctx"])
        if "legs" in s:
            n_sweep += 1
            row.update(withdrawal_legs=s["legs"], collisions=s["collisions"], declared_fits=[f"{c['moving']} x {c['static']}" for c in s["declared_fits_met"]])
            for k in ("not_swept", "flex_sweeps"):
                if k in s:
                    row[k] = s[k]
        if s["hardware"]:
            row["hardware"] = [dict(part=h["part"], dir=h["dir"], open=h["open"], blocked_by=h["blocked_by"]) for h in s["hardware"]]
            n_hw += len(s["hardware"])
        if s["screws"]:
            row["screws"] = [dict(screw=x["screw"], tool_d=x.get("tool_d"), tool_dir=x["tool_dir"], free=x["free_D4p5"], own_recess_only=x["own_recess_only"],
                                  free_ring_radius=x["free_ring_radius"], ok=x["ok"], blocked_by=x["blocked_by"]) for x in s["screws"]]
            n_sc += len(s["screws"])
            keys += [x["screw"] for x in s["screws"] if (x.get("tool_d") or 4.5) < 4.5]
        steps.append(row)
    # ---- T5: T_stred lowered straight down over everything that is in place (exact plan clearance)
    LW = importlib.import_module("lowering")
    sixth = [s for s in d["steps"] if s["id"] == "T5"]
    present_t5 = [n for n in REC if REC[n]["module"] == "ram" and REC[n]["group"] == "T" and n not in ("pastorok_pan",)
                  and not n.startswith(("skr_F1_", "pd_F1_"))] + ["ffc_A_nosic", "ffc_B_nosic"]
    # the black cap spigot (T_spodok, z <= SPIGOT top -78.0 incl. its 0.6 lead-in) is the declared 0.2 locating fit that guides the
    # white lip at T5: it is tested on its own against the fit value; everything above it against K7_LOWER_MIN
    zsp = C.SPIGOT["z"][1] + 0.05
    stred_T = TM.stl("T_stred")
    low = LW.run(stred_T, {n: TM.stl(n) for n in present_t5}, zwin={"T_spodok": (zsp, 1e9)})
    spg = LW.run(stred_T, {"T_spodok": TM.stl("T_spodok")}, zwin={"T_spodok": (-1e9, zsp)})["T_spodok"]
    low_rows = sorted([dict(part=n, plan_clearance=rd(c), at=at) for n, (c, at) in low.items() if c < 1.6], key=lambda r: r["plan_clearance"])
    low_bad = [r for r in low_rows if r["plan_clearance"] < K7_LOWER_MIN]
    for r in low_bad:
        fail.append(f"T5 lowering: {r['part']} plan clearance {r['plan_clearance']} < {K7_LOWER_MIN} at {r['at']}")
    spigot_row = dict(part="T_spodok spigot (z <= %.2f)" % zsp, plan_clearance=rd(spg[0]), at=spg[1], declared_fit=C.SPIGOT["fit"],
                      criterion=round(C.SPIGOT["fit"] - 0.03, 3), ok=bool(spg[0] >= C.SPIGOT["fit"] - 0.03))
    if not spigot_row["ok"]:
        fail.append(f"T5 lowering: spigot band plan clearance {spigot_row['plan_clearance']} < {spigot_row['criterion']} (declared fit {C.SPIGOT['fit']})")
    # ---- module rows: tool channels / reach / FFC line of sight / lift module out / neck out / USB plug
    mod, new_rows = {}, []
    rm, pm = module_check("ram"), module_check("pan")
    if rm is None or pm is None:
        fail.append(f"module checks missing: ram {rm is not None}, pan {pm is not None}")
    else:
        rv = mod_verdicts("ram", rm)
        for k in ("F_tool_channels", "H1_usb_plug_envelope_free", "H2_connectors_reachable_from_the_door"):
            mod[f"RAM {k}"] = rv.get(k)
            if not rv.get(k):
                fail.append(f"RAM {k} not ok")
        F = pm.get("F_k7", {})
        for k in ("F1", "F2", "F3", "F4"):
            mod[f"PAN {k}"] = (F.get(k) or {}).get("status")
            if not str((F.get(k) or {}).get("status", "")).startswith("PASS"):
                fail.append(f"PAN F_k7 {k}: {(F.get(k) or {}).get('status')}")
        a = pm.get("A_solids_slim", {})
        mod["PAN A stage through the ring"] = a.get("status")
        if a.get("status") != "PASS":
            fail.append("PAN A (stage r <= 26.5 through the glued ring) not PASS")
    st = {s["id"]: s for s in steps}

    def ok_step(i):
        s = st.get(i)
        return s is not None and not s.get("collisions") and all(x["ok"] for x in s.get("screws", [])) and all(h["open"] for h in s.get("hardware", []))
    new_rows = [
        dict(row="stage up through the glued ring (neck + lift module out, F15 out)", step="S3 + PAN A", ok=ok_step("S3") and mod.get("PAN A stage through the ring") == "PASS"),
        dict(row="neck out with DPS_krk (up through the glued collar disc)", step="S2 + PAN F2", ok=ok_step("S2") and str(mod.get("PAN F2", "")).startswith("PASS")),
        dict(row="lift module out through the door (ear on the pin)", step="S1 + PAN F1", ok=ok_step("S1") and str(mod.get("PAN F1", "")).startswith("PASS")),
        dict(row="pivot screw F15 tool path through the empty well", step="S4", ok=ok_step("S4")),
        dict(row="FFC into the DPS_krk ZIFs (door, stage at the +90 stop) and the carrier ZIFs", step="PAN F3 + RAM H2",
             ok=str(mod.get("PAN F3", "")).startswith("PASS") and bool(mod.get("RAM H2_connectors_reachable_from_the_door"))),
        dict(row="pan servo service with T_stred off", step="S5", ok=ok_step("S5")),
        dict(row="USB-C straight plug (envelope free, reachable from the door)", step="RAM H1 + H2", ok=bool(mod.get("RAM H1_usb_plug_envelope_free"))),
        dict(row="T_stred lowered straight over the tower (T5)", step="T5 + exact plan clearance", ok=ok_step("T5") and not low_bad),
        dict(row="carrier out through the door", step="S6", ok=ok_step("S6")),
    ]
    for r in new_rows:
        if not r["ok"]:
            fail.append(f"K7 row '{r['row']}' not ok")
    main = [s for s in steps if not s["bench"] and not s["service"]]
    return res("PASS" if not fail else "FAIL",
               f"{len(steps)} steps ({sum(s['bench'] for s in steps)} bench, {len(main)} torso, {sum(s['service'] for s in steps)} service rows): "
               f"{n_sweep} straight-line paths swept against the parts present - {sum(len(s.get('collisions', [])) for s in steps)} undeclared "
               f"collisions; {n_sc} screws with a straight tool channel (D4.5, or the named key: {sorted(set(keys))}); {n_hw} inserts / magnets / "
               f"pins with an open mouth; T_stred lowering: min plan clearance {low_rows[0]['plan_clearance'] if low_rows else '>= 1.6'} "
               f"({low_rows[0]['part'] if low_rows else ''}), spigot band {spigot_row['plan_clearance']} (declared locating fit {C.SPIGOT['fit']}); D6 rows {sum(r['ok'] for r in new_rows)}/{len(new_rows)} ok; module rows {mod}; "
               f"problems: {len(fail)}",
               failures=fail, steps=steps, d6_rows=new_rows, T5_lowering=low_rows, T5_spigot=spigot_row, module_rows=mod,
               not_path_tested=d["parts_arriving_without_a_path_test"], flexible_parts=d["flexible"],
               notes=["pan pinion: bonded in situ AFTER T5 (its tip circle r 29.6 cannot pass the T_stred lip; RAM C2) - step T5b",
                      "FFC pair, leads, PTFE tapes, PORON: flexible, not path-tested (reserved space)",
                      "FFCs are plugged into the DPS_krk ZIFs with the stage turned by hand to the +90 stop (PAN F3 line of sight)",
                      "F11 is driven on the bench (lift module out); F12 with a 1.3 hex key through the D2.4 bridge hole",
                      "stage removal: the soft fold CF of the lift loop is opened and the free FFC laid flat on the end wall (r <= 26.3)"],
               method=d["method"] + "  T5: exact plan clearance (integ2_work/lowering.py): every point of a part present at T5 against the "
                                    "T_stred points that pass below it while T_stred comes down")


# =====================================================================================================================
# K8  exterior fidelity, seams, see-through   (as rev. 1; the shells are rev. 2)
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
    dd = np.arange(2.6, 88.5, 0.05)
    da = max(abs(C.prof(float(x))[0] - C.prof_t3(float(x))[0]) for x in dd); db = max(abs(C.prof(float(x))[1] - C.prof_t3(float(x))[1]) for x in dd)
    if max(da, db) > 0.01:
        fail.append(f"analytic T4 profile differs from T3 below the rim zone by {max(da, db):.3f}")
    if om is None:
        return res("NOT RUN", "module check OBAL (M3 exterior grid, S1 seam backing, seam widths) has no valid result for the STL files on disk: "
                   + _MOD_NOTE.get("obal", ""), exterior_vs_T3=ext, see_through_26=see)
    m3, s1 = om.get("M3_exterior", {}), om.get("S1_seam_backing", {})
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
        notes.append(f"seam not backed (dark interior visible, no see-through): {k}: {v.get('open')} of {v.get('rays')} lines of sight - {v.get('reason')}")
    zs = ext["zones"]
    return res("PASS" if not fail else "FAIL",
               f"white shells + plugs: {zs['white']['points']} T3 grid points, deviation {ext['dev_strict_min']} .. {ext['dev_strict_max']} mm, "
               f"{ext['n_bad_strict']} over 0.05 outside the declared zones; analytic T4 vs T3 below drop 2.6: {max(da, db):.4f}; seams measured "
               f"{sw}; see-through from 26 viewpoints: {see['see_through']} of {see['rays']} rays; seam lines of sight leaving the torso: "
               f"{s1.get('see_through_total')}",
               failures=fail, notes=notes, exterior_vs_T3=ext, see_through_26=dict(rays=see["rays"], see_through=see["see_through"], pitch=see["pitch"],
                                                                                    scene=see["scene"], note=see["note"], views=see["views"]),
               module_obal=dict(M3_exterior=dict(ok=m3.get("ok"), seam_widths=sw), S1_seam_backing=dict(ok=s1.get("ok"),
                                                                                                          see_through_total=s1.get("see_through_total"))))


# =====================================================================================================================
# K9  real head / neck against the torso   (as rev. 1)
# =====================================================================================================================
def K9():
    d = bl_section("K9", ["--fine"])
    crit = d["criterion"]
    rows, table_needed, fail = [], {}, []
    for lift, v in sorted(d["lifts"].items(), key=lambda kv: -float(kv[0])):
        rows.append(dict(lift=float(lift), tilt_down_max=v["tilt_table_B"]["down"], tilt_up_max=v["tilt_table_B"]["up"], min_clearance=v["min_clearance"],
                         at=v["at"], head_vs_stage_min=v["head_vs_stage"]["min"]))
        if v["reduced_pans"]:
            table_needed[lift] = v["limit_per_pan"]
        if v["min_clearance"] <= 0.02:
            fail.append(f"lift {lift}: the head touches the torso inside the B tilt table ({v['at']})")
    worst = d["worst"]; margin = d["min_clearance"] - crit
    return res("PASS" if not fail else "FAIL",
               f"head (variant B STL, {len(d['head_parts'])} parts) vs torso meshes, pan -85..85 x lift 20 / 12.5 / 7.5 / 0 x tilt inside the B "
               f"table: min clearance {d['min_clearance']} mm at lift {worst['lift']}, tilt {worst['tilt']}, pan {worst['pan']} "
               f"({worst['torso_part']} / {worst['head_part']}); criterion {crit}; "
               + ("no pose below the criterion" if not table_needed else f"poses below the criterion at lifts {sorted(table_needed)} - tilt limit table attached")
               + f"; margin {margin:.3f} mm",
               failures=fail, criterion=crit, per_lift=rows, pan_dependent_tilt_limit_table=table_needed or None,
               recommendation="firmware: tilt down <= 27.5 deg for lift 10 .. 15 (all pans)" if margin < 0.1 else None,
               static_parts=d["static_parts"], not_included=d["not_included"], method=d["method"])


# =====================================================================================================================
# K10  printability on the Elegoo Saturn 4 Ultra 16K (211.68 x 118.37 x 220, 5 mm margin), orientation / supports / drains
# =====================================================================================================================
def K10():
    fail, rows = [], []
    rec = {}
    for mod in ("obal", "ram", "pan"):
        md = json.load(open(os.path.join(HERE, f"parts_{mod}.json")))
        for e in md["parts"]:
            if e.get("print"):
                rec[e["name"]] = e["print"]
    pm = module_check("pan") or {}
    gp = (pm.get("G_resin") or {}).get("print_table") or (pm.get("G_resin") or {}).get("print") or {}
    for r in PARTS:
        if not r["printed"]:
            continue
        b = np.array(r["bbox"]); ext = b[3:] - b[:3]
        fits_axis = bool(all(np.sort(ext + 10.0) <= np.sort(np.array(BUILD))))
        pr = rec.get(r["name"]) or (gp.get(r["name"]) if isinstance(gp, dict) else None)
        row = dict(part=r["name"], mat=r["mat"], bbox_extents=[rd(v, 1) for v in ext], fits_axis_aligned_with_5mm=fits_axis,
                   print_record=bool(pr), orientation=(pr or {}).get("orientation") if isinstance(pr, dict) else None)
        rows.append(row)
        if not r["mat"].startswith("resin"):
            fail.append(f"{r['name']}: printed but material {r['mat']}")
    mods = {}
    for name, keys in (("obal", ["R"]), ("ram", ["P_print_table"]), ("pan", ["G_resin"])):
        m = module_check(name)
        if m is None:
            mods[name] = "NO RESULT"; fail.append(f"module {name} print table has no valid result"); continue
        v = mod_verdicts(name, m); mods[name] = {k: v.get(k) for k in keys}
        if not all(v.get(k) for k in keys):
            fail.append(f"module {name} print verdicts {mods[name]}")
    not_axis = [r["part"] for r in rows if not r["fits_axis_aligned_with_5mm"]]
    no_rec = [r["part"] for r in rows if not r["print_record"]]
    return res("PASS" if not fail else "FAIL",
               f"{len(rows)} printed parts, all Elegoo Tough resin; {len(rows) - len(not_axis)} fit the 211.68 x 118.37 x 220 volume with 5 mm in "
               f"an axis-aligned orientation, {not_axis} fit tilted as the module print tables state; module print / support / cup / drain "
               f"verdicts {mods}; parts without a print record in parts_<module>.json: {no_rec} (PAN keeps its print table in pan_checks G)",
               failures=fail, parts=rows, module_print=mods, build_volume=BUILD)


RUN.update(K7=K7, K8=K8, K9=K9, K10=K10)


# =====================================================================================================================
# K12  STRENGTH - every row of the strength table under L1..L8 with the Z2 allowables (resin normal 8.5 / sustained 4.3 /
#      abuse 12.9 MPa incl. Kt, epoxy 2.7; bought metal parts against their own material) on the final geometry
# =====================================================================================================================
REV1_ROWS = [   # rows of overenie_pevnost.md (rev. 1) -> what carries the load in rev. 2 and where the row is recomputed
    ("1-3", "pan gear tooth, resin P_koleso", "bought brass 36T m0.8 (Lewis): PAN H n 1"),
    ("4-5", "pan pinion / resin face width", "bought brass / steel 18T m0.8 (Lewis): PAN H"),
    ("6-8", "pan stop groove in T_paluba, pin seat in P_koleso, engagement under L1", "2 steel pins D3 bonded in T_spodok posts: RAM S05a-e, PAN H stop rows, PAN D engagement 2.6 / 2.5"),
    ("9", "gear <-> hub epoxy", "PAN H n 2 / 3 (gear bonded under the hub disc)"),
    ("10", "pivot journal", "RAM S06c (T_cap D7.96 on PTFE tape)"),
    ("11", "pivot press seat in the deck boss", "deleted: T_cap bonded on the Al bridge T_most (RAM S06, S06b, S06d)"),
    ("12-14", "PTFE washer, T_paluba floor / plate under L2", "deck 2.0 on shims over the STS3215 + T_most: RAM rows A7b / 50 / 50b and the L2 stack 17.1"),
    ("15", "collar-ring glue as the only axial retention (L1)", "deleted: L1 goes F15 -> T_most -> F3b (RAM A7a-d); the ring carries nothing"),
    ("16-20", "resin ear L_ucho", "304 stainless ear 1.5: PAN H ear rows (metal)"),
    ("21", "ear slot / pin contact", "steel pin in the steel ear slot: PAN H"),
    ("22-25", "resin crank P_kluka", "bought aluminium arm: PAN H arm rows (metal)"),
    ("26", "crank pin seat", "pin pressed + 638 in the Al arm (metal): PAN H"),
    ("27", "tab post (F11 host)", "F11 into a DIN 562 nut in the pocket block: PAN H"),
    ("28-29", "0.8 ledge under the lift servo", "deleted: closed pocket with the keyhole end wall (PAN H keyhole bearing)"),
    ("30", "F11 thread-forming pilot", "DIN 562 nut: PAN H"),
    ("31", "bracket pad root r 3.0 sharp", "pads r 3.5 / 3.25 with R1 roots: PAN H pad rows"),
    ("32", "F10 slots held by friction", "F10 dowel + bottom rail: PAN H F10 rows"),
    ("33-35", "F12 in the resin foot, head on the resin flange, ear dowel", "metal-metal (Al foot tapped, steel ear): PAN H F12 rows"),
    ("36", "L_pata plate", "Al flat bar: PAN H"),
    ("37", "neck <-> foot epoxy", "PAN H bond row"),
    ("38", "MG90S output side load", "bought part rating not published: PAN H row (UNVERIFIED) - see not_verifiable"),
    ("39", "T_klb neck", "OBAL S1a / S1b"),
    ("40", "F8 inserts in the column boss", "RAM row 40, OBAL F8 rows"),
    ("41", "T_klb + F8 sideways topple", "OBAL S1c (estimate with an assumed impact force) - see not_verifiable"),
    ("42-45", "T_ram column, foot, torsion", "merged T_spodok column: RAM 42 / 42y / 43 / 44 / 42c / 45 + the integrator head / plate sections"),
    ("46", "column stop ring under the cap flange", "RAM 46 (+ the recommended F8 torque)"),
    ("47", "J1 pinion at stall", "bought brass m1 18T; the Loctite 638 joint releases at about 1.1 N.m first: RAM 48 / L8 rows"),
    ("48", "cradle walls", "2.5 walls: RAM 48"),
    ("49", "J1 stop lug", "lug 2.35 x 5.0 with R1 roots: RAM 49"),
    ("50", "floor under the STS3215", "4 corner pads 1.2 + window: RAM 50 / 50b"),
    ("51", "6805 seat", "RAM 51 / 51b"),
    ("52", "skirt disc", "deleted (S11)"),
    ("53", "F1", "OBAL F1 rows (bonded M2.5 inserts)"),
    ("54-55", "door hook tabs", "deleted: 4 magnet pairs (OBAL door rows)"),
    ("56", "door / frame magnet bonds", "OBAL magnet rows"),
    ("57-59", "insert / thread-forming torques at L7", "recommended torques R2['TORQUE_REC']: RAM L7 rows, OBAL torque rows, PAN F10 / F12 rows"),
    ("60", "screw heads on resin without washers", "washers under every head on resin (K13)"),
    ("61", "P_kluka hub around the countersunk head", "deleted (Al arm, metal-metal)"),
    ("62", "thread-forming boss hoop factor", "F13 / F14 bosses D5, engagement >= 2d (OBAL O4 / RAM P k13)"),
]


def _rows_ram(m):
    out = []
    for r in m.get("S", []):
        out.append(dict(module="RAM", id=r["no"], feature=r["feature"], case=r["case"], stress=r["stress"], allowable=r["allowable"],
                        margin=r.get("margin"), ok=r["ok"], decisive=not r.get("info"), note=r.get("note", "")))
    return out


def _rows_pan(m):
    h = (m or {}).get("H_strength", {})
    out = []
    for r in h.get("rows", []):
        v = str(r.get("verdict", ""))
        ok = True if v.startswith("OK") else (False if v.startswith(("FAIL", "NOT")) else None)
        out.append(dict(module="PAN", id=f"H{r.get('n')}", feature=r.get("feature"), case=r.get("load_case"), stress=r.get("stress"),
                        allowable=r.get("limit"), margin=r.get("margin"), ok=ok, decisive=True, note=f"{r.get('cls')}; {r.get('basis', '')}"))
    return out


def _rows_obal(m):
    s = (m or {}).get("S_strength", {})
    out = []
    for r in s.get("rows", []):
        role = r.get("role")
        out.append(dict(module="OBAL", id=r.get("id"), feature=r.get("feature"), case=r.get("load"), stress=r.get("stress_MPa"),
                        allowable=r.get("allowable_MPa"), margin=r.get("ratio"), ok=r.get("ok"),
                        decisive=role not in ("info", "spec torque"), note=f"role {role}; " + str(r.get("note", ""))))
    return out


def K12():
    rm, pm, om = module_check("ram"), module_check("pan"), module_check("obal")
    if rm is None or pm is None or om is None:
        return res("NOT RUN", f"module strength rows missing: ram {rm is not None}, pan {pm is not None}, obal {om is not None}: {_MOD_NOTE}")
    rows = _rows_ram(rm) + _rows_pan(pm) + _rows_obal(om)
    dec = [r for r in rows if r["decisive"]]
    fails = [r for r in dec if r["ok"] is False]
    unknown = [r for r in dec if r["ok"] is None]
    # criterion check (margin >= 1 against the Z2 allowable of the class; 12.9 for abuse = factor 2 on the UTS)
    bad_margin = [r for r in dec if r["ok"] and r.get("margin") is not None and r["margin"] < 1.0 - 1e-6]
    status = "FAIL" if (fails or bad_margin) else ("NOT RUN" if unknown else "PASS")
    tight = sorted([r for r in dec if r["ok"] and r.get("margin")], key=lambda r: r["margin"])[:8]
    return res(status,
               f"{len(rows)} rows ({len(dec)} decisive: RAM {sum(r['module'] == 'RAM' for r in dec)}, PAN {sum(r['module'] == 'PAN' for r in dec)}, "
               f"OBAL {sum(r['module'] == 'OBAL' for r in dec)}) recomputed on the final geometry with the Z2 allowables: {len(fails)} FAIL, "
               f"{len(unknown)} not verifiable (input not published / assumed), tightest OK: "
               + "; ".join(f"{r['module']} {r['id']} {str(r['feature'])[:40]} {r['stress']}/{r['allowable']}" for r in tight[:4])
               + ("; FAIL: " + "; ".join(f"{r['module']} {r['id']} {str(r['feature'])[:60]} ({r['case']}) {r['stress']} > {r['allowable']}" for r in fails[:6]) if fails else ""),
               failing_rows=fails, not_verifiable=unknown, rows=rows, rev1_table_mapping=[dict(rev1_rows=a, rev1=b, rev2=c) for a, b, c in REV1_ROWS],
               allowables=dict(normal=A_N, sustained_or_notch=A_S, abuse=A_A, epoxy=A_EP, note="resin rows include Kt; abuse 12.9 = factor 2 on the "
                                                                                                   "UTS lower bound 25.8; metal rows against the module's metal limit"),
               method="module strength rows re-run on the final STL / BREP set (t4_ram_checks.py S: sections of the real solids with "
                      "overenie_pevnost/pv_lib.py; t4_pan_checks.py H; checks_obal.py S) - hand / section calculations, no 3-D FE")


# =====================================================================================================================
# K13  RESIN RULES (T4_zivica Z1 / Z3, T4_rev2_plan D6)
# =====================================================================================================================
CSK_HOSTS = {"skr_F3b_1": "T_most (Al)", "skr_F3b_2": "T_most (Al)", "skr_F7_1": "DPS_riadenie (FR4)", "skr_F7_2": "DPS_riadenie (FR4)",
             "skr_ramena": "rameno_zdvih (Al arm)"}


def K13():
    fail, notes = [], []
    printed = [r for r in PARTS if r["printed"]]
    petg = [r["name"] for r in PARTS if r["mat"] in ("petg", "pom") or re.search(r"PETG|POM", r.get("label_sk") or "")]
    if petg:
        fail.append(f"PETG / POM parts: {petg}")
    inserts = [r for r in PARTS if r["name"].startswith(("vl_", "vlozka_"))]
    heat = [r["name"] for r in inserts if "lepen" not in (r.get("label_sk") or "")]
    if heat:
        fail.append(f"inserts not labelled bonded (lepená): {heat}")
    csk = [r["name"] for r in PARTS if re.search(r"zápustn|DIN 7991|ISO 10642", (r.get("label_sk") or "") + json.dumps(r.get("fastener") or {}))]
    csk_bad = [n for n in csk if n not in CSK_HOSTS]
    if csk_bad:
        fail.append(f"countersunk heads not in a metal / FR4 host: {csk_bad}")
    flex = [r["name"] for r in PARTS if re.search(r"hook|hák|klip|clip|snap", r["name"] + " " + (r.get("label_sk") or ""), re.I)]
    if flex or C.OBAL.get("DOOR_HOOK") is not None:
        fail.append(f"flexing features: {flex}, DOOR_HOOK {C.OBAL.get('DOOR_HOOK')}")
    mods, k13 = {}, {}
    for name, keys in (("ram", ["E2_insert_walls", "E3_roots", "P_print_table"]), ("pan", ["G_resin"]), ("obal", ["R", "O4"])):
        m = module_check(name)
        if m is None:
            mods[name] = "NO RESULT"; fail.append(f"module {name}: no valid result"); continue
        v = mod_verdicts(name, m); mods[name] = {k: v.get(k) for k in keys}
        if not all(v.get(k) for k in keys):
            fail.append(f"module {name} resin-rule verdicts {mods[name]}")
        k13[name] = (m.get("P", {}) or {}).get("k13") if name == "ram" else ((m.get("G_resin") or {}).get("k13") if name == "pan"
                                                                                else (m.get("R_resin") or {}).get("k13"))
    rec = {}
    for mod in ("obal", "ram"):
        for e in json.load(open(os.path.join(HERE, f"parts_{mod}.json")))["parts"]:
            if e.get("printed"):
                rec[e["name"]] = bool(e.get("print"))
    pan_print = bool(((module_check("pan") or {}).get("G_resin") or {}).get("status") == "PASS")
    no_rec = [r["name"] for r in printed if not rec.get(r["name"]) and not (r["module"] == "pan" and pan_print)]
    if no_rec:
        fail.append(f"printed parts without a print record (orientation / supports / drains): {no_rec}")
    return res("PASS" if not fail else "FAIL",
               f"{len(printed)} printed parts, all resin (no PETG / POM: {not petg}); {len(inserts)} inserts all bonded (no heat-set); countersunk "
               f"heads only in metal / FR4 ({ {n: CSK_HOSTS[n] for n in csk if n in CSK_HOSTS} }); no flexing feature (door hooks deleted); module "
               f"verdicts (insert walls, roots, print / support / cup / drain, slide fits) {mods}; print records missing: {no_rec}",
               failures=fail, module_verdicts=mods, module_k13=k13, countersunk=csk, notes=notes,
               rules="Z1 resin only; Z3.2 nothing flexes; Z3.3 roots (module root lists); Z3.4 inserts bonded, wall >= 1.6, engagement >= 3 / "
                     "thread-forming boss >= 2.5 d, engagement >= 2 d; Z3.5 no countersunk head on resin; Z3.6 slide fits + epoxy (module lists); "
                     "Z3.11 print strategy per part")


RUN.update(K12=K12, K13=K13)


# =====================================================================================================================
# main
# =====================================================================================================================
TITLES = {
    "K1": "valid closed solids / watertight STL", "K2": "no interference at rest (intended fits listed)",
    "K3": "moving clearances >= 1.0 (pan -90.3..90.3 x lift 0..20, front stack; J1 -155..155 vs the dummy hub)",
    "K4": "wall thickness (resin: structural 2.0 / local 1.2, declared exceptions)", "K5": "bought-part seats, centre distances, coaxial fasteners",
    "K6": "crank kinematics (stroke 20.0, dead centres), pan stop +-90, J1 stop", "K7": "assembly + service order, tool paths, T_stred lowering, D6 rows",
    "K8": "exterior fidelity (T3 shape, seams, no see-through from 26 viewpoints)", "K9": "real head / neck vs torso (Blender BVH), tilt table",
    "K10": "printability on the Saturn 4 Ultra 16K (size, orientation, supports, drains)", "K11": "mass + centre of gravity of the torso",
    "K12": "strength L1..L8 with the Z2 allowables (resin / epoxy / metal)", "K13": "resin rules (Z1, Z3)",
}


def main():
    say(f"== checks.py (rev. 2) {time.strftime('%Y-%m-%d %H:%M:%S')}  sections {' '.join(WANT)}  STL stamp {STAMP}  force {FORCE} ==")
    f = os.path.join(HERE, "checks.json")
    old = json.load(open(f)).get("checks", {}) if os.path.exists(f) else {}
    if old and json.load(open(f)).get("revision") != 2:
        old = {}
    out = {}
    need_mod = {"K3", "K4", "K5", "K6", "K7", "K8", "K10", "K12", "K13"}
    if need_mod & set(WANT) and not NO_MOD:
        start_module_checks()
    order = ["K1", "K2", "K11", "K9", "K3", "K6", "K4", "K5", "K7", "K8", "K10", "K12", "K13"]
    for k in order:
        if k in WANT and k in RUN:
            t = time.time()
            try:
                out[k] = RUN[k]()
            except Exception as e:
                out[k] = res("NOT RUN", f"the check raised {type(e).__name__}: {e}", traceback=traceback.format_exc()[-2500:])
            out[k]["time_s"] = round(time.time() - t, 1)
            say(f"{k} {out[k]['status']:8s} {out[k]['summary'][:500]}")
        elif k in old and old[k].get("stl_stamp") == STAMP and old[k].get("status") in ("PASS", "FAIL"):
            out[k] = old[k]
            say(f"{k} {out[k]['status']:8s} (kept from {old[k].get('generated')}, same STL set)")
        elif k in old:
            out[k] = res("NOT RUN", "stale: the STL set changed after this check last ran (" + str(old[k].get("generated")) + ", was " + str(old[k].get("status")) + ")")
        else:
            out[k] = res("NOT RUN", "not run yet")
        out[k]["title"] = TITLES[k]
    table = [dict(id=k, title=TITLES[k], status=out[k]["status"], summary=out[k]["summary"]) for k in SECTIONS]
    modsum = {}
    for name in ("ram", "pan", "obal"):
        st = os.path.join(WORK, f"mod_{name}.stamp"); fj = os.path.join(HERE, MODCHK[name][1])
        if not (os.path.exists(st) and os.path.exists(fj) and open(st).read().strip() == STAMP):
            modsum[name] = dict(valid_for_stl_set=False, note="no result stamped for the STL files on disk")
            continue
        v = mod_verdicts(name, json.load(open(fj)))
        modsum[name] = dict(valid_for_stl_set=True, verdicts=v, all_ok=bool(v) and all(v.values()), not_ok=[k for k, q in v.items() if not q])
    doc = dict(project="NOVA mini - T4 torso", revision=2, generated=time.strftime("%Y-%m-%d %H:%M:%S"), stl_stamp=STAMP, n_parts=len(PARTS),
               all_pass=all(out[k]["status"] == "PASS" for k in SECTIONS), table=table,
               module_check_notes=_MOD_NOTE, module_prechecks=modsum, integrator_rev2_changes=getattr(C, "INTEG2", {}).get("changes", []), checks=out)
    json.dump(doc, open(f, "w"), indent=1, ensure_ascii=False, default=lambda o: o.item() if hasattr(o, "item") else str(o))
    say("   module pre-checks: " + "; ".join(f"{k}: " + ("stale" if not v["valid_for_stl_set"] else "all ok" if v["all_ok"] else f"NOT OK {v['not_ok']}")
                                              for k, v in modsum.items()))
    say("== " + "  ".join(f"{k}:{out[k]['status']}" for k in SECTIONS) + f"  ({time.time() - T0:.0f} s) ==")
    return 0 if doc["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
