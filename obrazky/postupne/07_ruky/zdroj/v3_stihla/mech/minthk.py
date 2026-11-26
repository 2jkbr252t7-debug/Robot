"""R3/mech/minthk.py - minimum arm thickness at the joint for each packaging option, using the armgeo kt stand-ins
(inner face fixed, thinner from the outside).  Coarse scan kt 0.50..1.00 then bisection on the fit flag.
Writes out/minthk.json.   usage: /opt/venv/cad/bin/python minthk.py [options]"""
import sys, os, json, time
sys.dont_write_bytecode = True
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import fit, parts as PT
mod = fit.load_variant(os.path.join(HERE, "standin.py"))
OPTS = sys.argv[1].split(",") if len(sys.argv) > 1 else list(PT.options())
ALL = np.concatenate([p.surface(0.5) for o in PT.options().values() for p in o["parts"] if p.pebble and p.role != "torso"])
cache = {}


def run(kt):
    kt = round(kt, 4)
    if kt not in cache:
        vid = "kt%.2f" % (kt * 100)
        arm = fit.Arm(mod, vid, -1.0)
        L = arm.to_local(ALL)
        arm.build_cloud(L[:, 2].min() - 8.0, L[:, 2].max() + 8.0)
        cache[kt] = {o: fit.check(mod, vid, o, -1.0, True, arm=arm) for o in OPTS}
    return cache[kt]


t0 = time.time()
scan = np.round(np.arange(0.50, 1.0001, 0.05), 3)
res = {o: dict(scan=[]) for o in OPTS}
for kt in scan:
    R = run(kt)
    for o in OPTS:
        r = R[o]
        res[o]["scan"].append(dict(kt=float(kt), thickness=round(r["thickness"], 2), fits=r["fits"], outer=r["margin_outer"]["margin"],
                                   outer_at=r["margin_outer"]["part"], inner=r["margin_inner"]["margin"], pairs=r["margin_pairs"]["margin"]))
    print(f"kt {kt:.2f} " + "  ".join(f"{o}:{'Y' if R[o]['fits'] else 'n'}{R[o]['margin_outer']['margin']:+.2f}" for o in OPTS),
          f"{time.time()-t0:.0f}s", flush=True)
for o in OPTS:
    S = res[o]["scan"]
    fitsk = [s["kt"] for s in S if s["fits"]]
    if not fitsk:
        res[o]["kt_min"] = None; continue
    k_hi = min(fitsk)
    lower = [s["kt"] for s in S if s["kt"] < k_hi]
    k_lo = max(lower) if lower else None
    if k_lo is not None:
        for _ in range(6):
            km = round(0.5 * (k_lo + k_hi), 4)
            if run(km)[o]["fits"]:
                k_hi = km
            else:
                k_lo = km
    r = run(k_hi)[o]
    res[o].update(kt_min=k_hi, kt_fail=k_lo, thickness_min=round(r["thickness"], 2),
                  thickness_fail=None if k_lo is None else round(run(k_lo)[o]["thickness"], 2),
                  governing_at_min=r["margin_outer"], inner_at_min=r["margin_inner"], fits_all_thicker=all(s["fits"] for s in S if s["kt"] >= k_hi))
    print(o, "min kt", k_hi, "thickness", res[o]["thickness_min"], "governing", r["margin_outer"], flush=True)
json.dump(res, open(os.path.join(HERE, "out", "minthk.json"), "w"), indent=1)
print("done %.0fs" % (time.time() - t0))
