"""quick-look stress maps: splat the true-surface sample points (z-buffered) coloured by max principal stress.
usage: viz_stress.py case view [vmax] ; views: px (from +X), mx (from -X), my (from front -Y), py (from back +Y), mz (from below), pz (from above)"""
import sys, numpy as np
from PIL import Image, ImageDraw, ImageFont
case, view = sys.argv[1], sys.argv[2]; vmax = float(sys.argv[3]) if len(sys.argv) > 3 else 12.9
SP = np.load("surf_pts.npz"); P, N = SP["P"], SP["N"]
s = np.load(f"res/{case}_surf.npz"); s1 = s["s1"].astype(float)
V = {"px": ((1, 0, 0), (0, 1, 0)), "mx": ((-1, 0, 0), (0, -1, 0)), "my": ((0, -1, 0), (1, 0, 0)), "py": ((0, 1, 0), (-1, 0, 0)),
     "mz": ((0, 0, -1), (-1, 0, 0)), "pz": ((0, 0, 1), (1, 0, 0))}
d, right = [np.array(v, float) for v in V[view]]
up = np.cross(right, d) if view in ("mz", "pz") else np.array([0, 0, 1.0])
if view in ("mz", "pz"):
    up = np.array([0, 1.0, 0]); right = np.cross(d, up) * -1 if view == "mz" else np.cross(up, d)
u = P @ right; v = P @ up; depth = P @ d                     # larger depth = closer to the viewer (camera at +d)
facing = (N @ d) > -0.05
res = 0.07
u0, v0 = u.min() - 1, v.min() - 1
W = int((u.max() - u0 + 1) / res) + 1; H = int((v.max() - v0 + 1) / res) + 1
iu = ((u - u0) / res).astype(int); iv = (H - 1 - ((v - v0) / res)).astype(int)
zb = np.full((H, W), -1e9); col = np.full((H, W), np.nan)
o = np.argsort(depth)
for k in (0, 1):
    for dx in (0, 1):
        pass
idx = o[facing[o]]
zb_flat = zb.ravel(); col_flat = col.ravel()
for dx in (0, 1):
    for dy in (0, 1):
        ii = np.clip(iu[idx] + dx, 0, W - 1); jj = np.clip(iv[idx] + dy, 0, H - 1)
        lin = jj * W + ii
        upd = depth[idx] >= zb_flat[lin] - 0.3
        zb_flat[lin[upd]] = depth[idx][upd]; col_flat[lin[upd]] = s1[idx][upd]
img = np.full((H, W, 3), 245, np.uint8)
c = col_flat.reshape(H, W); m = ~np.isnan(c); c = np.nan_to_num(c)
t = np.clip(c / vmax, -1, 1)
r = np.where(t > 0, 255, (255 * (1 + t))).astype(np.uint8); g = (255 * (1 - np.abs(t))).astype(np.uint8); b = np.where(t < 0, 255, (255 * (1 - t))).astype(np.uint8)
img[m] = np.stack([r, g, b], -1)[m]
over = m & (c > vmax); img[over] = (90, 0, 0)
im = Image.fromarray(img)
dr = ImageDraw.Draw(im); f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)
dr.text((10, 10), f"{case}  view {view}  s1 (red +{vmax:.1f} MPa, dark red > {vmax:.1f}, blue -{vmax:.1f})", font=f, fill=(0, 0, 0))
im.save(f"img/fe_{case}_{view}.png"); print("saved", W, H)
