import sys
from build123d import import_step, Compound
for f in sys.argv[1:]:
    s=import_step(f)
    sols=s.solids()
    bb=s.bounding_box()
    print('====',f,'solids',len(sols),'bbox',[round(v,2) for v in (bb.min.X,bb.min.Y,bb.min.Z,bb.max.X,bb.max.Y,bb.max.Z)])
    for i,so in enumerate(sols):
        b=so.bounding_box()
        print(i,'vol %.1f'%so.volume,[round(v,2) for v in (b.min.X,b.min.Y,b.min.Z,b.max.X,b.max.Y,b.max.Z)])
