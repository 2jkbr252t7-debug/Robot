import sys, collections
from build123d import import_step, GeomType
f=sys.argv[1]
s=import_step(f)
for i,so in enumerate(s.solids()):
    b=so.bounding_box()
    print('--- solid',i,'size %.2f x %.2f x %.2f'%(b.size.X,b.size.Y,b.size.Z),'vol %.1f'%so.volume, 'faces',len(so.faces()))
    radii=collections.Counter()
    for e in so.edges():
        if e.geom_type==GeomType.CIRCLE:
            c=e.arc_center
            radii[(round(e.radius,3),round(c.X,2),round(c.Z,2))]+=1
    for k,v in sorted(radii.items()):
        print('   circle r=%.3f (D %.2f) centre x=%.2f z=%.2f  n=%d'%(k[0],2*k[0],k[1],k[2],v))
    # count small straight edges near hub (spline teeth)
    yv=collections.Counter(round(v.Y,2) for v in so.vertices())
    print('   y-levels',sorted(yv)[:12])
