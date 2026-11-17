"""p06 probe: shoulder (left; right is the mirror) - T_klb_L sections across the axis, column sections, boss, cap flange"""
import numpy as np, pv_lib as L
log = L.Log("p06_probe_shoulder")
for n in ("T_klb_L", "T_puzdro_L", "T_bok_L"):
    lo, hi = L.bbox(L.load(n)); log(n, lo.round(2), hi.round(2))
# T_klb_L sections x = const, (y, z) about the axis (3, -17)
for x in (38.6, 39.0, 39.5, 40.2, 40.8, 42.0, 44.5, 46.0, 48.0, 50.0, 51.0, 52.0, 55.0, 58.0):
    r = L.sec("T_klb_L", "x", x, window=(-12, 18, -32, -2), h=0.02)
    if r["A"] == 0: log("T_klb_L x", x, "empty"); continue
    zm = L.zmods(r)
    log("T_klb_L x %5.1f: A %6.1f y %.2f..%.2f z %.2f..%.2f  I_z(bend in z) %7.1f Z %6.1f/%6.1f  I_y %7.1f Z %6.1f/%6.1f" %
        (x, r["A"], r["umin"], r["umax"], r["wmin"], r["wmax"], r["Iu"], zm["Zu_p"], zm["Zu_m"], r["Iw"], zm["Zw_p"], zm["Zw_m"]))
for x in (39.0, 41.0, 43.0, 47.0):
    log("T_klb_L radial chords at x %.1f along +z from the axis:" % x, L.chords("T_klb_L", (x, 3.0, -17.0), (0, 0, 1)))
    log("T_klb_L radial chords at x %.1f along -y from the axis:" % x, L.chords("T_klb_L", (x, 3.0, -17.0), (0, -1, 0)))
log("T_klb_L chords along x on the axis:", L.chords("T_klb_L", (30, 3.0, -17.0), (1, 0, 0)))
for az in (90, 210, 330):
    import math
    dy, dz = 7.5 * math.cos(math.radians(az)), 7.5 * math.sin(math.radians(az))
    log("F8 hole az %d: T_klb chords along x:" % az, L.chords("T_klb_L", (30, 3 + dy, -17 + dz), (1, 0, 0)))
    log("              T_ram chords along x:", L.chords("T_ram", (30, 3 + dy, -17 + dz), (1, 0, 0)))
    log("              T_bok_L chords along x:", L.chords("T_bok_L", (30, 3 + dy, -17 + dz), (1, 0, 0)))
# column boss / stop ring of T_ram, sections x = const
for x in (34.6, 35.5, 36.5, 37.5, 38.2, 38.7):
    r = L.sec("T_ram", "x", x, window=(-12, 18, -32, -2), h=0.02)
    zm = L.zmods(r)
    log("T_ram boss x %5.1f: A %6.1f I_z %7.1f Z %6.1f/%6.1f I_y %7.1f" % (x, r["A"], r["Iu"], zm["Zu_p"], zm["Zu_m"], r["Iw"]))
# column: sections z = const (x, y), left column window x 33..44.5, y -12..18
for z in (-80.0, -78.5, -77.5, -76.0, -72.0, -65.0, -55.0, -45.0, -35.0, -30.5, -29.0, -27.0):
    r = L.sec("T_ram", "z", z, window=(33.0, 44.5, -12.0, 18.0), h=0.02)
    if r["A"] == 0: log("col z", z, "empty"); continue
    zm = L.zmods(r)
    log("T_ram col z %6.1f: A %6.1f x %.2f..%.2f y %.2f..%.2f  I_y(bend in x) %7.1f Z %6.1f/%6.1f  I_x(bend in y) %8.1f Z %7.1f/%7.1f" %
        (z, r["A"], r["umin"], r["umax"], r["wmin"], r["wmax"], r["Iw"], zm["Zw_p"], zm["Zw_m"], r["Iu"], zm["Zu_p"], zm["Zu_m"]))
# cap flange: T_bok_L section x 39.85
r = L.sec("T_bok_L", "x", 39.85, window=(-12, 18, -32, -2), h=0.02)
log("T_bok_L seat flange x 39.85: A %.1f  y %.2f..%.2f z %.2f..%.2f" % (r["A"], r["umin"], r["umax"], r["wmin"], r["wmax"]))
log("T_bok_L flange radial chords along +z at x 39.85:", L.chords("T_bok_L", (39.85, 3, -17), (0, 0, 1)))
log("T_bok_L flange radial chords along -z at x 39.85:", L.chords("T_bok_L", (39.85, 3, -17), (0, 0, -1)))
log("T_ram stop ring chords along +z at x 38.75:", L.chords("T_ram", (38.75, 3, -17), (0, 0, 1)))
log("T_ram chords along x at (y 3, z -17+12.2):", L.chords("T_ram", (30, 3, -4.8), (1, 0, 0)))
