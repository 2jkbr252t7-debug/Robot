import sys, json
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T1")
import t1lib as T
K2 = "/tmp/claude-0/gapwf/fin/T1/pack"
L = T.Layout(f"{K2}/layout.json")
out = json.load(open(f"{K2}/j1_arm_gaps.json"))
A = ["T_J1_noha", "T_J1_sukna", "T_J1_pastorok", "T_shell", "T_STS3215"]
B = ["Z_shell", "Z_J1_kanal", "Z_J1_kabel", "Z_J1_hub"]
best = (1e9, None)
for j in (-155, -120, -90, -45, 0, 45, 90, 120, 155):
    d, a, b = L.gaps({"j1": j}, A, B)
    if d < best[0]:
        best = (d, {"pose": {"j1": j}, "a": a, "b": b})
out["J1 torso parts below the floor vs base (excl. the gear mesh)"] = {"min_mm": round(best[0], 2), **best[1],
    "note": "bearing 6805 inner ring on the hub excluded (intended fit)"}
for k, (A_, B_) in {"well vs pan channel/cable": (["P_sachta"], ["T_kanal_pan", "T_kabel_pan"]),
                    "lift servo vs pan channel/cable": (["P_servo_zdvih"], ["T_kanal_pan", "T_kabel_pan"])}.items():
    bb = (1e9, None)
    for p in ({"pan": -85}, {"pan": 0}, {"pan": 85}):
        d, a, b = L.gaps(p, A_, B_)
        if d < bb[0]:
            bb = (d, {"pose": p, "a": a, "b": b})
    out[k] = {"min_mm": round(bb[0], 2), **bb[1]}
# arm limit at lift 12.5 tilt 30 pan 30 (table said 180 but clearance at 180 is 0.01)
HEAD = ["B_hlava", "B_usi", "B_ram_tvar", "B_uska"]
lim = json.load(open(f"{K2}/arm_limits.json"))
for st, row in lim.items():
    lift = float(st.split("_")[0][4:]); tilt = float(st.split("_")[1][4:])
    for pan, a_ in row.items():
        a = 180.0 if a_ >= 180 else a_
        while a > 60 and L.gaps({"pan": float(pan), "lift": lift, "tilt": tilt, "armR": a}, ["A_R_ruka", "A_R_kryt"], HEAD)[0] < 2.0:
            a -= 2.0
        row[pan] = int(a)                                   # whole degrees, rounded down
json.dump(lim, open(f"{K2}/arm_limits.json", "w"), indent=1)
json.dump(out, open(f"{K2}/j1_arm_gaps.json", "w"), indent=1)
print(json.dumps(out, indent=1)); print(json.dumps(lim, indent=1))
