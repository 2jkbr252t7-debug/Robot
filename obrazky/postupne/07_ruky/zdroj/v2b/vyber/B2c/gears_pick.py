"""B2: re-evaluate the short-listed printed bevel pairs (ratio <= 1.56 so that servo 300 deg gives the arm >= 192 deg)
at a finer raster; writes gears_pick.json"""
import sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gears as G
G_rt = G.rack_tooth
def fine(zv, a, x=0.0, **k):
    return G_rt(zv, a, x, n=420, nroll=380)
G.rack_tooth = fine
G._CACHE.clear()
L = [(0.5, 16, 24, 2.4, 20.0, 0.0), (0.5, 16, 24, 2.4, 25.0, 0.35), (0.55, 14, 21, 2.5, 25.0, 0.35), (0.55, 15, 23, 2.6, 25.0, 0.2),
     (0.6, 13, 20, 2.55, 25.0, 0.35), (0.65, 12, 18, 2.6, 25.0, 0.35), (0.7, 11, 17, 2.55, 25.0, 0.35), (0.75, 10, 15, 2.5, 25.0, 0.35),
     (0.6, 13, 20, 2.55, 25.0, 0.25), (0.65, 12, 18, 2.6, 25.0, 0.25)]
out = []
for m, z1, z2, b, a, x1 in L:
    bv = G.bevel(m, z1, z2, b, a, x1)
    bv["arm_range_deg"] = round(300.0 * z1 / z2, 1)
    for T in (0.004, 0.006, 0.010, 0.012, 0.015):
        bv[f"stress_at_{T}"] = G.stress(bv, T)
    out.append(bv)
    print("a%2.0f m%.2f %2d/%2d x1 %+.2f b %.2f ratio %.3f arm %5.1f  crown %.2f/%.2f  Y %.3f/%.3f Kf %.2f/%.2f tip %.2f/%.2f eps %.2f "
          "T@8.5 %.4f  s@0.012 %.1f/%.1f (Kf %.1f)" % (a, m, z1, z2, x1, b, z2 / z1, bv["arm_range_deg"], bv["crown1"], bv["crown2"],
          bv["Y1"]["Y"], bv["Y2"]["Y"], bv["Y1"]["Kf"], bv["Y2"]["Kf"], bv["Y1"]["s_tip_over_m"], bv["Y2"]["s_tip_over_m"], bv["eps"],
          bv["T_arm_at_allow"], bv["stress_at_0.012"]["s1"], bv["stress_at_0.012"]["s2"], max(bv["stress_at_0.012"]["s1_Kf"], bv["stress_at_0.012"]["s2_Kf"])), flush=True)
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "gears_pick.json"), "w"), indent=1, default=float)
