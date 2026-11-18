"""collect res/*_post.json + *_bond.json + the case logs into one table (summary.json, printed)"""
import json, glob, os
rows = {}
for f in sorted(glob.glob("res/*_post.json")):
    d = json.load(open(f)); c = d["case"]
    log = json.load(open(f"res/{c}.json"))
    b = json.load(open(f"res/{c}_bond.json")) if os.path.exists(f"res/{c}_bond.json") else {}
    reac = [l for l in log["log"] if "reactions" in l][0]["reactions"]
    rows[c] = dict(regions={k: (v["s1_avg04"], v["s1_raw"], v["at"], v["s3_avg04"]) for k, v in d["regions"].items()},
                   bond=dict(peel_tips_avg=d["bond"]["peel_max_avg"], shear_avg=d["bond"]["shear_max_avg"], peel_root_circle=b.get("peel_root_circle_avg0.6"),
                             tension_sum=b.get("tension_sum"), torque=d["bond"]["torque_about_z"]),
                   pocket_if=d["pocket_if"], reactions={k: v["F"] for k, v in reac.items()}, max_disp=d["max_disp"])
json.dump(rows, open("summary.json", "w"), indent=1)
for c, r in rows.items():
    print(f"\n=== {c}  (max |u| {r['max_disp']} mm)  reactions {r['reactions']}")
    for k, v in sorted(r["regions"].items(), key=lambda kv: -kv[1][0]):
        print(f"   {k:40s} s1 avg0.4 {v[0]:7.2f}  raw {v[1]:7.2f}  at {v[2]}  s3 {v[3]:7.2f}")
    print("   bond", r["bond"], "pocket_if", r["pocket_if"])
