#!/opt/venv/cad/bin/python
"""fe_sachta/run_fe.py - ONE entry script of the reproducible FE check of the rotating well (T4 rev. 3, plan acceptance).

    /opt/venv/cad/bin/python fe_sachta/run_fe.py                 mesh the CURRENT stl/P_sachta + koleso_pan + P_drziak_serva (h 0.4),
                                                                 run the acceptance cases + the two fail-safe cases, write results.json
    ... run_fe.py --cases L3_twist_ccw,L1_lift20c --tag try1 --h 0.6     subset / coarse lattice into res/try1 (results_try1.json)
    ... run_fe.py --collect-only                                 rebuild results.json from the case files in res/main
    ... run_fe.py --validate                                     rev. 2 STL (rev3_backup/stl) with the rev. 2 joint description:
                                                                 L1_lift20c + L3_twist_ccw + L8_stop_p90 vs sachta_a/results_v4.json -> validation.json

Acceptance cases (T4_rev3_sachta_plan.md): L1 at lift 0 and 20; L2 at lift 0 (chain and landed) / 10 / 20; L3 both directions;
L8 into both stops.  Fail-safe (R3-2): L1 at lift 0 / 20 with the gear bond failed completely (gear left out).
Method: femodel.py (model, contact solver), cases.py (loads, supports, joint), post.py (spots, averaging 0.4 mm x 1.04, bond 0.6 mm),
fe_design.py + design.json (joint description written by t4_pan.py).  One process per case, --jobs in parallel (2 x 4.8 GB at h 0.4).
results.json: rows = (spot, part, case, cls, stress, allowable, ok, at) + per-spot worst case + case convergence / reactions."""
import os, sys, json, time, argparse, subprocess, hashlib
HERE = os.path.dirname(os.path.abspath(__file__)); T4 = os.path.dirname(HERE)
PY = sys.executable
sys.path.insert(0, HERE)
FAILSAFE = ["L1_lift20c_nobond", "L1_lift0_nobond"]
ACCEPT = ["L1_lift0", "L1_lift20c", "L2_lift0_chain", "L2_lift0_landed", "L2_lift10", "L2_lift20c", "L3_twist_ccw", "L3_twist_cw", "L8_stop_p90", "L8_stop_m90"]
PARTS = ("P_sachta", "koleso_pan", "P_drziak_serva")


def stamp(stl_dir):
    m = hashlib.md5()
    for n in PARTS:
        m.update(open(os.path.join(stl_dir, n + ".stl"), "rb").read())
    return m.hexdigest()[:12]


def run_cases(stl, h, design, out, cases, jobs, force=False, extra=()):
    os.makedirs(out, exist_ok=True); st = stamp(stl)
    todo = []
    for c in cases:
        f = os.path.join(out, c + ".json")
        if not force and os.path.exists(f):
            try:
                d = json.load(open(f))
                if d.get("stl_stamp") == st and abs(d.get("h", 0) - h) < 1e-9 and d.get("rows") is not None and d["solver"]["converged"] and d.get("equilibrated"):
                    print(f"  {c}: kept (same STL stamp {st}, converged)"); continue
            except Exception:
                pass
        todo.append(c)
    if not todo:
        return
    # caches (occupancy, surface points) once, in this process, so that the parallel case processes only read them
    subprocess.run([PY, "-c", "import sys; sys.path.insert(0, %r); import femodel as FM, post; FM.occupancies(%r, %r, %r); "
                              "[post.surface_points(%r, n, %r) for n in ('P_sachta', 'P_drziak_serva')]" % (HERE, stl, h, os.path.join(HERE, "cache"), stl, os.path.join(HERE, "cache"))],
                   check=True)
    running = []; t0 = time.time()
    while todo or running:
        while todo and len(running) < jobs:
            c = todo.pop(0)
            lg = open(os.path.join(out, c + ".log"), "w")
            p = subprocess.Popen(["nice", "-n", "3", PY, "-u", os.path.join(HERE, "cases.py"), "--stl", stl, "--h", str(h), "--design", design, "--out", out, *extra, c],
                                 stdout=lg, stderr=subprocess.STDOUT, cwd=HERE)
            running.append((c, p, lg)); print(f"  started {c} ({time.time() - t0:.0f} s)", flush=True)
            time.sleep(45 if h < 0.5 else 5)                    # stagger the AMG set-up memory peaks
        for it in list(running):
            c, p, lg = it
            if p.poll() is not None:
                lg.close(); running.remove(it)
                print(f"  finished {c}: exit {p.returncode} ({time.time() - t0:.0f} s)", flush=True)
        time.sleep(3)


