"""overenie_C/lug_hole_C.py - is the stop lug (r <= 6.7, inside the arm's ring hole r 7.0) really 1.24 from the arm shell,
or is the 1.24 measured to pebble skin that the hole removes?  Distance from the lug to the inner-shell MATERIAL (wall 1.6)
that remains outside the hole cylinder r 7.0."""
import sys, os, math
sys.dont_write_bytecode = True
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R3/mech")
import geomC as G, parts as PT, own_fit_C as O
YA, ZA = 3.0, -17.0
shp = G.SHAPE_C
sdf = G.SDF(shp, 0.05, 0.45, ds=0.05, dth=0.04)
for oid in ("M2b", "M2", "M3"):
    lug = next(p for p in PT.options()[oid]["parts"] if p.name == "PLG_doraz")
    L = O.sample_part(lug, 0.05)
    rng = np.random.default_rng(0)
    Q = np.c_[rng.uniform(48, 57, 3_000_000), rng.uniform(YA - 11, YA + 11, 3_000_000), rng.uniform(ZA - 11, ZA + 11, 3_000_000)]
    Pl = G.to_local(Q)
    w, ins = sdf.query(Pl, "inn")
    rq = np.hypot(Q[:, 1] - YA, Q[:, 2] - ZA)
    shell = ins & (w <= 1.6) & (rq >= 7.0)
    d, _ = cKDTree(Q[shell]).query(L)
    w_l, _ = sdf.query(G.to_local(L), "inn")
    print(oid, "lug -> inner skin (pebble) min", round(float(w_l.min()), 3), "| lug -> remaining shell material (outside r 7.0) min",
          round(float(d.min()), 3), "(random-sample resolution ~0.06)")
