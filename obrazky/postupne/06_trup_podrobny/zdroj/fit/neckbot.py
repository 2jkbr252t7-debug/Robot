import sys, numpy as np
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T4/fit")
from stlio import load_stl
B="/tmp/claude-0/gapwf/fin/B/stl/"
import os
for fn in sorted(os.listdir(B)):
    if fn.startswith("CELOK"): continue
    T = load_stl(B+fn); P = T.reshape(-1,3)
    print(f"{fn:28s} tris {len(T):7d}  x {P[:,0].min():7.2f} {P[:,0].max():7.2f}  y {P[:,1].min():7.2f} {P[:,1].max():7.2f}  z {P[:,2].min():7.2f} {P[:,2].max():7.2f}")
# neck bottom faces
from PIL import Image, ImageDraw
sc=20
img = Image.new("RGB",(int(50*sc),int(24*sc)),"white"); dr=ImageDraw.Draw(img)
for fn,col in (("krk_predna_polovica.stl",(60,60,200)),("krk_zadna_polovica.stl",(200,60,60))):
    T = load_stl(B+fn)
    zmin = T[:,:,2].min()
    sel = (np.abs(T[:,:,2]-zmin) < 0.02).all(axis=1)
    print(fn, "zmin", zmin, "bottom tris", sel.sum())
    for t in T[sel]:
        dr.polygon([((p[0]+25)*sc,(12-p[1])*sc) for p in t], fill=col)
    # also faces at chamfer level
img.save("fit/neck_bottom.png")
# slice occupancy at z=-34 via ray test is heavy; instead show bottom-facing tris within z<-30 colored by z
img = Image.new("RGB",(int(50*sc),int(24*sc)),"white"); dr=ImageDraw.Draw(img)
for fn in ("krk_predna_polovica.stl","krk_zadna_polovica.stl"):
    T = load_stl(B+fn)
    n = np.cross(T[:,1]-T[:,0], T[:,2]-T[:,0]); nn = np.linalg.norm(n,axis=1)+1e-12; nz = n[:,2]/nn
    sel = (nz < -0.5) & (T[:,:,2].max(axis=1) < -20)
    order = np.argsort(-T[sel][:,:,2].mean(axis=1))
    for t in T[sel][order]:
        z = t[:,2].mean(); g = int(np.clip((z+36.5)/16*255,0,255))
        dr.polygon([((p[0]+25)*sc,(12-p[1])*sc) for p in t], fill=(g,g,255-g))
img.save("fit/neck_under.png")
