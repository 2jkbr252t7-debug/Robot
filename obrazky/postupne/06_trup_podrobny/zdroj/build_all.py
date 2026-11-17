#!/opt/venv/cad/bin/python
"""NOVA mini - T4 torso: build every module and export the deliverables.

    /opt/venv/cad/bin/python build_all.py [--rebuild] [--no-step] [--only obal,ram,pan] [--annotate]

    -> stl/<name>.stl      binary STL, ABSOLUTE chord deflection 0.01 mm (t4_obal.export_abs)
       step/<name>.step    only when the file stays below 12 MB (loft-derived parts: step = null, oversized file deleted)
       parts.json          one record per part: name, module, group (T / P / L / Z), mat, printed, label_sk, valid, n_solids,
                           volume (OCC), volume_mesh (from the written STL), bbox, cog, mass_g, stl{}, step, watertight
       parts_<module>.json the per-module files are refreshed with the new export records (their other keys are kept)

Mass: printed parts = STL volume x density (resin 1.15, PETG 1.27, POM 1.41 g/cm3); bought parts = datasheet mass given by
the module ("mass"), otherwise volume x density of the material (brass 8.5, steel 7.85, magnet 7.5, PTFE 2.2 ...).
"""
from __future__ import annotations
import os, sys, json, time, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
T0 = time.time()
import t4_common as C                                   # noqa: E402

MODULES = ("obal", "ram", "pan")


def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def build_module(mod, rebuild=False):
    """(registry, module object)"""
    if mod == "obal":
        import t4_obal as M
        if rebuild:
            import glob
            for f in glob.glob(os.path.join(C.CACHE, f"obal_{M.VER}_*.brep")):
                os.remove(f)
        return M.build(), M
    if mod == "ram":
        import t4_ram as M
        return M.build(rebuild), M
    import t4_pan as M
    return M.build(rebuild), M


def annotate():
    """write the integrator's change list and the modules' current deviation lists into parts.json / parts_<module>.json"""
    import importlib
    pj = os.path.join(HERE, "parts.json")
    doc = json.load(open(pj))
    doc["integrator_changes"] = C.INTEG["changes"]
    json.dump(doc, open(pj, "w"), indent=1, ensure_ascii=False)
    for mod in MODULES:
        mj = os.path.join(HERE, f"parts_{mod}.json")
        if not os.path.exists(mj):
            continue
        md = json.load(open(mj))
        M = importlib.import_module(f"t4_{mod}")
        dev = getattr(M, "DEVIATIONS", None)
        if dev:                                                   # obal / ram keep their list in the module source
            md["deviations"] = dev
        md["integrator_changes"] = [c for c in C.INTEG["changes"] if f"t4_{mod}" in c or f"{mod.upper()}[" in c or c.startswith(("export", "DENS"))]
        json.dump(md, open(mj, "w"), indent=1, ensure_ascii=False)


