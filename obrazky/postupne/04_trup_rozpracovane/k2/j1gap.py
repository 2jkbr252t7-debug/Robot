import sys, json
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T1")
import t1lib as T
L = T.Layout("/tmp/claude-0/gapwf/fin/T1/k2/layout.json")
A = ["T_J1_noha", "T_J1_sukna", "T_J1_pastorok", "T_J1_lozisko", "T_shell", "T_STS3215"]
B = ["Z_shell", "Z_J1_kanal", "Z_J1_kabel", "Z_J1_hub"]
out = {}
best = (1e9, None)
for j in (-155, -120, -90, -45, 0, 45, 90, 120, 155):
    d, a, b = L.gaps({"j1": j}, A, B)
    if d < best[0]:
        best = (d, {"pose": {"j1": j}, "a": a, "b": b})
out["J1 torso parts below the floor vs base (excl. the gear mesh)"] = {"min_mm": round(best[0], 2), **best[1]}
d, a, b = L.gaps({}, ["T_J1_pastorok"], ["Z_J1_koleso"])
out["J1 mesh (pinion tip vs sun gear tip cylinders overlap by design)"] = {"min_mm": round(d, 2)}
d, a, b = L.gaps({}, ["Z_J1_koleso"], ["T_shell", "T_J1_sukna"])
out["J1 sun gear vs torso floor / skirt"] = {"min_mm": round(d, 2), "a": a, "b": b}
# arm limit = 180 entries: verify >= 2 mm clearance at 180
lim = json.load(open("/tmp/claude-0/gapwf/fin/T1/k2/arm_limits.json"))
HEAD = ["B_hlava", "B_usi", "B_ram_tvar", "B_uska"]
ver = {}
for st, row in lim.items():
    lift = float(st.split("_")[0][4:]); tilt = float(st.split("_")[1][4:])
    for pan, a_ in row.items():
        if a_ >= 180:
            g = L.gaps({"pan": float(pan), "lift": lift, "tilt": tilt, "armR": 180}, ["A_R_ruka", "A_R_kryt"], HEAD)[0]
            ver[f"{st} pan {pan}"] = round(g, 2)
out["arm R at 180 deg: clearance to head where the table says 180"] = ver
json.dump(out, open("/tmp/claude-0/gapwf/fin/T1/k2/j1_arm_gaps.json", "w"), indent=1)
print(json.dumps(out, indent=1))
