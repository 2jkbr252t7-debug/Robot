import sys, math
import numpy as np
from build123d import import_step, Plane, Vector, Box, Pos, Axis
f=sys.argv[1]; sid=int(sys.argv[2]); cx=float(sys.argv[3]); cz=float(sys.argv[4])
so=import_step(f).solids()[sid]
bb=so.bounding_box()
for y in np.linspace(bb.min.Y+0.05,bb.max.Y-0.05,10):
    cut=so & Pos(cx,y,cz)*Box(14,0.01,14)
    fs=[fc for fc in cut.faces() if abs(fc.normal_at().Y)>0.99 and fc.center().Y<y]
    out=[]
    for fc in fs:
        for w in fc.inner_wires():
            pts=[]
            for e in w.edges():
                for t in np.linspace(0,1,15):
                    p=e.position_at(t); pts.append((p.X-cx,p.Z-cz))
            pts=np.array(pts); r=np.hypot(pts[:,0],pts[:,1])
            out.append('inner wire: centre (%.2f,%.2f) r %.3f..%.3f (D %.2f..%.2f) nedges %d'%(pts[:,0].mean(),pts[:,1].mean(),r.min(),r.max(),2*r.min(),2*r.max(),len(w.edges())))
        ow=fc.outer_wire(); 
    print('y %.2f'%y, '; '.join(o for o in out if 'centre (0.0' in o or 'centre (-0.0' in o) or [o for o in out][:2])
