#!/opt/venv/cad/bin/python
"""fix-back: write <tag>/<case>_rows.json + _curb.json from an already solved fe_gap.py case (saved U, case json, contact npz) - used once for
open_L2_h05 / L2_lift20c, whose run ended in a KeyError of the summary line AFTER the solve and the row evaluation (rows are in the .out log).
    /opt/venv/cad/bin/python fixback3_work/fe_gap_post.py <tag> <case> <gap> <h>"""
import os, sys, json
import numpy as np
T4 = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); FE = os.path.join(T4, "fe_sachta"); sys.path.insert(0, FE)
import cases as CS, fe_design as FD, post
tag, case, gap, h = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4])
out = os.path.join(T4, "fixback3_work", "fe_gap", tag); stl = os.path.join(T4, "stl"); cache = os.path.join(FE, "cache")
st = CS.Stage(stl, h, FD.load(os.path.join(FE, "design.json")), cache, nobond=False, collar=True, log=lambda s: None)
rs = json.load(open(os.path.join(out, case + ".json"))); assert rs["stl_stamp"] == st.m.stamp and abs(rs["h"] - h) < 1e-9
U = np.load(os.path.join(out, case + ".npz"))["U"].astype(np.float64)
z = np.load(os.path.join(out, case + "_contact.npz")); st.contact_pts = {k: z[k].astype(np.float64) for k in z.files}
rows = post.evaluate(st, U, rs, stl, cache, out, save_surf=False)
Uv = U.reshape(-1, 3); pr = [p for p in st.pairs if p[0] == "curb_y"][0]; a, b = np.asarray(pr[1]), np.asarray(pr[2]); rel = (Uv[b] - Uv[a])[:, 1]
info = dict(gap=gap, h=h, case=case, T=rs["spec"].get("T"), F=rs["spec"].get("F"), n=int(len(a)), rel_min=float(rel.min()), rel_max=float(rel.max()), rel_mean=float(rel.mean()),
            pair_forces=rs["pair_forces_on_pocket"], disp=rs.get("disp"),
            rows=[dict(spot=r["spot"], stress=r["stress"], allowable=r["allowable"], at=r["at"], peak=r.get("contact_zone_peak")) for r in rows if r["part"] == "P_drziak_serva" or r["kind"] != "structure"],
            solver={k: rs["solver"][k] for k in ("outer", "cg_total", "rel_res", "converged", "seconds")}, equilibrated=rs["equilibrated"], stl_stamp=rs["stl_stamp"],
            note="rows re-evaluated from the saved displacement field (float32) by fe_gap_post.py")
json.dump(info, open(os.path.join(out, case + "_curb.json"), "w"), indent=1, default=float)
json.dump(rows, open(os.path.join(out, case + "_rows.json"), "w"), indent=1, default=float)
for r in sorted(rows, key=lambda r: -(r["stress"] / r["allowable"]))[:8]:
    print(f"   {r['spot']:58s} {r['stress']:7.2f} / {r['allowable']:5.2f}  {'ok ' if r['ok'] else 'FAIL'} at {r['at']}")
print("curb", rs["pair_forces_on_pocket"]["curb_y"], "rel", round(float(rel.min()), 4), round(float(rel.max()), 4), "converged", rs["solver"]["converged"], "equilibrated", rs["equilibrated"])
