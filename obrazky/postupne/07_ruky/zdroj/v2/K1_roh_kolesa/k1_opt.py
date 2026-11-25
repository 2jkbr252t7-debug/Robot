"""K1 - best pose of a servo case with its shaft EXACTLY parallel to X (needed for a spur train to the X-parallel shoulder
axis), 4 DOF (x of the output face, y / z of the shaft, roll phi about X), maximising the worst clearance margin against the
K1 obstacle model (k1_hard<VAR>.npz; column, T_klb, amplifier, T_bok socket features already removed).
margin(p) = min( ds(p) - 0.25 - 0.3 ,  dm(p) - 0.25 - 1.0 )   (trilinear EDT to voxel centres; -0.25 = half voxel; +-0.25 accuracy)
Also scans: for every feasible pose (margin >= 0) the distance of the shaft to the shoulder axis.
usage: k1_opt.py <servo> <VAR> [both]   servo in scs | scs_full | kst | mg90s ; output face toward +X (and -X with 'both')"""
import sys, os, json, math, time
sys.dont_write_bytecode = True
import numpy as np
from scipy.ndimage import map_coordinates
from scipy.optimize import minimize
HERE = "/tmp/claude-0/gapwf/fin/R1/K1_roh_kolesa"
SERVO = sys.argv[1]; VAR = sys.argv[2] if len(sys.argv) > 2 else ""
BOTH = len(sys.argv) > 3 and sys.argv[3] == "both"
D = np.load(os.path.join(HERE, f"k1_hard{VAR}.npz"))
lo, h = D["lo"], float(D["h"])
from scipy import ndimage as _ndi
# SIGNED distances (negative = depth inside the obstacle), so that the optimiser sees how deep a pose penetrates
ds = D["ds"] - _ndi.distance_transform_edt(D["hard"], sampling=h).astype(np.float32)
dm = D["dm"] - _ndi.distance_transform_edt(D["move"], sampling=h).astype(np.float32)
AX = np.array([3.0, -17.0])
# (L, W, H case, shaft offset from the near end, extras)
SERV = dict(scs=(23.2, 12.1, 21.5, 5.9, ""), scs_full=(23.2, 12.1, 21.5, 5.9, "re"), kst=(20.0, 7.0, 16.6, 5.0, ""),
            mg90s=(22.8, 12.2, 22.7, 5.9, ""))
L, W, Hc, s0, EX = SERV[SERVO]


def local_pts(step=0.6):
    P = []

    def box(l0, l1, w0, w1, h0, h1, solid=False):
        ls = np.arange(l0, l1 + 1e-9, step); ws = np.arange(w0, w1 + 1e-9, step); hs = np.arange(h0, h1 + 1e-9, step)
        for a in (ls[0], l1):
            Wv, Hv = np.meshgrid(ws, hs, indexing="ij"); P.append(np.stack([np.full(Wv.size, a), Wv.ravel(), Hv.ravel()], 1))
        for b in (ws[0], w1):
            Lv, Hv = np.meshgrid(ls, hs, indexing="ij"); P.append(np.stack([Lv.ravel(), np.full(Lv.size, b), Hv.ravel()], 1))
        for c in (hs[0], h1):
            Lv, Wv = np.meshgrid(ls, ws, indexing="ij"); P.append(np.stack([Lv.ravel(), Wv.ravel(), np.full(Lv.size, c)], 1))
        if solid:
            Lv, Wv, Hv = np.meshgrid(ls[::2], ws[::2], hs[::2], indexing="ij"); P.append(np.stack([Lv.ravel(), Wv.ravel(), Hv.ravel()], 1))
    hb = -25.25 if "r" in EX else -Hc
    box(-s0, L - s0, -W / 2, W / 2, hb, 0.0, solid=True)
    if "e" in EX:
        box(-s0 - 4.7, L - s0 + 4.7, -W / 2, W / 2, -8.0, -3.5)
    th = np.linspace(0, 2 * np.pi, 24, endpoint=False)
    P.append(np.stack([4.0 * np.cos(th), 4.0 * np.sin(th), np.full(24, 0.6)], 1))
    return np.concatenate(P)


