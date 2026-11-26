import sys, collections
from build123d import import_step, GeomType
so=import_step(sys.argv[1]).solids()[int(sys.argv[2])]
c=collections.Counter()
for e in so.edges():
    if e.geom_type==GeomType.CIRCLE:
        p=e.arc_center
        c[(round(e.radius,3),round(p.X,2),round(p.Y,2),round(p.Z,2))]+=1
for k,v in sorted(c.items(), key=lambda kv:(kv[0][2],kv[0][0])):
    if k[0]>0.5: print('r %.3f D %.2f centre (%.2f, %.2f, %.2f) n %d'%(k[0],2*k[0],k[1],k[2],k[3],v))
ys=sorted(set(round(v.Y,2) for v in so.vertices()))
print('y levels top', ys[:14])
