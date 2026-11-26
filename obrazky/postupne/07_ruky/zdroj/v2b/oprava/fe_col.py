"""FIXER: voxel FE (fe3d, 8-node Wilson hexes, h 0.5) of the B1+ shoulder column ALONE (no side cap, no deck = conservative)
under L5 = 10 N along X at the arm tip (tip 53.75 mm from the shoulder axis, v_arm.json), arm angle a.
Column = v2 'stlp' solids WITHOUT rod holes (stlp + tyce voxels, both resin) + upper fill (judge colfill_B1merge, optionally clipped
to the deck path / servo corridor, see clip()) + optional torsion web between the legs at z -35..-26.85 (from the free map).
RIGHT side: computed in mirrored (x -> -x) coordinates: stlp minus the left-only web + F3a_2 boss, plus stena_P (mirrored), R fill.
Load: resultant (Fx, My, Mz) about (39, 3, -17) applied as a rigid-plate linear x-pressure on the boss face nodes x 38.5, r <= 11.
Support: all nodes z <= -76 fixed.  Output: nodal-averaged von Mises / principal, max by zone, json.
usage: fe_col.py SIDE VARIANT   (VARIANT: judge | clip | web)"""
import sys, os, json, math, time
import numpy as np
from scipy import ndimage as ndi
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T4/fe_sachta")
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R1/trup_servo")
import fe3d, voxlib as VL
SIDE, VAR0 = sys.argv[1], sys.argv[2]
NOSLOT = "+noslot" in VAR0; VAR0b = VAR0.replace("+noslot", ""); FACE = VAR0b.endswith("+face"); PLUG = VAR0b.endswith("+plug") or FACE; VAR = VAR0b.replace("+plug", "").replace("+face", "")
ANG = [float(a) for a in (sys.argv[3:] or ["0", "90", "135"])]
W = "/tmp/claude-0/gapwf/fin/R1/img_v2/work/stl/"
h = 0.5
g = VL.Grid((26.0, -22.0, -78.5), (46.5, 18.5, -3.5), h)
xs, ys, zs = g.axis(0), g.axis(1), g.axis(2)
X, Y, Z = np.meshgrid(xs, ys, zs, indexing="ij")
col = VL.vox_solid(VL.vlib.load_stl(W + "stlp.stl"), g, surface=False) | VL.vox_solid(VL.vlib.load_stl(W + "tyce.stl"), g, surface=False)
if SIDE == "R":
    webL = (X > 30.5) & (X < 32.65) & (Y > -14.6) & (Y < 9.2) & (Z > -70.5) & (Z < -48.8)
    f3 = (np.hypot(X - 29.5, Y - 4.0) < 2.6) & (Z > -52.7) & (Z < -48.8)
    col &= ~(webL | f3)
    col |= (X > 31.9) & (X < 32.65) & (Y > -14.6) & (Y < 9.2) & (Z > -70.5) & (Z < -48.8)
if NOSLOT:
    col |= (X > 37.0) & (X < 41.5) & (Y > -17.6) & (Y < -14.6) & (Z > -66.8) & (Z < -63.2)
F = np.load(f"/tmp/claude-0/gapwf/fin/R2c/vyber/B2c/colfill_B1merge_{SIDE}.npz")["P"].astype(float)
if SIDE == "R": F[:, 0] *= -1
def clip(P):
    """exact clips on voxel extents (h 0.5): deck lowering path (x >= 31.3 for voxels reaching above z -48.5) and the servo slide
    corridor (servo + 0.3: x >= 32.65, y -14.6..9.2) for voxels reaching below z -44.5"""
    x0, x1, y0, y1, z0, z1 = P[:, 0] - h/2, P[:, 0] + h/2, P[:, 1] - h/2, P[:, 1] + h/2, P[:, 2] - h/2, P[:, 2] + h/2
    bad = (z1 > -48.5) & (x0 < 31.3)
    bad |= (z0 < -44.5) & (x1 > 32.65) & (y1 > -14.6) & (y0 < 9.2)
    return P[~bad], int(bad.sum())
nclip = 0
if VAR in ("clip", "web"):
    F, nclip = clip(F)
