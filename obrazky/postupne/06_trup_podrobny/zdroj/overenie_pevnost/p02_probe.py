"""quick geometry probes for the lift chain (P_kluka, L_ucho, L_pata, P_drziak_serva, P_sachta pads)"""
import numpy as np, pv_lib as L
log = L.Log("p02_probe")
for n in ("P_kluka", "L_ucho", "L_pata", "P_drziak_serva", "cap_kluky", "servo_zdvih"):
    lo, hi = L.bbox(L.load(n)); log(n, lo.round(2), hi.round(2), "vol %.1f" % L.volume(L.load(n)))
# crank: sections z = const at rest (arm vertical), window x -17.5..-12.3, y 18..28.5
for z in (-27.6, -28.0, -28.5, -29.0, -30.0, -31.0, -32.0, -33.0, -34.2):
    r = L.sec("P_kluka", "z", z, window=(-17.5, -12.3, 18.0, 28.5), h=0.01)
    if r["A"] == 0: log("kluka z", z, "empty"); continue
    zm = L.zmods(r)
    log("P_kluka z %6.2f: A %5.2f x %.2f..%.2f y %.2f..%.2f (cy %.2f) I_bend_y %.3f Zy %.3f/%.3f  I_bend_x %.3f" %
        (z, r["A"], r["umin"], r["umax"], r["wmin"], r["wmax"], r["cw"], r["Iu"], zm["Zu_p"], zm["Zu_m"], r["Iw"]))
log("crank pin hole: chords along z through (x -15.75, y 23.2):", L.chords("P_kluka", (-15.75, 23.2, -40), (0, 0, 1)))
log("crank pin hole: chords along y through (x -15.75, z -34.2):", L.chords("P_kluka", (-15.75, 10, -34.2), (0, 1, 0)))
log("crank hub: chords along z through (x -14, y 23.2):", L.chords("P_kluka", (-14.0, 23.2, -40), (0, 0, 1)))
log("crank hub: chords along y through (x -14, z -24.2):", L.chords("P_kluka", (-14.0, 10, -24.2), (0, 1, 0)))
log("crank hub: chords along x through (y 23.2, z -24.2):", L.chords("P_kluka", (-25, 23.2, -24.2), (1, 0, 0)))
log("crank hub: chords along x through (y 23.2, z -21.7):", L.chords("P_kluka", (-25, 23.2, -21.7), (1, 0, 0)))
# ear: sections y = const, window x -20.5..-7, z -41..-31
for y in (10.0, 11.0, 12.0, 12.6, 13.2, 14.0, 16.0, 18.0, 20.0, 22.0, 23.2, 24.0, 24.5, 24.8):
    r = L.sec("L_ucho", "y", y, window=(-20.5, -7.0, -41.0, -31.0), h=0.01)
    if r["A"] == 0: log("ucho y", y, "empty"); continue
    zm = L.zmods(r)
    log("L_ucho y %5.2f: A %5.2f x %.2f..%.2f z %.2f..%.2f (cz %.2f) I_bend_z %.3f Z %.3f/%.3f" %
        (y, r["A"], r["umin"], r["umax"], r["wmin"], r["wmax"], r["cw"], r["Iu"], zm["Zu_p"], zm["Zu_m"]))
for y in (13.2, 18.0, 23.2, 24.6):
    log("L_ucho vertical chords at x -18.65, y %.1f:" % y, L.chords("L_ucho", (-18.65, y, -45), (0, 0, 1)))