def collect(stl, h, design_name, out, cases, target):
    rows = []; info = {}; missing = []
    st = stamp(stl)
    for c in cases:
        f = os.path.join(out, c + ".json")
        if not os.path.exists(f):
            missing.append(c); continue
        d = json.load(open(f))
        if d.get("stl_stamp") != st or d.get("rows") is None or abs(d.get("h", 0) - h) > 1e-9 or not d.get("equilibrated", False):
            missing.append(c); continue              # a case whose applied loads are not in equilibrium is NOT a result
        sp = d["spec"]
        for rw in d["rows"]:                         # LD5: capacity of every row that fails = load at which it reaches its allowable
            rw.setdefault("kind", "structure")
            if not rw["ok"] and rw["stress"] > 0:
                k = rw["allowable"] / rw["stress"]
                if "F" in sp:
                    rw["capacity_N"] = round(abs(sp["F"]) * k, 1); rw["ref_load"] = f"{abs(sp['F']):.0f} N on the head ({'up' if sp['F'] > 0 else 'down'})"
                else:
                    rw["capacity_Nmm"] = round(abs(sp["T"]) * k, 0); rw["ref_load"] = f"{abs(sp['T']):.0f} N.mm about the pan axis"
        rows += d["rows"]
        info[c] = dict(cls=d["spec"]["cls"], converged=d["solver"]["converged"], rel_res=d["solver"]["rel_res"], outer=d["solver"]["outer"],
                       cg=d["solver"]["cg_total"], seconds=d["solver"]["seconds"], reactions={k: dict(F=v["F"], n_active=v["n_active"]) for k, v in d["reactions"].items()},
                       reaction_sum=d["reaction_sum"], pair_forces_on_pocket=d["pair_forces_on_pocket"], bond=d.get("bond"), max_disp=d["max_disp"],
                       uz_axis=d.get("uz_axis"), disp=d.get("disp"), applied=[l for l in d["log"] if "F_applied" in l], loads=[l for l in d["log"] if "F_applied" not in l],
                       nodes=d["nodes"], design=d.get("design"), nobond=d.get("nobond"), equilibrated=d.get("equilibrated"))
    acc = [r for r in rows if r["cls"] != "failsafe"]
    spots = {}
    for r in acc:
        k = (r["part"], r["spot"]); u = r["stress"] / r["allowable"]
        if k not in spots or u > spots[k]["util"]:
            spots[k] = dict(spot=r["spot"], part=r["part"], case=r["case"], cls=r["cls"], kind=r.get("kind"), stress=r["stress"], allowable=r["allowable"],
                            ok=r["ok"], util=round(u, 3), at=r["at"], **{q: r[q] for q in ("capacity_N", "capacity_Nmm", "ref_load", "contact_zone_peak",
                                                                                         "force_N", "area_mm2", "edge_peak_06") if r.get(q) is not None})
    fs = {}
    for r in rows:
        if r["cls"] == "failsafe":
            k = r["spot"]
            if k not in fs or r["stress"] > fs[k]["stress"]:
                fs[k] = dict(spot=r["spot"], part=r["part"], case=r["case"], stress=r["stress"], allowable=r["allowable"], ok=r["ok"], at=r["at"])
    res = dict(generated=time.strftime("%Y-%m-%d %H:%M:%S"), stl_dir=os.path.relpath(stl, T4), stl_stamp=st, h=h, design=design_name,
               cases_requested=cases, cases_missing=missing, cases=info,
               all_converged=bool(info) and all(v["converged"] for v in info.values()),
               all_ok=bool(acc) and not missing and all(r["ok"] for r in acc),
               n_rows=len(rows), n_fail=sum(not r["ok"] for r in acc),
               worst_per_spot=sorted(spots.values(), key=lambda v: -v["util"]), failsafe_worst=sorted(fs.values(), key=lambda v: -v["stress"]),
               rows=rows,
               method=dict(fe="own voxel / finite-cell hexahedra with incompatible modes on the STL (sachta_a/fe3d.py, validated 2-4 % low in plain bending -> x 1.04)",
                           joint="positive location only (Z3.7): F10 pads bilateral in y, rail / pad faces compression only, tongue faces z and tongue ends x compression only, "
                                 "F10 dowel x + z; no friction", journal="compression-only gap springs, radial play 0.145", pivot="gear bore on the taped T_cap (radial)",
                           axial="retention washer: compression-only stop on the hub lip of the well (rev. 3) / on the gear top (rev. 2); PTFE thrust washer under the gear",
                           upper_guide="lift 20: collar-disc opening at z +3 (sachta_a fe_cases_v3); lift 0 / 10: strip tops",
                           collar="the glued collar disc of variant B (golier_kotuc, r 26.5, 6 thick) is part of the model up to z +0.5, tied to the well on "
                                  "the glue land r >= 24 (sachta_a: guide forces only, no stiffness - used for the rev. 2 validation with --no-collar)", stop="stop pin = compression-only line contact at r 30",
                           bond="nodes merged inside the root circle r <= 13.35 (rigid epoxy layer); peel / shear = nodal force / h^2 averaged over 0.6 mm",
                           averaging="max principal stress on the true surface averaged over 0.4 mm, x 1.04", E="resin 1600 MPa nu 0.38, brass 100 GPa",
                           contact_zones="LD1: structure rows use only surface points >= 1.0 mm (+ h / 2) away from every node of an ACTIVE joint contact "
                                         "(module pairs, dowel, stop line); the mesh-dependent peak inside the zone is kept as contact_zone_peak (information); "
                                         "every contact has its own row: nominal bearing pressure = pair force / engaged area vs the class allowable",
                           classes="LD2: L1 / L2 at lift 0 normal 8.5; L1 / L2 at lift > 2 abuse 12.9 (normal use there = 1/3 of the load: 4.3 <= 8.5 by scaling); "
                                   "L8 into a hard stop = fault = abuse 12.9; L3 abuse 12.9",
                           bond_acceptance="LD1: nominal average shear and tension <= 2.7 normal / 4.0 abuse; edge peaks information only",
                           allowables="T4_zivica Z2: normal 8.5 (L1, L2, L8), abuse 12.9 (L3), unfilleted notch 4.3 / 6.45, bond 2.7; fail-safe rows against the "
                                      "lower-bound strength 25.8 (not a design case)",
                           L2_lift10="vertical pin force 30 N in full, servo torque about x capped at the MG90S stall 216 N.mm (beyond it the head sinks)"))
    json.dump(res, open(target, "w"), indent=1)
    return res


