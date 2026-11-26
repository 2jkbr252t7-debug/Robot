import sys, math
import numpy as np
from build123d import import_step, Plane, Vector, Box, Pos, Cylinder, Rot
f=sys.argv[1]; sid=int(sys.argv[2]); cx=float(sys.argv[3]); cz=float(sys.argv[4])
so=import_step(f).solids()[sid]
bb=so.bounding_box()
for y in np.linspace(bb.min.Y+0.05,bb.max.Y-0.05,12):
    sec=so & Pos(cx,y,cz)*Box(12,0.02,12)
    if not sec.solids(): 
        print('y %.2f empty'%y); continue
    # sample radii by ray casting: points on circle radius r, check inside
    rs=np.arange(0.5,4.0,0.025)
    res=[]
    for ang in np.linspace(0,2*math.pi,72,endpoint=False):
        inside=[sec.is_inside(Vector(cx+r*math.cos(ang),y,cz+r*math.sin(ang))) for r in rs]
        # first r where inside material
        k=next((i for i,v in enumerate(inside) if v),None)
        res.append(rs[k] if k is not None else np.nan)
    res=np.array(res)
    print('y %.2f  hole inner radius min %.3f max %.3f  (D %.2f..%.2f)'%(y,np.nanmin(res),np.nanmax(res),2*np.nanmin(res),2*np.nanmax(res)))
