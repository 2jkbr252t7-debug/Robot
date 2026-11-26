"""overenie_C/wallscan_C.py - open-section (inner half alone, cover on magnets) lateral stress at the hub edge (u 0.40)
for 10 N at the tip, as a function of the shell wall; variant C vs the approved arm."""
import sys, os, json
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import strength_C as SC, geomC as G
out = {}
for vid, shp in (("C", G.SHAPE_C), ("0", G.SHAPE_0)):
    for t in (1.6, 2.0, 2.4, 2.8):
        SC.T_WALL = t
        for u in (0.40, 0.50):
            p = SC.section_props(shp, u, "open")
            M = SC.F_TIP * G.L * (SC.U_LOAD - u)
            s = M * p["cx"] / p["Iyy"]
            out[f"{vid} t{t} u{u}"] = dict(I=round(p["Iyy"], 1), s_lat=round(s, 2))
            print(vid, "wall", t, "u", u, "I_open", round(p["Iyy"], 1), "stress 10 N lateral", round(s, 2), "MPa", flush=True)
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "wallscan_C.json"), "w"), indent=1)
