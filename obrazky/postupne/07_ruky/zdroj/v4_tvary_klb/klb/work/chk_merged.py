import sys, json
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R4/klb"); sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R4/klb/work")
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R3/mech")
import numpy as np, klb as K, parts as MP
exec(open("/tmp/claude-0/gapwf/fin/R4/klb/build_klb.py").read().split("def merged")[0].split("REP = {}")[0])  # imports only
def merged(pf):
    keep = dict(K.NEST); K.NEST.update(x_step=52.8, r_step=9.6, x_back=54.8, r_rim=12.2)
    try: return pf()
    finally: K.NEST.clear(); K.NEST.update(keep)
import importlib.util
spec = importlib.util.spec_from_file_location("chk", "/tmp/claude-0/gapwf/fin/R4/klb/chk_klb.py")
src = open("/tmp/claude-0/gapwf/fin/R4/klb/chk_klb.py").read()
pp = src[src.index("def poly_poly"):src.index("ANG = ")]
exec(pp)
out = {}
for vid, sh in (("K1", 0.0), ("K3", 0.0), ("K3v", 1.5)):
    pr = [p for p in K.VARIANTS[vid]["parts"] if p["role"] == "rotating"][0]
    prof = merged(pr["profile"])
    rows = []
    for p in MP.options()["M2b"]["parts"]:
        if p.role in ("arm",):
            continue
        P = np.array(p.outline_xr(), float).copy(); P[:, 0] += sh
        rows.append((p.name, p.role, round(poly_poly(prof, P), 3)))
    out[vid] = rows
    print(vid, rows)
json.dump(out, open("/tmp/claude-0/gapwf/fin/R4/klb/chk_merged.json", "w"), indent=1)
