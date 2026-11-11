"""min clearances of critical moving pairs + cog / tipping + mass table -> gaps_cog.json"""
import sys, json, time
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T1")
import t1lib as T

L = T.Layout("/tmp/claude-0/gapwf/fin/T1/k2/layout.json")
names = {c["name"]: c["group"] for c in L.comps}
G = lambda g: [n for n, gg in names.items() if gg == g]
Tn = [n for n in G("T")]
Pn, Ln = G("P"), G("L")
PAIRS = {
    # pan stage + lift vs static torso (excluding the intended running fits listed separately)
    "P+L vs T (no running fits)": ([n for n in Pn + Ln if n not in ("P_sachta", "P_koleso_pan", "B_kabel_krk")],
                                   [n for n in Tn if n not in ("T_horny_kruh", "T_ptfe", "T_pan_pastorok", "T_cap")]),
    "P_sachta vs T (except journal ring)": (["P_sachta"], [n for n in Tn if n not in ("T_horny_kruh",)]),
    "P_koleso_pan vs T (except pinion, pin, PTFE)": (["P_koleso_pan"], [n for n in Tn if n not in ("T_pan_pastorok", "T_cap", "T_ptfe")]),
    "journal running fit P_sachta vs T_horny_kruh": (["P_sachta"], ["T_horny_kruh"]),
    "lift ear/foot vs well P_sachta": (["L_noha"], ["P_sachta", "P_servo_zdvih"]),
    "neck B_krk vs T/P static": (["B_krk"], ["T_horny_kruh", "T_shell", "P_servo_zdvih", "P_kluka"]),
}
J1PAIRS = {"J1: torso parts below floor vs base": (["T_J1_noha", "T_J1_sukna", "T_J1_pastorok", "T_J1_lozisko", "T_shell"],
                                                  ["Z_shell", "Z_J1_kanal", "Z_J1_kabel", "Z_J1_hub"]),
           "J1: arms vs base": (["A_R_ruka", "A_L_ruka"], ["Z_shell"])}
ARMP = {"arm R vs torso": (["A_R_ruka", "A_R_kryt", "A_R_servo"], ["T_shell", "T_kabel_ramena_R", "T_stlpik_R"]),
        "arm L vs torso": (["A_L_ruka", "A_L_kryt", "A_L_servo"], ["T_shell", "T_kabel_ramena_L", "T_stlpik_L"]),
        "arm R vs base": (["A_R_ruka"], ["Z_shell"]), "arm L vs base": (["A_L_ruka"], ["Z_shell"])}
HEADP = {"head vs torso shell": (["B_hlava", "B_usi", "B_ram_tvar"], ["T_shell"])}

if __name__ == "__main__":
    t0 = time.time()
    out = {"pairs": {}}
    pan_poses = [{"pan": a, "lift": l} for a in (-85, -45, 0, 45, 85) for l in (0, 10, 20)]
    for k, (A, B) in PAIRS.items():
        best = (1e9, None)
        for p in pan_poses:
            d, a, b = L.gaps(p, A, B)
            if d < best[0]:
                best = (d, {"pose": p, "a": a, "b": b})
        out["pairs"][k] = {"min_mm": round(best[0], 2), **best[1]}
        print(k, out["pairs"][k], round(time.time() - t0), flush=True)
    for k, (A, B) in J1PAIRS.items():
        best = (1e9, None)
        for j in (-150, -90, -30, 0, 30, 90, 150):
            p = {"j1": j}
            d, a, b = L.gaps(p, A, B)
            if d < best[0]:
                best = (d, {"pose": p, "a": a, "b": b})
        out["pairs"][k] = {"min_mm": round(best[0], 2), **best[1]}
        print(k, out["pairs"][k], round(time.time() - t0), flush=True)
    for k, (A, B) in ARMP.items():
        best = (1e9, None)
        for a_ in (-45, -20, 0, 30, 60, 90, 120, 150, 180):
            p = {"armR": a_, "armL": a_}
            d, a, b = L.gaps(p, A, B)
            if d < best[0]:
                best = (d, {"pose": p, "a": a, "b": b})
        out["pairs"][k] = {"min_mm": round(best[0], 2), **best[1]}
        print(k, out["pairs"][k], round(time.time() - t0), flush=True)
    for k, (A, B) in HEADP.items():
        best = (1e9, None)
        for p in ({}, {"lift": 20, "tilt": 40}, {"lift": 20, "tilt": -40}, {"lift": 12.5, "tilt": 30},
                  {"lift": 12.5, "tilt": -40}, {"lift": 0, "tilt": 5}, {"lift": 0, "tilt": -10},
                  {"pan": 85, "lift": 20, "tilt": 40}, {"pan": -85, "lift": 20, "tilt": -40}, {"pan": 45, "lift": 20, "tilt": 40}):
            d, a, b = L.gaps(p, A, B)
            if d < best[0]:
                best = (d, {"pose": p, "a": a, "b": b})
        out["pairs"][k] = {"min_mm": round(best[0], 2), **best[1]}
        print(k, out["pairs"][k], round(time.time() - t0), flush=True)
    # ---- mass, cog, tipping
    M, c, rows = L.cog({})
    out["mass_g"] = round(M, 1)
    out["mass_table"] = rows
    tip = {}
    for nm, p in {"rest": {}, "awake": {"lift": 12.5, "tilt": 10, "pan": 30, "armR": 60, "armL": -20},
                  "arms_fwd_head_down": {"armR": 100, "armL": 100, "lift": 20, "tilt": 40},
                  "j1_90_reach": {"j1": 90, "pan": 85, "lift": 20, "tilt": 40, "armR": 90, "armL": 90},
                  "j1_45_reach": {"j1": 45, "pan": 85, "lift": 20, "tilt": 40, "armR": 100, "armL": 100},
                  "arms_back": {"armR": -45, "armL": -45, "lift": 20, "tilt": -40}}.items():
        tip[nm] = {"pose": p, **L.tipping(p, accel_g=0.15)}
        print(nm, tip[nm], flush=True)
    out["tipping"] = tip
    json.dump(out, open("/tmp/claude-0/gapwf/fin/T1/k2/gaps_cog.json", "w"), indent=1)
    print("done", round(time.time() - t0))
