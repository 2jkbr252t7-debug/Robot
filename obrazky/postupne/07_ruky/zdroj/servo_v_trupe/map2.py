"""STEP 1b - analyse map1.npz: validation of the sweep, free regions near the shoulders and in the lower torso, largest
axis-aligned boxes, axis-aligned servo-case fit tests.  Writes map2.json."""
import sys, os, json, math, time
sys.dont_write_bytecode = True
import numpy as np
from scipy import ndimage as ndi
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import voxlib as V  # noqa: E402

t0 = time.time()
D = np.load(os.path.join(HERE, "map1.npz"))
lo, H = D["lo"], float(D["h"]); n = tuple(D["n"])
g = V.Grid(lo, lo + np.array(n) * H, H)
interior, static, moving, free = D["interior"], D["static"], D["moving"], D["free"]
ds, dm, label, lab_names = D["ds"], D["dm"], D["label"], list(D["lab_names"])
lower, s1, bokL, bokP, klbL, klbP, amp = (D[k] for k in ("lower", "s1", "bokL", "bokP", "klbL", "klbP", "amp"))
X, Y, Z = np.meshgrid(g.axis(0), g.axis(1), g.axis(2), indexing="ij")
R = np.hypot(X, Y)
out = {}

# ---------------------------------------------------------------- validation
val = {}
for z0, z1, rr in [(-47.2, -41.9, 17.5), (-41.9, -40.9, 26.5), (-40.9, -17.0, 33.4), (-17.0, -11.5, 32.2), (-11.5, 4.0, 26.5)]:
    m = moving & (Z > z0 + 0.3) & (Z < z1 - 0.3) & ~((R >= 15.2) & (R <= 25.1) & (Z >= -46.2) & (Z <= -41.9))
    val[f"z {z0}..{z1}"] = dict(PAN_ENV2_r=rr, voxel_sweep_r_max=round(float(R[m].max() + 0.25), 2) if m.any() else None)
# clearance column inner face (x 34.4) <-> sweep at the shoulder height (K3 / spec: 1.03 lift servo <-> left column)
colL = (label == lab_names.index("T_spodok")) & (X > 30) & (Z > -41) & (Z < -12)
colP = (label == lab_names.index("T_spodok")) & (X < -30) & (Z > -41) & (Z < -12)
val["min_dist_T_spodok_column_L_to_sweep_voxel_centres"] = round(float(dm[colL].min()), 2)
val["min_dist_T_spodok_column_P_to_sweep_voxel_centres"] = round(float(dm[colP].min()), 2)
val["note"] = ("voxel distances are between voxel centres (0.5 grid): true surface distances differ by up to +-0.43; "
               "the K3 exact value is 1.03 (lift servo <-> left column)")
out["validation"] = val
print(json.dumps(val, indent=1))


# ---------------------------------------------------------------- regions
def bounds(m):
    I = np.argwhere(m)
    a = g.lo + I.min(0) * H; b = g.lo + (I.max(0) + 1) * H
    return [round(float(a[0]), 1), round(float(b[0]), 1), round(float(a[1]), 1), round(float(b[1]), 1), round(float(a[2]), 1), round(float(b[2]), 1)]


def neighbours(m, dil=2):
    """names of static parts / moving sweep around a region (within dil voxels)"""
    ring = ndi.binary_dilation(m, iterations=dil) & ~m
    labs = np.unique(label[ring & static]); names = [lab_names[i] for i in labs if i > 0]
    mv = bool((ring & moving).any())
    return names + (["<pan/lift sweep>"] if mv else [])


VARIANTS = {
    "free": free,
    "free_minus_assembly": free & ~lower & ~s1 & ~amp,
}
REGIONS = {
    "L_shoulder (x>=20, z>=-48)": (X >= 20) & (Z >= -48),
    "P_shoulder (x<=-20, z>=-48)": (X <= -20) & (Z >= -48),
    "lower torso (z<-48)": (Z < -48),
}
comp_rows = []
for vname, F in VARIANTS.items():
    for rname, RM in REGIONS.items():
        M = F & RM
        lab, nlab = ndi.label(M)
        sizes = ndi.sum(M, lab, index=np.arange(1, nlab + 1))
        order = np.argsort(-sizes)
        for k in order[:12]:
            vol = float(sizes[k]) * H ** 3
            if vol < 150.0:
                break
            cm = lab == (k + 1)
            comp_rows.append(dict(variant=vname, region=rname, volume_mm3=round(vol), bounds_xyz=bounds(cm),
                                  centroid=[round(float(v), 1) for v in (g.lo + (np.argwhere(cm).mean(0) + 0.5) * H)],
                                  thickest_mm=round(2 * float(ndi.distance_transform_edt(cm, sampling=H).max()), 1),
                                  bordered_by=neighbours(cm)[:14]))
