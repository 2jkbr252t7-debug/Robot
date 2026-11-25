"""diagnostic slice images of the voxel map (not for the user): colours = static (grey, per part hue), sweep (orange),
free conservative (green), free optimistic only (light green), lowering sweep (blue tint), S1 path (purple tint)."""
import sys, os, json
sys.dont_write_bytecode = True
import numpy as np
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
D = np.load(os.path.join(HERE, "map1.npz"))
lo, H = D["lo"], float(D["h"]); n = tuple(D["n"])
interior, static, moving, free, label = D["interior"], D["static"], D["moving"], D["free"], D["label"]
names = list(D["lab_names"])
lower, s1 = D["lower"], D["s1"]
free_opt = interior & ~static & ~moving
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11)
os.makedirs(os.path.join(HERE, "diag"), exist_ok=True)


def colour(sl_static, sl_moving, sl_free, sl_opt, sl_int, sl_low, sl_s1, sl_lab):
    img = np.full(sl_static.shape + (3,), 255, np.uint8)
    img[sl_int] = (235, 235, 235)
    hue = (sl_lab.astype(np.int64) * 47) % 120
    img[sl_static] = np.stack([60 + hue, 60 + hue, 70 + hue], -1)[sl_static]
    img[sl_moving] = (240, 150, 40)
    img[sl_opt & ~sl_free] = (170, 230, 170)
    img[sl_free] = (40, 170, 60)
    t = sl_low & sl_free
    img[t] = (40, 120, 200)
    t = sl_s1 & sl_free
    img[t] = (150, 60, 180)
    return img


def axis_val(a, i):
    return lo[a] + (i + 0.5) * H


def slice_img(axis, value, scale=4, tag=""):
    i = int((value - lo[axis]) / H)
    sl = [slice(None)] * 3; sl[axis] = i; sl = tuple(sl)
    arrs = [a[sl] for a in (static, moving, free, free_opt, interior, lower, s1, label)]
    img = colour(*arrs)
    # orientation: for axis z -> image x = X (right = +X), image y = -Y (front -Y at the bottom? use top = +Y back)
    if axis == 2:
        img = np.transpose(img, (1, 0, 2))[::-1]          # rows = y (top = +y), cols = x
        ax_h, ax_v = 0, 1
    elif axis == 0:
        img = np.transpose(img, (1, 0, 2))[:, :, :]       # rows = z ... (1 = y, 2 = z) -> want cols = y, rows = z (top = +z)
        img = np.transpose(arrs_to(img), (0, 1, 2))
        ax_h, ax_v = 1, 2
    else:
        ax_h, ax_v = 0, 2
    return img, ax_h, ax_v


def arrs_to(x):
    return x


def make(axis, value, scale=4):
    i = int((value - lo[axis]) / H)
    sl = [slice(None)] * 3; sl[axis] = i; sl = tuple(sl)
    arrs = [a[sl] for a in (static, moving, free, free_opt, interior, lower, s1, label)]
    img = colour(*arrs)                 # shape (n_a, n_b, 3) with a < b the remaining axes in order
    rem = [k for k in range(3) if k != axis]
    ah, av = rem[0], rem[1]
    img = np.transpose(img, (1, 0, 2))[::-1]   # rows = av (top = max), cols = ah
    im = Image.fromarray(img).resize((img.shape[1] * scale, img.shape[0] * scale), Image.NEAREST)
    d = ImageDraw.Draw(im)
    # grid every 10 mm
    for v in range(-100, 101, 10):
        x = (v - lo[ah]) / H * scale
        if 0 <= x < im.width:
            d.line([(x, 0), (x, im.height)], fill=(200, 200, 255) if v else (120, 120, 255))
            d.text((x + 2, 2), str(v), fill=(0, 0, 160), font=font)
        y = im.height - (v - lo[av]) / H * scale
        if 0 <= y < im.height:
            d.line([(0, y), (im.width, y)], fill=(200, 200, 255) if v else (120, 120, 255))
            d.text((2, y + 2), str(v), fill=(0, 0, 160), font=font)
    # label the parts at their centroid in this slice
    labs = arrs[7]
    for k in np.unique(labs[arrs[0]]):
        if k == 0:
            continue
        I = np.argwhere(labs == k)
        if len(I) < 30:
            continue
        c = I.mean(0)
        x = (c[0] + 0.5) * scale; y = im.height - (c[1] + 0.5) * scale
        d.text((x, y), names[k][:14], fill=(255, 255, 0), font=font)
    nm = "xyz"[axis]
    d.text((10, im.height - 16), f"{nm} = {value}  (h: {'xyz'[ah]}, v: {'xyz'[av]})", fill=(0, 0, 0), font=font)
    p = os.path.join(HERE, "diag", f"slice_{nm}{value:+.1f}.png")
    im.save(p)
    return p


for axis, vals in ((2, (-17.0, -30.0, -40.0, -45.0, -52.0, -60.0, -72.0)), (0, (25.0, 30.0, 36.0, 40.0)), (1, (3.0, -22.0, 22.0))):
    for v in vals:
        print(make(axis, v, scale=3))
