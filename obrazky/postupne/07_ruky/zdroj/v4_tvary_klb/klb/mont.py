"""quick montage: python mont.py out.png cols label1=path1 label2=path2 ..."""
import sys
from PIL import Image, ImageDraw, ImageFont
out, cols = sys.argv[1], int(sys.argv[2])
items = [a.split("=", 1) for a in sys.argv[3:]]
ims = []
for lab, p in items:
    im = Image.open(p).convert("RGBA")
    bg = Image.new("RGBA", im.size, (236, 236, 234, 255)); bg.alpha_composite(im)
    ims.append((lab, bg.convert("RGB")))
w = max(i.size[0] for _, i in ims); h = max(i.size[1] for _, i in ims)
rows = (len(ims) + cols - 1) // cols
M = Image.new("RGB", (cols * w, rows * (h + 22)), (255, 255, 255))
d = ImageDraw.Draw(M)
try:
    f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 15)
except Exception:
    f = None
for k, (lab, im) in enumerate(ims):
    x, y = (k % cols) * w, (k // cols) * (h + 22)
    M.paste(im, (x, y + 22)); d.text((x + 6, y + 3), lab, fill=(0, 0, 0), font=f)
M.save(out)