log("L_ucho chords along y at x -18.65, z -34.2:", L.chords("L_ucho", (-18.65, 0, -34.2), (0, 1, 0)))
log("L_ucho chords along y at x -18.65, z -32.5:", L.chords("L_ucho", (-18.65, 0, -32.5), (0, 1, 0)))
log("L_ucho flange chords along z at x -10.0 (screw), y 11.0:", L.chords("L_ucho", (-10.0, 11.0, -45), (0, 0, 1)))
log("L_ucho flange chords along z at x -15.5 (dowel), y 11.0:", L.chords("L_ucho", (-15.5, 11.0, -45), (0, 0, 1)))
log("L_ucho flange chords along x at y 11.0, z -38.5:", L.chords("L_ucho", (-25, 11.0, -38.5), (1, 0, 0)))
log("L_ucho flange chords along x at y 11.0, z -38.95:", L.chords("L_ucho", (-25, 11.0, -38.95), (1, 0, 0)))
# foot: around the ear pilot (x -10, z -38.5) and dowel (x -15.5, z -38.95), along y from the back face
log("L_pata chords along z at x -10.0, y 7.0:", L.chords("L_pata", (-10.0, 7.0, -45), (0, 0, 1)))
log("L_pata chords along z at x -15.5, y 8.0:", L.chords("L_pata", (-15.5, 8.0, -45), (0, 0, 1)))
log("L_pata chords along x at y 7.0, z -38.5:", L.chords("L_pata", (-25, 7.0, -38.5), (1, 0, 0)))
log("L_pata chords along y at x -10, z -38.5:", L.chords("L_pata", (-10, -20, -38.5), (0, 1, 0)))
for yy in (0.0, 3.0, 6.0, 9.0):
    r = L.sec("L_pata", "y", yy, window=(-23, 23, -41, -36), h=0.01)
    zm = L.zmods(r)
    log("L_pata y %4.1f: A %6.2f I_bend_z %.2f Z %.2f/%.2f x %.2f..%.2f" % (yy, r["A"], r["Iu"], zm["Zu_p"], zm["Zu_m"], r["umin"], r["umax"]))
# bracket: ledge root y 17.1..18, post, plate
for y in (17.3, 18.0, 20.0, 22.0, 24.0):
    r = L.sec("P_drziak_serva", "y", y, window=(-7, 23, -42.5, -12), h=0.01)
    if r["A"] == 0: log("drziak y", y, "empty"); continue
    log("P_drziak_serva y %5.2f: A %6.2f x %.2f..%.2f z %.2f..%.2f" % (y, r["A"], r["umin"], r["umax"], r["wmin"], r["wmax"]))
for y in (17.5, 20.0, 23.2):
    r = L.sec("P_drziak_serva", "y", y, window=(-7, 17, -42.5, -40.5), h=0.005)
    zm = L.zmods(r)
    log("  ledge y %.1f: A %.2f z %.3f..%.3f I %.3f Z %.3f x %.2f..%.2f" % (y, r["A"], r["wmin"], r["wmax"], r["Iu"], zm["Zu_p"], r["umin"], r["umax"]))
    r = L.sec("P_drziak_serva", "y", y, window=(-1, 6, -19, -12), h=0.005)
    if r["A"]:
        zm = L.zmods(r)
        log("  post  y %.1f: A %.2f x %.2f..%.2f z %.3f..%.3f I %.3f Z %.3f/%.3f" % (y, r["A"], r["umin"], r["umax"], r["wmin"], r["wmax"], r["Iu"], zm["Zu_p"], zm["Zu_m"]))
log("bracket post pilot: chords along y at x 2.5 z -15.85:", L.chords("P_drziak_serva", (2.5, 10, -15.85), (0, 1, 0)))
log("bracket post pilot: chords along z at x 2.5 y 23.2:", L.chords("P_drziak_serva", (2.5, 23.2, -45), (0, 0, 1)))
log("bracket F10 slots: chords along y at (19.5, z -31.7):", L.chords("P_drziak_serva", (19.5, 0, -31.7), (0, 1, 0)))
log("bracket F10 slots: chords along y at (8.0, z -14.5):", L.chords("P_drziak_serva", (8.0, 0, -14.5), (0, 1, 0)))
for x0, z0 in ((19.5, -31.7), (8.0, -14.5)):
    log("bracket around F10 (%.1f, %.1f): chords along x at y 16.5:" % (x0, z0), L.chords("P_drziak_serva", (x0 - 10, 16.5, z0), (1, 0, 0)))
    log("                        chords along z at y 16.5:", L.chords("P_drziak_serva", (x0, 16.5, z0 - 10), (0, 0, 1)))
    log("P_sachta pad chords along y at (%.1f, %.1f):" % (x0, z0), L.chords("P_sachta", (x0, 0, z0), (0, 1, 0)))
    log("P_sachta pad chords along x at y 14.0:", L.chords("P_sachta", (x0 - 10, 14.0, z0), (1, 0, 0)))
    log("P_sachta pad chords along z at y 14.0:", L.chords("P_sachta", (x0, 14.0, z0 - 10), (0, 0, 1)))
    r = L.sec("P_sachta", "y", 13.0, window=(x0 - 4, x0 + 4, z0 - 4, z0 + 4), h=0.01)
    log("P_sachta pad section y 13.0: A %.2f I %.2f / %.2f" % (r["A"], r["Iu"], r["Iw"]))
