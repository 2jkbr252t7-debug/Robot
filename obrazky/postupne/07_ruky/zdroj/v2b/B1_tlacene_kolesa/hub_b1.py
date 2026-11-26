"""B1: room and clearances INSIDE the arm (dx -1.0).  Parts from geo_b1.arm_side():
  ARM_*  rotate with the arm (hub, 6700, washer, homing rib)       PLG_*  static plug features (ring, seat, homing lug)
  DRV_*  rotate with the gear-tube (drive hub, M2 screw head) - relative to the arm only while the clutch slips
Checks
  (1) every ARM_ / DRV_ part inside the pebble with >= 1.2 mm shell wall left (sdf <= -1.2), at rest (drive parts are
      axisymmetric, the arm-fixed ones move with the pebble, so rest = all poses);
  (2) static plug features vs arm-fixed parts over the swing -45..+135 (1 deg) : min distance, and the homing contact
      (rib vs lug) at the stop angle -51 deg;
  (3) drive parts vs arm-fixed parts (axisymmetric -> one pose) and vs static plug features.
Writes hub_b1.json"""
import sys, json, math, time
sys.dont_write_bytecode = True
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R1/geo")
from armgeo import sdf_world, swing   # noqa
import geo_b1 as B

DX = -1.0
STOP = -51.0                     # homing stop angle (arm), 6 deg beyond the -45 range end
W_RIB, W_LUG = 4.0 / 7.0, 4.5 / 5.8          # full angular widths (rad) used in geo_b1.sector
B.LUG_AZ = 270.0                              # lug at 6 o'clock (hidden inside the arm anyway)
# rib azimuth at rest such that its edge meets the lug edge at swing STOP (swing a rotates by -a in this azimuth convention)
B.RIB_AZ0 = B.LUG_AZ - math.degrees(W_LUG / 2 + W_RIB / 2) + STOP
t0 = time.time()
P = B.arm_side(h=0.15)
res = dict(dx=DX, stop_deg=STOP, lug_az=B.LUG_AZ, rib_az_rest=round(B.RIB_AZ0, 2), room={}, swing={}, drive={})
# (1) room
for k, v in P.items():
    if k.startswith("PLG"):
        continue
    d = sdf_world(v, dx=DX)
    i = int(np.argmax(d))
    res["room"][k] = dict(max_sdf=round(float(d.max()), 2), wall_left=round(float(-d.max()), 2), at=v[i].round(2).tolist(),
                          ok=bool(d.max() <= -1.2))
    print("room %-18s wall left %.2f at %s" % (k, -d.max(), v[i].round(2)), flush=True)
# (2) static plug features vs arm-fixed parts over the swing
ARM = {k: v for k, v in P.items() if k.startswith("ARM")}
PLG = {k: v for k, v in P.items() if k.startswith("PLG")}
angs = np.r_[np.arange(-45.0, 135.01, 1.0), STOP]
for pk, pv in PLG.items():
    tr = cKDTree(pv)
    for ak, av in ARM.items():
        if ak == "ARM_6700" and pk == "PLG_seat":
            continue                      # inner race on the seat (designed contact)
        best = (1e9, None)
        sym = (ak != "ARM_rib" and pk != "PLG_lug")      # both axisymmetric about the shoulder axis -> one pose
        for a in (angs[:1] if sym else angs[:-1]):
            d, _ = tr.query(swing(av, a), distance_upper_bound=3.0)
            m = float(d.min())
            if m < best[0]:
                best = (m, a)
        key = f"{ak} vs {pk}"
        res["swing"][key] = dict(min=round(best[0], 2) if best[0] < 3 else ">3", at_deg=best[1])
        print("swing %-28s min %s at %s deg" % (key, res["swing"][key]["min"], best[1]), flush=True)
# homing contact at STOP
d, _ = cKDTree(PLG["PLG_lug"]).query(swing(ARM["ARM_rib"], STOP))
d45, _ = cKDTree(PLG["PLG_lug"]).query(swing(ARM["ARM_rib"], -45.0))
res["homing"] = dict(gap_at_stop=round(float(d.min()), 3), gap_at_minus45=round(float(d45.min()), 3))
print("homing rib-lug gap at %.0f deg: %.3f ; at -45: %.3f" % (STOP, d.min(), d45.min()))
# contact overlap of the stop faces (radial x axial) for the strength calc
r_ov = (max(B.HUB["rib_r"][0], B.LUG["r"][0]), min(B.HUB["rib_r"][1], B.LUG["r"][1]))
x_ov = (max(B.HUB["rib_x"][0], B.LUG["x"][0]), min(B.HUB["rib_x"][1], B.LUG["x"][1]))
res["homing"]["contact_face"] = dict(r=r_ov, x=x_ov, area_mm2=round((r_ov[1] - r_ov[0]) * (x_ov[1] - x_ov[0]), 2),
                                     r_mean=round(sum(r_ov) / 2, 2))
print("stop contact face r %s x %s area %.2f mm2" % (r_ov, x_ov, res["homing"]["contact_face"]["area_mm2"]))
# (3) drive parts vs arm parts and plug features (no rotation needed: drive parts are axisymmetric, except the hub's
#     magnets which are inside the disc)
DRV = {k: v for k, v in P.items() if k.startswith("DRV")}
for dk, dv in DRV.items():
    for ok_, ov in {**ARM, **PLG}.items():
        if dk == "DRV_disc" and ok_ == "ARM_washer":
            continue                      # friction contact (designed)
        d, _ = cKDTree(ov).query(dv, distance_upper_bound=3.0)
        m = float(d.min())
        if m < 3:
            res["drive"][f"{dk} vs {ok_}"] = round(m, 2)
            print("drive %-28s %.2f" % (f"{dk} vs {ok_}", m), flush=True)
json.dump(res, open("hub_b1.json", "w"), indent=1)
print("done %.0fs" % (time.time() - t0))
