"""tiny montage helper for previews: mont.py out.png img1 img2 ... (row, light grey bg)"""
import sys
from PIL import Image
ims = [Image.open(p).convert("RGBA") for p in sys.argv[2:]]
H = max(i.height for i in ims); W = sum(i.width for i in ims) + 8 * (len(ims) - 1)
S = Image.new("RGBA", (W, H), (236, 236, 234, 255)); x = 0
for i in ims:
    S.alpha_composite(i, (x, 0)); x += i.width + 8
S.convert("RGB").save(sys.argv[1]); print(S.size)
