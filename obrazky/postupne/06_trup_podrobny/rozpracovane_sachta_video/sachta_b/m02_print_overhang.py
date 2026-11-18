"""m02: print-orientation overhang analysis of P_sachta as documented (top plate z -2 toward the build plate, axis vertical,
raised on supports): the part grows layer by layer from z -2 toward z -45.6.  Every surface whose outward normal points to
world +Z (except the z -2 plate face) is a "down-facing" surface in the printer and needs either neighbouring material in the
previous layer (self-supporting) or supports.  Z-column voxeliser on a 0.1 grid; layer 0.05.
Writes m02_overhang.json + m02_overhang_map.png (plan view, colour = cantilever distance of each unsupported pixel)."""
import json
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw, ImageFont
from sb_lib import read_stl, column_intervals, OUT

H = 0.1
LAYER = 0.05
S = read_stl("P_sachta")
xs, ys, cols = column_intervals(S, -27.0, 27.0, -27.0, 27.0, H)
nx, ny = len(xs), len(ys)
K = max(len(a) for a in cols)
Z = np.full((ny * nx, K), np.nan)
for k, a in enumerate(cols):
    Z[k, :len(a)] = a
LO, HI = Z[:, 0::2], Z[:, 1::2]
np.savez_compressed(f"{OUT}/m02_columns.npz", LO=LO, HI=HI, xs=xs, ys=ys)


def section(z):
    with np.errstate(invalid="ignore"):
        m = np.nanmax(((LO <= z) & (z <= HI)).astype(float), axis=1)
    return (np.nan_to_num(m) > 0).reshape(ny, nx)


tops = HI.copy()                                    # interval tops = first printed layer of each column segment
tops[tops > -2.0 - 0.02] = np.nan                   # the z -2 face sits on the supports (documented)
levels = np.unique(np.round(tops[~np.isnan(tops)] / LAYER) * LAYER)
report = []
dist_map = np.full((ny, nx), np.nan)
lev_map = np.full((ny, nx), np.nan)
for zl in levels:
    sel = np.abs(tops - zl) < LAYER / 2 + 1e-6
    pix = np.any(sel, axis=1).reshape(ny, nx)
    if pix.sum() == 0:
        continue
    prev = section(zl + LAYER * 0.6)                # material of the previous printed layer (closer to the plate)
    d = ndimage.distance_transform_edt(~prev) * H   # distance to the nearest previous-layer pixel
    dd = d[pix]
    area = pix.sum() * H * H
    a1 = (dd > 1.0).sum() * H * H
    a3 = (dd > 3.0).sum() * H * H
    report.append(dict(z=round(float(zl), 3), area_mm2=round(float(area), 2), area_gt1mm=round(float(a1), 2),
                       area_gt3mm=round(float(a3), 2), max_cantilever_mm=round(float(dd.max()), 2)))
    upd = pix & (np.isnan(dist_map) | (d > np.nan_to_num(dist_map)))
    dist_map[upd] = d[upd]; lev_map[upd] = zl

big = [r for r in report if r["area_gt1mm"] > 0.5]
# hub + floor level detail: where do the unsupported pixels lie
zf = -40.65
sel = np.abs(lev_map - zf) < 0.03
by_region = dict(
    hub_ring=float(((np.hypot(*np.meshgrid(xs, ys)) <= 12.6) & sel & (dist_map > 1.0)).sum() * H * H),
    floor_r_gt_12_6=float(((np.hypot(*np.meshgrid(xs, ys)) > 12.6) & sel & (dist_map > 1.0)).sum() * H * H))
out = dict(method=__doc__, grid=H, layer=LAYER, levels_with_unsupported_gt1mm=big, hub_floor_level=by_region,
           all_levels=report)
json.dump(out, open(f"{OUT}/m02_overhang.json", "w"), indent=1)
for r in big:
    print(r)
print(by_region)

# ---- plan-view map (looking from +Z, i.e. from the build plate side through the part) ------------------------------------
sc = 14                                              # px per mm
W = int(54 * sc)
img = Image.new("RGB", (W + 360, W + 120), (250, 250, 248))
dr = ImageDraw.Draw(img)
try:
    F = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
    Fs = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
except Exception:
    F = Fs = ImageFont.load_default()
plate = section(-2.5)
wall = section(-30.0)
X0, Y0 = 20, 80


def px(x, y):
    return X0 + (x + 27) * sc, Y0 + (27 - y) * sc


rgb = np.full((ny, nx, 3), 250, np.uint8)
rgb[plate] = (225, 225, 225)
rgb[wall] = (150, 150, 150)
cm = [(0.0, (255, 230, 120)), (1.0, (255, 170, 60)), (3.0, (230, 70, 40)), (6.0, (150, 0, 60))]
for (t0, c0), (t1, c1) in zip(cm[:-1], cm[1:]):
    m = (dist_map > t0) & (dist_map <= t1)
    rgb[m] = c1
rgb[dist_map > cm[-1][0]] = cm[-1][1]
im = Image.fromarray(rgb[::-1]).resize((nx * sc // 10, ny * sc // 10), Image.NEAREST)
img.paste(im, (X0, Y0))
dr.text((20, 10), "P_sachta - tlač hornou doskou k doske: plochy bez opory (pohľad zhora, os Z)", fill=(0, 0, 0), font=F)
dr.text((20, 40), "farba = vzdialenosť od materiálu predchádzajúcej vrstvy (dĺžka previsu)", fill=(60, 60, 60), font=Fs)
lx = W + 40
for i, (lab, c) in enumerate([("stena (z -30)", (150, 150, 150)), ("horná doska", (225, 225, 225)), ("previs ≤ 1 mm", (255, 170, 60)),
                               ("previs 1–3 mm", (230, 70, 40)), ("previs > 3 mm", (150, 0, 60))]):
    dr.rectangle([lx, 120 + 34 * i, lx + 24, 144 + 34 * i], fill=c, outline=(0, 0, 0))
    dr.text((lx + 34, 120 + 34 * i), lab, fill=(0, 0, 0), font=Fs)
yy = 320
for r in big[:8]:
    dr.text((lx, yy), f"z {r['z']:.2f}: {r['area_gt1mm']:.0f} mm² > 1 mm,", fill=(0, 0, 0), font=Fs)
    dr.text((lx, yy + 20), f"   max previs {r['max_cantilever_mm']:.1f} mm", fill=(0, 0, 0), font=Fs)
    yy += 48
x, y = px(0, 0); dr.line([x - 8, y, x + 8, y], fill=(0, 0, 0)); dr.line([x, y - 8, x, y + 8], fill=(0, 0, 0))
dr.text(px(-26, -25), "PREDOK (−Y)", fill=(0, 0, 0), font=Fs)
img.save(f"{OUT}/m02_overhang_map.png")
