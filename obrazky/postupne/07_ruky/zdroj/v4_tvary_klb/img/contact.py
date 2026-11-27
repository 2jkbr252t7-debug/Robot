"""quick contact sheet: contact.py OUT.png DIR 'pattern_{v}_{view}' v1,v2 view1,view2 [height]
rows = variants, columns = views; transparent renders composited on light grey; labels in the corner."""
import sys, os
from PIL import Image, ImageDraw, ImageFont

out, d, pat, vids, views = sys.argv[1:6]
H = int(sys.argv[6]) if len(sys.argv) > 6 else 360
vids, views = vids.split(","), views.split(",")
try:
    F = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
except Exception:
    F = ImageFont.load_default()
rows = []
for v in vids:
    ims = []
    for w in views:
        p = os.path.join(d, pat.format(v=v, view=w))
        im = Image.open(p).convert("RGBA")
        s = H / im.size[1]
        im = im.resize((max(1, int(im.size[0] * s)), H), Image.LANCZOS)
        bg = Image.new("RGBA", im.size, (236, 236, 234, 255)); bg.alpha_composite(im)
        ims.append(bg.convert("RGB"))
    W = sum(i.size[0] for i in ims) + 6 * (len(ims) - 1)
    r = Image.new("RGB", (W, H), (255, 255, 255)); x = 0
    for i in ims:
        r.paste(i, (x, 0)); x += i.size[0] + 6
    ImageDraw.Draw(r).text((8, 6), v, fill=(20, 20, 20), font=F)
    rows.append(r)
W = max(r.size[0] for r in rows)
sheet = Image.new("RGB", (W, sum(r.size[1] for r in rows) + 6 * (len(rows) - 1)), (255, 255, 255))
y = 0
for r in rows:
    sheet.paste(r, (0, y)); y += r.size[1] + 6
sheet.save(out)
print(out, sheet.size)
