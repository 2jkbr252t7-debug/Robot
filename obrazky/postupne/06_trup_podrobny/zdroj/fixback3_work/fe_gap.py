#!/opt/venv/cad/bin/python
"""fix-back after overenie3, finding V1: the -90 deg stop case of the FINAL set (same STL, same design.json, same harness) with a
CLEARANCE at the sole / curb contact (pair 'curb_y').  The harness files are not modified: the pair list of the Stage is patched
after construction and the soft regularisation spring of a gap contact is switched off for this pair (the module is held by the
clamped F10 pads, it cannot float).
    /opt/venv/cad/bin/python fixback3_work/fe_gap.py <gap mm> <h> <tag>      -> fixback3_work/fe_gap/<tag>/L8_stop_m90.json (+ _curb.json)
Linear elasticity + contact: the result at torque T with gap g equals (T / 880) x the result at 880 N.mm with gap g x 880 / T."""
import os, sys, json, time
import numpy as np
T4 = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); FE = os.path.join(T4, "fe_sachta")
sys.path.insert(0, FE)
import cases as CS, femodel as FM, fe_design as FD, post
gap = float(sys.argv[1]); h = float(sys.argv[2]); tag = sys.argv[3]; case = sys.argv[4] if len(sys.argv) > 4 else "L8_stop_m90"
out = os.path.join(T4, "fixback3_work", "fe_gap", tag); os.makedirs(out, exist_ok=True)
_C = FM.Contact


class C2(_C):
    def __init__(self, name, kind, k, **kw):
        if name == "curb_y_reg":
            k = 1e-6 * np.asarray(k, float)
        super().__init__(name, kind, k, **kw)


FM.Contact = C2
D = FD.load(os.path.join(FE, "design.json"))
log = lambda s: print(s, flush=True)
stl = os.path.join(T4, "stl"); cache = os.path.join(FE, "cache")
st = CS.Stage(stl, h, D, cache, nobond=False, collar=True, log=log)
if gap > 0:
    st.pairs = [(p[0], p[1], p[2], p[3], p[4], -gap) if p[0] == "curb_y" else p for p in st.pairs]
t0 = time.time()
U, rs = st.run(case, out, tol=2e-6, inner=150, max_outer=60)
rows = post.evaluate(st, U, rs, stl, cache, out)
for r in sorted(rows, key=lambda r: -(r["stress"] / r["allowable"]))[:14]:
    log(f"   {r['spot']:58s} {r['stress']:7.2f} / {r['allowable']:5.2f}  {'ok ' if r['ok'] else 'FAIL'} at {r['at']}")
Uv = U.reshape(-1, 3)
pr = [p for p in st.pairs if p[0] == "curb_y"][0]
a, b = np.asarray(pr[1]), np.asarray(pr[2])
rel = (Uv[b] - Uv[a])[:, 1]                       # +y of the pocket node relative to the well node; closing = negative
X = st.X[a]
o = np.argsort(rel)
info = dict(gap=gap, h=h, case=case, T=rs["spec"].get("T"), F=rs["spec"].get("F"), n=int(len(a)), rel_min=float(rel.min()), rel_max=float(rel.max()), rel_mean=float(rel.mean()),
            most_closing=[dict(x=float(X[i, 0]), z=float(X[i, 2]), rel=float(rel[i])) for i in o[:8]],
            least_closing=[dict(x=float(X[i, 0]), z=float(X[i, 2]), rel=float(rel[i])) for i in o[-4:]],
            pair_forces=rs["pair_forces_on_pocket"], stop=rs["reactions"].get("stop"), disp=rs.get("disp"),
            rows=[dict(spot=r["spot"], stress=r["stress"], allowable=r["allowable"], at=r["at"], peak=r.get("contact_zone_peak")) for r in rows if r["part"] == "P_drziak_serva" or r["kind"] != "structure"],
            solver={k: rs["solver"][k] for k in ("outer", "cg_total", "rel_res", "converged", "seconds")}, equilibrated=rs["equilibrated"], stl_stamp=rs["stl_stamp"])
json.dump(info, open(os.path.join(out, case + "_curb.json"), "w"), indent=1, default=float)
json.dump(rows, open(os.path.join(out, case + "_rows.json"), "w"), indent=1, default=float)
log(f"== gap {gap} h {h}: curb rel y min {rel.min():.4f} mean {rel.mean():.4f} max {rel.max():.4f}; curb force {rs['pair_forces_on_pocket']['curb_y']}; {time.time() - t0:.0f} s")
