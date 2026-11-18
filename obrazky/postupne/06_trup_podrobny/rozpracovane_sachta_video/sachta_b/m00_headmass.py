"""m00: head + neck mass estimate from the finished B STLs (volume x density). Densities are assumptions (resin 1.15,
display assembly from B's own note ~46 g, MG90S 13.4 g datasheet-class, steel 7.85, brass 8.5, magnets 7.5)."""
import json, numpy as np
from sb_lib import read_stl, OUT
B = "/tmp/claude-0/gapwf/fin/B/stl/"
def vol(T):
    return float(np.einsum("ij,ij->i", T[:, 0], np.cross(T[:, 1], T[:, 2])).sum() / 6.0)
rho = dict(hlava_skrupina=1.15, drziak_displeja=1.15, ram_displeja=1.15, krk_predna_polovica=1.15, krk_zadna_polovica=1.15,
           paka=1.15, usi=1.15, usko_kryt=1.15, golier_kotuc=1.15, led_kruzky=1.15, klzny_kruzok=1.2, capy=7.85, skrutky=7.85,
           loziska_MR85=7.85, magnety=7.5, led_dosky=1.9, kabel=2.0, pena_displeja=0.2, pena_serva=0.2, usko_lozisko=7.85)
out = {}; tot = 0.0
for n, r in rho.items():
    try:
        v = vol(read_stl(B + n + ".stl")) / 1000.0
    except Exception as e:
        out[n] = str(e); continue
    out[n] = dict(cm3=round(v, 2), g=round(v * r, 1)); tot += v * r
out["displej (B note: ~46 g Waveshare board)"] = 46.0; tot += 46.0
out["servo_MG90S (catalogue class 13.4 g)"] = 13.4; tot += 13.4
out["L_pata Al (parts.json)"] = 6.36; tot += 6.36
out["DPS_krk + FFC ends (assumed)"] = 3.0; tot += 3.0
out["TOTAL_head_neck_g"] = round(tot, 1)
json.dump(out, open(f"{OUT}/m00_headmass.json", "w"), indent=1)
print(json.dumps(out, indent=1))