out["components"] = comp_rows
for r in comp_rows:
    if r["variant"] == "free":
        print(r["region"], r["volume_mm3"], r["bounds_xyz"], "thick", r["thickest_mm"], r["bordered_by"][:8])
print(f"components {time.time()-t0:.0f}s")


# ---------------------------------------------------------------- largest boxes per region (0.5 grid; x/y sizes in 1 mm steps)
def sub(F, RM):
    M = F & RM
    I = np.argwhere(M)
    if len(I) == 0:
        return None, None
    a = I.min(0); b = I.max(0) + 1
    return M[a[0]:b[0], a[1]:b[1], a[2]:b[2]], a


boxes = []
for vname, F in VARIANTS.items():
    for rname, RM in REGIONS.items():
        S, a = sub(F, RM)
        if S is None:
            continue
        for md in (0, 14, 24):            # min dimension 0 / 7 / 12 mm
            v, p, d = V.max_box(S, H, step=2, min_dim=md)
            if p is None:
                boxes.append(dict(variant=vname, region=rname, min_dim_mm=md * H, box=None)); continue
            p0 = g.lo + (a + np.array(p)) * H; dd = np.array(d) * H
            boxes.append(dict(variant=vname, region=rname, min_dim_mm=md * H, size_xyz=[round(float(x), 1) for x in dd],
                              volume_mm3=round(float(np.prod(dd))),
                              at_xyz=[[round(float(p0[i]), 1), round(float(p0[i] + dd[i]), 1)] for i in range(3)]))
        print(vname, rname, [(b_.get("size_xyz"), b_.get("at_xyz")) for b_ in boxes[-3:]])
out["largest_boxes"] = boxes
print(f"boxes {time.time()-t0:.0f}s")

# ---------------------------------------------------------------- axis-aligned servo case fit (6 orientations)
SERVOS = {
    "SCS0009 case 23.2x12.1x21.5 (case height UNVERIFIED; 25.25 incl. shaft)": (23.2, 12.1, 21.5),
    "SCS0009 if 25.25 is the case": (23.2, 12.1, 25.25),
    "MG90S case 22.8x12.2x22.7 (no ears)": (22.8, 12.2, 22.7),
    "STS3032 case 23.5x12.5x23.0": (23.5, 12.5, 23.0),
    "KST X06 case 20x7x16.6": (20.0, 7.0, 16.6),
}
import itertools
fits = []
for vname, F in VARIANTS.items():
    for sname, dims in SERVOS.items():
        res = {}
        for perm in set(itertools.permutations(range(3))):
            dv = [int(math.ceil(dims[i] / H)) for i in perm]
            P = V.box_fits(F, dv)
            key = "x%.1f y%.1f z%.1f" % tuple(dims[i] for i in perm)
            if len(P):
                c = g.lo + (P + np.array(dv) / 2.0) * H
                res[key] = dict(n_positions=int(len(P)), example_centre=[round(float(v), 1) for v in c[len(c) // 2]],
                                centre_range=[[round(float(c[:, i].min()), 1), round(float(c[:, i].max()), 1)] for i in range(3)])
            else:
                res[key] = None
        fits.append(dict(variant=vname, servo=sname, orientations=res, fits_anywhere=any(v is not None for v in res.values())))
        print(vname, sname, {k: (v["example_centre"] if v else None) for k, v in res.items()})
out["servo_fits_axis_aligned"] = fits
out["seconds"] = round(time.time() - t0)
json.dump(out, open(os.path.join(HERE, "map2.json"), "w"), indent=1)
print("done", out["seconds"])
