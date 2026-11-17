"""p09 - the small extra numbers quoted in the report (so that every number has a script): countersunk cone bearing,
printed 21T serration (M08), column-foot carry-over, fix checks (metal F12 screw, MG90S held at two points, steel stop dowels),
open-U vs closed-box torsion of the column."""
import math, pv_lib as L
log = L.Log("p09_extra")
G = 9.80665
# countersunk M2.5 (dk 4.7, 90 deg) cone bearing at 0.3 N.m (preload 600 N)
F = 0.3 / (0.2 * 0.0025)
r1, r2 = 1.4, 2.35; s = (r2 - r1) * math.sqrt(2)
A = math.pi * (r1 + r2) * s
log("countersunk M2.5 cone: slant area %.1f mm2, preload %.0f N -> normal bearing %.0f MPa" % (A, F, F / A))
# printed 21T serration of P_kluka (d 4.44 / 4.84, engaged x -15.5..-12.7 = 2.8)
for nm, T in (("L2 mid 0.30 N.m", 0.30), ("MG90S stall 0.216 N.m", 0.216)):
    rm = (4.44 + 4.84) / 4; Ft = T * 1000 / rm
    A_fl = 21 * (4.84 - 4.44) / 2 * 2.8
    p_all, p_third = Ft / A_fl, Ft / (A_fl / 3)
    hoop = Ft / (math.pi * 2 * rm * 2.8) * (4.84 / 2) / 1.18
    log("serration %s: Ft %.0f N, flank bearing %.1f MPa (all 21 teeth) / %.1f (a third); hoop in the 1.18 wall %.1f MPa" % (nm, Ft, p_all, p_third, hoop))
# column foot moment by carry-over (propped cantilever: fixed at z -78, prop at -55): M_foot = M_prop / 2
for nm, Mp in (("L5", 1100.0), ("one arm 15 N", 15 * (54.8 - 36.5))):
    log("column foot %s: M_prop %.0f -> M_foot %.0f N.mm -> %.1f MPa (Z 21.0 at z -76)" % (nm, Mp, Mp / 2, Mp / 2 / 21.0))
# fix checks
As_m2 = 2.07
log("metal foot + metal ear, F12 M2 at 201 N: %.0f MPa in the screw (8.8: Rp0.2 640)" % (201 / As_m2))
x_load, x_tab = -18.65, -1.25
M = 30 * (x_tab - x_load)
log("MG90S held by both tabs (27.7 apart in z): moment %.0f N.mm -> %.1f N per screw; by a closed pocket gripping both case ends (22.5 apart in x): %.1f N"
    % (M, M / 27.7, 30 * (16.0 - x_load) / 22.5 - 30))
T = 0.6; r = 18.0; Fd = T * 1000 / r; d, Le, e = 3.0, 6.0, 1.5
p = Fd / (d * Le) + 6 * Fd * e / (d * Le ** 2)
log("steel stop dowel Ø3 embedded 6, contact at r 18, lever 1.5: F %.1f N, bearing in resin %.1f MPa" % (Fd, p))
# column torsion: open U (J = sum b t^3/3) vs closed box 24 x 7.6 with t 2.0 (Bredt J = 4 A^2 t / perimeter)
J_open = (24 * 2.0 ** 3 + 2 * 7.6 * 1.6 ** 3) / 3
Am = (24 - 2.0) * (7.6 - 2.0); per = 2 * ((24 - 2.0) + (7.6 - 2.0))
J_box = 4 * Am ** 2 * 2.0 / per
log("column torsion stiffness: open U J %.0f mm4, closed box (2.0 walls) J %.0f mm4 (x %.0f)" % (J_open, J_box, J_box / J_open))
# F8 clamp on the column stop ring (r 11.6..12.8) carrying the side-cap seat flange
A_ring = math.pi * (12.8 ** 2 - 11.6 ** 2)
for T in (0.15, 0.048):
    Fp = 3 * T / (0.2 * 0.002)
    log("F8 clamp at %.3f N.m: 3 x %.0f N on the stop ring %.1f mm2 -> %.1f MPa sustained" % (T, Fp / 3, A_ring, Fp / A_ring))
# disc springs (DIN 2093 10 x 5.2 x 0.4, load ASSUMED 100..150 N) inner edge line load on resin
for Fs in (100.0, 150.0):
    log("disc spring %.0f N on its inner edge (circumference %.1f mm): %.1f N/mm line load on resin" % (Fs, math.pi * 5.2, Fs / (math.pi * 5.2)))
# spring load needed for 0.25 N.m with mu 0.2 on 1 or 2 faces at r_m 3.8
for n in (1, 2):
    log("friction collar 0.25 N.m, mu 0.2, r_m 3.8, %d face(s): spring load %.0f N" % (n, 250 / (0.2 * 3.8 * n)))
log.save("p09_extra")
