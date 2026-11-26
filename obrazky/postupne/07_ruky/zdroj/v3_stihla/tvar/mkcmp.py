import sys
from PIL import Image, ImageDraw, ImageFont
d=sys.argv[1]; shots=sys.argv[2].split(","); vids=sys.argv[3].split(","); out=sys.argv[4]
crop=None
if len(sys.argv)>5: crop=[float(v) for v in sys.argv[5].split(",")]
rows=[]
for sh in shots:
    ims=[]
    for v in vids:
        im=Image.open(f"{d}/{sh}_{v}.png").convert("RGBA")
        if crop and sh in ("hero","front"):
            W,H=im.size; im=im.crop((int(crop[0]*W),int(crop[1]*H),int(crop[2]*W),int(crop[3]*H)))
        bg=Image.new("RGBA",im.size,(245,245,243,255)); bg.alpha_composite(im); ims.append(bg)
    rows.append(ims)
Wt=max(sum(i.width for i in r) for r in rows); Ht=sum(max(i.height for i in r) for r in rows)+30
o=Image.new("RGB",(Wt,Ht),(245,245,243)); y=30
dr=ImageDraw.Draw(o)
try: f=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",18)
except Exception: f=None
x=0
for v,i in zip(vids,rows[0]):
    dr.text((x+10,5),"variant "+v,fill=(0,0,0),font=f); x+=i.width
for r in rows:
    x=0
    for i in r:
        o.paste(i,(x,y)); x+=i.width
    y+=max(i.height for i in r)
o.save(out)