fill = np.zeros(g.n, bool)
I = np.round((F - g.lo - h / 2) / h).astype(int)
fill[I[:, 0], I[:, 1], I[:, 2]] = True
web = np.zeros(g.n, bool)
if VAR == "web":
    M = np.load(f"free_{SIDE}.npz")
    ds, dm, dl, capmin = M["ds"], M["dm"], M["dl"], M["capmin"]
    mx, my, mz = M["xs"], M["ys"], M["zs"]
    for k, z in enumerate(zs):
        if z < -34.75 or z > -27.0: continue
        kz = int(np.argmin(abs(mz - z)))
        for i, x in enumerate(xs):
            ix = int(np.argmin(abs(mx - x)))
            if abs(mx[ix] - x) > 1e-6: continue
            for j, y in enumerate(ys):
                if not (-9.5 <= y <= 8.0): continue
                jy = int(np.argmin(abs(my - y)))
                ok = ds[ix, jy, kz] >= 0.3 + h/2 and dm[ix, jy, kz] >= 1.0 + h/2 and dl[ix, jy, kz] >= 0.5 + h/2
                rsh = math.hypot(y - 3.0, z + 17.0)
                ok &= x <= (38.8 if rsh <= 16.3 else 41.5) - h/2
                ok &= x <= capmin[jy, kz] - 0.3 - h/2
                # exact shaft keep-out r 3.0 about (39, 3): nearest point of the voxel square
                dx = max(abs(x - 39.0) - h/2, 0); dy = max(abs(y - 3.0) - h/2, 0)
                ok &= math.hypot(dx, dy) >= 3.0
                ok &= x - h/2 >= 31.3
                if ok: web[i, j, k] = True
CLOCK = {12: (0.0, 1.0), 4: (math.sin(math.radians(120)), math.cos(math.radians(120))), 8: (math.sin(math.radians(240)), math.cos(math.radians(240))),
         10: (math.sin(math.radians(300)), math.cos(math.radians(300))), 2: (math.sin(math.radians(60)), math.cos(math.radians(60)))}
def cpt(hh, r=9.0):
    s_, c_ = CLOCK[hh]
    if SIDE == "R": s_ = s_      # mirrored model keeps the same (y, z) positions
    return 3.0 + r * s_, -17.0 + r * c_
plugb = np.zeros(g.n, bool)
if PLUG:
    # glued brass inserts (3 screws) and peg holes -> solid in the column; stiff plug = neck/body disc x 39..41 + screw/peg columns
    for hh, x0 in ((12, 34.9), (4, 34.9), (8, 34.9), (10, 36.4), (2, 36.4)):
        yy, zz = cpt(hh)
        rr = np.hypot(Y - yy, Z - zz)
        col |= (rr <= 1.6) & (X > x0) & (X < 38.5)
        plugb |= (rr <= 1.0) & (X > x0 + 0.1) & (X < 39.0)
    plugb |= (np.hypot(Y - 3.0, Z + 17.0) <= 13.5) & (X > 39.0) & (X < 41.0)
    if FACE:   # neck lengthened to touch the boss face (x 38.4): stiff neck cells x 38.5..39.0 inside r 11
        plugb |= (np.hypot(Y - 3.0, Z + 17.0) <= 11.0) & (X > 38.5) & (X < 39.0)
solid = col | fill | web
lab, nl = ndi.label(solid)
sizes = ndi.sum(solid, lab, range(1, nl + 1))
keep = 1 + int(np.argmax(sizes))
dropped = int(solid.sum() - (lab == keep).sum())
solid = lab == keep
info = dict(side=SIDE, variant=VAR, n_col=int(col.sum()), n_fill=int(fill.sum()), n_fill_clipped=nclip, n_web=int((web & ~col & ~fill).sum()),
            web_vol_mm3=round(float((web & ~col & ~fill).sum() * h ** 3), 1), n_solid=int(solid.sum()), dropped_islands=dropped)
print(info, flush=True)
np.save(f"col_{SIDE}_{VAR0}.npy", solid)
m = fe3d.Model(g.lo, h, g.n)
m.add_body("col", solid.astype(float), 2000.0, 0.38)
SCREWS = [cpt(hh) for hh in (12, 4, 8, 10, 2)]
def mergefn(P):
    r = np.hypot(P[:, 1] - 3.0, P[:, 2] + 17.0)
    ring = (abs(P[:, 0] - 39.0) < 1e-6) & (r >= 11.4) & (r <= 13.0)
    scr = np.zeros(len(P), bool)
    for (yy, zz) in SCREWS:
        scr |= (np.hypot(P[:, 1] - yy, P[:, 2] - zz) <= 1.01) & (P[:, 0] <= 38.5 + 1e-6)
    if FACE:
        ring |= (abs(P[:, 0] - 38.5) < 1e-6) & (r <= 11.0)
    return ring | scr