def table(res, n=40):
    print(f"\n== {res['stl_dir']} stamp {res['stl_stamp']} h {res['h']} design {res['design']}: {res['n_rows']} rows, {res['n_fail']} FAIL, "
          f"missing {res['cases_missing']}, all converged {res['all_converged']}, ALL OK {res['all_ok']}")
    for c, v in res["cases"].items():
        b = v.get("bond") or {}
        print(f"   {c:20s} conv {v['converged']} res {v['rel_res']:.1e} outer {v['outer']:2d} cg {v['cg']:4d} {v['seconds']:6.0f} s  max|u| {v['max_disp']}  "
              f"bond peel {b.get('peel_avg06')} shear {b.get('shear_avg06')}")
    for s in res["worst_per_spot"][:n]:
        print(f"   {s['spot'][:74]:74s} {s['stress']:7.2f} / {s['allowable']:5.2f}  {'ok  ' if s['ok'] else 'FAIL'} {s['case']:16s} at {s['at']}"
              + (f"  cz-peak {s['contact_zone_peak']}" if s.get("contact_zone_peak") else "") + (f"  cap {s['capacity_N']} N" if s.get("capacity_N") else ""))
    for s in res["failsafe_worst"][:6]:
        print(f"   [fail-safe, bond failed] {s['spot']:44s} {s['stress']:7.2f} / {s['allowable']:5.2f}  {s['case']}")


VAL_MAP = [  # (my spot, sachta_a hot-spot name)
    ("lens: hub ring <-> front wall junction", "lens: hub ring <-> front wall (|x|<=7)"),
    ("+X end-window top corners", "+X end-window top corners (z -15), SHARP"),
    ("back-window corners (top + sill / jamb)", "back-window corners (x -6.5/-20.9, z -10.9 and -40.9), SHARP"),
    ("slim corner arcs 1.34 (z -40.2..-10.8)", "corner arcs, 1.34 / 1.20 (all four, z>-40.9)"),
    ("slim corner arcs in the journal band zone", "corner arcs in the band zone (1.20, z>-10.8)"),
    ("rail / ledge of the lift module (lips, groove, roots)", "rail lips + groove (y > 13, z < -33.6)"),
    ("back floor (r > 12.8)", "back floor (z<=-40.5, y>3, r>12.8)"),
    ("back floor <-> back wall junction R1.0", "back floor <-> back wall junction R1.0"),
    ("-X end wall", "-X end wall"), ("journal band (r > 25.9)", "journal band (r>25.9, z -10.1..-2.9)"),
    ("drum shroud + lip + web (z < -41.9)", "drum shroud + lip (z < -41.9)"),
    ("thin floor 0.95 zone (FFC groove)", "thin floor 0.95 zone (x 15-23.5, y 3.3-7.2)"),
]


