import time, numpy as np, voxlib as V
g = V.Grid((-53,-41,-103),(53,41,4.5),0.5)
print(g.n, np.prod(g.n)/1e6)
for n in ["T_klb_L","T_stred","T_spodok","servo_zdvih"]:
    t0=time.time(); tr=V.load(n)
    m = V.vox_solid(tr, g, surface=False)
    ms = V.vox_solid(tr, g, surface=True)
    print(n, "mesh vol", round(V.vlib.volume(tr),1), "centre-inside vol", m.sum()*0.125, "with surface", ms.sum()*0.125, f"{time.time()-t0:.1f}s")
