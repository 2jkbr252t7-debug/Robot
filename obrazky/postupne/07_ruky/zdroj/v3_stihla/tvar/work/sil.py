"""front-view (x-z) and side (y-z, from +X) silhouettes of the variants + seam line, quick PIL plot"""
import sys, numpy as np
sys.dont_write_bytecode=True
sys.path.insert(0,"/tmp/claude-0/gapwf/fin/R3/tvar")
import importlib, variants as VA
from PIL import Image, ImageDraw
sys.path.insert(0,"/tmp/claude-0/gapwf/fin/T3"); import shape as S
vids=sys.argv[1].split(","); out=sys.argv[2]
sc=8.0; W,H=420*len(vids),720
im=Image.new("RGB",(W,H),(250,250,248)); d=ImageDraw.Draw(im)
def P(x,z,ox): return (ox+(x-40)*sc, (8-z)*sc)
# torso outline (front): x_surface max over y per z
import math
zs=np.arange(-80,4,0.5)
tor=[]
for z in zs:
    _,a,b,n=S.prof(S.s_of_drop(S.TOP-z)); tor.append((a,z))
for k,vid in enumerate(vids):
    ox=k*420+10
    d.line([P(a,z,ox) for a,z in tor],fill=(150,150,150),width=2)
    d.line([P(40,-17,ox),P(95,-17,ox)],fill=(220,180,180),width=1)
    rows,top,bot=VA.pebble_rows(vid,300,360)
    Wd=VA.to_world(rows.reshape(-1,3),vid).reshape(rows.shape)
    zz=np.arange(Wd[...,2].min()+0.1,Wd[...,2].max()-0.1,0.25)
    Pa=Wd.reshape(-1,3)
    lo=[];hi=[]
    for z in zz:
        m=np.abs(Pa[:,2]-z)<0.2
        if m.sum()<3: continue
        lo.append((Pa[m,0].min(),z)); hi.append((Pa[m,0].max(),z))
    poly=[P(x,z,ox) for x,z in lo]+[P(x,z,ox) for x,z in hi[::-1]]
    d.polygon(poly,fill=(225,225,222),outline=(40,40,40))
    # seam front line
    us=np.linspace(0.005,0.995,200)
    c,ti,to,w,_,_=VA.section(vid,us)
    sl=VA.to_world(np.c_[c,-w,-72*us],vid)
    d.line([P(x,z,ox) for x,y,z in sl],fill=(200,60,40),width=2)
    # midline of the front silhouette
    mid=[((a+b)/2,z) for (a,z),(b,_) in zip(lo,hi)]
    d.line([P(x,z,ox) for x,z in mid],fill=(60,120,200),width=1)
    d.text((ox+10,10),f"{vid}: max x {Pa[:,0].max():.1f}  min x {Pa[:,0].min():.2f}",fill=(0,0,0))
im.save(out)