if PLUG:
    m.add_body("plug", plugb.astype(float), 200000.0, 0.3)
    m.build_nodes(merges=[("col", "plug", mergefn)])
    print("merged", m.merged, flush=True)
else:
    m.build_nodes()
m.assemble()
Xn = m.X
fixed_nodes = np.nonzero(Xn[:, 2] <= -76.0 + 1e-6)[0]
fixed = np.concatenate([3 * fixed_nodes, 3 * fixed_nodes + 1, 3 * fixed_nodes + 2])
rsh_n = np.hypot(Xn[:, 1] - 3.0, Xn[:, 2] + 17.0)
face = np.nonzero((abs(Xn[:, 0] - (41.0 if PLUG else 38.5)) < 1e-6) & (rsh_n <= 11.0))[0]
info["n_face_nodes"] = int(len(face)); info["n_fixed_nodes"] = int(len(fixed_nodes))
yf, zf = Xn[face, 1] - 3.0, Xn[face, 2] + 17.0
A = np.array([[len(face), yf.sum(), zf.sum()], [(zf).sum(), (yf * zf).sum(), (zf * zf).sum()], [-(yf).sum(), -(yf * yf).sum(), -(yf * zf).sum()]])
tip = 53.75
res = dict(info=info, cases={})
for a in ANG:
    ar = math.radians(a)
    dy, dz = -tip * math.sin(ar), -tip * math.cos(ar)
    Fx = -10.0                                    # push toward the torso
    My, Mz = dz * Fx, -dy * Fx
    c = np.linalg.solve(A, np.array([Fx, My, Mz]))
    fx = c[0] + c[1] * yf + c[2] * zf
    Fv = np.zeros(3 * m.nn); Fv[3 * face] = fx
    U = m.solve(Fv, [], fixed=fixed, tol=1e-8, maxiter=800)
    ids, sig, sn = m.stresses(U, "col")
    if PLUG:   # tilt of the stiff plug (rigid) for information
        pass
    s = sig
    vm = np.sqrt(0.5 * ((s[:, 0] - s[:, 1]) ** 2 + (s[:, 1] - s[:, 2]) ** 2 + (s[:, 2] - s[:, 0]) ** 2) + 3 * (s[:, 3] ** 2 + s[:, 4] ** 2 + s[:, 5] ** 2))
    s1, s2, s3, _ = fe3d.principal(s)
    P = Xn[ids]
    excl = (((P[:, 0] >= 37.49) & (np.hypot(P[:, 1] - 3, P[:, 2] + 17) <= 11.6)) if not PLUG else np.zeros(len(P), bool)) | (P[:, 2] <= -74.0)
    zones = {"legs_z-49..-26": (P[:, 2] >= -49.0) & (P[:, 2] <= -26.0),
             "below_deck_z-74..-49": (P[:, 2] >= -74.0) & (P[:, 2] < -49.0),
             "boss_tongue_z>-26": P[:, 2] > -26.0}
    out = dict(Fx=Fx, My=round(My, 1), Mz=round(Mz, 1), its=len(m.last_res), umax=round(float(abs(U).max()), 4))
    for zn, zm in zones.items():
        mm = zm & ~excl
        if not mm.any(): continue
        v = vm[mm]; k = int(np.argmax(v))
        out[zn] = dict(vm_max=round(float(v.max()), 2), vm_p999=round(float(np.percentile(v, 99.9)), 2), vm_p99=round(float(np.percentile(v, 99)), 2),
                       at=[round(float(q), 2) for q in P[mm][k]],
                       s1_max=round(float(s1[mm].max()), 2), s3_min=round(float(s3[mm].min()), 2))
    # displacement of the plug face (tilt) for information
    ux = U[3 * face]
    out["face_tilt_mrad"] = [round(float(np.polyfit(yf, ux, 1)[0] * 1e3), 3), round(float(np.polyfit(zf, ux, 1)[0] * 1e3), 3)]
    res["cases"][str(a)] = out
    print(a, json.dumps(out), flush=True)
json.dump(res, open(f"fe_col_{SIDE}_{VAR0}.json", "w"), indent=1)
