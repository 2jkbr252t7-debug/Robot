"""Q8 helpers: outward shift dx of the approved pebble that clears the T_klb shoulder; exposed part of the D22 journal"""
from armgeo import *
T = load("T_klb_L")
P = vlib.sample_surface(T, 0.15)
r = np.hypot(P[:, 1] - SH_Y, P[:, 2] - ZS)
body = P[(P[:, 0] <= 51.3) & (r >= 11.2)]
for dx in (0.0, 0.5, 1.0, 1.3, 1.5, 1.8, 2.0, 2.5):
    sd = sdf_world(body, dx=dx)
    print("dx %.1f: min clearance pebble - T_klb shoulder/body %.3f" % (dx, sd.min()))
jr = P[(P[:, 0] >= 51.556) & (P[:, 0] <= 57.956) & (np.abs(r - 11.0) < 0.05)]
sd = sdf_world(jr)
out = jr[sd > 0]
az = np.degrees(np.arctan2(out[:, 2] - ZS, out[:, 1] - SH_Y)) % 360
print("D22 journal surface outside the pebble at rest: %.1f %% of its samples, x %.2f..%.2f, azimuth %.0f..%.0f (0 = back +Y, 90 = up, 270 = down)" %
      (100 * len(out) / len(jr), out[:, 0].min(), out[:, 0].max(), az.min(), az.max()))
# shoulder overlap: where on the pebble (u) and which T_klb feature
sdb = sdf_world(body); pin = body[sdb < 0]
loc = to_local(pin)
print("overlap: pebble u %.3f..%.3f, local x %.2f..%.2f (inner side), T_klb x %.2f..%.2f r %.2f..%.2f" %
      ((-loc[:, 2] / L).min(), (-loc[:, 2] / L).max(), loc[:, 0].min(), loc[:, 0].max(), pin[:, 0].min(), pin[:, 0].max(),
       np.hypot(pin[:, 1] - SH_Y, pin[:, 2] - ZS).min(), np.hypot(pin[:, 1] - SH_Y, pin[:, 2] - ZS).max()))
# T_bok_L near point at +135 deg: distance grows with dx ?
Tb = load("T_bok_L"); Pb = vlib.sample_surface(Tb, 0.2); Pb = Pb[(Pb[:, 0] > 44) & (np.linalg.norm(Pb - np.array([49.0, 5.85, -30.7]), axis=1) < 15)]
for dx in (0.0, 1.0, 1.5, 2.0):
    print("dx %.1f: T_bok_L clearance at arm +135 deg %.3f" % (dx, sdf_world(swing(Pb, -135), dx=dx).min()))
