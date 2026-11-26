"""VERIFIER: hand torque at the two-sided hidden stop (arm pushed past -51 / +140.5 by hand) - rib in the arm hub
(x 53..55, r 5.5..8.5, 32.7 deg) against the plug lug (r 5.0..6.6).  Contact r 5.5..6.6 x 2.0 (2.2 mm2) at r 6.05; rib root at
the hub bore wall r 7.5 (lever 1.45), section 2.0 axial x 3.5 circumferential.  Tip at 53.75 mm (v_arm.json)."""
import json
tip, r_c, A_c, lever, b, t = 53.75, 6.05, 2.2, 1.45, 2.0, 3.5
Z = b * t * t / 6
out = {}
for Ft in (1.0, 3.0, 5.0, 7.0, 10.0):
    F = Ft * tip / r_c
    out[f"tip {Ft} N"] = dict(stop_force_N=round(F, 1), bearing_MPa=round(F / A_c, 1), rib_bending_MPa=round(F * lever / Z, 1),
                              rib_shear_MPa=round(F / (b * t), 1))
F = 17.0 / r_c
out["homing at clutch 0.017"] = dict(stop_force_N=round(F, 2), bearing_MPa=round(F / A_c, 2))
# 90 deg rib (lug 78.5 deg keeps the same stop angles), radial overlap r 5.2..7.0 -> 3.6 mm2, t ~ 9.5 at r 6
Z2 = b * 9.5 ** 2 / 6
for Ft in (7.0, 10.0):
    F = Ft * tip / 6.1
    out[f"wide rib, tip {Ft} N"] = dict(bearing_MPa=round(F / 3.6, 1), rib_bending_MPa=round(F * 1.4 / Z2, 1))
print(json.dumps(out, indent=1)); json.dump(out, open("v_rib.json", "w"), indent=1)
