import sys, time; sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R3/mech")
import numpy as np, fit, parts as PT
mod = fit.load_variant("standin.py")
t=time.time(); arm = fit.Arm(mod, "kt100", -1.0)
allS = np.concatenate([p.surface(0.5) for p in PT.options()["M1"]["parts"] if p.pebble and p.role!="torso"])
L = arm.to_local(allS); print("bbox local z", L[:,2].min(), L[:,2].max())
S = arm.build_cloud(L[:,2].min()-8, L[:,2].max()+8); print("cloud", len(S), time.time()-t)
t=time.time(); Ss = {p.name: p.surface(0.15) for p in PT.options()["M1"]["parts"]}; print("surf", sum(len(v) for v in Ss.values()), time.time()-t)
t=time.time(); 
for k,v in Ss.items(): arm.walls(v)
print("walls", time.time()-t)
t=time.time(); o=PT.options()["M1"]["parts"]; print(fit.poly_dist(o[1].prof, o[6].prof), time.time()-t)
