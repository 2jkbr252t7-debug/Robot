"""K1 - free region of a gear plane (y-z slab, x from xa to xb) in the K1 obstacle model.
A gear (moving, mine) needs 0.5 to static parts: free2d = AND over the slab of (ds >= 0.5 + 0.25) & (dm >= 1.0 + 0.25).
Prints: largest gear tip radius on the shoulder axis (y 3, z -17); 2-D distance field; image img/plane_<xa>_<xb>.png.
usage: k1_plane.py <VAR> xa,xb [xa,xb ...]"""
import sys, os, math
sys.dont_write_bytecode = True
import numpy as np
from scipy import ndimage as ndi
from PIL import Image, ImageDraw
HERE = "/tmp/claude-0/gapwf/fin/R1/K1_roh_kolesa"
VAR = sys.argv[1]
D = np.load(os.path.join(HERE, f"k1_hard{VAR}.npz"))
lo, h = D["lo"], float(D["h"]); ds, dm, hard, move = D["ds"], D["dm"], D["hard"], D["move"]
ya = lo[1] + (np.arange(ds.shape[1]) + .5) * h; za = lo[2] + (np.arange(ds.shape[2]) + .5) * h
for arg in sys.argv[2:]:
    xa, xb = (float(v) for v in arg.split(","))
    i0, i1 = int(math.floor((xa - lo[0]) / h)), int(math.ceil((xb - lo[0]) / h))
    ok = np.all((ds[i0:i1] >= 0.75) & (dm[i0:i1] >= 1.25), axis=0)
    # free distance in the plane: distance from a free cell to the nearest blocked cell (+ half voxel)
    fd = ndi.distance_transform_edt(ok, sampling=h)
    j = int((3.0 - lo[1]) / h); k = int((-17.0 - lo[2]) / h)
    print(f"slab x {xa}..{xb}: max gear tip radius on the shoulder axis = {fd[j, k]:.2f}  (clearance 0.5 to static incl.)")
    img = np.zeros(ok.shape + (3,), np.uint8)
    img[ok] = (255, 255, 255); img[~ok] = (160, 160, 160)
    anyhard = np.any(hard[i0:i1], axis=0); img[anyhard & ~ok] = (110, 110, 110)
    S = 6
    im = Image.fromarray(img.transpose(1, 0, 2)[::-1]).resize((ok.shape[0] * S, ok.shape[1] * S), Image.NEAREST)
    d = ImageDraw.Draw(im); Hpx = ok.shape[1] * S
    for g in range(-40, 41, 5):
        px = (g - lo[1]) / h * S; d.line([(px, 0), (px, Hpx)], fill=(210, 210, 255) if g % 10 else (120, 120, 200))
        if g % 10 == 0: d.text((px + 2, 2), str(g), fill=(0, 0, 160))
    for g in range(-85, 5, 5):
        py = Hpx - (g - lo[2]) / h * S; d.line([(0, py), (ok.shape[0] * S, py)], fill=(210, 210, 255) if g % 10 else (120, 120, 200))
        if g % 10 == 0: d.text((2, py + 2), str(g), fill=(0, 0, 160))
    cy, cz = (3 - lo[1]) / h * S, Hpx - (-17 - lo[2]) / h * S
    for r in (5, 10, 15):
        d.ellipse([cy - r / h * S, cz - r / h * S, cy + r / h * S, cz + r / h * S], outline=(255, 0, 0))
    d.text((10, Hpx - 14), f"gear plane x {xa}..{xb} (y right, z up): white = room for a gear (0.5 to static)", fill=(200, 0, 0))
    im.save(os.path.join(HERE, "img", f"plane_{xa:g}_{xb:g}{VAR}.png"))
    np.save(os.path.join(HERE, f"plane_{xa:g}_{xb:g}{VAR}.npy"), fd.astype(np.float32))
