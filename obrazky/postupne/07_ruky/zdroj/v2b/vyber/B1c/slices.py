"""JUDGE: z-slices of the K3 map around the left shoulder (x 24..54, y -34..28) with the K3 servo footprint -> img/slices_L.png"""
import numpy as np, sys
from PIL import Image, ImageDraw, ImageFont
M = np.load("/tmp/claude-0/gapwf/fin/R1/K3_preusporiadanie/k3map.npz")
lo, h, n = M["lo"], float(M["h"]), M["n"]; ds, dm, hard, chg = M["ds"], M["dm"], M["hard"], M["chg"]
lower = np.load("/tmp/claude-0/gapwf/fin/R1/trup_servo/map1.npz")["lower"]
zs = [-76, -68, -60, -52, -46, -40, -34, -28, -22]
S = 8   # px per mm
x0, x1, y0, y1 = 24, 52.5, -34, 28
W, H = int((x1-x0)*S), int((y1-y0)*S)
font = ImageFont.load_default()
tiles = []
for z in zs:
    k = int((z - lo[2]) / h)
    im = Image.new("RGB", (W, H+14), "white"); px = im.load()
    for i in range(W):
        x = x0 + (i+0.5)/S; ii = int((x-lo[0])/h)
        for j in range(H):
            y = y1 - (j+0.5)/S; jj = int((y-lo[1])/h)
            c = (255,255,255)
            if hard[ii,jj,k]: c = (150,150,150)
            elif dm[ii,jj,k] < 1.25: c = (245,180,110)
            elif ds[ii,jj,k] < 0.55: c = (210,210,210)
            elif chg[ii,jj,k]: c = (200,230,255)
            if lower[ii,jj,k] and c == (255,255,255): c = (255,240,200)
            px[i,j] = c
    d = ImageDraw.Draw(im)
    def X(x): return (x-x0)*S
    def Y(y): return (y1-y)*S
    if -66.5 <= z <= -45: d.rectangle([X(32.95),Y(8.9),X(45.05),Y(-14.3)], outline=(120,60,180), width=2)
    if -51.8 <= z <= -49.3:
        d.rectangle([X(32.95),Y(-14.3),X(45.05),Y(-18.85)], outline=(160,90,220), width=2)
        d.rectangle([X(32.95),Y(13.45),X(45.05),Y(8.9)], outline=(160,90,220), width=2)
    for gx in range(25, 53, 5): d.line([X(gx),0,X(gx),H], fill=(220,220,240) if gx%10 else (180,180,220))
    for gy in range(y0, y1+1, 5): d.line([0,Y(gy),W,Y(gy)], fill=(220,220,240) if gy%10 else (180,180,220))
    d.text((3,H+2), f"z {z}  (x {x0}..{x1} -> right, y up)", fill=(0,0,0), font=font)
    tiles.append(im)
cols = 3
out = Image.new("RGB", (cols*(W+6), ((len(tiles)+cols-1)//cols)*(H+20)), (240,240,240))
for t_, im in enumerate(tiles):
    out.paste(im, ((t_%cols)*(W+6), (t_//cols)*(H+20)))
out.save("img_slices_L.png"); print(out.size)
