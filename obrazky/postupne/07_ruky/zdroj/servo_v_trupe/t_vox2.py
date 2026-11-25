import numpy as np, voxlib as V
tr=V.load("T_klb_L")
g = V.Grid((36,-12,-32),(60,18,-2),0.5)
m = V.vox_solid(tr, g, surface=False)
P = g.centres()
M = V.vlib.Mesh(tr)
ins = M.inside(P).reshape(g.n)
print("mine", m.sum()*0.125, "vlib", ins.sum()*0.125, "diff", (m^ins).sum())
d = np.argwhere(m^ins)[:10]; print(g.lo + (d+0.5)*0.5)
import json
pj=json.load(open('/tmp/claude-0/gapwf/fin/T4/parts.json'))
for p in pj['parts']:
    if p['name']=='T_klb_L': print({k:p[k] for k in ('volume','volume_mesh','stl')})
