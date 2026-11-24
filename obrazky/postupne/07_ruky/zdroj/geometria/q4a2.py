"""Q4 layout A (rerun with scans): margins at the approved pebble (exact), then the smallest thickness scale kt (attach rule of T3 kept:
inner surface at u_att stays 5 mm from the attach point -> growth goes outward), the smallest outward shift dx of the pebble relative to
T_klb / servo, and the smallest kt for a given dx."""
import json, time
from armgeo import *
exec(open("q4_common.py").read())
t0 = time.time()


def mfun(P, F, kt=1.0, dx=0.0, h=0.25):
    sd = sdf_world(P[~F], kt, dx=dx, dmax=2.6, h=h)
    return float((-sd - WALL).min())


KTS = np.round(np.arange(1.0, 2.001, 0.02), 3)
DXS = np.arange(0.0, 12.01, 1.0)
boxes = []
for nm, (L_, W_, H_, s) in CASES.items():
    for var, x0 in (("a", X_END + 0.3), ("b", X_CUT + 0.3)):
        for on, eL in ORI.items():
            if on == "back": continue                       # mirror of fwd (pebble symmetric fore-aft within 0.1)
            eH = np.array([1.0, 0, 0]); eW = np.cross(eH, eL)
            P, F = box_surface(AXP + np.array([x0, 0, 0]), eL, eW, eH, L_, W_, H_, s, 0.5)
            sd = sdf_world(P, dmax=30.0)
            mo = float((-sd[~F] - WALL).min()); at = P[~F][(-sd[~F]).argmin()]
            pin = float(sd[F].max())
            Pc, Fc = box_surface(AXP + np.array([x0, 0, 0]), eL, eW, eH, L_, W_, H_, s, 1.0)
            boxes.append(dict(case=nm, var=var, ori=on, x0=x0, x1=x0 + H_, margin=round(mo, 3), worst=np.round(at, 2).tolist(), face_out=round(pin, 3),
                              P=Pc, F=Fc, kt_only=None, dx_only=None, kt_for_dx={}))
            print("%s %s %-5s x %.2f..%.2f margin %+.3f worst %s shaft-face out of skin %+.3f" % (nm, var, on, x0, x0 + H_, mo, np.round(at, 2), pin), flush=True)
# dx only (kt 1)
for b in boxes:
    for dx in np.arange(0.0, 15.01, 0.25):
        if mfun(b["P"], b["F"], 1.0, dx) >= 0:
            b["dx_only"] = float(dx); break
print("dx scan done %.0f s" % (time.time() - t0), flush=True)
# kt scan (outer), dx grid (inner)
for kt in KTS:
    for b in boxes:
        for dx in DXS:
            if dx in b["kt_for_dx"]: continue
            if mfun(b["P"], b["F"], kt, dx) >= 0:
                b["kt_for_dx"][dx] = float(kt)
                if dx == 0.0: b["kt_only"] = float(kt)
print("kt scan done %.0f s" % (time.time() - t0), flush=True)
HTMAX = 2 * prof(np.linspace(0, 1, 20001))[1].max()
out = []
for b in boxes:
    kd = {float(k): v for k, v in sorted(b["kt_for_dx"].items())}
    # cheapest combined: smallest thickness growth over dx
    comb = min(((v - 1) * HTMAX, dx, v) for dx, v in kd.items()) if kd else None
    rec = {k: v for k, v in b.items() if k not in ("P", "F", "kt_for_dx")}
    rec["kt_for_dx"] = kd; rec["thick_growth_kt_only_mm"] = None if b["kt_only"] is None else round((b["kt_only"] - 1) * HTMAX, 2)
    rec["best_combined"] = None if comb is None else dict(growth_mm=round(comb[0], 2), dx=comb[1], kt=comb[2])
    out.append(rec)
    print("%s %s %-5s margin %+.2f | kt only %s (+%s mm) | dx only %s | kt for dx %s | cheapest combo %s" %
          (b["case"], b["var"], b["ori"], b["margin"], b["kt_only"], rec["thick_growth_kt_only_mm"], b["dx_only"],
           {k: v for k, v in kd.items()}, rec["best_combined"]))
json.dump(out, open("q4a_out.json", "w"), indent=1)
