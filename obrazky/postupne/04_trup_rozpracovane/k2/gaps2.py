"""supplementary min clearances of K2-designed moving parts only (no B-B pairs) -> gaps2.json"""
import sys, json, time
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T1")
import t1lib as T

L = T.Layout("/tmp/claude-0/gapwf/fin/T1/k2/layout.json")
grp = {c["name"]: c["group"] for c in L.comps}
Tst = [n for n, g in grp.items() if g == "T" and n not in ("T_horny_kruh", "T_ptfe", "T_pan_pastorok", "T_cap", "T_shell")
       and not n.startswith("B_")]
SETS = {
    "lift servo + crank + lift wire loop vs static torso internals": (["P_servo_zdvih", "P_kluka", "P_kabel_zdvih"], Tst),
    "neck foot + ear vs static torso internals": (["L_noha"], Tst),
    "well (corners r 28.1) vs static torso internals except journal ring": (["P_sachta"], Tst),
    "pan gear vs static torso internals except pinion/pin/PTFE": (["P_koleso_pan"], Tst),
    "pan stage + lift vs torso shell": (["P_sachta", "P_servo_zdvih", "P_kluka", "P_kabel_zdvih", "L_noha"], ["T_shell"]),
    "neck foot/ear vs pan stage (well, lift servo)": (["L_noha"], ["P_sachta", "P_servo_zdvih", "P_kabel_zdvih"]),
}
poses = [{"pan": a, "lift": l} for a in (-85, -60, -30, 0, 30, 60, 85) for l in (0, 10, 20)]
out = {}
t0 = time.time()
for k, (A, B) in SETS.items():
    best = (1e9, None)
    for p in poses:
        d, a, b = L.gaps(p, A, B)
        if d < best[0]:
            best = (d, {"pose": p, "a": a, "b": b})
    out[k] = {"min_mm": round(best[0], 2), **best[1]}
    print(k, out[k], round(time.time() - t0), flush=True)
json.dump(out, open("/tmp/claude-0/gapwf/fin/T1/k2/gaps2.json", "w"), indent=1)
