"""Q3: how deep T_klb sits in the pebble (rest pose) + where the pebble inner face meets the T_klb shoulder"""
from armgeo import *
xs = np.arange(40.0, 80.0, 0.002)
Q = np.column_stack([xs, np.full(len(xs), SH_Y), np.full(len(xs), ZS)])
sd = sdf_world(Q)
ins = sd < 0
x_in, x_out = xs[ins][0], xs[ins][-1]
w2 = sd <= -2.0
x_w_in, x_w_out = xs[w2][0], xs[w2][-1]
print("axis line: pebble inner x %.3f, outer x %.3f; 2.0-inset surface inner x %.3f, outer x %.3f; max depth %.3f at x %.3f" %
      (x_in, x_out, x_w_in, x_w_out, -sd.min(), xs[sd.argmin()]))
for nm, xe in (("T_klb end face (now)", 58.756), ("T_klb cut at 50.9", 50.9), ("step face", 50.956)):
    print("  %-22s x %.3f -> free depth to the inside of a 2.0 outer wall: %.3f mm ; to the outer surface %.3f" % (nm, xe, x_w_out - xe, x_out - xe))
print("  T_klb end face lies %.3f mm inside the pebble inner surface (along the axis)" % (58.756 - x_in))
# pebble inner-surface x as a function of (r, azimuth) around the shoulder axis; azimuth 0 = +Y (back), 90 = +Z (up), 180 = front, 270 = down
print("\npebble inner surface x (first entry along +X) on lines || X at radius r, azimuth az about the axis (az 0 = back +Y, 90 = up, 180 = front -Y, 270 = down)")
azs = np.arange(0, 360, 30)
print("   r  " + " ".join("%7d" % a for a in azs) + "   min (az)")
res = {}
xs = np.arange(44.0, 70.0, 0.005)
for r in (0, 4, 8, 10.2, 11.0, 11.4, 12.0, 12.7, 13.5, 14.0, 15.0, 16.0):
    row = []
    for az in np.arange(0, 360, 2):
        y = SH_Y + r * math.cos(math.radians(az)); z = ZS + r * math.sin(math.radians(az))
        Q = np.column_stack([xs, np.full(len(xs), y), np.full(len(xs), z)])
        ins = inside_local(to_local(Q))
        row.append(xs[ins][0] if ins.any() else np.nan)
    row = np.array(row); res[r] = row
    k = np.nanargmin(row)
    print("%5.1f " % r + " ".join("%7.2f" % row[int(a // 2)] for a in azs) + "   %.3f (%d)" % (row[k], 2 * k))
# T_klb shoulder (step face x 50.956 r 11.48..12.70, fillet/chamfer to r 13.5 at x 50.156): exact check with the STL
T = load("T_klb_L")
P = vlib.sample_surface(T, 0.15)
r = np.hypot(P[:, 1] - SH_Y, P[:, 2] - ZS)
body = (P[:, 0] <= 51.3) & (r >= 11.2)          # shoulder ring + body r 13.5 (not the journal)
jour = (P[:, 0] >= 51.3)                           # D22 journal + end face
sdb = sdf_world(P[body]); sdj = sdf_world(P[jour])
print("\nT_klb STL samples: shoulder/body part (x<=51.3, r>=11.2): %d samples, %d inside the pebble, max depth inside %.3f mm at %s" %
      (body.sum(), (sdb < 0).sum(), -sdb.min(), np.round(P[body][sdb.argmin()], 2)))
pb = P[body][sdb < 0]
if len(pb):
    rb = np.hypot(pb[:, 1] - SH_Y, pb[:, 2] - ZS); azb = np.degrees(np.arctan2(pb[:, 2] - ZS, pb[:, 1] - SH_Y)) % 360
    print("   inside region: x %.2f..%.2f, r %.2f..%.2f, azimuth %.0f..%.0f deg" % (pb[:, 0].min(), pb[:, 0].max(), rb.min(), rb.max(), azb.min(), azb.max()))
print("journal + end face (x>=51.3): %d samples, %d outside the pebble (max %.3f mm outside); min depth inside %.3f" %
      (jour.sum(), (sdj > 0).sum(), sdj.max(), -sdj.max()))
# gap along x between the step-face ring and the pebble at each azimuth (r 11.5..12.7): + = clear
print("x-gap pebble inner surface - step face 50.956 at r 12.0: min %.3f at az %d ; at r 12.7: min %.3f ; - chamfer x(r) at r 13.5 (50.156): %.3f" %
      (np.nanmin(res[12.0]) - 50.956, 2 * np.nanargmin(res[12.0]), np.nanmin(res[12.7]) - 50.956, np.nanmin(res[13.5]) - 50.156))
