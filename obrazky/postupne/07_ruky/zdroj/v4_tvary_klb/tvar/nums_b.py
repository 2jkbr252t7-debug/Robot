"""R4/tvar: collect the numbers of the arm-B rounding variants -> out/nums_b.json (CAD venv)
sources: variants_b.py (shape), out/fit_<v>.json (R3/mech/fit.py, option M2b), out/chk_*.json (chk_b.py = R3 gap method),
out/post_move_<v>_M2b.json (cover magnet posts)"""
import sys, json, glob
import numpy as np
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R4/tvar")
import variants_b as VA
CH = {}
for f in sorted(glob.glob("out/chk_*.json")):
    CH.update(json.load(open(f)))
u = np.linspace(0, 1, 20001)
out = {}
for v in list(VA.VIDS) + ["B4"]:
    T = VA.thickness(v, u); w, ti, to = VA.profile(v, u)
    c22, ti22, to22, w22, _, _ = [float(np.asarray(a)) for a in VA.section(v, 0.22)]
    fit = json.load(open(f"out/fit_{v}.json")); d = fit["parts"]["DRV_unasac"]
    po = json.load(open(f"out/post_move_{v}_M2b.json")) if v != "B4" else []
    ch = CH[v]
    out[v] = dict(name=VA.params(v)["name"], thickness_max=round(float(T.max()), 2), thickness_max_u=round(float(u[T.argmax()]), 3),
                  thickness_joint=round(ti22 + to22, 2), cover_joint=round(to22, 2), inner_joint=round(ti22, 2),
                  width_max=round(float(2 * w.max()), 2), width_max_u=round(float(u[w.argmax()]), 3),
                  width_joint=round(2 * w22, 2), seam_step=VA.reveal(v),
                  fit_M2b=bool(fit["fits"]), drv_wall_out=d["wall_out"], drv_wall_in=d["wall_in"],
                  joint_wall_min=round(min(d["wall_out"], d["wall_in"]), 3), joint_wall_at=d["at_out"] if d["wall_out"] <= d["wall_in"] else d["at_in"],
                  outer_margin_min=fit["margin_outer"], inner_margin_min=fit["margin_inner"],
                  gap_rest=ch["gap_rest"], gap_min_m45_135=ch["gap_min_-45_135"], gap_min_angle=ch["gap_min_angle"],
                  gap_at_140p5=ch["gap_at_140.5"], robot_width_over_arms=ch["robot_width_over_arms"],
                  innermost_world_x=ch["innermost_world_x"], outermost_world_x=ch["outermost_world_x"],
                  posts_from_u=min([p["u"] for p in po if p["u"] > 0.25 and p["min_to_moving"] >= 0.3], default=None),
                  params={k: val for k, val in VA.params(v).items() if k not in ("name",)})
    print(v, {k: val for k, val in out[v].items() if k not in ("params", "joint_wall_at", "outer_margin_min", "inner_margin_min")})
json.dump(out, open("out/nums_b.json", "w"), indent=1, ensure_ascii=False)