LP = local_pts()


def world(x):
    xt, ys, zs, ph = x[:4]; sg = x[4] if len(x) > 4 else 1.0
    el = np.array([math.cos(ph), math.sin(ph)]); ew = np.array([-math.sin(ph), math.cos(ph)])
    yz = LP[:, :1] * el + LP[:, 1:2] * ew
    return np.stack([xt + sg * LP[:, 2], ys + yz[:, 0], zs + yz[:, 1]], 1)


def margin(x, detail=False):
    P = world(x)
    I = ((P - lo) / h - 0.5).T
    a = map_coordinates(ds, I, order=1, mode="constant", cval=0.0) - 0.25 - 0.3
    b = map_coordinates(dm, I, order=1, mode="constant", cval=0.0) - 0.25 - 1.0
    m = np.minimum(a, b)
    return (m, a, b) if detail else m


def f(x):
    m = margin(x)
    return -float(m.min()) - 0.05 * float(np.mean(np.minimum(m, 0.0)))


t0 = time.time()
res = []
sgns = (1.0, -1.0) if BOTH else (1.0,)
cand = []
for sg in sgns:
    for xt in (np.arange(36.0, 42.1, 1.0) if sg > 0 else np.arange(14.0, 26.1, 2.0)):
        for ys in np.arange(-32.0, 24.1, 2.0):
            for zs in np.arange(-80.0, -18.0, 2.0):
                for ph in np.radians(np.arange(0, 360, 22.5)):
                    x0 = np.array([xt, ys, zs, ph, sg])
                    cand.append((float(margin(x0).min()), x0))
print("coarse evaluations", len(cand), f"{time.time()-t0:.0f}s", flush=True)
cand.sort(key=lambda t: -t[0])
# keep the best starts, but also the best start per region of the shaft (5 mm cells) so that near-axis poses are optimised too
keep, seen = [], set()
for m0, x0 in cand:
    key = (int(x0[1] // 5), int(x0[2] // 5), x0[4])
    if key in seen and len(keep) > 60: continue
    seen.add(key); keep.append((m0, x0))
    if len(keep) >= 160: break
for m0, x0 in keep:
    sg = x0[4]
    r = minimize(lambda v: f(np.r_[v, sg]), x0[:4], method="Nelder-Mead",
                 options=dict(xatol=0.05, fatol=0.005, maxiter=500, adaptive=True))
    m = margin(np.r_[r.x, sg]).min()
    res.append((float(m), [float(v) for v in r.x] + [sg]))
print("optimised", len(res), f"{time.time()-t0:.0f}s", flush=True)
res.sort(key=lambda t: -t[0])
out = []
for m, x in res[:60]:
    d = math.hypot(x[1] - AX[0], x[2] - AX[1])
    out.append(dict(margin=round(m, 2), x_face=round(x[0], 2), y=round(x[1], 2), z=round(x[2], 2),
                    phi_deg=round(math.degrees(x[3]) % 360, 1), out_dir="+X" if x[4] > 0 else "-X", d_axis=round(d, 2)))
best = out[0]
# best among poses with margin >= 0 by distance to the axis
feas = [o for o in out if o["margin"] >= 0]
summary = dict(servo=SERVO, var=VAR, case=[L, W, Hc, s0, EX], best=best,
               feasible_closest=(min(feas, key=lambda o: o["d_axis"]) if feas else None), top=out[:25],
               note="margin = clearance - required (0.3 static, 1.0 moving), voxel EDT, +-0.25 accuracy")
json.dump(summary, open(os.path.join(HERE, f"k1_opt_{SERVO}_{VAR or 'base'}{'_both' if BOTH else ''}.json"), "w"), indent=1)
print(json.dumps(dict(best=best, feasible_closest=summary["feasible_closest"]), indent=1))
