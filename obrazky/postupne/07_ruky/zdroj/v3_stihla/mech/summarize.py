"""R3/mech/summarize.py - collect minthk.json, envelope.json, calc.json and the stand-in fit reports into out/summary.json
(machine-readable; the image agent and the parent read this, no prose report)."""
import json, os, sys
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import parts as PT
O = os.path.join(HERE, "out")
mt = json.load(open(os.path.join(O, "minthk.json")))
env = json.load(open(os.path.join(O, "envelope.json")))["envelope"]
calc = json.load(open(os.path.join(O, "calc.json")))
fits = {}
for v in ("kt100", "kt085", "kt070", "kt057", "tvar_0", "tvar_A", "tvar_B", "tvar_C"):
    p = os.path.join(O, f"fit_{v}.json")
    if os.path.exists(p):
        for r in json.load(open(p)):
            fits.setdefault(r["option"], {})[v] = dict(thickness=round(r["thickness"], 2), fits=r["fits"], outer=r["margin_outer"],
                                                      inner=r["margin_inner"], pairs=r["margin_pairs"], stop=r.get("stop"))


def compact(e):
    """merge consecutive radii with the same requirement into bands"""
    out = []
    for row in e:
        x = row["x_outer_surface_min"]
        if x is None:
            continue
        if out and abs(out[-1]["x_outer_min"] - x) < 1e-6 and out[-1]["by"] == row["by"]:
            out[-1]["r_to"] = row["r"]
        else:
            out.append(dict(r_from=row["r"], r_to=row["r"], x_outer_min=x, by=row["by"]))
    return out


S = dict(frame="B: mm, Z up, front -Y, robot LEFT +X, left arm at rest, arm dx -1.0; right arm = mirror x -> -x",
         inner_skin_on_axis_x=49.645, options={})
for oid, o in PT.options().items():
    S["options"][oid] = dict(title=o["title"], envelope_bands=compact(env[oid]), min_thickness=mt.get(oid, {}),
                             standin_fits=fits.get(oid, {}), parts=[p.to_dict() for p in o["parts"]])
S["clutch"] = calc["clutch"]; S["strength"] = calc["strength"]; S["M3_torso_room"] = calc["M3_torso_room"]; S["M3_needs"] = calc["M3_needs"]
S["magnets"] = calc["magnets"]
json.dump(S, open(os.path.join(O, "summary.json"), "w"), indent=1, ensure_ascii=False)
for oid, v in S["options"].items():
    m = v["min_thickness"]
    print(oid, v["title"], "| min thickness", m.get("thickness_min"), "(fails at", m.get("thickness_fail"), ") governing",
          (m.get("governing_at_min") or {}).get("part"), (m.get("governing_at_min") or {}).get("at"))
    for b in v["envelope_bands"]:
        print("    r %5.2f..%5.2f  x_outer >= %6.2f  (%s)" % (b["r_from"], b["r_to"], b["x_outer_min"], b["by"]))
