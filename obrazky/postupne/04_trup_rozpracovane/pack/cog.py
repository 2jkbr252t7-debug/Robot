"""mass table (grouped) + CoG + tipping for the final layout; updates gaps_cog.json mass/tipping fields"""
import sys, json
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T1")
import t1lib as T
K2 = "/tmp/claude-0/gapwf/fin/T1/pack"
L = T.Layout(f"{K2}/layout.json")
M, c, rows = L.cog({})
grp = {cc["name"]: cc["group"] for cc in L.comps}
by = {}
for n, m in rows:
    g = grp[n]
    key = {"B": "base", "T": "torso", "P": "pan stage", "L": "lift (neck+foot)", "H": "head", "AR": "arm R",
           "AL": "arm L"}[g]
    by.setdefault(key, 0.0)
    by[key] += m
POSES = {"rest": {}, "awake": {"lift": 12.5, "tilt": 10, "pan": 30, "armR": 60, "armL": -20},
         "arms_fwd_head_down": {"armR": 100, "armL": 100, "lift": 20, "tilt": 40},
         "j1_90_reach": {"j1": 90, "pan": 85, "lift": 20, "tilt": 40, "armR": 90, "armL": 90},
         "j1_45_reach": {"j1": 45, "pan": 85, "lift": 20, "tilt": 40, "armR": 100, "armL": 100},
         "arms_back": {"armR": -45, "armL": -45, "lift": 20, "tilt": -40}}
tip = {k: {"pose": p, **L.tipping(p, accel_g=0.15)} for k, p in POSES.items()}
worst = min(tip.values(), key=lambda t: t["margin_at_accel_mm"])
gc = json.load(open(f"{K2}/gaps_cog.json"))
gc["mass_g"] = round(M, 1)
gc["mass_table"] = rows
gc["mass_by_group_g"] = {k: round(v, 1) for k, v in by.items()}
gc["cog_rest"] = [round(v, 1) for v in c]
gc["tipping"] = tip
gc["tipping_worst"] = worst
json.dump(gc, open(f"{K2}/gaps_cog.json", "w"), indent=1)
print(round(M, 1), [round(v, 1) for v in c])
print(json.dumps(gc["mass_by_group_g"]))
for n, m in sorted(rows, key=lambda r: -r[1]):
    print(f"{n:24s} {m:7.1f}")
for k, t in tip.items():
    print(k, t)