def validate(h, jobs):
    stl = os.path.join(T4, "rev3_backup", "stl"); out = os.path.join(HERE, "res", "val_rev2")
    cases = ["L1_lift20c", "L3_twist_ccw", "L8_stop_p90"]
    run_cases(stl, h, "rev2", out, cases, jobs, extra=("--no-collar",))
    res = collect(stl, h, "rev2", out, cases, os.path.join(HERE, "results_val_rev2.json"))
    ref = json.load(open(os.path.join(T4, "sachta_a", "results_v4.json")))
    comp = {}
    for c in cases:
        if c not in res["cases"] or c not in ref:
            continue
        mine = {r["spot"]: r for r in res["rows"] if r["case"] == c}; R = ref[c]; v = res["cases"][c]
        piv = (v["reactions"].get("pivot") or {}).get("F", [0, 0, 0]); jr = (v["reactions"].get("journal") or {}).get("F", [0, 0, 0])
        rows = [dict(quantity="pivot radial force N", mine=round((piv[0] ** 2 + piv[1] ** 2) ** 0.5, 1), sachta_a=R["pivot_radial_N"]),
                dict(quantity="journal force N", mine=round((jr[0] ** 2 + jr[1] ** 2) ** 0.5, 1), sachta_a=R["journal_N"]),
                dict(quantity="bond peel at the edge, 0.6 mm average MPa", mine=(v.get("bond") or {}).get("peel_avg06"), sachta_a=R["bond"]["peel_edge_avg06"]),
                dict(quantity="bond shear max, 0.6 mm average MPa", mine=(v.get("bond") or {}).get("shear_avg06"), sachta_a=R["bond"]["shear_max_avg"]),
                dict(quantity="bond tension resultant N", mine=(v.get("bond") or {}).get("tension_sum"), sachta_a=R["bond"]["tension_sum"]),
                dict(quantity="max |u| mm", mine=v["max_disp"], sachta_a=R["max_disp"])]
        for a, b in VAL_MAP:
            if a in mine and b in R["hotspots"]:
                rows.append(dict(quantity=f"s1 (0.4 avg x 1.04) MPa: {a}", mine=mine[a]["stress"], sachta_a=R["hotspots"][b]["s1_avg"], at_mine=mine[a]["at"], at_ref=R["hotspots"][b]["at"]))
        for r in rows:
            if isinstance(r["mine"], (int, float)) and isinstance(r["sachta_a"], (int, float)) and abs(r["sachta_a"]) > 1e-9:
                r["ratio"] = round(r["mine"] / r["sachta_a"], 2)
        comp[c] = dict(converged=v["converged"], sachta_a_iterations=R["iterations"], sachta_a_last_changed=R["last_changed"], rows=rows)
    note = ("rev. 2 STL (rev3_backup/stl), rev. 2 joint description, h 0.4.  Differences to sachta_a expected by construction: (1) every case is converged here "
            "(sachta_a stopped with 261-379 contact nodes still changing; L8 after 1 iteration with all contacts closed); (2) spot regions are slightly wider; "
            "(3) L8: the stop pin is a compression-only line contact at r 30 (sachta_a: bilateral springs over the whole lug face).")
    json.dump(dict(generated=time.strftime("%Y-%m-%d %H:%M:%S"), note=note, comparison=comp), open(os.path.join(HERE, "validation.json"), "w"), indent=1)
    for c, v in comp.items():
        print(f"\n== validation {c} (converged {v['converged']})")
        for r in v["rows"]:
            print(f"   {r['quantity'][:78]:78s} mine {r['mine']!s:>8} sachta_a {r['sachta_a']!s:>8} ratio {r.get('ratio')}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stl", default=os.path.join(T4, "stl")); ap.add_argument("--h", type=float, default=0.4)
    ap.add_argument("--design", default="current"); ap.add_argument("--tag", default="main"); ap.add_argument("--jobs", type=int, default=2)
    ap.add_argument("--cases", default=None); ap.add_argument("--collect-only", action="store_true"); ap.add_argument("--validate", action="store_true")
    ap.add_argument("--force", action="store_true"); ap.add_argument("--no-failsafe", action="store_true")
    a = ap.parse_args()
    if a.validate:
        validate(a.h, a.jobs); return 0
    stl = os.path.abspath(a.stl)
    cases = a.cases.split(",") if a.cases else ACCEPT + ([] if a.no_failsafe else FAILSAFE)
    out = os.path.join(HERE, "res", a.tag)
    dname = a.design
    if a.design == "current":
        dj = os.path.join(HERE, "design.json")
        dname = json.load(open(dj)).get("name", "current") if os.path.exists(dj) else "rev2"
    if not a.collect_only:
        run_cases(stl, a.h, a.design if a.design != "current" else os.path.join(HERE, "design.json"), out, cases, a.jobs, a.force)
    target = os.path.join(HERE, "results.json" if a.tag == "main" else f"results_{a.tag}.json")
    res = collect(stl, a.h, dname, out, cases, target)
    table(res)
    return 0 if res["all_ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
