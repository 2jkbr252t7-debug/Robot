"""R4 sheet numbers (CAD venv).  Collects the numbers printed on the v4 sheets from the designers' and verifiers' JSON files
and asserts them against the values quoted in the verification reports; writes nums_r4.json.
Sources:  R4/overenie_tvar/out/summary.json (dims, fit), posts2.json (magnet back walls), secrad.json (radii), tip.json,
          R4/tvar/out/nums_b.json (designer), R4/klb/klb_summary.json (joint look numbers), R4/overenie_klb (joint checks,
          numbers quoted from the verifier's report), R4/img/work/combo_chk.json (K3 on B1..B3, own pre-check)."""
import json, os, sys
sys.dont_write_bytecode = True
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R4/tvar")
import numpy as np
import variants_b as VA

HERE = os.path.dirname(os.path.abspath(__file__))
R4 = "/tmp/claude-0/gapwf/fin/R4"
J = lambda p: json.load(open(os.path.join(R4, p)))
SUM = J("overenie_tvar/out/summary.json")
NB = J("tvar/out/nums_b.json")
P2 = J("overenie_tvar/out/posts2.json")
SR = J("overenie_tvar/out/secrad.json")
TIP = J("overenie_tvar/out/tip.json")
KS = J("klb/klb_summary.json")
CC = json.load(open(os.path.join(HERE, "combo_chk.json")))

# verifier (shape): arm-torso gap, analytic rec1-type model (conservative of the two methods) - quoted from the report
GAP = {"B0": (3.703, 1.124, 0.970), "B1": (3.724, 1.345, 1.316), "B2": (3.703, 1.570, 1.471), "B3": (3.703, 1.575, 1.462)}
out = {"shape": {}, "joint": {}, "combo": CC}
for v in VA.VIDS:
    d = SUM["dims"][v]
    fit = SUM["fit_py_rerun"][v]
    wall = min(fit["DRV"])
    assert abs(wall - NB[v]["joint_wall_min"]) < 0.03, (v, wall)
    assert abs(GAP[v][0] - NB[v]["gap_rest"]) < 0.025 and abs(GAP[v][1] - NB[v]["gap_min_m45_135"]) < 0.01, v
    # outermost world point of the left arm (for the width dimension line)
    rows, top, bot = VA.pebble_rows(v, 300, 400)
    P = VA.to_world(rows.reshape(-1, 3), v, VA.DX)
    i = int(np.argmax(P[:, 0]))
    assert abs(P[i, 0] - d["outermost_world_x"]) < 0.05, (v, P[i, 0], d["outermost_world_x"])
    pc = P2[f"{v} inset 3.5"]
    out["shape"][v] = dict(
        t_max=d["T_max"], t_joint=d["T_joint"], cover_joint=d["cover_joint"], inner_joint=d["inner_joint"], w_max=d["W_max"],
        robot_width=d["robot_width_over_arms"], out_x=round(float(P[i, 0]), 3), out_z=round(float(P[i, 2]), 2),
        gap_rest=GAP[v][0], gap_min=GAP[v][1], gap_stop=GAP[v][2], wall=wall, reserve=round(wall - 1.5, 3),
        post_cover=pc["back_cover"], post_inner=pc["back_inner"],
        post37_cover=P2[f"{v} inset 3.7"]["back_cover"], post37_inner=P2[f"{v} inset 3.7"]["back_inner"],
        r_min_cover=SR[v]["min_out"]["r_out"], tip_vol=TIP[v]["tip_vol_inner_half"])
    print(v, out["shape"][v])
for k in ("K0", "K1", "K2", "K3", "K3v"):
    s = KS[k]
    out["joint"][k] = dict(visible_d=s["visible_d"], band=s["front_band"]["band_height_mm"], band_area=s["front_band"]["black_area_mm2"],
                           gap=s["gap_white_arm_torso"], width=s["robot_width_over_arms"],
                           black=dict((kk, s["look"][kk]["black_visible_mm"]) for kk in s["look"]))
    print(k, out["joint"][k])
json.dump(out, open(os.path.join(HERE, "nums_r4.json"), "w"), indent=1, ensure_ascii=False)