def main(argv):
    if "--annotate" in argv:
        annotate()
        print("annotated parts.json and the module files")
        return 0
    import t4_obal as O
    rebuild = "--rebuild" in argv
    do_step = "--no-step" not in argv
    only = MODULES
    if "--only" in argv:
        only = tuple(argv[argv.index("--only") + 1].split(","))
    pj = os.path.join(HERE, "parts.json")
    old = json.load(open(pj)) if os.path.exists(pj) else {}
    old_parts = {r["name"]: r for r in old.get("parts", [])}
    recs, bad, seen = [], [], {}
    for mod in MODULES:
        if mod not in only:
            recs += [r for r in old_parts.values() if r.get("module") == mod]
            continue
        t = time.time()
        reg, M = build_module(mod, rebuild)
        print(f"== {mod}: {len(reg)} parts built in {time.time() - t:.1f} s", flush=True)
        exp = {}
        if hasattr(M, "expected_bbox"):
            exp = {k: list(v) for k, v in M.expected_bbox().items()}
        elif hasattr(M, "BBOX_EXPECT"):
            exp = {k: list(v) for k, v in M.BBOX_EXPECT.items()}
        mj = os.path.join(HERE, f"parts_{mod}.json")
        mdoc = json.load(open(mj)) if os.path.exists(mj) else dict(module=mod, parts=[])
        mrec = {r["name"]: r for r in mdoc.get("parts", [])}
        out_mod = []
        for name, p in reg.items():
            assert name not in seen, f"part name {name} is used by {seen[name]} and {mod}"
            seen[name] = mod
            t1 = time.time()
            rec = O.export_abs(name, p, HERE, do_step=do_step)
            rec["module"] = mod
            if name in exp:
                rec["bbox_expected"] = exp[name]
                rec["bbox_ok"] = all(e is None or abs(a - e) <= 0.06 for a, e in zip(rec["bbox"], exp[name]))
                rec["ok"] = bool(rec["ok"] and rec["bbox_ok"])
            rec["stl"]["md5"] = md5(os.path.join(HERE, "stl", name + ".stl"))
            for k in ("source", "assembly_step", "assembly_dir", "fastener"):          # module knowledge kept in parts.json
                if k in mrec.get(name, {}):
                    rec[k] = mrec[name][k]
                elif k in p:
                    rec[k] = p[k]
            rec["export_s"] = round(time.time() - t1, 1)
            if not rec["ok"]:
                bad.append(name)
            recs.append(rec)
            m = dict(mrec.get(name, {})); m.update(rec); out_mod.append(m)
            b = rec["bbox"]
            print(f"{name:22s} {rec['group']} {rec['mat']:11s} {'ok ' if rec['ok'] else 'NOT'} vol {rec['volume_mesh']:10.1f} "
                  f"mass {str(rec['mass_g']):>7s} tris {rec['stl']['tris']:7d} step {'yes' if rec['step'] else '-':3s} "
                  f"{b[0]:7.2f}..{b[1]:6.2f} / {b[2]:7.2f}..{b[3]:6.2f} / {b[4]:7.2f}..{b[5]:6.2f}", flush=True)
        # stale exports of parts the module no longer has
        for n in [n for n in mrec if n not in reg]:
            for sub, ext in (("stl", ".stl"), ("step", ".step")):
                f = os.path.join(HERE, sub, n + ext)
                if os.path.exists(f):
                    os.remove(f); print("removed stale", f)
        mdoc["parts"] = out_mod
        mdoc["n_parts"] = len(out_mod)
        mdoc["all_ok"] = all(r["ok"] for r in out_mod); mdoc["not_ok"] = [r["name"] for r in out_mod if not r["ok"]]
        mdoc["exported_by"] = "build_all.py " + time.strftime("%Y-%m-%d %H:%M:%S")
        json.dump(mdoc, open(mj, "w"), indent=1, ensure_ascii=False)
    # files in stl/ and step/ that belong to no part
    names = {r["name"] for r in recs}
    orphans = []
    for sub, ext in (("stl", ".stl"), ("step", ".step")):
        for f in sorted(os.listdir(os.path.join(HERE, sub))):
            if f.endswith(ext) and f[:-len(ext)] not in names:
                orphans.append(f"{sub}/{f}")
    step_big = [f for f in os.listdir(os.path.join(HERE, "step")) if os.path.getsize(os.path.join(HERE, "step", f)) > C.INTEG["STEP_MAX_MB"] * 1e6]
    mass = {}
    for r in recs:
        g = r["group"]; k = "printed" if r["printed"] else "bought"
        mass.setdefault(g, dict(printed=0.0, bought=0.0, n=0, no_mass=[]))
        if r["mass_g"] is None:
            mass[g]["no_mass"].append(r["name"])
        else:
            mass[g][k] += r["mass_g"]
        mass[g]["n"] += 1
    for g in mass:
        mass[g]["printed"] = round(mass[g]["printed"], 2); mass[g]["bought"] = round(mass[g]["bought"], 2)
        mass[g]["total"] = round(mass[g]["printed"] + mass[g]["bought"], 2)
    doc = dict(project="NOVA mini - T4 torso", generated=time.strftime("%Y-%m-%d %H:%M:%S"), frame="B frame: mm, Z up, front -Y, robot left +X, "
               "torso top z +4; rest pose (lift 0, pan 0, J1 0)", n_parts=len(recs), n_printed=sum(r["printed"] for r in recs),
               all_ok=not bad, not_ok=bad,
               densities_g_cm3={k: (None if v is None else round(v * 1e3, 3)) for k, v in C.DENS.items()},
               stl=dict(deflection_mm=O.STL_LIN, angular_rad=O.STL_ANG, note="absolute chord deflection"),
               step_rule=f"STEP written only below {C.INTEG['STEP_MAX_MB']:.0f} MB; step = null for loft-derived parts",
               step_null=[r["name"] for r in recs if not r.get("step")], step_over_limit_on_disk=step_big, orphan_files=orphans,
               mass_by_group_g=mass, parts=recs)
    json.dump(doc, open(pj, "w"), indent=1, ensure_ascii=False)
    annotate()
    print(f"\n{len(recs)} parts ({doc['n_printed']} printed), not ok: {bad}; STEP null: {doc['step_null']}; orphans: {orphans}; "
          f"STEP over limit on disk: {step_big}")
    print("mass by group (g):", json.dumps(mass))
    print(f"total {time.time() - T0:.1f} s")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
